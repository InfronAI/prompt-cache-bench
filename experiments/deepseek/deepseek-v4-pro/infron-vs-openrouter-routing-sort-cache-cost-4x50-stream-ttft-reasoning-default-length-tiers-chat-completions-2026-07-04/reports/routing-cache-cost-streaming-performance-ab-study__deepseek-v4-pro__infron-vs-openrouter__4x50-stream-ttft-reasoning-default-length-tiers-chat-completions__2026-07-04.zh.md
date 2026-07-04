# Infron 与 OpenRouter 路由、缓存、成本与流式性能 A/B 实验报告

## 摘要

本报告评估 `deepseek/deepseek-v4-pro` 在 Infron 与 OpenRouter 的 Prompt Caching 工作负载表现。实验使用 `/v1/chat/completions`，保留模型与平台默认 reasoning/thinking 行为，并启用 prompt 长度分层。

过滤后保留 **791 个配对样本** 和 **3164 条请求级观测**，剔除 **18 条记录**。

核心结论：Infron 在全部路由模式下实际成本更低，并在端到端 E2E 时延上领先；OpenRouter 在全部路由模式下吞吐量和 Streaming TTFT 更优。缓存命中率在不同路由模式下接近或互有领先。

## 质量门禁

| 项目 | 值 |
| --- | --- |
| 模型 | `deepseek/deepseek-v4-pro` |
| API 协议 | 仅 `/v1/chat/completions` |
| 组数 / 轮数 | 4 组 x 50 轮 |
| Prompt 分层 | `short` about 1500, `medium` about 8000, `long` about 32000 tokens |
| Reasoning / thinking | 平台与模型默认行为；请求中不显式禁用 |
| 配对规则 | strict sort/group/round pair，first/second `usage.prompt_tokens` 差异均不超过 50 |
| 保留配对样本 | 791 |
| 请求级观测 | 3164 |
| 剔除记录 | 18 |

## 路由级结果矩阵

| 路由模式 | 配对样本 | Token 命中率 | 实际成本 | 吞吐量 | E2E 时延 | TTFT |
| --- | ---: | --- | --- | --- | --- | --- |
| 吞吐优先 | 200 | Infron 90.52% / **OpenRouter 95.98%** | **Infron $1.205367** / OpenRouter $2.110727 | Infron 2.805 tok/s / **OpenRouter 39.962 tok/s** | **Infron 4557.65 ms** / OpenRouter 10533.90 ms | Infron 4139.22 ms / **OpenRouter 3138.79 ms** |
| 价格优先 | 198 | **Infron 99.44%** / OpenRouter 98.26% | **Infron $0.337858** / OpenRouter $1.693868 | Infron 3.197 tok/s / **OpenRouter 38.359 tok/s** | **Infron 4023.15 ms** / OpenRouter 10514.30 ms | Infron 3350.61 ms / **OpenRouter 3210.02 ms** |
| 端到端时延优先 | 196 | Infron 91.27% / **OpenRouter 92.33%** | **Infron $1.109211** / OpenRouter $1.780845 | Infron 2.949 tok/s / **OpenRouter 39.703 tok/s** | **Infron 4305.92 ms** / OpenRouter 10042.08 ms | Infron 3863.79 ms / **OpenRouter 3191.40 ms** |
| 流式 TTFT 优先 | 197 | Infron 98.59% / **OpenRouter 99.45%** | **Infron $0.589968** / OpenRouter $1.442047 | Infron 2.790 tok/s / **OpenRouter 36.153 tok/s** | **Infron 4588.39 ms** / OpenRouter 10079.76 ms | Infron 4099.19 ms / **OpenRouter 3196.65 ms** |

## API 协议记录

| API 协议 | Endpoint | 说明 |
| --- | --- | --- |
| `chat_completions` | `/v1/chat/completions` | 本轮仅保留该标准 Chat Completions 协议；不包含 `/v1/messages` 或 `/v1/responses`。 |

## Prompt 长度分层缓存表现

| 分层 | 配对样本 | Token 命中率 | 调用命中率 | E2E 时延 | TTFT | Reasoning tokens |
| --- | ---: | --- | --- | --- | --- | --- |
| short |  | **Infron 0.00%** / OpenRouter 0.00% | **Infron 0.00%** / OpenRouter 0.00% | **Infron 0.00 ms** / OpenRouter 0.00 ms | **Infron 0.00 ms** / OpenRouter 0.00 ms | **Infron 0** / OpenRouter 0 |
| medium |  | **Infron 0.00%** / OpenRouter 0.00% | **Infron 0.00%** / OpenRouter 0.00% | **Infron 0.00 ms** / OpenRouter 0.00 ms | **Infron 0.00 ms** / OpenRouter 0.00 ms | **Infron 0** / OpenRouter 0 |
| long |  | **Infron 0.00%** / OpenRouter 0.00% | **Infron 0.00%** / OpenRouter 0.00% | **Infron 0.00 ms** / OpenRouter 0.00 ms | **Infron 0.00 ms** / OpenRouter 0.00 ms | **Infron 0** / OpenRouter 0 |

