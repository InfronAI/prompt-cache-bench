# moonshotai/kimi-k2.5 Routing, Cache, Cost, and Streaming Performance A/B Benchmark

This experiment compares Infron and OpenRouter for `moonshotai/kimi-k2.5` using the standard prompt-cache-bench A/B methodology.

## Experiment Design

- Model: `moonshotai/kimi-k2.5`
- A/B pair: Infron vs OpenRouter
- Protocol: `/v1/chat/completions`
- Runs: 4 groups x 50 rounds
- Streaming: enabled, with TTFT collection
- Routing modes: throughput, price, latency, ttft
- Reasoning/thinking: platform default
- Prompt tiers: short (~1500 tokens), medium (~8000 tokens), long (~32000 tokens)

## Data Quality Note

The run completed 1600 request attempts. After strict A/B pairing and input-token consistency filtering, the retained dataset contains 75 paired samples / 300 request-level observations. Excluded records: total=1450, incomplete=1155, unequal_input_tokens=295, anomalous_usage=0.

## Reports

- [Chinese HTML](reports/routing-cache-cost-streaming-performance-ab-study__kimi-k2-5__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-07.zh.html)
- [English HTML](reports/routing-cache-cost-streaming-performance-ab-study__kimi-k2-5__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-07.en.html)
- [Chinese Markdown](reports/routing-cache-cost-streaming-performance-ab-study__kimi-k2-5__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-07.zh.md)
- [English Markdown](reports/routing-cache-cost-streaming-performance-ab-study__kimi-k2-5__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-07.en.md)
- [Chinese PDF](reports/routing-cache-cost-streaming-performance-ab-study__kimi-k2-5__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-07.zh.pdf)
- [English PDF](reports/routing-cache-cost-streaming-performance-ab-study__kimi-k2-5__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-07.en.pdf)

## Data

- [Dataset directory](data/)
- [Manifest](metadata/manifest.json)
