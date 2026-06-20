# Dataset

This directory contains the full benchmark dataset for the DeepSeek V4 Flash prompt-cache routing A/B study.

| File | Purpose |
| --- | --- |
| `benchmark_pairs.csv` | Pair-level benchmark dataset. One row represents one strict A/B pair. |
| `benchmark_requests.jsonl` | Request-level telemetry for first/second requests. |
| `records.json` | Filtered structured records that pass usage and input-token equality checks. |
| `records_excluded.json` | Records excluded from final analysis. |
| `records_anomalous_usage.json` | Records excluded due to anomalous usage, such as invalid prompt token counts. |
| `records_unequal_input_tokens.json` | Records excluded because A/B input tokens were not strictly equal. |
| `records_incomplete.json` | Incomplete records. |
| `summary.json` | Aggregated report metrics. |

No API keys or authorization headers are included in these files.

