# Infron vs OpenRouter Routing, Cache, Cost, and Streaming Performance A/B Test Report

## Abstract and Executive Outline

**Keywords**: Prompt Caching; A/B Testing; Provider Routing; Cache Affinity; Latency; Throughput; Cost Attribution; glm-5

### Abstract

This report evaluates `z-ai/glm-5` on Infron and OpenRouter across cache reuse, observed cost, throughput, E2E latency, and Streaming TTFT under Prompt Caching workloads.

The main findings are: Infron leads Cache hit rate in 1/4 routing modes; OpenRouter leads in 3/4; 0/4 tie; Infron leads Observed cost in 2/4 routing modes; OpenRouter leads in 2/4; 0/4 tie; OpenRouter leads Throughput in all routing modes; Infron leads E2E latency in 3/4 routing modes; OpenRouter leads in 1/4; 0/4 tie; Infron leads Streaming TTFT in 3/4 routing modes; OpenRouter leads in 1/4; 0/4 tie.

Overall, Infron's cross-mode strengths are Streaming TTFT, E2E latency, while OpenRouter's cross-mode strengths are throughput, cache reuse. Platform choice should be driven by workload objective rather than a single headline metric.

### Figure 0: Normalized Capability Radar

The five radar axes represent throughput, price, E2E latency, Streaming TTFT, and cache hit rate. Every metric is normalized to a 0-100 score, with farther outward meaning better.

Thick solid lines show platform-level contours; translucent lines and points show individual routing modes.

Conclusion Overview: Core Metric Winners by Routing Mode

Based on strict A/B paired samples. Blue represents Infron, orange represents OpenRouter; gold cells mark the winner for the routing objective.

    **Throughput**OpenRouter wins 4/4Max advantage 104.15%, higher is better**Observed cost**Infron wins 2/4Max advantage 62.64%, lower is better**E2E latency**Infron wins 3/4Max advantage 64.76%, lower is better**Streaming TTFT**Infron wins 3/4Max advantage 47.57%, lower is better**Cache hit rate**OpenRouter wins 3/4Max advantage 4.00%, higher is better

| Routing mode | Throughput objective | Cost objective | Latency objective | TTFT objective | Cache result |
| --- | --- | --- | --- | --- | --- |
| **Throughput First**<br>throughput | OpenRouteradvantage 7.85% | OpenRouteradvantage 62.64% | Infronadvantage 10.78% | Infronadvantage 12.55% | Infronadvantage 1.72% |
| **Price First**<br>price | OpenRouteradvantage 104.15% | OpenRouteradvantage 20.72% | OpenRouteradvantage 64.76% | OpenRouteradvantage 47.57% | OpenRouteradvantage 4.00% |
| **Latency First**<br>latency | OpenRouteradvantage 19.66% | Infronadvantage 7.35% | Infronadvantage 3.14% | Infronadvantage 33.16% | OpenRouteradvantage 0.23% |
| **TTFT First**<br>ttft | OpenRouteradvantage 9.81% | Infronadvantage 2.54% | Infronadvantage 12.04% | Infronadvantage 39.74% | OpenRouteradvantage 0.27% |

### Executive Outline

| Dimension | Conclusion | Evidence |
| --- | --- | --- |
| Controls | First/second `usage.prompt_tokens` deltas are limited to 50 tokens within each `sort/group/round` pair. | Methods and data quality |
| Cache reuse | Infron leads Cache hit rate in 1/4 routing modes; OpenRouter leads in 3/4; 0/4 tie | Overall metrics and mechanism section |
| Observed cost | Infron leads Observed cost in 2/4 routing modes; OpenRouter leads in 2/4; 0/4 tie | Overall metrics and provider drill-down |
| Performance | OpenRouter leads Throughput in all routing modes; Infron leads E2E latency in 3/4 routing modes; OpenRouter leads in 1/4; 0/4 tie; Infron leads Streaming TTFT in 3/4 routing modes; OpenRouter leads in 1/4; 0/4 tie | Charts and statistical tests |
| Attribution boundary | Claims use observable response telemetry: usage, cost, TTFT, latency, provider fields, and cache tokens. | Provider/Route drill-down |
| Business meaning | Long-context, RAG-prefix, agent-tool, and high-frequency template workloads should evaluate cache rate, cost, first-token latency, and E2E latency together. | Discussion and conclusion |

