# YieldOS-Lite MVP Simulator

YieldOS-Lite is a Phase 1 research artifact for asking one question:

> When LLM inference workloads become heterogeneous, does a slow-path
> resource-governance control plane improve SLO-valid work over mechanistic
> schedulers such as continuous batching, chunked prefill, and prefill/decode
> disaggregation?

This repository contains the simulator, paper draft, generated figures,
experiment summaries, replay traces, and tests used to explore that question.
It is meant to be easy to read cold: start with this README, skim the paper,
run the smoke tests, then reproduce or extend the trace-driven experiments.

📄 **Read the paper:** [`paper/yieldos_lite_resource_governance_paper.pdf`](paper/yieldos_lite_resource_governance_paper.pdf)

## What This Is

YieldOS-Lite is a dependency-free trace simulator for LLM inference resource
governance. It models control-plane choices: SLO urgency, KV-cache value,
shape forecasts, policy cadence, and admission/dispatch decisions.

It is not a production serving engine. It does not implement CUDA kernels,
PagedAttention, TensorRT-LLM, or a real vLLM scheduler. The goal is to test
whether governance policies are promising before integrating with real engines.

The current takeaway is:

> YieldOS-Lite is not a better queue; it is a better response to workload
> heterogeneity.

## Where To Start

| If you want to... | Start here |
|---|---|
| Understand the research claim | [`paper/yieldos_lite_resource_governance_paper.pdf`](paper/yieldos_lite_resource_governance_paper.pdf) |
| Inspect the LaTeX source | [`paper/yieldos_lite_resource_governance_paper.tex`](paper/yieldos_lite_resource_governance_paper.tex) |
| Run the simulator | See [Quick Start](#quick-start) |
| Understand trace replay | [`docs/trace_format.md`](docs/trace_format.md) |
| See evaluation structure | [`docs/evaluation_outline.md`](docs/evaluation_outline.md) |
| Inspect headline results | `runs/*/summary.json`, `runs/*/summary.csv`, and `runs/*/report.md` |
| Modify policies | [`src/yieldos/policies.py`](src/yieldos/policies.py) |
| Modify the simulator loop | [`src/yieldos/simulator.py`](src/yieldos/simulator.py) |
| Regenerate paper figures | [`scripts/generate_paper_figures.py`](scripts/generate_paper_figures.py) |

## Repository Map

```text
README.md                         repo orientation and result summary
pyproject.toml                     package metadata
src/yieldos/                       simulator, policies, workloads, metrics
tests/                            smoke tests
docs/                             trace schema and evaluation outline
paper/                            LaTeX paper, compiled PDF, generated figures
scripts/generate_paper_figures.py figure generation from run summaries
runs/                             compact experiment outputs and replay traces
```

The committed `runs/` files intentionally include summaries, reports, and small
replay traces. Large per-policy decision logs (`*_decisions.jsonl`) are ignored
because they can make the working directory several gigabytes.

## Core Concepts

- **Governed goodput:** SLO-valid completed output tokens per simulated
  GPU-second, net of control-plane overhead.
- **SLO Notary:** predictive SLO governance that turns future breach risk into
  present scheduling pressure.
- **KV Treasury:** value-aware KV accounting that scores cache residency by
  expected utility, not raw hit count alone.
- **Shape forecast:** advisory request-shape evidence. It is not treated as a
  validated hard-routing authority.
- **Policy snapshot:** slow-path governance output consumed by a simple fast
  dispatch loop.
- **Obligation Heterogeneity Index (OHI):** coarse diagnostic for when
  governance should help.

## What To Believe

The evidence currently supports:

1. Resource governance is a promising research direction for heterogeneous LLM
   inference workloads.
2. YieldOS-Lite is runnable today as a simulator and trace-replay scaffold.
3. Predictive SLO governance is the strongest validated primitive in this MVP.
4. Value-aware KV accounting is promising under pressure, especially when
   evaluated by value preserved rather than raw hit rate.
5. Shape classification should remain advisory until better calibrated.

The evidence does not yet claim:

1. Production readiness.
2. CUDA-level serving speedup.
3. Direct replacement for vLLM, TensorRT-LLM, Sarathi-Serve, or DistServe.
4. Production GPU utilization gains on real deployment traces.
5. Universal dominance over disaggregated serving.

It implements:

- Synthetic heterogeneous trace generation.
- vLLM-style continuous batching baseline.
- Sarathi-style chunked-prefill baseline.
- DistServe-style prefill/decode-disaggregated baseline.
- YieldOS-Lite policy with:
  - probabilistic shape classification,
  - coarse value-aware KV Treasury,
  - predictive SLO Notary interventions,
  - governed-goodput metrics,
  - trace archive and decision logs.
- MVP ablations from the paper.

## Current Research Status

YieldOS-Lite is currently a Phase 1 control-plane simulator, not a production
serving engine.

The current evidence supports:

1. Predictive SLO governance is P1-ready.
2. Value-aware KV accounting is promising under KV pressure, especially when
   evaluated by value preserved rather than raw hit rate.
3. Shape classification should remain advisory; hard routing is not yet
   validated.
4. The largest observed gains appear in heterogeneous workloads such as
   RAG-heavy, code-heavy, batch-summary-heavy, and mixed-enterprise traffic.

The current evidence does not yet claim:

1. CUDA-level serving improvement.
2. Direct vLLM/TensorRT-LLM replacement.
3. Production GPU utilization gains on real traces.
4. Shape classification as a validated routing authority.

## Quick Start

Use Python 3.11+.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

Run a baseline comparison:

```bash
python -m yieldos.cli run --requests 800 --seed 7 --out runs/demo
```

Run the main experiment families:

```bash
python -m yieldos.cli ablate --requests 800 --seed 7 --out runs/ablations
python -m yieldos.cli workload-suite --requests 800 --seed 41 --out runs/workload_suite
python -m yieldos.cli replay --trace runs/workload_suite/traces/chat_heavy.csv --out runs/replay_chat
```

Run tests:

```bash
python -m unittest discover -s tests
```

The commands write `summary.csv`, `summary.json`, per-policy decision logs, and
a human-readable `report.md`.

Trace replay format is documented in `docs/trace_format.md`.

Figure regeneration requires `matplotlib`:

```bash
python -m pip install matplotlib
python scripts/generate_paper_figures.py
```

## Completed Runs

I ran the MVP comparison and ablation suite with `--requests 800 --seed 7`.

- Baseline comparison: `runs/final_compare_800/`
- MVP ablations: `runs/final_ablations_800/`

Headline comparison from the final run:

| policy | governed goodput | SLO attainment | TTFT p95 | ITL p95 |
|---|---:|---:|---:|---:|
| YieldOS-Lite | 486.41 | 0.274 | 30163.0 ms | 325.0 ms |
| DistServe-style | 401.63 | 0.258 | 32658.0 ms | 325.0 ms |
| Sarathi-style | 126.64 | 0.076 | 39016.6 ms | 905.0 ms |
| Continuous batching | 40.15 | 0.033 | 49318.0 ms | 625.0 ms |

The strongest ablation signal was SLO Notary removal, which dropped governed
goodput from 486.41 to 337.82 tokens/GPU-second. KV Treasury beat LRU on this
seed on governed goodput and recompute waste. A couple of control ablations
(`no_fallback_lane`, `no_online_reclass`) slightly exceeded the full policy,
which is useful evidence that the current fallback/reclassification heuristics
need another tuning pass before claiming they are universally beneficial.

## Next Experiments

I added and ran the follow-up experiments suggested by the first ablation:

- Ablation-refined policy comparison: `runs/next_policy_compare_800_v2/`
- KV-heavy stress: `runs/next_kv_stress_800_v2/`
- Shape-classifier stress: `runs/next_shape_stress_800_v2/`
- Policy tick sweep: `runs/next_tick_sweep_800_v2/`
- Load regimes: `runs/next_load_regimes_600_v2/`

The ablation-refined policy changes are:

- SLO Notary remains the authority for urgency.
- KV Treasury remains value-aware.
- Shape forecasts are soft scoring evidence, not hard lane assignment.
- Fallback demotion is removed.
- Online reclassification is hysteretic.

Headline results:

| experiment | best policy | governed goodput | main read |
|---|---|---:|---|
| default comparison | YieldOS-Lite | 507.88 | The ablation-refined policy beats the initial policy by 4.4% and DistServe-style by 26.5%. |
| KV stress | YieldOS-Lite | 29.82 | KV pressure is severe; value-aware KV beats LRU by 6.0% goodput and 2.9% recompute waste. |
| shape stress | no classifier | 163.19 | Hard routing fails badly; even soft forecasts still underperform SLO-only governance on this stress trace. |
| tick sweep | 100 ms | 522.12 | 75-100 ms is the current cadence knee; 5-10 ms lose to overhead, 200 ms goes stale. |
| load regimes | YieldOS-Lite / LRU split | 906.61 at 60% load | YieldOS-Lite beats DistServe at every load; KV value helps most at 120-150% load but LRU is close below 100%. |

The shape-stress result is the sharpest warning: the current classifier is still
not P1-ready. The simulator now supports the right architectural test, and the
result says the paper should claim predictive SLO governance first, KV Treasury
second, and shape classification as an open calibration problem rather than a
validated component.

## Further Sweeps

I added a value-weighted KV metric and ran the next experiment set:

- Load sweep: `runs/further_load_sweep_800/`
- KV pressure sweep: `runs/further_kv_pressure_sweep_800/`
- SLO tightness sweep: `runs/further_slo_tightness_sweep_800/`
- Normal tick sweep: `runs/further_tick_sweep_normal_800/`
- Stress tick sweep: `runs/further_tick_sweep_stress_800/`

New metric:

`kv_value_preserved = saved_prefix_tokens * slo_pressure * tenant_priority * expected_future_use * sharing_potential`

This is intentionally separate from raw KV hits. It is a coarse MVP proxy for
value-weighted KV residency.

Highlights:

| sweep | result |
|---|---|
| load | YieldOS-Lite beats DistServe-style at every tested load: +22.7% at 50%, +37.1% at 70%, +31.5% at 90%, +33.4% at 110%, +30.1% at 130%, and +42.5% at 150%. |
| KV pressure | YieldOS-Lite beats DistServe-style under every KV pressure level. Against LRU, value-aware KV is mixed on raw goodput but preserves more KV value at medium/high/extreme pressure. |
| SLO tightness | SLO Notary improves over no-Notary by +6.5% loose, +9.5% normal, +9.1% tight, and +11.2% impossible on this seed. |
| normal tick | best cadence is 100ms at 522.12 governed tokens/GPU-second; 75ms and 50ms are close, while 5-10ms lose to overhead and 200ms goes stale. |
| stress tick | best cadence shifts to 75ms at 32.59 governed tokens/GPU-second; severe contention changes the knee. |

The load sweep complicates the SLO story slightly: no-Notary is competitive at
some individual load points, but the SLO tightness sweep shows the Notary
consistently helps as SLO risk becomes the explicit experimental variable. The
more careful claim is: SLO Notary is most useful when SLO pressure, not merely
aggregate load, is the binding constraint.

## Interpretation Discipline

This simulator is not a CUDA-level serving benchmark. It is a control-plane
simulator. Its purpose is to test whether governance policies produce better
allocation behavior before integrating with real engines.

The current results support three claims:

1. Predictive SLO governance is P1-ready.
2. Value-aware KV accounting is promising, especially under KV pressure, but
   should be evaluated using value-weighted metrics rather than raw hit rate
   alone.
3. Shape classification is not yet validated as a hard routing primitive. In
   the current policy it is treated as soft evidence; further calibration is required before
   it can become routing authority.

Therefore, the MVP claim is not "full YieldOS works." The MVP claim is: a
slow-path SLO-aware resource governance layer can improve governed goodput over
mechanistic baselines in a trace simulator.

## Trace Compatibility

YieldOS-Lite can replay CSV and JSONL traces with:

`arrival_time_ms`, `prompt_tokens`, `output_tokens`, `tenant_id`,
`priority_class`, optional SLO fields, optional `prefix_id`, and optional
`abandoned_at_ms`.

This makes the simulator ready for public or production trace validation when
real traces are available.

## Semi-Realistic Profiles

I added a workload-suite runner for less synthetic, production-shaped traffic
profiles:

- `chat_heavy`
- `rag_heavy`
- `code_heavy`
- `batch_summary_heavy`
- `mixed_enterprise`

Canonical run: `runs/trace_workload_suite_800_v2/`

The runner also writes normalized replayable CSV traces under
`runs/trace_workload_suite_800_v2/traces/`. Replaying the generated
`chat_heavy.csv` trace produced the same YieldOS-Lite metrics as the workload-suite run,
which verifies that experiment labels do not affect policy randomness.

Profile results for YieldOS-Lite vs DistServe-style:

| profile | YieldOS-Lite | DistServe-style | improvement |
|---|---:|---:|---:|
| chat-heavy | 530.69 | 488.50 | +8.6% |
| RAG-heavy | 41.10 | 27.83 | +47.6% |
| code-heavy | 286.30 | 209.77 | +36.5% |
| batch-summary-heavy | 85.85 | 51.13 | +67.9% |
| mixed-enterprise | 172.82 | 77.90 | +121.8% |

This is still not external validation, but it is a cleaner bridge: YieldOS-Lite
now has an explicit replay schema and a profile suite that better resembles
chat, RAG, code, batch, and enterprise traffic mixes.

## External Trace Pilot

I added a BurstGPT adapter and ran a small external-trace pilot using the public
HPMLL/BurstGPT workload trace. BurstGPT provides request timestamps, request
tokens, response tokens, model name, and log type; the adapter normalizes those
fields into the YieldOS replay schema.

Canonical pilot runs:

- `runs/burstgpt_sample_800/` at 20x time scale
- `runs/burstgpt_sample_800_scale50/`
- `runs/burstgpt_sample_800_scale100/`
- `runs/burstgpt_sample_800_scale200/`

This pilot is deliberately not folded into the main positive claim. The first
800 BurstGPT rows are almost entirely interactive, have no prefix reuse signal,
and are relatively homogeneous compared with the mixed-enterprise profiles. In
that regime, DistServe-style disaggregation is competitive or better:

| time scale | best policy | note |
|---|---|---|
| 20x | DistServe-style, tied on goodput | very light contention; all governed-goodput values are effectively equal |
| 50x | DistServe-style, tied on goodput | still mostly equal |
| 100x | DistServe-style | DistServe reaches 507.77 vs YieldOS-Lite at 491.15 |
| 200x | DistServe-style | DistServe reaches 442.61 vs YieldOS-Lite at 367.68 |

This is a useful counterweight: YieldOS-Lite is not claiming universal dominance.
The current simulator says governance helps most when workload heterogeneity,
prefix reuse, tenant priority, and SLO pressure create competing obligations.
When an external sample is nearly all interactive and has no prefix reuse,
mechanistic disaggregation can be the better policy.

## Obligation Heterogeneity

I added a coarse Obligation Heterogeneity Index (OHI) to every report:

`OHI = (H(prompt_bucket) + H(output_bucket) + H(priority) + H(SLO) + prefix_reuse + KV_pressure) / 6`

This is not a final metric, but it makes the current hypothesis measurable:

YieldOS-Lite is not a better queue; it is a better response to heterogeneity.

Canonical OHI analysis: `runs/ohi_gain_analysis/`

| workload | OHI | YieldOS gain over DistServe-style |
|---|---:|---:|
| BurstGPT sample, 100x | 0.315 | -3.3% |
| chat-heavy | 0.540 | +8.6% |
| code-heavy | 0.666 | +36.5% |
| mixed-enterprise | 0.711 | +121.8% |
| batch-summary-heavy | 0.722 | +67.9% |
| RAG-heavy | 0.763 | +47.6% |

Across this small pilot set, OHI and YieldOS gain have a Pearson correlation of
0.713. This is suggestive, not definitive. The useful scientific claim is:
governance advantage appears to increase when requests impose heterogeneous
obligations on prefill compute, decode bandwidth, KV residency, SLO slack, and
tenant priority.

## Notes

The simulator is intentionally coarse. It is not a CUDA, vLLM, or TensorRT-LLM
replacement. It models the control-plane questions in the draft:

- Which requests should enter protected lanes?
- Which KV entries are worth keeping under pressure?
- When should the scheduler intervene before tail-latency collapse?
- How much of YieldOS-Lite's gain comes from each component?

The hot path consumes only a precomputed policy snapshot. Pricing, lane updates,
KV value scoring, and SLO prediction happen on the slow path at configurable
cadences.
