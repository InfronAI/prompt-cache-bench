# Infron 与 OpenRouter 路由、缓存、成本与流式性能 A/B 实验报告

## 摘要与结论大纲

**关键词**：Prompt Caching；A/B Testing；Provider Routing；Cache Affinity；Latency；Throughput；Cost Attribution；glm-5

### 摘要

本报告以 `z-ai/glm-5` 为对象，评估 Infron 与 OpenRouter 在 Prompt Caching 场景下的缓存复用、实际成本、吞吐、端到端时延和流式 TTFT 表现。

核心结论是：Infron 在 1/4 个路由模式下缓存命中率占优，OpenRouter 在 3/4 个路由模式下占优，0/4 个路由模式持平；Infron 在 2/4 个路由模式下实际成本占优，OpenRouter 在 2/4 个路由模式下占优，0/4 个路由模式持平；OpenRouter 在所有路由模式下吞吐量占优；Infron 在 3/4 个路由模式下端到端 E2E 时延占优，OpenRouter 在 1/4 个路由模式下占优，0/4 个路由模式持平；Infron 在 3/4 个路由模式下流式 TTFT占优，OpenRouter 在 1/4 个路由模式下占优，0/4 个路由模式持平。

整体看，Infron 的跨模式优势主要体现在流式 TTFT、端到端 E2E 时延，OpenRouter 的跨模式优势主要体现在吞吐、缓存复用。平台选择不应只看单一指标，而应按业务目标在成本、缓存稳定性、吞吐和交互时延之间取舍。

### 图 0：核心能力归一化雷达图

五个雷达轴分别代表吞吐量、价格、端到端 E2E 时延、流式 TTFT 和缓存命中率。所有指标统一转为 0-100 分，且越外侧越好。

粗实线表示平台综合轮廓，半透明细线和点表示各路由模式下的表现。

结论总览：核心指标与路由模式胜出方

基于严格 A/B 配对样本。蓝色代表 Infron，橙色代表 OpenRouter；金色单元格表示该路由模式的目标指标胜出方。

    **吞吐量**OpenRouter 4/4 胜出最大优势 104.15%, 越高越好**实际成本**Infron 2/4 胜出最大优势 62.64%, 越低越好**端到端 E2E 时延**Infron 3/4 胜出最大优势 64.76%, 越低越好**流式 TTFT**Infron 3/4 胜出最大优势 47.57%, 越低越好**缓存命中率**OpenRouter 3/4 胜出最大优势 4.00%, 越高越好

| 路由模式 | 吞吐目标 | 成本目标 | 时延目标 | TTFT 目标 | 缓存结果 |
| --- | --- | --- | --- | --- | --- |
| **吞吐优先**<br>throughput | OpenRouter优势 7.85% | OpenRouter优势 62.64% | Infron优势 10.78% | Infron优势 12.55% | Infron优势 1.72% |
| **价格优先**<br>price | OpenRouter优势 104.15% | OpenRouter优势 20.72% | OpenRouter优势 64.76% | OpenRouter优势 47.57% | OpenRouter优势 4.00% |
| **端到端时延优先**<br>latency | OpenRouter优势 19.66% | Infron优势 7.35% | Infron优势 3.14% | Infron优势 33.16% | OpenRouter优势 0.23% |
| **流式 TTFT 优先**<br>ttft | OpenRouter优势 9.81% | Infron优势 2.54% | Infron优势 12.04% | Infron优势 39.74% | OpenRouter优势 0.27% |

### 结论大纲

| 研究维度 | 结论 | 证据位置 |
| --- | --- | --- |
| 控制变量 | 同一 `sort/group/round` 下 first/second `usage.prompt_tokens` 偏差不超过 50 tokens；总 Input Tokens 使用响应 telemetry。 | 方法与数据质量章节 |
| 缓存复用 | Infron 在 1/4 个路由模式下缓存命中率占优，OpenRouter 在 3/4 个路由模式下占优，0/4 个路由模式持平 | 总体指标与机制解释章节 |
| 实际成本 | Infron 在 2/4 个路由模式下实际成本占优，OpenRouter 在 2/4 个路由模式下占优，0/4 个路由模式持平 | 总体指标与 Provider 下钻章节 |
| 性能表现 | OpenRouter 在所有路由模式下吞吐量占优；Infron 在 3/4 个路由模式下端到端 E2E 时延占优，OpenRouter 在 1/4 个路由模式下占优，0/4 个路由模式持平；Infron 在 3/4 个路由模式下流式 TTFT占优，OpenRouter 在 1/4 个路由模式下占优，0/4 个路由模式持平 | 结果可视化与统计检验章节 |
| 归因边界 | 报告只使用响应中可观测的 usage、cost、TTFT、latency、provider 字段和 cache tokens。 | Provider/Route 下钻分析章节 |
| 业务含义 | 长上下文、RAG 前缀、Agent 工具说明和高频模板请求应同时关注缓存命中率、成本、首包和端到端时延。 | 讨论与结论章节 |

