# Infron 与 OpenRouter 路由、缓存、成本与流式性能 A/B 实验报告

## 摘要与结论大纲

**关键词**：Prompt Caching；A/B Testing；Provider Routing；Cache Affinity；Latency；Throughput；Cost Attribution；minimax/minimax-m2.5

### 摘要

本报告以 `minimax/minimax-m2.5` 为对象，对比 Infron 与 OpenRouter 在 Prompt Caching 场景下的路由策略、缓存命中、实际成本、吞吐量、TTFT 首包响应时间和端到端时延。实验包含 4 个实验组、每组 50 轮，覆盖 4 种 routing sort 策略；其中 TTFT First 中，Infron 使用 `provider.sort=ttft`，OpenRouter 使用其支持的 `provider.sort=latency` 作为对照。经过异常 usage、HTTP 异常和 A/B input tokens 偏差超过 50 tokens 的样本剔除后，最终保留 767 个配对样本、3068 次请求级观测记录，剔除 66 条记录。

核心结论是：在 `usage.prompt_tokens` 偏差不超过 50 tokens 的配对样本中，Infron 在 `latency` 和 `ttft` 模式下，Token 级缓存命中率更高，OpenRouter 在 `throughput` 和 `price` 模式下，Token 级缓存命中率更高；Infron 在 `ttft` 模式下，实际成本更低，OpenRouter 在 `throughput`、`price` 和 `latency` 模式下，实际成本更低；Infron 在 `ttft` 模式下，吞吐量更高，OpenRouter 在 `throughput`、`price` 和 `latency` 模式下，吞吐量更高；Infron 在 `ttft` 模式下，时延更低，OpenRouter 在 `throughput`、`price` 和 `latency` 模式下，时延更低；Infron 在 `ttft` 模式下，TTFT 首包响应时间更低，OpenRouter 在 `throughput`、`price` 和 `latency` 模式下，TTFT 首包响应时间更低。整体看，Infron 的优势集中在成本控制、部分模式的低时延路径，OpenRouter 的优势集中在成本控制、吞吐、TTFT、部分模式的端到端时延表现。平台选择应围绕业务目标展开，单一指标不足以代表整体效果。

本轮未显式控制 reasoning/thinking，响应中的 reasoning tokens 作为观测变量记录。

![Inference 平台不可能四角](../routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260707_161700/charts/inference_impossible_quadrilateral.svg)

图 0：Inference 平台“不可能四角”。吞吐量、价格、端到端时延和 TTFT 很难同时达到最优，平台路由通常会在四个方向之间做取舍；图中将四项归一化指标投影为路由模式点，并将同一平台的四个点连接成区域。

![结论总览图](../routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260707_161700/charts/conclusion_overview.svg)

图 A：结论总览图。上方卡片概括跨路由模式的总体胜出方，下方矩阵按 throughput、price、latency、TTFT 的路由目标顺序组织列，金色对角线表示各路由模式目标指标的 A/B 胜出方。

### 结论大纲

| 研究维度 | 结论 | 证据位置 |
| --- | --- | --- |
| 控制变量 | 进入统计的 A/B 样本满足同一 `sort/group/round` 下 first/second 请求 `usage.prompt_tokens` 各自偏差不超过 50 tokens；各模式 Input Tokens 对照为 `throughput`=5487258/5487258；`price`=6009914/6009914；`latency`=6207912/6207912；`ttft`=6207912/6207912 | 方法与数据质量章节 |
| 缓存复用 | Infron 在 `latency` 和 `ttft` 模式下，Token 级缓存命中率更高，OpenRouter 在 `throughput` 和 `price` 模式下，Token 级缓存命中率更高，说明本轮 provider stick/cache affinity 已转化为可观测的缓存命中差异 | 结果与机制分析章节 |
| 实际成本 | Infron 在 `ttft` 模式下，实际成本更低，OpenRouter 在 `throughput`、`price` 和 `latency` 模式下，实际成本更低，成本差异与 cache read tokens 同向变化 | 结果与结论章节 |
| 性能表现 | Infron 在 `ttft` 模式下，吞吐量更高，OpenRouter 在 `throughput`、`price` 和 `latency` 模式下，吞吐量更高；Infron 在 `ttft` 模式下，时延更低，OpenRouter 在 `throughput`、`price` 和 `latency` 模式下，时延更低；Infron 在 `ttft` 模式下，TTFT 首包响应时间更低，OpenRouter 在 `throughput`、`price` 和 `latency` 模式下，TTFT 首包响应时间更低 | 结果可视化与结论章节 |
| Reasoning 控制 | 本轮未显式控制 reasoning/thinking，响应中的 reasoning tokens 作为观测变量记录。 | Reasoning / Thinking 控制校验章节 |
| 归因边界 | 报告只使用响应可观测 telemetry，包括 provider 字段、usage、cost breakdown、TTFT、latency 和 cache tokens；未把平台内部私有 routing trace 当作已观测事实 | 机制分析、下钻分析与局限性章节 |
| 业务含义 | 对稳定长上下文、RAG 前缀、Agent 工具说明和批处理任务，缓存命中率与成本可预测性是核心收益；对实时交互任务，latency 仍需作为独立约束 | 讨论与结论章节 |

### 路由模式级结论

#### Throughput First

| 指标 | Infron / OpenRouter 并列对比 | 胜出方 |
| --- | --- | --- |
| 缓存命中率 | <span class="provider-label">Infron</span>████████ 95.28%<br><span class="provider-label">OpenRouter</span>**████████ 98.51%** | **OpenRouter**（高 3.38%） |
| 实际成本 | <span class="provider-label">Infron</span>████████ $0.24704000<br><span class="provider-label">OpenRouter</span>**██████░░ $0.19202371** | **OpenRouter**（低 22.27%） |
| Throughput | <span class="provider-label">Infron</span>██████░░ 3.21 tok/s<br><span class="provider-label">OpenRouter</span>**████████ 4.18 tok/s** | **OpenRouter**（高 30.34%） |
| Latency | <span class="provider-label">Infron</span>████████ 4988.85 ms<br><span class="provider-label">OpenRouter</span>**██████░░ 3827.34 ms** | **OpenRouter**（低 23.28%） |
| TTFT | <span class="provider-label">Infron</span>████████ 4123.13 ms<br><span class="provider-label">OpenRouter</span>**██████░░ 3203.80 ms** | **OpenRouter**（低 22.30%） |

#### Price First

| 指标 | Infron / OpenRouter 并列对比 | 胜出方 |
| --- | --- | --- |
| 缓存命中率 | <span class="provider-label">Infron</span>████████ 96.45%<br><span class="provider-label">OpenRouter</span>**████████ 97.48%** | **OpenRouter**（高 1.07%） |
| 实际成本 | <span class="provider-label">Infron</span>████████ $0.27260500<br><span class="provider-label">OpenRouter</span>**██████░░ $0.19811206** | **OpenRouter**（低 27.33%） |
| Throughput | <span class="provider-label">Infron</span>████░░░░ 2.85 tok/s<br><span class="provider-label">OpenRouter</span>**████████ 5.18 tok/s** | **OpenRouter**（高 81.36%） |
| Latency | <span class="provider-label">Infron</span>████████ 8848.37 ms<br><span class="provider-label">OpenRouter</span>**███░░░░░ 3091.26 ms** | **OpenRouter**（低 65.06%） |
| TTFT | <span class="provider-label">Infron</span>████████ 7428.26 ms<br><span class="provider-label">OpenRouter</span>**███░░░░░ 2541.08 ms** | **OpenRouter**（低 65.79%） |

#### Latency First

| 指标 | Infron / OpenRouter 并列对比 | 胜出方 |
| --- | --- | --- |
| 缓存命中率 | <span class="provider-label">Infron</span>**████████ 99.89%**<br><span class="provider-label">OpenRouter</span>████████ 99.88% | **Infron**（高 0.01%） |
| 实际成本 | <span class="provider-label">Infron</span>████████ $0.20062900<br><span class="provider-label">OpenRouter</span>**████████ $0.19451608** | **OpenRouter**（低 3.05%） |
| Throughput | <span class="provider-label">Infron</span>████████ 4.71 tok/s<br><span class="provider-label">OpenRouter</span>**████████ 4.96 tok/s** | **OpenRouter**（高 5.42%） |
| Latency | <span class="provider-label">Infron</span>████████ 3399.66 ms<br><span class="provider-label">OpenRouter</span>**████████ 3224.87 ms** | **OpenRouter**（低 5.14%） |
| TTFT | <span class="provider-label">Infron</span>████████ 2853.13 ms<br><span class="provider-label">OpenRouter</span>**███████░ 2652.39 ms** | **OpenRouter**（低 7.04%） |

#### TTFT First

| 指标 | Infron / OpenRouter 并列对比 | 胜出方 |
| --- | --- | --- |
| 缓存命中率 | <span class="provider-label">Infron</span>**████████ 99.95%**<br><span class="provider-label">OpenRouter</span>████████ 99.53% | **Infron**（高 0.42%） |
| 实际成本 | <span class="provider-label">Infron</span>**███████░ $0.19270000**<br><span class="provider-label">OpenRouter</span>████████ $0.21689979 | **Infron**（低 11.16%） |
| Throughput | <span class="provider-label">Infron</span>**████████ 5.01 tok/s**<br><span class="provider-label">OpenRouter</span>████████ 4.76 tok/s | **Infron**（高 5.18%） |
| Latency | <span class="provider-label">Infron</span>**████████ 3192.90 ms**<br><span class="provider-label">OpenRouter</span>████████ 3358.71 ms | **Infron**（低 4.94%） |
| TTFT | <span class="provider-label">Infron</span>**████████ 2714.81 ms**<br><span class="provider-label">OpenRouter</span>████████ 2836.95 ms | **Infron**（低 4.31%） |

