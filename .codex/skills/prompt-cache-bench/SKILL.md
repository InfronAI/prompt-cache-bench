---
name: prompt-cache-bench
description: Use when working in the prompt-cache-bench repository on LLM prompt caching/provider-routing A/B experiments, report generation, reproducibility appendices, GitHub Pages publishing, release validation, or sensitive-data checks.
---

# Prompt Cache Bench

## Core workflow

1. Read `AGENTS.md`, `docs/methodology.md`, and `docs/benchmark-operations.md`.
2. For public report updates, keep changes staged under the experiment directory:
   `experiments/<model-family>/<model-id>/<ab-pair-and-run-id>/`.
3. Update related artifacts together: reports, data, figures, code snapshots, and metadata.
4. Keep large raw benchmark data out of report prose; link to GitHub `blob/main` or `tree/main` paths in reproducibility appendices.
5. Put configurable defaults in `.env.example` and local overrides/secrets in `.env`.
6. Run `python3 scripts/validate_release.py` before committing.

## Benchmark invariants

- Final comparisons use response-returned `usage.prompt_tokens` as the input-token source of truth.
- Included A/B pairs must have equal input tokens for the same model, payload, routing mode, group, and round.
- Exclude anomalous successful responses such as `usage.prompt_tokens=0`.
- Streaming TTFT requires consuming the full stream and reading final usage/cost chunks.
- Missing response cost is not zero.

## Report rules

- Chinese report prose and chart labels should be Chinese, preserving API fields and platform names.
- English report prose and chart labels should be English.
- HTML reports should include the Infron logo header and self-contained figures when practical.
- Online HTML preview links use GitHub Pages; source/data/code links use GitHub URLs.
- Report titles should match the experiment scope, not stale historical labels.

## Release safety

Run:

```bash
python3 scripts/validate_release.py
git diff --stat
git diff --check
```

Unexpected secret scan hits, broken GitHub links, missing report appendices, or unrendered Markdown links in HTML must be fixed before commit.
