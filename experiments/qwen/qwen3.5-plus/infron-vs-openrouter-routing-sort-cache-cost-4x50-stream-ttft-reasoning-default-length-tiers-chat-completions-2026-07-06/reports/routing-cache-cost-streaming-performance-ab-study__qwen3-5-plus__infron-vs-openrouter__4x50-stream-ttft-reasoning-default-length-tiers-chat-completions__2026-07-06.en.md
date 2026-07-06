# Infron vs OpenRouter Routing, Cache, Cost, and Streaming Performance A/B Report

## Executive Summary

This report evaluates `qwen/qwen3.5-plus` across Infron and OpenRouter under prompt-caching workloads. The run uses only `/v1/chat/completions`, keeps model/platform default reasoning and thinking behavior, and keeps prompt-length stratification enabled.

After A/B filtering, the analysis retains **715 paired samples** and **2860 request-level observations**. It excludes **170 records**. Provider model IDs are Infron `qwen/qwen3.5-plus` and OpenRouter `qwen/qwen3.5-plus-20260420`.

Core finding: token-level cache hit rate ties in every routing mode. Infron leads observed cost and E2E latency in every routing mode. OpenRouter leads throughput and Streaming TTFT in every routing mode. Cache read/write telemetry is zero on both platforms in this run, so the report does not attribute a cache advantage to either side.

## Quality Gate

| Item | Value |
| --- | --- |
| Model | `qwen/qwen3.5-plus` |
| Provider model IDs | Infron `qwen/qwen3.5-plus`; OpenRouter `qwen/qwen3.5-plus-20260420` |
| API protocol | `/v1/chat/completions` only |
| Groups / rounds | 4 groups x 50 rounds |
| Prompt tiers | `short`≈1500, `medium`≈8000, `long`≈32000 tokens |
| Reasoning / thinking | Default platform/model behavior; no explicit parameter |
| Pairing rule | strict sort/group/round pair with first/second `usage.prompt_tokens` deltas <= 50 |
| Retained pairs | 715 |
| Request-level rows | 2860 |
| Excluded records | 170 |

## Route-Level Result Matrix

| Routing mode | Pairs | Token cache hit rate | Observed cost | Throughput | E2E latency | TTFT |
| --- | ---: | --- | --- | --- | --- | --- |
| Throughput First | 157 | **Tie 0.00% / 0.00%** | **Infron $0.598793** / OpenRouter $2.382274 | Infron 3.491 / **OpenRouter 50.324** tok/s | **Infron 3481.37 ms** / OpenRouter 27183.00 ms | Infron 3201.57 ms / **OpenRouter 2634.81 ms** |
| Price First | 163 | **Tie 0.00% / 0.00%** | **Infron $0.334323** / OpenRouter $2.546479 | Infron 2.875 / **OpenRouter 49.998** tok/s | **Infron 4243.01 ms** / OpenRouter 27587.21 ms | Infron 3926.75 ms / **OpenRouter 2840.22 ms** |
| Latency First | 200 | **Tie 0.00% / 0.00%** | **Infron $1.228794** / OpenRouter $3.092506 | Infron 3.165 / **OpenRouter 50.051** tok/s | **Infron 3879.73 ms** / OpenRouter 26905.27 ms | Infron 3577.67 ms / **OpenRouter 2730.12 ms** |
| TTFT First | 195 | **Tie 0.00% / 0.00%** | **Infron $1.210111** / OpenRouter $3.009037 | Infron 3.253 / **OpenRouter 50.101** tok/s | **Infron 3783.04 ms** / OpenRouter 27125.24 ms | Infron 3453.44 ms / **OpenRouter 2733.46 ms** |

## API Protocol Record

| API protocol | Endpoint | Platform | Planned pairs | Requests | Success rate | Usage coverage | Cost coverage | Cache telemetry coverage | HTTP status | Top errors |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `chat_completions` | `/v1/chat/completions` | Infron | 800 | 1600 | 97.44% | 100.00% | 100.00% | 100.00% | 0:41, 200:1559 | [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1000) (24); [Errno 54] Connection reset by peer (14) |
| `chat_completions` | `/v1/chat/completions` | OpenRouter | 800 | 1600 | 94.38% | 100.00% | 100.00% | 100.00% | 0:40, 200:1510, 429:50 | [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1000) (38); [Errno 54] Connection reset by peer (2) |

