# Infron 与 OpenRouter 路由、缓存、成本与流式性能 A/B 实验报告

## 摘要与结论大纲

**关键词**：Prompt Caching；A/B Testing；Provider Routing；Cache Affinity；Latency；Throughput；Cost Attribution；qwen3.6-35b-a3b

### 摘要

本报告以 `qwen/qwen3.6-35b-a3b` 为对象，评估 Infron 与 OpenRouter 在 Prompt Caching 场景下的缓存复用、实际成本、吞吐、端到端时延和流式 TTFT 表现。

核心结论是：Infron 与 OpenRouter 在所有路由模式下缓存命中率持平；Infron 在 1/4 个路由模式下实际成本占优，OpenRouter 在 3/4 个路由模式下占优，0/4 个路由模式持平；Infron 在 1/4 个路由模式下吞吐量占优，OpenRouter 在 3/4 个路由模式下占优，0/4 个路由模式持平；Infron 在所有路由模式下端到端 E2E 时延占优；Infron 在 3/4 个路由模式下流式 TTFT占优，OpenRouter 在 1/4 个路由模式下占优，0/4 个路由模式持平。

整体看，Infron 的跨模式优势主要体现在流式 TTFT、端到端 E2E 时延，OpenRouter 的跨模式优势主要体现在吞吐、实际成本。平台选择不应只看单一指标，而应按业务目标在成本、缓存稳定性、吞吐和交互时延之间取舍。


### 图 0：核心能力归一化雷达图


五个雷达轴分别代表吞吐量、价格、端到端 E2E 时延、流式 TTFT 和缓存命中率。所有指标统一转为 0-100 分，且越外侧越好。



粗实线表示平台综合轮廓，半透明细线和点表示各路由模式下的表现。


结论总览：核心指标与路由模式胜出方


基于严格 A/B 配对样本。蓝色代表 Infron，橙色代表 OpenRouter；金色单元格表示该路由模式的目标指标胜出方。


    **吞吐量**OpenRouter 3/4 胜出最大优势 59.66%, 越高越好**实际成本**OpenRouter 3/4 胜出最大优势 39.08%, 越低越好**端到端 E2E 时延**Infron 4/4 胜出最大优势 79.79%, 越低越好**流式 TTFT**Infron 3/4 胜出最大优势 40.81%, 越低越好**缓存命中率**双方 4/4 持平最大优势 0.00%, 越高越好





| 路由模式 | 吞吐目标 | 成本目标 | 时延目标 | TTFT 目标 | 缓存结果 |
| --- | --- | --- | --- | --- | --- |
| **吞吐优先**<br>throughput | OpenRouter优势 59.66% | Infron优势 39.08% | Infron优势 79.79% | OpenRouter优势 40.81% | Tie持平 |
| **价格优先**<br>price | OpenRouter优势 8.40% | OpenRouter优势 6.98% | Infron优势 14.62% | Infron优势 14.31% | Tie持平 |
| **端到端时延优先**<br>latency | OpenRouter优势 10.56% | OpenRouter优势 6.96% | Infron优势 12.78% | Infron优势 13.51% | Tie持平 |
| **流式 TTFT 优先**<br>ttft | Infron优势 3.42% | OpenRouter优势 6.96% | Infron优势 28.90% | Infron优势 25.80% | Tie持平 |

### 结论大纲

| 研究维度 | 结论 | 证据位置 |
| --- | --- | --- |
| 控制变量 | 同一 `sort/group/round` 下 first/second `usage.prompt_tokens` 偏差不超过 50 tokens；总 Input Tokens 使用响应 telemetry。 | 方法与数据质量章节 |
| 缓存复用 | Infron 与 OpenRouter 在所有路由模式下缓存命中率持平 | 总体指标与机制解释章节 |
| 实际成本 | Infron 在 1/4 个路由模式下实际成本占优，OpenRouter 在 3/4 个路由模式下占优，0/4 个路由模式持平 | 总体指标与 Provider 下钻章节 |
| 性能表现 | Infron 在 1/4 个路由模式下吞吐量占优，OpenRouter 在 3/4 个路由模式下占优，0/4 个路由模式持平；Infron 在所有路由模式下端到端 E2E 时延占优；Infron 在 3/4 个路由模式下流式 TTFT占优，OpenRouter 在 1/4 个路由模式下占优，0/4 个路由模式持平 | 结果可视化与统计检验章节 |
| 归因边界 | 报告只使用响应中可观测的 usage、cost、TTFT、latency、provider 字段和 cache tokens。 | Provider/Route 下钻分析章节 |
| 业务含义 | 长上下文、RAG 前缀、Agent 工具说明和高频模板请求应同时关注缓存命中率、成本、首包和端到端时延。 | 讨论与结论章节 |

