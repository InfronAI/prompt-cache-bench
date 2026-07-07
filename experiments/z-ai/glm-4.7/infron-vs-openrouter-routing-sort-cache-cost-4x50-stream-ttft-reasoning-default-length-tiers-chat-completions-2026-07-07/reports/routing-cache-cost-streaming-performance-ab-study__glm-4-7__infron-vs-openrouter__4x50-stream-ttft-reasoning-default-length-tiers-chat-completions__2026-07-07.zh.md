# Infron 与 OpenRouter 路由、缓存、成本与流式性能 A/B 实验报告

## 摘要与结论大纲

**关键词**：Prompt Caching；A/B Testing；Provider Routing；Cache Affinity；Latency；Throughput；Cost Attribution；glm-4.7

### 摘要

本报告以 `z-ai/glm-4.7` 为对象，评估 Infron 与 OpenRouter 在 Prompt Caching 场景下的缓存复用、实际成本、吞吐、端到端时延和流式 TTFT 表现。

核心结论是：Infron 在 1/4 个路由模式下缓存命中率占优，OpenRouter 在 3/4 个路由模式下占优，0/4 个路由模式持平；Infron 在 3/4 个路由模式下实际成本占优，OpenRouter 在 1/4 个路由模式下占优，0/4 个路由模式持平；OpenRouter 在所有路由模式下吞吐量占优；Infron 在所有路由模式下端到端 E2E 时延占优；OpenRouter 在所有路由模式下流式 TTFT占优。

整体看，Infron 的跨模式优势主要体现在端到端 E2E 时延、实际成本，OpenRouter 的跨模式优势主要体现在吞吐、流式 TTFT、缓存复用。平台选择不应只看单一指标，而应按业务目标在成本、缓存稳定性、吞吐和交互时延之间取舍。

### 图 0：核心能力归一化雷达图

五个雷达轴分别代表吞吐量、价格、端到端 E2E 时延、流式 TTFT 和缓存命中率。所有指标统一转为 0-100 分，且越外侧越好。

粗实线表示平台综合轮廓，半透明细线和点表示各路由模式下的表现。

结论总览：核心指标与路由模式胜出方

基于严格 A/B 配对样本。蓝色代表 Infron，橙色代表 OpenRouter；金色单元格表示该路由模式的目标指标胜出方。

**吞吐量**OpenRouter 4/4 胜出最大优势 17.41%, 越高越好**实际成本**Infron 3/4 胜出最大优势 3.97%, 越低越好**端到端 E2E 时延**Infron 4/4 胜出最大优势 8.39%, 越低越好**流式 TTFT**OpenRouter 4/4 胜出最大优势 89.31%, 越低越好**缓存命中率**OpenRouter 3/4 胜出最大优势 2.79%, 越高越好

| 路由模式 | 吞吐目标 | 成本目标 | 时延目标 | TTFT 目标 | 缓存结果 |
| --- | --- | --- | --- | --- | --- |
| **吞吐优先** throughput | OpenRouter优势 17.41% | Infron优势 3.97% | Infron优势 8.39% | OpenRouter优势 89.31% | OpenRouter优势 2.79% |
| **价格优先** price | OpenRouter优势 12.90% | Infron优势 0.79% | Infron优势 3.35% | OpenRouter优势 14.37% | OpenRouter优势 0.16% |
| **端到端时延优先** latency | OpenRouter优势 27.40% | OpenRouter优势 105.88% | Infron优势 0.03% | OpenRouter优势 18.74% | OpenRouter优势 2.66% |
| **流式 TTFT 优先** ttft | OpenRouter优势 12.11% | Infron优势 3.22% | Infron优势 1.51% | OpenRouter优势 40.25% | Infron优势 0.17% |

### 结论大纲

| 研究维度 | 结论 | 证据位置 |
| --- | --- | --- |
| 控制变量 | 同一 `sort/group/round` 下 first/second `usage.prompt_tokens` 偏差不超过 50 tokens；总 Input Tokens 使用响应 telemetry。 | 方法与数据质量章节 |
| 缓存复用 | Infron 在 1/4 个路由模式下缓存命中率占优，OpenRouter 在 3/4 个路由模式下占优，0/4 个路由模式持平 | 总体指标与机制解释章节 |
| 实际成本 | Infron 在 3/4 个路由模式下实际成本占优，OpenRouter 在 1/4 个路由模式下占优，0/4 个路由模式持平 | 总体指标与 Provider 下钻章节 |
| 性能表现 | OpenRouter 在所有路由模式下吞吐量占优；Infron 在所有路由模式下端到端 E2E 时延占优；OpenRouter 在所有路由模式下流式 TTFT占优 | 结果可视化与统计检验章节 |
| 归因边界 | 报告只使用响应中可观测的 usage、cost、TTFT、latency、provider 字段和 cache tokens。 | Provider/Route 下钻分析章节 |
| 业务含义 | 长上下文、RAG 前缀、Agent 工具说明和高频模板请求应同时关注缓存命中率、成本、首包和端到端时延。 | 讨论与结论章节 |

### 路由模式级结论

| 路由模式 | 目标 | 缓存胜出 | 成本胜出 | 吞吐胜出 | E2E 时延胜出 | TTFT 胜出 | 解读 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 吞吐优先 | 最大化单位时间输出能力 | **OpenRouter** | **Infron** | **OpenRouter** | **Infron** | **OpenRouter** | OpenRouter 综合占优（3/5 指标） |
| 价格优先 | 最小化单位请求和单位 token 成本 | **OpenRouter** | **Infron** | **OpenRouter** | **Infron** | **OpenRouter** | OpenRouter 综合占优（3/5 指标） |
| 端到端时延优先 | 最小化完整响应等待时间 | **OpenRouter** | **OpenRouter** | **OpenRouter** | **Infron** | **OpenRouter** | OpenRouter 综合占优（4/5 指标） |
| 流式 TTFT 优先 | 最小化流式首包响应时间 | **Infron** | **Infron** | **OpenRouter** | **Infron** | **OpenRouter** | Infron 综合占优（3/5 指标） |

