# Routing, Cache, Cost, and Streaming Performance A/B Study

Model: `moonshotai/kimi-k2.6`

This report compares Infron and OpenRouter using the standard benchmark matrix: 4 experiment groups, 50 rounds per group, streaming enabled, Chat Completions protocol, and short/medium/long prompt length tiers.

## Data Quality

- Completed request slots: 1600
- Excluded records: 2 total; 0 incomplete, 0 anomalous usage, 2 unequal input-token pairs.
- The aggregate tables below are computed from the cleaned comparable records in `summary.json`.

## Aggregate Results

| Routing objective | Provider | Effective rounds | Cache hit rate | Total cost (USD) | Avg latency (ms) | P95 latency (ms) | Avg TTFT (ms) | P95 TTFT (ms) | Output TPS |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| throughput | infron | 199 | 0.949095 | 1.860533 | 5,479.215 | 11,184.024 | 4,279.986 | 8,473.936 | 10.103 |
| throughput | openrouter | 199 | 0.937591 | 1.399763 | 3,599.820 | 7,769.273 | 3,249.455 | 6,972.787 | 4.401 |
| price | infron | 200 | 0.968800 | 1.027136 | 5,760.196 | 16,688.310 | 5,137.981 | 15,290.953 | 2.538 |
| price | openrouter | 200 | 0.872746 | 1.399067 | 3,349.988 | 7,019.753 | 2,951.806 | 6,101.972 | 4.744 |
| latency | infron | 200 | 0.995763 | 1.011204 | 4,719.127 | 8,972.701 | 3,894.173 | 7,912.929 | 3.390 |
| latency | openrouter | 200 | 0.880515 | 1.548765 | 3,609.943 | 7,814.770 | 3,043.024 | 6,637.909 | 4.391 |
| ttft | infron | 200 | 0.998972 | 0.965508 | 4,425.148 | 8,039.589 | 3,576.759 | 7,098.014 | 3.616 |
| ttft | openrouter | 200 | 0.879672 | 1.614516 | 2,898.347 | 5,391.626 | 2,560.995 | 4,778.549 | 5.473 |

## Readout

- Infron shows materially higher cache-hit rates across all routing objectives in this run, especially in latency and TTFT-optimized groups.
- OpenRouter is faster on average latency and TTFT in this sample, while Infron is cheaper in the price, latency, and TTFT groups.
- Throughput mode is the main exception on cost: OpenRouter recorded lower total cost in this run, while Infron recorded higher output-token throughput.
- Only two records were excluded due to unequal input token counts, so this run is broadly suitable for comparison.

## Source Artifacts

- Run directory: `export/kimi_k26_all_experiments/routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260707`
- Raw records: `records.json`
- Request corpus: `benchmark_requests.jsonl`
- Summary: `summary.json`

## Reproducibility Links

- Summary: <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/moonshotai/kimi-k2.6/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/summary.json>
- Paired dataset CSV: <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/moonshotai/kimi-k2.6/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/benchmark_pairs.csv>
- Request-level dataset JSONL: <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/moonshotai/kimi-k2.6/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/benchmark_requests.jsonl>
- Filtered structured records: <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/moonshotai/kimi-k2.6/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/records.json>
- Excluded-record audit: <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/moonshotai/kimi-k2.6/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/records_excluded.json>
- Benchmark runner source: <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/moonshotai/kimi-k2.6/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/code/rerun_routing_sort_cache_cost_ab.py>
- HTML report renderer source: <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/moonshotai/kimi-k2.6/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/code/render_glm52_deepseek_style_report.py>
- Test source: <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/moonshotai/kimi-k2.6/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/code/test_rerun_routing_sort_cache_cost_ab.py>
- A/B report standard: <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/moonshotai/kimi-k2.6/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/code/ab-report-standard.md>
- Data directory: <https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/moonshotai/kimi-k2.6/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data>
- Code snapshot: <https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/moonshotai/kimi-k2.6/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/code>
