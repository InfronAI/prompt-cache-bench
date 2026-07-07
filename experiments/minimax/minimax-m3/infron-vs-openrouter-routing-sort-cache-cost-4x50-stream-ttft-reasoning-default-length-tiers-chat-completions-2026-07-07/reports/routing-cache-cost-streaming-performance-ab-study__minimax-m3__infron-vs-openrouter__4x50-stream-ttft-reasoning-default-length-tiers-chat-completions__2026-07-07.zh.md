# Infron 与 OpenRouter 路由、缓存、成本与流式性能 A/B 实验报告

模型：`minimax/minimax-m3`

本报告沿用标准 A/B benchmark 矩阵：4 个实验组、每组 50 轮、开启 streaming、使用 Chat Completions 协议、reasoning 保持默认行为，并覆盖 short / medium / long 三档 prompt 长度。

## 数据质量

- 请求级记录数：3196
- 可比较 A/B 配对样本：799
- 剔除记录：共 2 条；其中 incomplete 1 条，anomalous usage 0 条，input tokens 不一致 1 条。
- Request JSONL SHA256：`333491a80a3af487f260ea9b9f6b7cd3f863e3b150f025ea62796a345bf8caa0`
- Pair CSV SHA256：`04e9799be91b7b05670e88c20259466bba36f0132affa8f618fe73864239406d`

## 聚合结果

| 路由目标 | 平台 | 有效轮次 | Token 缓存命中率 | 实际成本 | 平均 Latency (ms) | 平均 TTFT (ms) | 输出 TPS |
|---|---:|---:|---:|---:|---:|---:|---:|
| throughput | infron | 199 | 99.75% | $0.44453200 | 4,187.992 | 3,906.654 | 3.820 |
| throughput | openrouter | 199 | 97.78% | $0.42616452 | 3,520.482 | 3,320.929 | 4.480 |
| price | infron | 200 | 87.07% | $0.86923800 | 4,215.047 | 3,970.207 | 5.706 |
| price | openrouter | 200 | 99.71% | $0.38910666 | 3,183.654 | 2,988.125 | 5.026 |
| latency | infron | 200 | 99.56% | $0.38928600 | 3,610.426 | 3,345.935 | 4.432 |
| latency | openrouter | 200 | 97.80% | $0.50588802 | 3,322.030 | 3,069.540 | 4.816 |
| ttft | infron | 200 | 99.56% | $0.38928600 | 3,405.387 | 3,123.363 | 4.698 |
| ttft | openrouter | 200 | 99.71% | $0.49761108 | 3,616.816 | 3,377.282 | 4.424 |

## 结论解读

整体看，本轮实验没有出现单一平台在所有指标上绝对领先。Infron 在 4 个路由目标中的 3 个目标上缓存复用更强，并且在 latency / TTFT 模式下实际成本更低；OpenRouter 在 throughput、price、latency 三个模式下平均时延更低；在显式 TTFT 目标下，Infron 的平均 TTFT 更低。`price` 模式是 Infron 成本侧的主要异常点，原因是该组缓存复用明显低于 OpenRouter。

## 可复现性附录

- 在线英文 HTML：[https://infronai.github.io/prompt-cache-bench/experiments/minimax/minimax-m3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/reports/routing-cache-cost-streaming-performance-ab-study__minimax-m3__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-07.en.html](https://infronai.github.io/prompt-cache-bench/experiments/minimax/minimax-m3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/reports/routing-cache-cost-streaming-performance-ab-study__minimax-m3__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-07.en.html)
- 在线中文 HTML：[https://infronai.github.io/prompt-cache-bench/experiments/minimax/minimax-m3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/reports/routing-cache-cost-streaming-performance-ab-study__minimax-m3__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-07.zh.html](https://infronai.github.io/prompt-cache-bench/experiments/minimax/minimax-m3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/reports/routing-cache-cost-streaming-performance-ab-study__minimax-m3__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-07.zh.html)
- 实验目录：[https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/minimax/minimax-m3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07](https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/minimax/minimax-m3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07)
- 报告目录：[https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/minimax/minimax-m3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/reports](https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/minimax/minimax-m3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/reports)
- 数据集目录：[https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/minimax/minimax-m3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data](https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/minimax/minimax-m3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data)
- Summary：[https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/minimax/minimax-m3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/summary.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/minimax/minimax-m3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/summary.json)
- Pair CSV：[https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/minimax/minimax-m3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/benchmark_pairs.csv](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/minimax/minimax-m3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/benchmark_pairs.csv)
- Request JSONL：[https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/minimax/minimax-m3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/benchmark_requests.jsonl](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/minimax/minimax-m3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/benchmark_requests.jsonl)
- Records JSON：[https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/minimax/minimax-m3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/records.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/minimax/minimax-m3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/records.json)
- 剔除记录：[https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/minimax/minimax-m3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/records_excluded.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/minimax/minimax-m3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/records_excluded.json)
- 执行脚本：[https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/minimax/minimax-m3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/code/rerun_routing_sort_cache_cost_ab.py](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/minimax/minimax-m3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/code/rerun_routing_sort_cache_cost_ab.py)
- 渲染脚本：[https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/minimax/minimax-m3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/code/render_report.py](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/minimax/minimax-m3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/code/render_report.py)
- 测试源码：[https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/minimax/minimax-m3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/code/test_rerun_routing_sort_cache_cost_ab.py](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/minimax/minimax-m3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/code/test_rerun_routing_sort_cache_cost_ab.py)
- Manifest：[https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/minimax/minimax-m3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/metadata/manifest.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/minimax/minimax-m3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/metadata/manifest.json)
