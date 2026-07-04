# Infron vs OpenRouter Routing, Cache, Cost, and Streaming Performance A/B Report

## Executive Summary

This report evaluates `deepseek/deepseek-v4-pro` across Infron and OpenRouter in prompt-caching workloads. The experiment uses only `/v1/chat/completions`, keeps model/platform default reasoning and thinking behavior, and keeps prompt-length stratification enabled.

After A/B filtering, the analysis retains **791 paired samples** and **3164 request-level observations**. It excludes **18 records**.

Core finding: Infron leads observed cost in every routing mode and leads E2E latency overall. OpenRouter leads throughput and Streaming TTFT in every routing mode. Cache-rate winners are close and vary by routing mode.

## Quality Gate

| Item | Value |
| --- | --- |
| Model | `deepseek/deepseek-v4-pro` |
| API protocol | `/v1/chat/completions` only |
| Groups / rounds | 4 groups x 50 rounds |
| Prompt tiers | `short` about 1500, `medium` about 8000, `long` about 32000 tokens |
| Reasoning / thinking | Default platform/model behavior; no explicit disable parameter |
| Pairing rule | strict sort/group/round pair with first/second usage.prompt_tokens deltas <= 50 |
| Retained pairs | 791 |
| Request-level rows | 3164 |
| Excluded records | 18 |

## Route-Level Result Matrix

| Routing mode | Pairs | Token cache hit rate | Observed cost | Throughput | E2E latency | TTFT |
| --- | ---: | --- | --- | --- | --- | --- |
| Throughput First | 200 | Infron 90.52% / **OpenRouter 95.98%** | **Infron $1.205367** / OpenRouter $2.110727 | Infron 2.805 tok/s / **OpenRouter 39.962 tok/s** | **Infron 4557.65 ms** / OpenRouter 10533.90 ms | Infron 4139.22 ms / **OpenRouter 3138.79 ms** |
| Price First | 198 | **Infron 99.44%** / OpenRouter 98.26% | **Infron $0.337858** / OpenRouter $1.693868 | Infron 3.197 tok/s / **OpenRouter 38.359 tok/s** | **Infron 4023.15 ms** / OpenRouter 10514.30 ms | Infron 3350.61 ms / **OpenRouter 3210.02 ms** |
| Latency First | 196 | Infron 91.27% / **OpenRouter 92.33%** | **Infron $1.109211** / OpenRouter $1.780845 | Infron 2.949 tok/s / **OpenRouter 39.703 tok/s** | **Infron 4305.92 ms** / OpenRouter 10042.08 ms | Infron 3863.79 ms / **OpenRouter 3191.40 ms** |
| TTFT First | 197 | Infron 98.59% / **OpenRouter 99.45%** | **Infron $0.589968** / OpenRouter $1.442047 | Infron 2.790 tok/s / **OpenRouter 36.153 tok/s** | **Infron 4588.39 ms** / OpenRouter 10079.76 ms | Infron 4099.19 ms / **OpenRouter 3196.65 ms** |

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

| Routing mode | Infron reasoning tokens | OpenRouter reasoning tokens | Infron avg/request | OpenRouter avg/request |
| --- | ---: | ---: | ---: | ---: |
| Throughput First | **0** | 162216 | **0.0000** | 405.5400 |
| Price First | **0** | 153691 | **0.0000** | 388.1086 |
| Latency First | **0** | 150585 | **0.0000** | 384.1454 |
| TTFT First | **0** | 138211 | **0.0000** | 350.7893 |

## Reproducibility References

| Artifact | GitHub path | SHA256 / Notes |
| --- | --- | --- |
| Summary | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-pro/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/data/summary.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-pro/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/data/summary.json) | `0984289dd19dcfd12644cbe0d4e2473b57ee98cf65ced71209d32710e8102e13` |
| Paired dataset CSV | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-pro/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/data/benchmark_pairs.csv](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-pro/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/data/benchmark_pairs.csv) | `858cdad534209908d7dbce59a92205040a3a008e639bf860d527b4358b1ba24b` |
| Request-level dataset JSONL | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-pro/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/data/benchmark_requests.jsonl](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-pro/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/data/benchmark_requests.jsonl) | `c1958ba57cc831fad6677f10937e6ce984137f351f2e7b1f1f05e345584b1f41` |
| Excluded-record audit | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-pro/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/data/records_excluded.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-pro/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/data/records_excluded.json) | `104a6a0249e8026ea16e841ebdff3e855e6a526297db4a5ef6441f39994c4771` |
| Benchmark runner source | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-pro/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/code/rerun_routing_sort_cache_cost_ab.py](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-pro/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/code/rerun_routing_sort_cache_cost_ab.py) | `a485c5116e99375e6b171d0328e5a423babd1ee6b206c72f54053a3a045b1075` |
| HTML report renderer source | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-pro/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/code/render_glm52_deepseek_style_report.py](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-pro/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/code/render_glm52_deepseek_style_report.py) | `e5bb0d32361d70ee688e0d0a0da3302a1e542e33e53876c905814eb5c27b0532` |
| Test source | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-pro/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/code/test_rerun_routing_sort_cache_cost_ab.py](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-pro/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/code/test_rerun_routing_sort_cache_cost_ab.py) | `c086ddc5d0a9a91eba82b7e8767d7bddf2f1ca4a28af0a87056b7028825adce4` |
| Reports directory | [https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/deepseek/deepseek-v4-pro/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/reports](https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/deepseek/deepseek-v4-pro/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/reports) | Bilingual HTML / Markdown / PDF reports |
| Data directory | [https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/deepseek/deepseek-v4-pro/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/data](https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/deepseek/deepseek-v4-pro/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/data) | Pair data, request telemetry, summary, and excluded records |
| Manifest | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-pro/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/metadata/manifest.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-pro/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/metadata/manifest.json) | File sizes and SHA-256 checksums |

Dataset reference: `business_representative` built-in representative business templates; request-level export is `benchmark_requests.jsonl`.

Online HTML: Chinese [https://infronai.github.io/prompt-cache-bench/experiments/deepseek/deepseek-v4-pro/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/reports/routing-cache-cost-streaming-performance-ab-study__deepseek-v4-pro__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-04.zh.html](https://infronai.github.io/prompt-cache-bench/experiments/deepseek/deepseek-v4-pro/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/reports/routing-cache-cost-streaming-performance-ab-study__deepseek-v4-pro__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-04.zh.html); English [https://infronai.github.io/prompt-cache-bench/experiments/deepseek/deepseek-v4-pro/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/reports/routing-cache-cost-streaming-performance-ab-study__deepseek-v4-pro__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-04.en.html](https://infronai.github.io/prompt-cache-bench/experiments/deepseek/deepseek-v4-pro/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/reports/routing-cache-cost-streaming-performance-ab-study__deepseek-v4-pro__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-04.en.html).
