from __future__ import annotations

import random

from .models import TraceRecord


def _slo_for(priority: str) -> tuple[int, int]:
    if priority == "interactive":
        return 950, 145
    if priority == "standard":
        return 2_600, 280
    return 8_000, 900


def _clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


def generate_mixed_trace(
    requests: int = 800,
    seed: int = 7,
    load: float = 1.0,
) -> list[TraceRecord]:
    """Generate a heterogeneous trace matching the MVP evaluation plan."""
    rng = random.Random(seed)
    out: list[TraceRecord] = []
    t = 0.0
    prefix_pool = [f"shared-{i:02d}" for i in range(42)]

    for i in range(requests):
        burst = 0.35 if i % 170 in range(25) else 1.0
        t += rng.expovariate(load / (42.0 * burst))
        kind = rng.choices(
            [
                "short_chat",
                "doc_qa",
                "code_gen",
                "batch_summary",
                "streaming",
                "adversarial",
            ],
            weights=[34, 18, 16, 13, 13, 6],
        )[0]

        if kind == "short_chat":
            prompt = _clamp(int(rng.lognormvariate(4.7, 0.45)), 20, 420)
            output = _clamp(int(rng.lognormvariate(3.8, 0.55)), 8, 180)
            priority = "interactive"
        elif kind == "doc_qa":
            prompt = _clamp(int(rng.lognormvariate(7.4, 0.55)), 900, 12_000)
            output = _clamp(int(rng.lognormvariate(4.4, 0.65)), 40, 420)
            priority = rng.choices(["interactive", "standard"], [35, 65])[0]
        elif kind == "code_gen":
            prompt = _clamp(int(rng.lognormvariate(5.8, 0.7)), 180, 2_800)
            output = _clamp(int(rng.lognormvariate(5.8, 0.75)), 80, 1_800)
            priority = rng.choices(["interactive", "standard"], [50, 50])[0]
        elif kind == "batch_summary":
            prompt = _clamp(int(rng.lognormvariate(7.8, 0.55)), 1_400, 18_000)
            output = _clamp(int(rng.lognormvariate(4.9, 0.55)), 80, 700)
            priority = "batch"
        elif kind == "streaming":
            prompt = _clamp(int(rng.lognormvariate(5.2, 0.6)), 80, 900)
            output = _clamp(int(rng.lognormvariate(6.4, 0.65)), 300, 2_800)
            priority = rng.choices(["interactive", "standard"], [60, 40])[0]
        else:
            prompt = _clamp(int(rng.lognormvariate(6.8, 0.7)), 500, 9_000)
            output = _clamp(int(rng.lognormvariate(6.7, 0.7)), 500, 4_500)
            priority = rng.choices(["interactive", "standard", "batch"], [25, 45, 30])[0]

        ttft, itl = _slo_for(priority)
        if kind in {"doc_qa", "batch_summary"} and rng.random() < 0.58:
            prefix = rng.choice(prefix_pool)
        elif kind == "short_chat" and rng.random() < 0.14:
            prefix = rng.choice(prefix_pool[:12])
        else:
            prefix = None

        abandoned = None
        if priority == "interactive" and rng.random() < 0.045:
            abandoned = int(t + rng.randint(1_200, 4_800))
        elif priority == "standard" and rng.random() < 0.025:
            abandoned = int(t + rng.randint(4_000, 14_000))

        out.append(
            TraceRecord(
                request_id=f"req-{i:05d}",
                arrival_time_ms=int(t),
                prompt_tokens=prompt,
                output_tokens=output,
                tenant_id=f"tenant-{rng.randint(1, 14):02d}",
                priority_class=priority,
                ttft_slo_ms=ttft,
                itl_slo_ms=itl,
                prefix_id=prefix,
                abandoned_at_ms=abandoned,
            )
        )
    return out


