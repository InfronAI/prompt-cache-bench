# Infron vs OpenRouter A/B Report: moonshotai/kimi-k2.5
## Summary
This report compares Infron and OpenRouter for `moonshotai/kimi-k2.5` using the same experiment parameters as the previous standard A/B runs: Chat Completions, streaming enabled, 4 groups x 50 rounds, routing modes `throughput`, `price`, `latency`, and `ttft`, with prompt length tiers `short:1500`, `medium:8000`, and `long:32000`.
The run completed 1600 request attempts. After filtering incomplete records and A/B input-token mismatches, the effective paired dataset retained 75 paired samples / 300 request-level observations. This makes the result useful for directional comparison, but the high exclusion count should be treated as a data-quality limitation for this model/run.
## Data Quality
- Included paired samples: 75
- Request-level observations in included pairs: 300
- Excluded records: total=1450, incomplete=1155, unequal_input_tokens=295, anomalous_usage=0
## Key Metrics
| Routing mode | Platform | Included rounds | Cache hit rate | Total actual cost | Avg latency | P95 latency | Avg TTFT | P95 TTFT | Throughput |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| throughput | infron | 2 | 15.263% | $0.01313 | 3529.005 ms | 4584.956 ms | 3362.166 ms | 4476.370 ms | 1.133 tok/s |
| throughput | openrouter | 2 | 98.642% | $0.00215256 | 3264.427 ms | 5481.420 ms | 2259.224 ms | 3348.969 ms | 3.982 tok/s |
| price | infron | 0 | 0.000% | $0 | 0.000 ms | N/A | 0.000 ms | N/A | 0.000 tok/s |
| price | openrouter | 0 | 0.000% | $0 | 0.000 ms | N/A | 0.000 ms | N/A | 0.000 tok/s |
| latency | infron | 0 | 0.000% | $0 | 0.000 ms | N/A | 0.000 ms | N/A | 0.000 tok/s |
| latency | openrouter | 0 | 0.000% | $0 | 0.000 ms | N/A | 0.000 ms | N/A | 0.000 tok/s |
| ttft | infron | 73 | 98.835% | $0.142192 | 6604.166 ms | 15517.549 ms | 6317.804 ms | 15382.806 ms | 0.892 tok/s |
| ttft | openrouter | 73 | 99.600% | $0.246045 | 3219.541 ms | 8827.668 ms | 2687.385 ms | 8105.855 ms | 4.725 tok/s |

## Conclusion
Within the retained comparable samples, OpenRouter shows lower average TTFT and lower average end-to-end latency for `moonshotai/kimi-k2.5`, while Infron is cheaper in the `ttft` routing mode. The `price` and `latency` modes retained no comparable paired samples after filtering, so they should not be interpreted as zero-performance modes; they are data-quality exclusions in this run.
## Reproducibility

- Experiment directory: <https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/moonshotai/kimi-k2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07>
- Reports directory: <https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/moonshotai/kimi-k2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/reports>
- Dataset directory: <https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/moonshotai/kimi-k2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data>
- Figures directory: <https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/moonshotai/kimi-k2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/figures>
- Code snapshot: <https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/moonshotai/kimi-k2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/code>
- Manifest: <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/moonshotai/kimi-k2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/metadata/manifest.json>
- Pair dataset: <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/moonshotai/kimi-k2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/benchmark_pairs.csv>
- Request telemetry: <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/moonshotai/kimi-k2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/benchmark_requests.jsonl>
- Summary: <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/moonshotai/kimi-k2.5/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/summary.json>
