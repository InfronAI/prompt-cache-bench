# Infron vs OpenRouter Routing, Cache, Cost, and Streaming Performance A/B Test Report

## Abstract and Executive Outline

**Keywords**: Prompt Caching; A/B Testing; Provider Routing; Cache Affinity; Latency; Throughput; Cost Attribution; glm-4.7

### Abstract

This report evaluates `z-ai/glm-4.7` on Infron and OpenRouter across cache reuse, observed cost, throughput, E2E latency, and Streaming TTFT under Prompt Caching workloads.

The main findings are: Infron leads Cache hit rate in 1/4 routing modes; OpenRouter leads in 3/4; 0/4 tie; Infron leads Observed cost in 3/4 routing modes; OpenRouter leads in 1/4; 0/4 tie; OpenRouter leads Throughput in all routing modes; Infron leads E2E latency in all routing modes; OpenRouter leads Streaming TTFT in all routing modes.

Overall, Infron's cross-mode strengths are E2E latency, observed cost, while OpenRouter's cross-mode strengths are throughput, Streaming TTFT, cache reuse. Platform choice should be driven by workload objective rather than a single headline metric.

### Figure 0: Normalized Capability Radar

The five radar axes represent throughput, price, E2E latency, Streaming TTFT, and cache hit rate. Every metric is normalized to a 0-100 score, with farther outward meaning better.

Thick solid lines show platform-level contours; translucent lines and points show individual routing modes.

Conclusion Overview: Core Metric Winners by Routing Mode

Based on strict A/B paired samples. Blue represents Infron, orange represents OpenRouter; gold cells mark the winner for the routing objective.

**Throughput**OpenRouter wins 4/4Max advantage 17.41%, higher is better**Observed cost**Infron wins 3/4Max advantage 3.97%, lower is better**E2E latency**Infron wins 4/4Max advantage 8.39%, lower is better**Streaming TTFT**OpenRouter wins 4/4Max advantage 89.31%, lower is better**Cache hit rate**OpenRouter wins 3/4Max advantage 2.79%, higher is better

| Routing mode | Throughput objective | Cost objective | Latency objective | TTFT objective | Cache result |
| --- | --- | --- | --- | --- | --- |
| **Throughput First** throughput | OpenRouteradvantage 17.41% | Infronadvantage 3.97% | Infronadvantage 8.39% | OpenRouteradvantage 89.31% | OpenRouteradvantage 2.79% |
| **Price First** price | OpenRouteradvantage 12.90% | Infronadvantage 0.79% | Infronadvantage 3.35% | OpenRouteradvantage 14.37% | OpenRouteradvantage 0.16% |
| **Latency First** latency | OpenRouteradvantage 27.40% | OpenRouteradvantage 105.88% | Infronadvantage 0.03% | OpenRouteradvantage 18.74% | OpenRouteradvantage 2.66% |
| **TTFT First** ttft | OpenRouteradvantage 12.11% | Infronadvantage 3.22% | Infronadvantage 1.51% | OpenRouteradvantage 40.25% | Infronadvantage 0.17% |

### Executive Outline

| Dimension | Conclusion | Evidence |
| --- | --- | --- |
| Controls | First/second `usage.prompt_tokens` deltas are limited to 50 tokens within each `sort/group/round` pair. | Methods and data quality |
| Cache reuse | Infron leads Cache hit rate in 1/4 routing modes; OpenRouter leads in 3/4; 0/4 tie | Overall metrics and mechanism section |
| Observed cost | Infron leads Observed cost in 3/4 routing modes; OpenRouter leads in 1/4; 0/4 tie | Overall metrics and provider drill-down |
| Performance | OpenRouter leads Throughput in all routing modes; Infron leads E2E latency in all routing modes; OpenRouter leads Streaming TTFT in all routing modes | Charts and statistical tests |
| Attribution boundary | Claims use observable response telemetry: usage, cost, TTFT, latency, provider fields, and cache tokens. | Provider/Route drill-down |
| Business meaning | Long-context, RAG-prefix, agent-tool, and high-frequency template workloads should evaluate cache rate, cost, first-token latency, and E2E latency together. | Discussion and conclusion |

### Routing-Mode Conclusions

| Routing mode | Objective | Cache winner | Cost winner | Throughput winner | E2E latency winner | TTFT winner | Interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Throughput First | Maximize output capacity per unit time | **OpenRouter** | **Infron** | **OpenRouter** | **Infron** | **OpenRouter** | OpenRouter leads overall (3/5 metrics) |
| Price First | Minimize request and token cost | **OpenRouter** | **Infron** | **OpenRouter** | **Infron** | **OpenRouter** | OpenRouter leads overall (3/5 metrics) |
| Latency First | Minimize full-response waiting time | **OpenRouter** | **OpenRouter** | **OpenRouter** | **Infron** | **OpenRouter** | OpenRouter leads overall (4/5 metrics) |
| TTFT First | Minimize streaming first-token time | **Infron** | **Infron** | **OpenRouter** | **Infron** | **OpenRouter** | Infron leads overall (3/5 metrics) |

## 1. Introduction: Background, Questions, and Contributions

LLM inference-platform behavior is shaped by provider routing, prompt caching, streaming response handling, cost attribution, and fallback policy. This report treats the platform as an observable system and measures speed, cost, cache reuse, and first-token experience through strict A/B pairs.

