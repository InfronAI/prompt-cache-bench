# Infron 与 OpenRouter 路由、缓存、成本与流式性能 A/B 实验报告

## 摘要与结论大纲

**关键词**：Prompt Caching；A/B Testing；Provider Routing；Cache Affinity；Latency；Throughput；Cost Attribution；openai/gpt-4o-mini

### 摘要

本报告以 `openai/gpt-4o-mini` 为对象，对比 Infron 与 OpenRouter 在 Prompt Caching 场景下的路由策略、缓存命中、实际成本、吞吐量、TTFT 首包响应时间和端到端时延。实验包含 4 个实验组、每组 50 轮，覆盖 4 种 routing sort 策略；其中 TTFT First 中，Infron 使用 `provider.sort=ttft`，OpenRouter 使用其支持的 `provider.sort=latency` 作为对照。经过异常 usage、HTTP 异常和 A/B input tokens 偏差超过 50 tokens 的样本剔除后，最终保留 783 个配对样本、3132 次请求级观测记录，剔除 34 条记录。

核心结论是：在 `usage.prompt_tokens` 偏差不超过 50 tokens 的配对样本中，OpenRouter 在所有路由模式下，Token 级缓存命中率都更高；OpenRouter 在所有路由模式下，实际成本都更低；Infron 在 `throughput` 和 `latency` 模式下，吞吐量更高，OpenRouter 在 `price` 和 `ttft` 模式下，吞吐量更高；Infron 在 `throughput` 和 `latency` 模式下，时延更低，OpenRouter 在 `price` 和 `ttft` 模式下，时延更低；Infron 在 `throughput` 和 `latency` 模式下，TTFT 首包响应时间更低，OpenRouter 在 `price` 和 `ttft` 模式下，TTFT 首包响应时间更低。整体看，Infron 的优势集中在成本控制、部分模式的低时延路径，OpenRouter 的优势集中在缓存复用、成本控制、吞吐、TTFT、部分模式的端到端时延表现。平台选择应围绕业务目标展开，单一指标不足以代表整体效果。

本轮未显式控制 reasoning/thinking，响应中的 reasoning tokens 作为观测变量记录。

![Inference 平台不可能四角](gpt4o_mini_all_experiments/routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260706_104500_rerun/charts/inference_impossible_quadrilateral.svg)

图 0：Inference 平台“不可能四角”。吞吐量、价格、端到端时延和 TTFT 很难同时达到最优，平台路由通常会在四个方向之间做取舍；图中将四项归一化指标投影为路由模式点，并将同一平台的四个点连接成区域。

![结论总览图](gpt4o_mini_all_experiments/routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260706_104500_rerun/charts/conclusion_overview.svg)

图 A：结论总览图。上方卡片概括跨路由模式的总体胜出方，下方矩阵按 throughput、price、latency、TTFT 的路由目标顺序组织列，金色对角线表示各路由模式目标指标的 A/B 胜出方。

### 结论大纲

| 研究维度 | 结论 | 证据位置 |
| --- | --- | --- |
| 控制变量 | 进入统计的 A/B 样本满足同一 `sort/group/round` 下 first/second 请求 `usage.prompt_tokens` 各自偏差不超过 50 tokens；各模式 Input Tokens 对照为 `throughput`=6262980/6262980；`price`=6262980/6262980；`latency`=5713910/5713910；`ttft`=6262980/6262980 | 方法与数据质量章节 |
| 缓存复用 | OpenRouter 在所有路由模式下，Token 级缓存命中率都更高，说明本轮 provider stick/cache affinity 已转化为可观测的缓存命中差异 | 结果与机制分析章节 |
| 实际成本 | OpenRouter 在所有路由模式下，实际成本都更低，成本差异与 cache read tokens 同向变化 | 结果与结论章节 |
| 性能表现 | Infron 在 `throughput` 和 `latency` 模式下，吞吐量更高，OpenRouter 在 `price` 和 `ttft` 模式下，吞吐量更高；Infron 在 `throughput` 和 `latency` 模式下，时延更低，OpenRouter 在 `price` 和 `ttft` 模式下，时延更低；Infron 在 `throughput` 和 `latency` 模式下，TTFT 首包响应时间更低，OpenRouter 在 `price` 和 `ttft` 模式下，TTFT 首包响应时间更低 | 结果可视化与结论章节 |
| Reasoning 控制 | 本轮未显式控制 reasoning/thinking，响应中的 reasoning tokens 作为观测变量记录。 | Reasoning / Thinking 控制校验章节 |
| 归因边界 | 报告只使用响应可观测 telemetry，包括 provider 字段、usage、cost breakdown、TTFT、latency 和 cache tokens；未把平台内部私有 routing trace 当作已观测事实 | 机制分析、下钻分析与局限性章节 |
| 业务含义 | 对稳定长上下文、RAG 前缀、Agent 工具说明和批处理任务，缓存命中率与成本可预测性是核心收益；对实时交互任务，latency 仍需作为独立约束 | 讨论与结论章节 |

### 路由模式级结论

#### Throughput First

| 指标 | Infron / OpenRouter 并列对比 | 胜出方 |
| --- | --- | --- |
| 缓存命中率 | <span class="provider-label">Infron</span>████████ 97.23%<br><span class="provider-label">OpenRouter</span>**████████ 98.15%** | **OpenRouter**（高 0.95%） |
| 实际成本 | <span class="provider-label">Infron</span>████████ $0.70693500<br><span class="provider-label">OpenRouter</span>**██████░░ $0.49990860** | **OpenRouter**（低 29.29%） |
| Throughput | <span class="provider-label">Infron</span>**████████ 4.96 tok/s**<br><span class="provider-label">OpenRouter</span>███████░ 4.59 tok/s | **Infron**（高 7.91%） |
| Latency | <span class="provider-label">Infron</span>**███████░ 2664.97 ms**<br><span class="provider-label">OpenRouter</span>████████ 2898.56 ms | **Infron**（低 8.06%） |
| TTFT | <span class="provider-label">Infron</span>**███████░ 2282.74 ms**<br><span class="provider-label">OpenRouter</span>████████ 2626.91 ms | **Infron**（低 13.10%） |

#### Price First

| 指标 | Infron / OpenRouter 并列对比 | 胜出方 |
| --- | --- | --- |
| 缓存命中率 | <span class="provider-label">Infron</span>████████ 98.21%<br><span class="provider-label">OpenRouter</span>**████████ 98.26%** | **OpenRouter**（高 0.05%） |
| 实际成本 | <span class="provider-label">Infron</span>████████ $0.70694600<br><span class="provider-label">OpenRouter</span>**█████░░░ $0.47874300** | **OpenRouter**（低 32.28%） |
| Throughput | <span class="provider-label">Infron</span>████████ 4.74 tok/s<br><span class="provider-label">OpenRouter</span>**████████ 5.00 tok/s** | **OpenRouter**（高 5.45%） |
| Latency | <span class="provider-label">Infron</span>████████ 2799.51 ms<br><span class="provider-label">OpenRouter</span>**████████ 2658.69 ms** | **OpenRouter**（低 5.03%） |
| TTFT | <span class="provider-label">Infron</span>████████ 2424.80 ms<br><span class="provider-label">OpenRouter</span>**████████ 2379.53 ms** | **OpenRouter**（低 1.87%） |

#### Latency First