## 1. 引言：背景、研究问题与贡献

LLM 推理平台的真实性能不仅由模型决定，也由 provider 路由、提示词缓存、流式响应、成本归因和 fallback 策略共同决定。本报告把平台视为可观测系统，以 A/B 配对方式评估速度、成本、缓存和首包体验的多目标权衡。

### 1.1 研究假设

| 假设 | 内容 | 验证指标 |
| --- | --- | --- |
| H1 | 重复稳定长前缀请求中，更强的 provider/cache affinity 会提升 Token 级缓存命中率。 | 第二次请求 cache read tokens、Token 级命中率 |
| H2 | 更高缓存命中率会降低真实响应成本，但不必然降低 TTFT 或端到端 latency。 | 实际成本、平均 TTFT、平均 latency/请求 |
| H3 | 不同 routing sort 会改变 provider 选择，从而形成不同的成本、吞吐和时延 Pareto 前沿。 | provider 分布、throughput、latency、cost |

### 1.2 本文贡献

- 使用响应返回的 `usage.prompt_tokens` 作为真实 input token 控制变量，并允许 50 tokens 内的小幅跨平台计数波动。

- 将 prompt caching 评估扩展到成本、吞吐、E2E latency、TTFT、provider 分布、reasoning telemetry 和配对统计检验。

- 所有结论只基于响应可观测 telemetry，不把平台内部私有 routing trace 当作已观测事实。

## 2. 方法：实验设计、数据集构造与控制变量

### 2.1 数据集生成方法

数据集名称为 `business_representative`，覆盖 4 种 routing sort、2 个平台、4 个实验组、每组 50 轮。每轮包含 first/second 两次相同 Chat Completions 请求：第一次建立或刷新缓存状态，第二次观测 cache read tokens、TTFT 和端到端响应。

业务模板覆盖稳定长上下文场景，包括 RAG 客服、Agent 工具说明、营销自动化和代码审查等高复用 prompt 结构。

### 2.2 控制变量方法

图 1：实验设计与严格 A/B 配对过滤

**固定 Payload**模型 z-ai/glm-4.7，同一路由模式下 payload SHA256 固定 → **请求 A1/B1**第一次请求建立或刷新缓存状态 → **请求 A2/B2**第二次请求观测 cache read tokens 与 TTFT → **严格过滤**只聚合 input-token 偏差不超过 50 的 A/B pairs

控制变量方法：同一 `sort/group/round` 下，两个平台 first/second 两次请求的 `usage.prompt_tokens` 各自偏差必须不超过 50 tokens。总 Input Tokens 使用响应返回的 `usage.prompt_tokens`，不使用本地 tokenizer 估算。

### 2.3 指标定义

| 指标 | 定义 | 解释方向 |
| --- | --- | --- |
| 调用级命中率 | 第二次请求 `cache_read_tokens > 0` 的轮次占比 | 越高表示越稳定触发缓存读取 |
| Token 级命中率 | 第二次请求 cache read tokens / 第二次请求 prompt tokens | 越高表示输入 token 复用比例越高 |
| 实际成本 | first + second 两次请求返回 usage/cost 的合计 | 越低越好 |
| Throughput | 响应 completion tokens / 请求 latency seconds | 越高越好 |
| E2E latency | 每次请求完整响应耗时均值 | 越低越好 |
| TTFT | streaming 下首包/首 token 到达时间均值 | 越低越好 |
| Reasoning 口径 | 响应 usage 中的 reasoning token 字段保留为观测变量 | 用于解释时延、吞吐和成本，不单独作为业务产出 |

## 3. 实验环境与数据质量控制

| 项目 | 配置 |
| --- | --- |
| 模型 | `z-ai/glm-4.7` |
| 平台实际模型 ID | infron: `z-ai/glm-4.7`; openrouter: `z-ai/glm-4.7` |
| 平台 | Infron、OpenRouter |
| API 协议 | `/v1/chat/completions` |
| 路由模式 | 吞吐优先、价格优先、端到端时延优先、流式 TTFT 优先 |
| 实验组 | 4 |
| 每组轮数 | 50 |
| Workers | 24 |
| 请求方式 | 流式 Chat Completions，采集 TTFT |
| Reasoning / Thinking 控制 | 未显式指定 reasoning/thinking 参数；保留模型与平台默认行为 |
| Prompt 长度分层 | `short`≈1500、`medium`≈8000、`long`≈32000 |
| 剔除记录 | 16 |

## 4. 结果：总体指标与主要发现

| 路由模式 | 平台 | 严格配对轮数 | 总 Input Tokens | Token 级缓存命中率 | 实际成本 | 吞吐量 | 端到端 E2E 时延 | 流式 TTFT |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 吞吐优先 | Infron | 196 | 6340852 | 87.70% | **$2.35911200** | 2.61 tok/s | **4815.56 ms** | 4237.16 ms |
| 吞吐优先 | **OpenRouter** | 196 | 6340852 | **90.15%** | $11.72252143 | **48.12 tok/s** | 45202.33 ms | **2238.17 ms** |
| 价格优先 | Infron | 197 | 6332778 | 97.16% | **$1.29962000** | 3.39 tok/s | **3695.85 ms** | 3278.24 ms |
| 价格优先 | **OpenRouter** | 197 | 6332778 | **97.32%** | $1.30994008 | **47.05 tok/s** | 16059.34 ms | **2866.39 ms** |
| 端到端时延优先 | Infron | 200 | 6414682 | 96.85% | $3.45964100 | 4.03 tok/s | **3119.38 ms** | 2835.38 ms |
| 端到端时延优先 | **OpenRouter** | 200 | 6414682 | **99.43%** | **$1.68043559** | **5.13 tok/s** | 3120.18 ms | **2387.82 ms** |
| 流式 TTFT 优先 | **Infron** | 199 | 6396238 | **90.65%** | **$1.47298600** | 3.17 tok/s | **3927.90 ms** | 3460.80 ms |
| 流式 TTFT 优先 | OpenRouter | 199 | 6396238 | 90.50% | $6.21110423 | **41.60 tok/s** | 9840.11 ms | **2467.55 ms** |

