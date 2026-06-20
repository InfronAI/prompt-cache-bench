# Methodology

The benchmark uses strict A/B pairing:

1. The same model, request payload, routing sort, group, and round are sent to Infron and OpenRouter.
2. Each provider receives two identical requests per round.
3. The first request warms or refreshes prompt cache behavior.
4. The second request observes cache-read tokens.
5. A pair enters the final comparison only when Infron and OpenRouter return identical `usage.prompt_tokens` for both first and second requests.

The comparison uses response-returned `usage.prompt_tokens` as the source of truth, because platform-side prompt wrapping, tokenizer differences, and cache accounting can diverge from local token estimates.

Core metrics:

- Token cache hit rate: second request cache-read tokens divided by second request prompt tokens.
- Actual cost: response-returned cost fields only; missing cost is not treated as zero.
- Throughput: response completion tokens divided by response latency seconds.
- Latency: full request-response elapsed time.
- TTFT: first streaming chunk/token arrival time.