说明：每个区块对应一种路由模式；同一指标行内的 Infron 与 OpenRouter 柱条按两者最大值归一化。缓存命中率和 throughput 越高越好，实际成本、latency 和 TTFT 越低越好。

## 1. 引言：背景、研究问题与贡献

本实验评估同一 OpenAI-compatible Chat Completions 请求在 Infron 与 OpenRouter 两个平台上的 prompt caching 表现。评估重点是：在输入条件严格一致时，不同 provider routing sort 策略会如何影响缓存命中、实际成本、吞吐量和端到端时延。

Prompt caching 对生产业务的核心价值在于：当业务请求包含稳定系统提示词、长上下文模板、RAG 前缀、工具说明或固定工作流指令时，第二次及后续请求理论上可以复用已处理的输入 token，从而降低单位请求成本，并可能改善整体服务稳定性。本实验通过“两次相同 prompt 请求”的方式构造可重复观测场景，用第二次请求的 cache read tokens 衡量缓存收益。

本报告回答三个问题：第一，在相同 payload 和 `usage.prompt_tokens` 偏差不超过 50 tokens 的口径下，Infron 与 OpenRouter 的缓存命中和成本表现有何差异；第二，不同 routing sort（`throughput`、`price`、`latency`、`ttft`）下速度、成本、首包和缓存如何变化；第三，从可观测 telemetry 看，两个平台的路由选择如何影响最终结果。由于 OpenRouter 不支持 `provider.sort=ttft`，TTFT First 的 A/B 设计为 Infron `sort=ttft` 对比 OpenRouter `sort=latency`。

### 1.1 研究假设

| 假设 | 内容 | 验证指标 |
| --- | --- | --- |
| H1 | 在重复稳定长前缀请求中，更强的 provider/cache affinity 会提升 Token 级缓存命中率 | 第二次请求 cache read tokens、Token 级命中率 |
| H2 | 更高缓存命中率会降低真实响应成本，但不必然降低 TTFT 或端到端 latency | 实际成本、平均 TTFT、平均 latency/请求 |
| H3 | 不同 routing sort 会改变 provider 选择，从而形成不同的成本、吞吐和时延 Pareto 前沿 | provider 分布、throughput、latency、cost |

### 1.2 本文贡献

- 给出一个严格配对的 A/B benchmark 方法，使用响应返回的 `usage.prompt_tokens` 作为真实 input token 控制变量。
- 将 prompt caching 评估从单一 cache hit 指标扩展到成本、吞吐、latency、TTFT、provider 分布和可复现数据集。
- 支持按 prompt 长度 tier 分层观察 cache read tokens、Token 级命中率和成本，让缓存收益不再只看总体均值。
- 用可观测 telemetry 解释 Infron 与 OpenRouter 的路由差异，同时明确内部 routing trace 缺失时的归因边界。
- 提供配对级 CSV、请求级 JSONL 和 A/B testing 代码，便于后续重复实验和第三方审计。

## 2. 方法：实验设计、数据集构造与控制变量

### 2.1 数据集生成方法

实验数据集由脚本自动生成，共覆盖 4 种 routing sort、2 个平台、4 个实验组、每组 50 轮。每一轮包含两次完全相同的 `chat/completions` 请求：第一次用于建立或触发缓存写入，第二次用于观测缓存读取。每个逻辑 routing sort 都记录平台侧实际 payload 的 SHA256，以便验证请求内容没有漂移。

Prompt 使用脚本内置的代表性业务模板，覆盖 RAG 客服、Agent 工具说明、营销自动化和代码审查四类稳定长上下文场景。每一轮在同一 `group/round` 下向 Infron 与 OpenRouter 发送完全相同的 messages，用于观察真实路由、缓存、成本、吞吐和时延差异。 本轮同时启用 prompt 长度分层：`short`≈1500 tokens, `medium`≈8000 tokens, `long`≈32000 tokens；脚本按 `group/round` 稳定分配 tier。

### 2.2 控制变量方法

A/B 测试的基本配对单元是同一 `sort/group/round` 下的 Infron 记录和 OpenRouter 记录。只有当两边 first request 与 second request 的 `usage.prompt_tokens` 各自偏差不超过 50 tokens 时，该配对才进入最终统计；任何 HTTP 非 200、请求异常、`usage.prompt_tokens <= 0` 或 A/B 输入 token 偏差超过阈值的记录都会被剔除。这保证了成本、缓存命中率、吞吐量和时延的对比建立在相近输入规模上。

本报告中的总 Input Tokens 严格取自响应返回的 `usage.prompt_tokens`，不使用本地 tokenizer 估算值。原因是 provider 的真实处理、缓存和计费口径最终以响应 usage 为准。通过使用响应 usage 并执行 A/B 配对一致性过滤，实验避免了 tokenizer 差异、服务端 prompt 包装和异常 usage 上报带来的偏差。

本轮启用 prompt 长度分层测试，分层计划为 `short`≈1500 tokens、`medium`≈8000 tokens、`long`≈32000 tokens。分层只改变稳定 prefix 的目标长度，不改变模型、temperature、max_tokens、routing sort、first/second 双请求、A/B input token 容差和 telemetry 口径；同一 `sort/group/round` 下 Infron 与 OpenRouter 仍发送同一 tier 的同源 messages。

### 2.3 实验设置图示与代码示例

下图展示单个 routing sort 下的实验流水线：同一 payload 分别发送到 Infron 与 OpenRouter，每个平台每轮连续发送两次相同请求，最终在同一 `sort/group/round` 维度做严格 A/B 配对。

![实验流程图](../routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260707_161700/charts/experiment_flow.svg)

图 1：实验流水线。该图强调每个 routing sort 下的同源 payload、双平台请求和 first/second request 配对关系，用于说明实验如何构造可比样本。

A/B 配对过滤的目标是确保比较只发生在输入 token 规模足够接近的样本上。只有 first request 与 second request 的 `usage.prompt_tokens` 在两边各自偏差不超过 50 tokens，样本才进入最终统计。

![A/B 配对过滤图](../routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260707_161700/charts/ab_pairing.svg)

图 2：A/B 配对过滤逻辑。该图明确展示异常 usage、HTTP 异常、非完整配对和 input tokens 不一致样本如何被排除，保证最终对比符合控制变量要求。

核心请求 payload 结构如下。实验固定模型、温度、最大输出 token、usage 返回和 provider sort，只改变路由优先模式。

```json
{
  "model": "minimax/minimax-m2.5",
  "messages": [
    {"role": "system", "content": "<stable long cache probe prefix>"},
    {"role": "user", "content": "Reply with exactly: cache probe ok"}
  ],
  "temperature": 0,
  "max_tokens": 16,
  "usage": {"include": true},
  "provider": {"sort": "throughput | price | latency | ttft", "allow_fallbacks": true}
}
```

TTFT First 对照规则：Infron 请求使用 `provider.sort=ttft`；OpenRouter 不支持该参数，因此 OpenRouter 请求使用 `provider.sort=latency` 作为首包/时延优先对照。报告中的逻辑路由模式仍统一记为 `ttft`，用于配对、聚合和可视化。

最终过滤逻辑可概括为以下伪代码。这个步骤是本实验控制变量的核心。

```python
for pair in group_by(records, key=(sort, group, round)):
    infron = pair['infron']
    openrouter = pair['openrouter']
    if not both_http_200(infron, openrouter):
        exclude(pair)
    elif any(request.usage.prompt_tokens <= 0 for request in pair.requests):
        exclude(pair)
    elif (infron.first.prompt_tokens, infron.second.prompt_tokens) != (openrouter.first.prompt_tokens, openrouter.second.prompt_tokens):
        exclude(pair)
    else:
        include(pair)
```

### 2.4 指标定义

表 1：核心指标定义与解释方向。

| 指标 | 定义 | 解释方向 |
| --- | --- | --- |
| 调用级命中率 | 第二次请求 `cache_read_tokens > 0` 的轮次占比 | 越高表示越稳定触发缓存读取 |
| Token 级命中率 | 第二次请求 cache read tokens / 第二次请求 prompt tokens | 越高表示输入 token 复用比例越高 |
| 实际成本 | first + second 两次请求返回 usage/cost 的合计 | 越低越好，代表真实账单风险更低 |
| 平均 throughput | 响应 completion tokens / 请求 latency seconds；reasoning tokens 作为响应 usage 组成部分处理，不单独拆成独立 KPI | 越高越好，代表单位时间响应输出能力更强 |
| 平均 latency/请求 | 每次请求完整响应耗时均值 | 越低越好，代表用户等待时间更短 |
| 平均 TTFT | streaming 下首包/首 token 到达时间均值 | 越低越好，代表用户更快看到首个响应信号 |
| Reasoning 口径 | 响应 usage 中的 reasoning token 字段作为响应统计的组成部分保留在原始记录和 summary 中 | 不单独展示排名，避免把内部推理预算误读为独立业务产出 |
| TTFT | 首 token 到达时间 | 本轮已启用 streaming 并采集 TTFT；TTFT 与完整响应 latency 分别代表首 token 体验和完整响应体验 |

### 2.5 表格、图表与架构图表达规范