### 4.1 尾延迟与显著性检验

尾延迟分位数补充均值无法表达的尾部风险。

| 路由模式 | 平台 | P50 Latency | P95 Latency | P99 Latency | P50 TTFT | P95 TTFT | P99 TTFT |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 吞吐优先 | Infron | 3205.84 ms | **15260.63 ms** | **27522.80 ms** | 2755.11 ms | 14748.86 ms | 26879.53 ms |
| 吞吐优先 | **OpenRouter** | **1986.21 ms** | 488985.92 ms | 978823.46 ms | **1844.43 ms** | **5059.73 ms** | **5890.09 ms** |
| 价格优先 | Infron | **3175.76 ms** | **8392.18 ms** | **12749.50 ms** | 2778.86 ms | 7766.03 ms | 12389.07 ms |
| 价格优先 | **OpenRouter** | 3223.35 ms | 22306.38 ms | 597046.76 ms | **2420.72 ms** | **5461.09 ms** | **8349.43 ms** |
| 端到端时延优先 | Infron | **2356.66 ms** | 6139.54 ms | 10955.27 ms | **2168.31 ms** | 5550.92 ms | 10530.32 ms |
| 端到端时延优先 | **OpenRouter** | 2896.61 ms | **5714.99 ms** | **7332.56 ms** | 2183.62 ms | **4346.92 ms** | **5286.50 ms** |
| 流式 TTFT 优先 | **Infron** | 2817.32 ms | 10246.12 ms | **29526.18 ms** | 2313.33 ms | 9510.77 ms | 29429.36 ms |
| 流式 TTFT 优先 | OpenRouter | **2542.11 ms** | **6319.66 ms** | 55239.59 ms | **2048.63 ms** | **5144.78 ms** | **10020.13 ms** |

均值差使用 bootstrap 95% CI，p-value 使用 paired sign-flip permutation test。

| 路由模式 | 指标 | 均值差 | 95% CI | p-value | 配对数 | 解释 |
| --- | --- | --- | --- | --- | --- | --- |
| 吞吐优先 | Latency: OpenRouter - Infron | **80773.54 ms** | 48187.49 ms to 115069.98 ms | <0.001 | 196 | 正值表示 Infron latency 更低 |
| 吞吐优先 | TTFT: OpenRouter - Infron | **-3997.97 ms** | -5040.73 ms to -3118.27 ms | <0.001 | 196 | 正值表示 Infron TTFT 更低 |
| 吞吐优先 | Throughput: Infron - OpenRouter | **-13.0327 tok/s** | -15.4306 tok/s to -10.7098 tok/s | <0.001 | 196 | 正值表示 Infron throughput 更高 |
| 吞吐优先 | Cost: OpenRouter - Infron | **$0.04777250** | $0.04158206 to $0.05474179 | <0.001 | 196 | 正值表示 Infron 成本更低 |
| 吞吐优先 | Token Cache Hit: Infron - OpenRouter | **-3.91 pp** | -8.94 pp to 1.55 pp | 0.1547 | 196 | 正值表示 Infron cache hit 更高 |
| 价格优先 | Latency: OpenRouter - Infron | **24726.98 ms** | 9517.45 ms to 42808.20 ms | <0.001 | 197 | 正值表示 Infron latency 更低 |
| 价格优先 | TTFT: OpenRouter - Infron | **-823.70 ms** | -1358.63 ms to -275.83 ms | 0.0030 | 197 | 正值表示 Infron TTFT 更低 |
| 价格优先 | Throughput: Infron - OpenRouter | **-5.0436 tok/s** | -7.0884 tok/s to -3.2296 tok/s | <0.001 | 197 | 正值表示 Infron throughput 更高 |
| 价格优先 | Cost: OpenRouter - Infron | **$0.00005239** | $-0.00230687 to $0.00269302 | 0.9660 | 197 | 正值表示 Infron 成本更低 |
| 价格优先 | Token Cache Hit: Infron - OpenRouter | **-3.25 pp** | -5.89 pp to -0.73 pp | 0.0140 | 197 | 正值表示 Infron cache hit 更高 |
| 端到端时延优先 | Latency: OpenRouter - Infron | **1.61 ms** | -607.85 ms to 509.31 ms | 0.9955 | 200 | 正值表示 Infron latency 更低 |
| 端到端时延优先 | TTFT: OpenRouter - Infron | **-895.11 ms** | -1460.28 ms to -439.17 ms | <0.001 | 200 | 正值表示 Infron TTFT 更低 |
| 端到端时延优先 | Throughput: Infron - OpenRouter | **-0.5847 tok/s** | -1.0223 tok/s to -0.1315 tok/s | 0.0177 | 200 | 正值表示 Infron throughput 更高 |
| 端到端时延优先 | Cost: OpenRouter - Infron | **$-0.00889603** | $-0.01153673 to $-0.00616604 | <0.001 | 200 | 正值表示 Infron 成本更低 |
| 端到端时延优先 | Token Cache Hit: Infron - OpenRouter | **-1.46 pp** | -3.96 pp to 1.22 pp | 0.3007 | 200 | 正值表示 Infron cache hit 更高 |
| 流式 TTFT 优先 | Latency: OpenRouter - Infron | **11824.42 ms** | 674.68 ms to 27150.73 ms | 0.1325 | 199 | 正值表示 Infron latency 更低 |
| 流式 TTFT 优先 | TTFT: OpenRouter - Infron | **-1986.49 ms** | -2989.55 ms to -1004.35 ms | <0.001 | 199 | 正值表示 Infron TTFT 更低 |
| 流式 TTFT 优先 | Throughput: Infron - OpenRouter | **-3.1953 tok/s** | -4.5543 tok/s to -2.1213 tok/s | <0.001 | 199 | 正值表示 Infron throughput 更高 |
| 流式 TTFT 优先 | Cost: OpenRouter - Infron | **$0.02380964** | $0.01799208 to $0.02969512 | <0.001 | 199 | 正值表示 Infron 成本更低 |
| 流式 TTFT 优先 | Token Cache Hit: Infron - OpenRouter | **1.13 pp** | -3.76 pp to 6.03 pp | 0.6888 | 199 | 正值表示 Infron cache hit 更高 |

