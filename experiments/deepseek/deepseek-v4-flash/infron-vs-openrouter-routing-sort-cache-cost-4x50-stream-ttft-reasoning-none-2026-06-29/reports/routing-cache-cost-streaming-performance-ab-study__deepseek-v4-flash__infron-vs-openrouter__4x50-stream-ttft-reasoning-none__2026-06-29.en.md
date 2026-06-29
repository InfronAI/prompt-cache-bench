# deepseek-v4-flash Routing, Prompt Caching, and Streaming TTFT A/B Benchmark Report

## Abstract and Executive Outline

This report evaluates `deepseek/deepseek-v4-flash` on Infron and OpenRouter across provider routing, prompt caching, observed cost, throughput, E2E latency, and Streaming TTFT. The experiment uses 4 groups, 50 rounds per group, and streaming requests. Each round sends two identical requests to each platform, then retains only strict A/B pairs with exactly equal `usage.prompt_tokens`.

The final analysis keeps 797 strict A/B pairs and 3188 request-level observations. Data-quality rules exclude 6 records. All core metrics are derived from response-returned telemetry: `usage.prompt_tokens`, cache tokens, cost fields, E2E latency, Streaming TTFT, and provider fields.

![Impossible quadrilateral](../figures/inference_impossible_quadrilateral.en.svg)

Figure 0: The inference-platform impossible quadrilateral. The chart compares throughput, price, E2E latency, and Streaming TTFT, showing how routing modes move across multi-objective trade-offs.

![Conclusion overview](../figures/conclusion_overview.en.svg)

Figure A: Conclusion overview. The matrix shows winners for cache hit rate, observed cost, throughput, E2E latency, and Streaming TTFT under each routing mode.

### Routing-Mode Conclusions

| Routing mode | Objective winner | Cache hit rate | Observed cost | Throughput | E2E latency | Streaming TTFT |
| --- | --- | --- | --- | --- | --- | --- |
| Throughput First | **Infron** | **OpenRouter** (13.64%) | **OpenRouter** (23.27%) | **Infron** (675.35%) | **OpenRouter** (93.21%) | **Infron** (13.70%) |
| Price First | **OpenRouter** | **OpenRouter** (1213.63%) | **OpenRouter** (205.97%) | **Infron** (1334.94%) | **OpenRouter** (62.87%) | **Infron** (27.67%) |
| Latency First | **Infron** | **Infron** (14.60%) | **Infron** (9.15%) | **Infron** (152.73%) | **Infron** (91.34%) | **Infron** (97.83%) |
| TTFT First | **OpenRouter** | **Infron** (0.97%) | **Infron** (22.42%) | **Infron** (179.67%) | **OpenRouter** (62.03%) | **OpenRouter** (42.74%) |

### Core Metric Winner Summary

| Metric | Infron-winning modes | OpenRouter-winning modes | Largest advantage |
| --- | --- | --- | --- |
| Cache hit rate | Latency First, TTFT First | Throughput First, Price First | OpenRouter 1213.63% |
| Observed cost | Latency First, TTFT First | Throughput First, Price First | OpenRouter 205.97% |
| Throughput | Throughput First, Price First, Latency First, TTFT First | - | Infron 1334.94% |
| E2E latency | Latency First | Throughput First, Price First, TTFT First | OpenRouter 93.21% |
| Streaming TTFT | Throughput First, Price First, Latency First | TTFT First | Infron 97.83% |

### Reasoning Control and Cache/Cost Attribution Summary

This run explicitly sets `reasoning.effort=none` on every request to control Thinking/Reasoning effects on Streaming TTFT, E2E latency, and throughput. Response telemetry shows Infron / Throughput First: 65934; Infron / Price First: 102730; Infron / TTFT First: 16447. OpenRouter / Throughput First; OpenRouter / Price First; Infron / Latency First; OpenRouter / Latency First; OpenRouter / TTFT First report zero reasoning tokens.

