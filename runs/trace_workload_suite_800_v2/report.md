# YieldOS-Lite Run Report

Best governed goodput: `yieldos_v02_chat_heavy` at 530.69 tokens/GPU-second.

| policy | governed goodput | SLO attainment | TTFT p95 | ITL p95 | KV hits | KV value preserved | KV recompute waste | overhead ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| yieldos_v02_chat_heavy | 530.69 | 0.270 | 13465.5 | 100.0 | 80509 | 541872.1 | 33766.3 | 1503.2 |
| yieldos_v02_lru_kv_chat_heavy | 530.48 | 0.270 | 13447.5 | 100.0 | 81030 | 544021.4 | 25659.5 | 1503.6 |
| distserve_disaggregated_chat_heavy | 488.50 | 0.273 | 13948.0 | 401.2 | 69516 | 369549.1 | 24274.1 | 1258.0 |
| yieldos_v02_code_heavy | 286.30 | 0.146 | 83012.6 | 75.0 | 53248 | 502521.0 | 241999.1 | 7498.3 |
| yieldos_v02_lru_kv_code_heavy | 283.57 | 0.146 | 83304.4 | 75.0 | 53267 | 501668.0 | 256635.7 | 7497.5 |
| yieldos_v02_no_slo_notary_code_heavy | 270.57 | 0.134 | 83508.4 | 75.0 | 54014 | 502966.4 | 213792.7 | 7506.2 |
| yieldos_v02_no_slo_notary_chat_heavy | 258.78 | 0.171 | 23424.8 | 25.0 | 81879 | 576125.8 | 34258.8 | 2066.6 |
| distserve_disaggregated_code_heavy | 209.77 | 0.114 | 86039.4 | 533.7 | 55890 | 259847.0 | 167163.9 | 7231.1 |
| yieldos_v02_lru_kv_mixed_enterprise | 174.13 | 0.111 | 32855.8 | 25.0 | 253340 | 5937918.1 | 1474895.5 | 3027.1 |
| yieldos_v02_mixed_enterprise | 172.82 | 0.110 | 32953.4 | 25.0 | 257340 | 6668863.3 | 1384588.5 | 3026.6 |
| yieldos_v02_no_slo_notary_mixed_enterprise | 118.74 | 0.080 | 34488.0 | 25.0 | 252728 | 7107066.6 | 1254866.7 | 3299.6 |
| yieldos_v02_lru_kv_batch_summary_heavy | 86.25 | 0.089 | 69709.2 | 25.0 | 479336 | 13716883.2 | 2309895.6 | 5702.3 |
| yieldos_v02_batch_summary_heavy | 85.85 | 0.091 | 70097.5 | 25.0 | 483369 | 15260296.4 | 2252930.9 | 5733.5 |
| distserve_disaggregated_mixed_enterprise | 77.90 | 0.048 | 37292.2 | 25.0 | 226803 | 1445805.5 | 1281329.0 | 3116.7 |
| yieldos_v02_no_slo_notary_batch_summary_heavy | 52.26 | 0.064 | 71071.0 | 25.0 | 484240 | 16363851.2 | 2429786.1 | 6040.2 |
| distserve_disaggregated_batch_summary_heavy | 51.13 | 0.052 | 71258.1 | 25.0 | 467760 | 2635576.3 | 2579194.2 | 5878.4 |
| yieldos_v02_rag_heavy | 41.10 | 0.050 | 52289.8 | 25.0 | 576514 | 26494421.2 | 1800852.8 | 4111.1 |
| yieldos_v02_lru_kv_rag_heavy | 39.39 | 0.049 | 53223.8 | 25.0 | 556973 | 23627693.6 | 1996796.3 | 4136.1 |
| yieldos_v02_no_slo_notary_rag_heavy | 29.79 | 0.037 | 55298.0 | 25.0 | 554594 | 25139589.5 | 1548046.9 | 4523.3 |
| distserve_disaggregated_rag_heavy | 27.83 | 0.029 | 60046.0 | 25.0 | 533011 | 3679354.4 | 2011027.6 | 4164.6 |

## Interpretation

Governed goodput counts only completed output tokens from requests that met both TTFT and ITL SLOs, then divides by simulated GPU time plus control-plane overhead.
The simulator is intentionally coarse; use it to compare policy behavior and ablations before integrating with a real engine.
