# Infron vs OpenRouter Routing, Cache, Cost, and Streaming Performance A/B Test Report

## Abstract and Executive Outline

**Keywords**: Prompt Caching; A/B Testing; Provider Routing; Cache Affinity; Latency; Throughput; Cost Attribution; qwen3.6-35b-a3b

### Abstract

This report evaluates `qwen/qwen3.6-35b-a3b` on Infron and OpenRouter across cache reuse, observed cost, throughput, E2E latency, and Streaming TTFT under Prompt Caching workloads.

The main findings are: Infron and OpenRouter tie on Cache hit rate in all routing modes; Infron leads Observed cost in 1/4 routing modes; OpenRouter leads in 3/4; 0/4 tie; Infron leads Throughput in 1/4 routing modes; OpenRouter leads in 3/4; 0/4 tie; Infron leads E2E latency in all routing modes; Infron leads Streaming TTFT in 3/4 routing modes; OpenRouter leads in 1/4; 0/4 tie.

Overall, Infron's cross-mode strengths are Streaming TTFT, E2E latency, while OpenRouter's cross-mode strengths are throughput, observed cost. Platform choice should be driven by workload objective rather than a single headline metric.


### Figure 0: Normalized Capability Radar


The five radar axes represent throughput, price, E2E latency, Streaming TTFT, and cache hit rate. Every metric is normalized to a 0-100 score, with farther outward meaning better.



Thick solid lines show platform-level contours; translucent lines and points show individual routing modes.


Conclusion Overview: Core Metric Winners by Routing Mode


Based on strict A/B paired samples. Blue represents Infron, orange represents OpenRouter; gold cells mark the winner for the routing objective.


    **Throughput**OpenRouter wins 3/4Max advantage 59.66%, higher is better**Observed cost**OpenRouter wins 3/4Max advantage 39.08%, lower is better**E2E latency**Infron wins 4/4Max advantage 79.79%, lower is better**Streaming TTFT**Infron wins 3/4Max advantage 40.81%, lower is better**Cache hit rate**Tie in 4/4 modesMax advantage 0.00%, higher is better





| Routing mode | Throughput objective | Cost objective | Latency objective | TTFT objective | Cache result |
| --- | --- | --- | --- | --- | --- |
| **Throughput First**<br>throughput | OpenRouteradvantage 59.66% | Infronadvantage 39.08% | Infronadvantage 79.79% | OpenRouteradvantage 40.81% | Tietie |
| **Price First**<br>price | OpenRouteradvantage 8.40% | OpenRouteradvantage 6.98% | Infronadvantage 14.62% | Infronadvantage 14.31% | Tietie |
| **Latency First**<br>latency | OpenRouteradvantage 10.56% | OpenRouteradvantage 6.96% | Infronadvantage 12.78% | Infronadvantage 13.51% | Tietie |
| **TTFT First**<br>ttft | Infronadvantage 3.42% | OpenRouteradvantage 6.96% | Infronadvantage 28.90% | Infronadvantage 25.80% | Tietie |

### Executive Outline

| Dimension | Conclusion | Evidence |
| --- | --- | --- |
| Controls | First/second `usage.prompt_tokens` deltas are limited to 50 tokens within each `sort/group/round` pair. | Methods and data quality |
| Cache reuse | Infron and OpenRouter tie on Cache hit rate in all routing modes | Overall metrics and mechanism section |
| Observed cost | Infron leads Observed cost in 1/4 routing modes; OpenRouter leads in 3/4; 0/4 tie | Overall metrics and provider drill-down |
| Performance | Infron leads Throughput in 1/4 routing modes; OpenRouter leads in 3/4; 0/4 tie; Infron leads E2E latency in all routing modes; Infron leads Streaming TTFT in 3/4 routing modes; OpenRouter leads in 1/4; 0/4 tie | Charts and statistical tests |
| Attribution boundary | Claims use observable response telemetry: usage, cost, TTFT, latency, provider fields, and cache tokens. | Provider/Route drill-down |
| Business meaning | Long-context, RAG-prefix, agent-tool, and high-frequency template workloads should evaluate cache rate, cost, first-token latency, and E2E latency together. | Discussion and conclusion |

### Routing-Mode Conclusions

