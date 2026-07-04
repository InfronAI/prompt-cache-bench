# Dataset

This directory contains the public benchmark datasets for `infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04`.

## Files

- `benchmark_pairs.csv`: A/B pair-level dataset after quality filtering.
- `benchmark_requests.jsonl`: request-level telemetry used for reproducibility.
- `records.json`: raw benchmark records emitted by the runner.
- `records_excluded.json`: records excluded from final aggregation.
- `records_incomplete.json`: incomplete records excluded from final aggregation.
- `records_anomalous_usage.json`: records excluded for anomalous `usage.prompt_tokens`.
- `records_unequal_input_tokens.json`: pairs excluded because A/B `usage.prompt_tokens` differed by more than the configured tolerance.
- `summary.json`: derived aggregate metrics used by the reports.
- `*_infron_group_*.json` and `*_openrouter_group_*.json`: routing-mode, API protocol, and group-level run outputs.

## Design

- Model: `deepseek/deepseek-v4-flash`
- API protocol: `/v1/chat/completions` only
- Routing modes: `throughput, price, latency, ttft`
- Groups: `4`
- Rounds per group: `50`
- Streaming: `True`
- Reasoning control: platform default, no explicit `reasoning.effort` in the request payload.
- Prompt length tiers: short, medium, long.
- A/B token tolerance: first/second `usage.prompt_tokens` deltas <= 50 tokens inside the same pair.
- Included A/B pairs: `699`
- Request-level observations in `benchmark_requests.jsonl`: `2796`

The final comparison uses response-returned `usage.prompt_tokens` as the input-token source of truth.
