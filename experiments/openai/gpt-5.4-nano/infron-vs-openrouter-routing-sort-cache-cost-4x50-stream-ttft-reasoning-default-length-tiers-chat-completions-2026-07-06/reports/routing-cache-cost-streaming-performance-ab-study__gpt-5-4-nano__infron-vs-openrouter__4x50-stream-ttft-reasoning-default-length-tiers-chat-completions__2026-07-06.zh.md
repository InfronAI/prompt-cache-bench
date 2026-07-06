# Infron 与 OpenRouter 路由、缓存、成本与流式性能 A/B 实验报告

## 摘要与结论大纲

**关键词**：Prompt Caching；A/B Testing；Provider Routing；Cache Affinity；Latency；Throughput；Cost Attribution；gpt-5.4-nano

### 摘要

本报告以 `openai/gpt-5.4-nano` 为对象，评估 Infron 与 OpenRouter 在 Prompt Caching 场景下的缓存复用、实际成本、吞吐、端到端时延和流式 TTFT 表现。

核心结论是：Infron 在 1/4 个路由模式下缓存命中率占优，OpenRouter 在 3/4 个路由模式下占优，0/4 个路由模式持平；Infron 在所有路由模式下实际成本占优；Infron 在所有路由模式下吞吐量占优；OpenRouter 在所有路由模式下端到端 E2E 时延占优；OpenRouter 在所有路由模式下流式 TTFT占优。

整体看，Infron 的跨模式优势主要体现在吞吐、实际成本，OpenRouter 的跨模式优势主要体现在流式 TTFT、端到端 E2E 时延、缓存复用。平台选择不应只看单一指标，而应按业务目标在成本、缓存稳定性、吞吐和交互时延之间取舍。

### 图 0：Inference 平台“不可能四角”归一化综合轮廓

五个方向分别代表吞吐量、价格、端到端 E2E 时延、流式 TTFT 和缓存命中率。所有指标统一转为 0-100 分，且越外侧越好。

粗实线表示平台综合轮廓，半透明细线和点表示各路由模式下的表现。

结论总览：核心指标与路由模式胜出方

基于严格 A/B 配对样本。蓝色代表 Infron，橙色代表 OpenRouter；金色单元格表示该路由模式的目标指标胜出方。
**吞吐量**Infron 4/4 胜出最大优势 2.61%, 越高越好**实际成本**Infron 4/4 胜出最大优势 14.54%, 越低越好**端到端 E2E 时延**OpenRouter 4/4 胜出最大优势 25.05%, 越低越好**流式 TTFT**OpenRouter 4/4 胜出最大优势 11.30%, 越低越好**缓存命中率**OpenRouter 3/4 胜出最大优势 3.90%, 越高越好

| 路由模式 | 吞吐目标 | 成本目标 | 时延目标 | TTFT 目标 | 缓存结果 |
| --- | --- | --- | --- | --- | --- |
| **吞吐优先**<br>throughput | Infron优势 2.52% | Infron优势 12.51% | OpenRouter优势 19.78% | OpenRouter优势 10.85% | OpenRouter优势 0.40% |
| **价格优先**<br>price | Infron优势 2.61% | Infron优势 2.18% | OpenRouter优势 15.58% | OpenRouter优势 0.15% | OpenRouter优势 3.67% |
| **端到端时延优先**<br>latency | Infron优势 2.39% | Infron优势 14.54% | OpenRouter优势 22.52% | OpenRouter优势 7.38% | Infron优势 0.26% |
| **流式 TTFT 优先**<br>ttft | Infron优势 2.37% | Infron优势 0.25% | OpenRouter优势 25.05% | OpenRouter优势 11.30% | OpenRouter优势 3.90% |

### 结论大纲

| 研究维度 | 结论 | 证据位置 |
| --- | --- | --- |
| 控制变量 | 同一 `sort/group/round` 下 first/second `usage.prompt_tokens` 偏差不超过 50 tokens；总 Input Tokens 使用响应 telemetry。 | 方法与数据质量章节 |
| 缓存复用 | Infron 在 1/4 个路由模式下缓存命中率占优，OpenRouter 在 3/4 个路由模式下占优，0/4 个路由模式持平 | 总体指标与机制解释章节 |
| 实际成本 | Infron 在所有路由模式下实际成本占优 | 总体指标与 Provider 下钻章节 |
| 性能表现 | Infron 在所有路由模式下吞吐量占优；OpenRouter 在所有路由模式下端到端 E2E 时延占优；OpenRouter 在所有路由模式下流式 TTFT占优 | 结果可视化与统计检验章节 |
| 归因边界 | 报告只使用响应中可观测的 usage、cost、TTFT、latency、provider 字段和 cache tokens。 | Provider/Route 下钻分析章节 |
| 业务含义 | 长上下文、RAG 前缀、Agent 工具说明和高频模板请求应同时关注缓存命中率、成本、首包和端到端时延。 | 讨论与结论章节 |

