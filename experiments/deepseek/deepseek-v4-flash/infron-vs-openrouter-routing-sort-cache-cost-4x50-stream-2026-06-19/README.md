# Prompt Cache Routing A/B Study: DeepSeek V4 Flash

This experiment compares Infron and OpenRouter on `deepseek/deepseek-v4-flash` under three provider routing priorities:

- Throughput First
- Price First
- Latency First

The experiment uses a 4x50 streaming design. Each `sort/group/round` pair is sent to both platforms. Each platform receives two identical requests per round so that the second request can observe prompt-cache read behavior.

## Report

- [GitHub Markdown preview](reports/prompt-cache-routing-ab-study__deepseek-v4-flash__infron-vs-openrouter__4x50-stream__2026-06-19.zh.md)
- [Self-contained HTML report](reports/prompt-cache-routing-ab-study__deepseek-v4-flash__infron-vs-openrouter__4x50-stream__2026-06-19.zh.html)

Use the Markdown report for online preview in GitHub. GitHub displays `.html` files as source code unless GitHub Pages is enabled.

Report filename convention:

```text
{study-name}__{model}__{provider-a-vs-provider-b}__{design}__{date}.{lang}.{ext}
```

## Data

- `data/benchmark_pairs.csv`: paired A/B dataset used for aggregate tables and figures.
- `data/benchmark_requests.jsonl`: request-level telemetry dataset.
- `data/records.json`: filtered structured records used by the report.
- `data/records_excluded.json`: excluded records for auditability.
- `data/summary.json`: computed summary metrics and chart metadata.

## Code

- `code/rerun_routing_sort_cache_cost_ab.py`: exact experiment/report script snapshot.
- `code/export_routing_report_pdf.py`: report HTML/PDF exporter snapshot.

## Reproduce

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
