# Infron vs OpenRouter Routing, Cache, Cost, and Streaming Performance A/B Report

## Executive Summary

This report evaluates `z-ai/glm-5.2` across Infron and OpenRouter in prompt-caching workloads. The experiment uses only `/v1/chat/completions`, keeps model/platform default reasoning and thinking behavior, and keeps prompt-length stratification enabled.

After A/B filtering, the analysis retains **757 paired samples** and **3028 request-level observations**. It excludes **86 records**.

Core finding: Infron leads observed cost in every routing mode. OpenRouter leads throughput, E2E latency, and Streaming TTFT in every routing mode. Cache-rate winners are split: Infron leads Throughput First and Price First, while OpenRouter slightly leads Latency First and TTFT First.

## Quality Gate

| Item | Value |
| --- | --- |
| Model | `z-ai/glm-5.2` |
| API protocol | `/v1/chat/completions` only |
| Groups / rounds | 4 groups x 50 rounds |
| Prompt tiers | `short` about 1500, `medium` about 8000, `long` about 32000 tokens |
| Reasoning / thinking | Default platform/model behavior; no explicit disable parameter |
| Pairing rule | strict sort/group/round pair with first/second usage.prompt_tokens deltas <= 50 |
| Retained pairs | 757 |
| Request-level rows | 3028 |
| Excluded records | 86 |

## Route-Level Result Matrix

| Routing mode | Pairs | Token cache hit rate | Observed cost | Throughput | E2E latency | TTFT |
| --- | ---: | --- | --- | --- | --- | --- |
| Throughput First | 186 | **Infron 94.17%** / OpenRouter 58.11% | **Infron $1.301319** / OpenRouter $4.617887 | Infron 1.756 tok/s / **OpenRouter 3.028 tok/s** | Infron 7726.33 ms / **OpenRouter 5284.79 ms** | Infron 7082.53 ms / **OpenRouter 4977.95 ms** |
| Price First | 190 | **Infron 99.58%** / OpenRouter 90.96% | **Infron $0.878579** / OpenRouter $1.521277 | Infron 2.029 tok/s / **OpenRouter 2.346 tok/s** | Infron 6974.85 ms / **OpenRouter 6821.29 ms** | Infron 6378.09 ms / **OpenRouter 6331.30 ms** |
| Latency First | 189 | Infron 99.58% / **OpenRouter 99.83%** | **Infron $0.868005** / OpenRouter $1.827801 | Infron 1.884 tok/s / **OpenRouter 5.129 tok/s** | Infron 7395.10 ms / **OpenRouter 3119.52 ms** | Infron 6710.94 ms / **OpenRouter 2709.15 ms** |
| TTFT First | 192 | Infron 99.62% / **OpenRouter 99.82%** | **Infron $0.872405** / OpenRouter $1.625334 | Infron 2.976 tok/s / **OpenRouter 4.892 tok/s** | Infron 4644.30 ms / **OpenRouter 3270.76 ms** | Infron 4023.05 ms / **OpenRouter 2866.14 ms** |

## API Protocol Record

| API protocol | Endpoint | Note |
| --- | --- | --- |
| `chat_completions` | `/v1/chat/completions` | This run keeps only the standard Chat Completions protocol; it does not include `/v1/messages` or `/v1/responses`. |

## Prompt-Length Stratified Cache Performance

| Tier | Pairs | Token cache hit rate | Call cache hit rate | E2E latency | TTFT | Reasoning tokens |
| --- | ---: | --- | --- | --- | --- | --- |
| short | 259 | **Infron 91.86%** / OpenRouter 84.29% | **Infron 97.30%** / OpenRouter 88.80% | Infron 5094.35 ms / **OpenRouter 3443.73 ms** | Infron 4437.02 ms / **OpenRouter 3031.17 ms** | **Infron 0** / OpenRouter 8845 |
| medium | 251 | **Infron 98.23%** / OpenRouter 86.34% | **Infron 98.41%** / OpenRouter 88.84% | Infron 6449.15 ms / **OpenRouter 4341.44 ms** | Infron 5771.49 ms / **OpenRouter 3938.75 ms** | **Infron 0** / OpenRouter 8815 |
| long | 247 | **Infron 98.61%** / OpenRouter 87.95% | **Infron 98.79%** / OpenRouter 90.28% | Infron 8556.78 ms / **OpenRouter 6133.46 ms** | Infron 7984.41 ms / **OpenRouter 5738.76 ms** | **Infron 0** / OpenRouter 8829 |

