# Infron 与 OpenRouter A/B 实验报告：z-ai/glm-5.1

本报告按 prompt-cache-bench 标准发布，包含中英文 HTML、Markdown、PDF、数据集、代码快照和 manifest。

- 模型：`z-ai/glm-5.1`
- API：`/v1/chat/completions`
- 实验设计：4 x 50，streaming，routing sort: throughput / price / latency / ttft，平台默认 reasoning，short / medium / long prompt tiers
- 有效配对样本：`778`

## 路由模式结果摘要

| 路由模式 | 缓存胜出 | 成本胜出 | 吞吐胜出 | E2E 时延胜出 | TTFT 胜出 |
| --- | --- | --- | --- | --- | --- |
| 吞吐优先 | n/a | n/a | n/a | n/a | n/a |
| 价格优先 | n/a | n/a | n/a | n/a | n/a |
| 时延优先 | n/a | n/a | n/a | n/a | n/a |
| TTFT 优先 | n/a | n/a | n/a | n/a | n/a |

## 可复现文件

| 工件 | 链接 |
| --- | --- |
| ZH HTML | https://infronai.github.io/prompt-cache-bench/experiments/z-ai/glm-5.1/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/reports/routing-cache-cost-streaming-performance-ab-study__glm-5-1__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-06.zh.html |
| EN HTML | https://infronai.github.io/prompt-cache-bench/experiments/z-ai/glm-5.1/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/reports/routing-cache-cost-streaming-performance-ab-study__glm-5-1__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-06.en.html |
| ZH PDF | https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5.1/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/reports/routing-cache-cost-streaming-performance-ab-study__glm-5-1__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-06.zh.pdf |
| EN PDF | https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5.1/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/reports/routing-cache-cost-streaming-performance-ab-study__glm-5-1__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-06.en.pdf |
| Summary | https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5.1/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/summary.json |
| Paired dataset | https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5.1/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/benchmark_pairs.csv |
| Request dataset | https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5.1/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/benchmark_requests.jsonl |
| Records | https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5.1/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/records.json |

## 可复现性附录

完整数据、代码快照和 manifest 位于 [experiments/z-ai/glm-5.1/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06](https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/z-ai/glm-5.1/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06)。
