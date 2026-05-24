# YieldOS-Lite Trace Format

YieldOS-Lite can replay CSV or JSONL traces. The replay adapter is intentionally
small so public traces or production exports can be normalized without changing
the simulator.

## Required Fields

| field | type | meaning |
|---|---|---|
| `arrival_time_ms` | integer | request arrival timestamp in milliseconds |
| `prompt_tokens` | integer | prompt length |
| `output_tokens` | integer | realized output length |
| `tenant_id` | string | tenant or workload owner |
| `priority_class` | string | `interactive`, `standard`, or `batch` |

## Optional Fields

| field | type | default |
|---|---|---|
| `request_id` | string | generated from row number |
| `ttft_slo_ms` | integer | derived from priority class |
| `itl_slo_ms` | integer | derived from priority class |
| `prefix_id` | string | no shared prefix |
| `abandoned_at_ms` | integer | request is never abandoned |
| `request_type` | string | ignored by the simulator, kept for analysis |

## CSV Example

```csv
request_id,arrival_time_ms,prompt_tokens,output_tokens,tenant_id,priority_class,ttft_slo_ms,itl_slo_ms,prefix_id,abandoned_at_ms,request_type
r1,0,128,64,tenant-a,interactive,950,145,,,
r2,32,4096,180,tenant-b,standard,2600,280,doc-17,,rag_qa
```

## JSONL Example

```jsonl
{"request_id":"r1","arrival_time_ms":0,"prompt_tokens":128,"output_tokens":64,"tenant_id":"tenant-a","priority_class":"interactive"}
{"request_id":"r2","arrival_time_ms":32,"prompt_tokens":4096,"output_tokens":180,"tenant_id":"tenant-b","priority_class":"standard","prefix_id":"doc-17","request_type":"rag_qa"}
```

## Replay

```bash
PYTHONPATH=src python3 -m yieldos.cli replay --trace path/to/trace.csv --out runs/replay_demo
```

## BurstGPT Adapter

YieldOS-Lite includes a BurstGPT normalizer for the public HPMLL/BurstGPT trace.
BurstGPT provides request submission timestamps, request-token counts,
response-token counts, model names, and log type. YieldOS maps those fields into
the replay schema and writes the normalized sample under the run directory.

```bash
PYTHONPATH=src python3 -m yieldos.cli burstgpt-replay \
  --source https://raw.githubusercontent.com/HPMLL/BurstGPT/main/data/BurstGPT_1.csv \
  --limit 800 \
  --time-scale 20 \
  --out runs/burstgpt_sample
```

`--time-scale` compresses interarrival times. For example, `20` means 20x
higher request rate than the raw timestamps. This keeps the replay explicit:
the source trace is external, while the stress level is an experimental knob.
