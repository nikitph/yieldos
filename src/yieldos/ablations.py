from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from .metrics import write_results
from .models import SimConfig, SimResult, TraceRecord
from .policies import (
    ablation_suite,
    kv_stress_suite,
    policy_suite,
    shape_stress_suite,
    tick_sweep_suite,
    yieldos_v02,
)
from .simulator import run_simulation
from .trace_io import load_burstgpt_trace, load_trace, write_trace_csv
from .workloads import (
    available_profiles,
    generate_kv_heavy_trace,
    generate_mixed_trace,
    generate_profile_trace,
    generate_shape_stress_trace,
)


def run_policy_comparison(requests: int, seed: int, out_dir: Path) -> list[SimResult]:
    trace = generate_mixed_trace(requests=requests, seed=seed)
    config = SimConfig()
    results = [
        run_simulation(trace, policy, config=config, seed=seed)
        for policy in policy_suite()
    ]
    write_results(results, out_dir)
    return results


def run_ablations(requests: int, seed: int, out_dir: Path) -> list[SimResult]:
    trace = generate_mixed_trace(requests=requests, seed=seed)
    config = SimConfig()
    results = [
        run_simulation(trace, policy, config=config, seed=seed)
        for policy in ablation_suite()
    ]
    write_results(results, out_dir)
    return results


def run_kv_stress(requests: int, seed: int, out_dir: Path) -> list[SimResult]:
    trace = generate_kv_heavy_trace(requests=requests, seed=seed, load=1.12)
    config = SimConfig(kv_capacity_tokens=24_000, max_time_ms=700_000)
    results = [
        run_simulation(trace, policy, config=config, seed=seed)
        for policy in kv_stress_suite()
    ]
    write_results(results, out_dir)
    return results


def run_shape_stress(requests: int, seed: int, out_dir: Path) -> list[SimResult]:
    trace = generate_shape_stress_trace(requests=requests, seed=seed, load=1.05)
    config = SimConfig(kv_capacity_tokens=42_000, max_time_ms=700_000)
    results = [
        run_simulation(trace, policy, config=config, seed=seed)
        for policy in shape_stress_suite()
    ]
    write_results(results, out_dir)
    return results


def run_tick_sweep(requests: int, seed: int, out_dir: Path) -> list[SimResult]:
    trace = generate_mixed_trace(requests=requests, seed=seed, load=1.0)
    config = SimConfig()
    results = [
        run_simulation(trace, policy, config=config, seed=seed)
        for policy in tick_sweep_suite()
    ]
    write_results(results, out_dir)
    return results


def run_load_regimes(requests: int, seed: int, out_dir: Path) -> list[SimResult]:
    results: list[SimResult] = []
    policies = [
        replace(yieldos_v02(), name="yieldos_v02"),
        replace(
            yieldos_v02(),
            name="yieldos_v02_lru_kv",
            kv_treasury=False,
        ),
        replace(
            yieldos_v02(),
            name="yieldos_v02_no_slo_notary",
            slo_notary=False,
        ),
        replace(
            yieldos_v02(),
            name="distserve_disaggregated",
            scheduler_style="distserve",
            shape_classifier=False,
            kv_treasury=False,
            slo_notary=False,
            shape_authority="hard",
        ),
    ]
    for load in [0.60, 0.80, 1.00, 1.20, 1.50]:
        trace = generate_mixed_trace(requests=requests, seed=seed, load=load)
        config = SimConfig(max_time_ms=750_000)
        for policy in policies:
            named = replace(policy, name=f"{policy.name}_load_{load:.2f}")
            results.append(run_simulation(trace, named, config=config, seed=seed))
    write_results(results, out_dir)
    return results


def run_load_sweep(requests: int, seed: int, out_dir: Path) -> list[SimResult]:
    results: list[SimResult] = []
    policies = _core_policy_set()
    for load in [0.50, 0.70, 0.90, 1.10, 1.30, 1.50]:
        trace = generate_mixed_trace(requests=requests, seed=seed, load=load)
        config = SimConfig(max_time_ms=750_000)
        for policy in policies:
            named = replace(policy, name=f"{policy.name}_load_{load:.2f}")
            results.append(run_simulation(trace, named, config=config, seed=seed))
    write_results(results, out_dir)
    return results


