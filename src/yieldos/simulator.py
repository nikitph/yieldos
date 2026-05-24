from __future__ import annotations

import copy
import random
from dataclasses import asdict

from .classifier import classify_request
from .kv import KVTreasury
from .metrics import compute_metrics
from .models import Decision, Forecast, PolicyConfig, RequestShape, RequestState, SimConfig, SimResult, TraceRecord
from .slo import update_slo_notary


def run_simulation(
    trace: list[TraceRecord],
    policy: PolicyConfig,
    config: SimConfig | None = None,
    seed: int = 7,
) -> SimResult:
    config = copy.copy(config or SimConfig())
    config.slow_policy_tick_ms = policy.policy_tick_ms
    stable_policy_offset = _policy_rng_offset(policy)
    rng = random.Random(seed + stable_policy_offset)
    states = [RequestState(trace=r, prefill_remaining=float(r.prompt_tokens), output_remaining=r.output_tokens) for r in trace]
    arrivals = sorted(states, key=lambda r: r.trace.arrival_time_ms)
    waiting: list[RequestState] = []
    active: list[RequestState] = []
    done: list[RequestState] = []
    decisions: list[Decision] = []
    kv = KVTreasury(config.kv_capacity_tokens, value_aware=policy.kv_treasury)
    now = 0
    next_arrival_idx = 0
    next_policy_tick = 0
    scheduler_overhead_ms = 0.0
    protective_mode_until = -1

    while now <= config.max_time_ms:
        while next_arrival_idx < len(arrivals) and arrivals[next_arrival_idx].trace.arrival_time_ms <= now:
            req = arrivals[next_arrival_idx]
            req.arrival_seen_ms = now
            if policy.shape_classifier:
                req.shape = classify_request(req.trace, policy, rng)
            else:
                req.shape = RequestShape(
                    output_forecast=Forecast(
                        p50=256,
                        p90=900,
                        p99=1_800,
                        bucket="unknown",
                        confidence=0.30,
                    ),
                    phase_profile="balanced",
                    cacheability="low",
                    latency_class=req.trace.priority_class,
                    memory_risk="medium",
                    routing_class="baseline_conservative",
                    fallback_to_baseline=True,
                )
            saved = kv.lookup_prefix(req, now)
            if saved:
                req.cache_hit_tokens = saved
                req.prefill_remaining = max(1.0, req.prefill_remaining - saved * 0.78)
                decisions.append(
                    Decision(
                        now,
                        req.request_id,
                        "kv_prefix_hit",
                        {"saved_tokens": saved, "prefix_id": req.trace.prefix_id},
                    )
                )
            waiting.append(req)
            next_arrival_idx += 1

        for req in waiting + active:
            if req.trace.abandoned_at_ms is not None and now >= req.trace.abandoned_at_ms and not req.done:
                req.abandoned = True
                req.done = False
                req.finish_ms = now
                kv.release_active_kv(req)
                decisions.append(Decision(now, req.request_id, "abandoned", {}))

        waiting = [r for r in waiting if not r.abandoned]
        active = [r for r in active if not r.abandoned]

        policy_updates = 0
        while now >= next_policy_tick:
            scheduler_overhead_ms += config.control_overhead_ms * max(1, len(waiting) + len(active)) / 20.0
            policy_updates += 1
            next_policy_tick += max(1, policy.policy_tick_ms)
        if policy_updates:
            queue_depth = len(waiting) + len(active)
            if policy.slo_notary:
                high_risk = 0
                for req in active + waiting:
                    action = update_slo_notary(req, now, queue_depth)
                    if action != "none":
                        high_risk += 1
                        decisions.append(
                            Decision(
                                now,
                                req.request_id,
                                "slo_notary",
                                {"action": action, "breach_probability": round(req.breach_probability, 3)},
                            )
                        )
                if high_risk >= max(4, queue_depth // 8):
                    protective_mode_until = now + 3 * config.tick_ms
                    decisions.append(Decision(now, "cluster", "protective_mode", {"high_risk": high_risk}))
            if policy.shape_classifier and policy.online_reclassification:
                for req in active:
                    if _should_reclassify(req, policy, now):
                        old_shape = req.shape
                        new_shape = classify_request(req.trace, policy, rng, req.output_done)
                        if _accept_reclassification(old_shape, new_shape, policy):
                            req.shape = new_shape
                            req.last_reclass_ms = now
                            req.reclass_count += 1
                            decisions.append(
                                Decision(
                                    now,
                                    req.request_id,
                                    "reclassify",
                                    {
                                        "old_route": old_shape.routing_class if old_shape else "unknown",
                                        "new_route": new_shape.routing_class,
                                        "confidence": round(new_shape.output_forecast.confidence, 3),
                                    },
                                )
                            )

        newly_admitted = _admit_waiting(waiting, active, policy, config, now, protective_mode_until)
        for req in newly_admitted:
            decisions.append(
                Decision(
                    now,
                    req.request_id,
                    "admit",
                    {"route": req.shape.routing_class if req.shape else "unknown"},
                )
            )

        if policy.scheduler_style == "continuous":
            _tick_continuous(active, config, now, kv)
        elif policy.scheduler_style == "sarathi":
            _tick_sarathi(active, config, now, kv)
        elif policy.scheduler_style == "distserve":
            _tick_distserve(active, config, now, kv)
        else:
            _tick_yieldos(active, policy, config, now, kv, protective_mode_until)

        still_active: list[RequestState] = []
        for req in active:
            if req.output_remaining <= 0:
                req.done = True
                req.finish_ms = now
                kv.release_active_kv(req)
                kv.admit_sequence(req, now, active)
                done.append(req)
                decisions.append(Decision(now, req.request_id, "complete", {"tokens": req.output_done}))
            else:
                still_active.append(req)
        active = still_active

        if len(done) + sum(1 for r in states if r.abandoned) >= len(states):
            break
        if next_arrival_idx >= len(arrivals) and not waiting and not active:
            break
        now += config.tick_ms

    finish_time = max((r.finish_ms or now for r in states), default=now)
    metrics = compute_metrics(
        policy.name,
        states,
        finish_time,
        scheduler_overhead_ms,
        kv.hit_tokens,
        kv.value_preserved,
        kv.recompute_waste,
    )
    return SimResult(metrics=metrics, requests=states, decisions=decisions, kv_entries=list(kv.entries.values()))


def _policy_rng_offset(policy: PolicyConfig) -> int:
    fields = asdict(policy)
    fields.pop("name", None)
    signature = repr(sorted(fields.items()))
    return sum((i + 1) * ord(ch) for i, ch in enumerate(signature)) % 10_000


def _admit_waiting(
    waiting: list[RequestState],
    active: list[RequestState],
    policy: PolicyConfig,
    config: SimConfig,
    now: int,
    protective_mode_until: int,
) -> list[RequestState]:
    if not waiting:
        return []
    max_active = 96 if policy.scheduler_style in {"distserve", "yieldos"} else 78
    slots = max(0, max_active - len(active))
    if slots <= 0:
        return []

    def rank(req: RequestState) -> tuple[float, int]:
        age = now - req.trace.arrival_time_ms
        route = req.shape.routing_class if req.shape else "balanced"
        score = age * 0.002 + req.priority_weight
        if policy.scheduler_style == "yieldos":
            if req.slo_action != "none":
                score += 5.0
            if policy.shape_authority == "soft":
                score += _shape_soft_score(req)
            else:
                if route == "low_latency_decode":
                    score += 2.4
                elif route == "decode_residency_protected":
                    score += 1.6
                elif route == "opportunistic_throughput":
                    score -= 1.5
                elif route == "baseline_conservative" and policy.fallback_to_baseline:
                    score -= 0.5
            if now < protective_mode_until and req.trace.prompt_tokens > 4_000:
                score -= 4.0
        return (-score, req.trace.arrival_time_ms)

    waiting.sort(key=rank)
    admitted: list[RequestState] = []
    for req in list(waiting):
        if len(admitted) >= slots:
            break
        if (
            policy.scheduler_style == "yieldos"
            and now < protective_mode_until
            and req.trace.prompt_tokens > 8_000
            and req.trace.priority_class != "interactive"
            and policy.shape_authority == "hard"
        ):
            continue
        waiting.remove(req)
        req.admitted_ms = now
        req.queue = "active"
        active.append(req)
        admitted.append(req)
    return admitted


def _prefill_ready(req: RequestState) -> bool:
    return req.prefill_remaining <= 0


def _emit_decode(req: RequestState, now: int, kv: KVTreasury, active: list[RequestState]) -> None:
    if req.output_remaining <= 0:
        return
    if req.first_token_ms is None:
        req.first_token_ms = now
    if req.last_token_ms is not None:
        req.max_itl_ms = max(req.max_itl_ms, now - req.last_token_ms)
    req.last_token_ms = now
    req.output_done += 1
    req.output_remaining -= 1
    kv.grow_active_kv(req, 1, now, active)


def _run_prefill(req: RequestState, amount: float, now: int) -> float:
    used = min(amount, req.prefill_remaining)
    req.prefill_remaining -= used
    if req.prefill_remaining <= 0 and req.prefill_done_ms is None:
        req.prefill_done_ms = now
    return used


def _tick_continuous(active: list[RequestState], config: SimConfig, now: int, kv: KVTreasury) -> None:
    budget = float(config.unified_tokens_per_tick)
    for req in sorted(active, key=lambda r: (r.trace.arrival_time_ms, -r.priority_weight)):
        if budget <= 0:
            break
        if not _prefill_ready(req):
            budget -= _run_prefill(req, min(budget, config.prefill_chunk_tokens * 2), now)
    decode_budget = int(max(0, budget // 3))
    for req in sorted((r for r in active if _prefill_ready(r)), key=lambda r: r.trace.arrival_time_ms):
        if decode_budget <= 0:
            break
        _emit_decode(req, now, kv, active)
        decode_budget -= 1


def _tick_sarathi(active: list[RequestState], config: SimConfig, now: int, kv: KVTreasury) -> None:
    decode_budget = config.decode_tokens_per_tick
    for req in sorted((r for r in active if _prefill_ready(r)), key=lambda r: (r.trace.priority_class != "interactive", r.trace.arrival_time_ms)):
        if decode_budget <= 0:
            break
        _emit_decode(req, now, kv, active)
        decode_budget -= 1
    prefill_budget = config.prefill_tokens_per_tick
    for req in sorted((r for r in active if not _prefill_ready(r)), key=lambda r: r.trace.arrival_time_ms):
        if prefill_budget <= 0:
            break
        prefill_budget -= _run_prefill(req, min(prefill_budget, config.prefill_chunk_tokens), now)


def _tick_distserve(active: list[RequestState], config: SimConfig, now: int, kv: KVTreasury) -> None:
    prefill_budget = int(config.prefill_tokens_per_tick * 1.12)
    decode_budget = int(config.decode_tokens_per_tick * 1.10)
    for req in sorted((r for r in active if not _prefill_ready(r)), key=lambda r: (r.trace.priority_class == "batch", r.trace.arrival_time_ms)):
        if prefill_budget <= 0:
            break
        prefill_budget -= _run_prefill(req, min(prefill_budget, config.prefill_chunk_tokens * 2), now)
    for req in sorted((r for r in active if _prefill_ready(r)), key=lambda r: (r.trace.priority_class != "interactive", r.trace.arrival_time_ms)):
        if decode_budget <= 0:
            break
        _emit_decode(req, now, kv, active)
        decode_budget -= 1


def _tick_yieldos(
    active: list[RequestState],
    policy: PolicyConfig,
    config: SimConfig,
    now: int,
    kv: KVTreasury,
    protective_mode_until: int,
) -> None:
    decode_budget = int(config.decode_tokens_per_tick * 1.10)
    prefill_budget = int(config.prefill_tokens_per_tick * 1.12)
    reserve = max(5, decode_budget // 9) if now < protective_mode_until else max(2, decode_budget // 18)
    protected = [r for r in active if _prefill_ready(r) and (r.protected_decode or r.trace.priority_class == "interactive")]
    ordinary = [r for r in active if _prefill_ready(r) and r not in protected]
    protected.sort(key=lambda r: (-r.breach_probability, r.trace.arrival_time_ms))
    ordinary.sort(key=lambda r: _decode_rank(r, now, policy))

    protected_limit = int(decode_budget * (0.68 if now < protective_mode_until else 0.56))
    protected_used = 0
    for req in protected:
        if decode_budget <= reserve or protected_used >= protected_limit:
            break
        _emit_decode(req, now, kv, active)
        decode_budget -= 1
        protected_used += 1

    candidates = [r for r in active if not _prefill_ready(r)]
    candidates.sort(key=lambda r: _prefill_rank(r, now, protective_mode_until, policy))
    for req in candidates:
        if prefill_budget <= 0:
            break
        route = _effective_route(req, hard=policy.shape_authority == "hard")
        chunk = config.prefill_chunk_tokens
        if policy.shape_authority == "hard":
            if route == "chunked_prefill":
                chunk = int(config.prefill_chunk_tokens * 0.65)
            elif route == "low_latency_decode":
                chunk = int(config.prefill_chunk_tokens * 1.1)
            elif route == "opportunistic_throughput" and now < protective_mode_until:
                chunk = int(config.prefill_chunk_tokens * 0.35)
        elif now < protective_mode_until and req.trace.priority_class == "batch":
            chunk = int(config.prefill_chunk_tokens * 0.65)
        prefill_budget -= _run_prefill(req, min(prefill_budget, chunk), now)

    for req in ordinary:
        if decode_budget <= 0:
            break
        _emit_decode(req, now, kv, active)
        decode_budget -= 1


def _decode_rank(req: RequestState, now: int, policy: PolicyConfig) -> tuple[float, int]:
    since_last = now - (req.last_token_ms or req.prefill_done_ms or now)
    route = _effective_route(req, hard=policy.shape_authority == "hard")
    score = req.priority_weight + since_last / max(1, req.trace.itl_slo_ms)
    if policy.shape_authority == "soft":
        score += _shape_soft_score(req) * 0.6
    else:
        if route == "decode_residency_protected":
            score += 1.8
        if route == "opportunistic_throughput":
            score -= 0.8
    return (-score, req.trace.arrival_time_ms)


def _prefill_rank(
    req: RequestState,
    now: int,
    protective_mode_until: int,
    policy: PolicyConfig,
) -> tuple[float, int]:
    route = _effective_route(req, hard=policy.shape_authority == "hard")
    age = now - req.trace.arrival_time_ms
    score = req.priority_weight + age * 0.001
    if policy.shape_authority == "soft":
        score += _shape_soft_score(req)
    else:
        if route == "chunked_prefill":
            score += 1.0
        if route == "prefix_cache":
            score += 0.7
    if req.slo_action in {"boost_priority", "stop_large_prefill_admission"}:
        score += 3.0
    if req.trace.priority_class == "interactive" and req.first_token_ms is None:
        elapsed = now - req.trace.arrival_time_ms
        score += min(2.4, elapsed / max(1, req.trace.ttft_slo_ms))
    if route == "opportunistic_throughput":
        score -= 1.2
    if now < protective_mode_until and req.trace.prompt_tokens > 4_000:
        score -= 2.5
    return (-score, req.trace.arrival_time_ms)


def _effective_route(req: RequestState, hard: bool) -> str:
    if req.shape is None:
        return "balanced"
    if hard:
        return req.shape.routing_class
    if req.shape.routing_class == "baseline_conservative":
        return "balanced"
    return req.shape.routing_class


def _shape_soft_score(req: RequestState) -> float:
    if req.shape is None:
        return 0.0
    forecast = req.shape.output_forecast
    score = 0.0
    if req.shape.phase_profile == "prefill_heavy":
        score += 0.35
    if req.shape.phase_profile == "decode_heavy":
        score += 0.25
    if req.shape.cacheability == "high":
        score += 0.25
    if forecast.confidence < 0.45:
        score -= 0.15
    return score


def _should_reclassify(req: RequestState, policy: PolicyConfig, now: int) -> bool:
    if req.done or req.output_done == 0 or req.output_done % 160 != 0:
        return False
    if policy.reclass_min_dwell_ms and req.last_reclass_ms is not None:
        if now - req.last_reclass_ms < policy.reclass_min_dwell_ms:
            return False
    return True


def _accept_reclassification(
    old_shape: RequestShape | None,
    new_shape: RequestShape,
    policy: PolicyConfig,
) -> bool:
    if old_shape is None:
        return True
    old_forecast = old_shape.output_forecast
    new_forecast = new_shape.output_forecast
    if policy.reclass_min_bucket_change and old_forecast.bucket == new_forecast.bucket:
        return False
    confidence_delta = abs(new_forecast.confidence - old_forecast.confidence)
    if confidence_delta < policy.reclass_min_confidence_delta and old_shape.routing_class == new_shape.routing_class:
        return False
    return True
