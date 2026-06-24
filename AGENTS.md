# AGENTS.md

This repository publishes reproducible benchmark artifacts for LLM prompt caching and provider-routing A/B testing.

## Operating Rules

- Treat every public report update as a release. Update the report, datasets, figures, code snapshots, and metadata together.
- Keep live API keys and local environment files out of the repository. `.env.example` may contain placeholders only.
- Public reports should reference large raw benchmark datasets by GitHub path instead of embedding full raw records in report bodies.
- Use response-returned telemetry as the source of truth for benchmark metrics, especially `usage.prompt_tokens`, cost fields, streaming TTFT, E2E latency, provider fields, and cache tokens.
- Preserve strict A/B pairing. Included pairs must keep the same model, request payload, routing mode, group, round, and equal `usage.prompt_tokens`.
- Use streaming with usage collection when measuring TTFT and final usage/cost fields.
- Put reusable configuration in `.env.example`; put local secrets and overrides in `.env`. Scripts should read `PROMPT_CACHE_BENCH_*` variables where applicable.
- Keep Chinese reports Chinese and English reports English, while preserving necessary API field names, model IDs, and platform names.
- HTML reports should be self-contained for figures and brand assets when possible. GitHub Pages links should be used for online HTML preview; GitHub `blob`/`tree` links should be used for source files and datasets.
- Before committing, run `python3 scripts/validate_release.py` and review `git diff --stat`.

## Primary References

- `docs/methodology.md`: benchmark methodology and metric definitions.
- `docs/benchmark-operations.md`: end-to-end operating workflow and reusable atomic capabilities.
- `docs/report-release-runbook.md`: release flow from local debug export to open-source staging and GitHub.