| Routing mode | Objective | Cache winner | Cost winner | Throughput winner | E2E latency winner | TTFT winner | Interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Throughput First | Maximize output capacity per unit time | **Tie** | **Infron** | **OpenRouter** | **Infron** | **OpenRouter** | Mixed result |
| Price First | Minimize request and token cost | **Tie** | **OpenRouter** | **OpenRouter** | **Infron** | **Infron** | Mixed result |
| Latency First | Minimize full-response waiting time | **Tie** | **OpenRouter** | **OpenRouter** | **Infron** | **Infron** | Mixed result |
| TTFT First | Minimize streaming first-token time | **Tie** | **OpenRouter** | **Infron** | **Infron** | **Infron** | Infron leads overall (3/5 metrics) |

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


    **Fixed Payload**Model qwen/qwen3.6-35b-a3b; payload SHA-256 is fixed within each routing mode
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
| Model | `qwen/qwen3.6-35b-a3b` |
| Provider model IDs | infron: `qwen/qwen3.6-35b-a3b`; openrouter: `qwen/qwen3.6-35b-a3b` |
| Platforms | Infron and OpenRouter |
| API protocol | `/v1/chat/completions` |
| Routing modes | Throughput First, Price First, Latency First, TTFT First |
| Groups | 4 |
| Rounds per group | 50 |
| Workers | 24 |
| Request mode | Streaming Chat Completions with TTFT collection |
| Reasoning / thinking control | No explicit reasoning/thinking parameter; model and platform defaults are preserved |
| Prompt length tiers | `short`≈1500, `medium`≈8000, `long`≈32000 |
| Excluded records | 44 |

## 4. Results: Overall Metrics and Main Findings

| Routing mode | Platform | Strict pairs | Total Input Tokens | Token cache hit rate | Observed cost | Throughput | E2E latency | Streaming TTFT |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Throughput First | Infron | 183 | 6518330 | **0.00%** | **$1.10165200** | 1.82 tok/s | **7012.66 ms** | 6295.91 ms |
| Throughput First | OpenRouter | 183 | 6517598 | **0.00%** | $1.53220679 | **110.28 tok/s** | 12607.91 ms | **4471.16 ms** |
| Price First | Infron | 198 | 6912806 | **0.00%** | $1.04198600 | 5.05 tok/s | **2550.52 ms** | **2154.21 ms** |
| Price First | OpenRouter | 198 | 6912014 | **0.00%** | **$0.97401796** | **5.47 tok/s** | 2923.52 ms | 2462.44 ms |
| Latency First | Infron | 199 | 6995010 | **0.00%** | $1.05411900 | 4.93 tok/s | **2601.72 ms** | **2207.81 ms** |
| Latency First | OpenRouter | 199 | 6994214 | **0.00%** | **$0.98555796** | **5.45 tok/s** | 2934.25 ms | 2506.11 ms |
| TTFT First | **Infron** | 198 | 7052586 | **0.00%** | $1.06273300 | **4.81 tok/s** | **2668.04 ms** | **2245.36 ms** |
| TTFT First | OpenRouter | 198 | 7051794 | **0.00%** | **$0.99358716** | 4.65 tok/s | 3439.11 ms | 2824.57 ms |

### 4.1 Tail Latency and Statistical Tests

Tail percentiles expose risk that averages hide.

| Routing mode | Platform | P50 latency | P95 latency | P99 latency | P50 TTFT | P95 TTFT | P99 TTFT |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Throughput First | Infron | **3225.24 ms** | 36021.12 ms | 76341.10 ms | **2607.03 ms** | 32788.62 ms | 75861.00 ms |
| Throughput First | OpenRouter | 8180.42 ms | **24318.35 ms** | **69734.35 ms** | 3561.57 ms | **10965.10 ms** | **18717.57 ms** |
| Price First | Infron | **2421.66 ms** | **3823.41 ms** | **5155.24 ms** | **2046.43 ms** | **3363.70 ms** | **4954.53 ms** |
| Price First | OpenRouter | 2754.80 ms | 4687.15 ms | 7454.65 ms | 2264.44 ms | 3915.50 ms | 7060.60 ms |
| Latency First | Infron | **2458.84 ms** | **4075.08 ms** | **6160.28 ms** | **2053.23 ms** | **3603.98 ms** | **5056.58 ms** |
| Latency First | OpenRouter | 2650.83 ms | 4688.94 ms | 6982.76 ms | 2268.77 ms | 3874.55 ms | 5812.22 ms |
| TTFT First | **Infron** | **2508.98 ms** | **4255.28 ms** | **5551.96 ms** | **2132.70 ms** | **3484.38 ms** | **4838.64 ms** |
| TTFT First | OpenRouter | 2985.83 ms | 6412.05 ms | 10396.74 ms | 2486.73 ms | 5304.79 ms | 8646.82 ms |