### 1.1 Research Hypotheses

| Hypothesis | Statement | Validation metric |
| --- | --- | --- |
| H1 | Stronger provider/cache affinity improves token-level cache hit rate for repeated stable prefixes. | Second-request cache-read tokens and token cache hit rate |
| H2 | Higher cache hit rate can reduce observed cost, but does not necessarily reduce TTFT or E2E latency. | Observed cost, average TTFT, average request latency |
| H3 | Different routing sorts change provider selection and produce different cost/throughput/latency frontiers. | Provider distribution, throughput, latency, cost |

### 1.2 Contributions

- Uses response-returned `usage.prompt_tokens` as the input-token control while allowing small cross-platform accounting variance up to 50 tokens.

- Extends prompt-caching evaluation to cost, throughput, E2E latency, TTFT, provider distribution, reasoning telemetry, and paired statistical tests.

- Scopes every claim to observable response telemetry instead of private routing internals.

## 2. Experimental Design, Dataset, and Controls

### 2.1 Dataset Construction

The dataset is `business_representative`, covering 4 routing sorts, 2 platforms, 4 groups, and 50 rounds per group. Each round sends identical first/second Chat Completions requests; the second request observes cache-read tokens, TTFT, and E2E latency.

The built-in business templates represent stable long-context workloads such as RAG support, agent tool instructions, marketing automation, and code review.

### 2.2 Controlled Variables

Figure 1: Experimental Design and Strict A/B Pairing Filter

**Fixed Payload**Model z-ai/glm-4.7; payload SHA-256 is fixed within each routing mode → **Request A1/B1**First request establishes or refreshes cache state → **Request A2/B2**Second request observes cache-read tokens and TTFT → **Strict Filter**Only A/B pairs with input-token deltas up to 50 are aggregated

Controlled-variable rule: within the same `sort/group/round`, both platforms must have first/second `usage.prompt_tokens` deltas no greater than 50 tokens. Total Input Tokens are computed from response-returned usage, not local tokenizer estimates.

### 2.3 Metric Definitions

| Metric | Definition | Direction |
| --- | --- | --- |
| Call cache hit rate | Share of second requests with `cache_read_tokens > 0` | Higher is better |
| Token cache hit rate | Second-request cache-read tokens / second-request prompt tokens | Higher is better |
| Observed cost | Sum of first + second request usage/cost values | Lower is better |
| Throughput | Completion tokens / request latency seconds | Higher is better |
| E2E latency | Full response latency per request | Lower is better |
| TTFT | Streaming first-token arrival time | Lower is better |
| Reasoning telemetry | Reasoning tokens from response usage | Used to explain latency, throughput, and cost |

## 3. Experimental Environment and Data Quality

| Item | Configuration |
| --- | --- |
| Model | `z-ai/glm-4.7` |
| Provider model IDs | infron: `z-ai/glm-4.7`; openrouter: `z-ai/glm-4.7` |
| Platforms | Infron and OpenRouter |
| API protocol | `/v1/chat/completions` |
| Routing modes | Throughput First, Price First, Latency First, TTFT First |
| Groups | 4 |
| Rounds per group | 50 |
| Workers | 24 |
| Request mode | Streaming Chat Completions with TTFT collection |
| Reasoning / thinking control | No explicit reasoning/thinking parameter; model and platform defaults are preserved |
| Prompt length tiers | `short`≈1500, `medium`≈8000, `long`≈32000 |
| Excluded records | 16 |

## 4. Results: Overall Metrics and Main Findings

| Routing mode | Platform | Strict pairs | Total Input Tokens | Token cache hit rate | Observed cost | Throughput | E2E latency | Streaming TTFT |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Throughput First | Infron | 196 | 6340852 | 87.70% | **$2.35911200** | 2.61 tok/s | **4815.56 ms** | 4237.16 ms |
| Throughput First | **OpenRouter** | 196 | 6340852 | **90.15%** | $11.72252143 | **48.12 tok/s** | 45202.33 ms | **2238.17 ms** |
| Price First | Infron | 197 | 6332778 | 97.16% | **$1.29962000** | 3.39 tok/s | **3695.85 ms** | 3278.24 ms |
| Price First | **OpenRouter** | 197 | 6332778 | **97.32%** | $1.30994008 | **47.05 tok/s** | 16059.34 ms | **2866.39 ms** |
| Latency First | Infron | 200 | 6414682 | 96.85% | $3.45964100 | 4.03 tok/s | **3119.38 ms** | 2835.38 ms |
| Latency First | **OpenRouter** | 200 | 6414682 | **99.43%** | **$1.68043559** | **5.13 tok/s** | 3120.18 ms | **2387.82 ms** |
| TTFT First | **Infron** | 199 | 6396238 | **90.65%** | **$1.47298600** | 3.17 tok/s | **3927.90 ms** | 3460.80 ms |
| TTFT First | OpenRouter | 199 | 6396238 | 90.50% | $6.21110423 | **41.60 tok/s** | 9840.11 ms | **2467.55 ms** |

### 4.1 Tail Latency and Statistical Tests

Tail percentiles expose risk that averages hide.

