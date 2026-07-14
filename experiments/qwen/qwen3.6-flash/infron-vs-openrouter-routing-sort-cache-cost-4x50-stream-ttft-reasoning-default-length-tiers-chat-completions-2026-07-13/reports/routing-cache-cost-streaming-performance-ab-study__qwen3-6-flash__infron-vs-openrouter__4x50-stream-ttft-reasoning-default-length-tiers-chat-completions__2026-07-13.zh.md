# Infron 与 OpenRouter A/B 实验报告：qwen/qwen3.6-flash

本报告是本次实验的短版摘要；完整中文 Markdown、标准中英文 HTML、PDF、summary JSON、配对 CSV 和请求级 JSONL 均保存在同一 export 目录。

- 模型：`qwen/qwen3.6-flash`
- API：`/v1/chat/completions`
- 实验规模：4 组 x 50 轮 x 4 个 routing sort x 2 平台 x first/second replay
- Reasoning / Thinking：平台默认行为，payload 未显式设置 `reasoning.effort`
- 有效配对：800；请求级记录：3200
- 排除记录：0（incomplete=0, anomalous_usage=0, unequal_input_tokens=0）
- 报告日期：2026-07-13

## 路由模式结果摘要

| 路由模式 | 配对数 | 缓存胜出 | 成本胜出 | 吞吐胜出 | E2E 时延胜出 | TTFT 胜出 |
| --- | ---: | --- | --- | --- | --- | --- |
| Throughput First | 200 | Tie (0.00%) | Infron ($0.665154 / $1.536957) | OpenRouter (73.810 tok/s / 84.768 tok/s) | OpenRouter (5564.89 ms / 5506.76 ms) | OpenRouter (2990.30 ms / 2734.06 ms) |
| Price First | 200 | Tie (0.00%) | Infron ($0.667731 / $1.633638) | OpenRouter (73.787 tok/s / 100.547 tok/s) | Infron (5742.80 ms / 6779.32 ms) | OpenRouter (3163.75 ms / 2931.36 ms) |
| Latency First | 200 | Tie (0.00%) | Infron ($0.668748 / $1.538766) | OpenRouter (72.183 tok/s / 81.984 tok/s) | OpenRouter (5941.66 ms / 5742.78 ms) | OpenRouter (3185.38 ms / 2871.39 ms) |
| TTFT First | 200 | Tie (0.00%) | Infron ($0.666943 / $1.537904) | OpenRouter (72.026 tok/s / 80.861 tok/s) | OpenRouter (5827.88 ms / 5798.80 ms) | OpenRouter (3133.68 ms / 2909.38 ms) |

## 跨模式结论

- 缓存命中：Infron 0/4，OpenRouter 0/4，Tie 4/4。
- 实际成本：Infron 4/4，OpenRouter 0/4，Tie 0/4。
- 吞吐：Infron 0/4，OpenRouter 4/4，Tie 0/4。
- E2E 时延：Infron 1/4，OpenRouter 3/4，Tie 0/4。
- TTFT：Infron 0/4，OpenRouter 4/4，Tie 0/4。

## 数据与报告工件

| 工件 | 路径 |
| --- | --- |
| 完整中文 Markdown | `routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260713-report-zh.md` |
| 中文摘要 Markdown | `routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260713-summary-zh.md` |
| English summary Markdown | `routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260713-summary-en.md` |
| 标准中文 HTML | `routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260713-standard-ab-report-zh.html` |
| Standard English HTML | `routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260713-standard-ab-report-en.html` |
| Summary JSON | `routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260713/summary.json` |
| Paired CSV | `routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260713/benchmark_pairs.csv` |
| Request JSONL | `routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260713/benchmark_requests.jsonl` |

## 可复现文件

- 中文 HTML：https://infronai.github.io/prompt-cache-bench/experiments/qwen/qwen3.6-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-13/reports/routing-cache-cost-streaming-performance-ab-study__qwen3-6-flash__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-13.zh.html
- English HTML：https://infronai.github.io/prompt-cache-bench/experiments/qwen/qwen3.6-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-13/reports/routing-cache-cost-streaming-performance-ab-study__qwen3-6-flash__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-13.en.html
- Summary JSON：https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.6-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-13/data/summary.json
- 配对数据集：https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.6-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-13/data/benchmark_pairs.csv
- 请求级数据集：https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.6-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-13/data/benchmark_requests.jsonl
- 过滤后记录：https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.6-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-13/data/records.json
- 排除记录审计：https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.6-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-13/data/records_excluded.json
- 代码快照：https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/qwen/qwen3.6-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-13/code