### Routing-Mode Conclusions

| Routing mode | Objective | Cache winner | Cost winner | Throughput winner | E2E latency winner | TTFT winner | Interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Throughput First | Maximize output capacity per unit time | **Infron** | **OpenRouter** | **OpenRouter** | **Infron** | **Infron** | Infron leads overall (3/5 metrics) |
| Price First | Minimize request and token cost | **OpenRouter** | **OpenRouter** | **OpenRouter** | **OpenRouter** | **OpenRouter** | OpenRouter leads overall (5/5 metrics) |
| Latency First | Minimize full-response waiting time | **OpenRouter** | **Infron** | **OpenRouter** | **Infron** | **Infron** | Infron leads overall (3/5 metrics) |
| TTFT First | Minimize streaming first-token time | **OpenRouter** | **Infron** | **OpenRouter** | **Infron** | **Infron** | Infron leads overall (3/5 metrics) |

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

    **Fixed Payload**Model z-ai/glm-5; payload SHA-256 is fixed within each routing mode
    →
    **Request A1/B1**First request establishes or refreshes cache state
    →
    **Request A2/B2**Second request observes cache-read tokens and TTFT
    →
    **Strict Filter**Only A/B pairs with input-token deltas up to 50 are aggregated

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
| Model | `z-ai/glm-5` |
| Provider model IDs | infron: `z-ai/glm-5`; openrouter: `z-ai/glm-5` |
| Platforms | Infron and OpenRouter |
| API protocol | `/v1/chat/completions` |
| Routing modes | Throughput First, Price First, Latency First, TTFT First |
| Groups | 4 |
| Rounds per group | 50 |
| Workers | 24 |
| Request mode | Streaming Chat Completions with TTFT collection |
| Reasoning / thinking control | No explicit reasoning/thinking parameter; model and platform defaults are preserved |
| Prompt length tiers | `short`≈1500, `medium`≈8000, `long`≈32000 |
| Excluded records | 24 |

## 4. Results: Overall Metrics and Main Findings

| Routing mode | Platform | Strict pairs | Total Input Tokens | Token cache hit rate | Observed cost | Throughput | E2E latency | Streaming TTFT |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Throughput First | **Infron** | 200 | 6414682 | **99.79%** | $1.61315300 | 2.52 tok/s | **5311.71 ms** | **4992.94 ms** |
| Throughput First | OpenRouter | 200 | 6414682 | 98.10% | **$0.99183578** | **2.72 tok/s** | 5884.51 ms | 5619.75 ms |
| Price First | Infron | 195 | 6040276 | 95.70% | $0.99697000 | 1.52 tok/s | 8506.60 ms | 7224.73 ms |
| Price First | **OpenRouter** | 195 | 6040283 | **99.53%** | **$0.82584095** | **3.10 tok/s** | **5163.02 ms** | **4895.85 ms** |
| Latency First | **Infron** | 193 | 6273860 | 99.61% | **$0.77495600** | 2.61 tok/s | **4966.67 ms** | **3645.69 ms** |
| Latency First | OpenRouter | 193 | 6273860 | **99.84%** | $0.83192194 | **3.12 tok/s** | 5122.85 ms | 4854.43 ms |
| TTFT First | **Infron** | 200 | 6414682 | 99.56% | **$0.84264400** | 2.73 tok/s | **4758.14 ms** | **3596.32 ms** |
| TTFT First | OpenRouter | 200 | 6414682 | **99.83%** | $0.86408455 | **3.00 tok/s** | 5331.20 ms | 5025.52 ms |

### 4.1 Tail Latency and Statistical Tests

Tail percentiles expose risk that averages hide.

