# Infron 与 OpenRouter 路由、缓存、成本与流式性能 A/B 实验报告

## 摘要

本报告评估 `z-ai/glm-5.2` 在 Infron 与 OpenRouter 的 Prompt Caching 工作负载表现。实验使用 `/v1/chat/completions`，保留模型与平台默认 reasoning/thinking 行为，并启用 prompt 长度分层。

过滤后保留 **757 个配对样本** 和 **3028 条请求级观测**，剔除 **86 条记录**。

核心结论：Infron 在全部路由模式下实际成本更低；OpenRouter 在全部路由模式下吞吐量、端到端 E2E 时延和 Streaming TTFT 更优。缓存命中率方面，Infron 在吞吐优先、价格优先占优，OpenRouter 在端到端时延优先、Streaming TTFT 优先略占优。

## 质量门禁

| 项目 | 值 |
| --- | --- |
| 模型 | `z-ai/glm-5.2` |
| API 协议 | 仅 `/v1/chat/completions` |
| 组数 / 轮数 | 4 组 x 50 轮 |
| Prompt 分层 | `short`≈1500, `medium`≈8000, `long`≈32000 tokens |
| Reasoning / thinking | 平台与模型默认行为；请求中不显式禁用 |
| 配对规则 | strict sort/group/round pair，first/second `usage.prompt_tokens` 差异均不超过 50 |
| 保留配对样本 | 757 |
| 请求级观测 | 3028 |
| 剔除记录 | 86 |

## 路由级结果矩阵

| 路由模式 | 配对样本 | Token 命中率 | 实际成本 | 吞吐量 | E2E 时延 | TTFT |
| --- | ---: | --- | --- | --- | --- | --- |
| 吞吐优先 | 186 | **Infron 94.17%** / OpenRouter 58.11% | **Infron $1.301319** / OpenRouter $4.617887 | Infron 1.756 tok/s / **OpenRouter 3.028 tok/s** | Infron 7726.33 ms / **OpenRouter 5284.79 ms** | Infron 7082.53 ms / **OpenRouter 4977.95 ms** |
| 价格优先 | 190 | **Infron 99.58%** / OpenRouter 90.96% | **Infron $0.878579** / OpenRouter $1.521277 | Infron 2.029 tok/s / **OpenRouter 2.346 tok/s** | Infron 6974.85 ms / **OpenRouter 6821.29 ms** | Infron 6378.09 ms / **OpenRouter 6331.30 ms** |
| 端到端时延优先 | 189 | Infron 99.58% / **OpenRouter 99.83%** | **Infron $0.868005** / OpenRouter $1.827801 | Infron 1.884 tok/s / **OpenRouter 5.129 tok/s** | Infron 7395.10 ms / **OpenRouter 3119.52 ms** | Infron 6710.94 ms / **OpenRouter 2709.15 ms** |
| 流式 TTFT 优先 | 192 | Infron 99.62% / **OpenRouter 99.82%** | **Infron $0.872405** / OpenRouter $1.625334 | Infron 2.976 tok/s / **OpenRouter 4.892 tok/s** | Infron 4644.30 ms / **OpenRouter 3270.76 ms** | Infron 4023.05 ms / **OpenRouter 2866.14 ms** |

## API 协议记录

| API 协议 | Endpoint | 说明 |
| --- | --- | --- |
| `chat_completions` | `/v1/chat/completions` | 本轮仅保留该标准 Chat Completions 协议；不包含 `/v1/messages` 或 `/v1/responses`。 |

## Prompt 长度分层缓存表现

| 分层 | 配对样本 | Token 命中率 | 调用命中率 | E2E 时延 | TTFT | Reasoning tokens |
| --- | ---: | --- | --- | --- | --- | --- |
| short | 259 | **Infron 91.86%** / OpenRouter 84.29% | **Infron 97.30%** / OpenRouter 88.80% | Infron 5094.35 ms / **OpenRouter 3443.73 ms** | Infron 4437.02 ms / **OpenRouter 3031.17 ms** | **Infron 0** / OpenRouter 8845 |
| medium | 251 | **Infron 98.23%** / OpenRouter 86.34% | **Infron 98.41%** / OpenRouter 88.84% | Infron 6449.15 ms / **OpenRouter 4341.44 ms** | Infron 5771.49 ms / **OpenRouter 3938.75 ms** | **Infron 0** / OpenRouter 8815 |
| long | 247 | **Infron 98.61%** / OpenRouter 87.95% | **Infron 98.79%** / OpenRouter 90.28% | Infron 8556.78 ms / **OpenRouter 6133.46 ms** | Infron 7984.41 ms / **OpenRouter 5738.76 ms** | **Infron 0** / OpenRouter 8829 |

