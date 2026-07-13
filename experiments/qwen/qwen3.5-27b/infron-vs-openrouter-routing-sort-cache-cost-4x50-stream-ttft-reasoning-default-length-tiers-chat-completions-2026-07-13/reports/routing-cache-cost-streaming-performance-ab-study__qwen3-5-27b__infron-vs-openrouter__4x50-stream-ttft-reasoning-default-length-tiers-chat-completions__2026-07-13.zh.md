# Infron 与 OpenRouter A/B 实验报告：qwen/qwen3.5-27b

本报告是本次实验的短版摘要；完整中文 Markdown、标准中英文 HTML、PDF、summary JSON、配对 CSV 和请求级 JSONL 均保存在同一 export 目录。

- 模型：`qwen/qwen3.5-27b`
- API：`/v1/chat/completions`
- 实验规模：4 组 x 50 轮 x 4 个 routing sort x 2 平台 x first/second replay
- Reasoning / Thinking：平台默认行为，payload 未显式设置 `reasoning.effort`
- 有效配对：800；请求级记录：3200
- 排除记录：0（incomplete=0, anomalous_usage=0, unequal_input_tokens=0）
- 报告日期：2026-07-13

## 路由模式结果摘要

| 路由模式 | 配对数 | 缓存胜出 | 成本胜出 | 吞吐胜出 | E2E 时延胜出 | TTFT 胜出 |
| --- | ---: | --- | --- | --- | --- | --- |
| Throughput First | 200 | Tie (0.00%) | Infron ($1.584584) | Infron (12.067 tok/s) | OpenRouter (6786.48 ms) | OpenRouter (6047.10 ms) |
| Price First | 200 | Tie (0.00%) | Infron ($0.931282) | Infron (27.608 tok/s) | Infron (18616.78 ms) | OpenRouter (6789.28 ms) |
| Latency First | 200 | Tie (0.00%) | Infron ($1.087530) | Infron (27.556 tok/s) | OpenRouter (14778.19 ms) | OpenRouter (7395.33 ms) |
| TTFT First | 200 | Tie (0.00%) | Infron ($1.284133) | Infron (28.635 tok/s) | OpenRouter (13060.52 ms) | OpenRouter (6161.58 ms) |

## 可复现文件

| 工件 | GitHub 链接 |
| --- | --- |
| Summary JSON | [routing-cache-cost-streaming-performance-ab-study__qwen3-5-27b__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-13/data/summary.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.5-27b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-13/data/summary.json) |
| 配对数据集 | [routing-cache-cost-streaming-performance-ab-study__qwen3-5-27b__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-13/data/benchmark_pairs.csv](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.5-27b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-13/data/benchmark_pairs.csv) |
| 请求级数据集 | [routing-cache-cost-streaming-performance-ab-study__qwen3-5-27b__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-13/data/benchmark_requests.jsonl](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.5-27b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-13/data/benchmark_requests.jsonl) |
| 过滤后结构化记录 | [routing-cache-cost-streaming-performance-ab-study__qwen3-5-27b__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-13/data/records.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.5-27b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-13/data/records.json) |
| 剔除记录审计 | [routing-cache-cost-streaming-performance-ab-study__qwen3-5-27b__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-13/data/records_excluded.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.5-27b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-13/data/records_excluded.json) |
| 数据目录 | [data/](https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/qwen/qwen3.5-27b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-13/data) |
| 代码快照 | [code/](https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/qwen/qwen3.5-27b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-13/code) |
| 标准中文 HTML | [GitHub Pages](https://infronai.github.io/prompt-cache-bench/experiments/qwen/qwen3.5-27b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-13/reports/routing-cache-cost-streaming-performance-ab-study__qwen3-5-27b__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-13.zh.html) |
| Standard English HTML | [GitHub Pages](https://infronai.github.io/prompt-cache-bench/experiments/qwen/qwen3.5-27b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-13/reports/routing-cache-cost-streaming-performance-ab-study__qwen3-5-27b__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-13.en.html) |
