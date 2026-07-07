# Routing, Cache, Cost, and Streaming Performance A/B Study

Model: `minimax/minimax-m3`

This report compares Infron and OpenRouter using the standard benchmark matrix: 4 experiment groups, 50 rounds per group, streaming enabled, Chat Completions protocol, default reasoning behavior, and short/medium/long prompt length tiers.

## Data Quality

- Completed request-level records: 3196
- Comparable A/B pairs: 799
- Excluded records: 2 total; 1 incomplete, 0 anomalous usage, 1 unequal input-token pairs.
- Request JSONL SHA256: `333491a80a3af487f260ea9b9f6b7cd3f863e3b150f025ea62796a345bf8caa0`
- Pair CSV SHA256: `04e9799be91b7b05670e88c20259466bba36f0132affa8f618fe73864239406d`

## Aggregate Results

| Routing objective | Provider | Effective rounds | Cache hit rate | Total cost (USD) | Avg latency (ms) | Avg TTFT (ms) | Output TPS |
|---|---:|---:|---:|---:|---:|---:|---:|
| throughput | infron | 199 | 99.75% | $0.44453200 | 4,187.992 | 3,906.654 | 3.820 |
| throughput | openrouter | 199 | 97.78% | $0.42616452 | 3,520.482 | 3,320.929 | 4.480 |
| price | infron | 200 | 87.07% | $0.86923800 | 4,215.047 | 3,970.207 | 5.706 |
| price | openrouter | 200 | 99.71% | $0.38910666 | 3,183.654 | 2,988.125 | 5.026 |
| latency | infron | 200 | 99.56% | $0.38928600 | 3,610.426 | 3,345.935 | 4.432 |
| latency | openrouter | 200 | 97.80% | $0.50588802 | 3,322.030 | 3,069.540 | 4.816 |
| ttft | infron | 200 | 99.56% | $0.38928600 | 3,405.387 | 3,123.363 | 4.698 |
| ttft | openrouter | 200 | 99.71% | $0.49761108 | 3,616.816 | 3,377.282 | 4.424 |

## Readout

Overall, this run shows no single platform dominating every axis. Infron is strongest on cache reuse in three of four routing objectives and has lower cost in latency/TTFT modes. OpenRouter is faster in throughput, price, and latency modes, while Infron has the lower TTFT in the explicit TTFT objective. The price objective is the largest outlier for Infron cost because cache reuse was materially lower than OpenRouter in that group.

## Reproducibility Appendix

- Online English HTML: [https://infronai.github.io/prompt-cache-bench/experiments/minimax/minimax-m3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/reports/routing-cache-cost-streaming-performance-ab-study__minimax-m3__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-07.en.html](https://infronai.github.io/prompt-cache-bench/experiments/minimax/minimax-m3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/reports/routing-cache-cost-streaming-performance-ab-study__minimax-m3__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-07.en.html)
- Online Chinese HTML: [https://infronai.github.io/prompt-cache-bench/experiments/minimax/minimax-m3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/reports/routing-cache-cost-streaming-performance-ab-study__minimax-m3__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-07.zh.html](https://infronai.github.io/prompt-cache-bench/experiments/minimax/minimax-m3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/reports/routing-cache-cost-streaming-performance-ab-study__minimax-m3__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-07.zh.html)
- Experiment directory: [https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/minimax/minimax-m3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07](https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/minimax/minimax-m3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07)
- Reports directory: [https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/minimax/minimax-m3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/reports](https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/minimax/minimax-m3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/reports)
- Dataset directory: [https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/minimax/minimax-m3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data](https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/minimax/minimax-m3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data)
- Summary: [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/minimax/minimax-m3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/summary.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/minimax/minimax-m3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/summary.json)
- Pair CSV: [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/minimax/minimax-m3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/benchmark_pairs.csv](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/minimax/minimax-m3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/benchmark_pairs.csv)
- Request JSONL: [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/minimax/minimax-m3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/benchmark_requests.jsonl](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/minimax/minimax-m3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/benchmark_requests.jsonl)
- Records JSON: [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/minimax/minimax-m3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/records.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/minimax/minimax-m3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/records.json)
- Excluded records: [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/minimax/minimax-m3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/records_excluded.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/minimax/minimax-m3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/records_excluded.json)
- Runner source: [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/minimax/minimax-m3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/code/rerun_routing_sort_cache_cost_ab.py](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/minimax/minimax-m3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/code/rerun_routing_sort_cache_cost_ab.py)
- Renderer source: [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/minimax/minimax-m3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/code/render_report.py](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/minimax/minimax-m3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/code/render_report.py)
- Test source: [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/minimax/minimax-m3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/code/test_rerun_routing_sort_cache_cost_ab.py](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/minimax/minimax-m3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/code/test_rerun_routing_sort_cache_cost_ab.py)
- Manifest: [https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/minimax/minimax-m3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/metadata/manifest.json](https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/minimax/minimax-m3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/metadata/manifest.json)
