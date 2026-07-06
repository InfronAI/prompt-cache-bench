# Data

This directory contains the derived datasets and request-level telemetry for the `z-ai/glm-5` Infron vs OpenRouter A/B benchmark.

- `summary.json`: aggregate metrics and experiment settings.
- `benchmark_pairs.csv`: strict paired A/B dataset used by the report.
- `benchmark_requests.jsonl`: request-level telemetry export.
- `records.json`: filtered structured records.
- `records_excluded.json`, `records_incomplete.json`, `records_unequal_input_tokens.json`, `records_anomalous_usage.json`: exclusion audit files.
- `chat_completions_*_group_*.json`: per-routing-mode, per-platform raw group outputs.

Dataset reference: `business_representative` built-in representative business templates.