### 4.2 Reasoning / Thinking 控制校验

本轮未显式指定 reasoning/thinking 参数，保留模型与平台默认行为；该表记录默认行为下的 reasoning telemetry。

| 路由模式 | 平台 | Reasoning Tokens | 平均 Reasoning Tokens/请求 | Reasoning 请求数 | 平均首 Reasoning Token | 平均 TTFT | 平均 E2E 时延 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 吞吐优先 | Infron | **0** | **0.0000** | **0** | **0.00 ms** | 4237.16 ms | **4815.56 ms** |
| 吞吐优先 | **OpenRouter** | 852412 | 2174.5204 | 392 | 2238.17 ms | **2238.17 ms** | 45202.33 ms |
| 价格优先 | Infron | **0** | **0.0000** | **0** | **0.00 ms** | 3278.24 ms | **3695.85 ms** |
| 价格优先 | **OpenRouter** | 300492 | 762.6701 | 394 | 2866.39 ms | **2866.39 ms** | 16059.34 ms |
| 端到端时延优先 | Infron | **0** | **0.0000** | **0** | **0.00 ms** | 2835.38 ms | **3119.38 ms** |
| 端到端时延优先 | **OpenRouter** | 9454 | 23.6350 | 400 | 2387.82 ms | **2387.82 ms** | 3120.18 ms |
| 流式 TTFT 优先 | **Infron** | **0** | **0.0000** | **0** | **0.00 ms** | 3460.80 ms | **3927.90 ms** |
| 流式 TTFT 优先 | OpenRouter | 164853 | 414.2035 | 398 | 2467.55 ms | **2467.55 ms** | 9840.11 ms |

### 4.3 API 协议兼容性矩阵

本轮 API 协议为 `/v1/chat/completions`；本表记录两家平台在该协议下的成功响应、usage、成本和缓存 telemetry 覆盖。

| API 协议 | Endpoint | 平台 | 配对轮数 | 请求数 | 成功率 | Usage 覆盖 | Token Usage 覆盖 | 成本覆盖 | 缓存 Telemetry 覆盖 | HTTP 状态 | 主要错误 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `chat_completions` | `/v1/chat/completions` | Infron | 800 | 1600 | **100.00%** | **100.00%** | **100.00%** | **100.00%** | **100.00%** | {"200":1600} |  |
| `chat_completions` | `/v1/chat/completions` | OpenRouter | 800 | 1600 | 99.94% | 99.69% | 99.69% | 99.69% | **100.00%** | {"0":1,"200":1599} | 1 x Remote end closed connection without response |

## 5. 结果可视化：按路由模式的核心指标变化

以下图表使用同一份严格配对后的 summary 数据驱动，统一展示路由模式、平台差异、成本、缓存、端到端 E2E 时延、流式 TTFT 和上游 Provider 分布。

### 5.1 核心指标图表总览

以下图表使用同一份严格配对后的 summary 数据生成，统一展示路由模式、平台差异、成本、缓存、端到端 E2E 时延、流式 TTFT 和上游 Provider 分布。

图 3-E1：路由模式级核心指标对比

按路由模式并列展示 Infron 与 OpenRouter。

图 3-E2：归一化综合轮廓

五项指标统一转为 0-100 且越高越好。

图 3-E3：成本-缓存效率平面

横轴为 Token 级缓存命中率，纵轴为总实际成本。

图 3-E4：端到端 E2E 时延与流式 TTFT

实线表示端到端 E2E 时延，虚线表示流式 TTFT。

图 3-E5：上游 Provider 分布

按路由模式展示主要上游路径占比。

### 模式级下钻图表

横轴表示相对优势百分比：右侧蓝色代表 Infron 优势，左侧橙色代表 OpenRouter 优势。

图 4-E1：Throughput First 路由模式下的核心指标对比

展示五项核心指标的相对优势方向与幅度。

图 4-E2：Price First 路由模式下的核心指标对比

展示五项核心指标的相对优势方向与幅度。

图 4-E3：Latency First 路由模式下的核心指标对比

展示五项核心指标的相对优势方向与幅度。

图 4-E4：TTFT First 路由模式下的核心指标对比

展示五项核心指标的相对优势方向与幅度。

## 6. Infron 技术架构与缓存/成本机制解释

图 12：Infron 多 provider 路由与缓存控制面

**统一 API 入口**OpenAI-compatible 请求进入网关，保留 usage、stream 和 provider routing 参数 → **路由策略层**按 throughput / price / latency / ttft 目标选择健康上游路径 → **Provider Stick / Cache Affinity**重复长前缀尽量落入稳定缓存域 → **上游 Provider**响应 telemetry 反馈 provider、usage、cost、latency 和 TTFT

### 6.1 多 provider 路由与可观测控制面

请求进入统一 API 后，路由策略层根据 throughput、price、latency 或 ttft 目标选择健康上游路径。稳定长前缀请求是否落在相同缓存域，会直接影响第二次请求的 cache read tokens。

