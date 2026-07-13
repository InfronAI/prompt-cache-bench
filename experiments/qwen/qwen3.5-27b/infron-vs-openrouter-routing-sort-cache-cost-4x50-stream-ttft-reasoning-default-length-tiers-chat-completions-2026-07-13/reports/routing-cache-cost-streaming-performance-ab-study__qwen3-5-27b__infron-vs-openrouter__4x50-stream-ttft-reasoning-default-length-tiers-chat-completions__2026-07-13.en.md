# Infron vs OpenRouter A/B Test Report: qwen/qwen3.5-27b

This is the short summary for the new experiment. The full Chinese Markdown report, bilingual standard HTML reports, PDFs, summary JSON, paired CSV, and request-level JSONL are stored in the same export directory.

- Model: `qwen/qwen3.5-27b`
- API: `/v1/chat/completions`
- Scale: 4 groups x 50 rounds x 4 routing sorts x 2 platforms x first/second replay
- Reasoning / Thinking: platform default behavior; the payload did not explicitly set `reasoning.effort`
- Valid pairs: 800; request-level rows: 3200
- Excluded records: 0 (incomplete=0, anomalous_usage=0, unequal_input_tokens=0)
- Report date: 2026-07-13

## Routing-Mode Summary

| Routing mode | Pairs | Cache winner | Cost winner | Throughput winner | E2E latency winner | TTFT winner |
| --- | ---: | --- | --- | --- | --- | --- |
| Throughput First | 200 | Tie (0.00%) | Infron ($1.584584) | Infron (12.067 tok/s) | OpenRouter (6786.48 ms) | OpenRouter (6047.10 ms) |
| Price First | 200 | Tie (0.00%) | Infron ($0.931282) | Infron (27.608 tok/s) | Infron (18616.78 ms) | OpenRouter (6789.28 ms) |
| Latency First | 200 | Tie (0.00%) | Infron ($1.087530) | Infron (27.556 tok/s) | OpenRouter (14778.19 ms) | OpenRouter (7395.33 ms) |
| TTFT First | 200 | Tie (0.00%) | Infron ($1.284133) | Infron (28.635 tok/s) | OpenRouter (13060.52 ms) | OpenRouter (6161.58 ms) |

## Reproducibility

| Artifact | GitHub link |
| --- | --- |
| Summary JSON | [routing-cache-cost-streaming-performance-ab-study__qwen3-5-27b__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-13/data/summary.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.5-27b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-13/data/summary.json) |
| Paired dataset | [routing-cache-cost-streaming-performance-ab-study__qwen3-5-27b__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-13/data/benchmark_pairs.csv](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.5-27b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-13/data/benchmark_pairs.csv) |
| Request-level dataset | [routing-cache-cost-streaming-performance-ab-study__qwen3-5-27b__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-13/data/benchmark_requests.jsonl](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.5-27b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-13/data/benchmark_requests.jsonl) |
| Filtered structured records | [routing-cache-cost-streaming-performance-ab-study__qwen3-5-27b__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-13/data/records.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.5-27b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-13/data/records.json) |
| Excluded-record audit | [routing-cache-cost-streaming-performance-ab-study__qwen3-5-27b__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-13/data/records_excluded.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.5-27b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-13/data/records_excluded.json) |
| Data directory | [data/](https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/qwen/qwen3.5-27b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-13/data) |
| Code snapshot | [code/](https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/qwen/qwen3.5-27b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-13/code) |
| Standard Chinese HTML | [GitHub Pages](https://infronai.github.io/prompt-cache-bench/experiments/qwen/qwen3.5-27b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-13/reports/routing-cache-cost-streaming-performance-ab-study__qwen3-5-27b__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-13.zh.html) |
| Standard English HTML | [GitHub Pages](https://infronai.github.io/prompt-cache-bench/experiments/qwen/qwen3.5-27b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-13/reports/routing-cache-cost-streaming-performance-ab-study__qwen3-5-27b__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-13.en.html) |
