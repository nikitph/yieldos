from __future__ import annotations

import random

from .models import Forecast, PolicyConfig, RequestShape, TraceRecord


def _bucket(tokens: int) -> str:
    if tokens <= 160:
        return "short"
    if tokens <= 750:
        return "medium"
    return "long"


def classify_request(
    record: TraceRecord,
    policy: PolicyConfig,
    rng: random.Random,
    partial_output_tokens: int = 0,
) -> RequestShape:
    """Probabilistic request-shape classifier with oracle/noisy modes."""
    actual_remaining = max(1, record.output_tokens - partial_output_tokens)
    if policy.exact_output_oracle:
        p50 = actual_remaining
        confidence = 0.98
    else:
        base = actual_remaining
        if policy.noisy_forecasts:
            sigma = 0.42 if record.prompt_tokens < 2_000 else 0.58
            multiplier = rng.lognormvariate(0.0, sigma)
        else:
            multiplier = 1.0
        p50 = max(1, int(base * multiplier))
        confidence = max(0.25, min(0.9, 1.0 - abs(multiplier - 1.0) * 0.55))

    p90 = max(p50 + 1, int(p50 * (1.55 if confidence < 0.65 else 1.3)))
    p99 = max(p90 + 1, int(p50 * (2.25 if confidence < 0.65 else 1.7)))
    bucket = _bucket(p90)

    if record.prompt_tokens >= 4_000 and p90 < 700:
        phase = "prefill_heavy"
    elif p90 >= 900:
        phase = "decode_heavy"
    elif record.priority_class == "interactive" and record.prompt_tokens < 800:
        phase = "streaming_chat"
    else:
        phase = "balanced"

    if record.priority_class == "batch":
        latency = "batch"
    elif record.priority_class == "interactive":
        latency = "interactive"
    else:
        latency = "standard"

    if record.prefix_id and record.prompt_tokens >= 1_000:
        cacheability = "high"
    elif record.prefix_id:
        cacheability = "medium"
    else:
        cacheability = "low"

    memory_risk = "high" if record.prompt_tokens + p90 > 6_000 else "medium"
    if record.prompt_tokens + p90 < 1_200:
        memory_risk = "low"

    if confidence < 0.45:
        routing = "baseline_conservative"
        fallback = True
    elif latency == "interactive" and bucket == "short":
        routing = "low_latency_decode"
        fallback = False
    elif phase == "prefill_heavy":
        routing = "chunked_prefill"
        fallback = False
    elif phase == "decode_heavy":
        routing = "decode_residency_protected"
        fallback = False
    elif latency == "batch":
        routing = "opportunistic_throughput"
        fallback = False
    elif cacheability == "high":
        routing = "prefix_cache"
        fallback = False
    else:
        routing = "balanced"
        fallback = False

    return RequestShape(
        output_forecast=Forecast(
            p50=p50,
            p90=p90,
            p99=p99,
            bucket=bucket,
            confidence=confidence,
        ),
        phase_profile=phase,
        cacheability=cacheability,
        latency_class=latency,
        memory_risk=memory_risk,
        routing_class=routing,
        fallback_to_baseline=fallback,
    )