### 路由模式级结论

| 路由模式 | 目标 | 缓存胜出 | 成本胜出 | 吞吐胜出 | E2E 时延胜出 | TTFT 胜出 | 解读 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 吞吐优先 | 最大化单位时间输出能力 | **Tie** | **Infron** | **OpenRouter** | **Infron** | **OpenRouter** | 双方各有优势 |
| 价格优先 | 最小化单位请求和单位 token 成本 | **Tie** | **OpenRouter** | **OpenRouter** | **Infron** | **Infron** | 双方各有优势 |
| 端到端时延优先 | 最小化完整响应等待时间 | **Tie** | **OpenRouter** | **OpenRouter** | **Infron** | **Infron** | 双方各有优势 |
| 流式 TTFT 优先 | 最小化流式首包响应时间 | **Tie** | **OpenRouter** | **Infron** | **Infron** | **Infron** | Infron 综合占优（3/5 指标） |

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


    **固定 Payload**模型 qwen/qwen3.6-35b-a3b，同一路由模式下 payload SHA256 固定
    →
    **请求 A1/B1**第一次请求建立或刷新缓存状态
    →
    **请求 A2/B2**第二次请求观测 cache read tokens 与 TTFT
    →
    **严格过滤**只聚合 input-token 偏差不超过 50 的 A/B pairs


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
| 模型 | `qwen/qwen3.6-35b-a3b` |
| 平台实际模型 ID | infron: `qwen/qwen3.6-35b-a3b`; openrouter: `qwen/qwen3.6-35b-a3b` |
| 平台 | Infron、OpenRouter |
| API 协议 | `/v1/chat/completions` |
| 路由模式 | 吞吐优先、价格优先、端到端时延优先、流式 TTFT 优先 |
| 实验组 | 4 |
| 每组轮数 | 50 |
| Workers | 24 |
| 请求方式 | 流式 Chat Completions，采集 TTFT |
| Reasoning / Thinking 控制 | 未显式指定 reasoning/thinking 参数；保留模型与平台默认行为 |
| Prompt 长度分层 | `short`≈1500、`medium`≈8000、`long`≈32000 |
| 剔除记录 | 44 |

## 4. 结果：总体指标与主要发现

| 路由模式 | 平台 | 严格配对轮数 | 总 Input Tokens | Token 级缓存命中率 | 实际成本 | 吞吐量 | 端到端 E2E 时延 | 流式 TTFT |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 吞吐优先 | Infron | 183 | 6518330 | **0.00%** | **$1.10165200** | 1.82 tok/s | **7012.66 ms** | 6295.91 ms |
| 吞吐优先 | OpenRouter | 183 | 6517598 | **0.00%** | $1.53220679 | **110.28 tok/s** | 12607.91 ms | **4471.16 ms** |
| 价格优先 | Infron | 198 | 6912806 | **0.00%** | $1.04198600 | 5.05 tok/s | **2550.52 ms** | **2154.21 ms** |
| 价格优先 | OpenRouter | 198 | 6912014 | **0.00%** | **$0.97401796** | **5.47 tok/s** | 2923.52 ms | 2462.44 ms |
| 端到端时延优先 | Infron | 199 | 6995010 | **0.00%** | $1.05411900 | 4.93 tok/s | **2601.72 ms** | **2207.81 ms** |
| 端到端时延优先 | OpenRouter | 199 | 6994214 | **0.00%** | **$0.98555796** | **5.45 tok/s** | 2934.25 ms | 2506.11 ms |
| 流式 TTFT 优先 | **Infron** | 198 | 7052586 | **0.00%** | $1.06273300 | **4.81 tok/s** | **2668.04 ms** | **2245.36 ms** |
| 流式 TTFT 优先 | OpenRouter | 198 | 7051794 | **0.00%** | **$0.99358716** | 4.65 tok/s | 3439.11 ms | 2824.57 ms |

