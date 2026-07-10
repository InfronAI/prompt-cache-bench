# moonshotai/kimi-k2.7-code Routing, Cache, Cost, and Streaming Performance A/B Benchmark

Model: `moonshotai/kimi-k2.7-code`

This report compares Infron and OpenRouter using the standard prompt-cache-bench A/B methodology: 4 experiment groups, 50 rounds per group, streaming Chat Completions, short/medium/long prompt length tiers, and platform-default reasoning behavior.

## Data Quality

- Completed round slots: 1600
- Request-level observations: 3200
- Paired samples: 800
- Excluded records: 0 total; 0 incomplete, 0 anomalous usage, 0 unequal input-token pairs.
- The aggregate tables below are computed from cleaned comparable records in `summary.json`.

## Aggregate Results

| Routing objective | Provider | Effective rounds | Cache hit rate | Total cost (USD) | Avg latency (ms) | P95 latency (ms) | Avg TTFT (ms) | P95 TTFT (ms) | Output TPS |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| throughput | infron | 200 | 0.954646 | 0.980326 | 5,605.977 | 11,593.691 | 4,769.417 | 10,308.844 | 5.369 |
| throughput | openrouter | 200 | 0.976019 | 2.016535 | 2,759.595 | 4,844.239 | 2,593.428 | 4,541.029 | 5.153 |
| price | infron | 200 | 0.982922 | 0.944881 | 6,081.993 | 14,662.979 | 5,360.048 | 13,225.201 | 4.286 |
| price | openrouter | 200 | 0.929548 | 1.809493 | 10,768.469 | 37,562.774 | 9,952.846 | 29,846.345 | 1.368 |
| latency | infron | 200 | 0.916395 | 1.409992 | 8,638.226 | 16,980.644 | 7,891.779 | 15,814.239 | 2.407 |
| latency | openrouter | 200 | 0.974580 | 1.625742 | 7,154.683 | 15,814.692 | 6,888.809 | 14,972.450 | 2.001 |
| ttft | infron | 200 | 0.998297 | 0.941845 | 7,862.916 | 14,168.666 | 7,231.294 | 13,384.801 | 2.866 |
| ttft | openrouter | 200 | 0.997828 | 1.567765 | 6,955.335 | 14,086.271 | 6,741.560 | 13,847.978 | 2.084 |

## Readout

- Infron recorded lower observed cost across all routing objectives in this run.
- Cache-hit leadership varied by routing objective; see `summary.json` and the HTML report for tier-level analysis and charts.
- Latency and TTFT leadership should be interpreted by routing objective because provider selection differs by `provider.sort`.
- No records were excluded after the standard data-quality and input-token pairing filters, so the run is suitable for direct paired comparison.

## Reproducibility Links

- Summary: <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/moonshotai/kimi-k2.7-code/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-10/data/summary.json>
- Paired dataset CSV: <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/moonshotai/kimi-k2.7-code/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-10/data/benchmark_pairs.csv>
- Request-level dataset JSONL: <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/moonshotai/kimi-k2.7-code/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-10/data/benchmark_requests.jsonl>
- Filtered structured records: <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/moonshotai/kimi-k2.7-code/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-10/data/records.json>
- Excluded-record audit: <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/moonshotai/kimi-k2.7-code/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-10/data/records_excluded.json>
- Benchmark runner source: <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/moonshotai/kimi-k2.7-code/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-10/code/rerun_routing_sort_cache_cost_ab.py>
- HTML report renderer source: <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/moonshotai/kimi-k2.7-code/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-10/code/render_glm52_deepseek_style_report.py>
- Test source: <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/moonshotai/kimi-k2.7-code/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-10/code/test_rerun_routing_sort_cache_cost_ab.py>
- A/B report standard: <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/moonshotai/kimi-k2.7-code/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-10/code/ab-report-standard.md>
- Data directory: <https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/moonshotai/kimi-k2.7-code/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-10/data>
- Code snapshot: <https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/moonshotai/kimi-k2.7-code/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-10/code>
- English HTML report: <https://infronai.github.io/prompt-cache-bench/experiments/moonshotai/kimi-k2.7-code/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-10/reports/routing-cache-cost-streaming-performance-ab-study__kimi-k2-7-code__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-10.en.html>
- Chinese HTML report: <https://infronai.github.io/prompt-cache-bench/experiments/moonshotai/kimi-k2.7-code/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-10/reports/routing-cache-cost-streaming-performance-ab-study__kimi-k2-7-code__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-10.zh.html>
