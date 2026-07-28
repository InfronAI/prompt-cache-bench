# Infron vs OpenRouter A/B Test Report: moonshotai/kimi-k3

This report is the short summary for the experiment; the complete standard Chinese/English HTML, PDFs, summary JSON, paired CSV, and request-level JSONL are saved in the same export directory.

- Model: `moonshotai/kimi-k3`
- API: `/v1/chat/completions`
- Experiment size: 4 groups x 50 rounds x 4 routing sorts x 2 platforms x first/second replay
- Reasoning / Thinking: platform defaults; payload does not explicitly set `reasoning.effort`
- Effective pairs: 800; request-level records: 3200
- Excluded records: 0
- Report date: 2026-07-28

## Routing Mode Summary

| Routing mode | Pairs | Cache winner | Cost winner | Throughput winner | E2E latency winner | TTFT winner |
| --- | ---: | --- | --- | --- | --- | --- |
| Throughput First | 200 | Infron (90.73% / 81.07%) | Infron ($3.687283 / $8.711514) | OpenRouter (1.174 tok/s / 1.645 tok/s) | OpenRouter (13624.80 ms / 9724.88 ms) | OpenRouter (12485.09 ms / 9377.65 ms) |
| Price First | 200 | Infron (96.95% / 92.42%) | Infron ($2.003152 / $4.956052) | Infron (3.212 tok/s / 2.492 tok/s) | Infron (4981.17 ms / 6420.97 ms) | Infron (3664.40 ms / 5861.22 ms) |
| Latency First | 200 | Infron (96.95% / 90.61%) | Infron ($2.003152 / $5.158083) | Infron (3.381 tok/s / 2.682 tok/s) | Infron (4731.76 ms / 5965.07 ms) | Infron (3447.95 ms / 5448.98 ms) |
| TTFT First | 200 | Infron (96.95% / 94.34%) | Infron ($2.003152 / $4.384893) | OpenRouter (2.746 tok/s / 2.946 tok/s) | OpenRouter (5825.79 ms / 5431.57 ms) | Infron (4439.04 ms / 5107.21 ms) |

## Data And Report Artifacts

| Artifact | Path |
| --- | --- |
| Chinese summary Markdown | `routing-cache-cost-streaming-performance-ab-study__kimi-k3__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-28.zh.md` |
| English summary Markdown | `routing-cache-cost-streaming-performance-ab-study__kimi-k3__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-28.en.md` |
| Standard Chinese HTML | `routing-cache-cost-streaming-performance-ab-study__kimi-k3__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-28.zh.html` |
| Standard English HTML | `routing-cache-cost-streaming-performance-ab-study__kimi-k3__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-28.en.html` |
| Summary JSON | `data/summary.json` |
| Paired CSV | `data/benchmark_pairs.csv` |
| Request JSONL | `data/benchmark_requests.jsonl` |

## Reproducibility

- English HTML: https://infronai.github.io/prompt-cache-bench/experiments/moonshotai/kimi-k3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-28/reports/routing-cache-cost-streaming-performance-ab-study__kimi-k3__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-28.en.html
- Chinese HTML: https://infronai.github.io/prompt-cache-bench/experiments/moonshotai/kimi-k3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-28/reports/routing-cache-cost-streaming-performance-ab-study__kimi-k3__infron-vs-openrouter__4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-28.zh.html
- Summary JSON: https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/moonshotai/kimi-k3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-28/data/summary.json
- Paired dataset: https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/moonshotai/kimi-k3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-28/data/benchmark_pairs.csv
- Request-level dataset: https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/moonshotai/kimi-k3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-28/data/benchmark_requests.jsonl
- Filtered records: https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/moonshotai/kimi-k3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-28/data/records.json
- Excluded-record audit: https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/moonshotai/kimi-k3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-28/data/records_excluded.json
- Code snapshot: https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/moonshotai/kimi-k3/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-28/code