Mean deltas use bootstrap 95% CIs; p-values use paired sign-flip permutation tests.

| Routing mode | Metric | Mean delta | 95% CI | p-value | Pairs | Interpretation |
| --- | --- | --- | --- | --- | --- | --- |
| Throughput First | Latency: OpenRouter - Infron | **11190.50 ms** | 5095.00 ms to 18202.66 ms | <0.001 | 183 | Positive means lower Infron latency |
| Throughput First | TTFT: OpenRouter - Infron | **-3649.50 ms** | -6439.99 ms to -1011.78 ms | 0.0130 | 183 | Positive means lower Infron TTFT |
| Throughput First | Throughput: Infron - OpenRouter | **-61.3866 tok/s** | -69.0973 tok/s to -54.0288 tok/s | <0.001 | 183 | Positive means higher Infron throughput |
| Throughput First | Cost: OpenRouter - Infron | **$0.00235276** | $0.00104649 to $0.00405145 | <0.001 | 183 | Positive means lower Infron cost |
| Throughput First | Token Cache Hit: Infron - OpenRouter | 0.00 pp | 0.00 pp to 0.00 pp | 1.0000 | 183 | Positive means higher Infron cache hit |
| Price First | Latency: OpenRouter - Infron | **745.99 ms** | 509.43 ms to 980.71 ms | <0.001 | 198 | Positive means lower Infron latency |
| Price First | TTFT: OpenRouter - Infron | **616.47 ms** | 407.90 ms to 827.36 ms | <0.001 | 198 | Positive means lower Infron TTFT |
| Price First | Throughput: Infron - OpenRouter | **-0.6455 tok/s** | -0.9905 tok/s to -0.2833 tok/s | <0.001 | 198 | Positive means higher Infron throughput |
| Price First | Cost: OpenRouter - Infron | **$-0.00034327** | $-0.00038772 to $-0.00029569 | <0.001 | 198 | Positive means lower Infron cost |
| Price First | Token Cache Hit: Infron - OpenRouter | 0.00 pp | 0.00 pp to 0.00 pp | 1.0000 | 198 | Positive means higher Infron cache hit |
| Latency First | Latency: OpenRouter - Infron | **665.05 ms** | 286.41 ms to 1140.86 ms | <0.001 | 199 | Positive means lower Infron latency |
| Latency First | TTFT: OpenRouter - Infron | **596.61 ms** | 242.28 ms to 1040.33 ms | <0.001 | 199 | Positive means lower Infron TTFT |
| Latency First | Throughput: Infron - OpenRouter | **-0.8180 tok/s** | -1.1561 tok/s to -0.4885 tok/s | <0.001 | 199 | Positive means higher Infron throughput |
| Latency First | Cost: OpenRouter - Infron | **$-0.00034453** | $-0.00039038 to $-0.00029616 | <0.001 | 199 | Positive means lower Infron cost |
| Latency First | Token Cache Hit: Infron - OpenRouter | 0.00 pp | 0.00 pp to 0.00 pp | 1.0000 | 199 | Positive means higher Infron cache hit |
| TTFT First | Latency: OpenRouter - Infron | **1542.14 ms** | 999.45 ms to 2239.81 ms | <0.001 | 198 | Positive means lower Infron latency |
| TTFT First | TTFT: OpenRouter - Infron | **1158.43 ms** | 687.84 ms to 1810.62 ms | <0.001 | 198 | Positive means lower Infron TTFT |
| TTFT First | Throughput: Infron - OpenRouter | **-0.2542 tok/s** | -0.6401 tok/s to 0.1419 tok/s | 0.1987 | 198 | Positive means higher Infron throughput |
| TTFT First | Cost: OpenRouter - Infron | **$-0.00034922** | $-0.00039530 to $-0.00030316 | <0.001 | 198 | Positive means lower Infron cost |
| TTFT First | Token Cache Hit: Infron - OpenRouter | 0.00 pp | 0.00 pp to 0.00 pp | 1.0000 | 198 | Positive means higher Infron cache hit |

### 4.2 Reasoning / Thinking Control Check

This run does not explicitly set reasoning/thinking parameters and keeps model/platform defaults; this table records reasoning telemetry under default behavior.