### 路由模式级结论

| 路由模式 | 目标 | 缓存胜出 | 成本胜出 | 吞吐胜出 | E2E 时延胜出 | TTFT 胜出 | 解读 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 吞吐优先 | 最大化单位时间输出能力 | **OpenRouter** | **Infron** | **Infron** | **OpenRouter** | **OpenRouter** | OpenRouter 综合占优（3/5 指标） |
| 价格优先 | 最小化单位请求和单位 token 成本 | **OpenRouter** | **Infron** | **Infron** | **OpenRouter** | **OpenRouter** | OpenRouter 综合占优（3/5 指标） |
| 端到端时延优先 | 最小化完整响应等待时间 | **Infron** | **Infron** | **Infron** | **OpenRouter** | **OpenRouter** | Infron 综合占优（3/5 指标） |
| 流式 TTFT 优先 | 最小化流式首包响应时间 | **OpenRouter** | **Infron** | **Infron** | **OpenRouter** | **OpenRouter** | OpenRouter 综合占优（3/5 指标） |

## 1. 引言：背景、研究问题与贡献

LLM 推理平台的真实性能不仅由模型决定，也由 provider 路由、提示词缓存、流式响应、成本归因和 fallback 策略共同决定。本报告把平台视为可观测系统，以 A/B 配对方式评估速度、成本、缓存和首包体验的多目标权衡。

### 1.1 研究假设

| 假设 | 内容 | 验证指标 |
| --- | --- | --- |
| H1 | 重复稳定长前缀请求中，更强的 provider/cache affinity 会提升 Token 级缓存命中率。 | 第二次请求 cache read tokens、Token 级命中率 |
| H2 | 更高缓存命中率会降低真实响应成本，但不必然降低 TTFT 或端到端 latency。 | 实际成本、平均 TTFT、平均 latency/请求 |
| H3 | 不同 routing sort 会改变 provider 选择，从而形成不同的成本、吞吐和时延 Pareto 前沿。 | provider 分布、throughput、latency、cost |

### 1.2 本文贡献
使用响应返回的 `usage.prompt_tokens` 作为真实 input token 控制变量，并允许 50 tokens 内的小幅跨平台计数波动。将 prompt caching 评估扩展到成本、吞吐、E2E latency、TTFT、provider 分布、reasoning telemetry 和配对统计检验。所有结论只基于响应可观测 telemetry，不把平台内部私有 routing trace 当作已观测事实。

## 2. 方法：实验设计、数据集构造与控制变量

### 2.1 数据集生成方法

数据集名称为 `business_representative`，覆盖 4 种 routing sort、2 个平台、4 个实验组、每组 50 轮。每轮包含 first/second 两次相同 Chat Completions 请求：第一次建立或刷新缓存状态，第二次观测 cache read tokens、TTFT 和端到端响应。

业务模板覆盖稳定长上下文场景，包括 RAG 客服、Agent 工具说明、营销自动化和代码审查等高复用 prompt 结构。

### 2.2 控制变量方法

图 1：实验设计与严格 A/B 配对过滤
**固定 Payload**模型 openai/gpt-5.4-nano，同一路由模式下 payload SHA256 固定→**请求 A1/B1**第一次请求建立或刷新缓存状态→**请求 A2/B2**第二次请求观测 cache read tokens 与 TTFT→**严格过滤**只聚合 input-token 偏差不超过 50 的 A/B pairs

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
| 模型 | `openai/gpt-5.4-nano` |
| 平台实际模型 ID | infron: `openai/gpt-5.4-nano`; openrouter: `openai/gpt-5.4-nano` |
| 平台 | Infron、OpenRouter |
| API 协议 | `/v1/chat/completions` |
| 路由模式 | 吞吐优先、价格优先、端到端时延优先、流式 TTFT 优先 |
| 实验组 | 4 |
| 每组轮数 | 50 |
| Workers | 24 |
| 请求方式 | 流式 Chat Completions，采集 TTFT |
| Reasoning / Thinking 控制 | 未显式指定 reasoning/thinking 参数；保留模型与平台默认行为 |
| Prompt 长度分层 | `short`≈1500、`medium`≈8000、`long`≈32000 |
| 剔除记录 | 20 |

## 4. 结果：总体指标与主要发现