| Routing mode | Platform | P50 latency | P95 latency | P99 latency | P50 TTFT | P95 TTFT | P99 TTFT |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Throughput First | Infron | 3205.84 ms | **15260.63 ms** | **27522.80 ms** | 2755.11 ms | 14748.86 ms | 26879.53 ms |
| Throughput First | **OpenRouter** | **1986.21 ms** | 488985.92 ms | 978823.46 ms | **1844.43 ms** | **5059.73 ms** | **5890.09 ms** |
| Price First | Infron | **3175.76 ms** | **8392.18 ms** | **12749.50 ms** | 2778.86 ms | 7766.03 ms | 12389.07 ms |
| Price First | **OpenRouter** | 3223.35 ms | 22306.38 ms | 597046.76 ms | **2420.72 ms** | **5461.09 ms** | **8349.43 ms** |
| Latency First | Infron | **2356.66 ms** | 6139.54 ms | 10955.27 ms | **2168.31 ms** | 5550.92 ms | 10530.32 ms |
| Latency First | **OpenRouter** | 2896.61 ms | **5714.99 ms** | **7332.56 ms** | 2183.62 ms | **4346.92 ms** | **5286.50 ms** |
| TTFT First | **Infron** | 2817.32 ms | 10246.12 ms | **29526.18 ms** | 2313.33 ms | 9510.77 ms | 29429.36 ms |
| TTFT First | OpenRouter | **2542.11 ms** | **6319.66 ms** | 55239.59 ms | **2048.63 ms** | **5144.78 ms** | **10020.13 ms** |

Mean deltas use bootstrap 95% CIs; p-values use paired sign-flip permutation tests.

| Routing mode | Metric | Mean delta | 95% CI | p-value | Pairs | Interpretation |
| --- | --- | --- | --- | --- | --- | --- |
| Throughput First | Latency: OpenRouter - Infron | **80773.54 ms** | 48187.49 ms to 115069.98 ms | <0.001 | 196 | Positive means lower Infron latency |
| Throughput First | TTFT: OpenRouter - Infron | **-3997.97 ms** | -5040.73 ms to -3118.27 ms | <0.001 | 196 | Positive means lower Infron TTFT |
| Throughput First | Throughput: Infron - OpenRouter | **-13.0327 tok/s** | -15.4306 tok/s to -10.7098 tok/s | <0.001 | 196 | Positive means higher Infron throughput |
| Throughput First | Cost: OpenRouter - Infron | **$0.04777250** | $0.04158206 to $0.05474179 | <0.001 | 196 | Positive means lower Infron cost |
| Throughput First | Token Cache Hit: Infron - OpenRouter | **-3.91 pp** | -8.94 pp to 1.55 pp | 0.1547 | 196 | Positive means higher Infron cache hit |
| Price First | Latency: OpenRouter - Infron | **24726.98 ms** | 9517.45 ms to 42808.20 ms | <0.001 | 197 | Positive means lower Infron latency |
| Price First | TTFT: OpenRouter - Infron | **-823.70 ms** | -1358.63 ms to -275.83 ms | 0.0030 | 197 | Positive means lower Infron TTFT |
| Price First | Throughput: Infron - OpenRouter | **-5.0436 tok/s** | -7.0884 tok/s to -3.2296 tok/s | <0.001 | 197 | Positive means higher Infron throughput |
| Price First | Cost: OpenRouter - Infron | **$0.00005239** | $-0.00230687 to $0.00269302 | 0.9660 | 197 | Positive means lower Infron cost |
| Price First | Token Cache Hit: Infron - OpenRouter | **-3.25 pp** | -5.89 pp to -0.73 pp | 0.0140 | 197 | Positive means higher Infron cache hit |
| Latency First | Latency: OpenRouter - Infron | **1.61 ms** | -607.85 ms to 509.31 ms | 0.9955 | 200 | Positive means lower Infron latency |
| Latency First | TTFT: OpenRouter - Infron | **-895.11 ms** | -1460.28 ms to -439.17 ms | <0.001 | 200 | Positive means lower Infron TTFT |
| Latency First | Throughput: Infron - OpenRouter | **-0.5847 tok/s** | -1.0223 tok/s to -0.1315 tok/s | 0.0177 | 200 | Positive means higher Infron throughput |
| Latency First | Cost: OpenRouter - Infron | **$-0.00889603** | $-0.01153673 to $-0.00616604 | <0.001 | 200 | Positive means lower Infron cost |
| Latency First | Token Cache Hit: Infron - OpenRouter | **-1.46 pp** | -3.96 pp to 1.22 pp | 0.3007 | 200 | Positive means higher Infron cache hit |
| TTFT First | Latency: OpenRouter - Infron | **11824.42 ms** | 674.68 ms to 27150.73 ms | 0.1325 | 199 | Positive means lower Infron latency |
| TTFT First | TTFT: OpenRouter - Infron | **-1986.49 ms** | -2989.55 ms to -1004.35 ms | <0.001 | 199 | Positive means lower Infron TTFT |
| TTFT First | Throughput: Infron - OpenRouter | **-3.1953 tok/s** | -4.5543 tok/s to -2.1213 tok/s | <0.001 | 199 | Positive means higher Infron throughput |
| TTFT First | Cost: OpenRouter - Infron | **$0.02380964** | $0.01799208 to $0.02969512 | <0.001 | 199 | Positive means lower Infron cost |
| TTFT First | Token Cache Hit: Infron - OpenRouter | **1.13 pp** | -3.76 pp to 6.03 pp | 0.6888 | 199 | Positive means higher Infron cache hit |