| Routing mode | Platform | P50 latency | P95 latency | P99 latency | P50 TTFT | P95 TTFT | P99 TTFT |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Throughput First | **Infron** | **5019.43 ms** | **8949.33 ms** | **11000.97 ms** | **4695.00 ms** | **8587.00 ms** | **10897.81 ms** |
| Throughput First | OpenRouter | 5511.87 ms | 9758.45 ms | 12789.27 ms | 5324.60 ms | 9432.64 ms | 12480.67 ms |
| Price First | Infron | **4307.77 ms** | 31280.13 ms | 93253.06 ms | **3325.72 ms** | 22342.13 ms | 92413.82 ms |
| Price First | **OpenRouter** | 5101.24 ms | **7374.62 ms** | **8385.21 ms** | 4839.13 ms | **7071.70 ms** | **7957.55 ms** |
| Latency First | **Infron** | **4716.31 ms** | 7963.46 ms | 9700.74 ms | **3452.01 ms** | **6130.44 ms** | **8077.04 ms** |
| Latency First | OpenRouter | 5123.94 ms | **7437.43 ms** | **8328.80 ms** | 4865.67 ms | 7124.79 ms | 8211.71 ms |
| TTFT First | **Infron** | **4371.01 ms** | **7859.70 ms** | 9668.50 ms | **3308.84 ms** | **6277.24 ms** | **8130.10 ms** |
| TTFT First | OpenRouter | 5290.40 ms | 7983.31 ms | **8954.58 ms** | 5070.78 ms | 7718.23 ms | 8577.17 ms |

Mean deltas use bootstrap 95% CIs; p-values use paired sign-flip permutation tests.

| Routing mode | Metric | Mean delta | 95% CI | p-value | Pairs | Interpretation |
| --- | --- | --- | --- | --- | --- | --- |
| Throughput First | Latency: OpenRouter - Infron | **1145.60 ms** | 725.46 ms to 1593.91 ms | <0.001 | 200 | Positive means lower Infron latency |
| Throughput First | TTFT: OpenRouter - Infron | **1253.63 ms** | 821.31 ms to 1704.47 ms | <0.001 | 200 | Positive means lower Infron TTFT |
| Throughput First | Throughput: Infron - OpenRouter | **-0.1442 tok/s** | -0.3115 tok/s to 0.0211 tok/s | 0.0855 | 200 | Positive means higher Infron throughput |
| Throughput First | Cost: OpenRouter - Infron | **$-0.00310659** | $-0.00390526 to $-0.00242740 | <0.001 | 200 | Positive means lower Infron cost |
| Throughput First | Token Cache Hit: Infron - OpenRouter | **1.01 pp** | -0.97 pp to 3.01 pp | 0.2524 | 200 | Positive means higher Infron cache hit |
| Price First | Latency: OpenRouter - Infron | **-6687.16 ms** | -10536.36 ms to -3483.40 ms | <0.001 | 195 | Positive means lower Infron latency |
| Price First | TTFT: OpenRouter - Infron | **-4657.75 ms** | -8398.45 ms to -1592.26 ms | 0.0065 | 195 | Positive means lower Infron TTFT |
| Price First | Throughput: Infron - OpenRouter | **-0.6011 tok/s** | -0.8364 tok/s to -0.3715 tok/s | <0.001 | 195 | Positive means higher Infron throughput |
| Price First | Cost: OpenRouter - Infron | **$-0.00087758** | $-0.00153961 to $-0.00029056 | 0.0052 | 195 | Positive means lower Infron cost |
| Price First | Token Cache Hit: Infron - OpenRouter | **-4.48 pp** | -7.99 pp to -1.34 pp | 0.0105 | 195 | Positive means higher Infron cache hit |
| Latency First | Latency: OpenRouter - Infron | **312.37 ms** | -91.12 ms to 681.67 ms | 0.1197 | 193 | Positive means lower Infron latency |
| Latency First | TTFT: OpenRouter - Infron | **2417.48 ms** | 2093.52 ms to 2728.71 ms | <0.001 | 193 | Positive means lower Infron TTFT |
| Latency First | Throughput: Infron - OpenRouter | **-0.6766 tok/s** | -0.8531 tok/s to -0.5050 tok/s | <0.001 | 193 | Positive means higher Infron throughput |
| Latency First | Cost: OpenRouter - Infron | **$0.00029516** | $0.00021278 to $0.00036663 | <0.001 | 193 | Positive means lower Infron cost |
| Latency First | Token Cache Hit: Infron - OpenRouter | **-0.21 pp** | -1.29 pp to 0.38 pp | 1.0000 | 193 | Positive means higher Infron cache hit |
| TTFT First | Latency: OpenRouter - Infron | **1146.12 ms** | 764.77 ms to 1497.12 ms | <0.001 | 200 | Positive means lower Infron latency |
| TTFT First | TTFT: OpenRouter - Infron | **2858.40 ms** | 2535.21 ms to 3162.86 ms | <0.001 | 200 | Positive means lower Infron TTFT |
| TTFT First | Throughput: Infron - OpenRouter | **-0.4132 tok/s** | -0.5904 tok/s to -0.2386 tok/s | <0.001 | 200 | Positive means higher Infron throughput |
| TTFT First | Cost: OpenRouter - Infron | **$0.00010720** | $-0.00023742 to $0.00037466 | 0.5111 | 200 | Positive means lower Infron cost |
| TTFT First | Token Cache Hit: Infron - OpenRouter | **-0.62 pp** | -2.14 pp to 0.42 pp | 0.5049 | 200 | Positive means higher Infron cache hit |

