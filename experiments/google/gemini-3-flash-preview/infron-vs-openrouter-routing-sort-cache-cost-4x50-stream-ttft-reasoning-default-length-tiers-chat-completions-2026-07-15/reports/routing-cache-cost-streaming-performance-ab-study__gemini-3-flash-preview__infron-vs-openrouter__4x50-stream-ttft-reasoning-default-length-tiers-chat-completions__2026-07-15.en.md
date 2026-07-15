# Infron vs OpenRouter A/B Report: `google/gemini-3-flash-preview`

This report summarizes a controlled prompt-cache and routing A/B benchmark for `google/gemini-3-flash-preview`. The experiment kept the previous run parameters unchanged: Chat Completions streaming, four routing sort modes, 4 groups x 50 rounds, workers=24, platform-default reasoning, local SOCKS5 proxy, and 50-token `usage.prompt_tokens` pairing tolerance.

## Experiment Design

| Field | Value |
| --- | --- |
| Model | `google/gemini-3-flash-preview` |
| A/B pair | Infron vs OpenRouter |
| API protocol | `/v1/chat/completions` |
| Streaming | Enabled; TTFT captured |
| Sort modes | throughput / price / latency / ttft |
| Groups and rounds | 4 groups x 50 rounds |
| Effective paired samples | 792 |
| Excluded records | 16 |
| Input token tolerance | 50 tokens |

## Results

| Sort mode | Provider | Rounds | Cache hit | Observed cost | Avg latency | Avg TTFT | Output TPS |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Throughput First | infron | 192 | 0.00% | $0.323119 | 1,540.554 ms | 1,472.190 ms | 7.791 |
| Throughput First | openrouter | 192 | 0.00% | $0.312770 | 2,193.614 ms | 1,974.817 ms | 1.368 |
| Price First | infron | 200 | 0.00% | $0.336800 | 1,649.173 ms | 1,580.236 ms | 7.276 |
| Price First | openrouter | 200 | 0.00% | $0.325878 | 2,270.021 ms | 2,134.001 ms | 1.322 |
| Latency First | infron | 200 | 0.00% | $0.336800 | 1,648.057 ms | 1,579.911 ms | 7.281 |
| Latency First | openrouter | 200 | 0.00% | $0.325896 | 2,183.360 ms | 2,086.625 ms | 1.374 |
| TTFT First | infron | 200 | 0.00% | $0.252942 | 1,694.768 ms | 1,588.248 ms | 7.480 |
| TTFT First | openrouter | 200 | 0.00% | $0.325925 | 2,336.145 ms | 2,171.444 ms | 1.284 |

## Interpretation

Cache hit rate was 0 in this run, meaning this model/platform combination did not report observable cache-read tokens for the controlled cache probe. Infron showed lower TTFT and lower average end-to-end latency in all four modes. OpenRouter showed slightly lower observed cost in throughput/price/latency modes, while Infron was lower cost in ttft mode.

## Reproducibility

- Experiment directory: https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/google/gemini-3-flash-preview/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-15
- Reports directory: https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/google/gemini-3-flash-preview/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-15/reports
- Dataset directory: https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/google/gemini-3-flash-preview/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-15/data
- Figures directory: https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/google/gemini-3-flash-preview/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-15/figures
- Code snapshot: https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/google/gemini-3-flash-preview/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-15/code
- Manifest: https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/google/gemini-3-flash-preview/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-15/metadata/manifest.json
- Pair dataset: https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/google/gemini-3-flash-preview/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-15/data/benchmark_pairs.csv
- Request telemetry: https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/google/gemini-3-flash-preview/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-15/data/benchmark_requests.jsonl
- Summary: https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/google/gemini-3-flash-preview/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-15/data/summary.json
