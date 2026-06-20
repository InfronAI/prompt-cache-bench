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
| `deepseek/deepseek-v4-flash` | Infron vs OpenRouter, routing sort `throughput/price/latency`, 4x50 streaming run | [GitHub Pages HTML](https://infronai.github.io/prompt-cache-bench/experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-2026-06-19/reports/prompt-cache-routing-ab-study__deepseek-v4-flash__infron-vs-openrouter__4x50-stream__2026-06-19.zh.html) / [GitHub Markdown preview](experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-2026-06-19/reports/prompt-cache-routing-ab-study__deepseek-v4-flash__infron-vs-openrouter__4x50-stream__2026-06-19.zh.md) | [data directory](experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-2026-06-19/data/) |

## Online Preview

GitHub Pages is the recommended way to read the self-contained HTML report online:

- Project page: <https://infronai.github.io/prompt-cache-bench/>
- Full HTML report: <https://infronai.github.io/prompt-cache-bench/experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-2026-06-19/reports/prompt-cache-routing-ab-study__deepseek-v4-flash__infron-vs-openrouter__4x50-stream__2026-06-19.zh.html>

The Markdown report remains available for GitHub-native review and source diffs.

## Install

Clone the repository and use Python 3.11+.

```bash
git clone https://github.com/InfronAI/prompt-cache-bench.git
cd prompt-cache-bench
python3 --version
```

The benchmark runner only uses the Python standard library. No package install is required for running the checked-in experiment script.

Optional: create a virtual environment if you prefer an isolated shell.

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## Configure API Keys

The repository includes `.env.example` with empty API key placeholders. Before running live benchmark requests, copy it to `.env` and fill in your own keys.

```bash
cp .env.example .env
```

Edit `.env`:

```bash
INFRON_BASE_URL=https://api.infron.ai/v1
INFRON_API_KEY=your_infron_api_key_here

OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_HTTP_REFERER=https://github.com/InfronAI/prompt-cache-bench
OPENROUTER_APP_TITLE=prompt-cache-bench
```

Do not commit `.env`. It is ignored by Git.

## Quick Start: Inspect Existing Results

You do not need API keys to inspect the published experiment. The raw dataset, charts, and report are already checked in.

Open the GitHub-rendered Markdown report online:

[prompt-cache-routing-ab-study__deepseek-v4-flash__infron-vs-openrouter__4x50-stream__2026-06-19.zh.md](experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-2026-06-19/reports/prompt-cache-routing-ab-study__deepseek-v4-flash__infron-vs-openrouter__4x50-stream__2026-06-19.zh.md)

GitHub does not render repository `.html` files as normal web pages in the file viewer. Use the Markdown report for online preview.

To open the self-contained HTML report locally:

```bash
open experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-2026-06-19/reports/prompt-cache-routing-ab-study__deepseek-v4-flash__infron-vs-openrouter__4x50-stream__2026-06-19.zh.html
```

Or inspect the data directly:

```bash
ls experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-2026-06-19/data
```

## Quick Start: Run a Small Smoke Benchmark

After configuring `.env`, run a small 1x2 streaming smoke benchmark first. This validates credentials and request formatting without spending much.

```bash
PYTHONPATH=. python3 scripts/rerun_routing_sort_cache_cost_ab.py \
  --groups 1 \
  --rounds 2 \
  --timeout 120 \
  --workers 1 \
  --stream \
  --dataset-name business_representative \
  --out-dir export/smoke_1x2 \
  --report export/smoke_1x2-report.md
```

The script writes:

- `records.json`
- `records_excluded.json`
- `benchmark_pairs.csv`
- `benchmark_requests.jsonl`
- `summary.json`
- report Markdown and SVG charts

## Reproduce the Published 4x50 Experiment

This command re-runs the full published design. It makes live API calls to both providers.

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

## Regenerate HTML Report

The report exporter can turn Markdown reports into standalone HTML with embedded SVG figures.

```bash
python3 scripts/export_routing_report_pdf.py \
  experiments/deepseek/deepseek-v4-flash/infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-2026-06-19/reports/prompt-cache-routing-ab-study__deepseek-v4-flash__infron-vs-openrouter__4x50-stream__2026-06-19.zh.md \
  /tmp/prompt-cache-report.pdf \
  --embed-assets \
  --html-only
```

Use `--html-only` when you only need a browser-readable report. PDF generation is optional and can be slow for very large appendices.

## Security

No API keys or bearer tokens are committed. Raw request/response telemetry is retained only for benchmark observability fields such as usage, cost, provider metadata, TTFT, latency, and cache tokens.
