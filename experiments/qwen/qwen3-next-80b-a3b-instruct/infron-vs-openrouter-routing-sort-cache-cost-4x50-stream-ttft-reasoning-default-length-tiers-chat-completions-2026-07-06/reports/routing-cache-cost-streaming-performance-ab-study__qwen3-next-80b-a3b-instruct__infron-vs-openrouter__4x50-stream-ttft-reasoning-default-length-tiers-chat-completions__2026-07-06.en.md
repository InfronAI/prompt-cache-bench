# Infron vs OpenRouter A/B Test Report: qwen/qwen3-next-80b-a3b-instruct

This report is published under the prompt-cache-bench standard, with bilingual HTML, Markdown, PDF, datasets, code snapshots, and manifest.

- Model: `qwen/qwen3-next-80b-a3b-instruct`
- API: `/v1/chat/completions`
- Design: 4 x 50, streaming, routing sort: throughput / price / latency / ttft, platform-default reasoning, short / medium / long prompt tiers

## Routing-Mode Summary

| Routing mode | Cache winner | Cost winner | Throughput winner | E2E latency winner | TTFT winner |
| --- | --- | --- | --- | --- | --- |
| Throughput First | Tie | Infron | OpenRouter | OpenRouter | OpenRouter |
| Price First | Tie | Infron | Infron | Infron | Infron |
| Latency First | OpenRouter | Infron | OpenRouter | OpenRouter | OpenRouter |
| TTFT First | OpenRouter | Infron | OpenRouter | OpenRouter | OpenRouter |

## Reproducibility Files

| Artifact | Link |
| --- | --- |
| ZH HTML | https://infronai.github.io/prompt-cache-bench/experiments/qwen/qwen3-next-80b-a3b-instruct/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/reports/routing-cache-cost-streaming-performance-ab-study__qwen3-next-80b-a3b-instruct__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-06.zh.html |
| EN HTML | https://infronai.github.io/prompt-cache-bench/experiments/qwen/qwen3-next-80b-a3b-instruct/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/reports/routing-cache-cost-streaming-performance-ab-study__qwen3-next-80b-a3b-instruct__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-06.en.html |
| ZH PDF | https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3-next-80b-a3b-instruct/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/reports/routing-cache-cost-streaming-performance-ab-study__qwen3-next-80b-a3b-instruct__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-06.zh.pdf |
| EN PDF | https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3-next-80b-a3b-instruct/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/reports/routing-cache-cost-streaming-performance-ab-study__qwen3-next-80b-a3b-instruct__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-06.en.pdf |
| Summary | https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3-next-80b-a3b-instruct/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/summary.json |
| Paired dataset | https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3-next-80b-a3b-instruct/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/benchmark_pairs.csv |
| Request dataset | https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3-next-80b-a3b-instruct/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/benchmark_requests.jsonl |
| Records | https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3-next-80b-a3b-instruct/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/records.json |

## Reproducibility Appendix

Full data, code snapshots, and manifest are available at [experiments/qwen/qwen3-next-80b-a3b-instruct/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06](https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/qwen/qwen3-next-80b-a3b-instruct/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06).