### 路由模式级结论

| 路由模式 | 目标 | 缓存胜出 | 成本胜出 | 吞吐胜出 | E2E 时延胜出 | TTFT 胜出 | 解读 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 吞吐优先 | 最大化单位时间输出能力 | **Infron** | **OpenRouter** | **OpenRouter** | **Infron** | **Infron** | Infron 综合占优（3/5 指标） |
| 价格优先 | 最小化单位请求和单位 token 成本 | **OpenRouter** | **OpenRouter** | **OpenRouter** | **OpenRouter** | **OpenRouter** | OpenRouter 综合占优（5/5 指标） |
| 端到端时延优先 | 最小化完整响应等待时间 | **OpenRouter** | **Infron** | **OpenRouter** | **Infron** | **Infron** | Infron 综合占优（3/5 指标） |
| 流式 TTFT 优先 | 最小化流式首包响应时间 | **OpenRouter** | **Infron** | **OpenRouter** | **Infron** | **Infron** | Infron 综合占优（3/5 指标） |

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

    **固定 Payload**模型 z-ai/glm-5，同一路由模式下 payload SHA256 固定
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
| 模型 | `z-ai/glm-5` |
| 平台实际模型 ID | infron: `z-ai/glm-5`; openrouter: `z-ai/glm-5` |
| 平台 | Infron、OpenRouter |
| API 协议 | `/v1/chat/completions` |
| 路由模式 | 吞吐优先、价格优先、端到端时延优先、流式 TTFT 优先 |
| 实验组 | 4 |
| 每组轮数 | 50 |
| Workers | 24 |
| 请求方式 | 流式 Chat Completions，采集 TTFT |
| Reasoning / Thinking 控制 | 未显式指定 reasoning/thinking 参数；保留模型与平台默认行为 |
| Prompt 长度分层 | `short`≈1500、`medium`≈8000、`long`≈32000 |
| 剔除记录 | 24 |

## 4. 结果：总体指标与主要发现

| 路由模式 | 平台 | 严格配对轮数 | 总 Input Tokens | Token 级缓存命中率 | 实际成本 | 吞吐量 | 端到端 E2E 时延 | 流式 TTFT |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 吞吐优先 | **Infron** | 200 | 6414682 | **99.79%** | $1.61315300 | 2.52 tok/s | **5311.71 ms** | **4992.94 ms** |
| 吞吐优先 | OpenRouter | 200 | 6414682 | 98.10% | **$0.99183578** | **2.72 tok/s** | 5884.51 ms | 5619.75 ms |
| 价格优先 | Infron | 195 | 6040276 | 95.70% | $0.99697000 | 1.52 tok/s | 8506.60 ms | 7224.73 ms |
| 价格优先 | **OpenRouter** | 195 | 6040283 | **99.53%** | **$0.82584095** | **3.10 tok/s** | **5163.02 ms** | **4895.85 ms** |
| 端到端时延优先 | **Infron** | 193 | 6273860 | 99.61% | **$0.77495600** | 2.61 tok/s | **4966.67 ms** | **3645.69 ms** |
| 端到端时延优先 | OpenRouter | 193 | 6273860 | **99.84%** | $0.83192194 | **3.12 tok/s** | 5122.85 ms | 4854.43 ms |
| 流式 TTFT 优先 | **Infron** | 200 | 6414682 | 99.56% | **$0.84264400** | 2.73 tok/s | **4758.14 ms** | **3596.32 ms** |
| 流式 TTFT 优先 | OpenRouter | 200 | 6414682 | **99.83%** | $0.86408455 | **3.00 tok/s** | 5331.20 ms | 5025.52 ms |

### 4.1 尾延迟与显著性检验

尾延迟分位数补充均值无法表达的尾部风险。

