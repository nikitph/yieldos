# YieldOS-Lite Run Report

Best governed goodput: `distserve_disaggregated_burstgpt` at 133.43 tokens/GPU-second.

| policy | governed goodput | SLO attainment | TTFT p95 | ITL p95 | KV hits | KV value preserved | KV recompute waste | overhead ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| distserve_disaggregated_burstgpt | 133.43 | 0.466 | 90.0 | 25.0 | 0 | 0.0 | 0.0 | 538.1 |
| yieldos_v02_lru_kv_burstgpt | 133.43 | 0.466 | 115.0 | 25.0 | 0 | 0.0 | 0.0 | 539.7 |
| yieldos_v02_no_slo_notary_burstgpt | 133.43 | 0.466 | 115.0 | 25.0 | 0 | 0.0 | 0.0 | 539.7 |
| yieldos_v02_burstgpt | 133.43 | 0.466 | 115.0 | 25.0 | 0 | 0.0 | 0.0 | 539.7 |

## Interpretation

Governed goodput counts only completed output tokens from requests that met both TTFT and ITL SLOs, then divides by simulated GPU time plus control-plane overhead.
The simulator is intentionally coarse; use it to compare policy behavior and ablations before integrating with a real engine.
