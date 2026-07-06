# Infron 与 OpenRouter 路由、缓存、成本与流式性能 A/B 实验报告

## 摘要

本报告以 `qwen/qwen3.5-plus` 为对象，对比 Infron 与 OpenRouter 在 Prompt Caching 场景下的路由、缓存、实际成本、吞吐、端到端时延和流式 TTFT 表现。本轮仅使用 `/v1/chat/completions`，保留模型与平台默认 reasoning/thinking 行为，并启用 prompt 长度分层。

过滤后保留 **715 个配对样本**、**2860 条请求级观测**，剔除 **170 条记录**。平台实际模型 ID：Infron `qwen/qwen3.5-plus`；OpenRouter `qwen/qwen3.5-plus-20260420`。

核心结论：双方 Token 级缓存命中率在所有路由模式下持平；Infron 在所有路由模式下实际成本和端到端 E2E 时延占优；OpenRouter 在所有路由模式下吞吐和流式 TTFT 占优。本轮双方 cache read/write telemetry 均为 0，因此报告不把缓存解释为任何一方优势。

## 质量门禁

| 项目 | 值 |
| --- | --- |
| 模型 | `qwen/qwen3.5-plus` |
| 平台实际模型 ID | Infron `qwen/qwen3.5-plus`；OpenRouter `qwen/qwen3.5-plus-20260420` |
| API 协议 | `/v1/chat/completions` only |
| 实验组 / 轮数 | 4 groups x 50 rounds |
| Prompt 分层 | `short`≈1500，`medium`≈8000，`long`≈32000 tokens |
| Reasoning / thinking | 未显式指定；保留平台与模型默认行为 |
| 配对过滤 | 同一 sort/group/round 下 first/second `usage.prompt_tokens` 偏差 <= 50 |
| 保留配对样本 | 715 |
| 请求级记录 | 2860 |
| 剔除记录 | 170 |

## 路由模式级结论矩阵

| 路由模式 | 配对样本 | Token 缓存命中率 | 实际成本 | Throughput | E2E latency | TTFT |
| --- | ---: | --- | --- | --- | --- | --- |
| 吞吐优先 | 157 | **持平 0.00% / 0.00%** | **Infron $0.598793** / OpenRouter $2.382274 | Infron 3.491 / **OpenRouter 50.324** tok/s | **Infron 3481.37 ms** / OpenRouter 27183.00 ms | Infron 3201.57 ms / **OpenRouter 2634.81 ms** |
| 价格优先 | 163 | **持平 0.00% / 0.00%** | **Infron $0.334323** / OpenRouter $2.546479 | Infron 2.875 / **OpenRouter 49.998** tok/s | **Infron 4243.01 ms** / OpenRouter 27587.21 ms | Infron 3926.75 ms / **OpenRouter 2840.22 ms** |
| 时延优先 | 200 | **持平 0.00% / 0.00%** | **Infron $1.228794** / OpenRouter $3.092506 | Infron 3.165 / **OpenRouter 50.051** tok/s | **Infron 3879.73 ms** / OpenRouter 26905.27 ms | Infron 3577.67 ms / **OpenRouter 2730.12 ms** |
| TTFT 优先 | 195 | **持平 0.00% / 0.00%** | **Infron $1.210111** / OpenRouter $3.009037 | Infron 3.253 / **OpenRouter 50.101** tok/s | **Infron 3783.04 ms** / OpenRouter 27125.24 ms | Infron 3453.44 ms / **OpenRouter 2733.46 ms** |

## API 协议兼容性记录

| API protocol | Endpoint | Platform | Planned pairs | Requests | Success rate | Usage coverage | Cost coverage | Cache telemetry coverage | HTTP status | Top errors |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `chat_completions` | `/v1/chat/completions` | Infron | 800 | 1600 | 97.44% | 100.00% | 100.00% | 100.00% | 0:41, 200:1559 | [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1000) (24); [Errno 54] Connection reset by peer (14) |
| `chat_completions` | `/v1/chat/completions` | OpenRouter | 800 | 1600 | 94.38% | 100.00% | 100.00% | 100.00% | 0:40, 200:1510, 429:50 | [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1000) (38); [Errno 54] Connection reset by peer (2) |

## Prompt 长度分层结果