| Routing mode | Platform | Reasoning tokens | Avg reasoning tokens/request | Reasoning requests | Avg first reasoning token | Avg TTFT | Avg E2E latency |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Throughput First | Infron | **0** | **0.0000** | **0** | **0.00 ms** | 6295.91 ms | **7012.66 ms** |
| Throughput First | OpenRouter | 497478 | 1359.2295 | 366 | 4471.16 ms | **4471.16 ms** | 12607.91 ms |
| Price First | Infron | **0** | **0.0000** | **0** | **0.00 ms** | **2154.21 ms** | **2550.52 ms** |
| Price First | OpenRouter | 6508 | 16.4343 | 396 | 2462.44 ms | 2462.44 ms | 2923.52 ms |
| Latency First | Infron | **0** | **0.0000** | **0** | **0.00 ms** | **2207.81 ms** | **2601.72 ms** |
| Latency First | OpenRouter | 6625 | 16.6457 | 398 | 2506.11 ms | 2506.11 ms | 2934.25 ms |
| TTFT First | **Infron** | **0** | **0.0000** | **0** | **0.00 ms** | **2245.36 ms** | **2668.04 ms** |
| TTFT First | OpenRouter | 6492 | 16.3939 | 396 | 2824.57 ms | 2824.57 ms | 3439.11 ms |

### 4.3 API Protocol Compatibility Matrix

This run uses `/v1/chat/completions`; this table records success response, usage, cost, and cache telemetry coverage for both platforms under that protocol.

| API protocol | Endpoint | Platform | Pairs | Requests | Success rate | Usage coverage | Token usage coverage | Cost coverage | Cache telemetry coverage | HTTP statuses | Top errors |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `chat_completions` | `/v1/chat/completions` | Infron | 800 | 1600 | **99.81%** | **100.00%** | **100.00%** | **100.00%** | **100.00%** | {"0":3,"200":1597} | 3 x Remote end closed connection without response |
| `chat_completions` | `/v1/chat/completions` | OpenRouter | 800 | 1600 | 98.81% | **100.00%** | **100.00%** | **100.00%** | **100.00%** | {"0":19,"200":1581} | 10 x Remote end closed connection without response<br>6 x [SYS] unknown error (_ssl.c:2406) |

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
| Throughput First | Infron | 366 | 366 | `deepinfra` 250, `wafer` 69, `alibaba/cn` 47 |
| Throughput First | OpenRouter | 366 | 366 | `AtlasCloud` 333, `AkashML` 33 |
| Price First | Infron | 396 | 396 | `deepinfra` 395, `alibaba/cn` 1 |
| Price First | OpenRouter | 396 | 396 | `AkashML` 396 |
| Latency First | Infron | 398 | 398 | `deepinfra` 398 |
| Latency First | OpenRouter | 398 | 398 | `AkashML` 398 |
| TTFT First | Infron | 396 | 396 | `deepinfra` 396 |
| TTFT First | OpenRouter | 396 | 396 | `AkashML` 396 |

### Upstream Provider Detail Distribution

