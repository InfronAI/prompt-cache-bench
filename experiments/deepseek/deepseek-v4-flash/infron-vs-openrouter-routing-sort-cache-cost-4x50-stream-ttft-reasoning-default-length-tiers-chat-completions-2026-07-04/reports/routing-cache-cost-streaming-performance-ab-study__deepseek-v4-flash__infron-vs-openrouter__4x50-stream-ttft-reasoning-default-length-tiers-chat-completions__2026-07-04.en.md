# Infron vs OpenRouter Routing, Cache, Cost, and Streaming Performance A/B Report

## Executive Summary

This report evaluates `deepseek/deepseek-v4-flash` across Infron and OpenRouter in prompt-caching workloads. The experiment uses only `/v1/chat/completions`, keeps model/platform default reasoning and thinking behavior, and keeps prompt-length stratification enabled.

After A/B filtering, the analysis retains **699 paired samples** and **2796 request-level observations**. It excludes **202 records**.

Core finding: Infron leads token-level cache reuse and E2E latency in every routing mode. OpenRouter leads throughput in every routing mode. TTFT winners vary by routing mode; see the result matrix.

## Quality Gate

| Item | Value |
| --- | --- |
| Model | `deepseek/deepseek-v4-flash` |
| API protocol | `/v1/chat/completions` only |
| Groups / rounds | 4 groups x 50 rounds |
| Prompt tiers | `short`≈1500, `medium`≈8000, `long`≈32000 tokens |
| Reasoning / thinking | Default platform/model behavior; no explicit disable parameter |
| Pairing rule | strict sort/group/round pair with first/second usage.prompt_tokens deltas <= 50 |
| Retained pairs | 699 |
| Request-level rows | 2796 |
| Excluded records | 202 |

## Route-Level Result Matrix

| Routing mode | Pairs | Token cache hit rate | Observed cost | Throughput | E2E latency | TTFT |
| --- | ---: | --- | --- | --- | --- | --- |
| Throughput First | 197 | **Infron 96.98%** / OpenRouter 94.98% | Infron $0.213942 / **OpenRouter $0.159170** | Infron 3.286 / **OpenRouter 5.487** tok/s | Infron 3722.44 ms / **OpenRouter 2915.93 ms** | Infron 3433.18 ms / **OpenRouter 2584.72 ms** |
| Price First | 120 | **Infron 99.14%** / OpenRouter 53.07% | **Infron $0.061492** / OpenRouter $0.259405 | Infron 2.839 / **OpenRouter 31.698** tok/s | **Infron 4102.95 ms** / OpenRouter 7446.27 ms | **Infron 3797.36 ms** / OpenRouter 4704.57 ms |
| Latency First | 183 | **Infron 99.45%** / OpenRouter 58.12% | **Infron $0.190216** / OpenRouter $0.346087 | Infron 5.407 / **OpenRouter 31.747** tok/s | **Infron 2291.26 ms** / OpenRouter 6849.25 ms | **Infron 2107.77 ms** / OpenRouter 4375.07 ms |
| TTFT First | 199 | **Infron 99.44%** / OpenRouter 56.25% | **Infron $0.188229** / OpenRouter $0.384197 | Infron 5.659 / **OpenRouter 27.038** tok/s | **Infron 2179.19 ms** / OpenRouter 5916.65 ms | **Infron 1994.39 ms** / OpenRouter 3804.41 ms |

## API Protocol Record

| API protocol | Endpoint | Platform | Planned pairs | Requests | Success rate | Usage coverage | Token usage coverage | Cost coverage | Cache telemetry coverage | HTTP status | Top errors |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `chat_completions` | `/v1/chat/completions` | infron | 800 | 1600 | **98.06%** | 100.00% | 100.00% | 100.00% | 100.00% | 0:31, 200:1569 | [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1000) (26); [Errno 54] Connection reset by peer (3) |
| `chat_completions` | `/v1/chat/completions` | openrouter | 800 | 1600 | 90.62% | 99.93% | 99.93% | 99.93% | 100.00% | 0:150, 200:1450 | [Errno 61] Connection refused (93); [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1000) (51) |

## Prompt-Length Stratified Cache Performance

