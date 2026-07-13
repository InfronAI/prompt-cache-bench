# Infron vs OpenRouter A/B Test Report: qwen/qwen3.6-35b-a3b

This public report summarizes the 2026-07-13 benchmark release for `qwen/qwen3.6-35b-a3b`. Full bilingual HTML/PDF reports, aggregate data, paired rows, request-level telemetry, and code snapshots are published in this experiment directory.

- Model: `qwen/qwen3.6-35b-a3b`
- API: `/v1/chat/completions`
- Scale: 4 groups x 50 rounds x 4 routing sorts x 2 platforms x first/second replay
- Reasoning / Thinking: platform default behavior; the payload did not explicitly set `reasoning.effort`
- Valid pairs: 800; request-level rows: 3200
- Excluded records: 0 (incomplete=0, anomalous_usage=0, unequal_input_tokens=0)
- Report date: 2026-07-13

## Routing-Mode Summary

| Routing mode | Pairs | Cache winner | Cost winner | Throughput winner | E2E latency winner | TTFT winner |
| --- | --- | --- | --- | --- | --- | --- |
| Throughput First | 200 | OpenRouter (80.73%) | Infron ($0.970041) | OpenRouter (6.735 tok/s) | OpenRouter (2375.54 ms) | OpenRouter (2135.09 ms) |
| Price First | 200 | Tie (0.00%) | OpenRouter ($0.997101) | OpenRouter (4.506 tok/s) | Infron (3034.01 ms) | Infron (2685.27 ms) |
| Latency First | 200 | OpenRouter (93.45%) | Infron ($1.047512) | OpenRouter (6.572 tok/s) | OpenRouter (2434.56 ms) | OpenRouter (2179.26 ms) |
| TTFT First | 200 | OpenRouter (81.66%) | OpenRouter ($1.609827) | Infron (107.504 tok/s) | OpenRouter (2658.67 ms) | OpenRouter (2354.80 ms) |

## Reproducibility

| Artifact | GitHub link |
| --- | --- |
| Summary JSON | [Summary JSON](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.6-35b-a3b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-13/data/summary.json) |
| Paired dataset | [Paired dataset](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.6-35b-a3b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-13/data/benchmark_pairs.csv) |
| Request-level dataset | [Request-level dataset](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.6-35b-a3b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-13/data/benchmark_requests.jsonl) |
| Filtered structured records | [Filtered structured records](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.6-35b-a3b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-13/data/records.json) |
| Excluded-record audit | [Excluded-record audit](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.6-35b-a3b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-13/data/records_excluded.json) |
| Data directory | [Data directory](https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/qwen/qwen3.6-35b-a3b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-13/data) |
| Code snapshot | [Code snapshot](https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/qwen/qwen3.6-35b-a3b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-13/code) |
| Standard Chinese HTML | [Standard Chinese HTML](https://infronai.github.io/prompt-cache-bench/experiments/qwen/qwen3.6-35b-a3b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-13/reports/routing-cache-cost-streaming-performance-ab-study__qwen3-6-35b-a3b__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-13.zh.html) |
| Standard English HTML | [Standard English HTML](https://infronai.github.io/prompt-cache-bench/experiments/qwen/qwen3.6-35b-a3b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-13/reports/routing-cache-cost-streaming-performance-ab-study__qwen3-6-35b-a3b__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-13.en.html) |