def generate_kv_heavy_trace(
    requests: int = 800,
    seed: int = 11,
    load: float = 1.0,
) -> list[TraceRecord]:
    """Generate memory-pressure-heavy reuse traces for KV Treasury stress."""
    rng = random.Random(seed)
    out: list[TraceRecord] = []
    t = 0.0
    rag_docs = [f"rag-doc-{i:02d}" for i in range(22)]
    chat_sessions = [f"chat-session-{i:02d}" for i in range(34)]
    tenant_priority = {
        f"tenant-{i:02d}": rng.choice(["interactive", "standard", "batch"])
        for i in range(1, 16)
    }

    for i in range(requests):
        t += rng.expovariate(load / 35.0)
        kind = rng.choices(
            ["rag_reuse", "multiturn_chat", "long_context", "abandoned_session", "cold_noise"],
            weights=[34, 28, 16, 12, 10],
        )[0]
        tenant = f"tenant-{rng.randint(1, 15):02d}"

        if kind == "rag_reuse":
            prefix = rng.choice(rag_docs)
            prompt = _clamp(int(rng.lognormvariate(8.25, 0.32)), 2_800, 18_000)
            output = _clamp(int(rng.lognormvariate(4.8, 0.55)), 80, 780)
            priority = rng.choices(["interactive", "standard", "batch"], [24, 56, 20])[0]
        elif kind == "multiturn_chat":
            prefix = rng.choice(chat_sessions)
            turn = 1 + (i % 9)
            prompt = _clamp(int(rng.lognormvariate(6.0 + turn * 0.08, 0.38)), 350, 5_500)
            output = _clamp(int(rng.lognormvariate(4.35, 0.55)), 40, 520)
            priority = rng.choices(["interactive", "standard"], [70, 30])[0]
        elif kind == "long_context":
            prefix = rng.choice(rag_docs + chat_sessions)
            prompt = _clamp(int(rng.lognormvariate(8.65, 0.35)), 4_500, 26_000)
            output = _clamp(int(rng.lognormvariate(5.35, 0.6)), 120, 1_200)
            priority = rng.choices(["interactive", "standard"], [20, 80])[0]
        elif kind == "abandoned_session":
            prefix = rng.choice(chat_sessions)
            prompt = _clamp(int(rng.lognormvariate(7.6, 0.55)), 1_400, 14_000)
            output = _clamp(int(rng.lognormvariate(5.8, 0.65)), 220, 1_800)
            priority = tenant_priority[tenant]
        else:
            prefix = None
            prompt = _clamp(int(rng.lognormvariate(6.7, 0.65)), 450, 7_500)
            output = _clamp(int(rng.lognormvariate(5.0, 0.65)), 70, 1_200)
            priority = rng.choice(["interactive", "standard", "batch"])

        ttft, itl = _slo_for(priority)
        abandoned = None
        if kind == "abandoned_session" or (priority == "interactive" and rng.random() < 0.07):
            abandoned = int(t + rng.randint(1_500, 9_000))

        out.append(
            TraceRecord(
                request_id=f"kv-{i:05d}",
                arrival_time_ms=int(t),
                prompt_tokens=prompt,
                output_tokens=output,
                tenant_id=tenant,
                priority_class=priority,
                ttft_slo_ms=ttft,
                itl_slo_ms=itl,
                prefix_id=prefix,
                abandoned_at_ms=abandoned,
            )
        )
    return out