### 4.2 Reasoning / Thinking Control Check

This run does not explicitly set reasoning/thinking parameters and keeps model/platform defaults; this table records reasoning telemetry under default behavior.

| Routing mode | Platform | Reasoning tokens | Avg reasoning tokens/request | Reasoning requests | Avg first reasoning token | Avg TTFT | Avg E2E latency |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Throughput First | Infron | **0** | **0.0000** | **0** | **0.00 ms** | 4237.16 ms | **4815.56 ms** |
| Throughput First | **OpenRouter** | 852412 | 2174.5204 | 392 | 2238.17 ms | **2238.17 ms** | 45202.33 ms |
| Price First | Infron | **0** | **0.0000** | **0** | **0.00 ms** | 3278.24 ms | **3695.85 ms** |
| Price First | **OpenRouter** | 300492 | 762.6701 | 394 | 2866.39 ms | **2866.39 ms** | 16059.34 ms |
| Latency First | Infron | **0** | **0.0000** | **0** | **0.00 ms** | 2835.38 ms | **3119.38 ms** |
| Latency First | **OpenRouter** | 9454 | 23.6350 | 400 | 2387.82 ms | **2387.82 ms** | 3120.18 ms |
| TTFT First | **Infron** | **0** | **0.0000** | **0** | **0.00 ms** | 3460.80 ms | **3927.90 ms** |
| TTFT First | OpenRouter | 164853 | 414.2035 | 398 | 2467.55 ms | **2467.55 ms** | 9840.11 ms |

### 4.3 API Protocol Compatibility Matrix

This run uses `/v1/chat/completions`; this table records success response, usage, cost, and cache telemetry coverage for both platforms under that protocol.

| API protocol | Endpoint | Platform | Pairs | Requests | Success rate | Usage coverage | Token usage coverage | Cost coverage | Cache telemetry coverage | HTTP statuses | Top errors |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `chat_completions` | `/v1/chat/completions` | Infron | 800 | 1600 | **100.00%** | **100.00%** | **100.00%** | **100.00%** | **100.00%** | {"200":1600} |  |
| `chat_completions` | `/v1/chat/completions` | OpenRouter | 800 | 1600 | 99.94% | 99.69% | 99.69% | 99.69% | **100.00%** | {"0":1,"200":1599} | 1 x Remote end closed connection without response |

## 5. Result Visualizations by Routing Mode

The following charts are driven by the strict-paired summary data and present routing-mode, platform, cost, cache, E2E latency, Streaming TTFT, and upstream provider differences.

### 5.1 Core Metric Chart Overview

The charts below are generated from the same strict-paired summary data.

Figure 3-E1: Routing-mode core metric comparison

Infron and OpenRouter are shown side by side by routing mode.

Figure 3-E2: Normalized capability contour

Five metrics are normalized to 0-100, where higher is better.

Figure 3-E3: Cost-cache efficiency plane

X-axis is token cache hit rate; Y-axis is observed total cost.

Figure 3-E4: E2E latency and Streaming TTFT

Solid lines show E2E latency; dashed lines show Streaming TTFT.

Figure 3-E5: Upstream provider distribution

Provider shares explain cache-domain and performance differences.

### Routing-Mode Drill-Down Charts

The horizontal axis shows relative advantage: blue to the right indicates Infron advantage, orange to the left indicates OpenRouter advantage.

Figure 4-E1: Throughput First core metric comparison

Direction and magnitude of relative advantage across five metrics.

Figure 4-E2: Price First core metric comparison

Direction and magnitude of relative advantage across five metrics.

Figure 4-E3: Latency First core metric comparison

Direction and magnitude of relative advantage across five metrics.

Figure 4-E4: TTFT First core metric comparison

Direction and magnitude of relative advantage across five metrics.

## 6. Infron Technical Architecture and Cache/Cost Mechanism

Figure 12: Infron Multi-Provider Routing and Cache Control Plane

**Unified API Entry**OpenAI-compatible requests enter the gateway with usage, stream, and provider routing parameters → **Routing Policy Layer**Selects healthy upstream paths by throughput / price / latency / ttft objective → **Provider Stick / Cache Affinity**Repeated long prefixes are kept in stable cache domains where possible → **Upstream Provider**Response telemetry reports provider, usage, cost, latency, and TTFT

### 6.1 Multi-Provider Routing and Observable Control Plane

Requests enter a unified API, and the routing layer selects healthy upstream paths according to throughput, price, latency, or ttft objectives. Whether stable long prefixes stay in the same cache domain directly affects second-request cache-read tokens.

### 6.2 Provider Stick and Cache Affinity

Provider stick is cache affinity, not a permanent provider lock. Its goal is to reduce cache-domain fragmentation while respecting health and SLA constraints.

### 6.3 Cost-Control Path

