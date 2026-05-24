# YieldOS-Lite Run Report

Best governed goodput: `ablate_no_fallback_lane` at 495.34 tokens/GPU-second.

| policy | governed goodput | SLO attainment | TTFT p95 | ITL p95 | KV hits | KV recompute waste | overhead ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| ablate_no_fallback_lane | 495.34 | 0.281 | 30852.4 | 300.0 | 69970 | 316422.6 | 3014.8 |
| ablate_no_online_reclass | 493.61 | 0.282 | 31086.0 | 500.0 | 70674 | 298131.9 | 3039.4 |
| ablate_no_shape_classifier | 489.73 | 0.287 | 28878.5 | 175.0 | 71822 | 293697.4 | 2925.8 |
| yieldos_lite | 486.41 | 0.274 | 30163.0 | 325.0 | 73765 | 319145.8 | 3029.5 |
| ablate_exact_output_oracle | 482.75 | 0.278 | 31188.1 | 628.7 | 73157 | 308036.8 | 3034.3 |
| ablate_lru_kv | 481.92 | 0.282 | 31115.2 | 400.0 | 72811 | 397248.1 | 3030.4 |
| ablate_noisy_forecasts | 473.53 | 0.282 | 31237.2 | 400.0 | 72563 | 342543.8 | 3024.7 |
| ablate_policy_tick_1ms | 465.89 | 0.278 | 31053.8 | 450.0 | 76739 | 330907.9 | 6042.6 |
| ablate_policy_tick_100ms | 460.49 | 0.269 | 30535.8 | 375.0 | 68915 | 343869.5 | 1510.1 |
| ablate_no_slo_notary | 337.82 | 0.200 | 30350.9 | 250.0 | 76518 | 348873.7 | 3042.2 |

## Interpretation

Governed goodput counts only completed output tokens from requests that met both TTFT and ITL SLOs, then divides by simulated GPU time plus control-plane overhead.
The simulator is intentionally coarse; use it to compare policy behavior and ablations before integrating with a real engine.
