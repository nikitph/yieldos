# YieldOS-Lite Run Report

Best governed goodput: `yieldos_lite_v02_tick_75ms` at 32.59 tokens/GPU-second.

| policy | governed goodput | SLO attainment | TTFT p95 | ITL p95 | KV hits | KV value preserved | KV recompute waste | overhead ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| yieldos_lite_v02_tick_75ms | 32.59 | 0.046 | 75474.2 | 25.0 | 175222 | 7211941.3 | 5076121.5 | 3506.9 |
| yieldos_lite_v02_tick_50ms | 29.82 | 0.046 | 74495.0 | 25.0 | 193728 | 8045727.7 | 5071964.8 | 5231.7 |
| yieldos_lite_v02_tick_25ms | 27.54 | 0.045 | 74501.2 | 25.0 | 202918 | 7967716.6 | 5131454.9 | 10462.4 |
| yieldos_lite_v02_tick_200ms | 24.88 | 0.033 | 75801.4 | 25.0 | 162659 | 7852056.7 | 5141966.4 | 1362.2 |
| yieldos_lite_v02_tick_10ms | 24.73 | 0.045 | 73671.8 | 25.0 | 220773 | 9525078.5 | 5199997.0 | 26019.5 |
| yieldos_lite_v02_tick_100ms | 23.15 | 0.033 | 74229.5 | 25.0 | 198192 | 8642173.5 | 5006204.2 | 2621.5 |
| yieldos_lite_v02_tick_5ms | 20.11 | 0.044 | 74726.2 | 25.0 | 189200 | 7534278.9 | 5079957.1 | 52260.0 |

## Interpretation

Governed goodput counts only completed output tokens from requests that met both TTFT and ITL SLOs, then divides by simulated GPU time plus control-plane overhead.
The simulator is intentionally coarse; use it to compare policy behavior and ablations before integrating with a real engine.