| Mechanism | Cache-rate effect | Cost effect | Observable signal |
| --- | --- | --- | --- |
| Stable prefix detection | Repeated prefixes are more likely to hit cache | Reduces repeated prefill cost | Payload SHA-256 and second-request cache-read tokens |
| Provider stick / cache affinity | Reduces cross-domain cache fragmentation | Avoids repeated cache warm-up | Provider distribution and token cache hit rate |
| Health checks and fallback | Protects availability while sometimes sacrificing cache | Reduces failure cost | HTTP status, provider distribution, tail latency |
| Cost-aware routing | Prefers lower-cost paths under constraints | Reduces total and per-round cost | Observed cost, cost breakdown coverage, cache-read tokens |

## 7. Provider/Route Drill-Down

| Routing mode | Platform | Total requests | Attributed requests | Provider distribution |
| --- | --- | --- | --- | --- |
| Throughput First | Infron | 392 | 392 | `atlas-cloud` 128, `alibaba/cn` 96, `z-ai` 85, `deepinfra` 83 |
| Throughput First | OpenRouter | 392 | 392 | `Cerebras` 275, `StreamLake` 43, `DeepInfra` 40, `Google` 34 |
| Price First | Infron | 394 | 394 | `alibaba/cn` 262, `atlas-cloud` 114, `deepinfra` 18 |
| Price First | OpenRouter | 394 | 394 | `DeepInfra` 373, `StreamLake` 21 |
| Latency First | Infron | 400 | 400 | `cerebras` 224, `atlas-cloud` 176 |
| Latency First | OpenRouter | 400 | 400 | `DeepInfra` 336, `Cerebras` 61, `Google` 3 |
| TTFT First | Infron | 398 | 398 | `cerebras` 190, `deepinfra` 183, `byteplus` 25 |
| TTFT First | OpenRouter | 398 | 398 | `Cerebras` 184, `DeepInfra` 149, `Google` 57, `StreamLake` 5, `Venice` 3 |

### Upstream Provider Detail Distribution

| Routing mode | Platform | Upstream provider | Requests | Share | first/second | Covered rounds | Avg TTFT | Avg latency | Prompt tokens | Completion tokens | Reasoning tokens | Cache-read tokens | Observed cost |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Throughput First | Infron | `atlas-cloud` | 128 | 32.65% | 57/71 | 71 | 3015.57 ms | 3378.43 ms | 2172789 | 1676 | 0 | 1835392 | $1.13278600 |
| Throughput First | Infron | `alibaba/cn` | 96 | 24.49% | 55/41 | 55 | 3523.03 ms | 3881.86 ms | 1343164 | 1184 | 0 | 968832 | $0.15570100 |
| Throughput First | Infron | `z-ai` | 85 | 21.68% | 45/40 | 54 | 5791.82 ms | 6227.12 ms | 1386006 | 1025 | 0 | 1140224 | $0.83385100 |
| Throughput First | Infron | `deepinfra` | 83 | 21.17% | 39/44 | 53 | 5354.90 ms | 6666.21 ms | 1438893 | 1049 | 0 | 1064480 | $0.23677400 |
| Throughput First | OpenRouter | `Cerebras` | 275 | 70.15% | 137/138 | 163 | 1784.62 ms | 1848.12 ms | 4030603 | 4400 | 4400 | 3679360 | $9.08095675 |
| Throughput First | OpenRouter | `StreamLake` | 43 | 10.97% | 23/20 | 42 | 4411.22 ms | 394378.19 ms | 1064769 | 847035 | 846252 | 1060864 | $2.00187072 |
| Throughput First | OpenRouter | `DeepInfra` | 40 | 10.20% | 18/22 | 22 | 1993.00 ms | 2727.93 ms | 213119 | 640 | 932 | 210272 | $0.01908056 |
| Throughput First | OpenRouter | `Google` | 34 | 8.67% | 18/16 | 31 | 3446.75 ms | 4226.42 ms | 1032361 | 544 | 828 | 542272 | $0.62061340 |
| Price First | Infron | `alibaba/cn` | 262 | 66.50% | 132/130 | 139 | 3374.68 ms | 3753.99 ms | 4201868 | 3192 | 0 | 4065408 | $0.25841400 |
| Price First | Infron | `atlas-cloud` | 114 | 28.93% | 56/58 | 65 | 2982.92 ms | 3405.47 ms | 1840318 | 1534 | 0 | 1789824 | $0.95965100 |
| Price First | Infron | `deepinfra` | 18 | 4.57% | 9/9 | 9 | 3744.93 ms | 4688.60 ms | 290592 | 204 | 0 | 109504 | $0.08155500 |
| Price First | OpenRouter | `DeepInfra` | 373 | 94.67% | 188/185 | 196 | 2684.14 ms | 3596.74 ms | 5907457 | 5968 | 9116 | 5565920 | $0.59233240 |
| Price First | OpenRouter | `StreamLake` | 21 | 5.33% | 9/12 | 20 | 6103.59 ms | 237418.80 ms | 425321 | 291735 | 291376 | 370816 | $0.71760768 |
| Latency First | Infron | `cerebras` | 224 | 56.00% | 115/109 | 129 | 1669.54 ms | 1820.29 ms | 1423410 | 2784 | 0 | 1183872 | $0.86027200 |
| Latency First | Infron | `atlas-cloud` | 176 | 44.00% | 85/91 | 105 | 4319.17 ms | 4772.76 ms | 4991272 | 2238 | 0 | 4888320 | $2.59936900 |
| Latency First | OpenRouter | `DeepInfra` | 336 | 84.00% | 166/170 | 174 | 2524.43 ms | 3381.79 ms | 5897735 | 5376 | 8420 | 5689408 | $0.54789144 |
| Latency First | OpenRouter | `Cerebras` | 61 | 15.25% | 33/28 | 38 | 1655.31 ms | 1714.24 ms | 496719 | 976 | 976 | 482688 | $1.12030175 |
| Latency First | OpenRouter | `Google` | 3 | 0.75% | 1/2 | 3 | 1982.30 ms | 2407.21 ms | 20228 | 48 | 58 | 18432 | $0.01224240 |
| TTFT First | Infron | `cerebras` | 190 | 47.74% | 98/92 | 113 | 1579.81 ms | 1718.75 ms | 1098069 | 2250 | 0 | 1085184 | $0.66387200 |
| TTFT First | Infron | `deepinfra` | 183 | 45.98% | 86/97 | 109 | 3299.62 ms | 4156.87 ms | 4602829 | 2342 | 0 | 4544320 | $0.39109400 |
| TTFT First | Infron | `byteplus` | 25 | 6.28% | 15/10 | 22 | 18936.10 ms | 19041.43 ms | 695340 | 367 | 0 | 0 | $0.41802000 |
| TTFT First | OpenRouter | `Cerebras` | 184 | 46.23% | 93/91 | 113 | 1996.63 ms | 2064.39 ms | 2088233 | 2944 | 2944 | 1977344 | $4.70662025 |
| TTFT First | OpenRouter | `DeepInfra` | 149 | 37.44% | 74/75 | 87 | 2665.34 ms | 3745.02 ms | 2639463 | 2384 | 3831 | 2549664 | $0.24406472 |
| TTFT First | OpenRouter | `Google` | 57 | 14.32% | 28/29 | 47 | 2900.58 ms | 3388.18 ms | 1481877 | 912 | 1458 | 986432 | $0.89113260 |
| TTFT First | OpenRouter | `StreamLake` | 5 | 1.26% | 3/2 | 5 | 7491.29 ms | 553229.52 ms | 130771 | 156626 | 156539 | 93056 | $0.33843184 |
| TTFT First | OpenRouter | `Venice` | 3 | 0.75% | 1/2 | 3 | 4926.22 ms | 6411.97 ms | 55894 | 48 | 81 | 32 | $0.03085482 |

