# Dataset

This directory contains the public benchmark datasets for `infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-04`.

## Files

- `benchmark_pairs.csv`: strict A/B pair-level dataset after quality filtering.
- `benchmark_requests.jsonl`: request-level telemetry used for reproducibility.
- `records.json`: raw benchmark records emitted by the runner.
- `records_excluded.json`: records excluded from final aggregation.
- `records_incomplete.json`: incomplete records excluded from final aggregation.
- `records_anomalous_usage.json`: records excluded for anomalous `usage.prompt_tokens`.
- `records_unequal_input_tokens.json`: pairs excluded because A/B `usage.prompt_tokens` exceeded the 50-token tolerance.
- `summary.json`: derived aggregate metrics used by the reports.
- `*_infron_group_*.json` and `*_openrouter_group_*.json`: routing-mode and group-level run outputs.

## Design

- Model: `z-ai/glm-5.2`
- Routing modes: `throughput, price, latency, ttft`
- Groups: `4`
- Rounds per group: `50`
- Streaming: `True`
- API protocol: `/v1/chat/completions` only.
- Reasoning control: platform default, no explicit `reasoning.effort` in the request payload.
- Prompt length tiers: short, medium, long.
- Included strict A/B pairs: `757`
- Request-level observations in `benchmark_requests.jsonl`: `3028`

The final comparison uses response-returned `usage.prompt_tokens` as the input-token source of truth.
