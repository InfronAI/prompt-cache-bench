# Infron vs OpenRouter A/B Test Report: z-ai/glm-5.1

This report is published under the prompt-cache-bench standard, with bilingual HTML, Markdown, PDF, datasets, code snapshots, and manifest.

- Model: `z-ai/glm-5.1`
- API: `/v1/chat/completions`
- Design: 4 x 50, streaming, routing sort: throughput / price / latency / ttft, platform-default reasoning, short / medium / long prompt tiers
- Valid paired samples: `778`

## Routing-Mode Summary

| Routing mode | Cache winner | Cost winner | Throughput winner | E2E latency winner | TTFT winner |
| --- | --- | --- | --- | --- | --- |
| Throughput First | n/a | n/a | n/a | n/a | n/a |
| Price First | n/a | n/a | n/a | n/a | n/a |
| Latency First | n/a | n/a | n/a | n/a | n/a |
| TTFT First | n/a | n/a | n/a | n/a | n/a |

## Reproducibility Files

| Artifact | Link |
| --- | --- |
| ZH HTML | https://infronai.github.io/prompt-cache-bench/experiments/z-ai/glm-5.1/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/reports/routing-cache-cost-streaming-performance-ab-study__glm-5-1__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-06.zh.html |
| EN HTML | https://infronai.github.io/prompt-cache-bench/experiments/z-ai/glm-5.1/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/reports/routing-cache-cost-streaming-performance-ab-study__glm-5-1__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-06.en.html |
| ZH PDF | https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5.1/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/reports/routing-cache-cost-streaming-performance-ab-study__glm-5-1__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-06.zh.pdf |
| EN PDF | https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5.1/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/reports/routing-cache-cost-streaming-performance-ab-study__glm-5-1__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-06.en.pdf |
| Summary | https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5.1/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/summary.json |
| Paired dataset | https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5.1/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/benchmark_pairs.csv |
| Request dataset | https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5.1/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/benchmark_requests.jsonl |
| Records | https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5.1/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/records.json |

## Reproducibility Appendix

Full data, code snapshots, and manifest are available at [experiments/z-ai/glm-5.1/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06](https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/z-ai/glm-5.1/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06).