### 7.1 Cache-Rate and Cost Divergence Drill-Down

This table combines cache, cost, provider distribution, and reasoning telemetry to explain routing-mode differences.

| Routing mode | Cache-hit delta | Infron cost multiple | Infron top path | OpenRouter top path | Reasoning token delta | Main attribution |
| --- | --- | --- | --- | --- | --- | --- |
| Throughput First | -2.45 pp | **0.20x** | **`atlas-cloud` 32.65%** | **`Cerebras` 70.15%** | **-852412** | Cache and cost move in different directions; evaluate with speed metrics |
| Price First | -0.16 pp | **0.99x** | **`alibaba/cn` 66.50%** | **`DeepInfra` 94.67%** | **-300492** | Cache and cost move in different directions; evaluate with speed metrics |
| Latency First | -2.58 pp | 2.06x | `cerebras` 56.00% | **`DeepInfra` 84.00%** | **-9454** | OpenRouter has higher cache and lower cost; provider/cache-domain mix is the main signal |
| TTFT First | **+0.15 pp** | **0.24x** | **`cerebras` 47.74%** | `Cerebras` 46.23% | **-164853** | Infron leads both cache and cost |

## 8. Stratified Results: Prompt-Length Cache Performance

This section aggregates second-request cache-read tokens, token-level cache hit rate, observed cost, E2E latency, and Streaming TTFT by prompt-length tier. Bold cells mark the advantaged side within each tier.

### Prompt-Length Tier Overview

| Prompt length tier | Target tokens | Platform | Pairs | Second prompt tokens | Second cache read tokens | Token cache hit rate | Observed cost | Avg E2E latency | Avg TTFT |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `short` | 1500 | Infron | **266** | **468570** | 426208 | 90.96% | **$0.40699000** | **2062.10 ms** | 1753.08 ms |
| `short` | 1500 | OpenRouter | **266** | **468570** | **438400** | **93.56%** | $1.14530131 | 6198.48 ms | **1687.32 ms** |
| `medium` | 8000 | Infron | **263** | **2427115** | 2302784 | 94.88% | **$1.80182600** | **3563.12 ms** | 3122.63 ms |
| `medium` | 8000 | OpenRouter | **263** | **2427115** | **2349728** | **96.81%** | $5.54600964 | 15638.37 ms | **2252.96 ms** |
| `long` | 32000 | Infron | **263** | **9846590** | 9133536 | 92.76% | **$6.38254300** | **6052.63 ms** | 5492.40 ms |
| `long` | 32000 | OpenRouter | **263** | **9846590** | **9234880** | **93.79%** | $14.23269038 | 33626.91 ms | **3538.45 ms** |

### Prompt Length x Routing Mode Cache Hit Rate