为了让报告更容易审计，表格、图表和架构图采用统一表达方式：表格负责精确数值比较，趋势图展示指标变化过程，架构图解释机制假设与可观测证据之间的关系。结论以响应 telemetry 为准，架构图只用于解释机制。

表 2：可视化与表格专业性评估。

| 类型 | 当前用途 | 专业性评估 | 后续可补充项 |
| --- | --- | --- | --- |
| 总览表 | 展示核心指标、胜出方和可比样本规模 | 保留精确数值、单位和胜出高亮，适合审计；本轮报告已加入 bootstrap CI 与 paired permutation test | `已补充：bootstrap CI、p-value；后续可加入 standardized effect size` |
| 分组明细表 | 检查不同 group 的稳定性 | 能发现单组异常和策略漂移；本轮报告已加入 P50/P95/P99 latency/TTFT | `已补充：P50/P95/P99；后续可加入 IQR 和 tail amplification` |
| 核心指标柱状图 | 按 routing mode 对比 latency、throughput、cost、cache hit rate | 适合快速判断胜出方和指标差异；后续可增加误差棒 | `待补充：error bar、confidence band 可视化` |
| 指标生成曲线 | 展示每组请求的指标变化过程 | 有助于观察缓存预热、波动和异常点；后续可加入事件标注 | `待补充：warm-up annotation、outlier labels` |
| 架构图 | 解释 Infron provider routing、provider stick 和成本控制机制 | 明确区分可观测证据与机制解释，避免把内部实现假设误写成事实 | `待补充：真实 routing trace、provider cost breakdown 明细` |

## 3. 实验环境与数据质量控制

表 3：实验配置与数据质量控制规则。

| 项目 | 配置 |
| --- | --- |
| 测试模型 | `minimax/minimax-m2.5` |
| 对比平台 | Infron、OpenRouter |
| 路由偏好 | `throughput`、`price`、`latency`、`ttft` |
| TTFT First 对照 | Infron 使用 `provider.sort=ttft`；OpenRouter 使用 `provider.sort=latency` |
| 数据集名称 | `business_representative` |
| 数据集类型 | Built-in representative business prompt templates |
| 外部业务语料 | 未提供；本轮使用脚本内置/合成数据集 |
| 实验组数 | 每个平台每种路由 4 组 |
| 每组轮次 | 50 轮 |
| 并发 worker 数 | 24 |
| 长稳运行目标 | 0 秒 |
| 本地代理控制 | 同一本地代理：是；代理：启用 `socks5://127.0.0.1:1086`；隐式环境代理：已禁用 |
| 每轮请求 | 两次相同 prompt 请求，用第二次请求统计缓存命中 |
| Usage 采集 | 请求默认带 `usage: {"include": true}`，以响应 usage 作为真实统计口径 |
| 成本口径 | 只统计响应真实返回的 `usage.cost` 或 cost breakdown；若平台未返回成本字段，则显示 `N/A`，不按 0 计入胜负 |
| Reasoning / Thinking 控制 | 请求未显式指定 reasoning effort，保留模型与平台默认 thinking/reasoning 行为；响应 usage 中的 reasoning tokens 作为观测变量记录 |
| Streaming / TTFT 采集 | 已启用 streaming，并记录 TTFT/首内容 token/首 reasoning token 时间 |
| Provider 归因采集 | 脚本记录响应 headers、response model/id/system fingerprint、provider/routing trace 候选字段、provider cost breakdown 候选字段 |
| 结果目录 | <https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/minimax/minimax-m2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data> |
| 剔除规则 | HTTP 非 200、请求异常、任一请求 `usage.prompt_tokens <= 0`、或同一 `sort/group/round` 下 A/B 两边 first/second `usage.prompt_tokens` 偏差超过 50 tokens 的轮次不进入统计 |
| 剔除记录数 | 66 条 |
| `throughput` payload SHA256 | Infron `4c093944dee6cae73536a69f7f655331615cdf4ca66d9b608a7d2e82c03bacdf`<br>OpenRouter `4c093944dee6cae73536a69f7f655331615cdf4ca66d9b608a7d2e82c03bacdf` |
| `price` payload SHA256 | Infron `d728d4cc219996b302e4299efcc7a425f2253f17ec056f068762c641f12d00a0`<br>OpenRouter `d728d4cc219996b302e4299efcc7a425f2253f17ec056f068762c641f12d00a0` |
| `latency` payload SHA256 | Infron `908176fc8909553b6f956b2bed64af43c927432833e2cea673439d937f6c2b04`<br>OpenRouter `908176fc8909553b6f956b2bed64af43c927432833e2cea673439d937f6c2b04` |
| `ttft` payload SHA256 | Infron `1d66a9176b9bbb9220e9c00f79c345dc656f48d9c369951d2e5776562cc0f48b`<br>OpenRouter `908176fc8909553b6f956b2bed64af43c927432833e2cea673439d937f6c2b04` |

说明：A/B 控制变量是同一 routing sort 下发送给 Infron 和 OpenRouter 的请求 payload。总览中的 Input Tokens 按响应返回的 `usage.prompt_tokens` 汇总，代表各平台实际统计和计费口径下处理的输入 token 量。

## 4. 结果：总体指标与主要发现

说明：本节的 throughput、latency 和 TTFT 均为响应级整体指标。若响应 usage 中 `completion_tokens` 包含 reasoning tokens，则 reasoning 过程已纳入 throughput 分子；请求 latency 是完整响应端到端耗时，天然包含 reasoning 过程耗时；TTFT 是 streaming 下首个 SSE token/chunk 到达时间，代表首包响应体验。成本只使用响应明确返回的 cost 字段；未返回 cost 时标记为 `N/A`，不视为 0。

表 4：总体 A/B 指标对比。加粗单元表示同一 routing sort 下表现更好的一方；Input Tokens 加粗表示两边严格相等。

| 路由偏好 | 平台 | 总轮数 | 成功轮数 | 总 Input Tokens (`usage.prompt_tokens`) | 调用级命中率 | Token 级命中率 | 实际总成本 | 平均每轮成本 | 平均响应 throughput（含 reasoning） | 平均 latency/请求（含 reasoning） | 平均 TTFT | HTTP 状态 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `throughput` | Infron | **176** | **176** | **5487258** | 98.86% | 95.28% | $0.24704000 | $0.00140364 | 3.21 response tok/s | 4988.85 ms | 4123.13 ms | **200** |
| `throughput` | OpenRouter | **176** | **176** | **5487258** | **100.00%** | **98.51%** | **$0.19202371** | **$0.00109104** | **4.18 response tok/s** | **3827.34 ms** | **3203.80 ms** | **200** |
| `price` | Infron | **191** | **191** | **6009914** | 98.95% | 96.45% | $0.27260500 | $0.00142725 | 2.85 response tok/s | 8848.37 ms | 7428.26 ms | **200** |
| `price` | OpenRouter | **191** | **191** | **6009914** | **100.00%** | **97.48%** | **$0.19811206** | **$0.00103724** | **5.18 response tok/s** | **3091.26 ms** | **2541.08 ms** | **200** |
| `latency` | Infron | **200** | **200** | **6207912** | **100.00%** | **99.89%** | $0.20062900 | $0.00100314 | 4.71 response tok/s | 3399.66 ms | 2853.13 ms | **200** |
| `latency` | OpenRouter | **200** | **200** | **6207912** | **100.00%** | 99.88% | **$0.19451608** | **$0.00097258** | **4.96 response tok/s** | **3224.87 ms** | **2652.39 ms** | **200** |
| `ttft` | Infron | **200** | **200** | **6207912** | **100.00%** | **99.95%** | **$0.19270000** | **$0.00096350** | **5.01 response tok/s** | **3192.90 ms** | **2714.81 ms** | **200** |
| `ttft` | OpenRouter | **200** | **200** | **6207912** | 99.00% | 99.53% | $0.21689979 | $0.00108450 | 4.76 response tok/s | 3358.71 ms | 2836.95 ms | **200** |

### 4.1 尾延迟与显著性检验

表 5：尾延迟分位数。P95/P99 直接从请求级 latency 与 TTFT 计算，补充均值无法表达的尾部风险。

| 路由偏好 | 平台 | P50 Latency | P95 Latency | P99 Latency | P50 TTFT | P95 TTFT | P99 TTFT |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `throughput` | Infron | 3622.81 ms | 17148.15 ms | 21506.56 ms | 2944.11 ms | 14396.62 ms | 17850.89 ms |
| `throughput` | OpenRouter | **3328.39 ms** | **7127.15 ms** | **14950.30 ms** | **2690.51 ms** | **6573.05 ms** | **12289.60 ms** |
| `price` | Infron | 3372.95 ms | 51450.01 ms | 105079.91 ms | 2875.16 ms | 34764.97 ms | 102041.89 ms |
| `price` | OpenRouter | **2950.22 ms** | **4541.46 ms** | **5816.34 ms** | **2362.16 ms** | **3981.28 ms** | **5437.62 ms** |
| `latency` | Infron | 3151.37 ms | 5629.61 ms | 7199.06 ms | 2602.71 ms | 5086.86 ms | 6380.45 ms |
| `latency` | OpenRouter | **3014.57 ms** | **5374.84 ms** | **6654.78 ms** | **2421.81 ms** | **4911.88 ms** | **5984.79 ms** |
| `ttft` | Infron | 2995.60 ms | 5130.66 ms | **6299.52 ms** | 2498.83 ms | 4565.82 ms | **5773.80 ms** |
| `ttft` | OpenRouter | **2810.86 ms** | **4867.88 ms** | 19270.06 ms | **2262.56 ms** | **4248.25 ms** | 18346.08 ms |