| 路由模式 | 平台 | 严格配对轮数 | 总 Input Tokens | Token 级缓存命中率 | 实际成本 | 吞吐量 | 端到端 E2E 时延 | 流式 TTFT |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 吞吐优先 | Infron | 200 | 6262580 | 92.54% | **$0.21638200** | **18.24 tok/s** | 3196.16 ms | 2422.16 ms |
| 吞吐优先 | **OpenRouter** | 200 | 6262580 | **92.91%** | $0.24345791 | 5.18 tok/s | **2668.31 ms** | **2185.01 ms** |
| 价格优先 | Infron | 194 | 5964592 | 93.81% | **$0.15337700** | **18.45 tok/s** | 3161.83 ms | 2373.12 ms |
| 价格优先 | **OpenRouter** | 194 | 5964592 | **97.25%** | $0.15672743 | 5.11 tok/s | **2735.66 ms** | **2369.49 ms** |
| 端到端时延优先 | **Infron** | 198 | 6117118 | **95.38%** | **$0.14883400** | **18.23 tok/s** | 3207.86 ms | 2419.43 ms |
| 端到端时延优先 | OpenRouter | 198 | 6117118 | 95.12% | $0.17046894 | 5.38 tok/s | **2618.18 ms** | **2253.12 ms** |
| 流式 TTFT 优先 | Infron | 198 | 6117122 | 93.46% | **$0.15877500** | **17.63 tok/s** | 3321.51 ms | 2498.98 ms |
| 流式 TTFT 优先 | **OpenRouter** | 198 | 6117122 | **97.11%** | $0.15917730 | 5.23 tok/s | **2656.24 ms** | **2245.33 ms** |

### 4.1 尾延迟与显著性检验

尾延迟分位数补充均值无法表达的尾部风险。

| 路由模式 | 平台 | P50 Latency | P95 Latency | P99 Latency | P50 TTFT | P95 TTFT | P99 TTFT |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 吞吐优先 | Infron | 2955.57 ms | 4934.77 ms | **6023.18 ms** | 2227.26 ms | 3945.49 ms | 5730.02 ms |
| 吞吐优先 | **OpenRouter** | **2396.26 ms** | **4269.54 ms** | 10115.76 ms | **2020.34 ms** | **3519.31 ms** | **4767.88 ms** |
| 价格优先 | Infron | 3019.49 ms | 4669.59 ms | 6120.17 ms | 2222.34 ms | **3599.42 ms** | **4969.66 ms** |
| 价格优先 | **OpenRouter** | **2463.58 ms** | **4238.64 ms** | **5744.71 ms** | **2156.99 ms** | 3669.98 ms | 5449.70 ms |
| 端到端时延优先 | **Infron** | 3054.49 ms | 4658.03 ms | **5847.52 ms** | 2193.80 ms | 3677.12 ms | **4926.94 ms** |
| 端到端时延优先 | OpenRouter | **2392.75 ms** | **4109.78 ms** | 6010.21 ms | **2087.42 ms** | **3573.68 ms** | 5224.04 ms |
| 流式 TTFT 优先 | Infron | 3067.54 ms | 5172.86 ms | 7030.92 ms | 2242.49 ms | 4074.42 ms | 6279.34 ms |
| 流式 TTFT 优先 | **OpenRouter** | **2432.86 ms** | **4209.05 ms** | **5721.74 ms** | **2112.12 ms** | **3730.59 ms** | **5219.15 ms** |

均值差使用 bootstrap 95% CI，p-value 使用 paired sign-flip permutation test。

