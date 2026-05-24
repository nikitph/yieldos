from __future__ import annotations

from .models import RequestState


def update_slo_notary(req: RequestState, now_ms: int, queue_depth: int) -> str:
    """Predict breach risk and choose a coarse intervention."""
    if req.done or req.abandoned:
        req.breach_probability = 0.0
        req.slo_action = "none"
        return "none"

    elapsed = now_ms - req.trace.arrival_time_ms
    if req.first_token_ms is None:
        slack = req.trace.ttft_slo_ms - elapsed
        pressure = 1.0 - (slack / max(1, req.trace.ttft_slo_ms))
        pressure += min(0.45, queue_depth / 220.0)
        if req.trace.priority_class == "interactive" and pressure > 0.62:
            req.breach_probability = min(0.99, pressure)
            req.slo_action = "stop_large_prefill_admission"
            req.protected_decode = True
            return req.slo_action
        if pressure > 0.82:
            req.breach_probability = min(0.99, pressure)
            req.slo_action = "boost_priority"
            return req.slo_action
    else:
        since_last = now_ms - (req.last_token_ms or req.first_token_ms)
        pressure = since_last / max(1, req.trace.itl_slo_ms)
        pressure += min(0.35, queue_depth / 260.0)
        if pressure > 0.72 and req.trace.priority_class != "batch":
            req.breach_probability = min(0.99, pressure)
            req.slo_action = "reserve_decode_slot"
            req.protected_decode = True
            return req.slo_action

    req.breach_probability = 0.0
    req.slo_action = "none"
    return "none"