表 6：配对统计检验。均值差使用 bootstrap 95% CI，p-value 使用 paired sign-flip permutation test。指标名给出差值方向，解释列说明正值代表的含义。

| 路由偏好 | 指标 | 均值差 | 95% CI | p-value | 配对数 | 解释 |
| --- | --- | ---: | --- | ---: | ---: | --- |
| `throughput` | Latency: OpenRouter - Infron | -2323.03 ms | [-3474.78 ms, -1201.53 ms] | <0.001 | 176 | 正值表示 Infron latency 更低 |
| `throughput` | TTFT: OpenRouter - Infron | -1838.67 ms | [-2917.66 ms, -821.38 ms] | 0.0010 | 176 | 正值表示 Infron TTFT 更低 |
| `throughput` | Throughput: Infron - OpenRouter | -0.5632 tok/s | [-0.8739 tok/s, -0.2575 tok/s] | <0.001 | 176 | 正值表示 Infron throughput 更高 |
| `throughput` | Cost: OpenRouter - Infron | $-0.00031259 | [$-0.00052131, $-0.00011431] | <0.001 | 176 | 正值表示 Infron 成本更低 |
| `throughput` | Token Cache Hit: Infron - OpenRouter | -1.97 pp | [-4.83 pp, 0.33 pp] | 0.2099 | 176 | 正值表示 Infron cache hit 更高 |
| `price` | Latency: OpenRouter - Infron | -11514.22 ms | [-16046.66 ms, -7286.99 ms] | <0.001 | 191 | 正值表示 Infron latency 更低 |
| `price` | TTFT: OpenRouter - Infron | -9774.34 ms | [-13716.61 ms, -6204.28 ms] | <0.001 | 191 | 正值表示 Infron TTFT 更低 |
| `price` | Throughput: Infron - OpenRouter | -1.0266 tok/s | [-1.2713 tok/s, -0.7757 tok/s] | <0.001 | 191 | 正值表示 Infron throughput 更高 |
| `price` | Cost: OpenRouter - Infron | $-0.00039002 | [$-0.00061573, $-0.00018150] | <0.001 | 191 | 正值表示 Infron 成本更低 |
| `price` | Token Cache Hit: Infron - OpenRouter | -2.89 pp | [-6.45 pp, 0.23 pp] | 0.1170 | 191 | 正值表示 Infron cache hit 更高 |
| `latency` | Latency: OpenRouter - Infron | -349.58 ms | [-742.77 ms, 40.87 ms] | 0.0700 | 200 | 正值表示 Infron latency 更低 |
| `latency` | TTFT: OpenRouter - Infron | -401.49 ms | [-763.38 ms, -44.85 ms] | 0.0247 | 200 | 正值表示 Infron TTFT 更低 |
| `latency` | Throughput: Infron - OpenRouter | -0.2884 tok/s | [-0.5010 tok/s, -0.0538 tok/s] | 0.0135 | 200 | 正值表示 Infron throughput 更高 |
| `latency` | Cost: OpenRouter - Infron | $-0.00003056 | [$-0.00010816, $0.00000923] | 1.0000 | 200 | 正值表示 Infron 成本更低 |
| `latency` | Token Cache Hit: Infron - OpenRouter | -0.16 pp | [-1.17 pp, 0.37 pp] | 1.0000 | 200 | 正值表示 Infron cache hit 更高 |
| `ttft` | Latency: OpenRouter - Infron | 331.62 ms | [-375.66 ms, 1142.08 ms] | 0.4396 | 200 | 正值表示 Infron latency 更低 |
| `ttft` | TTFT: OpenRouter - Infron | 244.28 ms | [-455.40 ms, 1038.26 ms] | 0.5596 | 200 | 正值表示 Infron TTFT 更低 |
| `ttft` | Throughput: Infron - OpenRouter | -0.2826 tok/s | [-0.5001 tok/s, -0.0623 tok/s] | 0.0130 | 200 | 正值表示 Infron throughput 更高 |
| `ttft` | Cost: OpenRouter - Infron | $0.00012100 | [$0.00000912, $0.00032571] | <0.001 | 200 | 正值表示 Infron 成本更低 |
| `ttft` | Token Cache Hit: Infron - OpenRouter | 1.32 pp | [0.30 pp, 2.84 pp] | <0.001 | 200 | 正值表示 Infron cache hit 更高 |

### 4.2 Reasoning / Thinking 控制校验

表 7：Reasoning telemetry 观测。本轮未显式指定 reasoning/thinking 参数，保留模型与平台默认行为；该表用于记录默认行为下的 reasoning tokens 和首 reasoning token 观测。

| 路由偏好 | 平台 | Reasoning Tokens | 平均 Reasoning Tokens/请求 | Reasoning 请求数 | 平均首 Reasoning Token | 平均 TTFT | 平均端到端 E2E 时延 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `throughput` | Infron | **0** | **0.0000** | **0** | 4209.96 ms | 4123.13 ms | 4988.85 ms |
| `throughput` | OpenRouter | 10488 | 29.7955 | 352 | **3203.80 ms** | **3203.80 ms** | **3827.34 ms** |
| `price` | Infron | **3404** | **8.9110** | **28** | 7460.71 ms | 7428.26 ms | 8848.37 ms |
| `price` | OpenRouter | 11393 | 29.8246 | 382 | **2541.08 ms** | **2541.08 ms** | **3091.26 ms** |
| `latency` | Infron | **0** | **0.0000** | **0** | 2888.12 ms | 2853.13 ms | 3399.66 ms |
| `latency` | OpenRouter | 11921 | 29.8025 | 400 | **2652.39 ms** | **2652.39 ms** | **3224.87 ms** |
| `ttft` | Infron | **0** | **0.0000** | **0** | **2740.30 ms** | **2714.81 ms** | **3192.90 ms** |
| `ttft` | OpenRouter | 11946 | 29.8650 | 400 | 2836.95 ms | 2836.95 ms | 3358.71 ms |

本轮 Reasoning / Thinking 控制：请求未显式指定 reasoning effort，保留模型与平台默认 thinking/reasoning 行为；响应 usage 中的 reasoning tokens 作为观测变量记录。


### 4.3 API 协议记录

本轮 API 协议为 `/v1/chat/completions`；本表记录两家平台在该协议下的 HTTP 成功、usage、token usage、成本和缓存 telemetry 覆盖。加粗单元表示覆盖率更高的一方。

| API 协议 | Endpoint | 平台 | 配对轮数 | 请求数 | 成功率 | Usage 覆盖 | Token Usage 覆盖 | 成本覆盖 | 缓存 Telemetry 覆盖 | HTTP 状态 | 主要错误 |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `chat_completions` | `/v1/chat/completions` | Infron | 800 | 1600 | 97.31% | **100.00%** | **100.00%** | **100.00%** | **100.00%** | `{"0":43,"200":1557}` | 35 x [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1000)<br>8 x [Errno 54] Connection reset by peer |
| `chat_completions` | `/v1/chat/completions` | OpenRouter | 800 | 1600 | **99.75%** | **100.00%** | **100.00%** | **100.00%** | **100.00%** | `{"0":4,"200":1596}` | 4 x [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1000) |


## 5. 结果可视化：按路由模式的核心指标变化

说明：本节按路由模式组织图表。每张图对应一种 First 路由模式，并在同一图内对比 Infron 与 OpenRouter 的 latency、TTFT、throughput、实际成本和 Token 级缓存命中率，方便观察同一模式下的 A/B 指标差异。本轮已启用 streaming，并采集 TTFT、首内容 token 与首 reasoning token 时间；TTFT 代表首包响应体验，latency 代表完整响应体验。

### Throughput First 路由模式

![Throughput First 路由模式下的核心指标 A/B 对比](../routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260707_161700/charts/throughput_first.svg)

图 3：Throughput First 路由模式下的核心指标对比。柱状图同时呈现缓存、成本、吞吐、TTFT 和 latency 表现。

![Throughput First 路由模式下的综合雷达图](../routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260707_161700/charts/throughput_first_radar.svg)

图 4：Throughput First 路由模式下的综合雷达图。所有轴都按“越外圈越好”归一化，便于快速比较两家平台的综合形状。

![Throughput First 路由模式下的指标生成过程对比曲线](../routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260707_161700/charts/throughput_first_curves.svg)

图 5：Throughput First 路由模式下的指标生成过程曲线。该图用于观察指标随 group/round 的变化，而不只依赖均值。

### Price First 路由模式

![Price First 路由模式下的核心指标 A/B 对比](../routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260707_161700/charts/price_first.svg)

图 6：Price First 路由模式下的核心指标对比。柱状图同时呈现缓存、成本、吞吐、TTFT 和 latency 表现。

![Price First 路由模式下的综合雷达图](../routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260707_161700/charts/price_first_radar.svg)

图 7：Price First 路由模式下的综合雷达图。所有轴都按“越外圈越好”归一化，便于快速比较两家平台的综合形状。

![Price First 路由模式下的指标生成过程对比曲线](../routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260707_161700/charts/price_first_curves.svg)

图 8：Price First 路由模式下的指标生成过程曲线。该图用于观察指标随 group/round 的变化，而不只依赖均值。

### Latency First 路由模式

![Latency First 路由模式下的核心指标 A/B 对比](../routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260707_161700/charts/latency_first.svg)