| 路由模式 | 指标 | 均值差 | 95% CI | p-value | 配对数 | 解释 |
| --- | --- | --- | --- | --- | --- | --- |
| 吞吐优先 | Latency: OpenRouter - Infron | **-1055.70 ms** | -1452.44 ms to -655.74 ms | <0.001 | 200 | 正值表示 Infron latency 更低 |
| 吞吐优先 | TTFT: OpenRouter - Infron | **-474.31 ms** | -813.67 ms to -167.56 ms | 0.0018 | 200 | 正值表示 Infron TTFT 更低 |
| 吞吐优先 | Throughput: Infron - OpenRouter | **12.6346 tok/s** | 10.8967 tok/s to 14.4725 tok/s | <0.001 | 200 | 正值表示 Infron throughput 更高 |
| 吞吐优先 | Cost: OpenRouter - Infron | **$0.00013538** | $-0.00005966 to $0.00031376 | 0.1690 | 200 | 正值表示 Infron 成本更低 |
| 吞吐优先 | Token Cache Hit: Infron - OpenRouter | **24.34 pp** | 17.41 pp to 30.72 pp | <0.001 | 200 | 正值表示 Infron cache hit 更高 |
| 价格优先 | Latency: OpenRouter - Infron | **-852.35 ms** | -1242.40 ms to -382.43 ms | <0.001 | 194 | 正值表示 Infron latency 更低 |
| 价格优先 | TTFT: OpenRouter - Infron | **-7.27 ms** | -346.64 ms to 447.53 ms | 0.9788 | 194 | 正值表示 Infron TTFT 更低 |
| 价格优先 | Throughput: Infron - OpenRouter | **12.1359 tok/s** | 10.3406 tok/s to 13.9050 tok/s | <0.001 | 194 | 正值表示 Infron throughput 更高 |
| 价格优先 | Cost: OpenRouter - Infron | **$0.00001727** | $-0.00009310 to $0.00012059 | 0.7486 | 194 | 正值表示 Infron 成本更低 |
| 价格优先 | Token Cache Hit: Infron - OpenRouter | **-1.27 pp** | -4.24 pp to 1.76 pp | 0.5349 | 194 | 正值表示 Infron cache hit 更高 |
| 端到端时延优先 | Latency: OpenRouter - Infron | **-1179.35 ms** | -1523.12 ms to -842.98 ms | <0.001 | 198 | 正值表示 Infron latency 更低 |
| 端到端时延优先 | TTFT: OpenRouter - Infron | **-332.61 ms** | -682.64 ms to -20.97 ms | 0.0310 | 198 | 正值表示 Infron TTFT 更低 |
| 端到端时延优先 | Throughput: Infron - OpenRouter | **12.1062 tok/s** | 10.3876 tok/s to 13.8536 tok/s | <0.001 | 198 | 正值表示 Infron throughput 更高 |
| 端到端时延优先 | Cost: OpenRouter - Infron | **$0.00010927** | $-0.00002411 to $0.00026074 | 0.1232 | 198 | 正值表示 Infron 成本更低 |
| 端到端时延优先 | Token Cache Hit: Infron - OpenRouter | **-2.30 pp** | -5.20 pp to 0.59 pp | 0.1025 | 198 | 正值表示 Infron cache hit 更高 |
| 流式 TTFT 优先 | Latency: OpenRouter - Infron | **-1330.55 ms** | -1592.49 ms to -1087.56 ms | <0.001 | 198 | 正值表示 Infron latency 更低 |
| 流式 TTFT 优先 | TTFT: OpenRouter - Infron | **-507.29 ms** | -741.64 ms to -280.94 ms | <0.001 | 198 | 正值表示 Infron TTFT 更低 |
| 流式 TTFT 优先 | Throughput: Infron - OpenRouter | **11.8163 tok/s** | 10.0745 tok/s to 13.5822 tok/s | <0.001 | 198 | 正值表示 Infron throughput 更高 |
| 流式 TTFT 优先 | Cost: OpenRouter - Infron | **$0.00000203** | $-0.00011899 to $0.00010971 | 0.9763 | 198 | 正值表示 Infron 成本更低 |
| 流式 TTFT 优先 | Token Cache Hit: Infron - OpenRouter | **-1.55 pp** | -4.38 pp to 0.98 pp | 0.2927 | 198 | 正值表示 Infron cache hit 更高 |

### 4.2 Reasoning / Thinking 控制校验

本轮未显式指定 reasoning/thinking 参数，保留模型与平台默认行为；该表记录默认行为下的 reasoning telemetry。

| 路由模式 | 平台 | Reasoning Tokens | 平均 Reasoning Tokens/请求 | Reasoning 请求数 | 平均首 Reasoning Token | 平均 TTFT | 平均 E2E 时延 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 吞吐优先 | Infron | **0** | **0.0000** | **0** | **0.00 ms** | 2422.16 ms | 3196.16 ms |
| 吞吐优先 | **OpenRouter** | **0** | **0.0000** | **0** | **0.00 ms** | **2185.01 ms** | **2668.31 ms** |
| 价格优先 | Infron | **0** | **0.0000** | **0** | **0.00 ms** | 2373.12 ms | 3161.83 ms |
| 价格优先 | **OpenRouter** | **0** | **0.0000** | **0** | **0.00 ms** | **2369.49 ms** | **2735.66 ms** |
| 端到端时延优先 | **Infron** | **0** | **0.0000** | **0** | **0.00 ms** | 2419.43 ms | 3207.86 ms |
| 端到端时延优先 | OpenRouter | **0** | **0.0000** | **0** | **0.00 ms** | **2253.12 ms** | **2618.18 ms** |
| 流式 TTFT 优先 | Infron | **0** | **0.0000** | **0** | **0.00 ms** | 2498.98 ms | 3321.51 ms |
| 流式 TTFT 优先 | **OpenRouter** | **0** | **0.0000** | **0** | **0.00 ms** | **2245.33 ms** | **2656.24 ms** |

