# moonshotai/kimi-k2.7-code 路由、缓存、成本与流式性能 A/B 实验

模型：`moonshotai/kimi-k2.7-code`

本报告使用标准 prompt-cache-bench A/B 方法，对比 Infron 与 OpenRouter 在 4 组、每组 50 轮、流式 Chat Completions、短/中/长 prompt 分层下的缓存、成本、吞吐、端到端时延和 TTFT 表现。

## 数据质量

- 完成请求槽位：1600
- 请求级观测：3200
- 配对样本：800
- 剔除记录：共 0 条；不完整 0 条，异常 usage 0 条，input tokens 不等 0 条。
- 下表基于 `summary.json` 中清洗后的可比样本聚合得到。

## 聚合结果

| 路由目标 | 平台 | 有效轮次 | 缓存命中率 | 总成本 USD | 平均 latency ms | P95 latency ms | 平均 TTFT ms | P95 TTFT ms | 输出 TPS |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| throughput | infron | 200 | 0.916270 | 1.190816 | 4,905.388 | 9,776.655 | 3,967.997 | 8,616.902 | 6.401 |
| throughput | openrouter | 200 | 0.978077 | 1.215148 | 3,002.508 | 5,158.986 | 2,623.435 | 4,460.518 | 4.714 |
| price | infron | 200 | 0.998282 | 1.018341 | 9,519.195 | 45,655.315 | 7,739.131 | 43,087.143 | 1.981 |
| price | openrouter | 200 | 0.982897 | 1.190685 | 3,388.530 | 6,482.456 | 2,931.515 | 5,565.656 | 4.398 |
| latency | infron | 200 | 0.999340 | 0.997955 | 5,646.342 | 8,440.445 | 3,509.058 | 6,159.659 | 2.834 |
| latency | openrouter | 200 | 0.985120 | 1.126289 | 3,221.597 | 5,259.715 | 2,742.343 | 4,679.844 | 4.677 |
| ttft | infron | 200 | 0.998747 | 1.078529 | 6,499.951 | 23,478.278 | 3,668.659 | 7,981.205 | 2.462 |
| ttft | openrouter | 200 | 0.995159 | 1.114939 | 3,212.642 | 5,520.038 | 2,676.150 | 4,557.333 | 4.746 |

## 结论摘要

- Infron 在本轮所有路由目标下实际观测成本更低。
- Infron 在 price、latency、TTFT 模式下 token 级缓存命中率更高；OpenRouter 在 throughput 模式下 token 级缓存命中率更高。
- OpenRouter 在本轮所有路由目标下平均端到端时延和流式 TTFT 更低。
- 本轮标准 A/B input-token 容差过滤后剔除 0 条记录，适合做直接配对比较。

## 可复现性链接

- Summary：<https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/moonshotai/kimi-k2.7-code/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-09/data/summary.json>
- 配对数据集 CSV：<https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/moonshotai/kimi-k2.7-code/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-09/data/benchmark_pairs.csv>
- 请求级数据集 JSONL：<https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/moonshotai/kimi-k2.7-code/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-09/data/benchmark_requests.jsonl>
- 过滤后结构化记录：<https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/moonshotai/kimi-k2.7-code/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-09/data/records.json>
- 剔除记录审计：<https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/moonshotai/kimi-k2.7-code/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-09/data/records_excluded.json>
- Benchmark 执行源码：<https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/moonshotai/kimi-k2.7-code/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-09/code/rerun_routing_sort_cache_cost_ab.py>
- HTML 报告渲染源码：<https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/moonshotai/kimi-k2.7-code/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-09/code/render_glm52_deepseek_style_report.py>
- 测试源码：<https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/moonshotai/kimi-k2.7-code/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-09/code/test_rerun_routing_sort_cache_cost_ab.py>
- A/B 报告标准：<https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/moonshotai/kimi-k2.7-code/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-09/code/ab-report-standard.md>
- 数据目录：<https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/moonshotai/kimi-k2.7-code/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-09/data>
- 代码快照：<https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/moonshotai/kimi-k2.7-code/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-09/code>
- English HTML 报告：<https://infronai.github.io/prompt-cache-bench/experiments/moonshotai/kimi-k2.7-code/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-09/reports/routing-cache-cost-streaming-performance-ab-study__kimi-k2-7-code__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-09.en.html>
- 中文 HTML 报告：<https://infronai.github.io/prompt-cache-bench/experiments/moonshotai/kimi-k2.7-code/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-09/reports/routing-cache-cost-streaming-performance-ab-study__kimi-k2-7-code__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-09.zh.html>
