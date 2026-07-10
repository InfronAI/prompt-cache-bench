# moonshotai/kimi-k2.7-code Routing, Cache, Cost, and Streaming Performance A/B Benchmark

This experiment compares Infron and OpenRouter for `moonshotai/kimi-k2.7-code` using the standard prompt-cache-bench A/B methodology.

- Model: `moonshotai/kimi-k2.7-code`
- Groups: 4
- Rounds per group: 50
- Routing modes: throughput, price, latency, ttft
- Streaming: enabled
- API protocol: Chat Completions
- Prompt length tiers: short, medium, long
- Reasoning: platform default

## Reports

- [Chinese HTML](reports/routing-cache-cost-streaming-performance-ab-study__kimi-k2-7-code__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-10.zh.html)
- [English HTML](reports/routing-cache-cost-streaming-performance-ab-study__kimi-k2-7-code__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-10.en.html)
- [Chinese Markdown](reports/routing-cache-cost-streaming-performance-ab-study__kimi-k2-7-code__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-10.zh.md)
- [English Markdown](reports/routing-cache-cost-streaming-performance-ab-study__kimi-k2-7-code__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-10.en.md)
- [Chinese PDF](reports/routing-cache-cost-streaming-performance-ab-study__kimi-k2-7-code__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-10.zh.pdf)
- [English PDF](reports/routing-cache-cost-streaming-performance-ab-study__kimi-k2-7-code__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-10.en.pdf)

## Data

- [Summary](data/summary.json)
- [Paired dataset](data/benchmark_pairs.csv)
- [Request-level dataset](data/benchmark_requests.jsonl)
- [Filtered records](data/records.json)
- [Excluded records](data/records_excluded.json)
