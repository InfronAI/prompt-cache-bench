# Routing, Cache, Cost, and Streaming Performance A/B Study

Model: `moonshotai/kimi-k2.7-code`

This report compares Infron and OpenRouter using the standard benchmark matrix: 4 experiment groups, 50 rounds per group, streaming enabled, Chat Completions protocol, and short/medium/long prompt length tiers.

## Data Quality

- Completed request slots: 1600
- Request-level observations: 3200
- Paired samples: 800
- Excluded records: 0 total; 0 incomplete, 0 anomalous usage, 0 unequal input-token pairs.
- The aggregate tables below are computed from the cleaned comparable records in `summary.json`.

## Aggregate Results

| Routing objective | Provider | Effective rounds | Cache hit rate | Total cost (USD) | Avg latency (ms) | P95 latency (ms) | Avg TTFT (ms) | P95 TTFT (ms) | Output TPS |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| throughput | infron | 200 | 0.916270 | 1.190816 | 4,905.388 | 9,776.655 | 3,967.997 | 8,616.902 | 6.401 |
| throughput | openrouter | 200 | 0.978077 | 1.215148 | 3,002.508 | 5,158.986 | 2,623.435 | 4,460.518 | 4.714 |
| price | infron | 200 | 0.998282 | 1.018341 | 9,519.195 | 45,655.315 | 7,739.131 | 43,087.143 | 1.981 |
| price | openrouter | 200 | 0.982897 | 1.190685 | 3,388.530 | 6,482.456 | 2,931.515 | 5,565.656 | 4.398 |
| latency | infron | 200 | 0.999340 | 0.997955 | 5,646.342 | 8,440.445 | 3,509.058 | 6,159.659 | 2.834 |
| latency | openrouter | 200 | 0.985120 | 1.126289 | 3,221.597 | 5,259.715 | 2,742.343 | 4,679.844 | 4.677 |
| ttft | infron | 200 | 0.998747 | 1.078529 | 6,499.951 | 23,478.278 | 3,668.659 | 7,981.205 | 2.462 |
| ttft | openrouter | 200 | 0.995159 | 1.114939 | 3,212.642 | 5,520.038 | 2,676.150 | 4,557.333 | 4.746 |

## Readout

- Infron records lower observed cost across all routing objectives in this run.
- Infron records higher token-level cache hit rate in price, latency, and TTFT routing modes, while OpenRouter records higher token-level cache hit rate in throughput mode.
- OpenRouter records lower average E2E latency and lower streaming TTFT across all routing objectives in this sample.
- No records were excluded after the standard token-tolerance A/B pairing filter, so the run is suitable for direct paired comparison.

## Reproducibility Links

- Summary: <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/moonshotai/kimi-k2.7-code/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-09/data/summary.json>
- Paired dataset CSV: <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/moonshotai/kimi-k2.7-code/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-09/data/benchmark_pairs.csv>
- Request-level dataset JSONL: <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/moonshotai/kimi-k2.7-code/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-09/data/benchmark_requests.jsonl>
- Filtered structured records: <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/moonshotai/kimi-k2.7-code/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-09/data/records.json>
- Excluded-record audit: <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/moonshotai/kimi-k2.7-code/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-09/data/records_excluded.json>
- Benchmark runner source: <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/moonshotai/kimi-k2.7-code/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-09/code/rerun_routing_sort_cache_cost_ab.py>
- HTML report renderer source: <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/moonshotai/kimi-k2.7-code/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-09/code/render_glm52_deepseek_style_report.py>
- Test source: <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/moonshotai/kimi-k2.7-code/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-09/code/test_rerun_routing_sort_cache_cost_ab.py>
- A/B report standard: <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/moonshotai/kimi-k2.7-code/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-09/code/ab-report-standard.md>
- Data directory: <https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/moonshotai/kimi-k2.7-code/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-09/data>
- Code snapshot: <https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/moonshotai/kimi-k2.7-code/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-09/code>
- English HTML report: <https://infronai.github.io/prompt-cache-bench/experiments/moonshotai/kimi-k2.7-code/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-09/reports/routing-cache-cost-streaming-performance-ab-study__kimi-k2-7-code__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-09.en.html>
- Chinese HTML report: <https://infronai.github.io/prompt-cache-bench/experiments/moonshotai/kimi-k2.7-code/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-09/reports/routing-cache-cost-streaming-performance-ab-study__kimi-k2-7-code__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-09.zh.html>