图 9：Latency First 路由模式下的核心指标对比。柱状图同时呈现缓存、成本、吞吐、TTFT 和 latency 表现。

![Latency First 路由模式下的综合雷达图](../routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260707_161700/charts/latency_first_radar.svg)

图 10：Latency First 路由模式下的综合雷达图。所有轴都按“越外圈越好”归一化，便于快速比较两家平台的综合形状。

![Latency First 路由模式下的指标生成过程对比曲线](../routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260707_161700/charts/latency_first_curves.svg)

图 11：Latency First 路由模式下的指标生成过程曲线。该图用于观察指标随 group/round 的变化，而不只依赖均值。

### TTFT First 路由模式

![TTFT First 路由模式下的核心指标 A/B 对比](../routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260707_161700/charts/ttft_first.svg)

图 12：TTFT First 路由模式下的核心指标对比。柱状图同时呈现缓存、成本、吞吐、TTFT 和 latency 表现。

![TTFT First 路由模式下的综合雷达图](../routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260707_161700/charts/ttft_first_radar.svg)

图 13：TTFT First 路由模式下的综合雷达图。所有轴都按“越外圈越好”归一化，便于快速比较两家平台的综合形状。

![TTFT First 路由模式下的指标生成过程对比曲线](../routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260707_161700/charts/ttft_first_curves.svg)

图 14：TTFT First 路由模式下的指标生成过程曲线。该图用于观察指标随 group/round 的变化，而不只依赖均值。

说明：TTFT First 中，Infron 使用 `provider.sort=ttft`；OpenRouter 使用 `provider.sort=latency` 作为可支持的对照策略。

## 6. Infron 技术架构与缓存/成本机制解释

本节使用本次 benchmark 的可观测结果解释 Infron 在高 cache rate 与成本控制上的工程路径。需要说明的是，报告没有采集 Infron 内部私有 routing trace；因此下文把响应中真实返回的 provider 分布、cache read tokens、cost breakdown 和 latency/throughput 指标作为证据，用架构图解释这些结果背后的合理机制。

### 6.1 多 provider 路由与可观测控制面

Infron 对外提供 OpenAI-compatible API，对内需要在多个上游 provider、模型部署和路由策略之间做选择。对 prompt caching 工作负载而言，路由层不只是选择一个可用 provider，还需要同时考虑缓存亲和性、健康状态、成本、吞吐和时延目标。

![Infron 多 provider 路由架构](../routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260707_161700/charts/infron_architecture.svg)

图 12：Infron 多 provider 路由与缓存控制面。该图用于说明请求从统一 API 入口进入后，路由控制面如何在健康状态、策略目标、provider 选择和缓存域之间形成决策链路。

本次实验中，Infron 在不同 routing sort 下呈现出可观测的 provider 分布：`throughput` 主要路由到 `inceptron`（100.00%）；`price` 主要路由到 `inceptron`（92.67%）；`latency` 主要路由到 `inceptron`（100.00%）；`ttft` 主要路由到 `inceptron`（100.00%）。这种模式说明路由结果不是完全随机扩散，而是围绕路由目标形成了较稳定的 provider 选择。稳定的 provider 选择是高缓存命中率的前提，因为 prompt cache 通常与具体 provider、模型部署或缓存域绑定。

### 6.2 Provider Stick 与 Cache Affinity

Provider stick 是多 provider 网关中的缓存亲和策略：当请求具有相同或高度稳定的 prompt prefix 时，路由层倾向于把同一类请求送往同一个健康 provider 或缓存域，以减少缓存碎片化。它不等于固定永不切换 provider；当上游不可用、限流或 SLA 风险升高时，路由仍应回退到其他健康路径。

![Provider stick 与 cache affinity](../routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260707_161700/charts/provider_stick_cache_affinity.svg)

图 13：Provider stick 与 cache affinity 机制。该图表达的是工程机制假设：同类请求在健康 provider 集合内保持缓存亲和，可减少跨 provider/cache domain 的缓存碎片。

本次实验中，Infron 的缓存命中优势并非在所有 routing sort 下都成立：`throughput` OpenRouter；`price` OpenRouter；`latency` Infron；`ttft` Infron。这说明 provider stick/cache affinity 的收益依赖具体路由目标和最终上游路径。对于相同 stable prefix 的连续双请求，若 first/second 请求稳定落在同一缓存域，第二次请求更容易读取第一次请求写入或刷新后的 KV/cache 状态；若请求跨 provider、跨部署或落到不充分支持该缓存口径的路径，同样的 prompt 也可能需要分别暖缓存，从而降低整体 cache read tokens。

### 6.3 成本控制路径

成本控制来自三层叠加：第一层是缓存命中降低重复 prefill 的有效处理成本；第二层是 provider routing 在健康 provider 集合内选择更合适的成本路径；第三层是输出 token 与 reasoning token 对总成本的影响。本次实验中，实际成本胜出方为：`throughput` OpenRouter；`price` OpenRouter；`latency` OpenRouter；`ttft` Infron。这说明缓存亲和、provider 单价、输出 token 数和 reasoning 执行情况会共同影响单位请求成本，不能只用 cache hit rate 单独解释成本结果。

![Infron 成本控制路径](../routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260707_161700/charts/infron_cost_control.svg)

图 14：Infron 成本控制路径。该图把缓存命中、provider stick、成本感知 routing 和响应 cost breakdown 连接起来，用于解释为什么 cache rate 与实际成本会同步改善。

表 7：Infron 缓存与成本控制机制的可观测证据。

| 机制 | 对 cache rate 的影响 | 对成本的影响 | 本次实验中的可观测信号 |
| --- | --- | --- | --- |
| Stable prefix 识别 | 相同前缀更容易命中已有 cache | 降低重复 prefill 的边际成本 | 同一 payload SHA256、第二次请求 cache read tokens 高 |
| Provider stick / cache affinity | 降低跨 provider/cache domain 的缓存碎片 | 减少重复暖缓存 | Infron 在 sort 内 provider 分布更集中，Token 命中率更高 |
| 健康检查与 fallback | 保护可用性，避免单 provider 故障 | fallback 可能牺牲部分缓存收益，但降低失败成本 | HTTP 状态均为 200，provider 分布仍保留少量切换可能 |
| 成本感知 routing | 在满足健康和策略约束下偏向低成本路径 | 降低总成本和每轮成本 | 本轮不同 routing sort 下成本胜出方不一致，需要结合 provider 分布、cache read tokens 和 reasoning tokens 解释 |

因此，本轮数据更准确的结论是：高 cache rate 的关键在于路由层、缓存域和 provider 选择之间是否形成稳定亲和，而不是平台名称本身。对于长 system prompt、RAG 固定前缀、工具说明和高频模板化请求，只有当路由目标与缓存亲和一致时，这种亲和性才会转化为更高的 cache read tokens，并进一步影响单位请求成本。

## 7. Provider/Route 下钻分析

说明：本轮 streaming 响应已采集到部分上游 provider 标识、响应 model/id、request_id、provider cost breakdown 候选字段；下钻分析结合这些真实返回字段与可观测 telemetry（缓存命中、实际成本、latency、TTFT、throughput）解释 Infron 与 OpenRouter 内部路由差异。

表 8：Provider/Route 下钻指标。该表把 provider 分布、成本、吞吐、TTFT 和 latency 放在同一层级，用于分析路由选择如何影响最终结果。

| 路由偏好 | 平台 | 有效轮次 | Input Tokens | Token 命中率 | 实际成本 | 成本/1K Input | 响应 Throughput（含 reasoning） | TTFT | Latency/请求（含 reasoning） | 可观测路由画像 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `throughput` | Infron | **176** | **5487258** | 95.28% | $0.24704000 | $0.000045 | 3.21 response tok/s | 4123.13 ms | 4988.85 ms | 表现均衡但无单项极值 |
| `throughput` | OpenRouter | **176** | **5487258** | **98.51%** | **$0.19202371** | **$0.000035** | **4.18 response tok/s** | **3203.80 ms** | **3827.34 ms** | 缓存、成本、速度指标同时占优 |
| `price` | Infron | **191** | **6009914** | 96.45% | $0.27260500 | $0.000045 | 2.85 response tok/s | 7428.26 ms | 8848.37 ms | 表现均衡但无单项极值 |
| `price` | OpenRouter | **191** | **6009914** | **97.48%** | **$0.19811206** | **$0.000033** | **5.18 response tok/s** | **2541.08 ms** | **3091.26 ms** | 缓存、成本、速度指标同时占优 |
| `latency` | Infron | **200** | **6207912** | **99.89%** | $0.20062900 | $0.000032 | 4.71 response tok/s | 2853.13 ms | 3399.66 ms | 表现均衡但无单项极值 |
| `latency` | OpenRouter | **200** | **6207912** | 99.88% | **$0.19451608** | **$0.000031** | **4.96 response tok/s** | **2652.39 ms** | **3224.87 ms** | 速度路径更激进，优先低时延/高吞吐 |
| `ttft` | Infron | **200** | **6207912** | **99.95%** | **$0.19270000** | **$0.000031** | **5.01 response tok/s** | **2714.81 ms** | **3192.90 ms** | 缓存、成本、速度指标同时占优 |
| `ttft` | OpenRouter | **200** | **6207912** | 99.53% | $0.21689979 | $0.000035 | 4.76 response tok/s | 2836.95 ms | 3358.71 ms | 表现均衡但无单项极值 |

### 上游 Provider 分布

