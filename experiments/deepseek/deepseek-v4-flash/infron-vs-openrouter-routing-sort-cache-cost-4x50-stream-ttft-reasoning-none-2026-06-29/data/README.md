# Dataset

This directory contains the public benchmark datasets for `infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-none-2026-06-29`.

## Files

- `benchmark_pairs.csv`: strict A/B pair-level dataset after quality filtering.
- `benchmark_requests.jsonl`: request-level telemetry used for reproducibility.
- `records.json`: raw benchmark records emitted by the runner.
- `records_excluded.json`: records excluded from final aggregation.
- `records_incomplete.json`: incomplete records excluded from final aggregation.
- `records_anomalous_usage.json`: records excluded for anomalous `usage.prompt_tokens`.
- `records_unequal_input_tokens.json`: pairs excluded because A/B `usage.prompt_tokens` did not match exactly.
- `summary.json`: derived aggregate metrics used by the reports.

## Design

- Model: `deepseek/deepseek-v4-flash`
- Routing modes: `throughput, price, latency, ttft`
- Groups: `4`
- Rounds per group: `50`
- Streaming: `True`
- Included strict A/B pairs: `797`
- Request-level observations in `benchmark_requests.jsonl`: `3188`

The final comparison uses response-returned `usage.prompt_tokens` as the input-token source of truth.