def generate_shape_stress_trace(
    requests: int = 800,
    seed: int = 13,
    load: float = 1.0,
) -> list[TraceRecord]:
    """Generate sharply heterogeneous shapes to test hard vs soft routing."""
    rng = random.Random(seed)
    out: list[TraceRecord] = []
    t = 0.0
    prefixes = [f"shape-prefix-{i:02d}" for i in range(28)]
    kinds = [
        "tiny_chat",
        "huge_prefill_short_answer",
        "short_prompt_long_stream",
        "code_generation",
        "batch_long_summary",
        "ambiguous_medium",
    ]
    weights = [24, 20, 18, 16, 12, 10]

    for i in range(requests):
        burst = 0.28 if i % 130 < 35 else 1.0
        t += rng.expovariate(load / (36.0 * burst))
        kind = rng.choices(kinds, weights=weights)[0]
        if kind == "tiny_chat":
            prompt = rng.randint(20, 220)
            output = rng.randint(12, 140)
            priority = "interactive"
            prefix = rng.choice(prefixes[:6]) if rng.random() < 0.12 else None
        elif kind == "huge_prefill_short_answer":
            prompt = rng.randint(5_000, 24_000)
            output = rng.randint(25, 260)
            priority = rng.choices(["interactive", "standard"], [35, 65])[0]
            prefix = rng.choice(prefixes)
        elif kind == "short_prompt_long_stream":
            prompt = rng.randint(80, 900)
            output = rng.randint(800, 4_200)
            priority = rng.choices(["interactive", "standard"], [64, 36])[0]
            prefix = None
        elif kind == "code_generation":
            prompt = rng.randint(250, 3_500)
            output = rng.randint(350, 3_200)
            priority = rng.choices(["interactive", "standard"], [48, 52])[0]
            prefix = rng.choice(prefixes[6:14]) if rng.random() < 0.25 else None
        elif kind == "batch_long_summary":
            prompt = rng.randint(3_000, 22_000)
            output = rng.randint(180, 1_000)
            priority = "batch"
            prefix = rng.choice(prefixes)
        else:
            prompt = rng.randint(450, 5_500)
            output = rng.randint(120, 1_400)
            priority = rng.choice(["interactive", "standard", "batch"])
            prefix = rng.choice(prefixes) if rng.random() < 0.35 else None

        ttft, itl = _slo_for(priority)
        abandoned = None
        if priority == "interactive" and rng.random() < 0.035:
            abandoned = int(t + rng.randint(1_500, 6_500))

        out.append(
            TraceRecord(
                request_id=f"shape-{i:05d}",
                arrival_time_ms=int(t),
                prompt_tokens=prompt,
                output_tokens=output,
                tenant_id=f"tenant-{rng.randint(1, 16):02d}",
                priority_class=priority,
                ttft_slo_ms=ttft,
                itl_slo_ms=itl,
                prefix_id=prefix,
                abandoned_at_ms=abandoned,
            )
        )
    return out


def generate_profile_trace(
    profile: str,
    requests: int = 800,
    seed: int = 41,
    load: float = 1.0,
) -> list[TraceRecord]:
    """Generate semi-realistic profile traces for research-readiness checks."""
    if profile == "chat_heavy":
        return _generate_profiled_trace(
            requests,
            seed,
            load,
            weights={
                "short_chat": 48,
                "multiturn_chat": 26,
                "streaming_chat": 14,
                "rag_qa": 7,
                "code": 5,
            },
        )
    if profile == "rag_heavy":
        return _generate_profiled_trace(
            requests,
            seed,
            load,
            weights={
                "rag_qa": 46,
                "long_rag": 22,
                "multiturn_chat": 14,
                "short_chat": 10,
                "batch_summary": 8,
            },
        )
    if profile == "code_heavy":
        return _generate_profiled_trace(
            requests,
            seed,
            load,
            weights={
                "code": 46,
                "long_code": 20,
                "short_chat": 12,
                "rag_qa": 10,
                "streaming_chat": 12,
            },
        )
    if profile == "batch_summary_heavy":
        return _generate_profiled_trace(
            requests,
            seed,
            load,
            weights={
                "batch_summary": 46,
                "long_rag": 18,
                "rag_qa": 16,
                "short_chat": 10,
                "code": 10,
            },
        )
    if profile == "mixed_enterprise":
        return _generate_profiled_trace(
            requests,
            seed,
            load,
            weights={
                "short_chat": 24,
                "rag_qa": 22,
                "code": 18,
                "batch_summary": 16,
                "multiturn_chat": 12,
                "long_rag": 8,
            },
        )
    raise ValueError(f"unknown profile {profile!r}")


def available_profiles() -> list[str]:
    return [
        "chat_heavy",
        "rag_heavy",
        "code_heavy",
        "batch_summary_heavy",
        "mixed_enterprise",
    ]


