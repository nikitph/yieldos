# YieldOS-Lite Run Report

Best governed goodput: `yieldos_v02_kv_low` at 24.43 tokens/GPU-second.

| policy | governed goodput | SLO attainment | TTFT p95 | ITL p95 | KV hits | KV value preserved | KV recompute waste | overhead ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| yieldos_v02_kv_low | 24.43 | 0.029 | 64656.3 | 25.0 | 546173 | 22186957.4 | 2039570.1 | 4896.0 |
| yieldos_v02_lru_kv_kv_medium | 22.02 | 0.029 | 69229.5 | 25.0 | 401952 | 16857202.6 | 4375880.9 | 5021.3 |
| yieldos_v02_kv_medium | 21.69 | 0.028 | 69229.0 | 25.0 | 398144 | 20489148.2 | 4126670.7 | 5047.7 |
| yieldos_v02_kv_high | 21.22 | 0.029 | 74696.5 | 25.0 | 245922 | 12580836.7 | 5409398.2 | 5269.2 |
| yieldos_v02_lru_kv_kv_high | 20.92 | 0.029 | 75992.0 | 25.0 | 218561 | 9657422.7 | 5455775.4 | 5336.1 |
| yieldos_v02_lru_kv_kv_low | 20.91 | 0.028 | 63983.1 | 25.0 | 566919 | 24181820.1 | 2068668.9 | 4901.8 |
| yieldos_v02_kv_extreme | 20.41 | 0.029 | 79421.9 | 25.0 | 123970 | 7026376.5 | 6445198.3 | 5527.5 |
| distserve_disaggregated_kv_low | 20.10 | 0.014 | 77029.1 | 25.0 | 556596 | 3951660.9 | 1690697.8 | 5132.7 |
| yieldos_v02_lru_kv_kv_extreme | 19.90 | 0.028 | 81071.9 | 25.0 | 80588 | 2456331.7 | 6525335.7 | 5591.0 |
| distserve_disaggregated_kv_medium | 19.05 | 0.014 | 83306.8 | 25.0 | 369906 | 2532181.4 | 3981241.1 | 5363.9 |
| distserve_disaggregated_kv_high | 18.06 | 0.014 | 89662.1 | 25.0 | 178109 | 1173591.1 | 5489282.5 | 5674.7 |
| distserve_disaggregated_kv_extreme | 17.63 | 0.014 | 92662.1 | 25.0 | 82756 | 577057.7 | 6758530.8 | 5829.8 |

## Interpretation

Governed goodput counts only completed output tokens from requests that met both TTFT and ITL SLOs, then divides by simulated GPU time plus control-plane overhead.
The simulator is intentionally coarse; use it to compare policy behavior and ablations before integrating with a real engine.