### 4.1 尾延迟与显著性检验

尾延迟分位数补充均值无法表达的尾部风险。

| 路由模式 | 平台 | P50 Latency | P95 Latency | P99 Latency | P50 TTFT | P95 TTFT | P99 TTFT |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 吞吐优先 | Infron | **3225.24 ms** | 36021.12 ms | 76341.10 ms | **2607.03 ms** | 32788.62 ms | 75861.00 ms |
| 吞吐优先 | OpenRouter | 8180.42 ms | **24318.35 ms** | **69734.35 ms** | 3561.57 ms | **10965.10 ms** | **18717.57 ms** |
| 价格优先 | Infron | **2421.66 ms** | **3823.41 ms** | **5155.24 ms** | **2046.43 ms** | **3363.70 ms** | **4954.53 ms** |
| 价格优先 | OpenRouter | 2754.80 ms | 4687.15 ms | 7454.65 ms | 2264.44 ms | 3915.50 ms | 7060.60 ms |
| 端到端时延优先 | Infron | **2458.84 ms** | **4075.08 ms** | **6160.28 ms** | **2053.23 ms** | **3603.98 ms** | **5056.58 ms** |
| 端到端时延优先 | OpenRouter | 2650.83 ms | 4688.94 ms | 6982.76 ms | 2268.77 ms | 3874.55 ms | 5812.22 ms |
| 流式 TTFT 优先 | **Infron** | **2508.98 ms** | **4255.28 ms** | **5551.96 ms** | **2132.70 ms** | **3484.38 ms** | **4838.64 ms** |
| 流式 TTFT 优先 | OpenRouter | 2985.83 ms | 6412.05 ms | 10396.74 ms | 2486.73 ms | 5304.79 ms | 8646.82 ms |

均值差使用 bootstrap 95% CI，p-value 使用 paired sign-flip permutation test。

| 路由模式 | 指标 | 均值差 | 95% CI | p-value | 配对数 | 解释 |
| --- | --- | --- | --- | --- | --- | --- |
| 吞吐优先 | Latency: OpenRouter - Infron | **11190.50 ms** | 5095.00 ms to 18202.66 ms | <0.001 | 183 | 正值表示 Infron latency 更低 |
| 吞吐优先 | TTFT: OpenRouter - Infron | **-3649.50 ms** | -6439.99 ms to -1011.78 ms | 0.0130 | 183 | 正值表示 Infron TTFT 更低 |
| 吞吐优先 | Throughput: Infron - OpenRouter | **-61.3866 tok/s** | -69.0973 tok/s to -54.0288 tok/s | <0.001 | 183 | 正值表示 Infron throughput 更高 |
| 吞吐优先 | Cost: OpenRouter - Infron | **$0.00235276** | $0.00104649 to $0.00405145 | <0.001 | 183 | 正值表示 Infron 成本更低 |
| 吞吐优先 | Token Cache Hit: Infron - OpenRouter | 0.00 pp | 0.00 pp to 0.00 pp | 1.0000 | 183 | 正值表示 Infron cache hit 更高 |
| 价格优先 | Latency: OpenRouter - Infron | **745.99 ms** | 509.43 ms to 980.71 ms | <0.001 | 198 | 正值表示 Infron latency 更低 |
| 价格优先 | TTFT: OpenRouter - Infron | **616.47 ms** | 407.90 ms to 827.36 ms | <0.001 | 198 | 正值表示 Infron TTFT 更低 |
| 价格优先 | Throughput: Infron - OpenRouter | **-0.6455 tok/s** | -0.9905 tok/s to -0.2833 tok/s | <0.001 | 198 | 正值表示 Infron throughput 更高 |
| 价格优先 | Cost: OpenRouter - Infron | **$-0.00034327** | $-0.00038772 to $-0.00029569 | <0.001 | 198 | 正值表示 Infron 成本更低 |
| 价格优先 | Token Cache Hit: Infron - OpenRouter | 0.00 pp | 0.00 pp to 0.00 pp | 1.0000 | 198 | 正值表示 Infron cache hit 更高 |
| 端到端时延优先 | Latency: OpenRouter - Infron | **665.05 ms** | 286.41 ms to 1140.86 ms | <0.001 | 199 | 正值表示 Infron latency 更低 |
| 端到端时延优先 | TTFT: OpenRouter - Infron | **596.61 ms** | 242.28 ms to 1040.33 ms | <0.001 | 199 | 正值表示 Infron TTFT 更低 |
| 端到端时延优先 | Throughput: Infron - OpenRouter | **-0.8180 tok/s** | -1.1561 tok/s to -0.4885 tok/s | <0.001 | 199 | 正值表示 Infron throughput 更高 |
| 端到端时延优先 | Cost: OpenRouter - Infron | **$-0.00034453** | $-0.00039038 to $-0.00029616 | <0.001 | 199 | 正值表示 Infron 成本更低 |
| 端到端时延优先 | Token Cache Hit: Infron - OpenRouter | 0.00 pp | 0.00 pp to 0.00 pp | 1.0000 | 199 | 正值表示 Infron cache hit 更高 |
| 流式 TTFT 优先 | Latency: OpenRouter - Infron | **1542.14 ms** | 999.45 ms to 2239.81 ms | <0.001 | 198 | 正值表示 Infron latency 更低 |
| 流式 TTFT 优先 | TTFT: OpenRouter - Infron | **1158.43 ms** | 687.84 ms to 1810.62 ms | <0.001 | 198 | 正值表示 Infron TTFT 更低 |
| 流式 TTFT 优先 | Throughput: Infron - OpenRouter | **-0.2542 tok/s** | -0.6401 tok/s to 0.1419 tok/s | 0.1987 | 198 | 正值表示 Infron throughput 更高 |
| 流式 TTFT 优先 | Cost: OpenRouter - Infron | **$-0.00034922** | $-0.00039530 to $-0.00030316 | <0.001 | 198 | 正值表示 Infron 成本更低 |
| 流式 TTFT 优先 | Token Cache Hit: Infron - OpenRouter | 0.00 pp | 0.00 pp to 0.00 pp | 1.0000 | 198 | 正值表示 Infron cache hit 更高 |

