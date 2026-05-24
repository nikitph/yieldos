# YieldOS-Lite Run Report

Best governed goodput: `yieldos_lite` at 486.41 tokens/GPU-second.

| policy | governed goodput | SLO attainment | TTFT p95 | ITL p95 | KV hits | KV recompute waste | overhead ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| yieldos_lite | 486.41 | 0.274 | 30163.0 | 325.0 | 73765 | 319145.8 | 3029.5 |
| distserve_disaggregated | 401.63 | 0.258 | 32658.0 | 325.0 | 64488 | 389913.4 | 2848.6 |
| sarathi_chunked_prefill | 126.64 | 0.076 | 39016.6 | 905.0 | 72184 | 378287.7 | 3501.1 |
| continuous_batching | 40.15 | 0.033 | 49318.0 | 625.0 | 56268 | 413997.3 | 4574.3 |

## Interpretation

Governed goodput counts only completed output tokens from requests that met both TTFT and ITL SLOs, then divides by simulated GPU time plus control-plane overhead.
The simulator is intentionally coarse; use it to compare policy behavior and ablations before integrating with a real engine.
