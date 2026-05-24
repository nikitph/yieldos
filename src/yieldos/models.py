from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


PriorityClass = str
PolicyName = str


@dataclass(frozen=True)
class TraceRecord:
    request_id: str
    arrival_time_ms: int
    prompt_tokens: int
    output_tokens: int
    tenant_id: str
    priority_class: PriorityClass
    ttft_slo_ms: int
    itl_slo_ms: int
    prefix_id: str | None = None
    abandoned_at_ms: int | None = None


@dataclass
class Forecast:
    p50: int
    p90: int
    p99: int
    bucket: str
    confidence: float


@dataclass
class RequestShape:
    output_forecast: Forecast
    phase_profile: str
    cacheability: str
    latency_class: str
    memory_risk: str
    routing_class: str
    fallback_to_baseline: bool = False


@dataclass
class RequestState:
    trace: TraceRecord
    shape: RequestShape | None = None
    arrival_seen_ms: int | None = None
    admitted_ms: int | None = None
    prefill_done_ms: int | None = None
    first_token_ms: int | None = None
    finish_ms: int | None = None
    prefill_remaining: float = 0.0
    output_remaining: int = 0
    output_done: int = 0
    last_token_ms: int | None = None
    max_itl_ms: int = 0
    queue: str = "pending"
    done: bool = False
    abandoned: bool = False
    slo_action: str = "none"
    breach_probability: float = 0.0
    protected_decode: bool = False
    kv_tokens: int = 0
    kv_recompute_tokens: float = 0.0
    cache_hit_tokens: int = 0
    last_reclass_ms: int | None = None
    reclass_count: int = 0

    @property
    def request_id(self) -> str:
        return self.trace.request_id

    @property
    def priority_weight(self) -> float:
        return {"interactive": 3.0, "standard": 1.5, "batch": 0.6}.get(
            self.trace.priority_class, 1.0
        )

    @property
    def ttft_ms(self) -> int | None:
        if self.first_token_ms is None:
            return None
        return self.first_token_ms - self.trace.arrival_time_ms

    @property
    def completed_output_tokens(self) -> int:
        return self.output_done


@dataclass
class SimConfig:
    tick_ms: int = 25
    max_time_ms: int = 600_000
    prefill_tokens_per_tick: int = 420
    decode_tokens_per_tick: int = 64
    unified_tokens_per_tick: int = 520
    kv_capacity_tokens: int = 62_000
    slow_policy_tick_ms: int = 50
    prefill_chunk_tokens: int = 768
    control_overhead_ms: float = 0.18
    fallback_enabled: bool = True


@dataclass(frozen=True)
class PolicyConfig:
    name: PolicyName
    shape_classifier: bool = False
    kv_treasury: bool = False
    slo_notary: bool = False
    exact_output_oracle: bool = False
    noisy_forecasts: bool = True
    online_reclassification: bool = True
    fallback_to_baseline: bool = True
    policy_tick_ms: int = 50
    scheduler_style: str = "continuous"
    shape_authority: str = "hard"
    probation_ms: int = 0
    reclass_min_dwell_ms: int = 0
    reclass_min_confidence_delta: float = 0.0
    reclass_min_bucket_change: bool = False


@dataclass
class KVEntry:
    prefix_id: str
    owner_request_id: str
    size_tokens: int
    recompute_cost: float
    expected_future_use: float
    slo_pressure: float
    tenant_priority: float
    sharing_potential: float
    value_density: float
    last_used_ms: int


@dataclass
class Decision:
    time_ms: int
    request_id: str
    kind: str
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass
class Metrics:
    policy: str
    requests: int
    obligation_heterogeneity_index: float
    completed: int
    abandoned: int
    slo_attainment: float
    governed_goodput: float
    raw_tokens_per_gpu_second: float
    ttft_p50: float
    ttft_p95: float
    ttft_p99: float
    itl_p50: float
    itl_p95: float
    itl_p99: float
    kv_hit_tokens: int
    kv_value_preserved: float
    kv_recompute_waste: float
    scheduler_overhead_ms: float
    finish_time_ms: int


@dataclass
class SimResult:
    metrics: Metrics
    requests: list[RequestState]
    decisions: list[Decision]
    kv_entries: list[KVEntry]