| 路由模式 | 平台 | P50 Latency | P95 Latency | P99 Latency | P50 TTFT | P95 TTFT | P99 TTFT |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 吞吐优先 | **Infron** | **5019.43 ms** | **8949.33 ms** | **11000.97 ms** | **4695.00 ms** | **8587.00 ms** | **10897.81 ms** |
| 吞吐优先 | OpenRouter | 5511.87 ms | 9758.45 ms | 12789.27 ms | 5324.60 ms | 9432.64 ms | 12480.67 ms |
| 价格优先 | Infron | **4307.77 ms** | 31280.13 ms | 93253.06 ms | **3325.72 ms** | 22342.13 ms | 92413.82 ms |
| 价格优先 | **OpenRouter** | 5101.24 ms | **7374.62 ms** | **8385.21 ms** | 4839.13 ms | **7071.70 ms** | **7957.55 ms** |
| 端到端时延优先 | **Infron** | **4716.31 ms** | 7963.46 ms | 9700.74 ms | **3452.01 ms** | **6130.44 ms** | **8077.04 ms** |
| 端到端时延优先 | OpenRouter | 5123.94 ms | **7437.43 ms** | **8328.80 ms** | 4865.67 ms | 7124.79 ms | 8211.71 ms |
| 流式 TTFT 优先 | **Infron** | **4371.01 ms** | **7859.70 ms** | 9668.50 ms | **3308.84 ms** | **6277.24 ms** | **8130.10 ms** |
| 流式 TTFT 优先 | OpenRouter | 5290.40 ms | 7983.31 ms | **8954.58 ms** | 5070.78 ms | 7718.23 ms | 8577.17 ms |

均值差使用 bootstrap 95% CI，p-value 使用 paired sign-flip permutation test。

| 路由模式 | 指标 | 均值差 | 95% CI | p-value | 配对数 | 解释 |
| --- | --- | --- | --- | --- | --- | --- |
| 吞吐优先 | Latency: OpenRouter - Infron | **1145.60 ms** | 725.46 ms to 1593.91 ms | <0.001 | 200 | 正值表示 Infron latency 更低 |
| 吞吐优先 | TTFT: OpenRouter - Infron | **1253.63 ms** | 821.31 ms to 1704.47 ms | <0.001 | 200 | 正值表示 Infron TTFT 更低 |
| 吞吐优先 | Throughput: Infron - OpenRouter | **-0.1442 tok/s** | -0.3115 tok/s to 0.0211 tok/s | 0.0855 | 200 | 正值表示 Infron throughput 更高 |
| 吞吐优先 | Cost: OpenRouter - Infron | **$-0.00310659** | $-0.00390526 to $-0.00242740 | <0.001 | 200 | 正值表示 Infron 成本更低 |
| 吞吐优先 | Token Cache Hit: Infron - OpenRouter | **1.01 pp** | -0.97 pp to 3.01 pp | 0.2524 | 200 | 正值表示 Infron cache hit 更高 |
| 价格优先 | Latency: OpenRouter - Infron | **-6687.16 ms** | -10536.36 ms to -3483.40 ms | <0.001 | 195 | 正值表示 Infron latency 更低 |
| 价格优先 | TTFT: OpenRouter - Infron | **-4657.75 ms** | -8398.45 ms to -1592.26 ms | 0.0065 | 195 | 正值表示 Infron TTFT 更低 |
| 价格优先 | Throughput: Infron - OpenRouter | **-0.6011 tok/s** | -0.8364 tok/s to -0.3715 tok/s | <0.001 | 195 | 正值表示 Infron throughput 更高 |
| 价格优先 | Cost: OpenRouter - Infron | **$-0.00087758** | $-0.00153961 to $-0.00029056 | 0.0052 | 195 | 正值表示 Infron 成本更低 |
| 价格优先 | Token Cache Hit: Infron - OpenRouter | **-4.48 pp** | -7.99 pp to -1.34 pp | 0.0105 | 195 | 正值表示 Infron cache hit 更高 |
| 端到端时延优先 | Latency: OpenRouter - Infron | **312.37 ms** | -91.12 ms to 681.67 ms | 0.1197 | 193 | 正值表示 Infron latency 更低 |
| 端到端时延优先 | TTFT: OpenRouter - Infron | **2417.48 ms** | 2093.52 ms to 2728.71 ms | <0.001 | 193 | 正值表示 Infron TTFT 更低 |
| 端到端时延优先 | Throughput: Infron - OpenRouter | **-0.6766 tok/s** | -0.8531 tok/s to -0.5050 tok/s | <0.001 | 193 | 正值表示 Infron throughput 更高 |
| 端到端时延优先 | Cost: OpenRouter - Infron | **$0.00029516** | $0.00021278 to $0.00036663 | <0.001 | 193 | 正值表示 Infron 成本更低 |
| 端到端时延优先 | Token Cache Hit: Infron - OpenRouter | **-0.21 pp** | -1.29 pp to 0.38 pp | 1.0000 | 193 | 正值表示 Infron cache hit 更高 |
| 流式 TTFT 优先 | Latency: OpenRouter - Infron | **1146.12 ms** | 764.77 ms to 1497.12 ms | <0.001 | 200 | 正值表示 Infron latency 更低 |
| 流式 TTFT 优先 | TTFT: OpenRouter - Infron | **2858.40 ms** | 2535.21 ms to 3162.86 ms | <0.001 | 200 | 正值表示 Infron TTFT 更低 |
| 流式 TTFT 优先 | Throughput: Infron - OpenRouter | **-0.4132 tok/s** | -0.5904 tok/s to -0.2386 tok/s | <0.001 | 200 | 正值表示 Infron throughput 更高 |
| 流式 TTFT 优先 | Cost: OpenRouter - Infron | **$0.00010720** | $-0.00023742 to $0.00037466 | 0.5111 | 200 | 正值表示 Infron 成本更低 |
| 流式 TTFT 优先 | Token Cache Hit: Infron - OpenRouter | **-0.62 pp** | -2.14 pp to 0.42 pp | 0.5049 | 200 | 正值表示 Infron cache hit 更高 |

