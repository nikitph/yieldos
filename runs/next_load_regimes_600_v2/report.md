# YieldOS-Lite Run Report

Best governed goodput: `yieldos_v02_lru_kv_load_0.60` at 906.61 tokens/GPU-second.

| policy | governed goodput | SLO attainment | TTFT p95 | ITL p95 | KV hits | KV recompute waste | overhead ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| yieldos_v02_lru_kv_load_0.60 | 906.61 | 0.497 | 13441.8 | 337.5 | 59933 | 230258.3 | 1380.6 |
| yieldos_v02_load_0.60 | 902.46 | 0.492 | 13449.0 | 312.5 | 59177 | 172002.4 | 1378.1 |
| yieldos_v02_no_slo_notary_load_0.60 | 819.80 | 0.442 | 13353.5 | 356.2 | 59133 | 183274.7 | 1384.2 |
| yieldos_v02_lru_kv_load_0.80 | 700.36 | 0.362 | 21213.4 | 300.0 | 51139 | 217718.3 | 1784.3 |
| yieldos_v02_load_0.80 | 686.79 | 0.357 | 20977.8 | 275.0 | 49521 | 172550.6 | 1779.6 |
| yieldos_v02_no_slo_notary_load_0.80 | 666.42 | 0.352 | 21082.4 | 321.3 | 53340 | 158570.5 | 1776.7 |
| distserve_disaggregated_load_0.60 | 653.46 | 0.398 | 16632.5 | 418.8 | 74236 | 202058.7 | 1362.0 |
| yieldos_v02_lru_kv_load_1.00 | 607.14 | 0.310 | 26169.9 | 272.5 | 51060 | 240392.4 | 2030.3 |
| yieldos_v02_load_1.00 | 604.39 | 0.307 | 25854.6 | 297.5 | 50164 | 179199.2 | 2030.2 |
| yieldos_v02_load_1.20 | 566.29 | 0.280 | 28799.7 | 275.0 | 48024 | 168572.2 | 2187.9 |
| yieldos_v02_lru_kv_load_1.20 | 558.03 | 0.275 | 29066.7 | 295.0 | 48024 | 241303.2 | 2189.3 |
| yieldos_v02_no_slo_notary_load_1.00 | 549.71 | 0.288 | 25628.8 | 300.0 | 49203 | 149444.2 | 2020.4 |
| distserve_disaggregated_load_0.80 | 544.44 | 0.298 | 24386.6 | 325.0 | 62896 | 214159.9 | 1737.9 |
| distserve_disaggregated_load_1.00 | 496.75 | 0.268 | 28806.7 | 447.5 | 58845 | 219922.2 | 1969.4 |
| yieldos_v02_load_1.50 | 473.00 | 0.243 | 31872.0 | 275.0 | 40301 | 174873.8 | 2346.2 |
| yieldos_v02_lru_kv_load_1.50 | 461.50 | 0.240 | 32083.2 | 317.5 | 40301 | 271797.5 | 2347.6 |
| distserve_disaggregated_load_1.20 | 420.92 | 0.242 | 31980.9 | 347.5 | 50438 | 215290.9 | 2136.4 |
| yieldos_v02_no_slo_notary_load_1.20 | 416.82 | 0.232 | 29452.0 | 347.5 | 42023 | 151493.4 | 2200.3 |
| distserve_disaggregated_load_1.50 | 400.35 | 0.225 | 34886.9 | 370.0 | 46370 | 226703.6 | 2307.1 |
| yieldos_v02_no_slo_notary_load_1.50 | 372.93 | 0.205 | 32505.9 | 347.5 | 47462 | 169507.7 | 2358.7 |

## Interpretation

Governed goodput counts only completed output tokens from requests that met both TTFT and ITL SLOs, then divides by simulated GPU time plus control-plane overhead.
The simulator is intentionally coarse; use it to compare policy behavior and ablations before integrating with a real engine.
