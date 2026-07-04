# A/B Report Standard

This is the canonical structure for generated A/B benchmark reports in this project. Future A/B reports must follow this structure unless the user explicitly requests a different report type.

## Scope

Use this standard for reports comparing two platforms, providers, routes, models, cache policies, latency policies, pricing policies, or other paired inference configurations.

The report must be self-contained. It should describe only the current experiment subject and must not say that it follows, references, reuses, or copies another report.

## Required Artifacts

Every A/B report must produce:

- Chinese HTML
- English HTML
- Markdown
- PDF

All files must be written under `export/`.

## Visual And Interaction Standard

- Use the project design system in `docs/design/infron-design-system/`.
- Use the established blue and warm comparison palette: blue for Infron or the first platform, warm orange for OpenRouter or the second platform, and gold only for objective winners.
- Use ECharts for interactive HTML charts.
- Keep the chart language, spacing, table density, conclusion matrix, and provider drill-down hierarchy consistent across Chinese and English.
- Keep bilingual reports structurally identical.
- In all comparable tables, bold the advantaged party or advantaged value.
- Do not hide denominators. Every percentage must be bound to its workload, request count, pair count, or token basis.

## Required Report Structure

Use this section order for every full A/B report:

1. Title
2. Abstract and executive outline
3. Conclusion overview matrix
4. Routing-mode or experiment-arm conclusions
5. Introduction: background, research questions, and contributions
6. Research hypotheses
7. Method: experimental design, dataset construction, and controlled variables
8. Dataset construction method
9. Pairing and filtering rule
10. Metric definitions
11. Experimental environment and data quality control
12. Overall metrics and main findings
13. Tail latency and statistical tests
14. Reasoning / thinking telemetry and control check
15. API protocol record
16. ECharts visualizations by routing mode or experiment arm
17. Technical architecture and mechanism explanation
18. Provider/route drill-down
19. Cache-rate and cost divergence drill-down
20. Prompt-length stratified cache analysis when the run includes length tiers
21. Stratified group-level stability check
22. Business value, applicability boundary, and engineering implications
23. Conclusion
24. Limitations, missing data, and next experiment plan
25. Reproducibility appendix

## Abstract Rule

The abstract must present conclusions, not implementation detail.

Include:

- Experiment subject and comparison target
- Main winners across cache, cost, throughput, E2E latency, and TTFT
- Practical interpretation for platform choice

Do not include in the abstract:

- Full experiment settings
- Detailed filtering rules
- Raw excluded-record counts
- Long reproducibility descriptions

Those details belong in Method, Data Quality, and Reproducibility sections.

## Data Quality And Pairing Rule

The report must state the pairing and filtering rule in the Method and Data Quality sections.

For input-token controlled LLM A/B tests:

- Use response-returned `usage.prompt_tokens` as the input-token control.
- Use the configured token-delta tolerance for paired inclusion.
- Preserve excluded records for audit.
- Explain whether token equality is exact or tolerance-based.
- Keep pair count and request-level observation count visible outside the abstract.

## Prompt Length Stratification

When an A/B atomic test enables prompt-length tiers, the report must include a dedicated prompt-length stratification section.

The runner should keep the original A/B controls unchanged and assign each `sort/group/round` pair to a deterministic tier, such as `short`, `medium`, and `long`. The tier changes only the stable prompt prefix length; model, route, first/second replay, token tolerance, telemetry extraction, and filtering rules remain unchanged.

The section must include:

- Tier label and target prompt-token scale.
- Actual response-returned second prompt tokens by platform.
- Second-request cache read tokens by platform.
- Token-level cache hit rate by platform.
- Cost, E2E latency, and TTFT by platform when available.
- A tier x routing-mode cache-hit table.
- Bold highlighting for the advantaged platform in every comparable row.

The paired CSV and request-level JSONL must include `prompt_length_tier` and `target_prompt_tokens`, while the summary JSON must include tier-level aggregates.

