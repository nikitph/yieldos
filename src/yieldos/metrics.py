from __future__ import annotations

import csv
import json
import math
from dataclasses import asdict
from pathlib import Path

from .models import Metrics, RequestState, SimResult


def percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    if len(values) == 1:
        return values[0]
    pos = (len(values) - 1) * q
    lo = int(pos)
    hi = min(len(values) - 1, lo + 1)
    frac = pos - lo
    return values[lo] * (1 - frac) + values[hi] * frac


def request_met_slo(req: RequestState) -> bool:
    if not req.done or req.first_token_ms is None:
        return False
    ttft = req.first_token_ms - req.trace.arrival_time_ms
    return ttft <= req.trace.ttft_slo_ms and req.max_itl_ms <= req.trace.itl_slo_ms


def compute_metrics(
    policy: str,
    requests: list[RequestState],
    finish_time_ms: int,
    scheduler_overhead_ms: float,
    kv_hit_tokens: int,
    kv_value_preserved: float,
    kv_recompute_waste: float,
) -> Metrics:
    completed = [r for r in requests if r.done]
    abandoned = [r for r in requests if r.abandoned]
    slo_ok = [r for r in completed if request_met_slo(r)]
    ttfts = [float(r.ttft_ms or 0) for r in completed if r.ttft_ms is not None]
    itls = [float(r.max_itl_ms) for r in completed]
    useful_tokens = sum(r.completed_output_tokens for r in slo_ok)
    raw_tokens = sum(r.completed_output_tokens for r in completed)
    gpu_seconds = max(0.001, (finish_time_ms + scheduler_overhead_ms) / 1000.0)
    return Metrics(
        policy=policy,
        requests=len(requests),
        obligation_heterogeneity_index=obligation_heterogeneity_index(requests),
        completed=len(completed),
        abandoned=len(abandoned),
        slo_attainment=len(slo_ok) / max(1, len(requests)),
        governed_goodput=useful_tokens / gpu_seconds,
        raw_tokens_per_gpu_second=raw_tokens / gpu_seconds,
        ttft_p50=percentile(ttfts, 0.50),
        ttft_p95=percentile(ttfts, 0.95),
        ttft_p99=percentile(ttfts, 0.99),
        itl_p50=percentile(itls, 0.50),
        itl_p95=percentile(itls, 0.95),
        itl_p99=percentile(itls, 0.99),
        kv_hit_tokens=kv_hit_tokens,
        kv_value_preserved=kv_value_preserved,
        kv_recompute_waste=kv_recompute_waste,
        scheduler_overhead_ms=scheduler_overhead_ms,
        finish_time_ms=finish_time_ms,
    )


def write_results(results: list[SimResult], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = [asdict(r.metrics) for r in results]
    with (out_dir / "summary.json").open("w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)
    with (out_dir / "summary.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    for result in results:
        with (out_dir / f"{result.metrics.policy}_decisions.jsonl").open("w", encoding="utf-8") as f:
            for decision in result.decisions:
                f.write(json.dumps(asdict(decision), sort_keys=True) + "\n")
    write_markdown_report(results, out_dir / "report.md")


def write_markdown_report(results: list[SimResult], path: Path) -> None:
    best = max(results, key=lambda r: r.metrics.governed_goodput)
    lines = [
        "# YieldOS-Lite Run Report",
        "",
        f"Best governed goodput: `{best.metrics.policy}` at {best.metrics.governed_goodput:.2f} tokens/GPU-second.",
        "",
        "| policy | OHI | governed goodput | SLO attainment | TTFT p95 | ITL p95 | KV hits | KV value preserved | KV recompute waste | overhead ms |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in sorted(results, key=lambda x: x.metrics.governed_goodput, reverse=True):
        m = r.metrics
        lines.append(
            f"| {m.policy} | {m.obligation_heterogeneity_index:.3f} | "
            f"{m.governed_goodput:.2f} | {m.slo_attainment:.3f} | "
            f"{m.ttft_p95:.1f} | {m.itl_p95:.1f} | {m.kv_hit_tokens} | "
            f"{m.kv_value_preserved:.1f} | {m.kv_recompute_waste:.1f} | "
            f"{m.scheduler_overhead_ms:.1f} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "Governed goodput counts only completed output tokens from requests that met both TTFT and ITL SLOs, then divides by simulated GPU time plus control-plane overhead.",
            "The simulator is intentionally coarse; use it to compare policy behavior and ablations before integrating with a real engine.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def obligation_heterogeneity_index(requests: list[RequestState]) -> float:
    """Coarse 0-1 signal for how much governance should matter."""
    if not requests:
        return 0.0
    records = [r.trace for r in requests]
    prompt_h = _normalized_entropy([_length_bucket(r.prompt_tokens) for r in records])
    output_h = _normalized_entropy([_length_bucket(r.output_tokens) for r in records])
    priority_h = _normalized_entropy([r.priority_class for r in records])
    slo_h = _normalized_entropy([_slo_bucket(r.ttft_slo_ms, r.itl_slo_ms) for r in records])
    prefix_reuse = _prefix_reuse_score(records)
    kv_pressure = _kv_pressure_score(records)
    return (
        prompt_h
        + output_h
        + priority_h
        + slo_h
        + prefix_reuse
        + kv_pressure
    ) / 6.0


def _length_bucket(tokens: int) -> str:
    if tokens <= 160:
        return "short"
    if tokens <= 750:
        return "medium"
    if tokens <= 3_000:
        return "long"
    return "xl"


def _slo_bucket(ttft_ms: int, itl_ms: int) -> str:
    if ttft_ms <= 1_200 and itl_ms <= 180:
        return "tight"
    if ttft_ms <= 3_000 and itl_ms <= 350:
        return "normal"
    return "loose"


def _normalized_entropy(values: list[str]) -> float:
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    if len(counts) <= 1:
        return 0.0
    total = len(values)
    entropy = 0.0
    for count in counts.values():
        p = count / total
        entropy -= p * math.log(p)
    return entropy / math.log(len(counts))


def _prefix_reuse_score(records) -> float:
    prefix_counts: dict[str, int] = {}
    for record in records:
        if record.prefix_id:
            prefix_counts[record.prefix_id] = prefix_counts.get(record.prefix_id, 0) + 1
    reused = sum(count for count in prefix_counts.values() if count > 1)
    return min(1.0, reused / max(1, len(records)))


def _kv_pressure_score(records) -> float:
    avg_context = sum(r.prompt_tokens + r.output_tokens for r in records) / max(1, len(records))
    return min(1.0, avg_context / 8_000.0)