### 4.2 Reasoning / Thinking Control Check

This run does not explicitly set reasoning/thinking parameters and keeps model/platform defaults; this table records reasoning telemetry under default behavior.

| Routing mode | Platform | Reasoning tokens | Avg reasoning tokens/request | Reasoning requests | Avg first reasoning token | Avg TTFT | Avg E2E latency |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Throughput First | **Infron** | **0** | **0.0000** | **0** | **0.00 ms** | **4992.94 ms** | **5311.71 ms** |
| Throughput First | OpenRouter | 6000 | 15.0000 | 400 | 5619.75 ms | 5619.75 ms | 5884.51 ms |
| Price First | Infron | **0** | **0.0000** | **0** | **0.00 ms** | 7224.73 ms | 8506.60 ms |
| Price First | **OpenRouter** | 5835 | 14.9615 | 389 | 4895.85 ms | **4895.85 ms** | **5163.02 ms** |
| Latency First | **Infron** | **0** | **0.0000** | **0** | **0.00 ms** | **3645.69 ms** | **4966.67 ms** |
| Latency First | OpenRouter | 5955 | 15.4275 | 386 | 4854.43 ms | 4854.43 ms | 5122.85 ms |
| TTFT First | **Infron** | **0** | **0.0000** | **0** | **0.00 ms** | **3596.32 ms** | **4758.14 ms** |
| TTFT First | OpenRouter | 6153 | 15.3825 | 400 | 5025.52 ms | 5025.52 ms | 5331.20 ms |

### 4.3 API Protocol Compatibility Matrix

This run uses `/v1/chat/completions`; this table records success response, usage, cost, and cache telemetry coverage for both platforms under that protocol.

| API protocol | Endpoint | Platform | Pairs | Requests | Success rate | Usage coverage | Token usage coverage | Cost coverage | Cache telemetry coverage | HTTP statuses | Top errors |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `chat_completions` | `/v1/chat/completions` | Infron | 800 | 1600 | **99.62%** | **100.00%** | **100.00%** | **100.00%** | **100.00%** | {"0":6,"200":1594} | 5 x The read operation timed out<br>1 x [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1000) |
| `chat_completions` | `/v1/chat/completions` | OpenRouter | 800 | 1600 | 99.44% | **100.00%** | **100.00%** | **100.00%** | **100.00%** | {"0":9,"200":1591} | 5 x [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1000)<br>4 x [Errno 54] Connection reset by peer |

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

    **Unified API Entry**OpenAI-compatible requests enter the gateway with usage, stream, and provider routing parameters
    →
    **Routing Policy Layer**Selects healthy upstream paths by throughput / price / latency / ttft objective
    →
    **Provider Stick / Cache Affinity**Repeated long prefixes are kept in stable cache domains where possible
    →
    **Upstream Provider**Response telemetry reports provider, usage, cost, latency, and TTFT

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
| Throughput First | Infron | 400 | 400 | `novita` 400 |
| Throughput First | OpenRouter | 400 | 400 | `StreamLake` 400 |
| Price First | Infron | 390 | 390 | `deepinfra` 340, `alibaba/cn` 50 |
| Price First | OpenRouter | 390 | 390 | `StreamLake` 389, `GMICloud` 1 |
| Latency First | Infron | 386 | 386 | `deepinfra` 386 |
| Latency First | OpenRouter | 386 | 386 | `StreamLake` 356, `DeepInfra` 30 |
| TTFT First | Infron | 400 | 400 | `deepinfra` 400 |
| TTFT First | OpenRouter | 400 | 400 | `StreamLake` 362, `DeepInfra` 31, `Baidu` 7 |

