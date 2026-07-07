# Infron 与 OpenRouter 路由、缓存、成本与流式性能 A/B 实验报告

## 摘要

本报告评估 `minimax/minimax-m2.7` 在标准 Infron vs OpenRouter Prompt Caching A/B benchmark 下的表现。缓存命中率：Infron 在 2/4 个路由模式中领先；实际成本：Infron 在 4/4 个路由模式中领先；吞吐量：OpenRouter 在 3/4 个路由模式中领先；端到端时延：OpenRouter 在 3/4 个路由模式中领先；TTFT：OpenRouter 在 3/4 个路由模式中领先。平台选择应围绕目标指标展开，不能只看单一全局均值。

A/B 过滤后保留 800 个配对样本和 3200 条请求级观测；剔除记录 0 条。全部核心指标来自响应 telemetry。

## 结论矩阵

| 路由模式 | 缓存命中率 | 实际成本 | 吞吐量 | E2E 时延 | TTFT |
| --- | --- | --- | --- | --- | --- |
| Throughput First | **Infron** | **Infron** | **OpenRouter** | **OpenRouter** | **OpenRouter** |
| Price First | **Infron** | **Infron** | **Infron** | **Infron** | **Infron** |
| Latency First | **OpenRouter** | **Infron** | **OpenRouter** | **OpenRouter** | **OpenRouter** |
| TTFT First | **OpenRouter** | **Infron** | **OpenRouter** | **OpenRouter** | **OpenRouter** |

## 总体指标

| 路由模式 | 平台 | 配对数 | Token 缓存命中率 | 实际成本 | 平均吞吐 | 平均 E2E 时延 | 平均 TTFT |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Throughput First | Infron | 200 | **97.41%** | **$0.36936000** | 2.67 tok/s | 5980.69 ms | 5786.47 ms |
| Throughput First | OpenRouter | 200 | 93.54% | $3.59489664 | **3.39 tok/s** | **4723.73 ms** | **4423.83 ms** |
| Price First | Infron | 200 | **98.58%** | **$0.35053300** | **2.60 tok/s** | **6150.60 ms** | **5959.01 ms** |
| Price First | OpenRouter | 200 | 66.56% | $0.72619654 | 1.79 tok/s | 8930.26 ms | 8499.25 ms |
| Latency First | Infron | 200 | 98.43% | **$0.39538500** | 5.30 tok/s | 3016.90 ms | 2837.35 ms |
| Latency First | OpenRouter | 200 | **98.90%** | $3.53757760 | **5.49 tok/s** | **2916.05 ms** | **2564.25 ms** |
| TTFT First | Infron | 200 | 98.43% | **$0.37421000** | 4.88 tok/s | 3281.74 ms | 2994.02 ms |
| TTFT First | OpenRouter | 200 | **98.88%** | $3.63688800 | **5.56 tok/s** | **2875.68 ms** | **2440.43 ms** |

## Prompt 长度分层

| 分层 | 平台 | 配对数 | Token 缓存命中率 | 实际成本 | 平均 E2E 时延 | 平均 TTFT |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| short（目标 1500 tokens） | Infron | 268 | 77.71% | **$0.13344700** | 3632.64 ms | 3421.09 ms |
| short（目标 1500 tokens） | OpenRouter | 268 | **81.22%** | $0.46397534 | **3568.51 ms** | **3223.26 ms** |
| medium（目标 8000 tokens） | Infron | 268 | **98.91%** | **$0.29008400** | **4367.24 ms** | **4173.93 ms** |
| medium（目标 8000 tokens） | OpenRouter | 268 | 87.49% | $2.26869193 | 4592.34 ms | 4219.52 ms |
| long（目标 32000 tokens） | Infron | 264 | **99.05%** | **$1.06595700** | **5840.97 ms** | **5605.71 ms** |
| long（目标 32000 tokens） | OpenRouter | 264 | 90.38% | $8.76289151 | 6447.10 ms | 6026.10 ms |

## 可复现性

本轮使用标准 4 组 x 50 轮设计、流式 Chat Completions、平台默认 reasoning/thinking、prompt 长度分层 `short:1500,medium:8000,long:32000`，且仅测试 `/v1/chat/completions`。A/B 纳入规则允许同一配对内 first/second 的 prompt tokens 偏差不超过 50 tokens。

| 工件 | 在线路径 |
| --- | --- |
| 中文 HTML 报告 | <https://infronai.github.io/prompt-cache-bench/experiments/minimax/minimax-m2.7/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/reports/routing-cache-cost-streaming-performance-ab-study__minimax-m2-7__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-07.zh.html> |
| English HTML 报告 | <https://infronai.github.io/prompt-cache-bench/experiments/minimax/minimax-m2.7/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/reports/routing-cache-cost-streaming-performance-ab-study__minimax-m2-7__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-07.en.html> |
| Summary JSON | <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/minimax/minimax-m2.7/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/summary.json> |
| 配对数据集 CSV | <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/minimax/minimax-m2.7/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/benchmark_pairs.csv> |
| 请求级 JSONL | <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/minimax/minimax-m2.7/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/benchmark_requests.jsonl> |
| 过滤后记录 | <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/minimax/minimax-m2.7/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/records.json> |
| 剔除记录审计 | <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/minimax/minimax-m2.7/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/records_excluded.json> |
| Benchmark 执行源码 | <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/minimax/minimax-m2.7/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/code/rerun_routing_sort_cache_cost_ab.py> |
| HTML 报告渲染源码 | <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/minimax/minimax-m2.7/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/code/render_report.py> |
| 测试源码 | <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/minimax/minimax-m2.7/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/code/test_rerun_routing_sort_cache_cost_ab.py> |
| 数据目录 | <https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/minimax/minimax-m2.7/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data> |
| 数据集引用 | 内置 `controlled_cache_probe` prompt-length tier 数据构造；请求级导出见 `benchmark_requests.jsonl` |