| Routing mode | Cache-hit delta | Infron cost multiple | Infron top upstream path | OpenRouter top upstream path | Reasoning-token delta | Primary attribution |
| --- | ---: | ---: | --- | --- | ---: | --- |
| Throughput First | -11.00 pp | 1.23x | `alibaba/cn` 57.00%, `fireworks` 30.50% | `Alibaba` 99.50%, `Fireworks` 0.50% | 65,934 | Weaker cache affinity than OpenRouter plus nonzero response-side reasoning tokens jointly increased observed cost. |
| Price First | -83.61 pp | 3.06x | `alibaba/cn` 100.00% | `GMICloud` 98.99%, `DigitalOcean` 0.50% | 102,730 | Weaker cache affinity than OpenRouter plus nonzero response-side reasoning tokens jointly increased observed cost. |
| Latency First | +12.67 pp | 0.92x | `fireworks` 100.00% | `GMICloud` 75.75%, `Cloudflare` 19.50% | 0 | Cache affinity and upstream price path jointly produce a cost advantage. |
| TTFT First | +0.79 pp | 0.82x | `fireworks` 82.32%, `alibaba/cn` 17.68% | `Cloudflare` 97.98%, `Parasail` 1.26% | 16,447 | Cache affinity and upstream price path jointly produce a cost advantage. |

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
| Throughput First | Infron | 200 | 657312 | 80.64% | $0.03119800 | **34.54 tok/s** | 5182.69 ms | **2185.81 ms** | 13069.44 ms | 19099.79 ms |
| Throughput First | OpenRouter | 200 | 657312 | **91.63%** | **$0.02530937** | 4.46 tok/s | **2682.41 ms** | 2485.29 ms | 3846.13 ms | 4930.68 ms |
| Price First | Infron | 199 | 654020 | 6.89% | $0.05729000 | **39.26 tok/s** | 6918.70 ms | **3077.02 ms** | 12625.87 ms | 17557.83 ms |
| Price First | OpenRouter | 199 | 654020 | **90.50%** | **$0.01872401** | 2.74 tok/s | **4247.97 ms** | 3928.34 ms | 7858.67 ms | 11465.22 ms |
| Latency First | Infron | 200 | 657312 | **99.44%** | **$0.02325700** | **7.63 tok/s** | **2097.07 ms** | **1794.06 ms** | 3743.97 ms | 4886.88 ms |
| Latency First | OpenRouter | 200 | 657312 | 86.77% | $0.02538584 | 3.02 tok/s | 4012.61 ms | 3549.11 ms | 8971.72 ms | 14784.79 ms |
| TTFT First | Infron | 198 | 650734 | **81.98%** | **$0.02832900** | **12.37 tok/s** | 4562.48 ms | 3615.03 ms | 10735.07 ms | 27416.20 ms |
| TTFT First | OpenRouter | 198 | 650734 | 81.20% | $0.03468097 | 4.42 tok/s | **2815.78 ms** | **2532.65 ms** | 5697.46 ms | 8340.43 ms |

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
| Throughput First | Infron | 400 | 400 | `alibaba/cn` 228, `fireworks` 122, `alibaba/us` 44, `gmicloud` 6 |
| Throughput First | OpenRouter | 400 | 400 | `Alibaba` 398, `Fireworks` 2 |
| Price First | Infron | 398 | 398 | `alibaba/cn` 398 |
| Price First | OpenRouter | 398 | 398 | `GMICloud` 394, `DigitalOcean` 2, `DeepInfra` 1, `Wafer` 1 |
| Latency First | Infron | 400 | 400 | `fireworks` 400 |
| Latency First | OpenRouter | 400 | 400 | `GMICloud` 303, `Cloudflare` 78, `WandB` 11, `Morph` 6, `Parasail` 2 |
| TTFT First | Infron | 396 | 396 | `fireworks` 326, `alibaba/cn` 70 |
| TTFT First | OpenRouter | 396 | 396 | `Cloudflare` 388, `Parasail` 5, `WandB` 3 |

### Cache-Hit and Observed-Cost Attribution Drill-Down

- **Throughput First**: Weaker cache affinity than OpenRouter plus nonzero response-side reasoning tokens jointly increased observed cost.
- **Price First**: Weaker cache affinity than OpenRouter plus nonzero response-side reasoning tokens jointly increased observed cost.
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