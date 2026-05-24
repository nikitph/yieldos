# YieldOS-Lite Run Report

Best governed goodput: `distserve_disaggregated_burstgpt` at 442.61 tokens/GPU-second.

| policy | governed goodput | SLO attainment | TTFT p95 | ITL p95 | KV hits | KV value preserved | KV recompute waste | overhead ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| distserve_disaggregated_burstgpt | 442.61 | 0.487 | 14040.2 | 25.0 | 0 | 0.0 | 0.0 | 1638.6 |
| yieldos_v02_burstgpt | 367.68 | 0.458 | 37335.0 | 125.0 | 0 | 0.0 | 0.0 | 3376.2 |
| yieldos_v02_lru_kv_burstgpt | 366.62 | 0.456 | 37391.0 | 125.0 | 0 | 0.0 | 0.0 | 3377.9 |
| yieldos_v02_no_slo_notary_burstgpt | 206.25 | 0.258 | 62898.2 | 25.0 | 0 | 0.0 | 0.0 | 4518.9 |

## Interpretation

Governed goodput counts only completed output tokens from requests that met both TTFT and ITL SLOs, then divides by simulated GPU time plus control-plane overhead.
The simulator is intentionally coarse; use it to compare policy behavior and ablations before integrating with a real engine.
