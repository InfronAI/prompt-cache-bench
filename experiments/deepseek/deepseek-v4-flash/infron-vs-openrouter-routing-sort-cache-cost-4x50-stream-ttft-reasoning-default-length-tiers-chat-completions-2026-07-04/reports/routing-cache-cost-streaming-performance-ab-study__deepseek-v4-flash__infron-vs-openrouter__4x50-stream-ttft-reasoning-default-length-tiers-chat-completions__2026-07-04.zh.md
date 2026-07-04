# Infron 与 OpenRouter 路由、缓存、成本与流式性能 A/B 实验报告

## 摘要

本报告以 `deepseek/deepseek-v4-flash` 为对象，对比 Infron 与 OpenRouter 在 Prompt Caching 场景下的路由策略、缓存命中、实际成本、吞吐量、TTFT 首包响应时间和端到端时延。本轮 API 协议仅使用 `/v1/chat/completions`，reasoning/thinking 保持模型与平台默认行为，并保留 prompt 长度分层。

经过 A/B 过滤后，最终保留 **699 个配对样本**、**2796 次请求级观测**，剔除 **202 条记录**。

核心结论：Infron 在所有 routing sort 下 Token 级缓存命中率更高、端到端 E2E latency 更低；OpenRouter 在所有 routing sort 下吞吐量更高。本轮 TTFT 胜出方随 routing sort 变化，详见结果矩阵。

## 数据质量与实验口径

| 项目 | 值 |
| --- | --- |
| 模型 | `deepseek/deepseek-v4-flash` |
| API 协议 | 仅 `/v1/chat/completions` |
| 实验组 / 轮数 | 4 组 x 50 轮 |
| Prompt 长度分层 | `short`≈1500，`medium`≈8000，`long`≈32000 tokens |
| Reasoning / Thinking | 默认平台/模型行为，未显式禁用或强制 |
| 配对规则 | strict sort/group/round pair with first/second usage.prompt_tokens deltas <= 50 |
| 保留配对样本 | 699 |
| 请求级观测 | 2796 |
| 剔除记录 | 202 |

## 路由模式结果矩阵

| 路由模式 | 配对数 | Token 级缓存命中率 | 观测成本 | 吞吐量 | E2E 时延 | TTFT |
| --- | ---: | --- | --- | --- | --- | --- |
| Throughput First | 197 | **Infron 96.98%** / OpenRouter 94.98% | Infron $0.213942 / **OpenRouter $0.159170** | Infron 3.286 / **OpenRouter 5.487** tok/s | Infron 3722.44 ms / **OpenRouter 2915.93 ms** | Infron 3433.18 ms / **OpenRouter 2584.72 ms** |
| Price First | 120 | **Infron 99.14%** / OpenRouter 53.07% | **Infron $0.061492** / OpenRouter $0.259405 | Infron 2.839 / **OpenRouter 31.698** tok/s | **Infron 4102.95 ms** / OpenRouter 7446.27 ms | **Infron 3797.36 ms** / OpenRouter 4704.57 ms |
| Latency First | 183 | **Infron 99.45%** / OpenRouter 58.12% | **Infron $0.190216** / OpenRouter $0.346087 | Infron 5.407 / **OpenRouter 31.747** tok/s | **Infron 2291.26 ms** / OpenRouter 6849.25 ms | **Infron 2107.77 ms** / OpenRouter 4375.07 ms |
| TTFT First | 199 | **Infron 99.44%** / OpenRouter 56.25% | **Infron $0.188229** / OpenRouter $0.384197 | Infron 5.659 / **OpenRouter 27.038** tok/s | **Infron 2179.19 ms** / OpenRouter 5916.65 ms | **Infron 1994.39 ms** / OpenRouter 3804.41 ms |

## API 协议记录

| API 协议 | Endpoint | 平台 | 计划配对 | 请求数 | 成功率 | Usage 覆盖 | Token Usage 覆盖 | 成本覆盖 | 缓存 Telemetry 覆盖 | HTTP 状态 | 主要错误 |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `chat_completions` | `/v1/chat/completions` | infron | 800 | 1600 | **98.06%** | 100.00% | 100.00% | 100.00% | 100.00% | 0:31, 200:1569 | [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1000) (26); [Errno 54] Connection reset by peer (3) |
| `chat_completions` | `/v1/chat/completions` | openrouter | 800 | 1600 | 90.62% | 99.93% | 99.93% | 99.93% | 100.00% | 0:150, 200:1450 | [Errno 61] Connection refused (93); [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1000) (51) |