### 4.2 Reasoning / Thinking 控制校验

本轮未显式指定 reasoning/thinking 参数，保留模型与平台默认行为；该表记录默认行为下的 reasoning telemetry。

| 路由模式 | 平台 | Reasoning Tokens | 平均 Reasoning Tokens/请求 | Reasoning 请求数 | 平均首 Reasoning Token | 平均 TTFT | 平均 E2E 时延 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 吞吐优先 | Infron | **0** | **0.0000** | **0** | **0.00 ms** | 6295.91 ms | **7012.66 ms** |
| 吞吐优先 | OpenRouter | 497478 | 1359.2295 | 366 | 4471.16 ms | **4471.16 ms** | 12607.91 ms |
| 价格优先 | Infron | **0** | **0.0000** | **0** | **0.00 ms** | **2154.21 ms** | **2550.52 ms** |
| 价格优先 | OpenRouter | 6508 | 16.4343 | 396 | 2462.44 ms | 2462.44 ms | 2923.52 ms |
| 端到端时延优先 | Infron | **0** | **0.0000** | **0** | **0.00 ms** | **2207.81 ms** | **2601.72 ms** |
| 端到端时延优先 | OpenRouter | 6625 | 16.6457 | 398 | 2506.11 ms | 2506.11 ms | 2934.25 ms |
| 流式 TTFT 优先 | **Infron** | **0** | **0.0000** | **0** | **0.00 ms** | **2245.36 ms** | **2668.04 ms** |
| 流式 TTFT 优先 | OpenRouter | 6492 | 16.3939 | 396 | 2824.57 ms | 2824.57 ms | 3439.11 ms |

### 4.3 API 协议兼容性矩阵

本轮 API 协议为 `/v1/chat/completions`；本表记录两家平台在该协议下的成功响应、usage、成本和缓存 telemetry 覆盖。

