# Infron vs OpenRouter Routing, Cache, Cost and Streaming A/B Report

## Executive Summary

This report evaluates `deepseek/deepseek-v4-flash` across Infron and OpenRouter under Prompt Caching workloads. The run keeps the routing, stream, group and round design unchanged, adds prompt-length stratification, and uses platform/model default reasoning behavior without sending an explicit `reasoning` or `thinking` control field.

After the A/B quality gate, the dataset retains **789 paired samples** and **3156 request-level observations**. The run excluded **22 records**: 11 incomplete records and 11 records whose paired `usage.prompt_tokens` delta exceeded the 50-token tolerance.

Core finding: Infron wins cost in every routing mode and wins token-level cache hit rate in `price`, `latency`, and `ttft`; OpenRouter wins throughput in every routing mode and wins TTFT in `throughput` and `ttft`. Prompt-length stratification shows Infron winning cache hit rate and cost in short, medium, and long prompt tiers, with the cache-rate gap increasing on longer prompts.

![Conclusion overview](../routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_20260702_rerun/charts/conclusion_overview.svg)

## 1. Experiment Quality Gate

| Item | Value |
| --- | --- |
| Model | `deepseek/deepseek-v4-flash` |
| Streaming | `True` |
| Groups / rounds | 4 groups x 50 rounds |
| Prompt length tiers | short=1500, medium=8000, long=32000 |
| A/B pairing | strict sort/group/round pair with first/second usage.prompt_tokens deltas <= 50 |
| Pair tolerance | 50 prompt tokens |
| Retained request rows | 3156 |
| Retained paired rows | 789 |
| Excluded records | 22 |
| Reasoning / thinking | Platform default; payload includes reasoning = `False` |

## 2. Route-Level Result Matrix

### Throughput First

| Metric | Infron | OpenRouter | Winner |
| --- | ---: | ---: | --- |
| Token cache hit rate | 75.64% | **90.94%** | **OpenRouter** |
| Actual cost | **$0.24870300** | $0.28981075 | **Infron** |
| Throughput | 2.30 tok/s | **19.09 tok/s** | **OpenRouter** |
| Latency | 5308.59 ms | **4581.42 ms** | **OpenRouter** |
| TTFT | 4994.47 ms | **3515.80 ms** | **OpenRouter** |

### Price First

| Metric | Infron | OpenRouter | Winner |
| --- | ---: | ---: | --- |
| Token cache hit rate | **88.29%** | 75.66% | **Infron** |
| Actual cost | **$0.18655200** | $0.27711419 | **Infron** |
| Throughput | 2.38 tok/s | **22.17 tok/s** | **OpenRouter** |
| Latency | **5212.66 ms** | 6875.58 ms | **Infron** |
| TTFT | **4950.45 ms** | 4953.93 ms | **Infron** |

### Latency First

| Metric | Infron | OpenRouter | Winner |
| --- | ---: | ---: | --- |
| Token cache hit rate | **86.89%** | 43.70% | **Infron** |
| Actual cost | **$0.17911600** | $0.52384433 | **Infron** |
| Throughput | 3.60 tok/s | **5.17 tok/s** | **OpenRouter** |
| Latency | **3450.91 ms** | 4727.19 ms | **Infron** |
| TTFT | **3177.64 ms** | 3877.73 ms | **Infron** |

### Ttft First

| Metric | Infron | OpenRouter | Winner |
| --- | ---: | ---: | --- |
| Token cache hit rate | **86.33%** | 36.46% | **Infron** |
| Actual cost | **$0.18308300** | $0.65891935 | **Infron** |
| Throughput | 3.66 tok/s | **4.39 tok/s** | **OpenRouter** |
| Latency | **3365.26 ms** | 3843.74 ms | **Infron** |
| TTFT | 3100.55 ms | **2956.95 ms** | **OpenRouter** |

## 3. Prompt-Length Stratified Cache Results

| Tier | Target prompt tokens | Pairs | Infron cache | OpenRouter cache | Cache winner | Infron cost | OpenRouter cost | Cost winner |
| --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | --- |
| short | 1500 | 267 | **78.29%** | 64.32% | **Infron** | **$0.03816800** | $0.07663082 | **Infron** |
| medium | 8000 | 264 | **81.23%** | 63.76% | **Infron** | **$0.16902100** | $0.34062648 | **Infron** |
| long | 32000 | 258 | **85.39%** | 61.13% | **Infron** | **$0.59026500** | $1.33243133 | **Infron** |

Across tiers, Infron keeps the stronger cache and cost profile. The cache-rate delta is 13.97 percentage points on short prompts, 17.46 points on medium prompts, and 24.26 points on long prompts, indicating that longer reusable prefixes amplify provider stickiness and cache-affinity effects.

## 4. Reasoning / Thinking Observation

This run does not explicitly disable or configure reasoning/thinking. The request payload keeps the platform default behavior, and response-side reasoning telemetry is treated as an observation rather than a controlled variable.

| Field | Value |
| --- | --- |
| Mode | `platform_default` |
| Payload includes reasoning field | `False` |
| Requested effort | `None` |
| Description | The request does not explicitly set reasoning.effort. It preserves the model and platform default reasoning behavior, and response-side reasoning tokens are recorded as an observed variable. |

## 5. Reproducibility References

| Artifact | Path | SHA-256 / Notes |
| --- | --- | --- |
| Runner source | `scripts/rerun_routing_sort_cache_cost_ab.py` | A/B runner and Markdown generator |
| HTML renderer | `scripts/render_glm52_deepseek_style_report.py` | ECharts report renderer |
| Report standard | `docs/ab-report-standard.md` | Project A/B report template standard |
| Request dataset | `export/deepseek_v4_flash_all_experiments/routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_20260702_rerun/benchmark_requests.jsonl` | `06d4f1fe318b450c71fc8809e095e7b5db3dcc6f87aeefed997a443d04ea317d` |
| Pair dataset | `export/deepseek_v4_flash_all_experiments/routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_20260702_rerun/benchmark_pairs.csv` | `32994cb3d660b93085e03aab095a24fcf1046671c1c3dd8ec5a17ff84d641627` |
| Summary | `export/deepseek_v4_flash_all_experiments/routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_20260702_rerun/summary.json` | Aggregated telemetry and chart source |

## Reproducibility Appendix

| Artifact | Link |
| --- | --- |
| Chinese HTML report | [GitHub Pages](https://infronai.github.io/prompt-cache-bench/experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-02/reports/routing-cache-cost-streaming-performance-ab-study__deepseek-v4-flash__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers__2026-07-02.zh.html) |
| English HTML report | [GitHub Pages](https://infronai.github.io/prompt-cache-bench/experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-02/reports/routing-cache-cost-streaming-performance-ab-study__deepseek-v4-flash__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers__2026-07-02.en.html) |
| Chinese Markdown | [GitHub](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-02/reports/routing-cache-cost-streaming-performance-ab-study__deepseek-v4-flash__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers__2026-07-02.zh.md) |
| English Markdown | [GitHub](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-02/reports/routing-cache-cost-streaming-performance-ab-study__deepseek-v4-flash__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers__2026-07-02.en.md) |
| Data directory | [GitHub](https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-02/data) |
| Code snapshot | [GitHub](https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-02/code) |
| Manifest | [GitHub](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-02/metadata/manifest.json) |