表 9：上游 provider 归因覆盖率总览。`总请求数` 是 first/second 请求级计数；`已归因请求数` 表示响应中可提取到 provider 标识的请求数。

| 路由偏好 | 平台 | 总请求数 | 已归因请求数 | 归因覆盖率 | Provider 分布 | Cost breakdown 请求数 |
| --- | ---: | ---: | ---: | ---: | --- | ---: |
| `throughput` | Infron | 352 | 352 | 100.00% | inceptron: 352 (100.00%) | 352 |
| `throughput` | OpenRouter | 352 | 352 | 100.00% | DeepInfra: 349 (99.15%), Mara: 3 (0.85%) | 352 |
| `price` | Infron | 382 | 382 | 100.00% | inceptron: 354 (92.67%), alibaba/cn: 28 (7.33%) | 382 |
| `price` | OpenRouter | 382 | 382 | 100.00% | DeepInfra: 382 (100.00%) | 382 |
| `latency` | Infron | 400 | 400 | 100.00% | inceptron: 400 (100.00%) | 400 |
| `latency` | OpenRouter | 400 | 400 | 100.00% | DeepInfra: 400 (100.00%) | 400 |
| `ttft` | Infron | 400 | 400 | 100.00% | inceptron: 400 (100.00%) | 400 |
| `ttft` | OpenRouter | 400 | 400 | 100.00% | DeepInfra: 396 (99.00%), WandB: 4 (1.00%) | 400 |

表 10：上游 provider 明细分布。该表按 provider 拆分请求占比、first/second 分布、覆盖轮次、时延、TTFT、token、cache 和成本，用于定位最终 A/B 差异来自哪个上游路径。

| 路由偏好 | 平台 | 上游 Provider | 请求数 | 占比 | first/second | 覆盖轮次 | Avg TTFT | Avg Latency | Prompt Tokens | Completion Tokens | Reasoning Tokens | Cache Read Tokens | 观测成本 | Cost breakdown 请求数 |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `throughput` | Infron | `inceptron` | 352 | 100.00% | 176/176 | 176 | 4123.13 ms | 4988.85 ms | 5487258 | 5632 | 0 | 5118848 | $0.24704000 | 352 |
| `throughput` | OpenRouter | `DeepInfra` | 349 | 99.15% | 173/176 | 176 | 3182.39 ms | 3805.94 ms | 5406089 | 5584 | 10440 | 5292288 | $0.18226039 | 349 |
| `throughput` | OpenRouter | `Mara` | 3 | 0.85% | 3/0 | 3 | 5693.59 ms | 6317.13 ms | 81169 | 48 | 48 | 0 | $0.00976332 | 3 |
| `price` | Infron | `inceptron` | 354 | 92.67% | 170/184 | 184 | 3259.72 ms | 3827.46 ms | 5625732 | 5664 | 0 | 5332560 | $0.23542700 | 354 |
| `price` | Infron | `alibaba/cn` | 28 | 7.33% | 21/7 | 21 | 60130.40 ms | 72327.13 ms | 384182 | 3983 | 3404 | 196864 | $0.03717800 | 28 |
| `price` | OpenRouter | `DeepInfra` | 382 | 100.00% | 191/191 | 191 | 2541.08 ms | 3091.26 ms | 6009914 | 6112 | 11393 | 5920032 | $0.19811206 | 382 |
| `latency` | Infron | `inceptron` | 400 | 100.00% | 200/200 | 200 | 2853.13 ms | 3399.66 ms | 6207912 | 6400 | 0 | 6166752 | $0.20062900 | 400 |
| `latency` | OpenRouter | `DeepInfra` | 400 | 100.00% | 200/200 | 200 | 2652.39 ms | 3224.87 ms | 6207912 | 6400 | 11921 | 6200256 | $0.19451608 | 400 |
| `ttft` | Infron | `inceptron` | 400 | 100.00% | 200/200 | 200 | 2714.81 ms | 3192.90 ms | 6207912 | 6400 | 0 | 6204512 | $0.19270000 | 400 |
| `ttft` | OpenRouter | `DeepInfra` | 396 | 99.00% | 199/197 | 199 | 2823.67 ms | 3348.14 ms | 6124987 | 6336 | 11827 | 6117408 | $0.19194549 | 396 |
| `ttft` | OpenRouter | `WandB` | 4 | 1.00% | 1/3 | 3 | 4151.36 ms | 4405.84 ms | 82925 | 64 | 119 | 36032 | $0.02495430 | 4 |

### 7.1 缓存命中率与实际成本反向表现下钻

本节专门解释两个问题：第一，为什么某些路由模式下 Infron 的缓存命中率低于 OpenRouter；第二，为什么某些路由模式下 Infron 的实际成本高于 OpenRouter。分析只使用本轮响应中可观测的 telemetry：provider 分布、cache read tokens、usage cost、completion tokens、reasoning tokens、TTFT 与端到端 E2E 时延。

表 10-A：按路由模式拆解缓存与成本差异。缓存差值为 Infron 减 OpenRouter，成本倍数为 Infron 实际成本 / OpenRouter 实际成本。

| 路由偏好 | 缓存命中差值 | Infron 成本倍数 | Infron 主要上游路径 | OpenRouter 主要上游路径 | Reasoning Tokens 差异 | 主要归因 |
| --- | ---: | ---: | --- | --- | ---: | --- |
| `throughput` | -3.22 pp | 1.29x | `inceptron` 100.0% | `DeepInfra` 99.1%<br>`Mara` 0.9% | -10488 | 缓存接近或更高，但 provider 单价路径更高 |
| `price` | -1.03 pp | 1.38x | `inceptron` 92.7%<br>`alibaba/cn` 7.3% | `DeepInfra` 100.0% | -7989 | 缓存接近或更高，但 provider 单价路径更高 |
| `latency` | +0.01 pp | 1.03x | `inceptron` 100.0% | `DeepInfra` 100.0% | -11921 | 缓存接近或更高，但 provider 单价路径更高 |
| `ttft` | +0.42 pp | 0.89x | `inceptron` 100.0% | `DeepInfra` 99.0%<br>`WandB` 1.0% | -11946 | 缓存亲和、reasoning 控制和 provider 成本路径共同改善 |

分模式解释：

- `throughput`：Infron Token 级缓存命中率为 95.28%，OpenRouter 为 98.51%，差值 -3.22 pp；Infron 成本为 $0.24704000，OpenRouter 为 $0.19202371，成本倍数 1.29x。Infron 主要路径为 `inceptron` 100.0%；OpenRouter 主要路径为 `DeepInfra` 99.1%，`Mara` 0.9%。OpenRouter 比 Infron 多 10488 个 reasoning tokens。该模式下 Infron 缓存命中率更低、实际成本更高，主要需要从 provider 单价路径、输出规模和缓存域稳定性解释。
- `price`：Infron Token 级缓存命中率为 96.45%，OpenRouter 为 97.48%，差值 -1.03 pp；Infron 成本为 $0.27260500，OpenRouter 为 $0.19811206，成本倍数 1.38x。Infron 主要路径为 `inceptron` 92.7%，`alibaba/cn` 7.3%；OpenRouter 主要路径为 `DeepInfra` 100.0%。OpenRouter 比 Infron 多 7989 个 reasoning tokens。该模式下 Infron 缓存命中率更低、实际成本更高，主要需要从 provider 单价路径、输出规模和缓存域稳定性解释。
- `latency`：Infron Token 级缓存命中率为 99.89%，OpenRouter 为 99.88%，差值 +0.01 pp；Infron 成本为 $0.20062900，OpenRouter 为 $0.19451608，成本倍数 1.03x。Infron 主要路径为 `inceptron` 100.0%；OpenRouter 主要路径为 `DeepInfra` 100.0%。OpenRouter 比 Infron 多 11921 个 reasoning tokens。该模式下 Infron 缓存命中率更高但实际成本更高，说明缓存收益被 provider 单价、输出规模或 usage/cost 计费路径抵消。
- `ttft`：Infron Token 级缓存命中率为 99.95%，OpenRouter 为 99.53%，差值 +0.42 pp；Infron 成本为 $0.19270000，OpenRouter 为 $0.21689979，成本倍数 0.89x。Infron 主要路径为 `inceptron` 100.0%；OpenRouter 主要路径为 `DeepInfra` 99.0%，`WandB` 1.0%。OpenRouter 比 Infron 多 11946 个 reasoning tokens。该模式下 Infron 同时取得更高缓存命中率和更低实际成本，说明当前 provider 路径与缓存域匹配较好；若速度指标未同步胜出，差异更可能来自上游响应路径和排队行为。

总体看，本轮真正影响缓存与成本的不是单一平台标签，而是“路由目标 → 实际 provider → 缓存域 → reasoning 执行 → usage/cost 返回”的链路组合。Infron 在 `latency`、`ttft` 的 Token 级缓存命中率高于 OpenRouter，在 `ttft` 的实际成本低于 OpenRouter。 Infron 实际成本高于 OpenRouter 的路由模式为 `throughput`、`price`、`latency`。 Reasoning tokens 差异主要出现在 `throughput` -10488；`price` -7989；`latency` -11921；`ttft` -11946。


