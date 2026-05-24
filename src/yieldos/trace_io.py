from __future__ import annotations

import csv
import io
import json
import urllib.request
from pathlib import Path
from typing import Any

from .models import TraceRecord
from .workloads import _slo_for


REQUIRED_FIELDS = {
    "arrival_time_ms",
    "prompt_tokens",
    "output_tokens",
    "tenant_id",
    "priority_class",
}


def load_trace(path: Path) -> list[TraceRecord]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return _load_csv(path)
    if suffix in {".jsonl", ".ndjson"}:
        return _load_jsonl(path)
    raise ValueError(f"unsupported trace format: {path.suffix}; use .csv or .jsonl")


def load_burstgpt_trace(source: str, limit: int | None = None, time_scale: float = 1.0) -> list[TraceRecord]:
    """Load a BurstGPT CSV sample into the YieldOS replay schema.

    BurstGPT timestamps are in seconds from the first day. `time_scale` compresses
    or expands interarrival times: 20.0 means 20x higher request rate.
    """
    if time_scale <= 0:
        raise ValueError("time_scale must be positive")
    records: list[TraceRecord] = []
    with _open_text_source(source) as f:
        reader = csv.DictReader(f)
        required = {"Timestamp", "Model", "Request tokens", "Response tokens", "Log Type"}
        if reader.fieldnames is None or required - set(reader.fieldnames):
            missing = required - set(reader.fieldnames or [])
            raise ValueError(f"BurstGPT trace missing required fields: {sorted(missing)}")
        first_ts: float | None = None
        for idx, row in enumerate(reader):
            response_tokens = _required_int(row, "Response tokens")
            if response_tokens <= 0:
                continue
            timestamp_s = float(row["Timestamp"])
            if first_ts is None:
                first_ts = timestamp_s
            arrival_ms = int(((timestamp_s - first_ts) * 1000.0) / time_scale)
            log_type = str(row.get("Log Type") or "")
            request_tokens = _required_int(row, "Request tokens")
            priority = _burstgpt_priority(log_type, request_tokens)
            ttft, itl = _slo_for(priority)
            model = str(row.get("Model") or "unknown").lower().replace(" ", "-")
            records.append(
                TraceRecord(
                    request_id=f"burstgpt-{len(records):06d}",
                    arrival_time_ms=arrival_ms,
                    prompt_tokens=request_tokens,
                    output_tokens=response_tokens,
                    tenant_id=f"model-{model}",
                    priority_class=priority,
                    ttft_slo_ms=ttft,
                    itl_slo_ms=itl,
                    prefix_id=None,
                    abandoned_at_ms=None,
                )
            )
            if limit is not None and len(records) >= limit:
                break
    return records


def write_trace_csv(trace: list[TraceRecord], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "request_id",
                "arrival_time_ms",
                "prompt_tokens",
                "output_tokens",
                "tenant_id",
                "priority_class",
                "ttft_slo_ms",
                "itl_slo_ms",
                "prefix_id",
                "abandoned_at_ms",
                "request_type",
            ],
        )
        writer.writeheader()
        for record in trace:
            writer.writerow(_record_to_row(record))


def _load_csv(path: Path) -> list[TraceRecord]:
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError("CSV trace has no header")
        missing = REQUIRED_FIELDS - set(reader.fieldnames)
        if missing:
            raise ValueError(f"CSV trace missing required fields: {sorted(missing)}")
        return [_row_to_record(row, idx) for idx, row in enumerate(reader)]


def _load_jsonl(path: Path) -> list[TraceRecord]:
    records: list[TraceRecord] = []
    with path.open(encoding="utf-8") as f:
        for idx, line in enumerate(f):
            if not line.strip():
                continue
            row = json.loads(line)
            missing = REQUIRED_FIELDS - set(row)
            if missing:
                raise ValueError(f"JSONL record {idx} missing required fields: {sorted(missing)}")
            records.append(_row_to_record(row, idx))
    return records


def _open_text_source(source: str):
    if source.startswith(("http://", "https://")):
        response = urllib.request.urlopen(source, timeout=60)  # noqa: S310 - user-provided research trace URL.
        return io.TextIOWrapper(response, encoding="utf-8", newline="")
    return Path(source).open(encoding="utf-8", newline="")


def _row_to_record(row: dict[str, Any], idx: int) -> TraceRecord:
    priority = str(row["priority_class"])
    ttft_default, itl_default = _slo_for(priority)
    request_id = str(row.get("request_id") or row.get("id") or f"trace-{idx:06d}")
    prefix = _optional_str(row.get("prefix_id"))
    abandoned = _optional_int(row.get("abandoned_at_ms"))
    return TraceRecord(
        request_id=request_id,
        arrival_time_ms=_required_int(row, "arrival_time_ms"),
        prompt_tokens=_required_int(row, "prompt_tokens"),
        output_tokens=_required_int(row, "output_tokens"),
        tenant_id=str(row["tenant_id"]),
        priority_class=priority,
        ttft_slo_ms=_optional_int(row.get("ttft_slo_ms")) or ttft_default,
        itl_slo_ms=_optional_int(row.get("itl_slo_ms")) or itl_default,
        prefix_id=prefix,
        abandoned_at_ms=abandoned,
    )


def _record_to_row(record: TraceRecord) -> dict[str, Any]:
    return {
        "request_id": record.request_id,
        "arrival_time_ms": record.arrival_time_ms,
        "prompt_tokens": record.prompt_tokens,
        "output_tokens": record.output_tokens,
        "tenant_id": record.tenant_id,
        "priority_class": record.priority_class,
        "ttft_slo_ms": record.ttft_slo_ms,
        "itl_slo_ms": record.itl_slo_ms,
        "prefix_id": record.prefix_id or "",
        "abandoned_at_ms": "" if record.abandoned_at_ms is None else record.abandoned_at_ms,
        "request_type": "",
    }


def _required_int(row: dict[str, Any], key: str) -> int:
    try:
        return int(float(row[key]))
    except (TypeError, ValueError, KeyError) as exc:
        raise ValueError(f"invalid integer field {key!r}: {row.get(key)!r}") from exc


def _optional_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    return int(float(value))


def _optional_str(value: Any) -> str | None:
    if value is None or value == "":
        return None
    return str(value)


def _burstgpt_priority(log_type: str, request_tokens: int) -> str:
    if request_tokens >= 12_000:
        return "batch"
    if log_type.lower().startswith("conversation"):
        return "interactive"
    return "standard"
