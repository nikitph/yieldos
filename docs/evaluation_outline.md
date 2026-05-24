# Evaluation Outline

## Scope and Non-Claims

YieldOS-Lite is a control-plane simulator, not a CUDA benchmark or a replacement
for vLLM, TensorRT-LLM, TGI, Sarathi-Serve, or DistServe. It tests whether
slow-path governance policies produce better allocation behavior before kernel
or serving-engine integration.

## Recommended Structure

1. Simulator Scope and Non-Claims
2. Policies Compared
3. Metric: Governed Goodput
4. Baseline Comparison
5. MVP Ablations
6. v0.2 Policy Refinement
7. Load Sweep
8. KV Pressure Sweep
9. SLO Tightness Sweep
10. Policy Cadence Sweep
11. Semi-Realistic Workload Profiles
12. Heterogeneity and Boundary Conditions
13. Lessons

## Lessons

- SLO pressure is distinct from aggregate load.
- KV hit rate is not KV value.
- Shape classification should not become routing authority too early.
- Governance cadence has a workload-dependent knee.
- Slow-path control can improve fast-path execution without entering the token
  hot loop.

## Heterogeneity Hypothesis

The current explanatory hypothesis is:

If all requests are similar, scheduling is often enough. If requests impose
different obligations, governance becomes valuable.

A coarse MVP metric, Obligation Heterogeneity Index (OHI), is reported as:

`OHI = (H(prompt_bucket) + H(output_bucket) + H(priority) + H(SLO) + prefix_reuse + KV_pressure) / 6`

The OHI analysis should be treated as explanatory, not conclusive. Its job is to
make the boundary condition explicit: YieldOS-Lite is expected to help under
heterogeneous mixed obligations and to be neutral or worse under homogeneous
interactive workloads where phase separation is enough.

## Current MVP Claim

A slow-path SLO-aware resource-governance layer can improve governed goodput over
mechanistic baselines in a trace simulator. The current result validates
predictive SLO governance most strongly, supports value-aware KV accounting under
pressure, and leaves hard shape-routing classification as future calibration
work.
