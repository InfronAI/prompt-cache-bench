# Infron vs OpenRouter Routing, Cache, Cost, and Streaming A/B Report



## Summary

This report evaluates `xiaomi/mimo-v2.5` on Infron and OpenRouter across cache reuse, observed cost, throughput, E2E latency, and streaming TTFT under Prompt Caching workloads.

Key findings: cache hit rate is led by Infron in 1/4 modes and OpenRouter in 3/4 modes; observed cost is led by Infron in 1/4 modes and OpenRouter in 3/4 modes; throughput is led by Infron in 3/4 modes and OpenRouter in 1/4 modes; E2E latency is led by Infron in 3/4 modes and OpenRouter in 1/4 modes; streaming TTFT is led by Infron in 3/4 modes and OpenRouter in 1/4 modes.

After strict A/B filtering, the dataset retains 800 paired samples and 3200 request-level observations, with 0 records excluded.



## Experiment Setup

| Item | Configuration |
| --- | --- |
| Model | `xiaomi/mimo-v2.5` |
| Provider model IDs | infron: `xiaomi/mimo-v2.5`; openrouter: `xiaomi/mimo-v2.5` |
| API protocol | `/v1/chat/completions` |
| Routing modes | Throughput First, Price First, Latency First, TTFT First |
| Groups / rounds per group | 4 / 50 |
| Workers | 24 |
| Request mode | Streaming Chat Completions with TTFT collection |
| Reasoning / Thinking control | No explicit reasoning/thinking parameter; model and platform defaults are preserved |
| Prompt length tiers | `short`≈1500, `medium`≈8000, `long`≈32000 |
| Input-token pair tolerance | 50 tokens |
| Excluded records | 0 |



## Overall Metrics

| Routing mode | Platform | Paired rounds | Total input tokens | Token cache hit rate | Observed cost | Throughput | E2E latency | Streaming TTFT |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Throughput First | Infron | 200 | 7075538 | 90.89% | $0.53792900 | **3.90 tok/s** | **6103.12 ms** | **5073.92 ms** |
| Throughput First | OpenRouter | 200 | 7075538 | **98.61%** | **$0.40888852** | 2.26 tok/s | 7073.03 ms | 6629.10 ms |
| Price First | Infron | 200 | 7076338 | **99.88%** | **$0.03393900** | 1.53 tok/s | 8371.81 ms | 7772.99 ms |
| Price First | OpenRouter | 200 | 7075538 | 99.14% | $0.40176022 | **2.57 tok/s** | **6221.51 ms** | **5804.38 ms** |
| Latency First | Infron | 200 | 7075538 | 99.73% | $0.61243900 | **4.74 tok/s** | **3373.85 ms** | **2904.79 ms** |
| Latency First | OpenRouter | 200 | 7075538 | **99.77%** | **$0.37016124** | 4.47 tok/s | 3577.79 ms | 3218.88 ms |
| TTFT First | Infron | 200 | 7075538 | 99.73% | $0.58492400 | **4.82 tok/s** | **3322.36 ms** | **2814.00 ms** |
| TTFT First | OpenRouter | 200 | 7075538 | **99.76%** | **$0.45699362** | 4.55 tok/s | 3515.33 ms | 3115.36 ms |



## Prompt Length Stratification

| Prompt length tier | Target tokens | Platform | Rounds | Token cache hit rate | Observed cost | Avg E2E latency | Avg TTFT |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `short` | 1500 | Infron | 268 | 94.92% | $0.08121300 | 4095.19 ms | 3458.13 ms |
| `short` | 1500 | OpenRouter | 268 | **97.77%** | **$0.06277326** | **3846.68 ms** | **3412.17 ms** |
| `medium` | 8000 | Infron | 268 | 96.26% | **$0.34829300** | 5183.66 ms | 4536.25 ms |
| `medium` | 8000 | OpenRouter | 268 | **98.76%** | $0.47585390 | **4706.89 ms** | **4295.43 ms** |
| `long` | 32000 | Infron | 264 | 98.02% | $1.33972500 | **6619.30 ms** | **5949.43 ms** |
| `long` | 32000 | OpenRouter | 264 | **99.54%** | **$1.09917644** | 6762.02 ms | 6393.59 ms |



## Reproducibility Appendix

| Artifact | Path |
| --- | --- |
| Summary | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/xiaomi/mimo-v2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/summary.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/xiaomi/mimo-v2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/summary.json) |
| Paired dataset | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/xiaomi/mimo-v2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/benchmark_pairs.csv](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/xiaomi/mimo-v2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/benchmark_pairs.csv) |
| Request-level dataset | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/xiaomi/mimo-v2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/benchmark_requests.jsonl](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/xiaomi/mimo-v2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/benchmark_requests.jsonl) |
| Filtered structured records | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/xiaomi/mimo-v2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/records.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/xiaomi/mimo-v2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/records.json) |
| Excluded-record audit | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/xiaomi/mimo-v2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/records_excluded.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/xiaomi/mimo-v2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/records_excluded.json) |
| Test source | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/xiaomi/mimo-v2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/code/test_rerun_routing_sort_cache_cost_ab.py](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/xiaomi/mimo-v2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/code/test_rerun_routing_sort_cache_cost_ab.py) |
| Benchmark runner source | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/xiaomi/mimo-v2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/code/rerun_routing_sort_cache_cost_ab.py](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/xiaomi/mimo-v2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/code/rerun_routing_sort_cache_cost_ab.py) |
| HTML report renderer source | [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/xiaomi/mimo-v2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/code/render_glm52_deepseek_style_report.py](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/xiaomi/mimo-v2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/code/render_glm52_deepseek_style_report.py) |
| Dataset reference | Built-in `business_representative` templates; request-level export in [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/xiaomi/mimo-v2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/benchmark_requests.jsonl](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/xiaomi/mimo-v2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/benchmark_requests.jsonl) |
