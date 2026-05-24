from __future__ import annotations

import argparse
from pathlib import Path

from .analysis import write_ohi_gain_report
from .ablations import (
    run_ablations,
    run_burstgpt_replay,
    run_kv_stress,
    run_kv_pressure_sweep,
    run_load_sweep,
    run_load_regimes,
    run_policy_comparison,
    run_replay,
    run_shape_stress,
    run_slo_tightness_sweep,
    run_tick_sweep,
    run_tick_sweep_stress,
    run_workload_suite,
)


def main() -> None:
    parser = argparse.ArgumentParser(prog="yieldos")
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in (
        "run",
        "ablate",
        "kv-stress",
        "shape-stress",
        "tick-sweep",
        "tick-sweep-stress",
        "load-regimes",
        "load-sweep",
        "kv-pressure-sweep",
        "slo-tightness-sweep",
        "workload-suite",
    ):
        p = sub.add_parser(name)
        p.add_argument("--requests", type=int, default=800)
        p.add_argument("--seed", type=int, default=7)
        p.add_argument("--out", type=Path, required=True)
    replay = sub.add_parser("replay")
    replay.add_argument("--trace", type=Path, required=True)
    replay.add_argument("--seed", type=int, default=7)
    replay.add_argument("--out", type=Path, required=True)
    burstgpt = sub.add_parser("burstgpt-replay")
    burstgpt.add_argument("--source", required=True)
    burstgpt.add_argument("--limit", type=int, default=800)
    burstgpt.add_argument("--time-scale", type=float, default=20.0)
    burstgpt.add_argument("--seed", type=int, default=7)
    burstgpt.add_argument("--out", type=Path, required=True)
    ohi = sub.add_parser("ohi-analysis")
    ohi.add_argument("--workload-summary", type=Path, required=True)
    ohi.add_argument("--burstgpt-summary", type=Path, required=True)
    ohi.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    if args.cmd == "run":
        results = run_policy_comparison(args.requests, args.seed, args.out)
    elif args.cmd == "ablate":
        results = run_ablations(args.requests, args.seed, args.out)
    elif args.cmd == "kv-stress":
        results = run_kv_stress(args.requests, args.seed, args.out)
    elif args.cmd == "shape-stress":
        results = run_shape_stress(args.requests, args.seed, args.out)
    elif args.cmd == "tick-sweep":
        results = run_tick_sweep(args.requests, args.seed, args.out)
    elif args.cmd == "tick-sweep-stress":
        results = run_tick_sweep_stress(args.requests, args.seed, args.out)
    elif args.cmd == "load-sweep":
        results = run_load_sweep(args.requests, args.seed, args.out)
    elif args.cmd == "kv-pressure-sweep":
        results = run_kv_pressure_sweep(args.requests, args.seed, args.out)
    elif args.cmd == "slo-tightness-sweep":
        results = run_slo_tightness_sweep(args.requests, args.seed, args.out)
    elif args.cmd == "workload-suite":
        results = run_workload_suite(args.requests, args.seed, args.out)
    elif args.cmd == "replay":
        results = run_replay(args.trace, args.seed, args.out)
    elif args.cmd == "burstgpt-replay":
        results = run_burstgpt_replay(args.source, args.limit, args.time_scale, args.seed, args.out)
    elif args.cmd == "ohi-analysis":
        write_ohi_gain_report(args.workload_summary, args.burstgpt_summary, args.out)
        print(f"wrote {args.out}")
        return
    else:
        results = run_load_regimes(args.requests, args.seed, args.out)

    best = max(results, key=lambda r: r.metrics.governed_goodput)
    print(f"wrote {args.out}")
    print(f"best={best.metrics.policy} governed_goodput={best.metrics.governed_goodput:.2f}")


if __name__ == "__main__":
    main()