| 指标 | Infron / OpenRouter 并列对比 | 胜出方 |
| --- | --- | --- |
| 缓存命中率 | <span class="provider-label">Infron</span>████████ 97.45%<br><span class="provider-label">OpenRouter</span>**████████ 98.92%** | **OpenRouter**（高 1.51%） |
| 实际成本 | <span class="provider-label">Infron</span>████████ $0.64497600<br><span class="provider-label">OpenRouter</span>**█████░░░ $0.43595370** | **OpenRouter**（低 32.41%） |
| Throughput | <span class="provider-label">Infron</span>**████████ 4.93 tok/s**<br><span class="provider-label">OpenRouter</span>████████ 4.72 tok/s | **Infron**（高 4.54%） |
| Latency | <span class="provider-label">Infron</span>**████████ 2687.86 ms**<br><span class="provider-label">OpenRouter</span>████████ 2826.35 ms | **Infron**（低 4.90%） |
| TTFT | <span class="provider-label">Infron</span>**███████░ 2318.86 ms**<br><span class="provider-label">OpenRouter</span>████████ 2574.86 ms | **Infron**（低 9.94%） |

#### TTFT First

| 指标 | Infron / OpenRouter 并列对比 | 胜出方 |
| --- | --- | --- |
| 缓存命中率 | <span class="provider-label">Infron</span>████████ 98.21%<br><span class="provider-label">OpenRouter</span>**████████ 99.42%** | **OpenRouter**（高 1.23%） |
| 实际成本 | <span class="provider-label">Infron</span>████████ $0.94275300<br><span class="provider-label">OpenRouter</span>**████░░░░ $0.47849820** | **OpenRouter**（低 49.24%） |
| Throughput | <span class="provider-label">Infron</span>████████ 4.67 tok/s<br><span class="provider-label">OpenRouter</span>**████████ 4.96 tok/s** | **OpenRouter**（高 6.30%） |
| Latency | <span class="provider-label">Infron</span>████████ 2953.82 ms<br><span class="provider-label">OpenRouter</span>**███████░ 2673.45 ms** | **OpenRouter**（低 9.49%） |
| TTFT | <span class="provider-label">Infron</span>████████ 2613.21 ms<br><span class="provider-label">OpenRouter</span>**███████░ 2428.65 ms** | **OpenRouter**（低 7.06%） |

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

![实验流程图](gpt4o_mini_all_experiments/routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260706_104500_rerun/charts/experiment_flow.svg)

图 1：实验流水线。该图强调每个 routing sort 下的同源 payload、双平台请求和 first/second request 配对关系，用于说明实验如何构造可比样本。

A/B 配对过滤的目标是确保比较只发生在输入 token 规模足够接近的样本上。只有 first request 与 second request 的 `usage.prompt_tokens` 在两边各自偏差不超过 50 tokens，样本才进入最终统计。

![A/B 配对过滤图](gpt4o_mini_all_experiments/routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260706_104500_rerun/charts/ab_pairing.svg)

图 2：A/B 配对过滤逻辑。该图明确展示异常 usage、HTTP 异常、非完整配对和 input tokens 不一致样本如何被排除，保证最终对比符合控制变量要求。

核心请求 payload 结构如下。实验固定模型、温度、最大输出 token、usage 返回和 provider sort，只改变路由优先模式。

