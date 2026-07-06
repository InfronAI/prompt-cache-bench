# Infron vs OpenRouter Routing, Cache, Cost, and Streaming Performance A/B Report

## Executive Summary

This report evaluates `openai/gpt-4o-mini` across Infron and OpenRouter under prompt-caching workloads. The run uses only `/v1/chat/completions`, keeps model/platform default reasoning and thinking behavior, and keeps prompt-length stratification enabled.

After A/B filtering, the analysis retains **783 paired samples** and **3132 request-level observations**. It excludes **34 records**. Provider model IDs are Infron `openai/gpt-4o-mini` and OpenRouter `openai/gpt-4o-mini`.

Core finding: OpenRouter leads token-level cache hit rate and observed cost in every routing mode. Throughput, E2E latency, and Streaming TTFT split 2/4 vs 2/4 across routing modes, so neither side shows a clear cross-mode lead on those performance axes.

## Quality Gate

| Item | Value |
| --- | --- |
| Model | `openai/gpt-4o-mini` |
| Provider model IDs | Infron `openai/gpt-4o-mini`; OpenRouter `openai/gpt-4o-mini` |
| API protocol | `/v1/chat/completions` only |
| Groups / rounds | 4 groups x 50 rounds |
| Prompt tiers | `short`≈1500, `medium`≈8000, `long`≈32000 tokens |
| Reasoning / thinking | Default platform/model behavior; no explicit parameter |
| Pairing rule | strict sort/group/round pair with first/second `usage.prompt_tokens` deltas <= 50 |
| Retained pairs | 783 |
| Request-level rows | 3132 |
| Excluded records | 34 |

## Route-Level Result Matrix

| Routing mode | Pairs | Token cache hit rate | Observed cost | Throughput | E2E latency | TTFT |
| --- | ---: | --- | --- | --- | --- | --- |
| Throughput First | 0 | **Tie 0.00% / 0.00%** | **Tie $0.00000000 / $0.00000000** | **Tie 0.00 tok/s / 0.00 tok/s** | **Tie 0.00 ms / 0.00 ms** | **Tie 0.00 ms / 0.00 ms** |
| Price First | 0 | **Tie 0.00% / 0.00%** | **Tie $0.00000000 / $0.00000000** | **Tie 0.00 tok/s / 0.00 tok/s** | **Tie 0.00 ms / 0.00 ms** | **Tie 0.00 ms / 0.00 ms** |
| Latency First | 0 | **Tie 0.00% / 0.00%** | **Tie $0.00000000 / $0.00000000** | **Tie 0.00 tok/s / 0.00 tok/s** | **Tie 0.00 ms / 0.00 ms** | **Tie 0.00 ms / 0.00 ms** |
| TTFT First | 0 | **Tie 0.00% / 0.00%** | **Tie $0.00000000 / $0.00000000** | **Tie 0.00 tok/s / 0.00 tok/s** | **Tie 0.00 ms / 0.00 ms** | **Tie 0.00 ms / 0.00 ms** |

## API Protocol Record

| API protocol | Endpoint | Platform | Planned pairs | Requests | Success rate | Usage coverage | Cost coverage | Cache telemetry coverage | HTTP status | Top errors |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `chat_completions` | `/v1/chat/completions` | Infron | 0 | 0 | 0.00% | 0.00% | 0.00% | 0.00% |  | None |
| `chat_completions` | `/v1/chat/completions` | OpenRouter | 0 | 0 | 0.00% | 0.00% | 0.00% | 0.00% |  | None |

## Prompt-Length Stratified Results

| Tier | Pairs | Token cache hit rate | Observed cost | E2E latency | TTFT |
| --- | ---: | --- | --- | --- | --- |
| short | 0 | Infron 91.85% / **OpenRouter 92.21%** | Infron $0.11666700 / **OpenRouter $0.08010330** | Infron 2083.56 ms / **OpenRouter 2081.97 ms** | **Infron 1744.61 ms** / OpenRouter 1844.16 ms |
| medium | 0 | Infron 97.52% / **OpenRouter 99.03%** | Infron $0.59036700 / **OpenRouter $0.37255890** | **Infron 2737.27 ms** / OpenRouter 2803.95 ms | **Infron 2389.97 ms** / OpenRouter 2544.34 ms |
| long | 0 | Infron 98.14% / **OpenRouter 98.91%** | Infron $2.29457600 / **OpenRouter $1.44044130** | Infron 3526.13 ms / **OpenRouter 3412.58 ms** | **Infron 3111.83 ms** / OpenRouter 3123.59 ms |

## Reasoning / Thinking Observation

This run does not explicitly disable or force reasoning/thinking. Reasoning tokens are treated as observed telemetry under model and platform defaults.

## Reproducibility References

| Artifact | Link | SHA256 / Notes |
| --- | --- | --- |
| Chinese HTML report | <https://infronai.github.io/prompt-cache-bench/experiments/openai/gpt-4o-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/reports/routing-cache-cost-streaming-performance-ab-study__gpt-4o-mini__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-06.zh.html> |  |
| English HTML report | <https://infronai.github.io/prompt-cache-bench/experiments/openai/gpt-4o-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/reports/routing-cache-cost-streaming-performance-ab-study__gpt-4o-mini__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-06.en.html> |  |
| Summary | <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-4o-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/summary.json> | `906b4557b6b175f514bd7a663bc404f68f4c6e86c8078df6861bc907e9530672` |
| Paired dataset CSV | <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-4o-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/benchmark_pairs.csv> | `a04ef6ecb5882f82aa039b2dabc41c4d2e6a0f36bedf88c542b5c06bb38121d4` |
| Request-level dataset JSONL | <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-4o-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/benchmark_requests.jsonl> | `853de5f12f65c3217531b5caedb8d1b94238521baec04908e318bf1676a89485` |
| Excluded-record audit | <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-4o-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/records_excluded.json> | `7c67d0f35c7a36a58703d6190af49ad14ba32379a6dc872a9739d3330aaf8d55` |
| Data directory | <https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/openai/gpt-4o-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data> |  |
| Benchmark runner source | <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-4o-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/code/rerun_routing_sort_cache_cost_ab.py> | `b8ff71395fb08a6ff817c03d153ac09914b2bddb6994265a86a5ecaba9471824` |
| HTML report renderer source | <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-4o-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/code/render_glm52_deepseek_style_report.py> | `411289b9087ee50275a2d08da86cb7342a9c81933764c05fe08acd684f818e0a` |
| Test source | <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-4o-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/code/test_rerun_routing_sort_cache_cost_ab.py> | `30b46e2b21db1b0e42899db12983d8e5bdfbaa8ceb9c64b04e5e664aa3914558` |
| A/B report standard | <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-4o-mini/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/code/ab-report-standard.md> | `81c99b29dceaf28a80ba9a12d648e138f7aa21b37b35c109f7ae30145e1e4263` |

Dataset reference: `business_representative` built-in representative business templates; exported request-level dataset is `benchmark_requests.jsonl`.