| API 协议 | Endpoint | 平台 | 配对轮数 | 请求数 | 成功率 | Usage 覆盖 | Token Usage 覆盖 | 成本覆盖 | 缓存 Telemetry 覆盖 | HTTP 状态 | 主要错误 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `chat_completions` | `/v1/chat/completions` | Infron | 800 | 1600 | **99.81%** | **100.00%** | **100.00%** | **100.00%** | **100.00%** | {"0":3,"200":1597} | 3 x Remote end closed connection without response |
| `chat_completions` | `/v1/chat/completions` | OpenRouter | 800 | 1600 | 98.81% | **100.00%** | **100.00%** | **100.00%** | **100.00%** | {"0":19,"200":1581} | 10 x Remote end closed connection without response<br>6 x [SYS] unknown error (_ssl.c:2406) |

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


    **统一 API 入口**OpenAI-compatible 请求进入网关，保留 usage、stream 和 provider routing 参数
    →
    **路由策略层**按 throughput / price / latency / ttft 目标选择健康上游路径
    →
    **Provider Stick / Cache Affinity**重复长前缀尽量落入稳定缓存域
    →
    **上游 Provider**响应 telemetry 反馈 provider、usage、cost、latency 和 TTFT


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
| 吞吐优先 | Infron | 366 | 366 | `deepinfra` 250, `wafer` 69, `alibaba/cn` 47 |
| 吞吐优先 | OpenRouter | 366 | 366 | `AtlasCloud` 333, `AkashML` 33 |
| 价格优先 | Infron | 396 | 396 | `deepinfra` 395, `alibaba/cn` 1 |
| 价格优先 | OpenRouter | 396 | 396 | `AkashML` 396 |
| 端到端时延优先 | Infron | 398 | 398 | `deepinfra` 398 |
| 端到端时延优先 | OpenRouter | 398 | 398 | `AkashML` 398 |
| 流式 TTFT 优先 | Infron | 396 | 396 | `deepinfra` 396 |
| 流式 TTFT 优先 | OpenRouter | 396 | 396 | `AkashML` 396 |

### 上游 Provider 明细分布

| 路由模式 | 平台 | 上游 Provider | 请求数 | 占比 | first/second | 覆盖轮次 | Avg TTFT | Avg Latency | Prompt Tokens | Completion Tokens | Reasoning Tokens | Cache Read Tokens | 观测成本 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 吞吐优先 | Infron | `deepinfra` | 250 | 68.31% | 120/130 | 130 | 2681.55 ms | 3414.00 ms | 4568041 | 3202 | 0 | 0 | $0.68825800 |
| 吞吐优先 | Infron | `wafer` | 69 | 18.85% | 32/37 | 41 | 3479.64 ms | 3834.30 ms | 1245543 | 894 | 0 | 0 | $0.23777200 |
| 吞吐优先 | Infron | `alibaba/cn` | 47 | 12.84% | 31/16 | 31 | 29655.76 ms | 30820.56 ms | 704746 | 570 | 0 | 0 | $0.17562200 |
| 吞吐优先 | OpenRouter | `AtlasCloud` | 333 | 90.98% | 166/167 | 174 | 4507.65 ms | 13411.27 ms | 6061381 | 508380 | 496950 | 0 | $1.46780841 |
| 吞吐优先 | OpenRouter | `AkashML` | 33 | 9.02% | 17/16 | 24 | 4102.93 ms | 4501.19 ms | 456217 | 528 | 528 | 0 | $0.06439838 |
| 价格优先 | Infron | `deepinfra` | 395 | 99.75% | 198/197 | 198 | 2133.21 ms | 2529.38 ms | 6910808 | 5084 | 0 | 0 | $1.04146700 |
| 价格优先 | Infron | `alibaba/cn` | 1 | 0.25% | 0/1 | 1 | 10447.95 ms | 10900.24 ms | 1998 | 16 | 0 | 0 | $0.00051900 |
| 价格优先 | OpenRouter | `AkashML` | 396 | 100.00% | 198/198 | 198 | 2462.44 ms | 2923.52 ms | 6912014 | 6336 | 6508 | 0 | $0.97401796 |
| 端到端时延优先 | Infron | `deepinfra` | 398 | 100.00% | 199/199 | 199 | 2207.81 ms | 2601.72 ms | 6995010 | 5107 | 0 | 0 | $1.05411900 |
| 端到端时延优先 | OpenRouter | `AkashML` | 398 | 100.00% | 199/199 | 199 | 2506.11 ms | 2934.25 ms | 6994214 | 6368 | 6625 | 0 | $0.98555796 |
| 流式 TTFT 优先 | Infron | `deepinfra` | 396 | 100.00% | 198/198 | 198 | 2245.36 ms | 2668.04 ms | 7052586 | 5083 | 0 | 0 | $1.06273300 |
| 流式 TTFT 优先 | OpenRouter | `AkashML` | 396 | 100.00% | 198/198 | 198 | 2824.57 ms | 3439.11 ms | 7051794 | 6336 | 6492 | 0 | $0.99358716 |