| Routing mode | Platform | Upstream provider | Requests | Share | first/second | Covered rounds | Avg TTFT | Avg latency | Prompt tokens | Completion tokens | Reasoning tokens | Cache-read tokens | Observed cost |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Throughput First | Infron | `deepinfra` | 250 | 68.31% | 120/130 | 130 | 2681.55 ms | 3414.00 ms | 4568041 | 3202 | 0 | 0 | $0.68825800 |
| Throughput First | Infron | `wafer` | 69 | 18.85% | 32/37 | 41 | 3479.64 ms | 3834.30 ms | 1245543 | 894 | 0 | 0 | $0.23777200 |
| Throughput First | Infron | `alibaba/cn` | 47 | 12.84% | 31/16 | 31 | 29655.76 ms | 30820.56 ms | 704746 | 570 | 0 | 0 | $0.17562200 |
| Throughput First | OpenRouter | `AtlasCloud` | 333 | 90.98% | 166/167 | 174 | 4507.65 ms | 13411.27 ms | 6061381 | 508380 | 496950 | 0 | $1.46780841 |
| Throughput First | OpenRouter | `AkashML` | 33 | 9.02% | 17/16 | 24 | 4102.93 ms | 4501.19 ms | 456217 | 528 | 528 | 0 | $0.06439838 |
| Price First | Infron | `deepinfra` | 395 | 99.75% | 198/197 | 198 | 2133.21 ms | 2529.38 ms | 6910808 | 5084 | 0 | 0 | $1.04146700 |
| Price First | Infron | `alibaba/cn` | 1 | 0.25% | 0/1 | 1 | 10447.95 ms | 10900.24 ms | 1998 | 16 | 0 | 0 | $0.00051900 |
| Price First | OpenRouter | `AkashML` | 396 | 100.00% | 198/198 | 198 | 2462.44 ms | 2923.52 ms | 6912014 | 6336 | 6508 | 0 | $0.97401796 |
| Latency First | Infron | `deepinfra` | 398 | 100.00% | 199/199 | 199 | 2207.81 ms | 2601.72 ms | 6995010 | 5107 | 0 | 0 | $1.05411900 |
| Latency First | OpenRouter | `AkashML` | 398 | 100.00% | 199/199 | 199 | 2506.11 ms | 2934.25 ms | 6994214 | 6368 | 6625 | 0 | $0.98555796 |
| TTFT First | Infron | `deepinfra` | 396 | 100.00% | 198/198 | 198 | 2245.36 ms | 2668.04 ms | 7052586 | 5083 | 0 | 0 | $1.06273300 |
| TTFT First | OpenRouter | `AkashML` | 396 | 100.00% | 198/198 | 198 | 2824.57 ms | 3439.11 ms | 7051794 | 6336 | 6492 | 0 | $0.99358716 |

### 7.1 Cache-Rate and Cost Divergence Drill-Down

This table combines cache, cost, provider distribution, and reasoning telemetry to explain routing-mode differences.

| Routing mode | Cache-hit delta | Infron cost multiple | Infron top path | OpenRouter top path | Reasoning token delta | Main attribution |
| --- | --- | --- | --- | --- | --- | --- |
| Throughput First | +0.00 pp | **0.72x** | **`deepinfra` 68.31%** | `AtlasCloud` 90.98% | **-497478** | Cache is tied; Infron leads cost |
| Price First | +0.00 pp | 1.07x | `deepinfra` 99.75% | **`AkashML` 100.00%** | **-6508** | Infron has higher cache but higher cost; inspect upstream unit price and completion/reasoning tokens |
| Latency First | +0.00 pp | 1.07x | `deepinfra` 100.00% | **`AkashML` 100.00%** | **-6625** | Infron has higher cache but higher cost; inspect upstream unit price and completion/reasoning tokens |
| TTFT First | +0.00 pp | 1.07x | `deepinfra` 100.00% | **`AkashML` 100.00%** | **-6492** | Infron has higher cache but higher cost; inspect upstream unit price and completion/reasoning tokens |

## 8. Stratified Results: Prompt-Length Cache Performance

This section aggregates second-request cache-read tokens, token-level cache hit rate, observed cost, E2E latency, and Streaming TTFT by prompt-length tier. Bold cells mark the advantaged side within each tier.

### Prompt-Length Tier Overview

| Prompt length tier | Target tokens | Platform | Pairs | Second prompt tokens | Second cache read tokens | Token cache hit rate | Observed cost | Avg E2E latency | Avg TTFT |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `short` | 1500 | Infron | **261** | **520226** | **0** | **0.00%** | **$0.16818700** | **2626.43 ms** | 2150.90 ms |
| `short` | 1500 | OpenRouter | **261** | 519704 | **0** | **0.00%** | $0.23414636 | 4128.76 ms | **2135.23 ms** |
| `medium` | 8000 | Infron | **261** | **2695686** | **0** | **0.00%** | **$0.84264700** | **3585.30 ms** | 3134.25 ms |
| `medium` | 8000 | OpenRouter | **261** | 2695164 | **0** | **0.00%** | $0.86707414 | 4570.77 ms | **2867.67 ms** |
| `long` | 32000 | Infron | **256** | **10523454** | **0** | **0.00%** | **$3.24965600** | **4738.56 ms** | 4231.23 ms |
| `long` | 32000 | OpenRouter | **256** | 10522942 | **0** | **0.00%** | $3.38414936 | 7345.25 ms | **4132.85 ms** |

### Prompt Length x Routing Mode Cache Hit Rate

