from __future__ import annotations

from .models import PolicyConfig


def policy_suite(policy_tick_ms: int = 50) -> list[PolicyConfig]:
    return [
        PolicyConfig(
            name="continuous_batching",
            scheduler_style="continuous",
            policy_tick_ms=policy_tick_ms,
        ),
        PolicyConfig(
            name="sarathi_chunked_prefill",
            scheduler_style="sarathi",
            policy_tick_ms=policy_tick_ms,
        ),
        PolicyConfig(
            name="distserve_disaggregated",
            scheduler_style="distserve",
            policy_tick_ms=policy_tick_ms,
        ),
        PolicyConfig(
            name="yieldos_lite",
            scheduler_style="yieldos",
            shape_classifier=True,
            kv_treasury=True,
            slo_notary=True,
            policy_tick_ms=policy_tick_ms,
        ),
        yieldos_v02(policy_tick_ms=policy_tick_ms),
    ]


def yieldos_v02(policy_tick_ms: int = 50) -> PolicyConfig:
    return PolicyConfig(
        name=f"yieldos_lite_v02_tick_{policy_tick_ms}ms",
        scheduler_style="yieldos",
        shape_classifier=True,
        kv_treasury=True,
        slo_notary=True,
        fallback_to_baseline=False,
        policy_tick_ms=policy_tick_ms,
        shape_authority="soft",
        probation_ms=250,
        reclass_min_dwell_ms=500,
        reclass_min_confidence_delta=0.18,
        reclass_min_bucket_change=True,
    )


def kv_stress_suite() -> list[PolicyConfig]:
    return [
        PolicyConfig(
            name="distserve_disaggregated",
            scheduler_style="distserve",
        ),
        yieldos_v02(),
        PolicyConfig(
            name="yieldos_v02_lru_kv",
            scheduler_style="yieldos",
            shape_classifier=True,
            kv_treasury=False,
            slo_notary=True,
            fallback_to_baseline=False,
            shape_authority="soft",
            reclass_min_dwell_ms=500,
            reclass_min_confidence_delta=0.18,
            reclass_min_bucket_change=True,
        ),
        PolicyConfig(
            name="yieldos_v02_no_slo_notary",
            scheduler_style="yieldos",
            shape_classifier=True,
            kv_treasury=True,
            slo_notary=False,
            fallback_to_baseline=False,
            shape_authority="soft",
        ),
    ]


def shape_stress_suite() -> list[PolicyConfig]:
    return [
        PolicyConfig(
            name="yieldos_shape_hard",
            scheduler_style="yieldos",
            shape_classifier=True,
            kv_treasury=True,
            slo_notary=True,
            shape_authority="hard",
        ),
        yieldos_v02(),
        PolicyConfig(
            name="yieldos_no_classifier",
            scheduler_style="yieldos",
            shape_classifier=False,
            kv_treasury=True,
            slo_notary=True,
            fallback_to_baseline=False,
            shape_authority="soft",
        ),
        PolicyConfig(
            name="yieldos_oracle_hard",
            scheduler_style="yieldos",
            shape_classifier=True,
            kv_treasury=True,
            slo_notary=True,
            exact_output_oracle=True,
            noisy_forecasts=False,
            shape_authority="hard",
        ),
        PolicyConfig(
            name="yieldos_noisy_hard",
            scheduler_style="yieldos",
            shape_classifier=True,
            kv_treasury=True,
            slo_notary=True,
            noisy_forecasts=True,
            shape_authority="hard",
        ),
    ]


def tick_sweep_suite(ticks: list[int] | None = None) -> list[PolicyConfig]:
    return [yieldos_v02(policy_tick_ms=t) for t in (ticks or [5, 10, 25, 50, 75, 100, 200])]


def ablation_suite() -> list[PolicyConfig]:
    base = PolicyConfig(
        name="yieldos_lite",
        scheduler_style="yieldos",
        shape_classifier=True,
        kv_treasury=True,
        slo_notary=True,
        policy_tick_ms=50,
    )
    return [
        base,
        PolicyConfig(
            name="ablate_no_shape_classifier",
            scheduler_style="yieldos",
            shape_classifier=False,
            kv_treasury=True,
            slo_notary=True,
            policy_tick_ms=50,
        ),
        PolicyConfig(
            name="ablate_lru_kv",
            scheduler_style="yieldos",
            shape_classifier=True,
            kv_treasury=False,
            slo_notary=True,
            policy_tick_ms=50,
        ),
        PolicyConfig(
            name="ablate_no_slo_notary",
            scheduler_style="yieldos",
            shape_classifier=True,
            kv_treasury=True,
            slo_notary=False,
            policy_tick_ms=50,
        ),
        PolicyConfig(
            name="ablate_exact_output_oracle",
            scheduler_style="yieldos",
            shape_classifier=True,
            kv_treasury=True,
            slo_notary=True,
            exact_output_oracle=True,
            noisy_forecasts=False,
            policy_tick_ms=50,
        ),
        PolicyConfig(
            name="ablate_noisy_forecasts",
            scheduler_style="yieldos",
            shape_classifier=True,
            kv_treasury=True,
            slo_notary=True,
            noisy_forecasts=True,
            policy_tick_ms=50,
        ),
        PolicyConfig(
            name="ablate_no_online_reclass",
            scheduler_style="yieldos",
            shape_classifier=True,
            kv_treasury=True,
            slo_notary=True,
            online_reclassification=False,
            policy_tick_ms=50,
        ),
        PolicyConfig(
            name="ablate_policy_tick_1ms",
            scheduler_style="yieldos",
            shape_classifier=True,
            kv_treasury=True,
            slo_notary=True,
            policy_tick_ms=1,
        ),
        PolicyConfig(
            name="ablate_policy_tick_100ms",
            scheduler_style="yieldos",
            shape_classifier=True,
            kv_treasury=True,
            slo_notary=True,
            policy_tick_ms=100,
        ),
        PolicyConfig(
            name="ablate_no_fallback_lane",
            scheduler_style="yieldos",
            shape_classifier=True,
            kv_treasury=True,
            slo_notary=True,
            fallback_to_baseline=False,
            policy_tick_ms=50,
        ),
        yieldos_v02(),
    ]
