# YieldOS-Lite Run Report

Best governed goodput: `yieldos_v02_lru_kv_slo_loose` at 429.41 tokens/GPU-second.

| policy | governed goodput | SLO attainment | TTFT p95 | ITL p95 | KV hits | KV value preserved | KV recompute waste | overhead ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| yieldos_v02_lru_kv_slo_loose | 429.41 | 0.336 | 36898.7 | 300.0 | 72048 | 717737.1 | 446935.5 | 3559.0 |
| yieldos_v02_slo_loose | 428.07 | 0.334 | 36781.4 | 300.0 | 79625 | 903901.0 | 424411.5 | 3566.8 |
| yieldos_v02_no_slo_notary_slo_loose | 402.01 | 0.316 | 37442.2 | 300.0 | 81884 | 952193.2 | 502261.0 | 3566.3 |
| distserve_disaggregated_slo_loose | 355.47 | 0.290 | 39189.5 | 217.5 | 84994 | 250088.2 | 448890.0 | 3362.1 |
| yieldos_v02_lru_kv_slo_normal | 337.85 | 0.265 | 36633.6 | 225.0 | 77604 | 739298.9 | 440930.7 | 3549.6 |
| yieldos_v02_slo_normal | 335.64 | 0.264 | 36621.4 | 225.0 | 78255 | 878205.2 | 482995.3 | 3551.8 |
| yieldos_v02_no_slo_notary_slo_normal | 306.59 | 0.235 | 37031.8 | 225.0 | 82859 | 963480.6 | 476689.2 | 3557.6 |
| distserve_disaggregated_slo_normal | 300.47 | 0.236 | 39189.5 | 217.5 | 84994 | 250088.2 | 448890.0 | 3362.1 |
| yieldos_v02_lru_kv_slo_tight | 293.75 | 0.212 | 36498.9 | 225.0 | 76158 | 824801.2 | 441991.6 | 3541.5 |
| yieldos_v02_slo_tight | 291.58 | 0.210 | 36663.1 | 200.0 | 84691 | 1034286.0 | 455177.8 | 3544.4 |
| yieldos_v02_no_slo_notary_slo_tight | 267.23 | 0.191 | 36776.4 | 200.0 | 80865 | 916755.4 | 468002.9 | 3533.4 |
| distserve_disaggregated_slo_tight | 262.31 | 0.200 | 39189.5 | 217.5 | 84994 | 250088.2 | 448890.0 | 3362.1 |
| yieldos_v02_lru_kv_slo_impossible | 250.93 | 0.163 | 36423.1 | 175.0 | 80694 | 865827.1 | 531940.4 | 3527.9 |
| yieldos_v02_slo_impossible | 246.81 | 0.169 | 36341.1 | 200.0 | 79204 | 992214.4 | 448501.6 | 3516.1 |
| distserve_disaggregated_slo_impossible | 229.66 | 0.164 | 39189.5 | 217.5 | 84994 | 250088.2 | 448890.0 | 3362.1 |
| yieldos_v02_no_slo_notary_slo_impossible | 221.87 | 0.135 | 36895.4 | 175.0 | 80187 | 1033160.6 | 425914.9 | 3535.3 |

## Interpretation

Governed goodput counts only completed output tokens from requests that met both TTFT and ITL SLOs, then divides by simulated GPU time plus control-plane overhead.
The simulator is intentionally coarse; use it to compare policy behavior and ablations before integrating with a real engine.