| Prompt length tier | Routing mode | Infron | OpenRouter | Winner |
| --- | --- | --- | --- | --- |
| `short` | Throughput First | 85.41% | **92.62%** | **OpenRouter** |
| `short` | Price First | 91.77% | **97.42%** | **OpenRouter** |
| `short` | Latency First | 93.06% | **94.03%** | **OpenRouter** |
| `short` | TTFT First | **93.62%** | 90.29% | **Infron** |
| `medium` | Throughput First | 91.44% | **93.48%** | **OpenRouter** |
| `medium` | Price First | 94.34% | **99.82%** | **OpenRouter** |
| `medium` | Latency First | 98.21% | **98.38%** | **OpenRouter** |
| `medium` | TTFT First | 95.33% | **95.34%** | **OpenRouter** |
| `long` | Throughput First | 86.93% | **89.25%** | **OpenRouter** |
| `long` | Price First | **98.13%** | 96.67% | **Infron** |
| `long` | Latency First | 96.70% | **99.96%** | **OpenRouter** |
| `long` | TTFT First | **89.35%** | 89.31% | **Infron** |

## 9. Stratified Results: Group-Level Stability

### Throughput First

| Platform | Group | Rounds | Successful rounds | Token cache hit rate | Observed cost | P95 latency | P95 TTFT |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Infron | 1 | 48 | 48 | 84.52% | **$0.20900000** | **15394.45 ms** | 14543.95 ms |
| Infron | 2 | 49 | 49 | **79.53%** | **$0.41033100** | **22335.58 ms** | 21558.06 ms |
| Infron | 3 | 49 | 49 | 92.16% | **$0.92022400** | **13146.75 ms** | 12940.77 ms |
| Infron | 4 | 50 | 50 | 94.70% | **$0.81955700** | **7774.10 ms** | 7350.46 ms |
| OpenRouter | 1 | 48 | 48 | **93.31%** | $2.92280559 | 487720.79 ms | **5337.85 ms** |
| OpenRouter | 2 | 49 | 49 | 77.90% | $2.62445875 | 623230.31 ms | **5314.08 ms** |
| OpenRouter | 3 | 49 | 49 | **94.84%** | $2.97944500 | 28482.04 ms | **4926.91 ms** |
| OpenRouter | 4 | 50 | 50 | **94.93%** | $3.19581209 | 44049.73 ms | **4526.62 ms** |

### Price First

| Platform | Group | Rounds | Successful rounds | Token cache hit rate | Observed cost | P95 latency | P95 TTFT |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Infron | 1 | 48 | 48 | 91.88% | **$0.16758700** | **9304.59 ms** | 8268.21 ms |
| Infron | 2 | 50 | 50 | 99.12% | **$0.33531200** | **7282.33 ms** | 7144.26 ms |
| Infron | 3 | 49 | 49 | **98.17%** | $0.40023700 | **5469.66 ms** | 5079.31 ms |
| Infron | 4 | 50 | 50 | 99.08% | $0.39648400 | 10892.53 ms | 10016.62 ms |
| OpenRouter | 1 | 48 | 48 | **94.85%** | $0.52433344 | 42930.43 ms | **5543.44 ms** |
| OpenRouter | 2 | 50 | 50 | **99.31%** | $0.37593736 | 23865.89 ms | **5852.94 ms** |
| OpenRouter | 3 | 49 | 49 | 95.28% | **$0.25281960** | 6450.57 ms | **4602.33 ms** |
| OpenRouter | 4 | 50 | 50 | **99.68%** | **$0.15684968** | **8191.63 ms** | **5221.84 ms** |

### Latency First

| Platform | Group | Rounds | Successful rounds | Token cache hit rate | Observed cost | P95 latency | P95 TTFT |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Infron | 1 | 50 | 50 | 98.13% | $0.87834400 | **5480.00 ms** | 5078.45 ms |
| Infron | 2 | 50 | 50 | 94.96% | $0.87516500 | 6819.94 ms | 5605.96 ms |
| Infron | 3 | 50 | 50 | 94.98% | $0.86795900 | 6129.32 ms | 5612.93 ms |
| Infron | 4 | 50 | 50 | 99.49% | $0.83817300 | 6073.53 ms | 5363.47 ms |
| OpenRouter | 1 | 50 | 50 | **99.65%** | **$0.45228386** | 5727.80 ms | **4333.76 ms** |
| OpenRouter | 2 | 50 | 50 | **98.54%** | **$0.36502139** | **5821.87 ms** | **4263.78 ms** |
| OpenRouter | 3 | 50 | 50 | **99.69%** | **$0.37872743** | **5397.15 ms** | **4378.57 ms** |
| OpenRouter | 4 | 50 | 50 | **99.89%** | **$0.48440291** | **5531.57 ms** | **4154.45 ms** |

### TTFT First

| Platform | Group | Rounds | Successful rounds | Token cache hit rate | Observed cost | P95 latency | P95 TTFT |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Infron | 1 | 50 | 50 | 63.83% | **$0.80475000** | 28182.96 ms | 28066.61 ms |
| Infron | 2 | 49 | 49 | **98.63%** | **$0.24074900** | **6190.14 ms** | **5378.94 ms** |
| Infron | 3 | 50 | 50 | **99.75%** | **$0.20363800** | 6177.89 ms | 5146.51 ms |
| Infron | 4 | 50 | 50 | **99.80%** | **$0.22384900** | **5185.56 ms** | **3845.64 ms** |
| OpenRouter | 1 | 50 | 50 | **94.85%** | $1.36985113 | **4181.53 ms** | **3503.71 ms** |
| OpenRouter | 2 | 49 | 49 | 75.58% | $2.11139781 | 9203.58 ms | 5565.45 ms |
| OpenRouter | 3 | 50 | 50 | 99.34% | $1.05860361 | **4848.89 ms** | **3330.83 ms** |
| OpenRouter | 4 | 50 | 50 | 92.41% | $1.67125168 | 8486.81 ms | 5933.69 ms |