### 6.2 Provider Stick 与 Cache Affinity

Provider stick 是缓存亲和策略，不等于固定锁死 provider。它的目标是在健康和 SLA 约束下减少缓存域碎片化，使重复 prefix 更容易复用已有缓存。

### 6.3 成本控制路径

| 机制 | 对 cache rate 的影响 | 对成本的影响 | 本次实验中的可观测信号 |
| --- | --- | --- | --- |
| Stable prefix 识别 | 相同前缀更容易命中已有 cache | 降低重复 prefill 的边际成本 | 同一 payload SHA256、第二次请求 cache read tokens |
| Provider stick / cache affinity | 降低跨 provider/cache domain 的缓存碎片 | 减少重复暖缓存 | provider 分布与 Token 级命中率共同变化 |
| 健康检查与 fallback | 保护可用性，必要时牺牲部分缓存收益 | 降低失败成本 | HTTP 状态、provider 分布和尾延迟变化 |
| 成本感知 routing | 在健康约束下偏向低成本路径 | 降低总成本和每轮成本 | 实际成本、cost breakdown 覆盖率、cache read tokens |

## 7. Provider/Route 下钻分析

| 路由模式 | 平台 | 总请求数 | 已归因请求数 | Provider 分布 |
| --- | --- | --- | --- | --- |
| 吞吐优先 | Infron | 392 | 392 | `atlas-cloud` 128, `alibaba/cn` 96, `z-ai` 85, `deepinfra` 83 |
| 吞吐优先 | OpenRouter | 392 | 392 | `Cerebras` 275, `StreamLake` 43, `DeepInfra` 40, `Google` 34 |
| 价格优先 | Infron | 394 | 394 | `alibaba/cn` 262, `atlas-cloud` 114, `deepinfra` 18 |
| 价格优先 | OpenRouter | 394 | 394 | `DeepInfra` 373, `StreamLake` 21 |
| 端到端时延优先 | Infron | 400 | 400 | `cerebras` 224, `atlas-cloud` 176 |
| 端到端时延优先 | OpenRouter | 400 | 400 | `DeepInfra` 336, `Cerebras` 61, `Google` 3 |
| 流式 TTFT 优先 | Infron | 398 | 398 | `cerebras` 190, `deepinfra` 183, `byteplus` 25 |
| 流式 TTFT 优先 | OpenRouter | 398 | 398 | `Cerebras` 184, `DeepInfra` 149, `Google` 57, `StreamLake` 5, `Venice` 3 |

### 上游 Provider 明细分布

| 路由模式 | 平台 | 上游 Provider | 请求数 | 占比 | first/second | 覆盖轮次 | Avg TTFT | Avg Latency | Prompt Tokens | Completion Tokens | Reasoning Tokens | Cache Read Tokens | 观测成本 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 吞吐优先 | Infron | `atlas-cloud` | 128 | 32.65% | 57/71 | 71 | 3015.57 ms | 3378.43 ms | 2172789 | 1676 | 0 | 1835392 | $1.13278600 |
| 吞吐优先 | Infron | `alibaba/cn` | 96 | 24.49% | 55/41 | 55 | 3523.03 ms | 3881.86 ms | 1343164 | 1184 | 0 | 968832 | $0.15570100 |
| 吞吐优先 | Infron | `z-ai` | 85 | 21.68% | 45/40 | 54 | 5791.82 ms | 6227.12 ms | 1386006 | 1025 | 0 | 1140224 | $0.83385100 |
| 吞吐优先 | Infron | `deepinfra` | 83 | 21.17% | 39/44 | 53 | 5354.90 ms | 6666.21 ms | 1438893 | 1049 | 0 | 1064480 | $0.23677400 |
| 吞吐优先 | OpenRouter | `Cerebras` | 275 | 70.15% | 137/138 | 163 | 1784.62 ms | 1848.12 ms | 4030603 | 4400 | 4400 | 3679360 | $9.08095675 |
| 吞吐优先 | OpenRouter | `StreamLake` | 43 | 10.97% | 23/20 | 42 | 4411.22 ms | 394378.19 ms | 1064769 | 847035 | 846252 | 1060864 | $2.00187072 |
| 吞吐优先 | OpenRouter | `DeepInfra` | 40 | 10.20% | 18/22 | 22 | 1993.00 ms | 2727.93 ms | 213119 | 640 | 932 | 210272 | $0.01908056 |
| 吞吐优先 | OpenRouter | `Google` | 34 | 8.67% | 18/16 | 31 | 3446.75 ms | 4226.42 ms | 1032361 | 544 | 828 | 542272 | $0.62061340 |
| 价格优先 | Infron | `alibaba/cn` | 262 | 66.50% | 132/130 | 139 | 3374.68 ms | 3753.99 ms | 4201868 | 3192 | 0 | 4065408 | $0.25841400 |
| 价格优先 | Infron | `atlas-cloud` | 114 | 28.93% | 56/58 | 65 | 2982.92 ms | 3405.47 ms | 1840318 | 1534 | 0 | 1789824 | $0.95965100 |
| 价格优先 | Infron | `deepinfra` | 18 | 4.57% | 9/9 | 9 | 3744.93 ms | 4688.60 ms | 290592 | 204 | 0 | 109504 | $0.08155500 |
| 价格优先 | OpenRouter | `DeepInfra` | 373 | 94.67% | 188/185 | 196 | 2684.14 ms | 3596.74 ms | 5907457 | 5968 | 9116 | 5565920 | $0.59233240 |
| 价格优先 | OpenRouter | `StreamLake` | 21 | 5.33% | 9/12 | 20 | 6103.59 ms | 237418.80 ms | 425321 | 291735 | 291376 | 370816 | $0.71760768 |
| 端到端时延优先 | Infron | `cerebras` | 224 | 56.00% | 115/109 | 129 | 1669.54 ms | 1820.29 ms | 1423410 | 2784 | 0 | 1183872 | $0.86027200 |
| 端到端时延优先 | Infron | `atlas-cloud` | 176 | 44.00% | 85/91 | 105 | 4319.17 ms | 4772.76 ms | 4991272 | 2238 | 0 | 4888320 | $2.59936900 |
| 端到端时延优先 | OpenRouter | `DeepInfra` | 336 | 84.00% | 166/170 | 174 | 2524.43 ms | 3381.79 ms | 5897735 | 5376 | 8420 | 5689408 | $0.54789144 |
| 端到端时延优先 | OpenRouter | `Cerebras` | 61 | 15.25% | 33/28 | 38 | 1655.31 ms | 1714.24 ms | 496719 | 976 | 976 | 482688 | $1.12030175 |
| 端到端时延优先 | OpenRouter | `Google` | 3 | 0.75% | 1/2 | 3 | 1982.30 ms | 2407.21 ms | 20228 | 48 | 58 | 18432 | $0.01224240 |
| 流式 TTFT 优先 | Infron | `cerebras` | 190 | 47.74% | 98/92 | 113 | 1579.81 ms | 1718.75 ms | 1098069 | 2250 | 0 | 1085184 | $0.66387200 |
| 流式 TTFT 优先 | Infron | `deepinfra` | 183 | 45.98% | 86/97 | 109 | 3299.62 ms | 4156.87 ms | 4602829 | 2342 | 0 | 4544320 | $0.39109400 |
| 流式 TTFT 优先 | Infron | `byteplus` | 25 | 6.28% | 15/10 | 22 | 18936.10 ms | 19041.43 ms | 695340 | 367 | 0 | 0 | $0.41802000 |
| 流式 TTFT 优先 | OpenRouter | `Cerebras` | 184 | 46.23% | 93/91 | 113 | 1996.63 ms | 2064.39 ms | 2088233 | 2944 | 2944 | 1977344 | $4.70662025 |
| 流式 TTFT 优先 | OpenRouter | `DeepInfra` | 149 | 37.44% | 74/75 | 87 | 2665.34 ms | 3745.02 ms | 2639463 | 2384 | 3831 | 2549664 | $0.24406472 |
| 流式 TTFT 优先 | OpenRouter | `Google` | 57 | 14.32% | 28/29 | 47 | 2900.58 ms | 3388.18 ms | 1481877 | 912 | 1458 | 986432 | $0.89113260 |
| 流式 TTFT 优先 | OpenRouter | `StreamLake` | 5 | 1.26% | 3/2 | 5 | 7491.29 ms | 553229.52 ms | 130771 | 156626 | 156539 | 93056 | $0.33843184 |
| 流式 TTFT 优先 | OpenRouter | `Venice` | 3 | 0.75% | 1/2 | 3 | 4926.22 ms | 6411.97 ms | 55894 | 48 | 81 | 32 | $0.03085482 |