| Tier | 配对样本 | Token 缓存命中率 | 实际成本 | E2E latency | TTFT | Reasoning tokens |
| --- | ---: | --- | --- | --- | --- | --- |
| short | 238 | **持平 0.00%** / 0.00% | **Infron $0.133744** / OpenRouter $1.309786 | **Infron 2604.15 ms** / OpenRouter 23440.01 ms | Infron 2321.52 ms / **OpenRouter 1968.25 ms** | **Infron 0** / OpenRouter 560458 |
| medium | 245 | **持平 0.00%** / 0.00% | **Infron $0.672494** / OpenRouter $2.727598 | **Infron 3718.17 ms** / OpenRouter 27129.94 ms | Infron 3397.07 ms / **OpenRouter 2516.97 ms** | **Infron 0** / OpenRouter 662088 |
| long | 232 | **持平 0.00%** / 0.00% | **Infron $2.565783** / OpenRouter $6.992912 | **Infron 5263.31 ms** / OpenRouter 31074.85 ms | Infron 4943.35 ms / **OpenRouter 3752.45 ms** | **Infron 0** / OpenRouter 697265 |

## Reasoning / Thinking 观测

本轮未显式禁用或强制 reasoning/thinking，响应中的 reasoning tokens 作为观测 telemetry 记录。

| 路由模式 | Infron reasoning tokens | OpenRouter reasoning tokens | Infron avg/request | OpenRouter avg/request |
| --- | ---: | ---: | ---: | ---: |
| 吞吐优先 | **0** | 423458 | **0.0000** | 1348.5924 |
| 价格优先 | **0** | 443252 | **0.0000** | 1359.6687 |
| 时延优先 | **0** | 530769 | **0.0000** | 1326.9225 |
| TTFT 优先 | **0** | 522332 | **0.0000** | 1339.3128 |

## 可复现性附录

| Artifact | Link | SHA256 / Notes |
| --- | --- | --- |
| 中文 HTML 报告 | <https://infronai.github.io/prompt-cache-bench/experiments/qwen/qwen3.5-plus/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/reports/routing-cache-cost-streaming-performance-ab-study__qwen3-5-plus__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-06.zh.html> |  |
| 英文 HTML 报告 | <https://infronai.github.io/prompt-cache-bench/experiments/qwen/qwen3.5-plus/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/reports/routing-cache-cost-streaming-performance-ab-study__qwen3-5-plus__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-06.en.html> |  |
| Summary | <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.5-plus/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/summary.json> | `4f74247f769ca6ca3b71d26963e90b7daf1d571bcae1bba0144da487a78e0f22` |
| 配对数据集 CSV | <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.5-plus/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/benchmark_pairs.csv> | `aea743349fc3592d9a0f4a3fee4b03fea667eac00a09e2d1921d7797331d19d4` |
| 请求级数据集 JSONL | <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.5-plus/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/benchmark_requests.jsonl> | `cc6dcf3628aced3eb697c349cfbf18070c293b9333fc86204e344694b7874eeb` |
| 剔除记录审计 | <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.5-plus/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/records_excluded.json> | `995eb8dba3f1b33db3384304899ec076aa51f1c592a48ae22b839314e58267f5` |
| 数据目录 | <https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/qwen/qwen3.5-plus/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data> |  |
| Benchmark 执行源码 | <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.5-plus/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/code/rerun_routing_sort_cache_cost_ab.py> | `b8ff71395fb08a6ff817c03d153ac09914b2bddb6994265a86a5ecaba9471824` |
| HTML 报告渲染源码 | <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.5-plus/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/code/render_glm52_deepseek_style_report.py> | `d82c729d73b4a19087506bc2381fd1dcf1ccf0270160a064a6a4ed5490855153` |
| 测试源码 | <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.5-plus/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/code/test_rerun_routing_sort_cache_cost_ab.py> | `30b46e2b21db1b0e42899db12983d8e5bdfbaa8ceb9c64b04e5e664aa3914558` |
| A/B 报告标准 | <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.5-plus/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/code/ab-report-standard.md> | `4c8633866de695fafeec1f70477340877b89b9253f24eb6c06b367656eae785c` |

数据集引用：`business_representative` 内置代表性业务模板；请求级导出见 `benchmark_requests.jsonl`。