## Reasoning / Thinking Observation

This run does not explicitly disable or force reasoning/thinking. Reasoning tokens are treated as observed telemetry.

| Routing mode | Infron reasoning tokens | OpenRouter reasoning tokens | Infron avg/request | OpenRouter avg/request |
| --- | ---: | ---: | ---: | ---: |
| Throughput First | **0** | 8247 | **0.0000** | 22.1694 |
| Price First | **0** | 6078 | **0.0000** | 15.9947 |
| Latency First | **0** | 6034 | **0.0000** | 15.9630 |
| TTFT First | **0** | 6130 | **0.0000** | 15.9635 |

## Reproducibility References

| Artifact | GitHub path | SHA256 / Notes |
| --- | --- | --- |
| Summary | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5.2/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-04/data/summary.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5.2/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-04/data/summary.json) | `534296f46e82f6a2e15221593b519fb7ff8c03e45fc719d0b7a75f7c9137cef2` |
| Paired dataset CSV | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5.2/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-04/data/benchmark_pairs.csv](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5.2/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-04/data/benchmark_pairs.csv) | `f892a492f0d9857164dd1f6faf33205df393957cf851230c3cc695defb3dc2ad` |
| Request-level dataset JSONL | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5.2/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-04/data/benchmark_requests.jsonl](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5.2/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-04/data/benchmark_requests.jsonl) | `237b16fd9bc60c9fa7bc2c4e2365bf2b3bcfb1f88978b357c2cc955589c3143e` |
| Excluded-record audit | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5.2/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-04/data/records_excluded.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5.2/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-04/data/records_excluded.json) | `ee6b2fc4533de02d659e3c2f21f24a8b1a587a5a99e6e8cbd7cea7186c64e327` |
| Benchmark runner source | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5.2/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-04/code/rerun_routing_sort_cache_cost_ab.py](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5.2/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-04/code/rerun_routing_sort_cache_cost_ab.py) | `a485c5116e99375e6b171d0328e5a423babd1ee6b206c72f54053a3a045b1075` |
| HTML report renderer source | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5.2/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-04/code/render_glm52_deepseek_style_report.py](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5.2/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-04/code/render_glm52_deepseek_style_report.py) | `e5bb0d32361d70ee688e0d0a0da3302a1e542e33e53876c905814eb5c27b0532` |
| Test source | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5.2/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-04/code/test_rerun_routing_sort_cache_cost_ab.py](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5.2/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-04/code/test_rerun_routing_sort_cache_cost_ab.py) | Experiment code snapshot path |
| Reports directory | [https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/z-ai/glm-5.2/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-04/reports](https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/z-ai/glm-5.2/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-04/reports) | Bilingual HTML / Markdown / PDF reports |
| Data directory | [https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/z-ai/glm-5.2/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-04/data](https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/z-ai/glm-5.2/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-04/data) | Pair data, request telemetry, summary, and excluded records |
| Manifest | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5.2/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-04/metadata/manifest.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/z-ai/glm-5.2/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-04/metadata/manifest.json) | File sizes and SHA-256 checksums |

Dataset reference: `business_representative` built-in representative business templates; request-level export is `benchmark_requests.jsonl`.

Online HTML: Chinese [https://infronai.github.io/prompt-cache-bench/experiments/z-ai/glm-5.2/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-04/reports/routing-cache-cost-streaming-performance-ab-study__glm-5-2__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers__2026-07-04.zh.html](https://infronai.github.io/prompt-cache-bench/experiments/z-ai/glm-5.2/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-04/reports/routing-cache-cost-streaming-performance-ab-study__glm-5-2__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers__2026-07-04.zh.html); English [https://infronai.github.io/prompt-cache-bench/experiments/z-ai/glm-5.2/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-04/reports/routing-cache-cost-streaming-performance-ab-study__glm-5-2__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers__2026-07-04.en.html](https://infronai.github.io/prompt-cache-bench/experiments/z-ai/glm-5.2/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-2026-07-04/reports/routing-cache-cost-streaming-performance-ab-study__glm-5-2__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers__2026-07-04.en.html).