### 7.1 缓存命中率与实际成本反向表现下钻

该表把 cache、cost、provider 分布和 reasoning telemetry 放在同一层级，解释每个路由模式的主要差异来源。

| 路由模式 | 缓存命中差值 | Infron 成本倍数 | Infron 主要路径 | OpenRouter 主要路径 | Reasoning Tokens 差异 | 主要归因 |
| --- | --- | --- | --- | --- | --- | --- |
| 吞吐优先 | +0.00 pp | **0.72x** | **`deepinfra` 68.31%** | `AtlasCloud` 90.98% | **-497478** | 双方缓存持平，Infron 成本占优 |
| 价格优先 | +0.00 pp | 1.07x | `deepinfra` 99.75% | **`AkashML` 100.00%** | **-6508** | Infron 缓存更高但成本更高，需检查上游单价、completion/reasoning tokens |
| 端到端时延优先 | +0.00 pp | 1.07x | `deepinfra` 100.00% | **`AkashML` 100.00%** | **-6625** | Infron 缓存更高但成本更高，需检查上游单价、completion/reasoning tokens |
| 流式 TTFT 优先 | +0.00 pp | 1.07x | `deepinfra` 100.00% | **`AkashML` 100.00%** | **-6492** | Infron 缓存更高但成本更高，需检查上游单价、completion/reasoning tokens |

## 8. 分层结果：按 Prompt 长度的缓存表现

本节按 prompt 长度 tier 聚合第二次请求的 cache read tokens、Token 级缓存命中率、实际成本、端到端时延和流式 TTFT。加粗单元表示同一长度 tier 下表现更优的一方。

### Prompt 长度分层总览

| Prompt 长度 tier | 目标 tokens | 平台 | 轮数 | 第二次 Prompt Tokens | 第二次 Cache Read Tokens | Token 级命中率 | 实际成本 | 平均 E2E 时延 | 平均 TTFT |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `short` | 1500 | Infron | **261** | **520226** | **0** | **0.00%** | **$0.16818700** | **2626.43 ms** | 2150.90 ms |
| `short` | 1500 | OpenRouter | **261** | 519704 | **0** | **0.00%** | $0.23414636 | 4128.76 ms | **2135.23 ms** |
| `medium` | 8000 | Infron | **261** | **2695686** | **0** | **0.00%** | **$0.84264700** | **3585.30 ms** | 3134.25 ms |
| `medium` | 8000 | OpenRouter | **261** | 2695164 | **0** | **0.00%** | $0.86707414 | 4570.77 ms | **2867.67 ms** |
| `long` | 32000 | Infron | **256** | **10523454** | **0** | **0.00%** | **$3.24965600** | **4738.56 ms** | 4231.23 ms |
| `long` | 32000 | OpenRouter | **256** | 10522942 | **0** | **0.00%** | $3.38414936 | 7345.25 ms | **4132.85 ms** |

### Prompt 长度 x 路由模式缓存命中率

| Prompt 长度 tier | 路由模式 | Infron | OpenRouter | 胜出方 |
| --- | --- | --- | --- | --- |
| `short` | 吞吐优先 | **0.00%** | **0.00%** | tie |
| `short` | 价格优先 | **0.00%** | **0.00%** | tie |
| `short` | 端到端时延优先 | **0.00%** | **0.00%** | tie |
| `short` | 流式 TTFT 优先 | **0.00%** | **0.00%** | tie |
| `medium` | 吞吐优先 | **0.00%** | **0.00%** | tie |
| `medium` | 价格优先 | **0.00%** | **0.00%** | tie |
| `medium` | 端到端时延优先 | **0.00%** | **0.00%** | tie |
| `medium` | 流式 TTFT 优先 | **0.00%** | **0.00%** | tie |
| `long` | 吞吐优先 | **0.00%** | **0.00%** | tie |
| `long` | 价格优先 | **0.00%** | **0.00%** | tie |
| `long` | 端到端时延优先 | **0.00%** | **0.00%** | tie |
| `long` | 流式 TTFT 优先 | **0.00%** | **0.00%** | tie |

