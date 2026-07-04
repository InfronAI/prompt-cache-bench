# Infron vs OpenRouter Routing, Cache, Cost, and Streaming Performance A/B Report

## Executive Summary

This report evaluates `openai/gpt-5.4-mini` across Infron and OpenRouter in prompt-caching workloads. The experiment uses only `/v1/chat/completions`, keeps model/platform default reasoning and thinking behavior, and keeps prompt-length stratification enabled.

After A/B filtering, the analysis retains **792 paired samples** and **3168 request-level observations**. It excludes **16 records**.

Core finding: Infron leads throughput in every routing mode and has lower cost in most routing modes. OpenRouter generally has lower E2E latency and Streaming TTFT. Cache hit rates are high on both platforms, with route-specific winners.

## Quality Gate

| Item | Value |
| --- | --- |
| Model | `openai/gpt-5.4-mini` |
| API protocol | `/v1/chat/completions` only |
| Groups / rounds | 4 groups x 50 rounds |
| Prompt tiers | `short` about 1500, `medium` about 8000, `long` about 32000 tokens |
| Reasoning / thinking | Default platform/model behavior; no explicit disable parameter |
| Pairing rule | strict sort/group/round pair with first/second usage.prompt_tokens deltas <= 50 |
| Retained pairs | 792 |
| Request-level rows | 3168 |
| Excluded records | 16 |

## Route-Level Result Matrix

| Routing mode | Pairs | Token cache hit rate | Observed cost | Throughput | E2E latency | TTFT |
| --- | ---: | --- | --- | --- | --- | --- |
| Throughput First | 200 | Infron 96.68% / **OpenRouter 97.91%** | **Infron $0.665196** / OpenRouter $0.736837 | **Infron 17.822 tok/s** / OpenRouter 5.076 tok/s | Infron 4042.33 ms / **OpenRouter 2737.70 ms** | Infron 2722.39 ms / **OpenRouter 2337.97 ms** |
| Price First | 200 | **Infron 97.99%** / OpenRouter 97.95% | **Infron $0.549838** / OpenRouter $0.643934 | **Infron 18.259 tok/s** / OpenRouter 4.922 tok/s | Infron 3896.09 ms / **OpenRouter 2830.58 ms** | Infron 2763.05 ms / **OpenRouter 2492.73 ms** |
| Latency First | 192 | **Infron 97.98%** / OpenRouter 96.73% | **Infron $0.514386** / OpenRouter $0.642328 | **Infron 20.873 tok/s** / OpenRouter 5.189 tok/s | Infron 3465.18 ms / **OpenRouter 2690.54 ms** | Infron 2473.68 ms / **OpenRouter 2350.08 ms** |
| TTFT First | 200 | Infron 96.43% / **OpenRouter 97.99%** | Infron $0.868611 / **OpenRouter $0.579755** | **Infron 25.861 tok/s** / OpenRouter 6.077 tok/s | Infron 2694.75 ms / **OpenRouter 2301.99 ms** | Infron 2141.42 ms / **OpenRouter 2098.17 ms** |

## API Protocol Record

| API protocol | Endpoint | Note |
| --- | --- | --- |
| `chat_completions` | `/v1/chat/completions` | This run keeps only the standard Chat Completions protocol; it does not include `/v1/messages` or `/v1/responses`. |

## Prompt-Length Stratified Cache Performance

| Tier | Pairs | Token cache hit rate | Call cache hit rate | E2E latency | TTFT | Reasoning tokens |
| --- | ---: | --- | --- | --- | --- | --- |
| short |  | **Infron 0.00%** / OpenRouter 0.00% | **Infron 0.00%** / OpenRouter 0.00% | **Infron 0.00 ms** / OpenRouter 0.00 ms | **Infron 0.00 ms** / OpenRouter 0.00 ms | **Infron 0** / OpenRouter 0 |
| medium |  | **Infron 0.00%** / OpenRouter 0.00% | **Infron 0.00%** / OpenRouter 0.00% | **Infron 0.00 ms** / OpenRouter 0.00 ms | **Infron 0.00 ms** / OpenRouter 0.00 ms | **Infron 0** / OpenRouter 0 |
| long |  | **Infron 0.00%** / OpenRouter 0.00% | **Infron 0.00%** / OpenRouter 0.00% | **Infron 0.00 ms** / OpenRouter 0.00 ms | **Infron 0.00 ms** / OpenRouter 0.00 ms | **Infron 0** / OpenRouter 0 |

