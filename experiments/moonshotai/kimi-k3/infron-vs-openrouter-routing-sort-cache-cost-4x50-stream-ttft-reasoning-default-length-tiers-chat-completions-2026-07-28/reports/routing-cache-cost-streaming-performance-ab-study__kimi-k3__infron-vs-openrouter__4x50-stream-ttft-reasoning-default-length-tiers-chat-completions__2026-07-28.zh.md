# Infron 与 OpenRouter A/B 实验报告：moonshotai/kimi-k3

本报告是本次实验的短版摘要；完整标准中英文 HTML、PDF、summary JSON、配对 CSV 和请求级 JSONL 均保存在同一 export 目录。

- 模型：`moonshotai/kimi-k3`
- API：`/v1/chat/completions`
- 实验规模：4 组 x 50 轮 x 4 个 routing sort x 2 平台 x first/second replay
- Reasoning / Thinking：平台默认行为，payload 未显式设置 `reasoning.effort`
- 有效配对：800；请求级记录：3200
- 排除记录：0
- 报告日期：2026-07-28

## 路由模式结果摘要

| 路由模式 | 配对数 | 缓存胜出 | 成本胜出 | 吞吐胜出 | E2E 时延胜出 | TTFT 胜出 |
| --- | ---: | --- | --- | --- | --- | --- |
| Throughput First | 200 | Infron (90.73% / 81.07%) | Infron ($3.687283 / $8.711514) | OpenRouter (1.174 tok/s / 1.645 tok/s) | OpenRouter (13624.80 ms / 9724.88 ms) | OpenRouter (12485.09 ms / 9377.65 ms) |
| Price First | 200 | Infron (96.95% / 92.42%) | Infron ($2.003152 / $4.956052) | Infron (3.212 tok/s / 2.492 tok/s) | Infron (4981.17 ms / 6420.97 ms) | Infron (3664.40 ms / 5861.22 ms) |
| Latency First | 200 | Infron (96.95% / 90.61%) | Infron ($2.003152 / $5.158083) | Infron (3.381 tok/s / 2.682 tok/s) | Infron (4731.76 ms / 5965.07 ms) | Infron (3447.95 ms / 5448.98 ms) |
| TTFT First | 200 | Infron (96.95% / 94.34%) | Infron ($2.003152 / $4.384893) | OpenRouter (2.746 tok/s / 2.946 tok/s) | OpenRouter (5825.79 ms / 5431.57 ms) | Infron (4439.04 ms / 5107.21 ms) |

## 数据与报告工件

| 工件 | 路径 |
| --- | --- |
| 中文摘要 Markdown | `routing-cache-cost-streaming-performance-ab-study__kimi-k3__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-28.zh.md` |
| English summary Markdown | `routing-cache-cost-streaming-performance-ab-study__kimi-k3__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-28.en.md` |
| 标准中文 HTML | `routing-cache-cost-streaming-performance-ab-study__kimi-k3__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-28.zh.html` |
| Standard English HTML | `routing-cache-cost-streaming-performance-ab-study__kimi-k3__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-28.en.html` |
| Summary JSON | `data/summary.json` |
| Paired CSV | `data/benchmark_pairs.csv` |
| Request JSONL | `data/benchmark_requests.jsonl` |

## 可复现文件

- 中文 HTML：https://infronai.github.io/prompt-cache-bench/experiments/moonshotai/kimi-k3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-28/reports/routing-cache-cost-streaming-performance-ab-study__kimi-k3__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-28.zh.html
- English HTML：https://infronai.github.io/prompt-cache-bench/experiments/moonshotai/kimi-k3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-28/reports/routing-cache-cost-streaming-performance-ab-study__kimi-k3__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-28.en.html
- Summary JSON：https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/moonshotai/kimi-k3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-28/data/summary.json
- 配对数据集：https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/moonshotai/kimi-k3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-28/data/benchmark_pairs.csv
- 请求级数据集：https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/moonshotai/kimi-k3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-28/data/benchmark_requests.jsonl
- 过滤后记录：https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/moonshotai/kimi-k3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-28/data/records.json
- 排除记录审计：https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/moonshotai/kimi-k3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-28/data/records_excluded.json
- 代码快照：https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/moonshotai/kimi-k3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-28/code