### 7.1 缓存命中率与实际成本反向表现下钻

该表把 cache、cost、provider 分布和 reasoning telemetry 放在同一层级，解释每个路由模式的主要差异来源。

| 路由模式 | 缓存命中差值 | Infron 成本倍数 | Infron 主要路径 | OpenRouter 主要路径 | Reasoning Tokens 差异 | 主要归因 |
| --- | --- | --- | --- | --- | --- | --- |
| 吞吐优先 | -2.45 pp | **0.20x** | **`atlas-cloud` 32.65%** | **`Cerebras` 70.15%** | **-852412** | 缓存和成本方向存在分化，需结合速度指标判断 |
| 价格优先 | -0.16 pp | **0.99x** | **`alibaba/cn` 66.50%** | **`DeepInfra` 94.67%** | **-300492** | 缓存和成本方向存在分化，需结合速度指标判断 |
| 端到端时延优先 | -2.58 pp | 2.06x | `cerebras` 56.00% | **`DeepInfra` 84.00%** | **-9454** | OpenRouter 缓存更高且成本更低，主要看 provider/cache 域差异 |
| 流式 TTFT 优先 | **+0.15 pp** | **0.24x** | **`cerebras` 47.74%** | `Cerebras` 46.23% | **-164853** | Infron 缓存与成本同向占优 |

## 8. 分层结果：按 Prompt 长度的缓存表现

本节按 prompt 长度 tier 聚合第二次请求的 cache read tokens、Token 级缓存命中率、实际成本、端到端时延和流式 TTFT。加粗单元表示同一长度 tier 下表现更优的一方。

### Prompt 长度分层总览

| Prompt 长度 tier | 目标 tokens | 平台 | 轮数 | 第二次 Prompt Tokens | 第二次 Cache Read Tokens | Token 级命中率 | 实际成本 | 平均 E2E 时延 | 平均 TTFT |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `short` | 1500 | Infron | **266** | **468570** | 426208 | 90.96% | **$0.40699000** | **2062.10 ms** | 1753.08 ms |
| `short` | 1500 | OpenRouter | **266** | **468570** | **438400** | **93.56%** | $1.14530131 | 6198.48 ms | **1687.32 ms** |
| `medium` | 8000 | Infron | **263** | **2427115** | 2302784 | 94.88% | **$1.80182600** | **3563.12 ms** | 3122.63 ms |
| `medium` | 8000 | OpenRouter | **263** | **2427115** | **2349728** | **96.81%** | $5.54600964 | 15638.37 ms | **2252.96 ms** |
| `long` | 32000 | Infron | **263** | **9846590** | 9133536 | 92.76% | **$6.38254300** | **6052.63 ms** | 5492.40 ms |
| `long` | 32000 | OpenRouter | **263** | **9846590** | **9234880** | **93.79%** | $14.23269038 | 33626.91 ms | **3538.45 ms** |

### Prompt 长度 x 路由模式缓存命中率

