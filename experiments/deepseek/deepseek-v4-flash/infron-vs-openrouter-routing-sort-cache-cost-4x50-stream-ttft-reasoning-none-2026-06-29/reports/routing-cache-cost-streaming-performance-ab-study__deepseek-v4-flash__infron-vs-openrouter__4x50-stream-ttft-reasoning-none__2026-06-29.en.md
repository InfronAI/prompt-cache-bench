# deepseek-v4-flash Routing, Prompt Caching, and Streaming TTFT A/B Benchmark Report

> Canonical interactive report: [English HTML on GitHub Pages](https://infronai.github.io/prompt-cache-bench/experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-none-2026-06-29/reports/routing-cache-cost-streaming-performance-ab-study__deepseek-v4-flash__infron-vs-openrouter__4x50-stream-ttft-reasoning-none__2026-06-29.en.html). This Markdown file is a lightweight index; the HTML version contains the updated ECharts-based figures and interactive report layout.


## Abstract and Executive Outline

This report evaluates `deepseek/deepseek-v4-flash` on Infron and OpenRouter across provider routing, prompt caching, observed cost, throughput, E2E latency, and Streaming TTFT. The experiment uses 4 groups, 50 rounds per group, and streaming requests. Each round sends two identical requests to each platform, then retains only strict A/B pairs with exactly equal `usage.prompt_tokens`.

The final analysis keeps 761 strict A/B pairs and 3044 request-level observations. Data-quality rules exclude 78 records. All core metrics are derived from response-returned telemetry: `usage.prompt_tokens`, cache tokens, cost fields, E2E latency, Streaming TTFT, and provider fields.

![Impossible quadrilateral](../figures/inference_impossible_quadrilateral.en.svg)

Figure 0: The inference-platform impossible quadrilateral. The chart compares throughput, price, E2E latency, and Streaming TTFT, showing how routing modes move across multi-objective trade-offs.

![Conclusion overview](../figures/conclusion_overview.en.svg)

Figure A: Conclusion overview. The matrix shows winners for cache hit rate, observed cost, throughput, E2E latency, and Streaming TTFT under each routing mode.

### Routing-Mode Conclusions

| Routing mode | Objective winner | Cache hit rate | Observed cost | Throughput | E2E latency | Streaming TTFT |
| --- | --- | --- | --- | --- | --- | --- |
| Throughput First | **OpenRouter** | **Infron** (0.42%) | **Infron** (42.25%) | **OpenRouter** (28.24%) | **OpenRouter** (28.11%) | **OpenRouter** (24.65%) |
| Price First | **Infron** | **Infron** (13.66%) | **Infron** (80.59%) | **OpenRouter** (331.85%) | **OpenRouter** (209.52%) | **OpenRouter** (235.90%) |
| Latency First | **Infron** | **Infron** (17.81%) | **Infron** (206.50%) | **Infron** (86.90%) | **Infron** (90.92%) | **Infron** (110.18%) |
| TTFT First | **OpenRouter** | **Infron** (38.41%) | **Infron** (388.03%) | **OpenRouter** (47.04%) | **OpenRouter** (43.66%) | **OpenRouter** (46.68%) |

### Core Metric Winner Summary

| Metric | Infron-winning modes | OpenRouter-winning modes | Largest advantage |
| --- | --- | --- | --- |
| Cache hit rate | Throughput First, Price First, Latency First, TTFT First | - | Infron 38.41% |
| Observed cost | Throughput First, Price First, Latency First, TTFT First | - | Infron 388.03% |
| Throughput | Latency First | Throughput First, Price First, TTFT First | OpenRouter 331.85% |
| E2E latency | Latency First | Throughput First, Price First, TTFT First | OpenRouter 209.52% |
| Streaming TTFT | Latency First | Throughput First, Price First, TTFT First | OpenRouter 235.90% |

### Reasoning Control and Cache/Cost Attribution Summary

This run explicitly sets `reasoning.effort=none` on every request to control Thinking/Reasoning effects on Streaming TTFT, E2E latency, and throughput. Response telemetry shows OpenRouter / Price First: 276. Infron / Throughput First; OpenRouter / Throughput First; Infron / Price First; Infron / Latency First; OpenRouter / Latency First; Infron / TTFT First; OpenRouter / TTFT First report zero reasoning tokens.

| Routing mode | Cache-hit delta | Infron cost multiple | Infron top upstream path | OpenRouter top upstream path | Reasoning-token delta | Primary attribution |
| --- | ---: | ---: | --- | --- | ---: | --- |
| Throughput First | +0.39 pp | 0.70x | `deepseek` 46.45%, `alibaba/sg` 30.87% | `Alibaba` 99.45%, `Fireworks` 0.27% | 0 | Cache affinity and upstream price path jointly produce a cost advantage. |
| Price First | +10.77 pp | 0.55x | `alibaba/cn` 70.68%, `deepseek` 29.32% | `GMICloud` 98.95%, `DigitalOcean` 0.52% | -276 | Cache affinity and upstream price path jointly produce a cost advantage. |
| Latency First | +14.13 pp | 0.33x | `deepseek` 100.00% | `GMICloud` 78.35%, `Cloudflare` 19.07% | 0 | Cache affinity and upstream price path jointly produce a cost advantage. |
| TTFT First | +25.94 pp | 0.20x | `deepseek` 100.00% | `Cloudflare` 87.31%, `WandB` 11.14% | 0 | Cache affinity and upstream price path jointly produce a cost advantage. |

## 1. Research Background

LLM inference-platform behavior is shaped not only by the model, but also by provider routing, prompt caching, streaming response handling, cost attribution, and fallback policy. For long-context, RAG, agent-tool, and stable system-prompt workloads, cache hit rate directly affects unit economics. Interactive products must also control E2E latency, Streaming TTFT, and throughput.

This study treats the inference platform as an observable system. The goal is not a single leaderboard score, but a controlled comparison of speed, cost, cache reuse, and first-token experience under different routing objectives.

## 2. Experimental Design, Dataset, and Controls

The experiment uses built-in representative business prompt templates covering stable long prefixes, RAG support, agent tool instructions, marketing automation, and code review. Each round contains a first request and a second request: the first establishes or refreshes cache state; the second observes cache reuse.

![Experiment flow](../figures/experiment_flow.en.svg)

Figure 1: Experimental flow. The same payload is sent to Infron and OpenRouter under each routing mode, and final aggregation uses only strict paired samples.

![A/B pairing filter](../figures/ab_pairing.en.svg)

Figure 2: A/B pairing filter. HTTP failures, incomplete records, `usage.prompt_tokens <= 0`, and unequal input-token pairs are excluded.

Core request shape:

```json
{
  "model": "deepseek/deepseek-v4-flash",
  "messages": [
    {
      "role": "system",
      "content": "<stable long prefix for cache probing>"
    },
    {
      "role": "user",
      "content": "Reply with exactly: cache probe ok"
    }
  ],
  "temperature": 0,
  "max_tokens": 320,
  "stream": true,
  "stream_options": {
    "include_usage": true
  },
  "usage": {
    "include": true
  },
  "reasoning": {
    "effort": "none"
  },
  "provider": {
    "sort": "throughput | price | latency | ttft",
    "allow_fallbacks": true
  }
}
```

Controlled-variable rule: within the same `sort/group/round`, both platforms must have exactly equal `usage.prompt_tokens` for the first and second requests. Total Input Tokens are computed from response-returned `usage.prompt_tokens`, not from local tokenizer estimates.

## 3. Experimental Environment and Data Quality

| Item | Configuration |
| --- | --- |
| Model | `deepseek/deepseek-v4-flash` |
| Platforms | Infron and OpenRouter |
| Routing modes | Throughput First, Price First, Latency First, TTFT First |
| Routing parameter mapping | Infron: `throughput, price, latency, ttft`; OpenRouter: `throughput, price, latency, latency` |
| Groups | 4 |
| Rounds per group | 50 |
| Workers | 4 |
| Request mode | Streaming Chat Completions with `stream_options.include_usage` and `usage.include` |
| Reasoning / thinking control | Every request explicitly includes `reasoning.effort=none`; response telemetry is used to verify whether reasoning tokens are still returned |
| Local network environment | Both platforms use the same local proxy: `socks5://127.0.0.1:1086` |
| Dataset | `business_representative`, Built-in representative business prompt templates |

## 4. Metric Definitions

| Metric | Definition | Direction |
| --- | --- | --- |
| Total Input Tokens | Sum of response-side `usage.prompt_tokens` for included requests | Control variable |
| Token cache hit rate | Second-request cache-read tokens / second-request prompt tokens | Higher is better |
| Observed cost | Sum of response-returned cost or cost breakdown | Lower is better |
| Throughput | Completion tokens / E2E latency seconds; reasoning is included when present in response usage | Higher is better |
| E2E latency | Elapsed time from request send to full response completion | Lower is better |
| Streaming TTFT | Time to first streamed chunk/token | Lower is better |

## 5. Core Metric Overview

| Routing mode | Platform | Strict paired rounds | Total Input Tokens | Token cache hit rate | Observed cost | Throughput | E2E latency | Streaming TTFT | P95 E2E latency | P99 E2E latency |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Throughput First | Infron | 183 | 601418 | **93.36%** | **$0.01549500** | 3.47 tok/s | 3530.87 ms | 3009.48 ms | 7547.27 ms | 10419.68 ms |
| Throughput First | OpenRouter | 183 | 601418 | 92.96% | $0.02204184 | **4.45 tok/s** | **2756.05 ms** | **2414.39 ms** | 4238.60 ms | 6676.47 ms |
| Price First | Infron | 191 | 627718 | **89.56%** | **$0.01342600** | 0.88 tok/s | 13452.75 ms | 13056.77 ms | 48793.74 ms | 68831.23 ms |
| Price First | OpenRouter | 191 | 627718 | 78.79% | $0.02424667 | **3.80 tok/s** | **4346.36 ms** | **3887.05 ms** | 8909.52 ms | 15111.11 ms |
| Latency First | Infron | 194 | 637616 | **93.47%** | **$0.00891300** | **4.59 tok/s** | **2630.68 ms** | **2172.98 ms** | 3517.18 ms | 4176.09 ms |
| Latency First | OpenRouter | 194 | 637616 | 79.34% | $0.02731861 | 2.46 tok/s | 5022.49 ms | 4567.21 ms | 10295.12 ms | 12937.33 ms |
| TTFT First | Infron | 193 | 634314 | **93.47%** | **$0.00886700** | 2.42 tok/s | 5006.64 ms | 4478.16 ms | 8032.61 ms | 10035.73 ms |
| TTFT First | OpenRouter | 193 | 634314 | 67.53% | $0.04327400 | **3.56 tok/s** | **3485.10 ms** | **3053.07 ms** | 6750.53 ms | 9059.90 ms |

## 6. Routing-Mode Drill-Down

### Throughput First

![Throughput First](../figures/throughput_first.en.svg)

![Throughput First radar](../figures/throughput_first_radar.en.svg)

### Price First

![Price First](../figures/price_first.en.svg)

![Price First radar](../figures/price_first_radar.en.svg)

### Latency First

![Latency First](../figures/latency_first.en.svg)

![Latency First radar](../figures/latency_first_radar.en.svg)

### TTFT First

![TTFT First](../figures/ttft_first.en.svg)

![TTFT First radar](../figures/ttft_first_radar.en.svg)


## 7. Core Metric Trend Charts

The charts are grouped by routing mode. Each chart compares E2E latency, throughput, observed cost, cache hit rate, and Streaming TTFT, with per-round curves where available.

![Throughput First trends](../figures/throughput_first_curves.en.svg)

![Price First trends](../figures/price_first_curves.en.svg)

![Latency First trends](../figures/latency_first_curves.en.svg)

![TTFT First trends](../figures/ttft_first_curves.en.svg)

## 8. Provider Routing Drill-Down

| Routing mode | Platform | Total requests | Attributed requests | Provider distribution |
| --- | --- | ---: | ---: | --- |
| Throughput First | Infron | 366 | 366 | `deepseek` 170, `alibaba/sg` 113, `fireworks` 83 |
| Throughput First | OpenRouter | 366 | 366 | `Alibaba` 364, `Fireworks` 1, `Novita` 1 |
| Price First | Infron | 382 | 382 | `alibaba/cn` 270, `deepseek` 112 |
| Price First | OpenRouter | 382 | 382 | `GMICloud` 378, `DigitalOcean` 2, `SiliconFlow` 2 |
| Latency First | Infron | 388 | 388 | `deepseek` 388 |
| Latency First | OpenRouter | 388 | 388 | `GMICloud` 304, `Cloudflare` 74, `WandB` 10 |
| TTFT First | Infron | 386 | 386 | `deepseek` 386 |
| TTFT First | OpenRouter | 386 | 386 | `Cloudflare` 337, `WandB` 43, `Parasail` 3, `Baidu` 2, `Novita` 1 |

### Cache-Hit and Observed-Cost Attribution Drill-Down

- **Throughput First**: Cache affinity and upstream price path jointly produce a cost advantage.
- **Price First**: Cache affinity and upstream price path jointly produce a cost advantage.
- **Latency First**: Cache affinity and upstream price path jointly produce a cost advantage.
- **TTFT First**: Cache affinity and upstream price path jointly produce a cost advantage.

## 9. Infron Technical Mechanism

![Infron architecture](../figures/infron_architecture.en.svg)

Figure 12: Infron architecture. Provider Stick and Cache Affinity make repeated long prefixes more likely to land in the same healthy cache domain.

![Provider Stick and cache affinity](../figures/provider_stick_cache_affinity.en.svg)

Figure 13: Provider Stick and cache affinity. This mechanism does not disable fallback; it preserves cache-domain stability within the healthy provider set.

![Cost-control mechanism](../figures/infron_cost_control.en.svg)

Figure 14: Cost-control mechanism. Observed cost is jointly determined by token processing, cache reads/writes, and upstream provider price.

## 10. Business Implications

Cache hit rate is most relevant to long-context, repeated system-prompt, RAG-prefix, and batch workloads. E2E latency and Streaming TTFT are most relevant to interactive products. Throughput matters for long-output and batch generation. Observed cost matters for budget-sensitive workloads. Routing mode should therefore follow the business KPI rather than a single average metric.

## 11. Limitations and Future Work

This run uses representative built-in business templates and does not cover every production corpus. Future work can add significance tests, longer time windows, concurrency stress tests, more models, more provider pairs, and finer upstream routing-trace and cost-breakdown evidence.

## 12. Reproducibility Appendix

| Artifact | Path |
| --- | --- |
| Chinese HTML report | [GitHub Pages](https://infronai.github.io/prompt-cache-bench/experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-none-2026-06-29/reports/routing-cache-cost-streaming-performance-ab-study__deepseek-v4-flash__infron-vs-openrouter__4x50-stream-ttft-reasoning-none__2026-06-29.zh.html) |
| English HTML report | [GitHub Pages](https://infronai.github.io/prompt-cache-bench/experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-none-2026-06-29/reports/routing-cache-cost-streaming-performance-ab-study__deepseek-v4-flash__infron-vs-openrouter__4x50-stream-ttft-reasoning-none__2026-06-29.en.html) |
| Chinese Markdown | [GitHub](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-none-2026-06-29/reports/routing-cache-cost-streaming-performance-ab-study__deepseek-v4-flash__infron-vs-openrouter__4x50-stream-ttft-reasoning-none__2026-06-29.zh.md) |
| English Markdown | [GitHub](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-none-2026-06-29/reports/routing-cache-cost-streaming-performance-ab-study__deepseek-v4-flash__infron-vs-openrouter__4x50-stream-ttft-reasoning-none__2026-06-29.en.md) |
| Data directory | [GitHub](https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-none-2026-06-29/data) |
| Paired dataset | [benchmark_pairs.csv](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-none-2026-06-29/data/benchmark_pairs.csv) |
| Request-level dataset | [benchmark_requests.jsonl](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-none-2026-06-29/data/benchmark_requests.jsonl) |
| Summary | [summary.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-none-2026-06-29/data/summary.json) |
| Experiment code | [rerun_routing_sort_cache_cost_ab.py](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-none-2026-06-29/code/rerun_routing_sort_cache_cost_ab.py) |
| Figure directory | [figures](https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-none-2026-06-29/figures) |
| Manifest | [manifest.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-none-2026-06-29/metadata/manifest.json) |