def run_kv_pressure_sweep(requests: int, seed: int, out_dir: Path) -> list[SimResult]:
    results: list[SimResult] = []
    trace = generate_kv_heavy_trace(requests=requests, seed=seed, load=0.96)
    policies = [
        replace(yieldos_v02(), name="yieldos_v02"),
        replace(yieldos_v02(), name="yieldos_v02_lru_kv", kv_treasury=False),
        replace(
            yieldos_v02(),
            name="distserve_disaggregated",
            scheduler_style="distserve",
            shape_classifier=False,
            kv_treasury=False,
            slo_notary=False,
            shape_authority="hard",
        ),
    ]
    pressure_to_capacity = {
        "low": 96_000,
        "medium": 48_000,
        "high": 24_000,
        "extreme": 12_000,
    }
    for pressure, capacity in pressure_to_capacity.items():
        config = SimConfig(kv_capacity_tokens=capacity, max_time_ms=750_000)
        for policy in policies:
            named = replace(policy, name=f"{policy.name}_kv_{pressure}")
            results.append(run_simulation(trace, named, config=config, seed=seed))
    write_results(results, out_dir)
    return results


def run_slo_tightness_sweep(requests: int, seed: int, out_dir: Path) -> list[SimResult]:
    results: list[SimResult] = []
    base_trace = generate_mixed_trace(requests=requests, seed=seed, load=1.0)
    policies = _core_policy_set()
    regimes = {
        "loose": 1.75,
        "normal": 1.00,
        "tight": 0.65,
        "impossible": 0.35,
    }
    for regime, multiplier in regimes.items():
        trace = _scale_slos(base_trace, multiplier)
        config = SimConfig(max_time_ms=750_000)
        for policy in policies:
            named = replace(policy, name=f"{policy.name}_slo_{regime}")
            results.append(run_simulation(trace, named, config=config, seed=seed))
    write_results(results, out_dir)
    return results


def run_tick_sweep_stress(requests: int, seed: int, out_dir: Path) -> list[SimResult]:
    trace = generate_kv_heavy_trace(requests=requests, seed=seed, load=1.12)
    config = SimConfig(kv_capacity_tokens=24_000, max_time_ms=750_000)
    results = [
        run_simulation(trace, policy, config=config, seed=seed)
        for policy in tick_sweep_suite()
    ]
    write_results(results, out_dir)
    return results


def run_workload_suite(requests: int, seed: int, out_dir: Path) -> list[SimResult]:
    results: list[SimResult] = []
    policies = _core_policy_set()
    trace_dir = out_dir / "traces"
    for profile in available_profiles():
        trace = generate_profile_trace(profile, requests=requests, seed=seed, load=1.0)
        write_trace_csv(trace, trace_dir / f"{profile}.csv")
        config = SimConfig(max_time_ms=750_000)
        for policy in policies:
            named = replace(policy, name=f"{policy.name}_{profile}")
            results.append(run_simulation(trace, named, config=config, seed=seed))
    write_results(results, out_dir)
    return results


def run_replay(trace_path: Path, seed: int, out_dir: Path) -> list[SimResult]:
    trace = load_trace(trace_path)
    policies = _core_policy_set()
    config = SimConfig(max_time_ms=750_000)
    results = [
        run_simulation(trace, replace(policy, name=f"{policy.name}_replay"), config=config, seed=seed)
        for policy in policies
    ]
    write_results(results, out_dir)
    return results


def run_burstgpt_replay(
    source: str,
    limit: int,
    time_scale: float,
    seed: int,
    out_dir: Path,
) -> list[SimResult]:
    trace = load_burstgpt_trace(source, limit=limit, time_scale=time_scale)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_trace_csv(trace, out_dir / "traces" / "burstgpt_sample.csv")
    policies = _core_policy_set()
    config = SimConfig(max_time_ms=750_000)
    results = [
        run_simulation(trace, replace(policy, name=f"{policy.name}_burstgpt"), config=config, seed=seed)
        for policy in policies
    ]
    write_results(results, out_dir)
    return results


def _core_policy_set() -> list:
    return [
        replace(yieldos_v02(), name="yieldos_v02"),
        replace(
            yieldos_v02(),
            name="yieldos_v02_lru_kv",
            kv_treasury=False,
        ),
        replace(
            yieldos_v02(),
            name="yieldos_v02_no_slo_notary",
            slo_notary=False,
        ),
        replace(
            yieldos_v02(),
            name="distserve_disaggregated",
            scheduler_style="distserve",
            shape_classifier=False,
            kv_treasury=False,
            slo_notary=False,
            shape_authority="hard",
        ),
    ]


def _scale_slos(trace: list[TraceRecord], multiplier: float) -> list[TraceRecord]:
    return [
        replace(
            record,
            ttft_slo_ms=max(1, int(record.ttft_slo_ms * multiplier)),
            itl_slo_ms=max(1, int(record.itl_slo_ms * multiplier)),
        )
        for record in trace
    ]