### Upstream Provider Detail Distribution

| Routing mode | Platform | Upstream provider | Requests | Share | first/second | Covered rounds | Avg TTFT | Avg latency | Prompt tokens | Completion tokens | Reasoning tokens | Cache-read tokens | Observed cost |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Throughput First | Infron | `novita` | 400 | 100.00% | 200/200 | 200 | 4992.94 ms | 5311.71 ms | 6414682 | 5357 | 0 | 6023296 | $1.61315300 |
| Throughput First | OpenRouter | `StreamLake` | 400 | 100.00% | 200/200 | 200 | 5619.75 ms | 5884.51 ms | 6414682 | 6400 | 6000 | 6136576 | $0.99183578 |
| Price First | Infron | `deepinfra` | 340 | 87.18% | 165/175 | 175 | 3392.45 ms | 4571.01 ms | 5509975 | 4395 | 0 | 5072832 | $0.88017800 |
| Price First | Infron | `alibaba/cn` | 50 | 12.82% | 30/20 | 30 | 33284.25 ms | 35268.63 ms | 530301 | 642 | 0 | 295424 | $0.11679200 |
| Price First | OpenRouter | `StreamLake` | 389 | 99.74% | 194/195 | 195 | 4890.95 ms | 5158.59 ms | 6002831 | 6224 | 5835 | 5983552 | $0.80333903 |
| Price First | OpenRouter | `GMICloud` | 1 | 0.26% | 1/0 | 1 | 6803.91 ms | 6883.60 ms | 37452 | 16 | 0 | 0 | $0.02250192 |
| Latency First | Infron | `deepinfra` | 386 | 100.00% | 193/193 | 193 | 3645.69 ms | 4966.67 ms | 6273860 | 5003 | 0 | 6249536 | $0.77495600 |
| Latency First | OpenRouter | `StreamLake` | 356 | 92.23% | 179/177 | 179 | 5045.97 ms | 5284.98 ms | 6114026 | 5696 | 5340 | 6105152 | $0.81128554 |
| Latency First | OpenRouter | `DeepInfra` | 30 | 7.77% | 14/16 | 16 | 2581.47 ms | 3198.99 ms | 159834 | 480 | 615 | 158880 | $0.02063640 |
| TTFT First | Infron | `deepinfra` | 400 | 100.00% | 200/200 | 200 | 3596.32 ms | 4758.14 ms | 6414682 | 5201 | 0 | 6285408 | $0.84264400 |
| TTFT First | OpenRouter | `StreamLake` | 362 | 90.50% | 181/181 | 182 | 5283.54 ms | 5564.29 ms | 6332869 | 5792 | 5430 | 6312768 | $0.84577285 |
| TTFT First | OpenRouter | `DeepInfra` | 31 | 7.75% | 15/16 | 17 | 2314.80 ms | 2897.23 ms | 62022 | 496 | 611 | 61056 | $0.00893800 |
| TTFT First | OpenRouter | `Baidu` | 7 | 1.75% | 4/3 | 5 | 3686.97 ms | 4056.14 ms | 19791 | 112 | 112 | 8448 | $0.00937370 |

### 7.1 Cache-Rate and Cost Divergence Drill-Down

This table combines cache, cost, provider distribution, and reasoning telemetry to explain routing-mode differences.

| Routing mode | Cache-hit delta | Infron cost multiple | Infron top path | OpenRouter top path | Reasoning token delta | Main attribution |
| --- | --- | --- | --- | --- | --- | --- |
| Throughput First | **+1.69 pp** | 1.63x | **`novita` 100.00%** | **`StreamLake` 100.00%** | **-6000** | Infron has higher cache but higher cost; inspect upstream unit price and completion/reasoning tokens |
| Price First | -3.83 pp | 1.21x | `deepinfra` 87.18% | **`StreamLake` 99.74%** | **-5835** | OpenRouter has higher cache and lower cost; provider/cache-domain mix is the main signal |
| Latency First | -0.23 pp | **0.93x** | **`deepinfra` 100.00%** | **`StreamLake` 92.23%** | **-5955** | Cache and cost move in different directions; evaluate with speed metrics |
| TTFT First | -0.27 pp | **0.98x** | **`deepinfra` 100.00%** | **`StreamLake` 90.50%** | **-6153** | Cache and cost move in different directions; evaluate with speed metrics |