## Reasoning / Thinking 观测

本轮不显式禁用或强制 reasoning/thinking；reasoning tokens 按响应 telemetry 观测。

| 路由模式 | Infron reasoning tokens | OpenRouter reasoning tokens | Infron 平均/请求 | OpenRouter 平均/请求 |
| --- | ---: | ---: | ---: | ---: |
| 吞吐优先 | **0** | 8247 | **0.0000** | 22.1694 |
| 价格优先 | **0** | 6078 | **0.0000** | 15.9947 |
| 端到端时延优先 | **0** | 6034 | **0.0000** | 15.9630 |
| 流式 TTFT 优先 | **0** | 6130 | **0.0000** | 15.9635 |

## 可复现性引用

| 工件 | GitHub 路径 | SHA256 / 说明 |
| --- | --- | --- |
| Summary | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5.2/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-04/data/summary.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5.2/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-04/data/summary.json) | `534296f46e82f6a2e15221593b519fb7ff8c03e45fc719d0b7a75f7c9137cef2` |
| 配对数据集 CSV | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5.2/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-04/data/benchmark_pairs.csv](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5.2/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-04/data/benchmark_pairs.csv) | `f892a492f0d9857164dd1f6faf33205df393957cf851230c3cc695defb3dc2ad` |
| 请求级数据集 JSONL | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5.2/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-04/data/benchmark_requests.jsonl](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5.2/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-04/data/benchmark_requests.jsonl) | `237b16fd9bc60c9fa7bc2c4e2365bf2b3bcfb1f88978b357c2cc955589c3143e` |
| 剔除记录审计 | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5.2/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-04/data/records_excluded.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5.2/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-04/data/records_excluded.json) | `ee6b2fc4533de02d659e3c2f21f24a8b1a587a5a99e6e8cbd7cea7186c64e327` |
| Benchmark 执行源码 | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5.2/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-04/code/rerun_routing_sort_cache_cost_ab.py](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5.2/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-04/code/rerun_routing_sort_cache_cost_ab.py) | `a485c5116e99375e6b171d0328e5a423babd1ee6b206c72f54053a3a045b1075` |
| HTML 报告渲染源码 | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5.2/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-04/code/render_glm52_deepseek_style_report.py](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5.2/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-04/code/render_glm52_deepseek_style_report.py) | `e5bb0d32361d70ee688e0d0a0da3302a1e542e33e53876c905814eb5c27b0532` |
| 测试源码 | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5.2/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-04/code/test_rerun_routing_sort_cache_cost_ab.py](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5.2/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-04/code/test_rerun_routing_sort_cache_cost_ab.py) | 实验代码快照路径 |
| Reports 目录 | [https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/z-ai/glm-5.2/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-04/reports](https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/z-ai/glm-5.2/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-04/reports) | 中英文 HTML / Markdown / PDF 报告 |
| Data 目录 | [https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/z-ai/glm-5.2/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-04/data](https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/z-ai/glm-5.2/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-04/data) | 配对数据、请求级 telemetry、summary 与剔除样本 |
| Manifest | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5.2/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-04/metadata/manifest.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5.2/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-04/metadata/manifest.json) | 文件大小与 SHA-256 checksum |

数据集引用：`business_representative` 内置代表性业务模板；请求级导出见 `benchmark_requests.jsonl`。

在线 HTML：中文 [https://infronai.github.io/prompt-cache-bench/experiments/z-ai/glm-5.2/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-04/reports/routing-cache-cost-streaming-performance-ab-study__glm-5-2__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers__2026-07-04.zh.html](https://infronai.github.io/prompt-cache-bench/experiments/z-ai/glm-5.2/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-04/reports/routing-cache-cost-streaming-performance-ab-study__glm-5-2__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers__2026-07-04.zh.html)；英文 [https://infronai.github.io/prompt-cache-bench/experiments/z-ai/glm-5.2/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-04/reports/routing-cache-cost-streaming-performance-ab-study__glm-5-2__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers__2026-07-04.en.html](https://infronai.github.io/prompt-cache-bench/experiments/z-ai/glm-5.2/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-04/reports/routing-cache-cost-streaming-performance-ab-study__glm-5-2__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers__2026-07-04.en.html)。