### 4.2 Reasoning / Thinking 控制校验

本轮未显式指定 reasoning/thinking 参数，保留模型与平台默认行为；该表记录默认行为下的 reasoning telemetry。

| 路由模式 | 平台 | Reasoning Tokens | 平均 Reasoning Tokens/请求 | Reasoning 请求数 | 平均首 Reasoning Token | 平均 TTFT | 平均 E2E 时延 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 吞吐优先 | **Infron** | **0** | **0.0000** | **0** | **0.00 ms** | **4992.94 ms** | **5311.71 ms** |
| 吞吐优先 | OpenRouter | 6000 | 15.0000 | 400 | 5619.75 ms | 5619.75 ms | 5884.51 ms |
| 价格优先 | Infron | **0** | **0.0000** | **0** | **0.00 ms** | 7224.73 ms | 8506.60 ms |
| 价格优先 | **OpenRouter** | 5835 | 14.9615 | 389 | 4895.85 ms | **4895.85 ms** | **5163.02 ms** |
| 端到端时延优先 | **Infron** | **0** | **0.0000** | **0** | **0.00 ms** | **3645.69 ms** | **4966.67 ms** |
| 端到端时延优先 | OpenRouter | 5955 | 15.4275 | 386 | 4854.43 ms | 4854.43 ms | 5122.85 ms |
| 流式 TTFT 优先 | **Infron** | **0** | **0.0000** | **0** | **0.00 ms** | **3596.32 ms** | **4758.14 ms** |
| 流式 TTFT 优先 | OpenRouter | 6153 | 15.3825 | 400 | 5025.52 ms | 5025.52 ms | 5331.20 ms |

### 4.3 API 协议兼容性矩阵

本轮 API 协议为 `/v1/chat/completions`；本表记录两家平台在该协议下的成功响应、usage、成本和缓存 telemetry 覆盖。

| API 协议 | Endpoint | 平台 | 配对轮数 | 请求数 | 成功率 | Usage 覆盖 | Token Usage 覆盖 | 成本覆盖 | 缓存 Telemetry 覆盖 | HTTP 状态 | 主要错误 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `chat_completions` | `/v1/chat/completions` | Infron | 800 | 1600 | **99.62%** | **100.00%** | **100.00%** | **100.00%** | **100.00%** | {"0":6,"200":1594} | 5 x The read operation timed out<br>1 x [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1000) |
| `chat_completions` | `/v1/chat/completions` | OpenRouter | 800 | 1600 | 99.44% | **100.00%** | **100.00%** | **100.00%** | **100.00%** | {"0":9,"200":1591} | 5 x [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1000)<br>4 x [Errno 54] Connection reset by peer |

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
| 吞吐优先 | Infron | 400 | 400 | `novita` 400 |
| 吞吐优先 | OpenRouter | 400 | 400 | `StreamLake` 400 |
| 价格优先 | Infron | 390 | 390 | `deepinfra` 340, `alibaba/cn` 50 |
| 价格优先 | OpenRouter | 390 | 390 | `StreamLake` 389, `GMICloud` 1 |
| 端到端时延优先 | Infron | 386 | 386 | `deepinfra` 386 |
| 端到端时延优先 | OpenRouter | 386 | 386 | `StreamLake` 356, `DeepInfra` 30 |
| 流式 TTFT 优先 | Infron | 400 | 400 | `deepinfra` 400 |
| 流式 TTFT 优先 | OpenRouter | 400 | 400 | `StreamLake` 362, `DeepInfra` 31, `Baidu` 7 |