## 8. Stratified Results: Prompt-Length Cache Performance

This section aggregates second-request cache-read tokens, token-level cache hit rate, observed cost, E2E latency, and Streaming TTFT by prompt-length tier. Bold cells mark the advantaged side within each tier.

### Prompt-Length Tier Overview

| Prompt length tier | Target tokens | Platform | Pairs | Second prompt tokens | Second cache read tokens | Token cache hit rate | Observed cost | Avg E2E latency | Avg TTFT |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `short` | 1500 | Infron | **265** | **466794** | 451616 | 96.75% | $0.17568300 | 4717.31 ms | **3737.61 ms** |
| `short` | 1500 | OpenRouter | **265** | **466794** | **457728** | **98.06%** | **$0.15285428** | **4144.39 ms** | 3863.12 ms |
| `medium` | 8000 | Infron | **265** | **2445560** | 2377760 | 97.23% | $0.80691000 | 5713.62 ms | **4668.79 ms** |
| `medium` | 8000 | OpenRouter | **265** | **2445560** | **2414592** | **98.73%** | **$0.71005725** | **5368.63 ms** | 5127.16 ms |
| `long` | 32000 | Infron | **258** | **9659396** | 9579360 | 99.17% | $3.24513000 | 7236.92 ms | **6211.62 ms** |
| `long` | 32000 | OpenRouter | **258** | **9659396** | **9613888** | **99.53%** | **$2.65077169** | **6657.73 ms** | 6349.72 ms |

### Prompt Length x Routing Mode Cache Hit Rate

| Prompt length tier | Routing mode | Infron | OpenRouter | Winner |
| --- | --- | --- | --- | --- |
| `short` | Throughput First | 96.63% | **98.10%** | **OpenRouter** |
| `short` | Price First | 93.95% | **98.10%** | **OpenRouter** |
| `short` | Latency First | **98.98%** | 98.10% | **Infron** |
| `short` | TTFT First | 97.53% | **97.94%** | **OpenRouter** |
| `medium` | Throughput First | **99.86%** | 96.88% | **Infron** |
| `medium` | Price First | 92.42% | **98.37%** | **OpenRouter** |
| `medium` | Latency First | 98.30% | **99.87%** | **OpenRouter** |
| `medium` | TTFT First | 98.37% | **99.86%** | **OpenRouter** |
| `long` | Throughput First | **99.92%** | 98.40% | **Infron** |
| `long` | Price First | 96.68% | **99.91%** | **OpenRouter** |
| `long` | Latency First | **99.96%** | 99.92% | **Infron** |
| `long` | TTFT First | **99.96%** | 99.92% | **Infron** |

## 9. Stratified Results: Group-Level Stability

### Throughput First

| Platform | Group | Rounds | Successful rounds | Token cache hit rate | Observed cost | P95 latency | P95 TTFT |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Infron | 1 | 50 | 50 | 99.62% | $0.62126500 | **8914.84 ms** | **8587.00 ms** |
| Infron | 2 | 50 | 50 | **99.85%** | $0.33495900 | 7957.49 ms | 7805.95 ms |
| Infron | 3 | 50 | 50 | **99.84%** | $0.33214400 | 9439.19 ms | 9017.67 ms |
| Infron | 4 | 50 | 50 | **99.84%** | $0.32478500 | 8212.44 ms | 8029.86 ms |
| OpenRouter | 1 | 50 | 50 | **99.84%** | **$0.30959630** | 12487.28 ms | 12033.90 ms |
| OpenRouter | 2 | 50 | 50 | 98.73% | **$0.22781642** | **7022.19 ms** | **6776.78 ms** |
| OpenRouter | 3 | 50 | 50 | 94.10% | **$0.24543220** | **9107.64 ms** | **8817.53 ms** |
| OpenRouter | 4 | 50 | 50 | **99.84%** | **$0.20899086** | **7794.67 ms** | **7290.17 ms** |