| Prompt 长度 tier | 路由模式 | Infron | OpenRouter | 胜出方 |
| --- | --- | --- | --- | --- |
| `short` | 吞吐优先 | 85.41% | **92.62%** | **OpenRouter** |
| `short` | 价格优先 | 91.77% | **97.42%** | **OpenRouter** |
| `short` | 端到端时延优先 | 93.06% | **94.03%** | **OpenRouter** |
| `short` | 流式 TTFT 优先 | **93.62%** | 90.29% | **Infron** |
| `medium` | 吞吐优先 | 91.44% | **93.48%** | **OpenRouter** |
| `medium` | 价格优先 | 94.34% | **99.82%** | **OpenRouter** |
| `medium` | 端到端时延优先 | 98.21% | **98.38%** | **OpenRouter** |
| `medium` | 流式 TTFT 优先 | 95.33% | **95.34%** | **OpenRouter** |
| `long` | 吞吐优先 | 86.93% | **89.25%** | **OpenRouter** |
| `long` | 价格优先 | **98.13%** | 96.67% | **Infron** |
| `long` | 端到端时延优先 | 96.70% | **99.96%** | **OpenRouter** |
| `long` | 流式 TTFT 优先 | **89.35%** | 89.31% | **Infron** |

## 9. 分层结果：按实验组的稳定性检查

### 吞吐优先

| 平台 | 组别 | 轮数 | 成功轮数 | Token 命中率 | 实际成本 | P95 Latency | P95 TTFT |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Infron | 1 | 48 | 48 | 84.52% | **$0.20900000** | **15394.45 ms** | 14543.95 ms |
| Infron | 2 | 49 | 49 | **79.53%** | **$0.41033100** | **22335.58 ms** | 21558.06 ms |
| Infron | 3 | 49 | 49 | 92.16% | **$0.92022400** | **13146.75 ms** | 12940.77 ms |
| Infron | 4 | 50 | 50 | 94.70% | **$0.81955700** | **7774.10 ms** | 7350.46 ms |
| OpenRouter | 1 | 48 | 48 | **93.31%** | $2.92280559 | 487720.79 ms | **5337.85 ms** |
| OpenRouter | 2 | 49 | 49 | 77.90% | $2.62445875 | 623230.31 ms | **5314.08 ms** |
| OpenRouter | 3 | 49 | 49 | **94.84%** | $2.97944500 | 28482.04 ms | **4926.91 ms** |
| OpenRouter | 4 | 50 | 50 | **94.93%** | $3.19581209 | 44049.73 ms | **4526.62 ms** |

### 价格优先

| 平台 | 组别 | 轮数 | 成功轮数 | Token 命中率 | 实际成本 | P95 Latency | P95 TTFT |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Infron | 1 | 48 | 48 | 91.88% | **$0.16758700** | **9304.59 ms** | 8268.21 ms |
| Infron | 2 | 50 | 50 | 99.12% | **$0.33531200** | **7282.33 ms** | 7144.26 ms |
| Infron | 3 | 49 | 49 | **98.17%** | $0.40023700 | **5469.66 ms** | 5079.31 ms |
| Infron | 4 | 50 | 50 | 99.08% | $0.39648400 | 10892.53 ms | 10016.62 ms |
| OpenRouter | 1 | 48 | 48 | **94.85%** | $0.52433344 | 42930.43 ms | **5543.44 ms** |
| OpenRouter | 2 | 50 | 50 | **99.31%** | $0.37593736 | 23865.89 ms | **5852.94 ms** |
| OpenRouter | 3 | 49 | 49 | 95.28% | **$0.25281960** | 6450.57 ms | **4602.33 ms** |
| OpenRouter | 4 | 50 | 50 | **99.68%** | **$0.15684968** | **8191.63 ms** | **5221.84 ms** |

### 端到端时延优先

| 平台 | 组别 | 轮数 | 成功轮数 | Token 命中率 | 实际成本 | P95 Latency | P95 TTFT |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Infron | 1 | 50 | 50 | 98.13% | $0.87834400 | **5480.00 ms** | 5078.45 ms |
| Infron | 2 | 50 | 50 | 94.96% | $0.87516500 | 6819.94 ms | 5605.96 ms |
| Infron | 3 | 50 | 50 | 94.98% | $0.86795900 | 6129.32 ms | 5612.93 ms |
| Infron | 4 | 50 | 50 | 99.49% | $0.83817300 | 6073.53 ms | 5363.47 ms |
| OpenRouter | 1 | 50 | 50 | **99.65%** | **$0.45228386** | 5727.80 ms | **4333.76 ms** |
| OpenRouter | 2 | 50 | 50 | **98.54%** | **$0.36502139** | **5821.87 ms** | **4263.78 ms** |
| OpenRouter | 3 | 50 | 50 | **99.69%** | **$0.37872743** | **5397.15 ms** | **4378.57 ms** |
| OpenRouter | 4 | 50 | 50 | **99.89%** | **$0.48440291** | **5531.57 ms** | **4154.45 ms** |

### 流式 TTFT 优先

| 平台 | 组别 | 轮数 | 成功轮数 | Token 命中率 | 实际成本 | P95 Latency | P95 TTFT |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Infron | 1 | 50 | 50 | 63.83% | **$0.80475000** | 28182.96 ms | 28066.61 ms |
| Infron | 2 | 49 | 49 | **98.63%** | **$0.24074900** | **6190.14 ms** | **5378.94 ms** |
| Infron | 3 | 50 | 50 | **99.75%** | **$0.20363800** | 6177.89 ms | 5146.51 ms |
| Infron | 4 | 50 | 50 | **99.80%** | **$0.22384900** | **5185.56 ms** | **3845.64 ms** |
| OpenRouter | 1 | 50 | 50 | **94.85%** | $1.36985113 | **4181.53 ms** | **3503.71 ms** |
| OpenRouter | 2 | 49 | 49 | 75.58% | $2.11139781 | 9203.58 ms | 5565.45 ms |
| OpenRouter | 3 | 50 | 50 | 99.34% | $1.05860361 | **4848.89 ms** | **3330.83 ms** |
| OpenRouter | 4 | 50 | 50 | 92.41% | $1.67125168 | 8486.81 ms | 5933.69 ms |

