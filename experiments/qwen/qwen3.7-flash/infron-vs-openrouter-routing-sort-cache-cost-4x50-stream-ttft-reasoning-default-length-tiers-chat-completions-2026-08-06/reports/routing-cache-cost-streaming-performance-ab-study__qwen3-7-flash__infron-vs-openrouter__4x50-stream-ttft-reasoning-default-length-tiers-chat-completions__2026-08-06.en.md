# Infron vs OpenRouter A/B Test Report: qwen/qwen3.7-flash

This is the public run summary. Full HTML, PDFs, aggregate results, and auditable data are in the same experiment directory.

- Model: `qwen/qwen3.7-flash`
- API: `/v1/chat/completions`
- Scale: 4 groups × 50 rounds × 4 routing modes × 2 platforms × first/second replay
- Reasoning control: platform default; no explicit `reasoning.effort` field was sent.
- Valid pairs: 685
- Excluded records: 230 (incomplete=115, anomalous_usage=0, unequal_input_tokens=115)
- Report date: 2026-08-06

## Routing Mode Summary

| Routing mode | Valid pairs | Cache winner | Cost winner | Throughput winner | E2E latency winner | TTFT winner |
| --- | ---: | --- | --- | --- | --- | --- |
| Throughput First | 163 | OpenRouter | Infron | Infron | OpenRouter | OpenRouter |
| Price First | 178 | OpenRouter | Infron | Infron | OpenRouter | Infron |
| Latency First | 177 | Infron | Infron | Infron | OpenRouter | OpenRouter |
| TTFT First | 167 | OpenRouter | Infron | Infron | OpenRouter | OpenRouter |

## Reproducibility Appendix

- [English HTML](https://infronai.github.io/prompt-cache-bench/experiments/qwen/qwen3.7-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-08-06/reports/routing-cache-cost-streaming-performance-ab-study__qwen3-7-flash__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-08-06.en.html)
- [Chinese HTML](https://infronai.github.io/prompt-cache-bench/experiments/qwen/qwen3.7-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-08-06/reports/routing-cache-cost-streaming-performance-ab-study__qwen3-7-flash__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-08-06.zh.html)
- [English Markdown](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.7-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-08-06/reports/routing-cache-cost-streaming-performance-ab-study__qwen3-7-flash__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-08-06.en.md)
- [Chinese Markdown](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.7-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-08-06/reports/routing-cache-cost-streaming-performance-ab-study__qwen3-7-flash__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-08-06.zh.md)
- [Summary JSON](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.7-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-08-06/data/summary.json)
- [Paired CSV](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.7-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-08-06/data/benchmark_pairs.csv)
- [Request-level JSONL](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.7-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-08-06/data/benchmark_requests.jsonl)
- [Filtered records](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.7-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-08-06/data/records.json)
- [Excluded-record audit](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.7-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-08-06/data/records_excluded.json)
- [Code snapshot](https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/qwen/qwen3.7-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-08-06/code)