## 9. 分层结果：按实验组的稳定性检查

### 吞吐优先

| 平台 | 组别 | 轮数 | 成功轮数 | Token 命中率 | 实际成本 | P95 Latency | P95 TTFT |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Infron | 1 | 47 | 47 | **0.00%** | $0.35669800 | 73376.27 ms | 72495.67 ms |
| Infron | 2 | 40 | 40 | **0.00%** | **$0.24394300** | **6182.79 ms** | **5152.62 ms** |
| Infron | 3 | 47 | 47 | **0.00%** | **$0.25199500** | **4571.83 ms** | **3892.25 ms** |
| Infron | 4 | 49 | 49 | **0.00%** | **$0.24901600** | **8015.77 ms** | **7220.52 ms** |
| OpenRouter | 1 | 47 | 47 | **0.00%** | **$0.35412248** | **22642.47 ms** | **6602.13 ms** |
| OpenRouter | 2 | 40 | 40 | **0.00%** | $0.37283790 | 49693.37 ms | 15145.92 ms |
| OpenRouter | 3 | 47 | 47 | **0.00%** | $0.39045837 | 23305.84 ms | 14300.73 ms |
| OpenRouter | 4 | 49 | 49 | **0.00%** | $0.41478804 | 21569.67 ms | 8358.01 ms |

### 价格优先

| 平台 | 组别 | 轮数 | 成功轮数 | Token 命中率 | 实际成本 | P95 Latency | P95 TTFT |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Infron | 1 | 50 | 50 | **0.00%** | $0.26138200 | **4012.04 ms** | **3623.15 ms** |
| Infron | 2 | 49 | 49 | **0.00%** | $0.26077100 | **3735.29 ms** | **3180.65 ms** |
| Infron | 3 | 49 | 49 | **0.00%** | $0.25824800 | **3307.70 ms** | **3015.72 ms** |
| Infron | 4 | 50 | 50 | **0.00%** | $0.26158500 | **4484.52 ms** | **3658.20 ms** |
| OpenRouter | 1 | 50 | 50 | **0.00%** | **$0.24438268** | 4842.60 ms | 3906.73 ms |
| OpenRouter | 2 | 49 | 49 | **0.00%** | **$0.24379264** | 5080.44 ms | 3800.59 ms |
| OpenRouter | 3 | 49 | 49 | **0.00%** | **$0.24145996** | 4072.86 ms | 3655.39 ms |
| OpenRouter | 4 | 50 | 50 | **0.00%** | **$0.24438268** | 4691.89 ms | 4065.72 ms |

### 端到端时延优先

| 平台 | 组别 | 轮数 | 成功轮数 | Token 命中率 | 实际成本 | P95 Latency | P95 TTFT |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Infron | 1 | 50 | 50 | **0.00%** | $0.26137700 | **3842.13 ms** | **3463.32 ms** |
| Infron | 2 | 50 | 50 | **0.00%** | $0.27311400 | **3785.03 ms** | **3108.52 ms** |
| Infron | 3 | 49 | 49 | **0.00%** | $0.25824800 | 4396.24 ms | 3999.43 ms |
| Infron | 4 | 50 | 50 | **0.00%** | $0.26138000 | **4441.58 ms** | **4002.67 ms** |
| OpenRouter | 1 | 50 | 50 | **0.00%** | **$0.24438268** | 3945.06 ms | 3576.85 ms |
| OpenRouter | 2 | 50 | 50 | **0.00%** | **$0.25533460** | 5305.07 ms | 4201.66 ms |
| OpenRouter | 3 | 49 | 49 | **0.00%** | **$0.24145800** | **4291.32 ms** | **3744.03 ms** |
| OpenRouter | 4 | 50 | 50 | **0.00%** | **$0.24438268** | 4492.70 ms | 4136.66 ms |

### 流式 TTFT 优先