### 上游 Provider 明细分布

| 路由模式 | 平台 | 上游 Provider | 请求数 | 占比 | first/second | 覆盖轮次 | Avg TTFT | Avg Latency | Prompt Tokens | Completion Tokens | Reasoning Tokens | Cache Read Tokens | 观测成本 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 吞吐优先 | Infron | `novita` | 400 | 100.00% | 200/200 | 200 | 4992.94 ms | 5311.71 ms | 6414682 | 5357 | 0 | 6023296 | $1.61315300 |
| 吞吐优先 | OpenRouter | `StreamLake` | 400 | 100.00% | 200/200 | 200 | 5619.75 ms | 5884.51 ms | 6414682 | 6400 | 6000 | 6136576 | $0.99183578 |
| 价格优先 | Infron | `deepinfra` | 340 | 87.18% | 165/175 | 175 | 3392.45 ms | 4571.01 ms | 5509975 | 4395 | 0 | 5072832 | $0.88017800 |
| 价格优先 | Infron | `alibaba/cn` | 50 | 12.82% | 30/20 | 30 | 33284.25 ms | 35268.63 ms | 530301 | 642 | 0 | 295424 | $0.11679200 |
| 价格优先 | OpenRouter | `StreamLake` | 389 | 99.74% | 194/195 | 195 | 4890.95 ms | 5158.59 ms | 6002831 | 6224 | 5835 | 5983552 | $0.80333903 |
| 价格优先 | OpenRouter | `GMICloud` | 1 | 0.26% | 1/0 | 1 | 6803.91 ms | 6883.60 ms | 37452 | 16 | 0 | 0 | $0.02250192 |
| 端到端时延优先 | Infron | `deepinfra` | 386 | 100.00% | 193/193 | 193 | 3645.69 ms | 4966.67 ms | 6273860 | 5003 | 0 | 6249536 | $0.77495600 |
| 端到端时延优先 | OpenRouter | `StreamLake` | 356 | 92.23% | 179/177 | 179 | 5045.97 ms | 5284.98 ms | 6114026 | 5696 | 5340 | 6105152 | $0.81128554 |
| 端到端时延优先 | OpenRouter | `DeepInfra` | 30 | 7.77% | 14/16 | 16 | 2581.47 ms | 3198.99 ms | 159834 | 480 | 615 | 158880 | $0.02063640 |
| 流式 TTFT 优先 | Infron | `deepinfra` | 400 | 100.00% | 200/200 | 200 | 3596.32 ms | 4758.14 ms | 6414682 | 5201 | 0 | 6285408 | $0.84264400 |
| 流式 TTFT 优先 | OpenRouter | `StreamLake` | 362 | 90.50% | 181/181 | 182 | 5283.54 ms | 5564.29 ms | 6332869 | 5792 | 5430 | 6312768 | $0.84577285 |
| 流式 TTFT 优先 | OpenRouter | `DeepInfra` | 31 | 7.75% | 15/16 | 17 | 2314.80 ms | 2897.23 ms | 62022 | 496 | 611 | 61056 | $0.00893800 |
| 流式 TTFT 优先 | OpenRouter | `Baidu` | 7 | 1.75% | 4/3 | 5 | 3686.97 ms | 4056.14 ms | 19791 | 112 | 112 | 8448 | $0.00937370 |

### 7.1 缓存命中率与实际成本反向表现下钻

该表把 cache、cost、provider 分布和 reasoning telemetry 放在同一层级，解释每个路由模式的主要差异来源。

| 路由模式 | 缓存命中差值 | Infron 成本倍数 | Infron 主要路径 | OpenRouter 主要路径 | Reasoning Tokens 差异 | 主要归因 |
| --- | --- | --- | --- | --- | --- | --- |
| 吞吐优先 | **+1.69 pp** | 1.63x | **`novita` 100.00%** | **`StreamLake` 100.00%** | **-6000** | Infron 缓存更高但成本更高，需检查上游单价、completion/reasoning tokens |
| 价格优先 | -3.83 pp | 1.21x | `deepinfra` 87.18% | **`StreamLake` 99.74%** | **-5835** | OpenRouter 缓存更高且成本更低，主要看 provider/cache 域差异 |
| 端到端时延优先 | -0.23 pp | **0.93x** | **`deepinfra` 100.00%** | **`StreamLake` 92.23%** | **-5955** | 缓存和成本方向存在分化，需结合速度指标判断 |
| 流式 TTFT 优先 | -0.27 pp | **0.98x** | **`deepinfra` 100.00%** | **`StreamLake` 90.50%** | **-6153** | 缓存和成本方向存在分化，需结合速度指标判断 |