### Price First

| Platform | Group | Rounds | Successful rounds | Token cache hit rate | Observed cost | P95 latency | P95 TTFT |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Infron | 1 | 45 | 45 | 87.04% | $0.32151800 | 87203.15 ms | 82998.06 ms |
| Infron | 2 | 50 | 50 | **98.79%** | $0.26056300 | 10749.09 ms | 7560.04 ms |
| Infron | 3 | 50 | 50 | 95.09% | $0.22211700 | 7220.94 ms | **5011.36 ms** |
| Infron | 4 | 50 | 50 | 99.68% | **$0.19277200** | **5882.42 ms** | **4402.77 ms** |
| OpenRouter | 1 | 45 | 45 | **99.81%** | **$0.17744723** | **7879.73 ms** | **7585.10 ms** |
| OpenRouter | 2 | 50 | 50 | 98.73% | **$0.22302410** | **7733.01 ms** | **7034.32 ms** |
| OpenRouter | 3 | 50 | 50 | **99.84%** | **$0.21637876** | **6704.80 ms** | 6390.40 ms |
| OpenRouter | 4 | 50 | 50 | **99.84%** | $0.20899086 | 7257.05 ms | 7153.45 ms |

### Latency First

| Platform | Group | Rounds | Successful rounds | Token cache hit rate | Observed cost | P95 latency | P95 TTFT |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Infron | 1 | 50 | 50 | 98.73% | **$0.19645000** | 8331.75 ms | 6502.38 ms |
| Infron | 2 | 45 | 45 | **99.91%** | **$0.18854500** | 7858.70 ms | **5589.52 ms** |
| Infron | 3 | 49 | 49 | **99.91%** | **$0.19837800** | **7133.50 ms** | **5437.50 ms** |
| Infron | 4 | 49 | 49 | **99.90%** | **$0.19158300** | 8337.99 ms | **6631.28 ms** |
| OpenRouter | 1 | 50 | 50 | **99.84%** | $0.20897198 | **6611.28 ms** | **6450.22 ms** |
| OpenRouter | 2 | 45 | 45 | 99.86% | $0.19904936 | **7447.01 ms** | 7141.62 ms |
| OpenRouter | 3 | 49 | 49 | 99.84% | $0.21566118 | 7305.77 ms | 7092.93 ms |
| OpenRouter | 4 | 49 | 49 | 99.84% | $0.20823942 | **7455.78 ms** | 7164.70 ms |

### TTFT First

| Platform | Group | Rounds | Successful rounds | Token cache hit rate | Observed cost | P95 latency | P95 TTFT |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Infron | 1 | 50 | 50 | 99.68% | **$0.19290200** | **6925.38 ms** | **4657.72 ms** |
| Infron | 2 | 50 | 50 | 98.79% | $0.22294100 | **7377.62 ms** | **5495.93 ms** |
| Infron | 3 | 50 | 50 | **99.91%** | $0.23476100 | 8549.03 ms | **7605.03 ms** |
| Infron | 4 | 50 | 50 | **99.90%** | **$0.19204000** | **7022.95 ms** | **5339.84 ms** |
| OpenRouter | 1 | 50 | 50 | **99.84%** | $0.20960816 | 8273.97 ms | 8007.52 ms |
| OpenRouter | 2 | 50 | 50 | **99.85%** | **$0.22287306** | 7871.29 ms | 7588.82 ms |
| OpenRouter | 3 | 50 | 50 | 99.84% | **$0.21622772** | **8257.15 ms** | 7862.65 ms |
| OpenRouter | 4 | 50 | 50 | 99.81% | $0.21537561 | 7708.44 ms | 7375.08 ms |

## 10. Discussion: Business Value, Boundaries, and Engineering Implications

Business decisions should not rely on one metric. Stable long-context and high-frequency template workloads should prioritize cache rate and cost; realtime interaction must constrain TTFT and E2E latency; batch processing often prioritizes throughput and failure cost.

