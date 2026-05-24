# YieldOS-Lite Run Report

Best governed goodput: `yieldos_v02_lru_kv_load_0.50` at 863.15 tokens/GPU-second.

| policy | governed goodput | SLO attainment | TTFT p95 | ITL p95 | KV hits | KV value preserved | KV recompute waste | overhead ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| yieldos_v02_lru_kv_load_0.50 | 863.15 | 0.512 | 7280.0 | 275.0 | 76996 | 825956.7 | 216610.4 | 1579.7 |
| yieldos_v02_no_slo_notary_load_0.50 | 854.47 | 0.509 | 7541.8 | 250.0 | 87601 | 1012474.1 | 201737.1 | 1595.2 |
| yieldos_v02_load_0.50 | 845.98 | 0.507 | 7177.7 | 250.0 | 89183 | 939623.5 | 210570.2 | 1588.3 |
| distserve_disaggregated_load_0.50 | 689.49 | 0.456 | 10116.0 | 350.0 | 79912 | 244672.0 | 199471.7 | 1442.3 |
| yieldos_v02_no_slo_notary_load_0.70 | 587.15 | 0.320 | 20764.4 | 250.0 | 74323 | 723581.9 | 210429.2 | 2432.2 |
| yieldos_v02_load_0.70 | 586.64 | 0.320 | 20703.4 | 250.0 | 66970 | 666610.4 | 212039.7 | 2440.7 |
| yieldos_v02_lru_kv_load_0.70 | 586.31 | 0.320 | 20556.1 | 250.0 | 77163 | 710878.3 | 247693.8 | 2437.1 |
| yieldos_v02_load_0.90 | 525.43 | 0.287 | 29049.8 | 250.0 | 77931 | 691265.8 | 194812.5 | 2991.4 |
| yieldos_v02_lru_kv_load_0.90 | 517.49 | 0.286 | 28874.3 | 250.0 | 79660 | 662244.2 | 274696.8 | 2982.0 |
| yieldos_v02_no_slo_notary_load_0.90 | 485.13 | 0.270 | 29323.0 | 225.0 | 74464 | 716158.6 | 196907.2 | 2994.1 |
| yieldos_v02_load_1.10 | 459.27 | 0.245 | 34340.8 | 252.5 | 70573 | 688231.0 | 201359.6 | 3350.6 |
| yieldos_v02_no_slo_notary_load_1.10 | 457.46 | 0.245 | 34551.4 | 275.0 | 71616 | 714260.0 | 198397.7 | 3350.5 |
| yieldos_v02_lru_kv_load_1.10 | 448.82 | 0.241 | 34251.5 | 250.0 | 69527 | 657009.2 | 288670.1 | 3352.7 |
| distserve_disaggregated_load_0.70 | 427.75 | 0.265 | 22362.8 | 375.0 | 91338 | 252932.9 | 237858.5 | 2290.4 |
| yieldos_v02_no_slo_notary_load_1.30 | 426.52 | 0.233 | 38397.2 | 250.0 | 67663 | 716433.6 | 200507.8 | 3612.0 |
| yieldos_v02_lru_kv_load_1.30 | 423.12 | 0.233 | 38425.3 | 250.0 | 67083 | 714825.7 | 320381.6 | 3622.1 |
| yieldos_v02_load_1.30 | 422.95 | 0.231 | 38437.7 | 225.0 | 69515 | 706786.1 | 235949.3 | 3622.7 |
| distserve_disaggregated_load_0.90 | 399.67 | 0.242 | 30770.1 | 252.5 | 75967 | 211951.2 | 229136.3 | 2838.7 |
| yieldos_v02_no_slo_notary_load_1.50 | 395.74 | 0.214 | 41312.9 | 275.0 | 59054 | 634199.7 | 236935.9 | 3825.4 |
| yieldos_v02_lru_kv_load_1.50 | 389.59 | 0.220 | 40818.0 | 252.5 | 60641 | 632416.2 | 260893.6 | 3800.1 |
| yieldos_v02_load_1.50 | 388.57 | 0.221 | 41104.5 | 250.0 | 62410 | 669365.7 | 233432.5 | 3803.4 |
| distserve_disaggregated_load_1.10 | 344.16 | 0.211 | 35861.3 | 375.0 | 82171 | 228103.4 | 246252.0 | 3202.3 |
| distserve_disaggregated_load_1.30 | 325.03 | 0.204 | 39341.9 | 328.7 | 68136 | 222454.6 | 246948.5 | 3464.5 |
| distserve_disaggregated_load_1.50 | 272.64 | 0.168 | 42245.4 | 405.0 | 56234 | 180220.2 | 245833.6 | 3654.8 |

## Interpretation

Governed goodput counts only completed output tokens from requests that met both TTFT and ITL SLOs, then divides by simulated GPU time plus control-plane overhead.
The simulator is intentionally coarse; use it to compare policy behavior and ablations before integrating with a real engine.
