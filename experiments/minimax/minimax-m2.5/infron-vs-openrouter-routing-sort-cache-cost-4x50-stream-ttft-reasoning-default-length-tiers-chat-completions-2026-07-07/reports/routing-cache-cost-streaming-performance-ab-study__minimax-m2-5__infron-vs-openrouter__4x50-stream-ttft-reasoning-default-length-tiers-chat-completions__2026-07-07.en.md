# Infron vs OpenRouter Routing, Cache, Cost, and Streaming Performance A/B Test Report

## Abstract

This report evaluates `minimax/minimax-m2.5` under the standard Infron vs OpenRouter Prompt Caching A/B benchmark. OpenRouter leads most cache, cost, throughput, E2E latency, and TTFT outcomes in Throughput First, Price First, and Latency First modes, while Infron leads all five core metrics in TTFT First. The practical interpretation is that OpenRouter was stronger for the general routing modes in this run, while Infron produced the best result when the route objective explicitly prioritized TTFT.

The strict A/B filter retained 767 paired samples and 3068 request-level observations; 66 records were excluded. All core metrics come from response telemetry.

## Conclusion Matrix

| Routing mode | Cache hit rate | Observed cost | Throughput | E2E latency | TTFT |
| --- | --- | --- | --- | --- | --- |
| Throughput First | **OpenRouter** | **OpenRouter** | **Infron** | **OpenRouter** | **OpenRouter** |
| Price First | **OpenRouter** | **OpenRouter** | **Infron** | **OpenRouter** | **OpenRouter** |
| Latency First | **Infron** | **OpenRouter** | **Infron** | **OpenRouter** | **OpenRouter** |
| TTFT First | **Infron** | **Infron** | **Infron** | **Infron** | **Infron** |

## Overall Metrics

| Routing mode | Platform | Pairs | Token cache hit rate | Actual cost | Avg throughput | Avg E2E latency | Avg TTFT |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Throughput First | Infron | 176 | 95.28% | $0.24704000 | 3.21 tok/s | 4988.85 ms | 4123.13 ms |
| Throughput First | OpenRouter | 176 | **98.51%** | **$0.19202371** | **4.18 tok/s** | **3827.34 ms** | **3203.80 ms** |
| Price First | Infron | 191 | 96.45% | $0.27260500 | 2.85 tok/s | 8848.37 ms | 7428.26 ms |
| Price First | OpenRouter | 191 | **97.48%** | **$0.19811206** | **5.18 tok/s** | **3091.26 ms** | **2541.08 ms** |
| Latency First | Infron | 200 | **99.89%** | $0.20062900 | 4.71 tok/s | 3399.66 ms | 2853.13 ms |
| Latency First | OpenRouter | 200 | 99.88% | **$0.19451608** | **4.96 tok/s** | **3224.87 ms** | **2652.39 ms** |
| TTFT First | Infron | 200 | **99.95%** | **$0.19270000** | **5.01 tok/s** | **3192.90 ms** | **2714.81 ms** |
| TTFT First | OpenRouter | 200 | 99.53% | $0.21689979 | 4.76 tok/s | 3358.71 ms | 2836.95 ms |

## Reproducibility

The run used the standard 4 groups x 50 rounds design, streaming Chat Completions, platform-default reasoning/thinking behavior, prompt-length tiers `short:1500,medium:8000,long:32000`, and `/v1/chat/completions` only. A/B inclusion allowed up to 50 prompt-token difference within each paired first/second request.

| Artifact | Path |
| --- | --- |
| Summary JSON | <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/minimax/minimax-m2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/summary.json> |
| Paired dataset CSV | <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/minimax/minimax-m2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/benchmark_pairs.csv> |
| Request-level JSONL | <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/minimax/minimax-m2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/benchmark_requests.jsonl> |
| Filtered records | <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/minimax/minimax-m2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/records.json> |
| Excluded-record audit | <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/minimax/minimax-m2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/records_excluded.json> |
| Benchmark runner source | <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/minimax/minimax-m2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/code/rerun_routing_sort_cache_cost_ab.py> |
| Test source | <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/minimax/minimax-m2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/code/test_rerun_routing_sort_cache_cost_ab.py> |
| Dataset reference | Built-in `business_representative`; request-level export in `benchmark_requests.jsonl` |
| Chinese HTML report | <https://infronai.github.io/prompt-cache-bench/experiments/minimax/minimax-m2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/reports/routing-cache-cost-streaming-performance-ab-study__minimax-m2-5__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-07.zh.html> |
| English HTML report | <https://infronai.github.io/prompt-cache-bench/experiments/minimax/minimax-m2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/reports/routing-cache-cost-streaming-performance-ab-study__minimax-m2-5__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-07.en.html> |