## Prompt-Length Stratified Results

| Tier | Pairs | Token cache hit rate | Observed cost | E2E latency | TTFT | Reasoning tokens |
| --- | ---: | --- | --- | --- | --- | --- |
| short | 238 | **Tie 0.00%** / 0.00% | **Infron $0.133744** / OpenRouter $1.309786 | **Infron 2604.15 ms** / OpenRouter 23440.01 ms | Infron 2321.52 ms / **OpenRouter 1968.25 ms** | **Infron 0** / OpenRouter 560458 |
| medium | 245 | **Tie 0.00%** / 0.00% | **Infron $0.672494** / OpenRouter $2.727598 | **Infron 3718.17 ms** / OpenRouter 27129.94 ms | Infron 3397.07 ms / **OpenRouter 2516.97 ms** | **Infron 0** / OpenRouter 662088 |
| long | 232 | **Tie 0.00%** / 0.00% | **Infron $2.565783** / OpenRouter $6.992912 | **Infron 5263.31 ms** / OpenRouter 31074.85 ms | Infron 4943.35 ms / **OpenRouter 3752.45 ms** | **Infron 0** / OpenRouter 697265 |

## Reasoning / Thinking Observation

This run does not explicitly disable or force reasoning/thinking. Reasoning tokens are treated as observed telemetry.

| Routing mode | Infron reasoning tokens | OpenRouter reasoning tokens | Infron avg/request | OpenRouter avg/request |
| --- | ---: | ---: | ---: | ---: |
| Throughput First | **0** | 423458 | **0.0000** | 1348.5924 |
| Price First | **0** | 443252 | **0.0000** | 1359.6687 |
| Latency First | **0** | 530769 | **0.0000** | 1326.9225 |
| TTFT First | **0** | 522332 | **0.0000** | 1339.3128 |

## Reproducibility References

| Artifact | Link | SHA256 / Notes |
| --- | --- | --- |
| Chinese HTML report | <https://infronai.github.io/prompt-cache-bench/experiments/qwen/qwen3.5-plus/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/reports/routing-cache-cost-streaming-performance-ab-study__qwen3-5-plus__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-06.zh.html> |  |
| English HTML report | <https://infronai.github.io/prompt-cache-bench/experiments/qwen/qwen3.5-plus/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/reports/routing-cache-cost-streaming-performance-ab-study__qwen3-5-plus__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-06.en.html> |  |
| Summary | <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.5-plus/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/summary.json> | `4f74247f769ca6ca3b71d26963e90b7daf1d571bcae1bba0144da487a78e0f22` |
| Paired dataset CSV | <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.5-plus/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/benchmark_pairs.csv> | `aea743349fc3592d9a0f4a3fee4b03fea667eac00a09e2d1921d7797331d19d4` |
| Request-level dataset JSONL | <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.5-plus/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/benchmark_requests.jsonl> | `cc6dcf3628aced3eb697c349cfbf18070c293b9333fc86204e344694b7874eeb` |
| Excluded-record audit | <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.5-plus/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/records_excluded.json> | `995eb8dba3f1b33db3384304899ec076aa51f1c592a48ae22b839314e58267f5` |
| Data directory | <https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/qwen/qwen3.5-plus/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data> |  |
| Benchmark runner source | <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.5-plus/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/code/rerun_routing_sort_cache_cost_ab.py> | `b8ff71395fb08a6ff817c03d153ac09914b2bddb6994265a86a5ecaba9471824` |
| HTML report renderer source | <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.5-plus/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/code/render_glm52_deepseek_style_report.py> | `d82c729d73b4a19087506bc2381fd1dcf1ccf0270160a064a6a4ed5490855153` |
| Test source | <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.5-plus/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/code/test_rerun_routing_sort_cache_cost_ab.py> | `30b46e2b21db1b0e42899db12983d8e5bdfbaa8ceb9c64b04e5e664aa3914558` |
| A/B report standard | <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.5-plus/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/code/ab-report-standard.md> | `4c8633866de695fafeec1f70477340877b89b9253f24eb6c06b367656eae785c` |

Dataset reference: `business_representative` built-in representative business templates; exported request-level dataset is `benchmark_requests.jsonl`.
