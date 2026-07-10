# Data Artifacts

This directory contains the public benchmark datasets for `infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-10`.

- `summary.json`: aggregate metrics and run metadata.
- `benchmark_pairs.csv`: strict A/B pair-level dataset after quality filtering.
- `benchmark_requests.jsonl`: request-level telemetry used for reproducibility.
- `records.json`: filtered structured benchmark records.
- `records_excluded.json`: excluded-record audit trail.
- `chat_completions_*_group_*.json`: grouped records by routing mode, provider, and group.

The source dataset is the built-in controlled synthetic prompt-cache probe.