### 4.3 API 协议兼容性矩阵

本轮 API 协议为 `/v1/chat/completions`；本表记录两家平台在该协议下的成功响应、usage、成本和缓存 telemetry 覆盖。

| API 协议 | Endpoint | 平台 | 配对轮数 | 请求数 | 成功率 | Usage 覆盖 | Token Usage 覆盖 | 成本覆盖 | 缓存 Telemetry 覆盖 | HTTP 状态 | 主要错误 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `chat_completions` | `/v1/chat/completions` | Infron | 800 | 1600 | 99.25% | **100.00%** | **100.00%** | **100.00%** | **100.00%** | {"0":12,"200":1588} | 7 x [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1000)<br>5 x Remote end closed connection without response |
| `chat_completions` | `/v1/chat/completions` | OpenRouter | 800 | 1600 | **100.00%** | **100.00%** | **100.00%** | **100.00%** | **100.00%** | {"200":1600} |  |

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
**统一 API 入口**OpenAI-compatible 请求进入网关，保留 usage、stream 和 provider routing 参数→**路由策略层**按 throughput / price / latency / ttft 目标选择健康上游路径→**Provider Stick / Cache Affinity**重复长前缀尽量落入稳定缓存域→**上游 Provider**响应 telemetry 反馈 provider、usage、cost、latency 和 TTFT

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
| 吞吐优先 | Infron | 400 | 400 | `azure` 400 |
| 吞吐优先 | OpenRouter | 400 | 400 | `OpenAI` 400 |
| 价格优先 | Infron | 388 | 388 | `azure` 388 |
| 价格优先 | OpenRouter | 388 | 388 | `OpenAI` 258, `Azure` 130 |
| 端到端时延优先 | Infron | 396 | 396 | `azure` 396 |
| 端到端时延优先 | OpenRouter | 396 | 396 | `OpenAI` 262, `Azure` 134 |
| 流式 TTFT 优先 | Infron | 396 | 396 | `azure` 396 |
| 流式 TTFT 优先 | OpenRouter | 396 | 396 | `OpenAI` 262, `Azure` 134 |

### 上游 Provider 明细分布

| 路由模式 | 平台 | 上游 Provider | 请求数 | 占比 | first/second | 覆盖轮次 | Avg TTFT | Avg Latency | Prompt Tokens | Completion Tokens | Reasoning Tokens | Cache Read Tokens | 观测成本 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 吞吐优先 | Infron | `azure` | 400 | 100.00% | 200/200 | 200 | 2422.16 ms | 3196.16 ms | 6262580 | 23320 | 0 | 5517568 | $0.21638200 |
| 吞吐优先 | OpenRouter | `OpenAI` | 400 | 100.00% | 200/200 | 200 | 2185.01 ms | 2668.31 ms | 6262580 | 5531 | 0 | 5644288 | $0.24345791 |
| 价格优先 | Infron | `azure` | 388 | 100.00% | 194/194 | 194 | 2373.12 ms | 3161.83 ms | 5964592 | 22628 | 0 | 5648384 | $0.15337700 |
| 价格优先 | OpenRouter | `OpenAI` | 258 | 66.49% | 129/129 | 129 | 2634.74 ms | 2985.22 ms | 5734596 | 3591 | 0 | 5613056 | $0.14105787 |
| 价格优先 | OpenRouter | `Azure` | 130 | 33.51% | 65/65 | 65 | 1843.05 ms | 2240.37 ms | 229996 | 1836 | 0 | 181248 | $0.01566956 |
| 端到端时延优先 | Infron | `azure` | 396 | 100.00% | 198/198 | 198 | 2419.43 ms | 3207.86 ms | 6117118 | 23162 | 0 | 5855232 | $0.14883400 |
| 端到端时延优先 | OpenRouter | `OpenAI` | 262 | 66.16% | 131/131 | 131 | 2525.49 ms | 2893.22 ms | 5880054 | 3742 | 0 | 5684224 | $0.15752798 |
| 端到端时延优先 | OpenRouter | `Azure` | 134 | 33.84% | 67/67 | 67 | 1720.59 ms | 2080.43 ms | 237064 | 1840 | 0 | 204288 | $0.01294096 |
| 流式 TTFT 优先 | Infron | `azure` | 396 | 100.00% | 198/198 | 198 | 2498.98 ms | 3321.51 ms | 6117122 | 23186 | 0 | 5781760 | $0.15877500 |
| 流式 TTFT 优先 | OpenRouter | `OpenAI` | 262 | 66.16% | 131/131 | 131 | 2478.41 ms | 2859.22 ms | 5880058 | 3671 | 0 | 5746432 | $0.14624259 |
| 流式 TTFT 优先 | OpenRouter | `Azure` | 134 | 33.84% | 67/67 | 67 | 1789.62 ms | 2259.38 ms | 237064 | 1835 | 0 | 204288 | $0.01293471 |

