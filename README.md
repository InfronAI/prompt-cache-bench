# prompt-cache-bench

Open benchmark artifacts for LLM prompt caching and provider-routing A/B testing.

This repository publishes reproducible experiment code, raw benchmark datasets, figures, and report pages for evaluating inference platforms across:

- prompt cache hit rate
- actual cost
- throughput
- latency
- TTFT
- provider routing behavior

## Repository Layout

```text
.
├── scripts/                         # Reusable benchmark and report tooling
├── docs/                            # Methodology and reproducibility notes
└── experiments/
    └── deepseek/
        └── deepseek-v4-flash/
            └── infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-2026-06-19/
                ├── reports/         # HTML/Markdown report artifacts
                ├── data/            # Raw and derived benchmark datasets
                ├── figures/         # SVG figures used by reports
                ├── code/            # Exact code snapshot for this experiment
                └── metadata/        # Manifest and checksums
```

## Published Experiment

| Model | A/B Pair | Report | Data |
| --- | --- | --- | --- |
| `deepseek/deepseek-v4-flash` | Infron vs OpenRouter, routing sort `throughput/price/latency`, 4x50 streaming run | [HTML report](experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-2026-06-19/reports/prompt-cache-routing-ab-study__deepseek-v4-flash__infron-vs-openrouter__4x50-stream__2026-06-19.zh.html) | [data directory](experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-2026-06-19/data/) |

## Reproduce

Install Python 3.11+, set API credentials in environment variables, then run:

```bash
PYTHONPATH=. python3 scripts/rerun_routing_sort_cache_cost_ab.py \
  --groups 4 \
  --rounds 50 \
  --timeout 120 \
  --workers 8 \
  --stream \
  --dataset-name business_representative \
  --soak-duration-seconds 0 \
  --out-dir export/routing_sort_cache_cost_ab_4x50_stream_academic_1781889000 \
  --report export/routing_sort_cache_cost_ab_4x50_stream_academic_1781889000-report-zh.md
```

The checked-in dataset is already sufficient to audit the published report without re-running API calls.

## Security

No API keys or bearer tokens are committed. Raw request/response telemetry is retained only for benchmark observability fields such as usage, cost, provider metadata, TTFT, latency, and cache tokens.