## 10. Discussion: Business Value, Boundaries, and Engineering Implications

Business decisions should not rely on one metric. Stable long-context and high-frequency template workloads should prioritize cache rate and cost; realtime interaction must constrain TTFT and E2E latency; batch processing often prioritizes throughput and failure cost.

| Routing mode | Business objective | Observed result | Scenarios | Caveat |
| --- | --- | --- | --- | --- |
| Throughput First | Maximize output capacity per unit time | OpenRouter leads overall (3/5 metrics) | Batch generation, offline summaries, backend processing | Good for throughput-first tasks; constrain cost and cache separately |
| Price First | Minimize request and token cost | OpenRouter leads overall (3/5 metrics) | High-frequency templates, support automation, marketing, RAG prefixes | Good for throughput-first tasks; constrain cost and cache separately |
| Latency First | Minimize full-response waiting time | OpenRouter leads overall (4/5 metrics) | Online chat, agent chains, IDE/writing assistants, realtime tools | Good for throughput-first tasks; constrain cost and cache separately |
| TTFT First | Minimize streaming first-token time | Infron leads overall (3/5 metrics) | Streaming chat, realtime copilots, first-screen feedback | Cache and cost are stronger; still check speed SLA |

## 11. Conclusion

### Routing-Mode Conclusions

| Routing mode | Objective | Cache winner | Cost winner | Throughput winner | E2E latency winner | TTFT winner | Interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Throughput First | Maximize output capacity per unit time | **OpenRouter** | **Infron** | **OpenRouter** | **Infron** | **OpenRouter** | OpenRouter leads overall (3/5 metrics) |
| Price First | Minimize request and token cost | **OpenRouter** | **Infron** | **OpenRouter** | **Infron** | **OpenRouter** | OpenRouter leads overall (3/5 metrics) |
| Latency First | Minimize full-response waiting time | **OpenRouter** | **OpenRouter** | **OpenRouter** | **Infron** | **OpenRouter** | OpenRouter leads overall (4/5 metrics) |
| TTFT First | Minimize streaming first-token time | **Infron** | **Infron** | **OpenRouter** | **Infron** | **OpenRouter** | Infron leads overall (3/5 metrics) |

## 12. Limitations, Missing Data, and Next Experiments

| Limitation | Impact | Next step | Current handling |
| --- | --- | --- | --- |
| Full routing trace | Cannot prove every provider choice, fallback, and retry path hop by hop | Add provider routing trace, decision logs, and fallback reasons | Use only returned provider fields and provider distribution |
| Longer time window | 4x50 observes short-window stability but not day-level drift | Add soak tests and repeated windows | Scope conclusions to this run |
| Production corpus | Built-in templates do not cover every workload distribution | Use sanitized production-stratified corpora | Discuss representative long-context templates only |
| Cost-field consistency | Cost coverage and semantics may differ by platform | Reconcile with billing and provider cost breakdown | Use only explicitly returned cost fields |

## 13. Reproducibility Appendix

| Artifact | Path |
| --- | --- |
| Summary | [summary.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-4.7/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/summary.json) |
| Paired dataset | [benchmark_pairs.csv](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-4.7/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/benchmark_pairs.csv) |
| Request-level dataset | [benchmark_requests.jsonl](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-4.7/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/benchmark_requests.jsonl) |
| Filtered structured records | [records.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-4.7/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/records.json) |
| Excluded-record audit | [records_excluded.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-4.7/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/records_excluded.json) |
| Test source | [test_rerun_routing_sort_cache_cost_ab.py](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-4.7/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/code/test_rerun_routing_sort_cache_cost_ab.py) |
| Benchmark runner source | [rerun_routing_sort_cache_cost_ab.py](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-4.7/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/code/rerun_routing_sort_cache_cost_ab.py) |
| HTML report renderer source | [render_glm52_deepseek_style_report.py](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-4.7/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/code/render_glm52_deepseek_style_report.py) |
| Dataset reference | `business_representative` built-in representative business templates; request-level export is `benchmark_requests.jsonl` |

Online HTML: Chinese [https://infronai.github.io/prompt-cache-bench/experiments/z-ai/glm-4.7/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/reports/routing-cache-cost-streaming-performance-ab-study__glm-4-7__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-07.zh.html](https://infronai.github.io/prompt-cache-bench/experiments/z-ai/glm-4.7/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/reports/routing-cache-cost-streaming-performance-ab-study__glm-4-7__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-07.zh.html); English [https://infronai.github.io/prompt-cache-bench/experiments/z-ai/glm-4.7/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/reports/routing-cache-cost-streaming-performance-ab-study__glm-4-7__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-07.en.html](https://infronai.github.io/prompt-cache-bench/experiments/z-ai/glm-4.7/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/reports/routing-cache-cost-streaming-performance-ab-study__glm-4-7__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-07.en.html).
