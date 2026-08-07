# Infron 与 OpenRouter A/B 实验报告：qwen/qwen3.7-flash

本文件是本次公开实验的摘要；完整 HTML、PDF、汇总与可审计数据均在同一实验目录。

- 模型: `qwen/qwen3.7-flash`
- API: `/v1/chat/completions`
- 规模: 4 groups × 50 rounds × 4 routing modes × 2 platforms × first/second replay
- 推理控制: 平台默认行为；未显式发送 `reasoning.effort`。
- 有效配对: 685
- 剔除记录: 230 (incomplete=115, anomalous_usage=0, unequal_input_tokens=115)
- 报告日期: 2026-08-06

## 路由模式摘要

| 路由模式 | 有效配对 | 缓存胜出方 | 成本胜出方 | 吞吐胜出方 | E2E 时延胜出方 | TTFT 胜出方 |
| --- | ---: | --- | --- | --- | --- | --- |
| 吞吐优先 | 163 | OpenRouter | Infron | Infron | OpenRouter | OpenRouter |
| 价格优先 | 178 | OpenRouter | Infron | Infron | OpenRouter | Infron |
| 时延优先 | 177 | Infron | Infron | Infron | OpenRouter | OpenRouter |
| TTFT 优先 | 167 | OpenRouter | Infron | Infron | OpenRouter | OpenRouter |

## 可复现性附录

- [英文 HTML](https://infronai.github.io/prompt-cache-bench/experiments/qwen/qwen3.7-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-08-06/reports/routing-cache-cost-streaming-performance-ab-study__qwen3-7-flash__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-08-06.en.html)
- [中文 HTML](https://infronai.github.io/prompt-cache-bench/experiments/qwen/qwen3.7-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-08-06/reports/routing-cache-cost-streaming-performance-ab-study__qwen3-7-flash__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-08-06.zh.html)
- [英文 Markdown](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.7-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-08-06/reports/routing-cache-cost-streaming-performance-ab-study__qwen3-7-flash__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-08-06.en.md)
- [中文 Markdown](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.7-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-08-06/reports/routing-cache-cost-streaming-performance-ab-study__qwen3-7-flash__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-08-06.zh.md)
- [汇总 JSON](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.7-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-08-06/data/summary.json)
- [配对 CSV](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.7-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-08-06/data/benchmark_pairs.csv)
- [请求级 JSONL](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.7-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-08-06/data/benchmark_requests.jsonl)
- [过滤记录](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.7-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-08-06/data/records.json)
- [剔除审计](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.7-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-08-06/data/records_excluded.json)
- [代码快照](https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/qwen/qwen3.7-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-08-06/code)
