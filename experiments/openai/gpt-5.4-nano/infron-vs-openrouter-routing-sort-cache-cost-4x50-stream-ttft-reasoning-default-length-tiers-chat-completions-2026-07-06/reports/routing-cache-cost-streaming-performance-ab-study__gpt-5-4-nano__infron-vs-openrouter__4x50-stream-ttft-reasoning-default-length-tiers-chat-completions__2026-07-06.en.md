# Infron vs OpenRouter Routing, Cache, Cost, and Streaming Performance A/B Report

## Abstract

This report evaluates `openai/gpt-5.4-nano` on Infron and OpenRouter under prompt-caching workloads. Infron wins observed cost and throughput in all four routing modes. OpenRouter wins E2E latency and streaming TTFT in all four routing modes. OpenRouter wins token-level cache hit rate in three of four routing modes, while Infron wins cache hit rate in the latency-first mode.

The benchmark retained 790 paired samples and 3160 request-level observations after paired filtering; 20 records were excluded. The run uses default reasoning/thinking behavior, prompt-length tiers, streaming Chat Completions, and `/v1/chat/completions` only.

## Winner Matrix

| Routing mode | Cache hit rate | Observed cost | Throughput | E2E latency | TTFT |
| --- | --- | --- | --- | --- | --- |
| Throughput First | **OpenRouter** | **Infron** | **Infron** | **OpenRouter** | **OpenRouter** |
| Price First | **OpenRouter** | **Infron** | **Infron** | **OpenRouter** | **OpenRouter** |
| Latency First | **Infron** | **Infron** | **Infron** | **OpenRouter** | **OpenRouter** |
| TTFT First | **OpenRouter** | **Infron** | **Infron** | **OpenRouter** | **OpenRouter** |

## Reproducibility Appendix

| Artifact | Online link |
| --- | --- |
| Chinese HTML report | [GitHub Pages](https://infronai.github.io/prompt-cache-bench/experiments/openai/gpt-5.4-nano/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/reports/routing-cache-cost-streaming-performance-ab-study__gpt-5-4-nano__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-06.zh.html) |
| English HTML report | [GitHub Pages](https://infronai.github.io/prompt-cache-bench/experiments/openai/gpt-5.4-nano/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/reports/routing-cache-cost-streaming-performance-ab-study__gpt-5-4-nano__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-06.en.html) |
| Summary | [summary.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-5.4-nano/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/summary.json) |
| Paired dataset | [benchmark_pairs.csv](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-5.4-nano/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/benchmark_pairs.csv) |
| Request-level dataset | [benchmark_requests.jsonl](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-5.4-nano/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/benchmark_requests.jsonl) |
| Filtered records | [records.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-5.4-nano/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/records.json) |
| Excluded-record audit | [records_excluded.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-5.4-nano/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/records_excluded.json) |
| Test source | [test_rerun_routing_sort_cache_cost_ab.py](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-5.4-nano/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/code/test_rerun_routing_sort_cache_cost_ab.py) |
| Benchmark runner source | [rerun_routing_sort_cache_cost_ab.py](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-5.4-nano/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/code/rerun_routing_sort_cache_cost_ab.py) |
| HTML report renderer source | [render_glm52_deepseek_style_report.py](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-5.4-nano/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/code/render_glm52_deepseek_style_report.py) |
| Dataset reference | `business_representative`; request-level export is [benchmark_requests.jsonl](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/openai/gpt-5.4-nano/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-06/data/benchmark_requests.jsonl) |