## 8. 分层结果：按 Prompt 长度的缓存表现

本节按 prompt 长度 tier 聚合第二次请求的 cache read tokens、Token 级缓存命中率、实际成本、端到端时延和流式 TTFT。加粗单元表示同一长度 tier 下表现更优的一方。

### Prompt 长度分层总览

| Prompt 长度 tier | 目标 tokens | 平台 | 轮数 | 第二次 Prompt Tokens | 第二次 Cache Read Tokens | Token 级命中率 | 实际成本 | 平均 E2E 时延 | 平均 TTFT |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `short` | 1500 | Infron | **265** | **466794** | 451616 | 96.75% | $0.17568300 | 4717.31 ms | **3737.61 ms** |
| `short` | 1500 | OpenRouter | **265** | **466794** | **457728** | **98.06%** | **$0.15285428** | **4144.39 ms** | 3863.12 ms |
| `medium` | 8000 | Infron | **265** | **2445560** | 2377760 | 97.23% | $0.80691000 | 5713.62 ms | **4668.79 ms** |
| `medium` | 8000 | OpenRouter | **265** | **2445560** | **2414592** | **98.73%** | **$0.71005725** | **5368.63 ms** | 5127.16 ms |
| `long` | 32000 | Infron | **258** | **9659396** | 9579360 | 99.17% | $3.24513000 | 7236.92 ms | **6211.62 ms** |
| `long` | 32000 | OpenRouter | **258** | **9659396** | **9613888** | **99.53%** | **$2.65077169** | **6657.73 ms** | 6349.72 ms |

### Prompt 长度 x 路由模式缓存命中率

| Prompt 长度 tier | 路由模式 | Infron | OpenRouter | 胜出方 |
| --- | --- | --- | --- | --- |
| `short` | 吞吐优先 | 96.63% | **98.10%** | **OpenRouter** |
| `short` | 价格优先 | 93.95% | **98.10%** | **OpenRouter** |
| `short` | 端到端时延优先 | **98.98%** | 98.10% | **Infron** |
| `short` | 流式 TTFT 优先 | 97.53% | **97.94%** | **OpenRouter** |
| `medium` | 吞吐优先 | **99.86%** | 96.88% | **Infron** |
| `medium` | 价格优先 | 92.42% | **98.37%** | **OpenRouter** |
| `medium` | 端到端时延优先 | 98.30% | **99.87%** | **OpenRouter** |
| `medium` | 流式 TTFT 优先 | 98.37% | **99.86%** | **OpenRouter** |
| `long` | 吞吐优先 | **99.92%** | 98.40% | **Infron** |
| `long` | 价格优先 | 96.68% | **99.91%** | **OpenRouter** |
| `long` | 端到端时延优先 | **99.96%** | 99.92% | **Infron** |
| `long` | 流式 TTFT 优先 | **99.96%** | 99.92% | **Infron** |

## 9. 分层结果：按实验组的稳定性检查

### 吞吐优先

| 平台 | 组别 | 轮数 | 成功轮数 | Token 命中率 | 实际成本 | P95 Latency | P95 TTFT |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Infron | 1 | 50 | 50 | 99.62% | $0.62126500 | **8914.84 ms** | **8587.00 ms** |
| Infron | 2 | 50 | 50 | **99.85%** | $0.33495900 | 7957.49 ms | 7805.95 ms |
| Infron | 3 | 50 | 50 | **99.84%** | $0.33214400 | 9439.19 ms | 9017.67 ms |
| Infron | 4 | 50 | 50 | **99.84%** | $0.32478500 | 8212.44 ms | 8029.86 ms |
| OpenRouter | 1 | 50 | 50 | **99.84%** | **$0.30959630** | 12487.28 ms | 12033.90 ms |
| OpenRouter | 2 | 50 | 50 | 98.73% | **$0.22781642** | **7022.19 ms** | **6776.78 ms** |
| OpenRouter | 3 | 50 | 50 | 94.10% | **$0.24543220** | **9107.64 ms** | **8817.53 ms** |
| OpenRouter | 4 | 50 | 50 | **99.84%** | **$0.20899086** | **7794.67 ms** | **7290.17 ms** |

