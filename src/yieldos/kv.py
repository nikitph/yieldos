from __future__ import annotations

from collections.abc import Iterable

from .models import KVEntry, RequestState


class KVTreasury:
    def __init__(self, capacity_tokens: int, value_aware: bool = True) -> None:
        self.capacity_tokens = capacity_tokens
        self.value_aware = value_aware
        self.entries: dict[str, KVEntry] = {}
        self.prefix_use_counts: dict[str, int] = {}
        self.current_tokens = 0
        self.hit_tokens = 0
        self.value_preserved = 0.0
        self.recompute_waste = 0.0
        self.evictions = 0

    def lookup_prefix(self, req: RequestState, now_ms: int) -> int:
        prefix_id = req.trace.prefix_id
        if prefix_id is None:
            return 0
        self.prefix_use_counts[prefix_id] = self.prefix_use_counts.get(prefix_id, 0) + 1
        entry = self.entries.get(prefix_id)
        if entry is None:
            return 0
        entry.last_used_ms = now_ms
        entry.expected_future_use *= 1.08
        saved = min(req.trace.prompt_tokens, entry.size_tokens)
        self.hit_tokens += saved
        self.value_preserved += (
            saved
            * max(1.0, entry.slo_pressure)
            * max(0.1, entry.tenant_priority)
            * max(0.1, entry.expected_future_use)
            * max(0.1, entry.sharing_potential)
        )
        return saved

    def admit_sequence(self, req: RequestState, now_ms: int, active: Iterable[RequestState]) -> None:
        prefix_id = req.trace.prefix_id
        if prefix_id is None:
            return
        historical_use = self.prefix_use_counts.get(prefix_id, 0)
        size = min(req.trace.prompt_tokens, max(128, int(req.trace.prompt_tokens * 0.72)))
        expected_future_use = 1.0 + min(4.0, historical_use * 0.75)
        sharing_potential = 1.5 + min(2.5, historical_use * 0.35) if req.shape and req.shape.cacheability == "high" else 0.65
        value_density = self._score(req, size, expected_future_use, sharing_potential, now_ms)
        old = self.entries.get(prefix_id)
        if old is not None:
            self.current_tokens -= old.size_tokens
        self.entries[prefix_id] = KVEntry(
            prefix_id=prefix_id,
            owner_request_id=req.request_id,
            size_tokens=size,
            recompute_cost=float(size),
            expected_future_use=expected_future_use,
            slo_pressure=_slo_pressure(req, now_ms),
            tenant_priority=req.priority_weight,
            sharing_potential=sharing_potential,
            value_density=value_density,
            last_used_ms=now_ms,
        )
        self.current_tokens += size
        self._evict_until_fit(now_ms, active)

    def grow_active_kv(self, req: RequestState, amount: int, now_ms: int, active: Iterable[RequestState]) -> None:
        req.kv_tokens += amount
        self.current_tokens += amount
        self._evict_until_fit(now_ms, active)

    def release_active_kv(self, req: RequestState) -> None:
        if req.kv_tokens <= 0:
            return
        self.current_tokens = max(0, self.current_tokens - req.kv_tokens)
        req.kv_tokens = 0

    def _evict_until_fit(self, now_ms: int, active: Iterable[RequestState]) -> None:
        protected_prefixes = {
            r.trace.prefix_id
            for r in active
            if r.trace.prefix_id and not r.done and (r.protected_decode or r.trace.priority_class == "interactive")
        }
        while self.current_tokens > self.capacity_tokens and self.entries:
            candidates = [e for e in self.entries.values() if e.prefix_id not in protected_prefixes]
            if not candidates:
                candidates = list(self.entries.values())
            if self.value_aware:
                victim = min(
                    candidates,
                    key=lambda e: (e.value_density, -max(0, now_ms - e.last_used_ms)),
                )
            else:
                victim = min(candidates, key=lambda e: e.last_used_ms)
            self.current_tokens -= victim.size_tokens
            self.recompute_waste += victim.recompute_cost * max(0.0, victim.expected_future_use)
            self.evictions += 1
            del self.entries[victim.prefix_id]

    def _score(
        self,
        req: RequestState,
        size: int,
        expected_future_use: float,
        sharing_potential: float,
        now_ms: int,
    ) -> float:
        return (
            max(1.0, size)
            * expected_future_use
            * sharing_potential
            * _slo_pressure(req, now_ms)
            * req.priority_weight
        ) / max(1.0, size)


def _slo_pressure(req: RequestState, now_ms: int) -> float:
    elapsed = max(0, now_ms - req.trace.arrival_time_ms)
    if req.first_token_ms is None:
        slack = req.trace.ttft_slo_ms - elapsed
        return 1.0 + max(0.0, 1.0 - slack / max(1, req.trace.ttft_slo_ms))
    if req.last_token_ms is None:
        return 1.0
    itl_slack = req.trace.itl_slo_ms - (now_ms - req.last_token_ms)
    return 1.0 + max(0.0, 1.0 - itl_slack / max(1, req.trace.itl_slo_ms))