| 平台 | 组别 | 轮数 | 成功轮数 | Token 命中率 | 实际成本 | P95 Latency | P95 TTFT |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Infron | 1 | 50 | 50 | **0.00%** | $0.26138100 | **4463.60 ms** | **3702.31 ms** |
| Infron | 2 | 49 | 49 | **0.00%** | $0.26998800 | **3683.86 ms** | **3276.06 ms** |
| Infron | 3 | 49 | 49 | **0.00%** | $0.26998300 | **4366.89 ms** | **3803.62 ms** |
| Infron | 4 | 50 | 50 | **0.00%** | $0.26138100 | **4235.40 ms** | **3382.72 ms** |
| OpenRouter | 1 | 50 | 50 | **0.00%** | **$0.24438268** | 6985.50 ms | 5304.65 ms |
| OpenRouter | 2 | 49 | 49 | **0.00%** | **$0.25241188** | 5527.35 ms | 4761.40 ms |
| OpenRouter | 3 | 49 | 49 | **0.00%** | **$0.25240992** | 5720.04 ms | 4630.07 ms |
| OpenRouter | 4 | 50 | 50 | **0.00%** | **$0.24438268** | 6419.30 ms | 4805.62 ms |

## 10. 讨论：业务价值、适用边界与工程启示

业务决策不应只看单一指标。稳定长上下文和高频模板请求优先关注缓存命中率与成本；实时交互应同时约束 TTFT 和端到端时延；后台批处理更重视吞吐与失败成本。

| 路由模式 | 主要业务目标 | 本轮数据体现 | 适用场景 | 注意事项 |
| --- | --- | --- | --- | --- |
| 吞吐优先 | 最大化单位时间输出能力 | 双方各有优势 | 批量内容生成、离线摘要、后台数据加工 | 适合吞吐优先任务，但成本和缓存需单独约束 |
| 价格优先 | 最小化单位请求和单位 token 成本 | 双方各有优势 | 高频模板化请求、客服自动化、营销触达、RAG 固定前缀 | 适合吞吐优先任务，但成本和缓存需单独约束 |
| 端到端时延优先 | 最小化完整响应等待时间 | 双方各有优势 | 在线聊天、Agent 调用链、IDE/写作辅助、实时运营工具 | 适合吞吐优先任务，但成本和缓存需单独约束 |
| 流式 TTFT 优先 | 最小化流式首包响应时间 | Infron 综合占优（3/5 指标） | 流式聊天、实时 Copilot、首屏反馈、长任务进度感知 | 需要结合预算、SLA 和缓存稳定性决策 |

## 11. 结论

### 路由模式级结论

| 路由模式 | 目标 | 缓存胜出 | 成本胜出 | 吞吐胜出 | E2E 时延胜出 | TTFT 胜出 | 解读 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 吞吐优先 | 最大化单位时间输出能力 | **Tie** | **Infron** | **OpenRouter** | **Infron** | **OpenRouter** | 双方各有优势 |
| 价格优先 | 最小化单位请求和单位 token 成本 | **Tie** | **OpenRouter** | **OpenRouter** | **Infron** | **Infron** | 双方各有优势 |
| 端到端时延优先 | 最小化完整响应等待时间 | **Tie** | **OpenRouter** | **OpenRouter** | **Infron** | **Infron** | 双方各有优势 |
| 流式 TTFT 优先 | 最小化流式首包响应时间 | **Tie** | **OpenRouter** | **Infron** | **Infron** | **Infron** | Infron 综合占优（3/5 指标） |

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
| Summary | [summary.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.6-35b-a3b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/summary.json) |
| 配对数据集 | [benchmark_pairs.csv](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.6-35b-a3b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/benchmark_pairs.csv) |
| 请求级数据集 | [benchmark_requests.jsonl](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.6-35b-a3b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/benchmark_requests.jsonl) |
| 过滤后结构化记录 | [records.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.6-35b-a3b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/records.json) |
| 剔除记录审计 | [records_excluded.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.6-35b-a3b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/records_excluded.json) |
| 测试源码 | [test_rerun_routing_sort_cache_cost_ab.py](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.6-35b-a3b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/code/test_rerun_routing_sort_cache_cost_ab.py) |
| Benchmark 执行源码 | [rerun_routing_sort_cache_cost_ab.py](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.6-35b-a3b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/code/rerun_routing_sort_cache_cost_ab.py) |
| HTML 报告渲染源码 | [render_glm52_deepseek_style_report.py](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.6-35b-a3b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/code/render_glm52_deepseek_style_report.py) |
| 数据集引用 | `business_representative` 内置代表性业务模板；请求级导出见 [benchmark_requests.jsonl](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.6-35b-a3b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/benchmark_requests.jsonl) |