| Routing mode | Business objective | Observed result | Scenarios | Caveat |
| --- | --- | --- | --- | --- |
| Throughput First | Maximize output capacity per unit time | Infron leads overall (3/5 metrics) | Batch generation, offline summaries, backend processing | Good for throughput-first tasks; constrain cost and cache separately |
| Price First | Minimize request and token cost | OpenRouter leads overall (5/5 metrics) | High-frequency templates, support automation, marketing, RAG prefixes | First-token and E2E response are faster; check cache and cost |
| Latency First | Minimize full-response waiting time | Infron leads overall (3/5 metrics) | Online chat, agent chains, IDE/writing assistants, realtime tools | Good for throughput-first tasks; constrain cost and cache separately |
| TTFT First | Minimize streaming first-token time | Infron leads overall (3/5 metrics) | Streaming chat, realtime copilots, first-screen feedback | Good for throughput-first tasks; constrain cost and cache separately |

## 11. Conclusion

### Routing-Mode Conclusions

| Routing mode | Objective | Cache winner | Cost winner | Throughput winner | E2E latency winner | TTFT winner | Interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Throughput First | Maximize output capacity per unit time | **Infron** | **OpenRouter** | **OpenRouter** | **Infron** | **Infron** | Infron leads overall (3/5 metrics) |
| Price First | Minimize request and token cost | **OpenRouter** | **OpenRouter** | **OpenRouter** | **OpenRouter** | **OpenRouter** | OpenRouter leads overall (5/5 metrics) |
| Latency First | Minimize full-response waiting time | **OpenRouter** | **Infron** | **OpenRouter** | **Infron** | **Infron** | Infron leads overall (3/5 metrics) |
| TTFT First | Minimize streaming first-token time | **OpenRouter** | **Infron** | **OpenRouter** | **Infron** | **Infron** | Infron leads overall (3/5 metrics) |

## 12. Limitations, Missing Data, and Next Experiments

| Limitation | Impact | Next step | Current handling |
| --- | --- | --- | --- |
| Full routing trace | Cannot prove every provider choice, fallback, and retry path hop by hop | Add provider routing trace, decision logs, and fallback reasons | Use only returned provider fields and provider distribution |
| Longer time window | 4x50 observes short-window stability but not day-level drift | Add soak tests and repeated windows | Scope conclusions to this run |
| Production corpus | Built-in templates do not cover every workload distribution | Use sanitized production-stratified corpora | Discuss representative long-context templates only |
| Cost-field consistency | Cost coverage and semantics may differ by platform | Reconcile with billing and provider cost breakdown | Use only explicitly returned cost fields |

## 13. Reproducibility Appendix

| Artifact | Public link |
| --- | --- |
| Summary | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/summary.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/summary.json) |
| Paired dataset | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/benchmark_pairs.csv](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/benchmark_pairs.csv) |
| Request-level dataset | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/benchmark_requests.jsonl](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/benchmark_requests.jsonl) |
| Filtered structured records | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/records.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/records.json) |
| Excluded-record audit | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/records_excluded.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/records_excluded.json) |
| Test source | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/code/test_rerun_routing_sort_cache_cost_ab.py](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/code/test_rerun_routing_sort_cache_cost_ab.py) |
| Benchmark runner source | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/code/rerun_routing_sort_cache_cost_ab.py](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/code/rerun_routing_sort_cache_cost_ab.py) |
| HTML report renderer source | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/code/render_glm52_deepseek_style_report.py](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/code/render_glm52_deepseek_style_report.py) |
| Dataset reference | `business_representative` built-in representative business templates; request-level export is [benchmark_requests.jsonl](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/benchmark_requests.jsonl) |
| GitHub Pages Chinese report | [https://infronai.github.io/prompt-cache-bench/experiments/z-ai/glm-5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/reports/routing-cache-cost-streaming-performance-ab-study__glm-5__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-06.zh.html](https://infronai.github.io/prompt-cache-bench/experiments/z-ai/glm-5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/reports/routing-cache-cost-streaming-performance-ab-study__glm-5__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-06.zh.html) |
| GitHub Pages English report | [https://infronai.github.io/prompt-cache-bench/experiments/z-ai/glm-5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/reports/routing-cache-cost-streaming-performance-ab-study__glm-5__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-06.en.html](https://infronai.github.io/prompt-cache-bench/experiments/z-ai/glm-5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/reports/routing-cache-cost-streaming-performance-ab-study__glm-5__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-06.en.html) |