### 价格优先

| 平台 | 组别 | 轮数 | 成功轮数 | Token 命中率 | 实际成本 | P95 Latency | P95 TTFT |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Infron | 1 | 45 | 45 | 87.04% | $0.32151800 | 87203.15 ms | 82998.06 ms |
| Infron | 2 | 50 | 50 | **98.79%** | $0.26056300 | 10749.09 ms | 7560.04 ms |
| Infron | 3 | 50 | 50 | 95.09% | $0.22211700 | 7220.94 ms | **5011.36 ms** |
| Infron | 4 | 50 | 50 | 99.68% | **$0.19277200** | **5882.42 ms** | **4402.77 ms** |
| OpenRouter | 1 | 45 | 45 | **99.81%** | **$0.17744723** | **7879.73 ms** | **7585.10 ms** |
| OpenRouter | 2 | 50 | 50 | 98.73% | **$0.22302410** | **7733.01 ms** | **7034.32 ms** |
| OpenRouter | 3 | 50 | 50 | **99.84%** | **$0.21637876** | **6704.80 ms** | 6390.40 ms |
| OpenRouter | 4 | 50 | 50 | **99.84%** | $0.20899086 | 7257.05 ms | 7153.45 ms |

### 端到端时延优先

| 平台 | 组别 | 轮数 | 成功轮数 | Token 命中率 | 实际成本 | P95 Latency | P95 TTFT |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Infron | 1 | 50 | 50 | 98.73% | **$0.19645000** | 8331.75 ms | 6502.38 ms |
| Infron | 2 | 45 | 45 | **99.91%** | **$0.18854500** | 7858.70 ms | **5589.52 ms** |
| Infron | 3 | 49 | 49 | **99.91%** | **$0.19837800** | **7133.50 ms** | **5437.50 ms** |
| Infron | 4 | 49 | 49 | **99.90%** | **$0.19158300** | 8337.99 ms | **6631.28 ms** |
| OpenRouter | 1 | 50 | 50 | **99.84%** | $0.20897198 | **6611.28 ms** | **6450.22 ms** |
| OpenRouter | 2 | 45 | 45 | 99.86% | $0.19904936 | **7447.01 ms** | 7141.62 ms |
| OpenRouter | 3 | 49 | 49 | 99.84% | $0.21566118 | 7305.77 ms | 7092.93 ms |
| OpenRouter | 4 | 49 | 49 | 99.84% | $0.20823942 | **7455.78 ms** | 7164.70 ms |

### 流式 TTFT 优先

| 平台 | 组别 | 轮数 | 成功轮数 | Token 命中率 | 实际成本 | P95 Latency | P95 TTFT |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Infron | 1 | 50 | 50 | 99.68% | **$0.19290200** | **6925.38 ms** | **4657.72 ms** |
| Infron | 2 | 50 | 50 | 98.79% | $0.22294100 | **7377.62 ms** | **5495.93 ms** |
| Infron | 3 | 50 | 50 | **99.91%** | $0.23476100 | 8549.03 ms | **7605.03 ms** |
| Infron | 4 | 50 | 50 | **99.90%** | **$0.19204000** | **7022.95 ms** | **5339.84 ms** |
| OpenRouter | 1 | 50 | 50 | **99.84%** | $0.20960816 | 8273.97 ms | 8007.52 ms |
| OpenRouter | 2 | 50 | 50 | **99.85%** | **$0.22287306** | 7871.29 ms | 7588.82 ms |
| OpenRouter | 3 | 50 | 50 | 99.84% | **$0.21622772** | **8257.15 ms** | 7862.65 ms |
| OpenRouter | 4 | 50 | 50 | 99.81% | $0.21537561 | 7708.44 ms | 7375.08 ms |

## 10. 讨论：业务价值、适用边界与工程启示

业务决策不应只看单一指标。稳定长上下文和高频模板请求优先关注缓存命中率与成本；实时交互应同时约束 TTFT 和端到端时延；后台批处理更重视吞吐与失败成本。