## Reasoning / Thinking Observation

This run does not explicitly disable or force reasoning/thinking. Reasoning tokens are treated as observed telemetry.

| Routing mode | Reasoning tokens | Avg reasoning tokens/request |
| --- | --- | --- |
| Throughput First | **Infron 0** / OpenRouter 0 | **Infron 0.0000** / OpenRouter 0.0000 |
| Price First | **Infron 0** / OpenRouter 0 | **Infron 0.0000** / OpenRouter 0.0000 |
| Latency First | **Infron 0** / OpenRouter 0 | **Infron 0.0000** / OpenRouter 0.0000 |
| TTFT First | **Infron 0** / OpenRouter 0 | **Infron 0.0000** / OpenRouter 0.0000 |

## Reproducibility References

| Artifact | GitHub path | SHA256 / Notes |
| --- | --- | --- |
| Summary | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-5.4-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/data/summary.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-5.4-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/data/summary.json) | `b5fcdd6787abbc331d2a4326ce6473a0bd40226faa9adc3bf370bfa1c381faf3` |
| Paired dataset CSV | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-5.4-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/data/benchmark_pairs.csv](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-5.4-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/data/benchmark_pairs.csv) | `3bd26737e7ca08438856d3d9f6367df63ac391adc7e0db841c81ae34a3880c23` |
| Request-level dataset JSONL | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-5.4-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/data/benchmark_requests.jsonl](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-5.4-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/data/benchmark_requests.jsonl) | `4ff92a2e44c3d37cf6eb732ca00a85393114c4712ec35780b884899c551f93b5` |
| Excluded-record audit | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-5.4-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/data/records_excluded.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-5.4-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/data/records_excluded.json) | `11e2ed24815a7cf38765b2149b9d28bd51f312a36dbcedad6ef6d32b1648c138` |
| Benchmark runner source | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-5.4-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/code/rerun_routing_sort_cache_cost_ab.py](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-5.4-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/code/rerun_routing_sort_cache_cost_ab.py) | `a485c5116e99375e6b171d0328e5a423babd1ee6b206c72f54053a3a045b1075` |
| HTML report renderer source | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-5.4-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/code/render_glm52_deepseek_style_report.py](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-5.4-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/code/render_glm52_deepseek_style_report.py) | `e5bb0d32361d70ee688e0d0a0da3302a1e542e33e53876c905814eb5c27b0532` |
| Test source | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-5.4-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/code/test_rerun_routing_sort_cache_cost_ab.py](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-5.4-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/code/test_rerun_routing_sort_cache_cost_ab.py) | `c086ddc5d0a9a91eba82b7e8767d7bddf2f1ca4a28af0a87056b7028825adce4` |
| Reports directory | [https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/openai/gpt-5.4-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/reports](https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/openai/gpt-5.4-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/reports) | Bilingual HTML / Markdown / PDF reports |
| Data directory | [https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/openai/gpt-5.4-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/data](https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/openai/gpt-5.4-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/data) | Pair data, request telemetry, summary, and excluded records |
| Manifest | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-5.4-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/metadata/manifest.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-5.4-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/metadata/manifest.json) | File sizes and SHA-256 checksums |

Dataset reference: `business_representative` built-in representative business templates; request-level export is `benchmark_requests.jsonl`.

Online HTML: Chinese [https://infronai.github.io/prompt-cache-bench/experiments/openai/gpt-5.4-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/reports/routing-cache-cost-streaming-performance-ab-study__gpt-5-4-mini__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-04.zh.html](https://infronai.github.io/prompt-cache-bench/experiments/openai/gpt-5.4-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/reports/routing-cache-cost-streaming-performance-ab-study__gpt-5-4-mini__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-04.zh.html); English [https://infronai.github.io/prompt-cache-bench/experiments/openai/gpt-5.4-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/reports/routing-cache-cost-streaming-performance-ab-study__gpt-5-4-mini__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-04.en.html](https://infronai.github.io/prompt-cache-bench/experiments/openai/gpt-5.4-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/reports/routing-cache-cost-streaming-performance-ab-study__gpt-5-4-mini__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-04.en.html).
