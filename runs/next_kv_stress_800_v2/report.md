# YieldOS-Lite Run Report

Best governed goodput: `yieldos_lite_v02_tick_50ms` at 29.82 tokens/GPU-second.

| policy | governed goodput | SLO attainment | TTFT p95 | ITL p95 | KV hits | KV recompute waste | overhead ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| yieldos_lite_v02_tick_50ms | 29.82 | 0.046 | 74495.0 | 25.0 | 193728 | 5071964.8 | 5231.7 |
| yieldos_v02_lru_kv | 28.12 | 0.044 | 73831.5 | 25.0 | 219256 | 5223037.7 | 5226.6 |
| yieldos_v02_no_slo_notary | 27.37 | 0.034 | 76619.5 | 25.0 | 172026 | 5088429.8 | 5648.3 |
| distserve_disaggregated | 18.30 | 0.014 | 85286.1 | 25.0 | 176084 | 4877996.1 | 5717.9 |

## Interpretation

Governed goodput counts only completed output tokens from requests that met both TTFT and ITL SLOs, then divides by simulated GPU time plus control-plane overhead.
The simulator is intentionally coarse; use it to compare policy behavior and ablations before integrating with a real engine.