## Prompt 长度分层缓存表现

| 分层 | 配对数 | Token 级缓存命中率 | 调用级缓存命中率 | E2E 时延 | TTFT | Reasoning Tokens |
| --- | ---: | --- | --- | --- | --- | --- |
| short | 235 | **Infron 94.28%** / OpenRouter 27.56% | **Infron 99.57%** / OpenRouter 36.60% | **Infron 2009.88 ms** / OpenRouter 3997.19 ms | **Infron 1797.20 ms** / OpenRouter 2226.81 ms | **Infron 0** / OpenRouter 57031 |
| medium | 234 | **Infron 99.24%** / OpenRouter 66.88% | **Infron 100.00%** / OpenRouter 71.79% | **Infron 2821.46 ms** / OpenRouter 5504.25 ms | **Infron 2605.96 ms** / OpenRouter 3534.99 ms | **Infron 0** / OpenRouter 67622 |
| long | 230 | **Infron 98.80%** / OpenRouter 68.93% | **Infron 99.13%** / OpenRouter 75.22% | **Infron 4113.44 ms** / OpenRouter 7267.33 ms | **Infron 3836.90 ms** / OpenRouter 5569.41 ms | **Infron 0** / OpenRouter 71043 |

## Reasoning / Thinking 默认状态观测

本轮未显式禁用或强制 reasoning/thinking，reasoning tokens 作为响应 telemetry 观测变量保留。

| 路由模式 | Infron Reasoning Tokens | OpenRouter Reasoning Tokens | Infron 平均/请求 | OpenRouter 平均/请求 |
| --- | ---: | ---: | ---: | ---: |
| Throughput First | **0** | 6304 | **0.0000** | 16.0000 |
| Price First | **0** | 53713 | **0.0000** | 223.8042 |
| Latency First | **0** | 75379 | **0.0000** | 205.9536 |
| TTFT First | **0** | 60300 | **0.0000** | 151.5075 |

## 可复现性引用路径

| 产物 | 路径 | SHA256 / 说明 |
| --- | --- | --- |
| Summary | `experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/data/summary.json` | `8da7075fa6740d6e6e4b19a82518fcee2ece5084d37fad3b141926101c45d10b` |
| 配对级数据集 CSV | `experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/data/benchmark_pairs.csv` | `d7543a3e2b66f54010e09ae42469b9581413674cacf487ceb6161641f223a5cb` |
| 请求级数据集 JSONL | `experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/data/benchmark_requests.jsonl` | `a7b621d771279e9e1bc98c076ff572235e263c03d8479ebbf007cf919ddcc878` |
| 剔除记录审计 | `experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/data/records_excluded.json` | `ce364bae7fa1550beaade3a5a7a75dc1b689ae4fbe0f026c5d515ce19c62803e` |
| Benchmark runner 源码 | `experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/code/rerun_routing_sort_cache_cost_ab.py` | `a485c5116e99375e6b171d0328e5a423babd1ee6b206c72f54053a3a045b1075` |
| HTML report renderer 源码 | `experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/code/render_glm52_deepseek_style_report.py` | `8d6047a98107177daf86e9525a78df4735d72bfda7a55e2ba661620cc7cbee33` |
| 测试源码 | `experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/code/test_rerun_routing_sort_cache_cost_ab.py` | `c086ddc5d0a9a91eba82b7e8767d7bddf2f1ca4a28af0a87056b7028825adce4` |
| A/B 报告标准 | `experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/code/ab-report-standard.md` | `897151e98e2fc4cd9d7acf2642e54f800f1b22712a70275d35526348460d8372` |



公开 GitHub 路径：
- Summary: <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/data/summary.json>
- 配对级数据集 CSV: <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/data/benchmark_pairs.csv>
- 请求级数据集 JSONL: <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/data/benchmark_requests.jsonl>
- 剔除记录审计: <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/data/records_excluded.json>
- Benchmark runner 源码: <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/code/rerun_routing_sort_cache_cost_ab.py>
- HTML 报告渲染源码: <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/code/render_glm52_deepseek_style_report.py>
- 测试源码: <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/code/test_rerun_routing_sort_cache_cost_ab.py>
- A/B 报告标准: <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/code/ab-report-standard.md>
- 数据目录: <https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/data>
- 代码快照: <https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/code>

数据集引用：`business_representative` 内置代表性业务模板；请求级导出见本轮目录下的 `benchmark_requests.jsonl`。
