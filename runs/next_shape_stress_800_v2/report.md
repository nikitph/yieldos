# YieldOS-Lite Run Report

Best governed goodput: `yieldos_no_classifier` at 163.19 tokens/GPU-second.

| policy | governed goodput | SLO attainment | TTFT p95 | ITL p95 | KV hits | KV recompute waste | overhead ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| yieldos_no_classifier | 163.19 | 0.045 | 197513.4 | 575.0 | 108143 | 13132085.1 | 17101.1 |
| yieldos_lite_v02_tick_50ms | 118.32 | 0.035 | 198140.1 | 450.0 | 136456 | 13122917.8 | 17149.1 |
| yieldos_shape_hard | 68.07 | 0.041 | 177167.8 | 965.0 | 94793 | 4334694.6 | 31713.9 |
| yieldos_noisy_hard | 45.23 | 0.033 | 176508.4 | 925.0 | 76799 | 4417632.2 | 31764.4 |
| yieldos_oracle_hard | 40.61 | 0.029 | 175319.6 | 1005.0 | 119533 | 4317131.7 | 31742.3 |

## Interpretation

Governed goodput counts only completed output tokens from requests that met both TTFT and ITL SLOs, then divides by simulated GPU time plus control-plane overhead.
The simulator is intentionally coarse; use it to compare policy behavior and ablations before integrating with a real engine.