## Reasoning / Thinking 观测

本轮不显式禁用或强制 reasoning/thinking；reasoning tokens 按响应 telemetry 观测。

| 路由模式 | Infron reasoning tokens | OpenRouter reasoning tokens | Infron 平均/请求 | OpenRouter 平均/请求 |
| --- | ---: | ---: | ---: | ---: |
| 吞吐优先 | **0** | 162216 | **0.0000** | 405.5400 |
| 价格优先 | **0** | 153691 | **0.0000** | 388.1086 |
| 端到端时延优先 | **0** | 150585 | **0.0000** | 384.1454 |
| 流式 TTFT 优先 | **0** | 138211 | **0.0000** | 350.7893 |

## 可复现性引用

| 工件 | GitHub 路径 | SHA256 / 说明 |
| --- | --- | --- |
| Summary | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-pro/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/data/summary.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-pro/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/data/summary.json) | `0984289dd19dcfd12644cbe0d4e2473b57ee98cf65ced71209d32710e8102e13` |
| 配对数据集 CSV | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-pro/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/data/benchmark_pairs.csv](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-pro/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/data/benchmark_pairs.csv) | `858cdad534209908d7dbce59a92205040a3a008e639bf860d527b4358b1ba24b` |
| 请求级数据集 JSONL | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-pro/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/data/benchmark_requests.jsonl](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-pro/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/data/benchmark_requests.jsonl) | `c1958ba57cc831fad6677f10937e6ce984137f351f2e7b1f1f05e345584b1f41` |
| 剔除记录审计 | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-pro/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/data/records_excluded.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-pro/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/data/records_excluded.json) | `104a6a0249e8026ea16e841ebdff3e855e6a526297db4a5ef6441f39994c4771` |
| Benchmark 执行源码 | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-pro/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/code/rerun_routing_sort_cache_cost_ab.py](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-pro/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/code/rerun_routing_sort_cache_cost_ab.py) | `a485c5116e99375e6b171d0328e5a423babd1ee6b206c72f54053a3a045b1075` |
| HTML 报告渲染源码 | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-pro/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/code/render_glm52_deepseek_style_report.py](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-pro/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/code/render_glm52_deepseek_style_report.py) | `e5bb0d32361d70ee688e0d0a0da3302a1e542e33e53876c905814eb5c27b0532` |
| 测试源码 | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-pro/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/code/test_rerun_routing_sort_cache_cost_ab.py](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-pro/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/code/test_rerun_routing_sort_cache_cost_ab.py) | `c086ddc5d0a9a91eba82b7e8767d7bddf2f1ca4a28af0a87056b7028825adce4` |
| Reports 目录 | [https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/deepseek/deepseek-v4-pro/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/reports](https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/deepseek/deepseek-v4-pro/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/reports) | 中英文 HTML / Markdown / PDF 报告 |
| Data 目录 | [https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/deepseek/deepseek-v4-pro/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/data](https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/deepseek/deepseek-v4-pro/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/data) | 配对数据、请求级 telemetry、summary 与剔除样本 |
| Manifest | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-pro/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/metadata/manifest.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-pro/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/metadata/manifest.json) | 文件大小与 SHA-256 checksum |

数据集引用：`business_representative` 内置代表性业务模板；请求级导出见 `benchmark_requests.jsonl`。

在线 HTML：中文 [https://infronai.github.io/prompt-cache-bench/experiments/deepseek/deepseek-v4-pro/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/reports/routing-cache-cost-streaming-performance-ab-study__deepseek-v4-pro__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-04.zh.html](https://infronai.github.io/prompt-cache-bench/experiments/deepseek/deepseek-v4-pro/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/reports/routing-cache-cost-streaming-performance-ab-study__deepseek-v4-pro__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-04.zh.html)；英文 [https://infronai.github.io/prompt-cache-bench/experiments/deepseek/deepseek-v4-pro/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/reports/routing-cache-cost-streaming-performance-ab-study__deepseek-v4-pro__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-04.en.html](https://infronai.github.io/prompt-cache-bench/experiments/deepseek/deepseek-v4-pro/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/reports/routing-cache-cost-streaming-performance-ab-study__deepseek-v4-pro__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-04.en.html)。
