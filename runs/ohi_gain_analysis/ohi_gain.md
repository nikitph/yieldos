# OHI vs YieldOS Gain

Pearson correlation over this small pilot set: `0.713`.

| workload | OHI | YieldOS v0.2 | DistServe-style | YieldOS gain |
|---|---:|---:|---:|---:|
| burstgpt_100x | 0.315 | 491.15 | 507.77 | -3.3% |
| chat_heavy | 0.540 | 530.69 | 488.50 | 8.6% |
| code_heavy | 0.666 | 286.30 | 209.77 | 36.5% |
| mixed_enterprise | 0.711 | 172.82 | 77.90 | 121.8% |
| batch_summary_heavy | 0.722 | 85.85 | 51.13 | 67.9% |
| rag_heavy | 0.763 | 41.10 | 27.83 | 47.6% |

## Interpretation

This is a coarse explanatory analysis, not a definitive law. The current pilot supports the hypothesis that YieldOS gains rise when obligation heterogeneity rises. The BurstGPT sample is a boundary condition: low OHI, no prefix reuse, mostly interactive traffic, and DistServe-style disaggregation wins.