- `throughput` 路由下：缓存命中 OpenRouter 更优，成本 OpenRouter 更低，throughput OpenRouter 更高，latency OpenRouter 更低，TTFT OpenRouter 更低。 这说明 OpenRouter 在该路由下更偏首包与完整响应速度路径。
- `price` 路由下：缓存命中 OpenRouter 更优，成本 OpenRouter 更低，throughput OpenRouter 更高，latency OpenRouter 更低，TTFT OpenRouter 更低。 这说明 OpenRouter 在该路由下更偏首包与完整响应速度路径。
- `latency` 路由下：缓存命中 Infron 更优，成本 OpenRouter 更低，throughput OpenRouter 更高，latency OpenRouter 更低，TTFT OpenRouter 更低。 这说明 OpenRouter 在该路由下更偏首包与完整响应速度路径。
- `ttft` 路由下：缓存命中 Infron 更优，成本 Infron 更低，throughput Infron 更高，latency Infron 更低，TTFT Infron 更低。 这说明 Infron 在该路由下更偏缓存亲和、成本控制和低时延的综合路径，OpenRouter 主要保留吞吐优势。
- 脚本已支持在后续实验中采集上游 provider 标识候选字段、routing trace 候选字段、provider cost breakdown 候选字段，并可通过 `--stream` 记录 TTFT、首内容 token 与首 reasoning token 时间。当前报告只展示响应中真实存在的字段，不伪造 provider identity。


## 8. 分层结果：按 Prompt 长度的缓存表现

本节按 prompt 长度 tier 聚合第二次请求的 cache read tokens、Token 级缓存命中率、实际成本和时延。加粗单元表示同一长度 tier 下表现更优的一方；缓存命中率越高越好，成本、latency 和 TTFT 越低越好。

表 11：Prompt 长度分层下的总体缓存表现。

| Prompt 长度 tier | 目标 tokens | 平台 | 轮数 | 第二次 Prompt Tokens | 第二次 Cache Read Tokens | Token 级命中率 | 实际成本 | 平均 Latency | 平均 TTFT |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `short` | 1500 | Infron | **253** | **443551** | 432320 | 97.47% | $0.04197400 | 3600.32 ms | 2837.32 ms |
| `short` | 1500 | OpenRouter | **253** | **443551** | **433792** | **97.80%** | **$0.03912148** | **2569.27 ms** | **1975.54 ms** |
| `medium` | 8000 | Infron | **260** | **2355938** | 2308000 | 97.97% | $0.18207300 | 4974.12 ms | 4043.95 ms |
| `medium` | 8000 | OpenRouter | **260** | **2355938** | **2343520** | **99.47%** | **$0.15929771** | **3143.56 ms** | **2603.53 ms** |
| `long` | 32000 | Infron | **254** | **9157009** | 8975024 | 98.01% | $0.68892700 | 6623.77 ms | 5861.38 ms |
| `long` | 32000 | OpenRouter | **254** | **9157009** | **9044224** | **98.77%** | **$0.60313245** | **4383.50 ms** | **3820.29 ms** |

表 11-2：Prompt 长度 × 路由模式的 Token 级缓存命中率。

| Prompt 长度 tier | 路由偏好 | Infron | OpenRouter | 胜出方 |
| --- | --- | ---: | ---: | --- |
| `short` | `throughput` | **97.75%** | 96.90% | **Infron** |
| `short` | `price` | 94.46% | **98.57%** | **OpenRouter** |
| `short` | `latency` | 98.00% | **98.56%** | **OpenRouter** |
| `short` | `ttft` | **99.47%** | 97.09% | **Infron** |
| `medium` | `throughput` | 96.63% | **99.86%** | **OpenRouter** |
| `medium` | `price` | 95.23% | **99.85%** | **OpenRouter** |
| `medium` | `latency` | **99.90%** | 99.86% | **Infron** |
| `medium` | `ttft` | **99.90%** | 98.37% | **Infron** |
| `long` | `throughput` | 94.81% | **98.23%** | **OpenRouter** |
| `long` | `price` | **96.86%** | 96.83% | **Infron** |
| `long` | `latency` | **99.98%** | 99.95% | **Infron** |
| `long` | `ttft` | **99.98%** | 99.95% | **Infron** |


## 9. 分层结果：按实验组的稳定性检查

### throughput

表 12-1：`throughput` 路由模式下的 group-level 稳定性检查。

| 平台 | 组别 | 轮数 | 成功轮数 | Token 级命中率 | 实际成本 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Infron | 1 | **35** | **35** | 91.38% | $0.08943200 |
| Infron | 2 | **45** | **45** | 89.15% | $0.06057000 |
| Infron | 3 | **48** | **48** | 98.80% | $0.05049400 |
| Infron | 4 | **48** | **48** | **99.95%** | **$0.04654400** |
| OpenRouter | 1 | **35** | **35** | **99.88%** | **$0.04520915** |
| OpenRouter | 2 | **45** | **45** | **94.61%** | **$0.04737048** |
| OpenRouter | 3 | **48** | **48** | **99.67%** | **$0.04923390** |
| OpenRouter | 4 | **48** | **48** | 99.88% | $0.05021018 |

### price

表 12-2：`price` 路由模式下的 group-level 稳定性检查。

| 平台 | 组别 | 轮数 | 成功轮数 | Token 级命中率 | 实际成本 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Infron | 1 | **44** | **44** | 98.09% | $0.09869600 |
| Infron | 2 | **48** | **48** | **97.65%** | $0.05995200 |
| Infron | 3 | **49** | **49** | 94.92% | $0.05723700 |
| Infron | 4 | **50** | **50** | 95.21% | $0.05672000 |
| OpenRouter | 1 | **44** | **44** | **99.88%** | **$0.04433152** |
| OpenRouter | 2 | **48** | **48** | 95.30% | **$0.05354946** |
| OpenRouter | 3 | **49** | **49** | **95.09%** | **$0.05252186** |
| OpenRouter | 4 | **50** | **50** | **99.87%** | **$0.04770922** |

### latency

表 12-3：`latency` 路由模式下的 group-level 稳定性检查。

| 平台 | 组别 | 轮数 | 成功轮数 | Token 级命中率 | 实际成本 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Infron | 1 | **50** | **50** | 99.72% | $0.05518500 |
| Infron | 2 | **50** | **50** | **99.95%** | **$0.04931200** |
| Infron | 3 | **50** | **50** | **99.95%** | **$0.04887600** |
| Infron | 4 | **50** | **50** | **99.94%** | **$0.04725600** |
| OpenRouter | 1 | **50** | **50** | **99.87%** | **$0.04770922** |
| OpenRouter | 2 | **50** | **50** | 99.88% | $0.04976566 |
| OpenRouter | 3 | **50** | **50** | 99.88% | $0.04933198 |
| OpenRouter | 4 | **50** | **50** | 99.87% | $0.04770922 |

### ttft

表 12-4：`ttft` 路由模式下的 group-level 稳定性检查。

| 平台 | 组别 | 轮数 | 成功轮数 | Token 级命中率 | 实际成本 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Infron | 1 | **50** | **50** | **99.94%** | **$0.04725600** |
| Infron | 2 | **50** | **50** | **99.95%** | **$0.04931200** |
| Infron | 3 | **50** | **50** | **99.95%** | **$0.04887600** |
| Infron | 4 | **50** | **50** | **99.94%** | **$0.04725600** |
| OpenRouter | 1 | **50** | **50** | 98.46% | $0.05062745 |
| OpenRouter | 2 | **50** | **50** | 99.88% | $0.04976566 |
| OpenRouter | 3 | **50** | **50** | 99.88% | $0.06879746 |
| OpenRouter | 4 | **50** | **50** | 99.87% | $0.04770922 |

## 10. 讨论：业务价值、适用边界与工程启示

四种 routing sort 对应不同业务目标，需要结合缓存、成本、吞吐、端到端时延和 TTFT 一起判断。`throughput` 更适合批处理、异步生成、长文本生产和离线任务；`price` 更适合高频低毛利调用、固定模板请求、客服/营销自动化等成本敏感场景；`latency` 更适合交互式产品、Agent 工具调用链、实时辅助写作和用户等待成本较高的场景；`ttft` 更适合首包体验敏感、需要快速给用户反馈的流式交互场景。

| 路由模式 | 主要业务目标 | 本轮数据体现 | 适用场景 | 注意事项 |
| --- | --- | --- | --- | --- |
| `throughput` | 最大化单位时间输出能力 | 缓存 OpenRouter 占优，成本 OpenRouter 占优，throughput OpenRouter 占优，latency OpenRouter 占优，TTFT OpenRouter 占优 | 批量内容生成、离线摘要、后台数据加工 | 速度和成本同时较强，但仍需确认缓存命中稳定性 |
| `price` | 最小化单位请求和单位 token 成本 | 缓存 OpenRouter 占优，成本 OpenRouter 占优，throughput OpenRouter 占优，latency OpenRouter 占优，TTFT OpenRouter 占优 | 高频模板化请求、客服自动化、营销触达、RAG 固定前缀 | 速度和成本同时较强，但仍需确认缓存命中稳定性 |
| `latency` | 最小化用户可感知等待时间 | 缓存 Infron 占优，成本 OpenRouter 占优，throughput OpenRouter 占优，latency OpenRouter 占优，TTFT OpenRouter 占优 | 在线聊天、Agent 调用链、IDE/写作辅助、实时运营工具 | 速度和成本同时较强，但仍需确认缓存命中稳定性 |
| `ttft` | 最小化流式首包响应时间 | 缓存 Infron 占优，成本 Infron 占优，throughput Infron 占优，latency Infron 占优，TTFT Infron 占优 | 流式聊天、实时 Copilot、首屏反馈、长思考任务的进度感知 | 更适合成本和体验受控的在线业务，但吞吐可能不是最优 |

