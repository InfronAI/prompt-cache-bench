# Infron 与 OpenRouter A/B 实验报告：qwen/qwen3.6-35b-a3b

本公开报告总结 `qwen/qwen3.6-35b-a3b` 在 2026-07-13 的 benchmark 发布结果。中英 HTML/PDF 报告、汇总数据、配对数据、请求级 telemetry 和代码快照均发布在本实验目录中。

- 模型：`qwen/qwen3.6-35b-a3b`
- API：`/v1/chat/completions`
- 实验规模：4 组 x 50 轮 x 4 个 routing sort x 2 平台 x first/second replay
- Reasoning / Thinking：平台默认行为，payload 未显式设置 `reasoning.effort`
- 有效配对：800；请求级记录：3200
- 排除记录：0 (incomplete=0, anomalous_usage=0, unequal_input_tokens=0)
- 报告日期：2026-07-13

## 路由模式结果摘要

| 路由模式 | 配对数 | 缓存胜出 | 成本胜出 | 吞吐胜出 | E2E 时延胜出 | TTFT 胜出 |
| --- | --- | --- | --- | --- | --- | --- |
| Throughput First | 200 | OpenRouter (80.73%) | Infron ($0.970041) | OpenRouter (6.735 tok/s) | OpenRouter (2375.54 ms) | OpenRouter (2135.09 ms) |
| Price First | 200 | Tie (0.00%) | OpenRouter ($0.997101) | OpenRouter (4.506 tok/s) | Infron (3034.01 ms) | Infron (2685.27 ms) |
| Latency First | 200 | OpenRouter (93.45%) | Infron ($1.047512) | OpenRouter (6.572 tok/s) | OpenRouter (2434.56 ms) | OpenRouter (2179.26 ms) |
| TTFT First | 200 | OpenRouter (81.66%) | OpenRouter ($1.609827) | Infron (107.504 tok/s) | OpenRouter (2658.67 ms) | OpenRouter (2354.80 ms) |

## 可复现文件

| 工件 | GitHub 链接 |
| --- | --- |
| Summary JSON | [Summary JSON](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.6-35b-a3b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-13/data/summary.json) |
| 配对数据集 | [配对数据集](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.6-35b-a3b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-13/data/benchmark_pairs.csv) |
| 请求级数据集 | [请求级数据集](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.6-35b-a3b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-13/data/benchmark_requests.jsonl) |
| 过滤后结构化记录 | [过滤后结构化记录](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.6-35b-a3b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-13/data/records.json) |
| 剔除记录审计 | [剔除记录审计](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.6-35b-a3b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-13/data/records_excluded.json) |
| 数据目录 | [数据目录](https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/qwen/qwen3.6-35b-a3b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-13/data) |
| 代码快照 | [代码快照](https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/qwen/qwen3.6-35b-a3b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-13/code) |
| 标准中文 HTML | [标准中文 HTML](https://infronai.github.io/prompt-cache-bench/experiments/qwen/qwen3.6-35b-a3b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-13/reports/routing-cache-cost-streaming-performance-ab-study__qwen3-6-35b-a3b__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-13.zh.html) |
| Standard English HTML | [Standard English HTML](https://infronai.github.io/prompt-cache-bench/experiments/qwen/qwen3.6-35b-a3b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-13/reports/routing-cache-cost-streaming-performance-ab-study__qwen3-6-35b-a3b__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-13.en.html) |
