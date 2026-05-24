from __future__ import annotations

import csv
import json
from pathlib import Path


def write_ohi_gain_report(
    workload_summary: Path,
    burstgpt_summary: Path,
    out_dir: Path,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    points = _profile_points(workload_summary) + _burstgpt_points(burstgpt_summary)
    corr = _pearson([p["ohi"] for p in points], [p["yieldos_gain_pct"] for p in points])
    with (out_dir / "ohi_gain.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["workload", "ohi", "yieldos_goodput", "distserve_goodput", "yieldos_gain_pct"],
        )
        writer.writeheader()
        writer.writerows(points)
    lines = [
        "# OHI vs YieldOS Gain",
        "",
        f"Pearson correlation over this small pilot set: `{corr:.3f}`.",
        "",
        "| workload | OHI | YieldOS v0.2 | DistServe-style | YieldOS gain |",
        "|---|---:|---:|---:|---:|",
    ]
    for point in sorted(points, key=lambda p: p["ohi"]):
        lines.append(
            f"| {point['workload']} | {point['ohi']:.3f} | "
            f"{point['yieldos_goodput']:.2f} | {point['distserve_goodput']:.2f} | "
            f"{point['yieldos_gain_pct']:.1f}% |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This is a coarse explanatory analysis, not a definitive law. The current pilot supports the hypothesis that YieldOS gains rise when obligation heterogeneity rises. The BurstGPT sample is a boundary condition: low OHI, no prefix reuse, mostly interactive traffic, and DistServe-style disaggregation wins.",
        ]
    )
    (out_dir / "ohi_gain.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _profile_points(summary_path: Path) -> list[dict[str, float | str]]:
    rows = _load(summary_path)
    by = {r["policy"]: r for r in rows}
    points: list[dict[str, float | str]] = []
    for profile in [
        "chat_heavy",
        "rag_heavy",
        "code_heavy",
        "batch_summary_heavy",
        "mixed_enterprise",
    ]:
        y = by[f"yieldos_v02_{profile}"]
        d = by[f"distserve_disaggregated_{profile}"]
        points.append(_point(profile, y, d))
    return points


def _burstgpt_points(summary_path: Path) -> list[dict[str, float | str]]:
    rows = _load(summary_path)
    by = {r["policy"]: r for r in rows}
    return [_point("burstgpt_100x", by["yieldos_v02_burstgpt"], by["distserve_disaggregated_burstgpt"])]


def _point(workload: str, yieldos: dict, distserve: dict) -> dict[str, float | str]:
    y_goodput = float(yieldos["governed_goodput"])
    d_goodput = float(distserve["governed_goodput"])
    return {
        "workload": workload,
        "ohi": float(yieldos["obligation_heterogeneity_index"]),
        "yieldos_goodput": y_goodput,
        "distserve_goodput": d_goodput,
        "yieldos_gain_pct": ((y_goodput - d_goodput) / d_goodput) * 100.0,
    }


def _load(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _pearson(xs: list[float], ys: list[float]) -> float:
    if len(xs) < 2:
        return 0.0
    x_mean = sum(xs) / len(xs)
    y_mean = sum(ys) / len(ys)
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
    x_var = sum((x - x_mean) ** 2 for x in xs)
    y_var = sum((y - y_mean) ** 2 for y in ys)
    denom = (x_var * y_var) ** 0.5
    if denom == 0:
        return 0.0
    return numerator / denom
