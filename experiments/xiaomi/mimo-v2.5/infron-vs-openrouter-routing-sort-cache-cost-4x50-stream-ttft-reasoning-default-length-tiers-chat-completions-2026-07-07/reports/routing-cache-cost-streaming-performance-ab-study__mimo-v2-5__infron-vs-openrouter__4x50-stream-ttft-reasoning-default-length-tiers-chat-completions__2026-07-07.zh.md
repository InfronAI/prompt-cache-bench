# Infron 与 OpenRouter 路由、缓存、成本与流式性能 A/B 实验报告



## 摘要

本报告以 `xiaomi/mimo-v2.5` 为对象，评估 Infron 与 OpenRouter 在 Prompt Caching 场景下的缓存复用、实际成本、吞吐、端到端时延和流式 TTFT 表现。

核心结论：缓存命中率 Infron 1/4 胜、OpenRouter 3/4 胜；实际成本 Infron 1/4 胜、OpenRouter 3/4 胜；吞吐 Infron 3/4 胜、OpenRouter 1/4 胜；端到端时延 Infron 3/4 胜、OpenRouter 1/4 胜；流式 TTFT Infron 3/4 胜、OpenRouter 1/4 胜。

严格 A/B 过滤后保留 800 个配对样本、3200 次请求级观测，剔除 0 条记录。



## 实验设置

| 项目 | 配置 |
| --- | --- |
| 模型 | `xiaomi/mimo-v2.5` |
| 平台实际模型 ID | infron: `xiaomi/mimo-v2.5`; openrouter: `xiaomi/mimo-v2.5` |
| API 协议 | `/v1/chat/completions` |
| 路由模式 | 吞吐优先、价格优先、端到端时延优先、流式 TTFT 优先 |
| 实验组 / 每组轮数 | 4 / 50 |
| Workers | 24 |
| 请求方式 | 流式 Chat Completions，采集 TTFT |
| Reasoning / Thinking 控制 | 未显式指定 reasoning/thinking 参数；保留模型与平台默认行为 |
| Prompt 长度分层 | `short`≈1500、`medium`≈8000、`long`≈32000 |
| Input token 配对容忍度 | 50 tokens |
| 剔除记录 | 0 |



## 总体指标

| 路由模式 | 平台 | 严格配对轮数 | 总 Input Tokens | Token 级缓存命中率 | 实际成本 | 吞吐量 | 端到端 E2E 时延 | 流式 TTFT |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 吞吐优先 | Infron | 200 | 7075538 | 90.89% | $0.53792900 | **3.90 tok/s** | **6103.12 ms** | **5073.92 ms** |
| 吞吐优先 | OpenRouter | 200 | 7075538 | **98.61%** | **$0.40888852** | 2.26 tok/s | 7073.03 ms | 6629.10 ms |
| 价格优先 | Infron | 200 | 7076338 | **99.88%** | **$0.03393900** | 1.53 tok/s | 8371.81 ms | 7772.99 ms |
| 价格优先 | OpenRouter | 200 | 7075538 | 99.14% | $0.40176022 | **2.57 tok/s** | **6221.51 ms** | **5804.38 ms** |
| 端到端时延优先 | Infron | 200 | 7075538 | 99.73% | $0.61243900 | **4.74 tok/s** | **3373.85 ms** | **2904.79 ms** |
| 端到端时延优先 | OpenRouter | 200 | 7075538 | **99.77%** | **$0.37016124** | 4.47 tok/s | 3577.79 ms | 3218.88 ms |
| 流式 TTFT 优先 | Infron | 200 | 7075538 | 99.73% | $0.58492400 | **4.82 tok/s** | **3322.36 ms** | **2814.00 ms** |
| 流式 TTFT 优先 | OpenRouter | 200 | 7075538 | **99.76%** | **$0.45699362** | 4.55 tok/s | 3515.33 ms | 3115.36 ms |



## Prompt 长度分层

| Prompt 长度 tier | 目标 tokens | 平台 | 轮数 | Token 级命中率 | 实际成本 | 平均 E2E 时延 | 平均 TTFT |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `short` | 1500 | Infron | 268 | 94.92% | $0.08121300 | 4095.19 ms | 3458.13 ms |
| `short` | 1500 | OpenRouter | 268 | **97.77%** | **$0.06277326** | **3846.68 ms** | **3412.17 ms** |
| `medium` | 8000 | Infron | 268 | 96.26% | **$0.34829300** | 5183.66 ms | 4536.25 ms |
| `medium` | 8000 | OpenRouter | 268 | **98.76%** | $0.47585390 | **4706.89 ms** | **4295.43 ms** |
| `long` | 32000 | Infron | 264 | 98.02% | $1.33972500 | **6619.30 ms** | **5949.43 ms** |
| `long` | 32000 | OpenRouter | 264 | **99.54%** | **$1.09917644** | 6762.02 ms | 6393.59 ms |



## 可复现性附录

| 工件 | 路径 |
| --- | --- |
| Summary | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/xiaomi/mimo-v2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/summary.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/xiaomi/mimo-v2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/summary.json) |
| 配对数据集 | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/xiaomi/mimo-v2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/benchmark_pairs.csv](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/xiaomi/mimo-v2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/benchmark_pairs.csv) |
| 请求级数据集 | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/xiaomi/mimo-v2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/benchmark_requests.jsonl](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/xiaomi/mimo-v2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/benchmark_requests.jsonl) |
| 过滤后结构化记录 | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/xiaomi/mimo-v2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/records.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/xiaomi/mimo-v2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/records.json) |
| 剔除记录审计 | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/xiaomi/mimo-v2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/records_excluded.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/xiaomi/mimo-v2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/records_excluded.json) |
| 测试源码 | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/xiaomi/mimo-v2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/code/test_rerun_routing_sort_cache_cost_ab.py](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/xiaomi/mimo-v2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/code/test_rerun_routing_sort_cache_cost_ab.py) |
| Benchmark 执行源码 | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/xiaomi/mimo-v2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/code/rerun_routing_sort_cache_cost_ab.py](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/xiaomi/mimo-v2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/code/rerun_routing_sort_cache_cost_ab.py) |
| HTML 报告渲染源码 | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/xiaomi/mimo-v2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/code/render_glm52_deepseek_style_report.py](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/xiaomi/mimo-v2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/code/render_glm52_deepseek_style_report.py) |
| 数据集引用 | `business_representative` 内置代表性业务模板；请求级导出见 [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/xiaomi/mimo-v2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/benchmark_requests.jsonl](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/xiaomi/mimo-v2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/benchmark_requests.jsonl) |