def _generate_profiled_trace(
    requests: int,
    seed: int,
    load: float,
    weights: dict[str, int],
) -> list[TraceRecord]:
    rng = random.Random(seed)
    out: list[TraceRecord] = []
    t = 0.0
    kinds = list(weights)
    kind_weights = [weights[k] for k in kinds]
    rag_prefixes = [f"profile-rag-{i:02d}" for i in range(36)]
    chat_prefixes = [f"profile-chat-{i:02d}" for i in range(48)]
    code_prefixes = [f"profile-code-{i:02d}" for i in range(24)]

    for i in range(requests):
        burst = 0.42 if i % 210 < 45 else 1.0
        t += rng.expovariate(load / (38.0 * burst))
        kind = rng.choices(kinds, weights=kind_weights)[0]
        prefix: str | None = None

        if kind == "short_chat":
            prompt = _clamp(int(rng.lognormvariate(4.6, 0.42)), 18, 360)
            output = _clamp(int(rng.lognormvariate(3.9, 0.52)), 10, 190)
            priority = "interactive"
            if rng.random() < 0.18:
                prefix = rng.choice(chat_prefixes)
        elif kind == "multiturn_chat":
            prefix = rng.choice(chat_prefixes)
            prompt = _clamp(int(rng.lognormvariate(6.2, 0.45)), 360, 4_800)
            output = _clamp(int(rng.lognormvariate(4.35, 0.55)), 45, 480)
            priority = rng.choices(["interactive", "standard"], [72, 28])[0]
        elif kind == "streaming_chat":
            prompt = _clamp(int(rng.lognormvariate(5.3, 0.52)), 100, 1_000)
            output = _clamp(int(rng.lognormvariate(6.1, 0.55)), 280, 2_300)
            priority = rng.choices(["interactive", "standard"], [70, 30])[0]
        elif kind == "rag_qa":
            prefix = rng.choice(rag_prefixes)
            prompt = _clamp(int(rng.lognormvariate(7.55, 0.45)), 1_100, 13_000)
            output = _clamp(int(rng.lognormvariate(4.55, 0.55)), 55, 520)
            priority = rng.choices(["interactive", "standard"], [36, 64])[0]
        elif kind == "long_rag":
            prefix = rng.choice(rag_prefixes)
            prompt = _clamp(int(rng.lognormvariate(8.45, 0.42)), 4_500, 24_000)
            output = _clamp(int(rng.lognormvariate(5.05, 0.55)), 110, 950)
            priority = rng.choices(["interactive", "standard", "batch"], [18, 62, 20])[0]
        elif kind == "code":
            if rng.random() < 0.32:
                prefix = rng.choice(code_prefixes)
            prompt = _clamp(int(rng.lognormvariate(5.9, 0.62)), 220, 3_200)
            output = _clamp(int(rng.lognormvariate(5.85, 0.62)), 140, 2_200)
            priority = rng.choices(["interactive", "standard"], [54, 46])[0]
        elif kind == "long_code":
            if rng.random() < 0.44:
                prefix = rng.choice(code_prefixes)
            prompt = _clamp(int(rng.lognormvariate(6.5, 0.55)), 650, 6_500)
            output = _clamp(int(rng.lognormvariate(6.55, 0.58)), 600, 4_200)
            priority = rng.choices(["interactive", "standard"], [38, 62])[0]
        else:
            prefix = rng.choice(rag_prefixes) if rng.random() < 0.52 else None
            prompt = _clamp(int(rng.lognormvariate(7.9, 0.52)), 1_700, 18_000)
            output = _clamp(int(rng.lognormvariate(4.95, 0.52)), 80, 780)
            priority = "batch"

        ttft, itl = _slo_for(priority)
        abandoned = None
        if priority == "interactive" and rng.random() < 0.035:
            abandoned = int(t + rng.randint(1_400, 5_800))
        elif priority == "standard" and rng.random() < 0.02:
            abandoned = int(t + rng.randint(4_500, 18_000))

        out.append(
            TraceRecord(
                request_id=f"profile-{i:05d}",
                arrival_time_ms=int(t),
                prompt_tokens=prompt,
                output_tokens=output,
                tenant_id=f"tenant-{rng.randint(1, 20):02d}",
                priority_class=priority,
                ttft_slo_ms=ttft,
                itl_slo_ms=itl,
                prefix_id=prefix,
                abandoned_at_ms=abandoned,
            )
        )

    return out