| Tier | Pairs | Token cache hit rate | Call cache hit rate | E2E latency | TTFT | Reasoning tokens |
| --- | ---: | --- | --- | --- | --- | --- |
| short | 235 | **Infron 94.28%** / OpenRouter 27.56% | **Infron 99.57%** / OpenRouter 36.60% | **Infron 2009.88 ms** / OpenRouter 3997.19 ms | **Infron 1797.20 ms** / OpenRouter 2226.81 ms | **Infron 0** / OpenRouter 57031 |
| medium | 234 | **Infron 99.24%** / OpenRouter 66.88% | **Infron 100.00%** / OpenRouter 71.79% | **Infron 2821.46 ms** / OpenRouter 5504.25 ms | **Infron 2605.96 ms** / OpenRouter 3534.99 ms | **Infron 0** / OpenRouter 67622 |
| long | 230 | **Infron 98.80%** / OpenRouter 68.93% | **Infron 99.13%** / OpenRouter 75.22% | **Infron 4113.44 ms** / OpenRouter 7267.33 ms | **Infron 3836.90 ms** / OpenRouter 5569.41 ms | **Infron 0** / OpenRouter 71043 |

## Reasoning / Thinking Observation

This run does not explicitly disable or force reasoning/thinking. Reasoning tokens are treated as observed telemetry.

| Routing mode | Infron reasoning tokens | OpenRouter reasoning tokens | Infron avg/request | OpenRouter avg/request |
| --- | ---: | ---: | ---: | ---: |
| Throughput First | **0** | 6304 | **0.0000** | 16.0000 |
| Price First | **0** | 53713 | **0.0000** | 223.8042 |
| Latency First | **0** | 75379 | **0.0000** | 205.9536 |
| TTFT First | **0** | 60300 | **0.0000** | 151.5075 |

## Reproducibility References

| Artifact | Path | SHA256 / Notes |
| --- | --- | --- |
| Summary | `experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/data/summary.json` | `8da7075fa6740d6e6e4b19a82518fcee2ece5084d37fad3b141926101c45d10b` |
| Paired dataset CSV | `experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/data/benchmark_pairs.csv` | `d7543a3e2b66f54010e09ae42469b9581413674cacf487ceb6161641f223a5cb` |
| Request-level dataset JSONL | `experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/data/benchmark_requests.jsonl` | `a7b621d771279e9e1bc98c076ff572235e263c03d8479ebbf007cf919ddcc878` |
| Excluded-record audit | `experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/data/records_excluded.json` | `ce364bae7fa1550beaade3a5a7a75dc1b689ae4fbe0f026c5d515ce19c62803e` |
| Benchmark runner source | `experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/code/rerun_routing_sort_cache_cost_ab.py` | `a485c5116e99375e6b171d0328e5a423babd1ee6b206c72f54053a3a045b1075` |
| HTML report renderer source | `experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/code/render_glm52_deepseek_style_report.py` | `8d6047a98107177daf86e9525a78df4735d72bfda7a55e2ba661620cc7cbee33` |
| Test source | `experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/code/test_rerun_routing_sort_cache_cost_ab.py` | `c086ddc5d0a9a91eba82b7e8767d7bddf2f1ca4a28af0a87056b7028825adce4` |
| A/B report standard | `experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/code/ab-report-standard.md` | `897151e98e2fc4cd9d7acf2642e54f800f1b22712a70275d35526348460d8372` |



Public GitHub paths:
- Summary: <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/data/summary.json>
- Paired dataset CSV: <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/data/benchmark_pairs.csv>
- Request-level dataset JSONL: <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/data/benchmark_requests.jsonl>
- Excluded-record audit: <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/data/records_excluded.json>
- Benchmark runner source: <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/code/rerun_routing_sort_cache_cost_ab.py>
- HTML report renderer source: <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/code/render_glm52_deepseek_style_report.py>
- Test source: <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/code/test_rerun_routing_sort_cache_cost_ab.py>
- A/B report standard: <https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/code/ab-report-standard.md>
- Data directory: <https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/data>
- Code snapshot: <https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-04/code>

Dataset reference: `business_representative` built-in representative business templates; exported request-level dataset is `benchmark_requests.jsonl` in the run directory.