### 7.1 缓存命中率与实际成本反向表现下钻

该表把 cache、cost、provider 分布和 reasoning telemetry 放在同一层级，解释每个路由模式的主要差异来源。

| 路由模式 | 缓存命中差值 | Infron 成本倍数 | Infron 主要路径 | OpenRouter 主要路径 | Reasoning Tokens 差异 | 主要归因 |
| --- | --- | --- | --- | --- | --- | --- |
| 吞吐优先 | -0.37 pp | **0.89x** | **`azure` 100.00%** | **`OpenAI` 100.00%** | +0 | 缓存和成本方向存在分化，需结合速度指标判断 |
| 价格优先 | -3.44 pp | **0.98x** | **`azure` 100.00%** | **`OpenAI` 66.49%** | +0 | 缓存和成本方向存在分化，需结合速度指标判断 |
| 端到端时延优先 | **+0.25 pp** | **0.87x** | **`azure` 100.00%** | `OpenAI` 66.16% | +0 | Infron 缓存与成本同向占优 |
| 流式 TTFT 优先 | -3.65 pp | **1.00x** | **`azure` 100.00%** | **`OpenAI` 66.16%** | +0 | 缓存和成本方向存在分化，需结合速度指标判断 |

## 8. 分层结果：按 Prompt 长度的缓存表现

本节按 prompt 长度 tier 聚合第二次请求的 cache read tokens、Token 级缓存命中率、实际成本、端到端时延和流式 TTFT。加粗单元表示同一长度 tier 下表现更优的一方。

### Prompt 长度分层总览

| Prompt 长度 tier | 目标 tokens | 平台 | 轮数 | 第二次 Prompt Tokens | 第二次 Cache Read Tokens | Token 级命中率 | 实际成本 | 平均 E2E 时延 | 平均 TTFT |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `short` | 1500 | Infron | **266** | **470594** | **393216** | **83.56%** | **$0.06510800** | 2650.17 ms | 1828.76 ms |
| `short` | 1500 | OpenRouter | **266** | **470594** | 297984 | 63.32% | $0.09124303 | **2213.67 ms** | **1779.54 ms** |
| `medium` | 8000 | Infron | **268** | **2449832** | 2302720 | 93.99% | $0.14227500 | 3086.51 ms | 2314.54 ms |
| `medium` | 8000 | OpenRouter | **268** | **2449832** | **2383360** | **97.29%** | **$0.13474755** | **2558.15 ms** | **2193.08 ms** |
| `long` | 32000 | Infron | **256** | **9310280** | 8774912 | 94.25% | **$0.46998500** | 3958.26 ms | 3171.55 ms |
| `long` | 32000 | OpenRouter | **256** | **9310280** | **9007616** | **96.75%** | $0.50384100 | **3258.96 ms** | **2837.01 ms** |

### Prompt 长度 x 路由模式缓存命中率

| Prompt 长度 tier | 路由模式 | Infron | OpenRouter | 胜出方 |
| --- | --- | --- | --- | --- |
| `short` | 吞吐优先 | **80.34%** | 0.00% | **Infron** |
| `short` | 价格优先 | **86.82%** | 81.48% | **Infron** |
| `short` | 端到端时延优先 | 81.64% | **86.82%** | **OpenRouter** |
| `short` | 流式 TTFT 优先 | **85.53%** | **85.53%** | tie |
| `medium` | 吞吐优先 | 92.17% | **96.56%** | **OpenRouter** |
| `medium` | 价格优先 | 92.17% | **98.02%** | **OpenRouter** |
| `medium` | 端到端时延优先 | 95.09% | **98.02%** | **OpenRouter** |
| `medium` | 流式 TTFT 优先 | **96.56%** | **96.56%** | tie |
| `long` | 吞吐优先 | 93.24% | **96.56%** | **OpenRouter** |
| `long` | 价格优先 | 94.61% | **97.84%** | **OpenRouter** |
| `long` | 端到端时延优先 | **96.15%** | 94.79% | **Infron** |
| `long` | 流式 TTFT 优先 | 93.05% | **97.84%** | **OpenRouter** |

## 9. 分层结果：按实验组的稳定性检查

### 吞吐优先

