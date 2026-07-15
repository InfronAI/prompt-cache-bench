# Infron vs OpenRouter A/B 报告：`google/gemini-3-flash-preview`

本报告总结 `google/gemini-3-flash-preview` 的受控 prompt-cache 与 routing A/B benchmark。实验保持上一轮参数不变：Chat Completions streaming、四种 routing sort、4 组 x 50 轮、workers=24、平台默认 reasoning、本地 SOCKS5 代理、`usage.prompt_tokens` 50-token 容差过滤。

## 实验设计

| 字段 | 值 |
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

## 结果

| 路由模式 | 平台 | Rounds | Cache hit | Observed cost | Avg latency | Avg TTFT | Output TPS |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 吞吐优先 | infron | 192 | 0.00% | $0.323119 | 1,540.554 ms | 1,472.190 ms | 7.791 |
| 吞吐优先 | openrouter | 192 | 0.00% | $0.312770 | 2,193.614 ms | 1,974.817 ms | 1.368 |
| 价格优先 | infron | 200 | 0.00% | $0.336800 | 1,649.173 ms | 1,580.236 ms | 7.276 |
| 价格优先 | openrouter | 200 | 0.00% | $0.325878 | 2,270.021 ms | 2,134.001 ms | 1.322 |
| 端到端时延优先 | infron | 200 | 0.00% | $0.336800 | 1,648.057 ms | 1,579.911 ms | 7.281 |
| 端到端时延优先 | openrouter | 200 | 0.00% | $0.325896 | 2,183.360 ms | 2,086.625 ms | 1.374 |
| 流式 TTFT 优先 | infron | 200 | 0.00% | $0.252942 | 1,694.768 ms | 1,588.248 ms | 7.480 |
| 流式 TTFT 优先 | openrouter | 200 | 0.00% | $0.325925 | 2,336.145 ms | 2,171.444 ms | 1.284 |

## 解读

本轮样本中，缓存命中率为 0，说明该模型/平台组合在当前 controlled cache probe 下没有返回可观测 cache-read tokens。Infron 在四种模式下 TTFT 和端到端平均时延均低于 OpenRouter；OpenRouter 的 observed cost 在 throughput/price/latency 模式略低，ttft 模式中 Infron 成本更低。

## 可复现性

- Experiment directory: https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/google/gemini-3-flash-preview/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-15
- Reports directory: https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/google/gemini-3-flash-preview/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-15/reports
- Dataset directory: https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/google/gemini-3-flash-preview/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-15/data
- Figures directory: https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/google/gemini-3-flash-preview/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-15/figures
- Code snapshot: https://github.com/InfronAI/prompt-cache-bench/tree/main/experiments/google/gemini-3-flash-preview/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-15/code
- Manifest: https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/google/gemini-3-flash-preview/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-15/metadata/manifest.json
- Pair dataset: https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/google/gemini-3-flash-preview/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-15/data/benchmark_pairs.csv
- Request telemetry: https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/google/gemini-3-flash-preview/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-15/data/benchmark_requests.jsonl
- Summary: https://github.com/InfronAI/prompt-cache-bench/blob/main/experiments/google/gemini-3-flash-preview/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-15/data/summary.json
