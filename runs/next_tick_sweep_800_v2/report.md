# YieldOS-Lite Run Report

Best governed goodput: `yieldos_lite_v02_tick_100ms` at 522.12 tokens/GPU-second.

| policy | governed goodput | SLO attainment | TTFT p95 | ITL p95 | KV hits | KV recompute waste | overhead ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| yieldos_lite_v02_tick_100ms | 522.12 | 0.287 | 28292.7 | 225.0 | 61993 | 301928.5 | 1459.0 |
| yieldos_lite_v02_tick_75ms | 514.55 | 0.289 | 28955.3 | 250.0 | 63523 | 243819.4 | 1950.7 |
| yieldos_lite_v02_tick_50ms | 507.88 | 0.286 | 28960.4 | 203.7 | 65176 | 296950.1 | 2938.5 |
| yieldos_lite_v02_tick_25ms | 503.41 | 0.292 | 28879.1 | 225.0 | 62679 | 253926.9 | 5856.1 |
| yieldos_lite_v02_tick_200ms | 430.39 | 0.235 | 28570.8 | 250.0 | 57759 | 248586.6 | 735.1 |
| yieldos_lite_v02_tick_10ms | 430.10 | 0.290 | 28940.3 | 225.0 | 63388 | 265366.2 | 14596.6 |
| yieldos_lite_v02_tick_5ms | 420.67 | 0.292 | 28647.8 | 250.0 | 63523 | 257930.2 | 29186.2 |

## Interpretation

Governed goodput counts only completed output tokens from requests that met both TTFT and ITL SLOs, then divides by simulated GPU time plus control-plane overhead.
The simulator is intentionally coarse; use it to compare policy behavior and ablations before integrating with a real engine.
