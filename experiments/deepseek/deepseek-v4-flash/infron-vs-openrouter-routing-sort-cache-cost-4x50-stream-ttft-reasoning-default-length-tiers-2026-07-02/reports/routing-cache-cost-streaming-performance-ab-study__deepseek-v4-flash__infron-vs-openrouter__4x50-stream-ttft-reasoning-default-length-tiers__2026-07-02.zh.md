# DeepSeek V4 Flash：路由、缓存、成本与流式 TTFT A/B 基准

> 完整交互式报告：[GitHub Pages 中文 HTML](https://infronai.github.io/prompt-cache-bench/experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-02/reports/routing-cache-cost-streaming-performance-ab-study__deepseek-v4-flash__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers__2026-07-02.zh.html)。本 Markdown 文件作为轻量索引使用，便于 GitHub 预览、diff 审阅和可复现性入口。

## 1. 实验摘要

| 字段 | 值 |
| --- | --- |
| 模型 | `deepseek/deepseek-v4-flash` |
| 对比对象 | Infron vs OpenRouter |
| 路由模式 | `throughput`, `price`, `latency`, `ttft` |
| 实验设计 | 4 组 x 50 轮，streaming |
| Prompt 长度分层 | short, medium, long |
| Reasoning 控制 | 平台默认；请求 payload 未显式包含 `reasoning.effort` |
| 保留请求行 | 3156 |
| 严格 A/B 配对 | 789 |
| 数据集 | `business_representative` |

## 2. 路由层结果矩阵

### Throughput First

| 指标 | Infron | OpenRouter | Winner |
| --- | ---: | ---: | --- |
| Token cache hit rate | 75.64% | **90.94%** | **OpenRouter** |
| Actual cost | **$0.24870300** | $0.28981075 | **Infron** |
| Throughput | 2.30 tok/s | **19.09 tok/s** | **OpenRouter** |
| Latency | 5308.59 ms | **4581.42 ms** | **OpenRouter** |
| TTFT | 4994.47 ms | **3515.80 ms** | **OpenRouter** |

### Price First

| 指标 | Infron | OpenRouter | Winner |
| --- | ---: | ---: | --- |
| Token cache hit rate | **88.29%** | 75.66% | **Infron** |
| Actual cost | **$0.18655200** | $0.27711419 | **Infron** |
| Throughput | 2.38 tok/s | **22.17 tok/s** | **OpenRouter** |
| Latency | **5212.66 ms** | 6875.58 ms | **Infron** |
| TTFT | **4950.45 ms** | 4953.93 ms | **Infron** |

### Latency First

| 指标 | Infron | OpenRouter | Winner |
| --- | ---: | ---: | --- |
| Token cache hit rate | **86.89%** | 43.70% | **Infron** |
| Actual cost | **$0.17911600** | $0.52384433 | **Infron** |
| Throughput | 3.60 tok/s | **5.17 tok/s** | **OpenRouter** |
| Latency | **3450.91 ms** | 4727.19 ms | **Infron** |
| TTFT | **3177.64 ms** | 3877.73 ms | **Infron** |

### TTFT First

| 指标 | Infron | OpenRouter | Winner |
| --- | ---: | ---: | --- |
| Token cache hit rate | **86.33%** | 36.46% | **Infron** |
| Actual cost | **$0.18308300** | $0.65891935 | **Infron** |
| Throughput | 3.66 tok/s | **4.39 tok/s** | **OpenRouter** |
| Latency | **3365.26 ms** | 3843.74 ms | **Infron** |
| TTFT | 3100.55 ms | **2956.95 ms** | **OpenRouter** |

## 3. Prompt 长度分层缓存结果

| Tier | Target prompt tokens | Pairs | Infron cache | OpenRouter cache | Cache winner | Infron cost | OpenRouter cost | Cost winner |
| --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | --- |
| short | 1500 | 267 | **78.29%** | 64.32% | **Infron** | **$0.03816800** | $0.07663082 | **Infron** |
| medium | 8000 | 264 | **81.23%** | 63.76% | **Infron** | **$0.16902100** | $0.34062648 | **Infron** |
| long | 32000 | 258 | **85.39%** | 61.13% | **Infron** | **$0.59026500** | $1.33243133 | **Infron** |

分层结果显示，Infron 在 short、medium、long 三档 prompt 中都保持更高的 token cache hit rate 和更低的实际成本。随着可复用前缀变长，缓存亲和与 provider stickiness 的收益更加明显。

## 4. Reasoning / Thinking 观测

本次请求没有显式关闭或配置 reasoning/thinking，而是保留模型与平台默认行为。响应中的 reasoning tokens 只作为观测变量记录，不作为受控变量。

| 字段 | 值 |
| --- | --- |
| Mode | `platform_default` |
| Payload includes reasoning field | `False` |
| Requested effort | `None` |
| Description | 请求未显式设置 `reasoning.effort`，保留模型与平台默认推理行为。 |

## 可复现性附录

| 工件 | 链接 |
| --- | --- |
| 中文 HTML 报告 | [GitHub Pages](https://infronai.github.io/prompt-cache-bench/experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-02/reports/routing-cache-cost-streaming-performance-ab-study__deepseek-v4-flash__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers__2026-07-02.zh.html) |
| English HTML report | [GitHub Pages](https://infronai.github.io/prompt-cache-bench/experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-02/reports/routing-cache-cost-streaming-performance-ab-study__deepseek-v4-flash__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers__2026-07-02.en.html) |
| 中文 Markdown | [GitHub](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-02/reports/routing-cache-cost-streaming-performance-ab-study__deepseek-v4-flash__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers__2026-07-02.zh.md) |
| English Markdown | [GitHub](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-02/reports/routing-cache-cost-streaming-performance-ab-study__deepseek-v4-flash__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers__2026-07-02.en.md) |
| 数据目录 | [GitHub](https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-02/data) |
| 代码快照 | [GitHub](https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-02/code) |
| Manifest | [GitHub](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-02/metadata/manifest.json) |
