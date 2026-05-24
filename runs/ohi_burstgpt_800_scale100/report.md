# YieldOS-Lite Run Report

Best governed goodput: `distserve_disaggregated_burstgpt` at 507.77 tokens/GPU-second.

| policy | OHI | governed goodput | SLO attainment | TTFT p95 | ITL p95 | KV hits | KV value preserved | KV recompute waste | overhead ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| distserve_disaggregated_burstgpt | 0.315 | 507.77 | 1.000 | 100.2 | 25.0 | 0 | 0.0 | 0.0 | 1073.4 |
| yieldos_v02_burstgpt | 0.315 | 491.15 | 0.973 | 460.0 | 125.0 | 0 | 0.0 | 0.0 | 1353.9 |
| yieldos_v02_lru_kv_burstgpt | 0.315 | 491.15 | 0.973 | 460.0 | 125.0 | 0 | 0.0 | 0.0 | 1354.1 |
| yieldos_v02_no_slo_notary_burstgpt | 0.315 | 230.46 | 0.472 | 18330.2 | 25.0 | 0 | 0.0 | 0.0 | 1814.5 |

## Interpretation

Governed goodput counts only completed output tokens from requests that met both TTFT and ITL SLOs, then divides by simulated GPU time plus control-plane overhead.
The simulator is intentionally coarse; use it to compare policy behavior and ablations before integrating with a real engine.