## Required Tables

At minimum, include these tables:

- Executive outline
- Routing-mode or experiment-arm winner matrix
- Metric definitions
- Environment and data quality
- Overall metrics
- Tail latency percentiles
- Statistical tests with bootstrap CI and paired permutation p-value when available
- Reasoning telemetry when applicable
- API protocol record
- Provider/route attribution summary
- Provider detail table
- Cache-rate and cost divergence drill-down
- Prompt-length stratified cache table when length tiers are enabled
- Group-level stability checks
- Business implication table
- Limitations table
- Reproducibility artifact table

All comparable metric tables must bold the advantaged value:

- Higher is better: cache hit rate, throughput, successful rounds, attribution coverage when used as a quality signal.
- Lower is better: observed cost, cost per 1K input tokens, E2E latency, TTFT, tail latency, reasoning tokens when `reasoning.effort=none` is a control.
- Winner-only tables must bold the winning platform name.

## Reasoning / Thinking Telemetry

Every LLM A/B report must keep a Reasoning / Thinking section. If the benchmark leaves reasoning/thinking at platform default, the section should state that no explicit `reasoning` parameter was sent and compare Infron versus OpenRouter under default behavior. If the benchmark explicitly sets `reasoning.effort`, the section should state the configured effort and treat reasoning telemetry as a control check.

At minimum, include reasoning tokens, average reasoning tokens per request, reasoning request count, first reasoning token timing when available, TTFT, and E2E latency.

## API Protocol

The canonical A/B benchmark protocol is:

- `/v1/chat/completions`

The report must record that the experiment uses `/v1/chat/completions` and must not include `/v1/messages` or `/v1/responses` as standard A/B dimensions.

The protocol section must compare Infron and OpenRouter for `/v1/chat/completions` and include:

- Endpoint path and protocol label.
- Request count and paired round count.
- HTTP success rate.
- Response `usage` coverage.
- Token usage coverage.
- Observed cost coverage.
- Cache telemetry coverage.
- HTTP status distribution.
- Top error messages, with sensitive values redacted.

The runner must default to `/v1/chat/completions` only. The paired CSV and request-level JSONL should include `api_protocol` and `endpoint_path`, and `summary.json` should include `api_protocol_compatibility` for the canonical Chat Completions endpoint.

## Required Charts

Use ECharts in HTML reports for:

- Conclusion or capability overview
- Routing-mode metric comparison
- Normalized radar/contour
- Cost-cache efficiency plane
- E2E latency vs TTFT
- Provider distribution
- Per-route metric advantage drill-down

Charts must be driven by the same summary data as the tables.

## Reproducibility Appendix

The appendix must include direct paths to:

- Summary JSON
- Paired dataset CSV
- Request-level dataset JSONL
- Filtered records
- Excluded-record audit file
- Benchmark runner source
- HTML/report renderer source
- Relevant test source
- Dataset reference or dataset file path

If an external dataset is not used, name the built-in dataset and point to the request-level export.

Path policy:

- Local debug/export reports may use repository-relative or `export/...` relative paths.
- Public GitHub Pages or open-source GitHub reports must use online-accessible GitHub links in the reproducibility appendix: `blob/main` URLs for files, `tree/main` URLs for directories, and GitHub Pages URLs for published HTML pages.
- Do not mix local filesystem paths into public report appendices unless they are explicitly labeled as local-only reproduction paths.

## Current Canonical Implementation

The current canonical implementation is:

- Renderer: `scripts/render_glm52_deepseek_style_report.py`
- Benchmark runner: `scripts/rerun_routing_sort_cache_cost_ab.py`
- Tests: `tests/test_rerun_routing_sort_cache_cost_ab.py`
- Example report: `export/glm52_all_experiments/reports_academic/routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_none_20260630-report-zh.html`

Future renderers may be generalized, but the generated report structure must remain compatible with this standard.