```json
{
  "model": "openai/gpt-4o-mini",
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
| 测试模型 | `openai/gpt-4o-mini` |
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
| 结果目录 | `export/gpt4o_mini_all_experiments/routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260706_104500_rerun/` |
| 剔除规则 | HTTP 非 200、请求异常、任一请求 `usage.prompt_tokens <= 0`、或同一 `sort/group/round` 下 A/B 两边 first/second `usage.prompt_tokens` 偏差超过 50 tokens 的轮次不进入统计 |
| 剔除记录数 | 34 条 |
| `throughput` payload SHA256 | Infron `33309581c6c2716b36afc5200461d0aba0834a68e81951ef06d22bd913c888a9`<br>OpenRouter `33309581c6c2716b36afc5200461d0aba0834a68e81951ef06d22bd913c888a9` |
| `price` payload SHA256 | Infron `0d4e123c180d0c338ccd3c08ceaa8778c659446be4affeb1a583199ae2b19ace`<br>OpenRouter `0d4e123c180d0c338ccd3c08ceaa8778c659446be4affeb1a583199ae2b19ace` |
| `latency` payload SHA256 | Infron `c2dd36fa2e40cc43d90288e0c544dfe4ee4cf0516cf60de029572965a322b638`<br>OpenRouter `c2dd36fa2e40cc43d90288e0c544dfe4ee4cf0516cf60de029572965a322b638` |
| `ttft` payload SHA256 | Infron `29aec12b32e0e071a408761cf353b9dea09bd6c8699ad5deaf349f6f42622443`<br>OpenRouter `c2dd36fa2e40cc43d90288e0c544dfe4ee4cf0516cf60de029572965a322b638` |

说明：A/B 控制变量是同一 routing sort 下发送给 Infron 和 OpenRouter 的请求 payload。总览中的 Input Tokens 按响应返回的 `usage.prompt_tokens` 汇总，代表各平台实际统计和计费口径下处理的输入 token 量。

## 4. 结果：总体指标与主要发现

说明：本节的 throughput、latency 和 TTFT 均为响应级整体指标。若响应 usage 中 `completion_tokens` 包含 reasoning tokens，则 reasoning 过程已纳入 throughput 分子；请求 latency 是完整响应端到端耗时，天然包含 reasoning 过程耗时；TTFT 是 streaming 下首个 SSE token/chunk 到达时间，代表首包响应体验。成本只使用响应明确返回的 cost 字段；未返回 cost 时标记为 `N/A`，不视为 0。

表 4：总体 A/B 指标对比。加粗单元表示同一 routing sort 下表现更好的一方；Input Tokens 加粗表示两边严格相等。

| 路由偏好 | 平台 | 总轮数 | 成功轮数 | 总 Input Tokens (`usage.prompt_tokens`) | 调用级命中率 | Token 级命中率 | 实际总成本 | 平均每轮成本 | 平均响应 throughput（含 reasoning） | 平均 latency/请求（含 reasoning） | 平均 TTFT | HTTP 状态 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `throughput` | Infron | **200** | **200** | **6262980** | 96.50% | 97.23% | $0.70693500 | $0.00353467 | **4.96 response tok/s** | **2664.97 ms** | **2282.74 ms** | **200** |
| `throughput` | OpenRouter | **200** | **200** | **6262980** | **98.50%** | **98.15%** | **$0.49990860** | **$0.00249954** | 4.59 response tok/s | 2898.56 ms | 2626.91 ms | **200** |
| `price` | Infron | **200** | **200** | **6262980** | 99.00% | 98.21% | $0.70694600 | $0.00353473 | 4.74 response tok/s | 2799.51 ms | 2424.80 ms | **200** |
| `price` | OpenRouter | **200** | **200** | **6262980** | **99.50%** | **98.26%** | **$0.47874300** | **$0.00239371** | **5.00 response tok/s** | **2658.69 ms** | **2379.53 ms** | **200** |
| `latency` | Infron | **183** | **183** | **5713910** | **97.81%** | 97.45% | $0.64497600 | $0.00352446 | **4.93 response tok/s** | **2687.86 ms** | **2318.86 ms** | **200** |
| `latency` | OpenRouter | **183** | **183** | **5713910** | **97.81%** | **98.92%** | **$0.43595370** | **$0.00238226** | 4.72 response tok/s | 2826.35 ms | 2574.86 ms | **200** |
| `ttft` | Infron | **200** | **200** | **6262980** | 99.00% | 98.21% | $0.94275300 | $0.00471376 | 4.67 response tok/s | 2953.82 ms | 2613.21 ms | **200** |
| `ttft` | OpenRouter | **200** | **200** | **6262980** | **100.00%** | **99.42%** | **$0.47849820** | **$0.00239249** | **4.96 response tok/s** | **2673.45 ms** | **2428.65 ms** | **200** |

### 4.1 尾延迟与显著性检验

表 5：尾延迟分位数。P95/P99 直接从请求级 latency 与 TTFT 计算，补充均值无法表达的尾部风险。

| 路由偏好 | 平台 | P50 Latency | P95 Latency | P99 Latency | P50 TTFT | P95 TTFT | P99 TTFT |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `throughput` | Infron | 2516.64 ms | **4167.37 ms** | **5434.68 ms** | **2152.59 ms** | **3932.18 ms** | **5177.68 ms** |
| `throughput` | OpenRouter | **2513.93 ms** | 5435.19 ms | 9738.89 ms | 2208.28 ms | 5156.10 ms | 9322.69 ms |
| `price` | Infron | 2570.86 ms | **4278.14 ms** | **5698.60 ms** | 2217.30 ms | **3909.23 ms** | **5224.94 ms** |
| `price` | OpenRouter | **2362.01 ms** | 5002.43 ms | 9347.08 ms | **2019.33 ms** | 4297.25 ms | 9229.51 ms |
| `latency` | Infron | **2481.07 ms** | **3847.75 ms** | **6411.37 ms** | **2167.90 ms** | **3286.72 ms** | **5658.62 ms** |
| `latency` | OpenRouter | 2496.38 ms | 4092.67 ms | 12208.70 ms | 2189.41 ms | 3902.63 ms | 11948.58 ms |
| `ttft` | Infron | 2530.45 ms | 4988.93 ms | **7625.37 ms** | **2186.28 ms** | 4438.47 ms | **7033.97 ms** |
| `ttft` | OpenRouter | **2456.57 ms** | **4203.69 ms** | 10554.81 ms | 2235.94 ms | **3770.17 ms** | 10363.93 ms |

表 6：配对统计检验。均值差使用 bootstrap 95% CI，p-value 使用 paired sign-flip permutation test。指标名给出差值方向，解释列说明正值代表的含义。

| 路由偏好 | 指标 | 均值差 | 95% CI | p-value | 配对数 | 解释 |
| --- | --- | ---: | --- | ---: | ---: | --- |
| `throughput` | Latency: OpenRouter - Infron | 467.18 ms | [201.55 ms, 774.40 ms] | 0.0030 | 200 | 正值表示 Infron latency 更低 |
| `throughput` | TTFT: OpenRouter - Infron | 688.35 ms | [438.99 ms, 980.68 ms] | <0.001 | 200 | 正值表示 Infron TTFT 更低 |
| `throughput` | Throughput: Infron - OpenRouter | 0.0842 tok/s | [-0.1132 tok/s, 0.2943 tok/s] | 0.4261 | 200 | 正值表示 Infron throughput 更高 |
| `throughput` | Cost: OpenRouter - Infron | $-0.00103513 | [$-0.00119770, $-0.00088765] | <0.001 | 200 | 正值表示 Infron 成本更低 |
| `throughput` | Token Cache Hit: Infron - OpenRouter | -1.96 pp | [-4.91 pp, 0.95 pp] | 0.2249 | 200 | 正值表示 Infron cache hit 更高 |
| `price` | Latency: OpenRouter - Infron | -281.64 ms | [-628.06 ms, 68.68 ms] | 0.1150 | 200 | 正值表示 Infron latency 更低 |
| `price` | TTFT: OpenRouter - Infron | -90.53 ms | [-432.87 ms, 245.01 ms] | 0.6048 | 200 | 正值表示 Infron TTFT 更低 |
| `price` | Throughput: Infron - OpenRouter | -0.3086 tok/s | [-0.5217 tok/s, -0.0782 tok/s] | 0.0082 | 200 | 正值表示 Infron throughput 更高 |
| `price` | Cost: OpenRouter - Infron | $-0.00114101 | [$-0.00130024, $-0.00098501] | <0.001 | 200 | 正值表示 Infron 成本更低 |
| `price` | Token Cache Hit: Infron - OpenRouter | -0.47 pp | [-1.96 pp, 1.03 pp] | 1.0000 | 200 | 正值表示 Infron cache hit 更高 |
| `latency` | Latency: OpenRouter - Infron | 276.99 ms | [-226.31 ms, 867.97 ms] | 0.3522 | 183 | 正值表示 Infron latency 更低 |
| `latency` | TTFT: OpenRouter - Infron | 512.00 ms | [10.69 ms, 1104.36 ms] | 0.0655 | 183 | 正值表示 Infron TTFT 更低 |
| `latency` | Throughput: Infron - OpenRouter | -0.0064 tok/s | [-0.2113 tok/s, 0.1961 tok/s] | 0.9493 | 183 | 正值表示 Infron throughput 更高 |
| `latency` | Cost: OpenRouter - Infron | $-0.00114220 | [$-0.00130168, $-0.00098122] | <0.001 | 183 | 正值表示 Infron 成本更低 |
| `latency` | Token Cache Hit: Infron - OpenRouter | -0.06 pp | [-3.21 pp, 3.06 pp] | 0.8068 | 183 | 正值表示 Infron cache hit 更高 |
| `ttft` | Latency: OpenRouter - Infron | -560.74 ms | [-1118.01 ms, -66.84 ms] | 0.0275 | 200 | 正值表示 Infron latency 更低 |
| `ttft` | TTFT: OpenRouter - Infron | -369.13 ms | [-925.25 ms, 116.37 ms] | 0.1752 | 200 | 正值表示 Infron TTFT 更低 |
| `ttft` | Throughput: Infron - OpenRouter | -0.0991 tok/s | [-0.3251 tok/s, 0.1311 tok/s] | 0.4059 | 200 | 正值表示 Infron throughput 更高 |
| `ttft` | Cost: OpenRouter - Infron | $-0.00232127 | [$-0.00264128, $-0.00201815] | <0.001 | 200 | 正值表示 Infron 成本更低 |
| `ttft` | Token Cache Hit: Infron - OpenRouter | -0.97 pp | [-2.43 pp, 0.00 pp] | 0.5069 | 200 | 正值表示 Infron cache hit 更高 |

### 4.2 Reasoning / Thinking 控制校验

表 7：Reasoning telemetry 观测。本轮未显式指定 reasoning/thinking 参数，保留模型与平台默认行为；该表用于记录默认行为下的 reasoning tokens 和首 reasoning token 观测。

| 路由偏好 | 平台 | Reasoning Tokens | 平均 Reasoning Tokens/请求 | Reasoning 请求数 | 平均首 Reasoning Token | 平均 TTFT | 平均端到端 E2E 时延 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `throughput` | Infron | **0** | **0.0000** | **0** | **0.00 ms** | **2282.74 ms** | **2664.97 ms** |
| `throughput` | OpenRouter | **0** | **0.0000** | **0** | **0.00 ms** | 2626.91 ms | 2898.56 ms |
| `price` | Infron | **0** | **0.0000** | **0** | **0.00 ms** | 2424.80 ms | 2799.51 ms |
| `price` | OpenRouter | **0** | **0.0000** | **0** | **0.00 ms** | **2379.53 ms** | **2658.69 ms** |
| `latency` | Infron | **0** | **0.0000** | **0** | **0.00 ms** | **2318.86 ms** | **2687.86 ms** |
| `latency` | OpenRouter | **0** | **0.0000** | **0** | **0.00 ms** | 2574.86 ms | 2826.35 ms |
| `ttft` | Infron | **0** | **0.0000** | **0** | **0.00 ms** | 2613.21 ms | 2953.82 ms |
| `ttft` | OpenRouter | **0** | **0.0000** | **0** | **0.00 ms** | **2428.65 ms** | **2673.45 ms** |

本轮 Reasoning / Thinking 控制：请求未显式指定 reasoning effort，保留模型与平台默认 thinking/reasoning 行为；响应 usage 中的 reasoning tokens 作为观测变量记录。


### 4.3 API 协议记录

本轮 API 协议为 `/v1/chat/completions`；本表记录两家平台在该协议下的 HTTP 成功、usage、token usage、成本和缓存 telemetry 覆盖。加粗单元表示覆盖率更高的一方。

| API 协议 | Endpoint | 平台 | 配对轮数 | 请求数 | 成功率 | Usage 覆盖 | Token Usage 覆盖 | 成本覆盖 | 缓存 Telemetry 覆盖 | HTTP 状态 | 主要错误 |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `chat_completions` | `/v1/chat/completions` | Infron | 800 | 1600 | 98.25% | **100.00%** | **100.00%** | **100.00%** | **100.00%** | `{"0":28,"200":1572}` | 14 x [Errno 54] Connection reset by peer<br>13 x [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1000) |
| `chat_completions` | `/v1/chat/completions` | OpenRouter | 800 | 1600 | **100.00%** | **100.00%** | **100.00%** | **100.00%** | **100.00%** | `{"200":1600}` |  |


## 5. 结果可视化：按路由模式的核心指标变化

说明：本节按路由模式组织图表。每张图对应一种 First 路由模式，并在同一图内对比 Infron 与 OpenRouter 的 latency、TTFT、throughput、实际成本和 Token 级缓存命中率，方便观察同一模式下的 A/B 指标差异。本轮已启用 streaming，并采集 TTFT、首内容 token 与首 reasoning token 时间；TTFT 代表首包响应体验，latency 代表完整响应体验。

### Throughput First 路由模式

![Throughput First 路由模式下的核心指标 A/B 对比](gpt4o_mini_all_experiments/routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260706_104500_rerun/charts/throughput_first.svg)

图 3：Throughput First 路由模式下的核心指标对比。柱状图同时呈现缓存、成本、吞吐、TTFT 和 latency 表现。

![Throughput First 路由模式下的综合雷达图](gpt4o_mini_all_experiments/routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260706_104500_rerun/charts/throughput_first_radar.svg)

图 4：Throughput First 路由模式下的综合雷达图。所有轴都按“越外圈越好”归一化，便于快速比较两家平台的综合形状。

![Throughput First 路由模式下的指标生成过程对比曲线](gpt4o_mini_all_experiments/routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260706_104500_rerun/charts/throughput_first_curves.svg)

图 5：Throughput First 路由模式下的指标生成过程曲线。该图用于观察指标随 group/round 的变化，而不只依赖均值。

### Price First 路由模式

![Price First 路由模式下的核心指标 A/B 对比](gpt4o_mini_all_experiments/routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260706_104500_rerun/charts/price_first.svg)

图 6：Price First 路由模式下的核心指标对比。柱状图同时呈现缓存、成本、吞吐、TTFT 和 latency 表现。

![Price First 路由模式下的综合雷达图](gpt4o_mini_all_experiments/routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260706_104500_rerun/charts/price_first_radar.svg)

图 7：Price First 路由模式下的综合雷达图。所有轴都按“越外圈越好”归一化，便于快速比较两家平台的综合形状。

![Price First 路由模式下的指标生成过程对比曲线](gpt4o_mini_all_experiments/routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260706_104500_rerun/charts/price_first_curves.svg)

图 8：Price First 路由模式下的指标生成过程曲线。该图用于观察指标随 group/round 的变化，而不只依赖均值。

### Latency First 路由模式

![Latency First 路由模式下的核心指标 A/B 对比](gpt4o_mini_all_experiments/routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260706_104500_rerun/charts/latency_first.svg)

图 9：Latency First 路由模式下的核心指标对比。柱状图同时呈现缓存、成本、吞吐、TTFT 和 latency 表现。

![Latency First 路由模式下的综合雷达图](gpt4o_mini_all_experiments/routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260706_104500_rerun/charts/latency_first_radar.svg)

图 10：Latency First 路由模式下的综合雷达图。所有轴都按“越外圈越好”归一化，便于快速比较两家平台的综合形状。

![Latency First 路由模式下的指标生成过程对比曲线](gpt4o_mini_all_experiments/routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260706_104500_rerun/charts/latency_first_curves.svg)

图 11：Latency First 路由模式下的指标生成过程曲线。该图用于观察指标随 group/round 的变化，而不只依赖均值。

### TTFT First 路由模式

![TTFT First 路由模式下的核心指标 A/B 对比](gpt4o_mini_all_experiments/routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260706_104500_rerun/charts/ttft_first.svg)

图 12：TTFT First 路由模式下的核心指标对比。柱状图同时呈现缓存、成本、吞吐、TTFT 和 latency 表现。

![TTFT First 路由模式下的综合雷达图](gpt4o_mini_all_experiments/routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260706_104500_rerun/charts/ttft_first_radar.svg)

图 13：TTFT First 路由模式下的综合雷达图。所有轴都按“越外圈越好”归一化，便于快速比较两家平台的综合形状。

![TTFT First 路由模式下的指标生成过程对比曲线](gpt4o_mini_all_experiments/routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260706_104500_rerun/charts/ttft_first_curves.svg)

图 14：TTFT First 路由模式下的指标生成过程曲线。该图用于观察指标随 group/round 的变化，而不只依赖均值。

说明：TTFT First 中，Infron 使用 `provider.sort=ttft`；OpenRouter 使用 `provider.sort=latency` 作为可支持的对照策略。

## 6. Infron 技术架构与缓存/成本机制解释

本节使用本次 benchmark 的可观测结果解释 Infron 在高 cache rate 与成本控制上的工程路径。需要说明的是，报告没有采集 Infron 内部私有 routing trace；因此下文把响应中真实返回的 provider 分布、cache read tokens、cost breakdown 和 latency/throughput 指标作为证据，用架构图解释这些结果背后的合理机制。

### 6.1 多 provider 路由与可观测控制面

Infron 对外提供 OpenAI-compatible API，对内需要在多个上游 provider、模型部署和路由策略之间做选择。对 prompt caching 工作负载而言，路由层不只是选择一个可用 provider，还需要同时考虑缓存亲和性、健康状态、成本、吞吐和时延目标。

![Infron 多 provider 路由架构](gpt4o_mini_all_experiments/routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260706_104500_rerun/charts/infron_architecture.svg)

图 12：Infron 多 provider 路由与缓存控制面。该图用于说明请求从统一 API 入口进入后，路由控制面如何在健康状态、策略目标、provider 选择和缓存域之间形成决策链路。

本次实验中，Infron 在不同 routing sort 下呈现出可观测的 provider 分布：`throughput` 主要路由到 `azure`（100.00%）；`price` 主要路由到 `azure`（100.00%）；`latency` 主要路由到 `azure`（100.00%）；`ttft` 主要路由到 `openai`（100.00%）。这种模式说明路由结果不是完全随机扩散，而是围绕路由目标形成了较稳定的 provider 选择。稳定的 provider 选择是高缓存命中率的前提，因为 prompt cache 通常与具体 provider、模型部署或缓存域绑定。

### 6.2 Provider Stick 与 Cache Affinity

Provider stick 是多 provider 网关中的缓存亲和策略：当请求具有相同或高度稳定的 prompt prefix 时，路由层倾向于把同一类请求送往同一个健康 provider 或缓存域，以减少缓存碎片化。它不等于固定永不切换 provider；当上游不可用、限流或 SLA 风险升高时，路由仍应回退到其他健康路径。

![Provider stick 与 cache affinity](gpt4o_mini_all_experiments/routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260706_104500_rerun/charts/provider_stick_cache_affinity.svg)

图 13：Provider stick 与 cache affinity 机制。该图表达的是工程机制假设：同类请求在健康 provider 集合内保持缓存亲和，可减少跨 provider/cache domain 的缓存碎片。

本次实验中，Infron 的缓存命中优势并非在所有 routing sort 下都成立：`throughput` OpenRouter；`price` OpenRouter；`latency` OpenRouter；`ttft` OpenRouter。这说明 provider stick/cache affinity 的收益依赖具体路由目标和最终上游路径。对于相同 stable prefix 的连续双请求，若 first/second 请求稳定落在同一缓存域，第二次请求更容易读取第一次请求写入或刷新后的 KV/cache 状态；若请求跨 provider、跨部署或落到不充分支持该缓存口径的路径，同样的 prompt 也可能需要分别暖缓存，从而降低整体 cache read tokens。

### 6.3 成本控制路径

成本控制来自三层叠加：第一层是缓存命中降低重复 prefill 的有效处理成本；第二层是 provider routing 在健康 provider 集合内选择更合适的成本路径；第三层是输出 token 与 reasoning token 对总成本的影响。本次实验中，实际成本胜出方为：`throughput` OpenRouter；`price` OpenRouter；`latency` OpenRouter；`ttft` OpenRouter。这说明缓存亲和、provider 单价、输出 token 数和 reasoning 执行情况会共同影响单位请求成本，不能只用 cache hit rate 单独解释成本结果。

![Infron 成本控制路径](gpt4o_mini_all_experiments/routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260706_104500_rerun/charts/infron_cost_control.svg)

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
| `throughput` | Infron | **200** | **6262980** | 97.23% | $0.70693500 | $0.000113 | **4.96 response tok/s** | **2282.74 ms** | **2664.97 ms** | 速度路径更激进，优先低时延/高吞吐 |
| `throughput` | OpenRouter | **200** | **6262980** | **98.15%** | **$0.49990860** | **$0.000080** | 4.59 response tok/s | 2626.91 ms | 2898.56 ms | 缓存亲和度高，成本控制更强 |
| `price` | Infron | **200** | **6262980** | 98.21% | $0.70694600 | $0.000113 | 4.74 response tok/s | 2424.80 ms | 2799.51 ms | 表现均衡但无单项极值 |
| `price` | OpenRouter | **200** | **6262980** | **98.26%** | **$0.47874300** | **$0.000076** | **5.00 response tok/s** | **2379.53 ms** | **2658.69 ms** | 缓存、成本、速度指标同时占优 |
| `latency` | Infron | **183** | **5713910** | 97.45% | $0.64497600 | $0.000113 | **4.93 response tok/s** | **2318.86 ms** | **2687.86 ms** | 速度路径更激进，优先低时延/高吞吐 |
| `latency` | OpenRouter | **183** | **5713910** | **98.92%** | **$0.43595370** | **$0.000076** | 4.72 response tok/s | 2574.86 ms | 2826.35 ms | 缓存亲和度高，成本控制更强 |
| `ttft` | Infron | **200** | **6262980** | 98.21% | $0.94275300 | $0.000151 | 4.67 response tok/s | 2613.21 ms | 2953.82 ms | 表现均衡但无单项极值 |
| `ttft` | OpenRouter | **200** | **6262980** | **99.42%** | **$0.47849820** | **$0.000076** | **4.96 response tok/s** | **2428.65 ms** | **2673.45 ms** | 缓存、成本、速度指标同时占优 |

### 上游 Provider 分布

表 9：上游 provider 归因覆盖率总览。`总请求数` 是 first/second 请求级计数；`已归因请求数` 表示响应中可提取到 provider 标识的请求数。

| 路由偏好 | 平台 | 总请求数 | 已归因请求数 | 归因覆盖率 | Provider 分布 | Cost breakdown 请求数 |
| --- | ---: | ---: | ---: | ---: | --- | ---: |
| `throughput` | Infron | 400 | 400 | 100.00% | azure: 400 (100.00%) | 400 |
| `throughput` | OpenRouter | 400 | 400 | 100.00% | OpenAI: 398 (99.50%), Azure: 2 (0.50%) | 400 |
| `price` | Infron | 400 | 400 | 100.00% | azure: 400 (100.00%) | 400 |
| `price` | OpenRouter | 400 | 400 | 100.00% | OpenAI: 399 (99.75%), Azure: 1 (0.25%) | 400 |
| `latency` | Infron | 366 | 366 | 100.00% | azure: 366 (100.00%) | 366 |
| `latency` | OpenRouter | 366 | 366 | 100.00% | OpenAI: 334 (91.26%), Azure: 32 (8.74%) | 366 |
| `ttft` | Infron | 400 | 400 | 100.00% | openai: 400 (100.00%) | 400 |
| `ttft` | OpenRouter | 400 | 400 | 100.00% | OpenAI: 364 (91.00%), Azure: 36 (9.00%) | 400 |

表 10：上游 provider 明细分布。该表按 provider 拆分请求占比、first/second 分布、覆盖轮次、时延、TTFT、token、cache 和成本，用于定位最终 A/B 差异来自哪个上游路径。

| 路由偏好 | 平台 | 上游 Provider | 请求数 | 占比 | first/second | 覆盖轮次 | Avg TTFT | Avg Latency | Prompt Tokens | Completion Tokens | Reasoning Tokens | Cache Read Tokens | 观测成本 | Cost breakdown 请求数 |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `throughput` | Infron | `azure` | 400 | 100.00% | 200/200 | 200 | 2282.74 ms | 2664.97 ms | 6262980 | 5282 | 0 | 5734784 | $0.70693500 | 400 |
| `throughput` | OpenRouter | `OpenAI` | 398 | 99.50% | 200/198 | 200 | 2594.15 ms | 2866.64 ms | 6259444 | 5302 | 0 | 5903104 | $0.49936500 | 398 |
| `throughput` | OpenRouter | `Azure` | 2 | 0.50% | 0/2 | 2 | 9146.59 ms | 9249.89 ms | 3536 | 22 | 0 | 0 | $0.00054360 | 2 |
| `price` | Infron | `azure` | 400 | 100.00% | 200/200 | 200 | 2424.80 ms | 2799.51 ms | 6262980 | 5304 | 0 | 6077952 | $0.70694600 | 400 |
| `price` | OpenRouter | `OpenAI` | 399 | 99.75% | 200/199 | 200 | 2362.38 ms | 2641.95 ms | 6261213 | 5296 | 0 | 6183552 | $0.47859315 | 399 |
| `price` | OpenRouter | `Azure` | 1 | 0.25% | 0/1 | 1 | 9222.77 ms | 9338.83 ms | 1767 | 16 | 0 | 1664 | $0.00014985 | 1 |
| `latency` | Infron | `azure` | 366 | 100.00% | 183/183 | 183 | 2318.86 ms | 2687.86 ms | 5713910 | 4852 | 0 | 5564928 | $0.64497600 | 366 |
| `latency` | OpenRouter | `OpenAI` | 334 | 91.26% | 167/167 | 167 | 2601.10 ms | 2864.40 ms | 5657366 | 4368 | 0 | 5607552 | $0.43065930 | 334 |
| `latency` | OpenRouter | `Azure` | 32 | 8.74% | 16/16 | 16 | 2301.06 ms | 2429.17 ms | 56544 | 512 | 0 | 46592 | $0.00529440 | 32 |
| `ttft` | Infron | `openai` | 400 | 100.00% | 200/200 | 200 | 2613.21 ms | 2953.82 ms | 6262980 | 5513 | 0 | 5887488 | $0.94275300 | 400 |
| `ttft` | OpenRouter | `OpenAI` | 364 | 91.00% | 182/182 | 182 | 2448.68 ms | 2702.23 ms | 6199368 | 4728 | 0 | 6130176 | $0.47297880 | 364 |
| `ttft` | OpenRouter | `Azure` | 36 | 9.00% | 18/18 | 18 | 2226.13 ms | 2382.45 ms | 63612 | 576 | 0 | 58240 | $0.00551940 | 36 |

### 7.1 缓存命中率与实际成本反向表现下钻

本节专门解释两个问题：第一，为什么某些路由模式下 Infron 的缓存命中率低于 OpenRouter；第二，为什么某些路由模式下 Infron 的实际成本高于 OpenRouter。分析只使用本轮响应中可观测的 telemetry：provider 分布、cache read tokens、usage cost、completion tokens、reasoning tokens、TTFT 与端到端 E2E 时延。

表 10-A：按路由模式拆解缓存与成本差异。缓存差值为 Infron 减 OpenRouter，成本倍数为 Infron 实际成本 / OpenRouter 实际成本。

| 路由偏好 | 缓存命中差值 | Infron 成本倍数 | Infron 主要上游路径 | OpenRouter 主要上游路径 | Reasoning Tokens 差异 | 主要归因 |
| --- | ---: | ---: | --- | --- | ---: | --- |
| `throughput` | -0.92 pp | 1.41x | `azure` 100.0% | `OpenAI` 99.5%<br>`Azure` 0.5% | +0 | 缓存接近或更高，但 provider 单价路径更高 |
| `price` | -0.05 pp | 1.48x | `azure` 100.0% | `OpenAI` 99.8%<br>`Azure` 0.2% | +0 | 缓存接近或更高，但 provider 单价路径更高 |
| `latency` | -1.47 pp | 1.48x | `azure` 100.0% | `OpenAI` 91.3%<br>`Azure` 8.7% | +0 | 缓存接近或更高，但 provider 单价路径更高 |
| `ttft` | -1.21 pp | 1.97x | `openai` 100.0% | `OpenAI` 91.0%<br>`Azure` 9.0% | +0 | 缓存接近或更高，但 provider 单价路径更高 |

分模式解释：

- `throughput`：Infron Token 级缓存命中率为 97.23%，OpenRouter 为 98.15%，差值 -0.92 pp；Infron 成本为 $0.70693500，OpenRouter 为 $0.49990860，成本倍数 1.41x。Infron 主要路径为 `azure` 100.0%；OpenRouter 主要路径为 `OpenAI` 99.5%，`Azure` 0.5%。双方均未观测到额外 reasoning tokens，或 Infron 未高于 OpenRouter。该模式下 Infron 缓存命中率更低、实际成本更高，主要需要从 provider 单价路径、输出规模和缓存域稳定性解释。
- `price`：Infron Token 级缓存命中率为 98.21%，OpenRouter 为 98.26%，差值 -0.05 pp；Infron 成本为 $0.70694600，OpenRouter 为 $0.47874300，成本倍数 1.48x。Infron 主要路径为 `azure` 100.0%；OpenRouter 主要路径为 `OpenAI` 99.8%，`Azure` 0.2%。双方均未观测到额外 reasoning tokens，或 Infron 未高于 OpenRouter。该模式下 Infron 缓存命中率更低、实际成本更高，主要需要从 provider 单价路径、输出规模和缓存域稳定性解释。
- `latency`：Infron Token 级缓存命中率为 97.45%，OpenRouter 为 98.92%，差值 -1.47 pp；Infron 成本为 $0.64497600，OpenRouter 为 $0.43595370，成本倍数 1.48x。Infron 主要路径为 `azure` 100.0%；OpenRouter 主要路径为 `OpenAI` 91.3%，`Azure` 8.7%。双方均未观测到额外 reasoning tokens，或 Infron 未高于 OpenRouter。该模式下 Infron 缓存命中率更低、实际成本更高，主要需要从 provider 单价路径、输出规模和缓存域稳定性解释。
- `ttft`：Infron Token 级缓存命中率为 98.21%，OpenRouter 为 99.42%，差值 -1.21 pp；Infron 成本为 $0.94275300，OpenRouter 为 $0.47849820，成本倍数 1.97x。Infron 主要路径为 `openai` 100.0%；OpenRouter 主要路径为 `OpenAI` 91.0%，`Azure` 9.0%。双方均未观测到额外 reasoning tokens，或 Infron 未高于 OpenRouter。该模式下 Infron 缓存命中率更低、实际成本更高，主要需要从 provider 单价路径、输出规模和缓存域稳定性解释。

总体看，本轮真正影响缓存与成本的不是单一平台标签，而是“路由目标 → 实际 provider → 缓存域 → reasoning 执行 → usage/cost 返回”的链路组合。Infron 在 无 的 Token 级缓存命中率高于 OpenRouter，在 无 的实际成本低于 OpenRouter。 Infron 实际成本高于 OpenRouter 的路由模式为 `throughput`、`price`、`latency`、`ttft`。 双方 reasoning tokens 差异未成为本轮成本差异的主要来源。


- `throughput` 路由下：缓存命中 OpenRouter 更优，成本 OpenRouter 更低，throughput Infron 更高，latency Infron 更低，TTFT Infron 更低。 综合看 Infron 的可观测路由结果更稳。
- `price` 路由下：缓存命中 OpenRouter 更优，成本 OpenRouter 更低，throughput OpenRouter 更高，latency OpenRouter 更低，TTFT OpenRouter 更低。 这说明 OpenRouter 在该路由下更偏首包与完整响应速度路径。
- `latency` 路由下：缓存命中 OpenRouter 更优，成本 OpenRouter 更低，throughput Infron 更高，latency Infron 更低，TTFT Infron 更低。 综合看 Infron 的可观测路由结果更稳。
- `ttft` 路由下：缓存命中 OpenRouter 更优，成本 OpenRouter 更低，throughput OpenRouter 更高，latency OpenRouter 更低，TTFT OpenRouter 更低。 这说明 OpenRouter 在该路由下更偏首包与完整响应速度路径。
- 脚本已支持在后续实验中采集上游 provider 标识候选字段、routing trace 候选字段、provider cost breakdown 候选字段，并可通过 `--stream` 记录 TTFT、首内容 token 与首 reasoning token 时间。当前报告只展示响应中真实存在的字段，不伪造 provider identity。


## 8. 分层结果：按 Prompt 长度的缓存表现

本节按 prompt 长度 tier 聚合第二次请求的 cache read tokens、Token 级缓存命中率、实际成本和时延。加粗单元表示同一长度 tier 下表现更优的一方；缓存命中率越高越好，成本、latency 和 TTFT 越低越好。

表 11：Prompt 长度分层下的总体缓存表现。

| Prompt 长度 tier | 目标 tokens | 平台 | 轮数 | 第二次 Prompt Tokens | 第二次 Cache Read Tokens | Token 级命中率 | 实际成本 | 平均 Latency | 平均 TTFT |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `short` | 1500 | Infron | **262** | **463769** | 425984 | 91.85% | $0.11666700 | 2083.56 ms | **1744.61 ms** |
| `short` | 1500 | OpenRouter | **262** | **463769** | **427648** | **92.21%** | **$0.08010330** | **2081.97 ms** | 1844.16 ms |
| `medium` | 8000 | Infron | **263** | **2404403** | 2344704 | 97.52% | $0.59036700 | **2737.27 ms** | **2389.97 ms** |
| `medium` | 8000 | OpenRouter | **263** | **2404403** | **2381056** | **99.03%** | **$0.37255890** | 2803.95 ms | 2544.34 ms |
| `long` | 32000 | Infron | **258** | **9383253** | 9208832 | 98.14% | $2.29457600 | 3526.13 ms | **3111.83 ms** |
| `long` | 32000 | OpenRouter | **258** | **9383253** | **9281408** | **98.91%** | **$1.44044130** | **3412.58 ms** | 3123.59 ms |

表 11-2：Prompt 长度 × 路由模式的 Token 级缓存命中率。

| Prompt 长度 tier | 路由偏好 | Infron | OpenRouter | 胜出方 |
| --- | --- | ---: | ---: | --- |
| `short` | `throughput` | 89.80% | **91.20%** | **OpenRouter** |
| `short` | `price` | 92.60% | **94.00%** | **OpenRouter** |
| `short` | `latency` | **92.47%** | 89.39% | **Infron** |
| `short` | `ttft` | 92.60% | **94.00%** | **OpenRouter** |
| `medium` | `throughput` | 94.96% | **99.41%** | **OpenRouter** |
| `medium` | `price` | **99.41%** | **99.41%** | **双方持平** |
| `medium` | `latency` | 96.20% | **97.80%** | **OpenRouter** |
| `medium` | `ttft` | **99.41%** | **99.41%** | **双方持平** |
| `long` | `throughput` | **98.18%** | **98.18%** | **双方持平** |
| `long` | `price` | **98.18%** | **98.18%** | **双方持平** |
| `long` | `latency` | 98.02% | **99.69%** | **OpenRouter** |
| `long` | `ttft` | 98.18% | **99.69%** | **OpenRouter** |


## 9. 分层结果：按实验组的稳定性检查

### throughput

表 12-1：`throughput` 路由模式下的 group-level 稳定性检查。

| 平台 | 组别 | 轮数 | 成功轮数 | Token 级命中率 | 实际成本 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Infron | 1 | **50** | **50** | 93.50% | $0.17325400 |
| Infron | 2 | **50** | **50** | 99.01% | $0.18103600 |
| Infron | 3 | **50** | **50** | 98.06% | $0.17938500 |
| Infron | 4 | **50** | **50** | **98.22%** | $0.17326000 |
| OpenRouter | 1 | **50** | **50** | **99.41%** | **$0.13083240** |
| OpenRouter | 2 | **50** | **50** | **99.22%** | **$0.12190830** |
| OpenRouter | 3 | **50** | **50** | **99.42%** | **$0.12421050** |
| OpenRouter | 4 | **50** | **50** | 94.47% | **$0.12295740** |

### price

表 12-2：`price` 路由模式下的 group-level 稳定性检查。

| 平台 | 组别 | 轮数 | 成功轮数 | Token 级命中率 | 实际成本 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Infron | 1 | **50** | **50** | **99.41%** | $0.17325700 |
| Infron | 2 | **50** | **50** | 94.91% | $0.18104600 |
| Infron | 3 | **50** | **50** | **99.42%** | $0.17938300 |
| Infron | 4 | **50** | **50** | **99.19%** | $0.17326000 |
| OpenRouter | 1 | **50** | **50** | **99.41%** | **$0.11660040** |
| OpenRouter | 2 | **50** | **50** | **99.43%** | **$0.12178770** |
| OpenRouter | 3 | **50** | **50** | **99.42%** | **$0.12093210** |
| OpenRouter | 4 | **50** | **50** | 94.69% | **$0.11942280** |

### latency

表 12-3：`latency` 路由模式下的 group-level 稳定性检查。

| 平台 | 组别 | 轮数 | 成功轮数 | Token 级命中率 | 实际成本 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Infron | 1 | **44** | **44** | 97.77% | $0.15025600 |
| Infron | 2 | **39** | **39** | 98.02% | $0.14207800 |
| Infron | 3 | **50** | **50** | 94.84% | $0.17938200 |
| Infron | 4 | **50** | **50** | **99.41%** | $0.17326000 |
| OpenRouter | 1 | **44** | **44** | **98.02%** | **$0.10181430** |
| OpenRouter | 2 | **39** | **39** | **99.20%** | **$0.09579090** |
| OpenRouter | 3 | **50** | **50** | **99.00%** | **$0.12162090** |
| OpenRouter | 4 | **50** | **50** | **99.41%** | **$0.11672760** |

### ttft

表 12-4：`ttft` 路由模式下的 group-level 稳定性检查。

| 平台 | 组别 | 轮数 | 成功轮数 | Token 级命中率 | 实际成本 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Infron | 1 | **50** | **50** | **99.41%** | $0.23104700 |
| Infron | 2 | **50** | **50** | **99.43%** | $0.24143200 |
| Infron | 3 | **50** | **50** | 99.21% | $0.23921800 |
| Infron | 4 | **50** | **50** | 94.69% | $0.23105600 |
| OpenRouter | 1 | **50** | **50** | **99.41%** | **$0.11670840** |
| OpenRouter | 2 | **50** | **50** | **99.43%** | **$0.12449490** |
| OpenRouter | 3 | **50** | **50** | **99.42%** | **$0.12068850** |
| OpenRouter | 4 | **50** | **50** | **99.41%** | **$0.11660640** |

## 10. 讨论：业务价值、适用边界与工程启示

四种 routing sort 对应不同业务目标，需要结合缓存、成本、吞吐、端到端时延和 TTFT 一起判断。`throughput` 更适合批处理、异步生成、长文本生产和离线任务；`price` 更适合高频低毛利调用、固定模板请求、客服/营销自动化等成本敏感场景；`latency` 更适合交互式产品、Agent 工具调用链、实时辅助写作和用户等待成本较高的场景；`ttft` 更适合首包体验敏感、需要快速给用户反馈的流式交互场景。

| 路由模式 | 主要业务目标 | 本轮数据体现 | 适用场景 | 注意事项 |
| --- | --- | --- | --- | --- |
| `throughput` | 最大化单位时间输出能力 | 缓存 OpenRouter 占优，成本 OpenRouter 占优，throughput Infron 占优，latency Infron 占优，TTFT Infron 占优 | 批量内容生成、离线摘要、后台数据加工 | 适合吞吐优先任务，但需接受缓存和成本可能被速度目标牺牲 |
| `price` | 最小化单位请求和单位 token 成本 | 缓存 OpenRouter 占优，成本 OpenRouter 占优，throughput OpenRouter 占优，latency OpenRouter 占优，TTFT OpenRouter 占优 | 高频模板化请求、客服自动化、营销触达、RAG 固定前缀 | 速度和成本同时较强，但仍需确认缓存命中稳定性 |
| `latency` | 最小化用户可感知等待时间 | 缓存 OpenRouter 占优，成本 OpenRouter 占优，throughput Infron 占优，latency Infron 占优，TTFT Infron 占优 | 在线聊天、Agent 调用链、IDE/写作辅助、实时运营工具 | 适合交互式任务，但需同时约束缓存命中和单位成本 |
| `ttft` | 最小化流式首包响应时间 | 缓存 OpenRouter 占优，成本 OpenRouter 占优，throughput OpenRouter 占优，latency OpenRouter 占优，TTFT OpenRouter 占优 | 流式聊天、实时 Copilot、首屏反馈、长思考任务的进度感知 | 速度和成本同时较强，但仍需确认缓存命中稳定性 |

从业务决策角度看，prompt caching 的价值不只体现在单次请求省钱，而是体现在大规模重复上下文请求的边际成本下降。若业务请求结构高度模板化，应优先关注 Token 级命中率和实际成本；若业务以用户实时体验为核心，应同时约束 latency；若业务为后台批量生成，则 throughput 可能比单请求 latency 更重要。

因此，本实验的推荐读法是：先确认 Input Tokens 是否完全可比，再按业务目标选择主指标，最后检查其他指标是否出现不可接受的副作用。例如某个平台吞吐更高但缓存命中显著较低，可能适合批处理，却未必适合需要稳定成本结构的高频在线业务。

## 11. 结论

表 13：路由模式级结论快照。该表综合缓存命中、成本、throughput、latency 和 TTFT，避免只按单一指标排序。

| 路由偏好 | 缓存命中更优 | 成本更低 | Throughput 更高 | Latency 更低 | TTFT 更低 | 综合解读 |
| --- | --- | --- | --- | --- | --- | --- |
| `throughput` | **OpenRouter** | **OpenRouter** | **Infron** | **Infron** | **Infron** | Infron 综合占优（3/5 可比指标） |
| `price` | **OpenRouter** | **OpenRouter** | **OpenRouter** | **OpenRouter** | **OpenRouter** | OpenRouter 综合占优（5/5 可比指标） |
| `latency` | **OpenRouter** | **OpenRouter** | **Infron** | **Infron** | **Infron** | Infron 综合占优（3/5 可比指标） |
| `ttft` | **OpenRouter** | **OpenRouter** | **OpenRouter** | **OpenRouter** | **OpenRouter** | OpenRouter 综合占优（5/5 可比指标） |

## 12. 局限性、缺失数据与后续实验计划

本报告区分“已观测事实”和“机制解释”。已观测事实来自响应 usage、cost、latency、TTFT、cache tokens、provider 字段和导出的请求级 telemetry；机制解释用于说明这些结果背后的合理工程路径，不代表平台内部私有实现的直接证据。

表 14：当前报告的局限性与后续补充计划。

| 缺失或不足 | 对结论的影响 | 后续补充方式 | 当前处理方式 |
| --- | --- | --- | --- |
| 上游完整 routing trace | 无法逐跳证明每次请求的 provider 选择、fallback 和重试路径 | `待补充：provider routing trace / decision log / fallback reason` | 仅使用响应中真实返回的 provider 字段和 provider 分布做归因 |
| Provider cost breakdown 全量字段 | 无法进一步拆分平台费、provider 费、cache read/write 成本 | `待补充：provider cost breakdown 明细、缓存读写计费项` | 只统计响应明确返回的 cost/cost_details |
| 显著性检验 | 已补充 bootstrap 95% CI 与 paired sign-flip permutation test；尚未给出 standardized effect size | `待补充：Cohen's d / Cliff's delta 等 effect size` | 使用严格 A/B 配对和 input token 相等过滤降低混杂偏差 |
| P95/P99 latency | 已补充 P50/P95/P99 latency 与 TTFT；尚未计算 IQR 和 tail amplification | `待补充：IQR、max、tail amplification ratio` | 当前展示均值、P50/P95/P99 和过程曲线 |
| 多模型泛化 | 单模型实验不能直接外推到所有模型 | `待补充：DeepSeek、Qwen、Claude、GPT 系列跨模型实验` | 结论限定于 `openai/gpt-4o-mini` 本轮样本 |
| 真实业务语料 | 本轮使用内置代表性业务模板，不等同于客户生产语料 | `待补充：脱敏真实 RAG、Agent、客服、代码生成、长文摘要业务数据集` | 脚本已支持 `--dataset-file` JSONL 输入 |
| 并发压力与长期运行 | 本轮使用 `workers` 并发执行，但不是长时间 soak test | `待补充：并发阶梯压测、24h soak test、cache TTL/eviction 观测` | 当前解释 4*50 并发执行窗口内的 A/B 结果 |

后续实验可以继续采用核心 A/B 配对方法：保持 payload SHA256、`usage.prompt_tokens` 偏差不超过 50 tokens 的配对过滤和 request-level telemetry，同时增加 routing trace、provider cost breakdown、尾延迟分位数和业务语料分层。这样可以把本报告扩展为更完整的生产决策评估框架。


## 13. 可复现性附录：Benchmark 数据集

本节给出复现结论和图表所需的数据文件。配对级 CSV 是报告中所有总览表、核心指标图和结论快照的直接输入；请求级 JSONL 保留每一次 first/second 请求的 telemetry，便于审计 provider、usage、cost、latency、TTFT 与缓存字段。公开版报告不在正文展开大体量原始数据，完整数据见公开数据目录。

| 数据文件 | 粒度 | 行数 | SHA256 | 用途 |
| --- | ---: | ---: | --- | --- |
| `export/gpt4o_mini_all_experiments/routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260706_104500_rerun/benchmark_pairs.csv` | A/B pair | 783 | `a04ef6ecb5882f82aa039b2dabc41c4d2e6a0f36bedf88c542b5c06bb38121d4` | 复现聚合表和核心图表 |
| `export/gpt4o_mini_all_experiments/routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260706_104500_rerun/benchmark_requests.jsonl` | request | 3132 | `853de5f12f65c3217531b5caedb8d1b94238521baec04908e318bf1676a89485` | 审计单次请求 telemetry |

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

## 14. 可复现性附录：代码

| 资产 | 在线链接 |
| --- | --- |
| A/B Testing 执行脚本 | <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-4o-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/code/rerun_routing_sort_cache_cost_ab.py> |
| HTML 报告渲染脚本 | <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-4o-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/code/render_glm52_deepseek_style_report.py> |
| PDF 导出脚本 | <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-4o-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/code/export_routing_report_pdf.py> |
| A/B 报告标准 | <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-4o-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/code/ab-report-standard.md> |
| 测试源码 | <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-4o-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/code/test_rerun_routing_sort_cache_cost_ab.py> |
| 实验目录 | <https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/openai/gpt-4o-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06> |
| 报告目录 | <https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/openai/gpt-4o-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/reports> |

## 15. 可复现性附录：原始 Benchmark 数据集

| 数据文件 | 在线链接 |
| --- | --- |
| 配对级 benchmark CSV | <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-4o-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/benchmark_pairs.csv> |
| 请求级 benchmark JSONL | <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-4o-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/benchmark_requests.jsonl> |
| 过滤后原始记录 | <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-4o-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/records.json> |
| 剔除样本记录 | <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-4o-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/records_excluded.json> |
| 汇总统计 | <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-4o-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/summary.json> |
| 数据目录 | <https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/openai/gpt-4o-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data> |

数据集引用：`business_representative` 内置业务代表性模板；请求级导出文件为 `benchmark_requests.jsonl`。