## 10. 讨论：业务价值、适用边界与工程启示

业务决策不应只看单一指标。稳定长上下文和高频模板请求优先关注缓存命中率与成本；实时交互应同时约束 TTFT 和端到端时延；后台批处理更重视吞吐与失败成本。

| 路由模式 | 主要业务目标 | 本轮数据体现 | 适用场景 | 注意事项 |
| --- | --- | --- | --- | --- |
| 吞吐优先 | 最大化单位时间输出能力 | OpenRouter 综合占优（3/5 指标） | 批量内容生成、离线摘要、后台数据加工 | 适合吞吐优先任务，但成本和缓存需单独约束 |
| 价格优先 | 最小化单位请求和单位 token 成本 | OpenRouter 综合占优（3/5 指标） | 高频模板化请求、客服自动化、营销触达、RAG 固定前缀 | 适合吞吐优先任务，但成本和缓存需单独约束 |
| 端到端时延优先 | 最小化完整响应等待时间 | OpenRouter 综合占优（4/5 指标） | 在线聊天、Agent 调用链、IDE/写作辅助、实时运营工具 | 适合吞吐优先任务，但成本和缓存需单独约束 |
| 流式 TTFT 优先 | 最小化流式首包响应时间 | Infron 综合占优（3/5 指标） | 流式聊天、实时 Copilot、首屏反馈、长任务进度感知 | 缓存和成本更稳，但仍需检查速度 SLA |

## 11. 结论

### 路由模式级结论

| 路由模式 | 目标 | 缓存胜出 | 成本胜出 | 吞吐胜出 | E2E 时延胜出 | TTFT 胜出 | 解读 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 吞吐优先 | 最大化单位时间输出能力 | **OpenRouter** | **Infron** | **OpenRouter** | **Infron** | **OpenRouter** | OpenRouter 综合占优（3/5 指标） |
| 价格优先 | 最小化单位请求和单位 token 成本 | **OpenRouter** | **Infron** | **OpenRouter** | **Infron** | **OpenRouter** | OpenRouter 综合占优（3/5 指标） |
| 端到端时延优先 | 最小化完整响应等待时间 | **OpenRouter** | **OpenRouter** | **OpenRouter** | **Infron** | **OpenRouter** | OpenRouter 综合占优（4/5 指标） |
| 流式 TTFT 优先 | 最小化流式首包响应时间 | **Infron** | **Infron** | **OpenRouter** | **Infron** | **OpenRouter** | Infron 综合占优（3/5 指标） |

## 12. 局限性、缺失数据与后续实验计划

| 缺失或不足 | 对结论的影响 | 后续补充方式 | 当前处理方式 |
| --- | --- | --- | --- |
| 完整 routing trace | 无法逐跳证明每次请求的 provider 选择、fallback 和重试路径 | 补充 provider routing trace、decision log 和 fallback reason | 只使用响应中真实返回的 provider 字段和 provider 分布 |
| 更长时间窗口 | 4x50 能观察短期稳定性，但不能覆盖日级波动 | 增加 soak test 和跨时段重复实验 | 报告限定在本轮窗口内解释 |
| 真实生产语料 | 内置模板不能覆盖全部业务分布 | 使用脱敏生产语料分层抽样 | 当前只讨论代表性长上下文业务模板 |
| 成本字段一致性 | 不同平台 cost 字段覆盖率和口径可能不同 | 结合账单回查和 provider cost breakdown | 只统计响应明确返回的成本字段 |

## 13. 可复现性附录

| 工件 | 路径 |
| --- | --- |
| Summary | [summary.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-4.7/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/summary.json) |
| 配对数据集 | [benchmark_pairs.csv](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-4.7/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/benchmark_pairs.csv) |
| 请求级数据集 | [benchmark_requests.jsonl](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-4.7/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/benchmark_requests.jsonl) |
| 过滤后结构化记录 | [records.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-4.7/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/records.json) |
| 剔除记录审计 | [records_excluded.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-4.7/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/records_excluded.json) |
| 测试源码 | [test_rerun_routing_sort_cache_cost_ab.py](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-4.7/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/code/test_rerun_routing_sort_cache_cost_ab.py) |
| Benchmark 执行源码 | [rerun_routing_sort_cache_cost_ab.py](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-4.7/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/code/rerun_routing_sort_cache_cost_ab.py) |
| HTML 报告渲染源码 | [render_glm52_deepseek_style_report.py](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-4.7/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/code/render_glm52_deepseek_style_report.py) |
| 数据集引用 | `business_representative` 内置代表性业务模板；请求级导出见 `benchmark_requests.jsonl` |

在线 HTML：中文 [https://infronai.github.io/prompt-cache-bench/experiments/z-ai/glm-4.7/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/reports/routing-cache-cost-streaming-performance-ab-study__glm-4-7__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-07.zh.html](https://infronai.github.io/prompt-cache-bench/experiments/z-ai/glm-4.7/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/reports/routing-cache-cost-streaming-performance-ab-study__glm-4-7__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-07.zh.html)；英文 [https://infronai.github.io/prompt-cache-bench/experiments/z-ai/glm-4.7/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/reports/routing-cache-cost-streaming-performance-ab-study__glm-4-7__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-07.en.html](https://infronai.github.io/prompt-cache-bench/experiments/z-ai/glm-4.7/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/reports/routing-cache-cost-streaming-performance-ab-study__glm-4-7__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-07.en.html)。