从业务决策角度看，prompt caching 的价值不只体现在单次请求省钱，而是体现在大规模重复上下文请求的边际成本下降。若业务请求结构高度模板化，应优先关注 Token 级命中率和实际成本；若业务以用户实时体验为核心，应同时约束 latency；若业务为后台批量生成，则 throughput 可能比单请求 latency 更重要。

因此，本实验的推荐读法是：先确认 Input Tokens 是否完全可比，再按业务目标选择主指标，最后检查其他指标是否出现不可接受的副作用。例如某个平台吞吐更高但缓存命中显著较低，可能适合批处理，却未必适合需要稳定成本结构的高频在线业务。

## 11. 结论

表 13：路由模式级结论快照。该表综合缓存命中、成本、throughput、latency 和 TTFT，避免只按单一指标排序。

| 路由偏好 | 缓存命中更优 | 成本更低 | Throughput 更高 | Latency 更低 | TTFT 更低 | 综合解读 |
| --- | --- | --- | --- | --- | --- | --- |
| `throughput` | **OpenRouter** | **OpenRouter** | **OpenRouter** | **OpenRouter** | **OpenRouter** | OpenRouter 综合占优（5/5 可比指标） |
| `price` | **OpenRouter** | **OpenRouter** | **OpenRouter** | **OpenRouter** | **OpenRouter** | OpenRouter 综合占优（5/5 可比指标） |
| `latency` | **Infron** | **OpenRouter** | **OpenRouter** | **OpenRouter** | **OpenRouter** | OpenRouter 综合占优（4/5 可比指标） |
| `ttft` | **Infron** | **Infron** | **Infron** | **Infron** | **Infron** | Infron 综合占优（5/5 可比指标） |

## 12. 局限性、缺失数据与后续实验计划

本报告区分“已观测事实”和“机制解释”。已观测事实来自响应 usage、cost、latency、TTFT、cache tokens、provider 字段和导出的请求级 telemetry；机制解释用于说明这些结果背后的合理工程路径，不代表平台内部私有实现的直接证据。

表 14：当前报告的局限性与后续补充计划。

| 缺失或不足 | 对结论的影响 | 后续补充方式 | 当前处理方式 |
| --- | --- | --- | --- |
| 上游完整 routing trace | 无法逐跳证明每次请求的 provider 选择、fallback 和重试路径 | `待补充：provider routing trace / decision log / fallback reason` | 仅使用响应中真实返回的 provider 字段和 provider 分布做归因 |
| Provider cost breakdown 全量字段 | 无法进一步拆分平台费、provider 费、cache read/write 成本 | `待补充：provider cost breakdown 明细、缓存读写计费项` | 只统计响应明确返回的 cost/cost_details |
| 显著性检验 | 已补充 bootstrap 95% CI 与 paired sign-flip permutation test；尚未给出 standardized effect size | `待补充：Cohen's d / Cliff's delta 等 effect size` | 使用严格 A/B 配对和 input token 相等过滤降低混杂偏差 |
| P95/P99 latency | 已补充 P50/P95/P99 latency 与 TTFT；尚未计算 IQR 和 tail amplification | `待补充：IQR、max、tail amplification ratio` | 当前展示均值、P50/P95/P99 和过程曲线 |
| 多模型泛化 | 单模型实验不能直接外推到所有模型 | `待补充：覆盖更多模型家族与不同上下文窗口的跨模型实验` | 结论限定于 `minimax/minimax-m2.5` 本轮样本 |
| 真实业务语料 | 本轮使用内置代表性业务模板，不等同于客户生产语料 | `待补充：脱敏真实 RAG、Agent、客服、代码生成、长文摘要业务数据集` | 脚本已支持 `--dataset-file` JSONL 输入 |
| 并发压力与长期运行 | 本轮使用 `workers` 并发执行，但不是长时间 soak test | `待补充：并发阶梯压测、24h soak test、cache TTL/eviction 观测` | 当前解释 4*50 并发执行窗口内的 A/B 结果 |

后续实验可以继续采用核心 A/B 配对方法：保持 payload SHA256、`usage.prompt_tokens` 偏差不超过 50 tokens 的配对过滤和 request-level telemetry，同时增加 routing trace、provider cost breakdown、尾延迟分位数和业务语料分层。这样可以把本报告扩展为更完整的生产决策评估框架。


## 13. 可复现性附录：Benchmark 数据集

本节给出复现结论和图表所需的数据文件。配对级 CSV 是报告中所有总览表、核心指标图和结论快照的直接输入；请求级 JSONL 保留每一次 first/second 请求的原始 telemetry，便于审计 provider、usage、cost、latency、TTFT 与缓存字段。公开报告只保留这些数据文件的在线引用路径，不在正文中展开全量请求记录。

| 数据文件 | 粒度 | 行数 | SHA256 | 用途 |
| 中文 HTML 报告 | <https://infronai.github.io/prompt-cache-bench/experiments/minimax/minimax-m2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/reports/routing-cache-cost-streaming-performance-ab-study__minimax-m2-5__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-07.zh.html> |  |
| English HTML 报告 | <https://infronai.github.io/prompt-cache-bench/experiments/minimax/minimax-m2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/reports/routing-cache-cost-streaming-performance-ab-study__minimax-m2-5__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-07.en.html> |  |
| --- | ---: | ---: | --- | --- |
| <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/minimax/minimax-m2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/benchmark_pairs.csv> | A/B pair | 767 | `be6978f3485b539f5d36394ac1b0e680dc5631d3bafc6d90d0ffdc115fec0523` | 复现聚合表和核心图表 |
| <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/minimax/minimax-m2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/benchmark_requests.jsonl> | request | 3068 | `d86e6264bdd2e477ef0e018f398ff9a0ea500e33976dc82010d19c1a48e8e246` | 审计单次请求 telemetry |

字段字典：

| 字段 | 含义 |
| --- | --- |
| `sort/group/round` | A/B 配对键；同一键下 Infron 与 OpenRouter first/second 输入 token 偏差不超过 50 |
| `prompt_length_tier` | Prompt 长度分层标签；未启用分层时为 `default` |
| `target_prompt_tokens` | 该 tier 的目标 prompt token 规模；实际比较仍以响应返回的 `usage.prompt_tokens` 为准 |
| `*_pair_cost_usd` | first + second 两次请求的真实响应成本 |
| `*_avg_latency_ms` | first/second 两次请求 latency 均值 |
| `*_avg_ttft_ms` | first/second 两次请求 TTFT 均值 |
| `*_response_throughput_tps` | 两次请求 completion tokens / 两次请求总 latency seconds |
| `*_second_cache_read_tokens` | 第二次请求读取缓存的 token 数 |
| `*_second_cache_hit_rate` | 第二次请求 cache read tokens / 第二次请求 prompt tokens |
| `*_provider` | 响应中可观测的上游 provider 标识 |

## 14. 可复现性附录：源码、数据集与执行命令

### 14.1 测试源码引用路径

| 类型 | 路径 | 用途 |
|---|---|---|
| A/B 实验脚本 | <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/minimax/minimax-m2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/code/rerun_routing_sort_cache_cost_ab.py> | 负责请求构造、流式 TTFT 采集、usage/cost/cache telemetry 采集、A/B 配对过滤与基础 Markdown 输出 |
| 回归测试 | <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/minimax/minimax-m2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/code/test_rerun_routing_sort_cache_cost_ab.py> | 覆盖 A/B 配对过滤、成本口径、Prompt 长度分层、API 协议字段与报告关键结构 |

### 14.2 数据集与实验产物引用路径

| 类型 | 路径 | 说明 |
|---|---|---|
| 实验结果目录 | <https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/minimax/minimax-m2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data> | 本轮 minimax/minimax-m2.5 A/B 实验的完整输出目录 |
| 配对级数据集 | <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/minimax/minimax-m2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/benchmark_pairs.csv> | 767 个过滤后 A/B 配对样本，用于复现聚合表和核心图表 |
| 请求级数据集 | <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/minimax/minimax-m2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/benchmark_requests.jsonl> | 3068 次请求级 telemetry，用于审计 TTFT、latency、usage、cost、cache 与 provider 字段 |
| 过滤后记录 | <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/minimax/minimax-m2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/records.json> | 进入统计口径的过滤后原始记录 |
| 剔除样本审计 | <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/minimax/minimax-m2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/records_excluded.json> | 66 条剔除记录及原因：33 条 incomplete，33 条 unequal_input_tokens |
| Prompt 长度分层配置 | `short:1500,medium:8000,long:32000` | 用于比较不同 Prompt 长度下的缓存表现 |
| 数据集名称 | `business_representative` | 本轮使用脚本内置代表性业务 prompt 模板；未引入外部敏感业务语料 |

### 14.3 本轮执行命令

```bash
PYTHONPATH=src python3 scripts/rerun_routing_sort_cache_cost_ab.py --model minimax/minimax-m2.5 --groups 4 --rounds 50 --workers 24 --timeout 180 --stream --dataset-name business_representative --prompt-length-tiers short:1500,medium:8000,long:32000 --api-protocols chat_completions --reasoning-effort default --out-dir export/minimax_m25_all_experiments/routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260707_161700 --report export/minimax_m25_all_experiments/routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260707_161700-report-zh.md
```

### 14.4 校验命令

```bash
PYTHONPATH=src pytest -q tests/test_rerun_routing_sort_cache_cost_ab.py
```

本附录只保留源码、数据集、执行命令和审计文件的引用路径，不在报告正文中展开敏感配置、密钥、全量请求内容或平台内部字段。
