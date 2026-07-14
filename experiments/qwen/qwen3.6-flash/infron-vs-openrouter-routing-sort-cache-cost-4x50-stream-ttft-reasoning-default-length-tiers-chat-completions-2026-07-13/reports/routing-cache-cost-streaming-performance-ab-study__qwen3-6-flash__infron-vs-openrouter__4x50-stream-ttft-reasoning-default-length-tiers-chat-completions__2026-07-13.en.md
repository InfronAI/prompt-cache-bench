# Infron vs OpenRouter A/B Test Report: qwen/qwen3.6-flash

This is the short summary for the run. The full Chinese Markdown, standard Chinese/English HTML, PDFs, summary JSON, paired CSV, and request JSONL are in the same export directory.

- Model: `qwen/qwen3.6-flash`
- API: `/v1/chat/completions`
- Scale: 4 groups x 50 rounds x 4 routing sorts x 2 platforms x first/second replay
- Reasoning / Thinking: platform default behavior; payload did not set `reasoning.effort` explicitly
- Valid pairs: 800; request rows: 3200
- Excluded records: 0 (incomplete=0, anomalous_usage=0, unequal_input_tokens=0)
- Report date: 2026-07-13

## Routing Mode Summary

| Routing mode | Pairs | Cache winner | Cost winner | Throughput winner | E2E latency winner | TTFT winner |
| --- | ---: | --- | --- | --- | --- | --- |
| Throughput First | 200 | Tie (0.00%) | Infron ($0.665154 / $1.536957) | OpenRouter (73.810 tok/s / 84.768 tok/s) | OpenRouter (5564.89 ms / 5506.76 ms) | OpenRouter (2990.30 ms / 2734.06 ms) |
| Price First | 200 | Tie (0.00%) | Infron ($0.667731 / $1.633638) | OpenRouter (73.787 tok/s / 100.547 tok/s) | Infron (5742.80 ms / 6779.32 ms) | OpenRouter (3163.75 ms / 2931.36 ms) |
| Latency First | 200 | Tie (0.00%) | Infron ($0.668748 / $1.538766) | OpenRouter (72.183 tok/s / 81.984 tok/s) | OpenRouter (5941.66 ms / 5742.78 ms) | OpenRouter (3185.38 ms / 2871.39 ms) |
| TTFT First | 200 | Tie (0.00%) | Infron ($0.666943 / $1.537904) | OpenRouter (72.026 tok/s / 80.861 tok/s) | OpenRouter (5827.88 ms / 5798.80 ms) | OpenRouter (3133.68 ms / 2909.38 ms) |

## Cross-Mode Conclusions

- Cache hit rate: Infron 0/4, OpenRouter 0/4, Tie 4/4.
- Observed cost: Infron 4/4, OpenRouter 0/4, Tie 0/4.
- Throughput: Infron 0/4, OpenRouter 4/4, Tie 0/4.
- E2E latency: Infron 1/4, OpenRouter 3/4, Tie 0/4.
- TTFT: Infron 0/4, OpenRouter 4/4, Tie 0/4.

## Data and Report Artifacts

| Artifact | Path |
| --- | --- |
| Full Chinese Markdown | `routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260713-report-zh.md` |
| Chinese summary Markdown | `routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260713-summary-zh.md` |
| English summary Markdown | `routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260713-summary-en.md` |
| Standard Chinese HTML | `routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260713-standard-ab-report-zh.html` |
| Standard English HTML | `routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260713-standard-ab-report-en.html` |
| Summary JSON | `routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260713/summary.json` |
| Paired CSV | `routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260713/benchmark_pairs.csv` |
| Request JSONL | `routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260713/benchmark_requests.jsonl` |

## Reproducibility

- English HTML: https://infronai.github.io/prompt-cache-bench/experiments/qwen/qwen3.6-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-13/reports/routing-cache-cost-streaming-performance-ab-study__qwen3-6-flash__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-13.en.html
- Chinese HTML: https://infronai.github.io/prompt-cache-bench/experiments/qwen/qwen3.6-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-13/reports/routing-cache-cost-streaming-performance-ab-study__qwen3-6-flash__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-13.zh.html
- Summary JSON: https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.6-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-13/data/summary.json
- Paired dataset: https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.6-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-13/data/benchmark_pairs.csv
- Request-level dataset: https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.6-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-13/data/benchmark_requests.jsonl
- Filtered records: https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.6-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-13/data/records.json
- Excluded-record audit: https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/qwen/qwen3.6-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-13/data/records_excluded.json
- Code snapshot: https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/qwen/qwen3.6-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-13/code