| Prompt length tier | Routing mode | Infron | OpenRouter | Winner |
| --- | --- | --- | --- | --- |
| `short` | Throughput First | **0.00%** | **0.00%** | tie |
| `short` | Price First | **0.00%** | **0.00%** | tie |
| `short` | Latency First | **0.00%** | **0.00%** | tie |
| `short` | TTFT First | **0.00%** | **0.00%** | tie |
| `medium` | Throughput First | **0.00%** | **0.00%** | tie |
| `medium` | Price First | **0.00%** | **0.00%** | tie |
| `medium` | Latency First | **0.00%** | **0.00%** | tie |
| `medium` | TTFT First | **0.00%** | **0.00%** | tie |
| `long` | Throughput First | **0.00%** | **0.00%** | tie |
| `long` | Price First | **0.00%** | **0.00%** | tie |
| `long` | Latency First | **0.00%** | **0.00%** | tie |
| `long` | TTFT First | **0.00%** | **0.00%** | tie |

## 9. Stratified Results: Group-Level Stability

### Throughput First

| Platform | Group | Rounds | Successful rounds | Token cache hit rate | Observed cost | P95 latency | P95 TTFT |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Infron | 1 | 47 | 47 | **0.00%** | $0.35669800 | 73376.27 ms | 72495.67 ms |
| Infron | 2 | 40 | 40 | **0.00%** | **$0.24394300** | **6182.79 ms** | **5152.62 ms** |
| Infron | 3 | 47 | 47 | **0.00%** | **$0.25199500** | **4571.83 ms** | **3892.25 ms** |
| Infron | 4 | 49 | 49 | **0.00%** | **$0.24901600** | **8015.77 ms** | **7220.52 ms** |
| OpenRouter | 1 | 47 | 47 | **0.00%** | **$0.35412248** | **22642.47 ms** | **6602.13 ms** |
| OpenRouter | 2 | 40 | 40 | **0.00%** | $0.37283790 | 49693.37 ms | 15145.92 ms |
| OpenRouter | 3 | 47 | 47 | **0.00%** | $0.39045837 | 23305.84 ms | 14300.73 ms |
| OpenRouter | 4 | 49 | 49 | **0.00%** | $0.41478804 | 21569.67 ms | 8358.01 ms |

### Price First

| Platform | Group | Rounds | Successful rounds | Token cache hit rate | Observed cost | P95 latency | P95 TTFT |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Infron | 1 | 50 | 50 | **0.00%** | $0.26138200 | **4012.04 ms** | **3623.15 ms** |
| Infron | 2 | 49 | 49 | **0.00%** | $0.26077100 | **3735.29 ms** | **3180.65 ms** |
| Infron | 3 | 49 | 49 | **0.00%** | $0.25824800 | **3307.70 ms** | **3015.72 ms** |
| Infron | 4 | 50 | 50 | **0.00%** | $0.26158500 | **4484.52 ms** | **3658.20 ms** |
| OpenRouter | 1 | 50 | 50 | **0.00%** | **$0.24438268** | 4842.60 ms | 3906.73 ms |
| OpenRouter | 2 | 49 | 49 | **0.00%** | **$0.24379264** | 5080.44 ms | 3800.59 ms |
| OpenRouter | 3 | 49 | 49 | **0.00%** | **$0.24145996** | 4072.86 ms | 3655.39 ms |
| OpenRouter | 4 | 50 | 50 | **0.00%** | **$0.24438268** | 4691.89 ms | 4065.72 ms |

### Latency First

| Platform | Group | Rounds | Successful rounds | Token cache hit rate | Observed cost | P95 latency | P95 TTFT |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Infron | 1 | 50 | 50 | **0.00%** | $0.26137700 | **3842.13 ms** | **3463.32 ms** |
| Infron | 2 | 50 | 50 | **0.00%** | $0.27311400 | **3785.03 ms** | **3108.52 ms** |
| Infron | 3 | 49 | 49 | **0.00%** | $0.25824800 | 4396.24 ms | 3999.43 ms |
| Infron | 4 | 50 | 50 | **0.00%** | $0.26138000 | **4441.58 ms** | **4002.67 ms** |
| OpenRouter | 1 | 50 | 50 | **0.00%** | **$0.24438268** | 3945.06 ms | 3576.85 ms |
| OpenRouter | 2 | 50 | 50 | **0.00%** | **$0.25533460** | 5305.07 ms | 4201.66 ms |
| OpenRouter | 3 | 49 | 49 | **0.00%** | **$0.24145800** | **4291.32 ms** | **3744.03 ms** |
| OpenRouter | 4 | 50 | 50 | **0.00%** | **$0.24438268** | 4492.70 ms | 4136.66 ms |