| 路由模式 | 主要业务目标 | 本轮数据体现 | 适用场景 | 注意事项 |
| --- | --- | --- | --- | --- |
| 吞吐优先 | 最大化单位时间输出能力 | Infron 综合占优（3/5 指标） | 批量内容生成、离线摘要、后台数据加工 | 适合吞吐优先任务，但成本和缓存需单独约束 |
| 价格优先 | 最小化单位请求和单位 token 成本 | OpenRouter 综合占优（5/5 指标） | 高频模板化请求、客服自动化、营销触达、RAG 固定前缀 | 首包与完整响应更快，但需检查缓存和成本 |
| 端到端时延优先 | 最小化完整响应等待时间 | Infron 综合占优（3/5 指标） | 在线聊天、Agent 调用链、IDE/写作辅助、实时运营工具 | 适合吞吐优先任务，但成本和缓存需单独约束 |
| 流式 TTFT 优先 | 最小化流式首包响应时间 | Infron 综合占优（3/5 指标） | 流式聊天、实时 Copilot、首屏反馈、长任务进度感知 | 适合吞吐优先任务，但成本和缓存需单独约束 |

## 11. 结论

### 路由模式级结论

| 路由模式 | 目标 | 缓存胜出 | 成本胜出 | 吞吐胜出 | E2E 时延胜出 | TTFT 胜出 | 解读 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 吞吐优先 | 最大化单位时间输出能力 | **Infron** | **OpenRouter** | **OpenRouter** | **Infron** | **Infron** | Infron 综合占优（3/5 指标） |
| 价格优先 | 最小化单位请求和单位 token 成本 | **OpenRouter** | **OpenRouter** | **OpenRouter** | **OpenRouter** | **OpenRouter** | OpenRouter 综合占优（5/5 指标） |
| 端到端时延优先 | 最小化完整响应等待时间 | **OpenRouter** | **Infron** | **OpenRouter** | **Infron** | **Infron** | Infron 综合占优（3/5 指标） |
| 流式 TTFT 优先 | 最小化流式首包响应时间 | **OpenRouter** | **Infron** | **OpenRouter** | **Infron** | **Infron** | Infron 综合占优（3/5 指标） |

## 12. 局限性、缺失数据与后续实验计划

| 缺失或不足 | 对结论的影响 | 后续补充方式 | 当前处理方式 |
| --- | --- | --- | --- |
| 完整 routing trace | 无法逐跳证明每次请求的 provider 选择、fallback 和重试路径 | 补充 provider routing trace、decision log 和 fallback reason | 只使用响应中真实返回的 provider 字段和 provider 分布 |
| 更长时间窗口 | 4x50 能观察短期稳定性，但不能覆盖日级波动 | 增加 soak test 和跨时段重复实验 | 报告限定在本轮窗口内解释 |
| 真实生产语料 | 内置模板不能覆盖全部业务分布 | 使用脱敏生产语料分层抽样 | 当前只讨论代表性长上下文业务模板 |
| 成本字段一致性 | 不同平台 cost 字段覆盖率和口径可能不同 | 结合账单回查和 provider cost breakdown | 只统计响应明确返回的成本字段 |

## 13. 可复现性附录

| 工件 | 公开链接 |
| --- | --- |
| Summary | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/summary.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/summary.json) |
| 配对数据集 | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/benchmark_pairs.csv](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/benchmark_pairs.csv) |
| 请求级数据集 | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/benchmark_requests.jsonl](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/benchmark_requests.jsonl) |
| 过滤后结构化记录 | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/records.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/records.json) |
| 剔除记录审计 | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/records_excluded.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/records_excluded.json) |
| 测试源码 | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/code/test_rerun_routing_sort_cache_cost_ab.py](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/code/test_rerun_routing_sort_cache_cost_ab.py) |
| Benchmark 执行源码 | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/code/rerun_routing_sort_cache_cost_ab.py](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/code/rerun_routing_sort_cache_cost_ab.py) |
| HTML 报告渲染源码 | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/code/render_glm52_deepseek_style_report.py](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/code/render_glm52_deepseek_style_report.py) |
| 数据集引用 | `business_representative` 内置代表性业务模板；请求级导出见 [benchmark_requests.jsonl](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/benchmark_requests.jsonl) |
| GitHub Pages 中文报告 | [https://infronai.github.io/prompt-cache-bench/experiments/z-ai/glm-5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/reports/routing-cache-cost-streaming-performance-ab-study__glm-5__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-06.zh.html](https://infronai.github.io/prompt-cache-bench/experiments/z-ai/glm-5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/reports/routing-cache-cost-streaming-performance-ab-study__glm-5__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-06.zh.html) |
| GitHub Pages English report | [https://infronai.github.io/prompt-cache-bench/experiments/z-ai/glm-5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/reports/routing-cache-cost-streaming-performance-ab-study__glm-5__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-06.en.html](https://infronai.github.io/prompt-cache-bench/experiments/z-ai/glm-5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/reports/routing-cache-cost-streaming-performance-ab-study__glm-5__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-06.en.html) |
