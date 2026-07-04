# Infron 与 OpenRouter 路由、缓存、成本与流式性能 A/B 实验报告

## 摘要

本报告评估 `openai/gpt-5.4-mini` 在 Infron 与 OpenRouter 的 Prompt Caching 工作负载表现。实验使用 `/v1/chat/completions`，保留模型与平台默认 reasoning/thinking 行为，并启用 prompt 长度分层。

过滤后保留 **792 个配对样本** 和 **3168 条请求级观测**，剔除 **16 条记录**。

核心结论：Infron 在吞吐量上全部路由模式占优，并在多数路由模式下成本更低；OpenRouter 在端到端 E2E 时延和 Streaming TTFT 上整体更低。缓存命中率两边均处于高位，不同路由模式下优势方有所变化。

## 质量门禁

| 项目 | 值 |
| --- | --- |
| 模型 | `openai/gpt-5.4-mini` |
| API 协议 | 仅 `/v1/chat/completions` |
| 组数 / 轮数 | 4 组 x 50 轮 |
| Prompt 分层 | `short` about 1500, `medium` about 8000, `long` about 32000 tokens |
| Reasoning / thinking | 平台与模型默认行为；请求中不显式禁用 |
| 配对规则 | strict sort/group/round pair，first/second `usage.prompt_tokens` 差异均不超过 50 |
| 保留配对样本 | 792 |
| 请求级观测 | 3168 |
| 剔除记录 | 16 |

## 路由级结果矩阵

| 路由模式 | 配对样本 | Token 命中率 | 实际成本 | 吞吐量 | E2E 时延 | TTFT |
| --- | ---: | --- | --- | --- | --- | --- |
| 吞吐优先 | 200 | Infron 96.68% / **OpenRouter 97.91%** | **Infron $0.665196** / OpenRouter $0.736837 | **Infron 17.822 tok/s** / OpenRouter 5.076 tok/s | Infron 4042.33 ms / **OpenRouter 2737.70 ms** | Infron 2722.39 ms / **OpenRouter 2337.97 ms** |
| 价格优先 | 200 | **Infron 97.99%** / OpenRouter 97.95% | **Infron $0.549838** / OpenRouter $0.643934 | **Infron 18.259 tok/s** / OpenRouter 4.922 tok/s | Infron 3896.09 ms / **OpenRouter 2830.58 ms** | Infron 2763.05 ms / **OpenRouter 2492.73 ms** |
| 端到端时延优先 | 192 | **Infron 97.98%** / OpenRouter 96.73% | **Infron $0.514386** / OpenRouter $0.642328 | **Infron 20.873 tok/s** / OpenRouter 5.189 tok/s | Infron 3465.18 ms / **OpenRouter 2690.54 ms** | Infron 2473.68 ms / **OpenRouter 2350.08 ms** |
| 流式 TTFT 优先 | 200 | Infron 96.43% / **OpenRouter 97.99%** | Infron $0.868611 / **OpenRouter $0.579755** | **Infron 25.861 tok/s** / OpenRouter 6.077 tok/s | Infron 2694.75 ms / **OpenRouter 2301.99 ms** | Infron 2141.42 ms / **OpenRouter 2098.17 ms** |

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

| 路由模式 | Reasoning tokens | Avg reasoning tokens/request |
| --- | --- | --- |
| 吞吐优先 | **Infron 0** / OpenRouter 0 | **Infron 0.0000** / OpenRouter 0.0000 |
| 价格优先 | **Infron 0** / OpenRouter 0 | **Infron 0.0000** / OpenRouter 0.0000 |
| 端到端时延优先 | **Infron 0** / OpenRouter 0 | **Infron 0.0000** / OpenRouter 0.0000 |
| 流式 TTFT 优先 | **Infron 0** / OpenRouter 0 | **Infron 0.0000** / OpenRouter 0.0000 |

## 可复现性引用

| 工件 | GitHub 路径 | SHA256 / 说明 |
| --- | --- | --- |
| Summary | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-5.4-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/data/summary.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-5.4-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/data/summary.json) | `b5fcdd6787abbc331d2a4326ce6473a0bd40226faa9adc3bf370bfa1c381faf3` |
| 配对数据集 CSV | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-5.4-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/data/benchmark_pairs.csv](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-5.4-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/data/benchmark_pairs.csv) | `3bd26737e7ca08438856d3d9f6367df63ac391adc7e0db841c81ae34a3880c23` |
| 请求级数据集 JSONL | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-5.4-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/data/benchmark_requests.jsonl](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-5.4-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/data/benchmark_requests.jsonl) | `4ff92a2e44c3d37cf6eb732ca00a85393114c4712ec35780b884899c551f93b5` |
| 剔除记录审计 | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-5.4-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/data/records_excluded.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-5.4-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/data/records_excluded.json) | `11e2ed24815a7cf38765b2149b9d28bd51f312a36dbcedad6ef6d32b1648c138` |
| Benchmark 执行源码 | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-5.4-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/code/rerun_routing_sort_cache_cost_ab.py](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-5.4-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/code/rerun_routing_sort_cache_cost_ab.py) | `a485c5116e99375e6b171d0328e5a423babd1ee6b206c72f54053a3a045b1075` |
| HTML 报告渲染源码 | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-5.4-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/code/render_glm52_deepseek_style_report.py](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-5.4-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/code/render_glm52_deepseek_style_report.py) | `e5bb0d32361d70ee688e0d0a0da3302a1e542e33e53876c905814eb5c27b0532` |
| 测试源码 | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-5.4-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/code/test_rerun_routing_sort_cache_cost_ab.py](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-5.4-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/code/test_rerun_routing_sort_cache_cost_ab.py) | `c086ddc5d0a9a91eba82b7e8767d7bddf2f1ca4a28af0a87056b7028825adce4` |
| Reports 目录 | [https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/openai/gpt-5.4-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/reports](https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/openai/gpt-5.4-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/reports) | 中英文 HTML / Markdown / PDF 报告 |
| Data 目录 | [https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/openai/gpt-5.4-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/data](https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/openai/gpt-5.4-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/data) | 配对数据、请求级 telemetry、summary 与剔除样本 |
| Manifest | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-5.4-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/metadata/manifest.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-5.4-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/metadata/manifest.json) | 文件大小与 SHA-256 checksum |

数据集引用：`business_representative` 内置代表性业务模板；请求级导出见 `benchmark_requests.jsonl`。

在线 HTML：中文 [https://infronai.github.io/prompt-cache-bench/experiments/openai/gpt-5.4-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/reports/routing-cache-cost-streaming-performance-ab-study__gpt-5-4-mini__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-04.zh.html](https://infronai.github.io/prompt-cache-bench/experiments/openai/gpt-5.4-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/reports/routing-cache-cost-streaming-performance-ab-study__gpt-5-4-mini__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-04.zh.html)；英文 [https://infronai.github.io/prompt-cache-bench/experiments/openai/gpt-5.4-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/reports/routing-cache-cost-streaming-performance-ab-study__gpt-5-4-mini__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-04.en.html](https://infronai.github.io/prompt-cache-bench/experiments/openai/gpt-5.4-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/reports/routing-cache-cost-streaming-performance-ab-study__gpt-5-4-mini__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-04.en.html)。