| 平台 | 组别 | 轮数 | 成功轮数 | Token 命中率 | 实际成本 | P95 Latency | P95 TTFT |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Infron | 1 | 50 | 50 | 83.84% | $0.09584800 | 4932.61 ms | 3955.95 ms |
| Infron | 2 | 50 | 50 | **98.38%** | **$0.03526900** | 4944.49 ms | 3919.29 ms |
| Infron | 3 | 50 | 50 | 93.82% | **$0.04386800** | 4589.81 ms | 3776.66 ms |
| Infron | 4 | 50 | 50 | **93.81%** | **$0.04139700** | 5520.54 ms | 4071.87 ms |
| OpenRouter | 1 | 50 | 50 | **94.04%** | **$0.08094779** | **4105.60 ms** | **3027.83 ms** |
| OpenRouter | 2 | 50 | 50 | 90.59% | $0.06182644 | **4411.93 ms** | **3585.49 ms** |
| OpenRouter | 3 | 50 | 50 | **94.17%** | $0.05021102 | **4227.23 ms** | **3552.50 ms** |
| OpenRouter | 4 | 50 | 50 | 92.88% | $0.05047266 | **3898.83 ms** | **2958.03 ms** |

### 价格优先

| 平台 | 组别 | 轮数 | 成功轮数 | Token 命中率 | 实际成本 | P95 Latency | P95 TTFT |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Infron | 1 | 50 | 50 | 97.35% | **$0.03795100** | 4616.45 ms | **3606.14 ms** |
| Infron | 2 | 49 | 49 | 91.49% | **$0.04011900** | 4681.38 ms | **3591.19 ms** |
| Infron | 3 | 46 | 46 | 88.99% | $0.04370300 | 4827.88 ms | 3755.10 ms |
| Infron | 4 | 49 | 49 | 97.25% | **$0.03160400** | **4473.22 ms** | **3460.36 ms** |
| OpenRouter | 1 | 50 | 50 | **97.45%** | $0.04113467 | **4252.44 ms** | 3632.78 ms |
| OpenRouter | 2 | 49 | 49 | **96.87%** | $0.04038242 | **4273.23 ms** | 3956.76 ms |
| OpenRouter | 3 | 46 | 46 | **97.26%** | **$0.03747866** | **3881.69 ms** | **3045.69 ms** |
| OpenRouter | 4 | 49 | 49 | **97.43%** | $0.03773168 | 4755.65 ms | 4033.56 ms |

### 端到端时延优先

| 平台 | 组别 | 轮数 | 成功轮数 | Token 命中率 | 实际成本 | P95 Latency | P95 TTFT |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Infron | 1 | 50 | 50 | 87.74% | $0.04320100 | 4679.88 ms | 3955.10 ms |
| Infron | 2 | 49 | 49 | **96.97%** | **$0.03291100** | 4204.07 ms | 3528.29 ms |
| Infron | 3 | 49 | 49 | **98.32%** | $0.04122100 | **4629.47 ms** | **3420.94 ms** |
| Infron | 4 | 50 | 50 | **98.51%** | **$0.03150100** | 4804.74 ms | 3981.56 ms |
| OpenRouter | 1 | 50 | 50 | **97.45%** | **$0.03949454** | **4043.33 ms** | **3374.09 ms** |
| OpenRouter | 2 | 49 | 49 | 92.82% | $0.04576162 | **3753.61 ms** | **3500.40 ms** |
| OpenRouter | 3 | 49 | 49 | 97.44% | **$0.03931312** | 4775.16 ms | 4261.07 ms |
| OpenRouter | 4 | 50 | 50 | 92.81% | $0.04589966 | **4133.43 ms** | **3240.43 ms** |

### 流式 TTFT 优先

| 平台 | 组别 | 轮数 | 成功轮数 | Token 命中率 | 实际成本 | P95 Latency | P95 TTFT |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Infron | 1 | 50 | 50 | 93.81% | **$0.03661500** | 5227.76 ms | 4093.91 ms |
| Infron | 2 | 49 | 49 | **98.54%** | **$0.03128400** | 5545.56 ms | 4657.69 ms |
| Infron | 3 | 49 | 49 | 87.61% | $0.04835800 | 4627.42 ms | **3696.16 ms** |
| Infron | 4 | 50 | 50 | 93.81% | $0.04251800 | 4737.60 ms | **3677.95 ms** |
| OpenRouter | 1 | 50 | 50 | **97.45%** | $0.03951579 | **3848.37 ms** | **3435.28 ms** |
| OpenRouter | 2 | 49 | 49 | 97.27% | $0.03954508 | **4207.71 ms** | **3590.66 ms** |
| OpenRouter | 3 | 49 | 49 | **97.44%** | **$0.03902909** | **4451.62 ms** | 3814.85 ms |
| OpenRouter | 4 | 50 | 50 | **96.28%** | **$0.04108734** | **3945.99 ms** | 3814.66 ms |

