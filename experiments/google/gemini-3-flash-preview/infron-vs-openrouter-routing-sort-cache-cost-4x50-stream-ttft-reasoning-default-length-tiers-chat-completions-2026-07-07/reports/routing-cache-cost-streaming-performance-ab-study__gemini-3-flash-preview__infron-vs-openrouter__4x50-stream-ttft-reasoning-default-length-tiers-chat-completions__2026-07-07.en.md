# Infron vs OpenRouter A/B Report: `google/gemini-3-flash-preview`

This public report summarizes a controlled prompt-cache and routing A/B benchmark for `google/gemini-3-flash-preview`. The experiment used matched payloads, streaming Chat Completions, four routing sort modes, prompt-length tiers, and platform-default reasoning/thinking behavior.

## Experiment Design

| Field | Value |
| --- | --- |
| Model | `google/gemini-3-flash-preview` |
| A/B pair | Infron vs OpenRouter |
| API protocol | `/v1/chat/completions` |
| Streaming | Enabled; TTFT captured |
| Sort modes | throughput / price / latency / ttft |
| Prompt tiers | short / medium / long |
| Groups and rounds | 4 groups x 50 rounds |
| Effective paired samples | 799 |
| Excluded samples | 2 |

## Results

| Sort mode | Provider | Rounds | Cache hit | Observed cost | Avg latency | Avg TTFT | Output TPS |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| throughput | infron | 200 | 84.53% | $1.013121 | 2,799.219 ms | 2,707.805 ms | 4.144 |
| throughput | openrouter | 200 | 86.92% | $0.927036 | 2,677.880 ms | 2,636.088 ms | 1.120 |
| price | infron | 200 | 63.73% | $1.234643 | 3,052.436 ms | 2,981.137 ms | 3.710 |
| price | openrouter | 200 | 87.32% | $0.821037 | 2,697.257 ms | 2,658.124 ms | 1.112 |
| latency | infron | 200 | 77.67% | $0.977398 | 3,828.602 ms | 3,747.774 ms | 3.021 |
| latency | openrouter | 200 | 86.62% | $0.829087 | 2,763.240 ms | 2,733.498 ms | 1.086 |
| ttft | infron | 199 | 87.88% | $0.784887 | 2,819.771 ms | 2,730.206 ms | 4.102 |
| ttft | openrouter | 199 | 74.31% | $1.434997 | 2,776.408 ms | 2,737.425 ms | 1.081 |

## Interpretation

OpenRouter showed lower observed cost and lower mean end-to-end latency in most routing modes. Infron showed materially higher output throughput across all modes, and in TTFT-first mode Infron had higher cache hit rate with nearly tied TTFT.

## Reproducibility

- Experiment directory: <https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/google/gemini-3-flash-preview/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07>
- Reports directory: <https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/google/gemini-3-flash-preview/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/reports>
- Dataset directory: <https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/google/gemini-3-flash-preview/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data>
- Figures directory: <https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/google/gemini-3-flash-preview/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/figures>
- Code snapshot: <https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/google/gemini-3-flash-preview/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/code>
- Manifest: <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/google/gemini-3-flash-preview/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/metadata/manifest.json>
- Pair dataset: <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/google/gemini-3-flash-preview/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/benchmark_pairs.csv>
- Request telemetry: <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/google/gemini-3-flash-preview/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/benchmark_requests.jsonl>
- Summary: <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/google/gemini-3-flash-preview/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-07/data/summary.json>