### TTFT First

| Platform | Group | Rounds | Successful rounds | Token cache hit rate | Observed cost | P95 latency | P95 TTFT |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Infron | 1 | 50 | 50 | **0.00%** | $0.26138100 | **4463.60 ms** | **3702.31 ms** |
| Infron | 2 | 49 | 49 | **0.00%** | $0.26998800 | **3683.86 ms** | **3276.06 ms** |
| Infron | 3 | 49 | 49 | **0.00%** | $0.26998300 | **4366.89 ms** | **3803.62 ms** |
| Infron | 4 | 50 | 50 | **0.00%** | $0.26138100 | **4235.40 ms** | **3382.72 ms** |
| OpenRouter | 1 | 50 | 50 | **0.00%** | **$0.24438268** | 6985.50 ms | 5304.65 ms |
| OpenRouter | 2 | 49 | 49 | **0.00%** | **$0.25241188** | 5527.35 ms | 4761.40 ms |
| OpenRouter | 3 | 49 | 49 | **0.00%** | **$0.25240992** | 5720.04 ms | 4630.07 ms |
| OpenRouter | 4 | 50 | 50 | **0.00%** | **$0.24438268** | 6419.30 ms | 4805.62 ms |

## 10. Discussion: Business Value, Boundaries, and Engineering Implications

Business decisions should not rely on one metric. Stable long-context and high-frequency template workloads should prioritize cache rate and cost; realtime interaction must constrain TTFT and E2E latency; batch processing often prioritizes throughput and failure cost.

| Routing mode | Business objective | Observed result | Scenarios | Caveat |
| --- | --- | --- | --- | --- |
| Throughput First | Maximize output capacity per unit time | Mixed result | Batch generation, offline summaries, backend processing | Good for throughput-first tasks; constrain cost and cache separately |
| Price First | Minimize request and token cost | Mixed result | High-frequency templates, support automation, marketing, RAG prefixes | Good for throughput-first tasks; constrain cost and cache separately |
| Latency First | Minimize full-response waiting time | Mixed result | Online chat, agent chains, IDE/writing assistants, realtime tools | Good for throughput-first tasks; constrain cost and cache separately |
| TTFT First | Minimize streaming first-token time | Infron leads overall (3/5 metrics) | Streaming chat, realtime copilots, first-screen feedback | Decide with budget, SLA, and cache stability together |

## 11. Conclusion

### Routing-Mode Conclusions

| Routing mode | Objective | Cache winner | Cost winner | Throughput winner | E2E latency winner | TTFT winner | Interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Throughput First | Maximize output capacity per unit time | **Tie** | **Infron** | **OpenRouter** | **Infron** | **OpenRouter** | Mixed result |
| Price First | Minimize request and token cost | **Tie** | **OpenRouter** | **OpenRouter** | **Infron** | **Infron** | Mixed result |
| Latency First | Minimize full-response waiting time | **Tie** | **OpenRouter** | **OpenRouter** | **Infron** | **Infron** | Mixed result |
| TTFT First | Minimize streaming first-token time | **Tie** | **OpenRouter** | **Infron** | **Infron** | **Infron** | Infron leads overall (3/5 metrics) |

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
| Summary | [summary.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.6-35b-a3b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/summary.json) |
| Paired dataset | [benchmark_pairs.csv](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.6-35b-a3b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/benchmark_pairs.csv) |
| Request-level dataset | [benchmark_requests.jsonl](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.6-35b-a3b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/benchmark_requests.jsonl) |
| Filtered structured records | [records.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.6-35b-a3b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/records.json) |
| Excluded-record audit | [records_excluded.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.6-35b-a3b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/records_excluded.json) |
| Test source | [test_rerun_routing_sort_cache_cost_ab.py](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.6-35b-a3b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/code/test_rerun_routing_sort_cache_cost_ab.py) |
| Benchmark runner source | [rerun_routing_sort_cache_cost_ab.py](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.6-35b-a3b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/code/rerun_routing_sort_cache_cost_ab.py) |
| HTML report renderer source | [render_glm52_deepseek_style_report.py](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.6-35b-a3b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/code/render_glm52_deepseek_style_report.py) |
| Dataset reference | `business_representative`; request-level export is [benchmark_requests.jsonl](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.6-35b-a3b/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/benchmark_requests.jsonl) |