## 10. 讨论：业务价值、适用边界与工程启示

业务决策不应只看单一指标。稳定长上下文和高频模板请求优先关注缓存命中率与成本；实时交互应同时约束 TTFT 和端到端时延；后台批处理更重视吞吐与失败成本。

| 路由模式 | 主要业务目标 | 本轮数据体现 | 适用场景 | 注意事项 |
| --- | --- | --- | --- | --- |
| 吞吐优先 | 最大化单位时间输出能力 | OpenRouter 综合占优（3/5 指标） | 批量内容生成、离线摘要、后台数据加工 | 首包与完整响应更快，但需检查缓存和成本 |
| 价格优先 | 最小化单位请求和单位 token 成本 | OpenRouter 综合占优（3/5 指标） | 高频模板化请求、客服自动化、营销触达、RAG 固定前缀 | 首包与完整响应更快，但需检查缓存和成本 |
| 端到端时延优先 | 最小化完整响应等待时间 | Infron 综合占优（3/5 指标） | 在线聊天、Agent 调用链、IDE/写作辅助、实时运营工具 | 缓存和成本更稳，但仍需检查速度 SLA |
| 流式 TTFT 优先 | 最小化流式首包响应时间 | OpenRouter 综合占优（3/5 指标） | 流式聊天、实时 Copilot、首屏反馈、长任务进度感知 | 首包与完整响应更快，但需检查缓存和成本 |

## 11. 结论

### 路由模式级结论

| 路由模式 | 目标 | 缓存胜出 | 成本胜出 | 吞吐胜出 | E2E 时延胜出 | TTFT 胜出 | 解读 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 吞吐优先 | 最大化单位时间输出能力 | **OpenRouter** | **Infron** | **Infron** | **OpenRouter** | **OpenRouter** | OpenRouter 综合占优（3/5 指标） |
| 价格优先 | 最小化单位请求和单位 token 成本 | **OpenRouter** | **Infron** | **Infron** | **OpenRouter** | **OpenRouter** | OpenRouter 综合占优（3/5 指标） |
| 端到端时延优先 | 最小化完整响应等待时间 | **Infron** | **Infron** | **Infron** | **OpenRouter** | **OpenRouter** | Infron 综合占优（3/5 指标） |
| 流式 TTFT 优先 | 最小化流式首包响应时间 | **OpenRouter** | **Infron** | **Infron** | **OpenRouter** | **OpenRouter** | OpenRouter 综合占优（3/5 指标） |

## 12. 局限性、缺失数据与后续实验计划

| 缺失或不足 | 对结论的影响 | 后续补充方式 | 当前处理方式 |
| --- | --- | --- | --- |
| 完整 routing trace | 无法逐跳证明每次请求的 provider 选择、fallback 和重试路径 | 补充 provider routing trace、decision log 和 fallback reason | 只使用响应中真实返回的 provider 字段和 provider 分布 |
| 更长时间窗口 | 4x50 能观察短期稳定性，但不能覆盖日级波动 | 增加 soak test 和跨时段重复实验 | 报告限定在本轮窗口内解释 |
| 真实生产语料 | 内置模板不能覆盖全部业务分布 | 使用脱敏生产语料分层抽样 | 当前只讨论代表性长上下文业务模板 |
| 成本字段一致性 | 不同平台 cost 字段覆盖率和口径可能不同 | 结合账单回查和 provider cost breakdown | 只统计响应明确返回的成本字段 |

## 13. 可复现性附录

| 工件 | 在线链接 |
| --- | --- |
| Summary | [summary.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-5.4-nano/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/summary.json) |
| 配对数据集 | [benchmark_pairs.csv](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-5.4-nano/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/benchmark_pairs.csv) |
| 请求级数据集 | [benchmark_requests.jsonl](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-5.4-nano/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/benchmark_requests.jsonl) |
| 过滤后结构化记录 | [records.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-5.4-nano/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/records.json) |
| 剔除记录审计 | [records_excluded.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-5.4-nano/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/records_excluded.json) |
| 测试源码 | [test_rerun_routing_sort_cache_cost_ab.py](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-5.4-nano/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/code/test_rerun_routing_sort_cache_cost_ab.py) |
| Benchmark 执行源码 | [rerun_routing_sort_cache_cost_ab.py](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-5.4-nano/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/code/rerun_routing_sort_cache_cost_ab.py) |
| HTML 报告渲染源码 | [render_glm52_deepseek_style_report.py](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-5.4-nano/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/code/render_glm52_deepseek_style_report.py) |
| 数据集引用 | `business_representative` 内置代表性业务模板；请求级导出见 [benchmark_requests.jsonl](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-5.4-nano/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/benchmark_requests.jsonl) |
