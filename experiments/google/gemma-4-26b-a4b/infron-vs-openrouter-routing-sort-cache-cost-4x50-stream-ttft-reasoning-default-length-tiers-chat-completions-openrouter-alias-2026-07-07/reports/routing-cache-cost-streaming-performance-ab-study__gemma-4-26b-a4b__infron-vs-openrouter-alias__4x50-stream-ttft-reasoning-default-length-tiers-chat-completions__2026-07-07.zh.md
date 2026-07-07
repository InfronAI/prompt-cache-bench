# Infron vs OpenRouter 路由、缓存、成本与流式性能 A/B 报告

## 摘要

本报告评估 `google/gemma-4-26b-a4b` 在 Infron 与 OpenRouter 上的缓存复用、实际成本、throughput、端到端 latency 与 streaming TTFT。本次 OpenRouter 侧使用 provider-specific model alias `google/gemma-4-26b-a4b-it`，修复了上一轮无效实验中的 HTTP 400 model id 兼容性问题。

经过严格 A/B 清洗后，本次公开数据集保留 746 个配对样本和 2984 条请求级观测，剔除 108 条记录。

## 实验设置

| 项目 | 配置 |
| --- | --- |
| Model | `google/gemma-4-26b-a4b` |
| Provider model IDs | Infron: `google/gemma-4-26b-a4b`; OpenRouter: `google/gemma-4-26b-a4b-it` |
| API protocol | `/v1/chat/completions` |
| Routing modes | Throughput First, Price First, Latency First, TTFT First |
| Groups / rounds per group | 4 / 50 |
| Request mode | Streaming Chat Completions with TTFT collection |
| Reasoning / Thinking control | 未显式设置 reasoning/thinking 参数，保留模型与平台默认行为 |
| Prompt length tiers | `short`≈1500, `medium`≈8000, `long`≈32000 |
| Input-token pair tolerance | 50 tokens |

## 总体指标

| 路由模式 | 平台 | 有效配对 | Token 缓存命中率 | 总成本 | 平均 latency | P95 latency | 平均 TTFT | P95 TTFT | Throughput |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Throughput First | Infron | 186 | 0.00% | $0.491438 | 3518.508 ms | 10988.806 ms | 3198.139 ms | 10797.790 ms | 1.137 tok/s |
| Throughput First | OpenRouter | 186 | 99.36% | $0.374302 | 3044.116 ms | 5819.176 ms | 2865.777 ms | 5716.568 ms | 1.314 tok/s |
| Price First | Infron | 165 | 1.81% | $0.421555 | 4283.032 ms | 9601.639 ms | 3875.656 ms | 9373.297 ms | 0.934 tok/s |
| Price First | OpenRouter | 165 | 93.45% | $0.308309 | 3342.003 ms | 8403.986 ms | 3147.680 ms | 8337.773 ms | 1.197 tok/s |
| Latency First | Infron | 195 | 51.00% | $0.915592 | 5452.119 ms | 10126.982 ms | 5187.900 ms | 9630.822 ms | 0.734 tok/s |
| Latency First | OpenRouter | 195 | 85.75% | $0.460012 | 3086.540 ms | 5164.898 ms | 2908.678 ms | 4925.935 ms | 1.296 tok/s |
| TTFT First | Infron | 200 | 81.56% | $0.620973 | 5707.612 ms | 11790.298 ms | 5390.366 ms | 11326.142 ms | 0.701 tok/s |
| TTFT First | OpenRouter | 200 | 84.91% | $0.498402 | 2827.304 ms | 5387.838 ms | 2647.020 ms | 5242.321 ms | 1.415 tok/s |

## 可复现性附录

| Artifact | Path |
| --- | --- |
| Summary | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/google/gemma-4-26b-a4b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-openrouter-alias-2026-07-07/data/summary.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/google/gemma-4-26b-a4b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-openrouter-alias-2026-07-07/data/summary.json) |
| Paired dataset | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/google/gemma-4-26b-a4b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-openrouter-alias-2026-07-07/data/benchmark_pairs.csv](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/google/gemma-4-26b-a4b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-openrouter-alias-2026-07-07/data/benchmark_pairs.csv) |
| Request-level dataset | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/google/gemma-4-26b-a4b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-openrouter-alias-2026-07-07/data/benchmark_requests.jsonl](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/google/gemma-4-26b-a4b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-openrouter-alias-2026-07-07/data/benchmark_requests.jsonl) |
| Filtered structured records | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/google/gemma-4-26b-a4b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-openrouter-alias-2026-07-07/data/records.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/google/gemma-4-26b-a4b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-openrouter-alias-2026-07-07/data/records.json) |
| Excluded-record audit | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/google/gemma-4-26b-a4b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-openrouter-alias-2026-07-07/data/records_excluded.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/google/gemma-4-26b-a4b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-openrouter-alias-2026-07-07/data/records_excluded.json) |
| Test source | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/google/gemma-4-26b-a4b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-openrouter-alias-2026-07-07/code/test_rerun_routing_sort_cache_cost_ab.py](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/google/gemma-4-26b-a4b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-openrouter-alias-2026-07-07/code/test_rerun_routing_sort_cache_cost_ab.py) |
| Benchmark runner source | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/google/gemma-4-26b-a4b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-openrouter-alias-2026-07-07/code/rerun_routing_sort_cache_cost_ab.py](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/google/gemma-4-26b-a4b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-openrouter-alias-2026-07-07/code/rerun_routing_sort_cache_cost_ab.py) |
| HTML report renderer source | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/google/gemma-4-26b-a4b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-openrouter-alias-2026-07-07/code/render_glm52_deepseek_style_report.py](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/google/gemma-4-26b-a4b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-openrouter-alias-2026-07-07/code/render_glm52_deepseek_style_report.py) |

