# YieldOS-Lite Run Report

Best governed goodput: `yieldos_v02_replay` at 530.69 tokens/GPU-second.

| policy | governed goodput | SLO attainment | TTFT p95 | ITL p95 | KV hits | KV value preserved | KV recompute waste | overhead ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| yieldos_v02_replay | 530.69 | 0.270 | 13465.5 | 100.0 | 80509 | 541872.1 | 33766.3 | 1503.2 |
| yieldos_v02_lru_kv_replay | 530.48 | 0.270 | 13447.5 | 100.0 | 81030 | 544021.4 | 25659.5 | 1503.6 |
| distserve_disaggregated_replay | 488.50 | 0.273 | 13948.0 | 401.2 | 69516 | 369549.1 | 24274.1 | 1258.0 |
| yieldos_v02_no_slo_notary_replay | 258.78 | 0.171 | 23424.8 | 25.0 | 81879 | 576125.8 | 34258.8 | 2066.6 |

## Interpretation

Governed goodput counts only completed output tokens from requests that met both TTFT and ITL SLOs, then divides by simulated GPU time plus control-plane overhead.
The simulator is intentionally coarse; use it to compare policy behavior and ablations before integrating with a real engine.
