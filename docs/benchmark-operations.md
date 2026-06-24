# Benchmark Operations Playbook

This playbook consolidates the reusable workflows and atomic capabilities used to maintain `prompt-cache-bench` as a long-running benchmark registry.

## 1. Project Intent

`prompt-cache-bench` is not a one-off model comparison. It is a longitudinal registry for inference-system behavior across models, providers, routing modes, cache strategies, cost profiles, TTFT, latency, throughput, and reproducibility artifacts.

Every published experiment should answer four questions:

1. What was controlled in the A/B design?
2. Which metrics were measured from response-returned telemetry?
3. Which platform or provider won under each routing objective?
4. Which raw datasets, code, figures, and metadata make the result reproducible?

## 2. Canonical Directory Contract

Published experiments use this structure:

```text
experiments/<model-family>/<model-id>/<ab-pair-and-run-id>/
├── reports/       # Final HTML and Markdown reports
├── data/          # Benchmark datasets required for reproduction
├── figures/       # SVG figures used by reports when not embedded
├── code/          # Exact experiment code snapshot
└── metadata/      # Manifest, checksums, and run metadata
```

Use model IDs as directory names where practical. Convert provider pairs and run parameters into explicit run IDs, for example:

```text
infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-2026-06-19
```

## 3. Benchmark Design Workflow

1. Define the model, provider pair, routing modes, groups, rounds, stream mode, timeout, and worker count.
2. Generate or select the benchmark corpus before starting the run. Keep the same payload for each A/B pair.
3. Send two identical requests per provider per pair:
   - first request: warms or refreshes cache behavior;
   - second request: observes cache reuse through cache read tokens.
4. Record request-level telemetry:
   - HTTP status and error state;
   - provider identifier when returned;
   - response-returned `usage`;
   - cost and cost details when returned;
   - streaming TTFT;
   - end-to-end E2E latency;
   - cache read/write tokens;
   - completion tokens and response throughput.
5. Exclude records that fail data-quality constraints:
   - HTTP failure or incomplete response;
   - missing final streaming usage when usage is required;
   - anomalous `usage.prompt_tokens`, including zero prompt tokens for successful benchmark responses;
   - unequal Infron/OpenRouter input tokens within the same A/B pair.

## 4. Metric Source Of Truth

Use API response telemetry, not local estimates, for final metrics.

| Metric | Source of truth | Direction |
| --- | --- | --- |
| Input tokens | `usage.prompt_tokens` | Equal across included A/B pairs |
| Completion tokens | response `usage` completion fields | Higher may increase output work |
| Cache hit rate | second request cache read tokens / second request prompt tokens | Higher is better |
| Actual cost | response-returned cost/cost_details | Lower is better |
| Throughput | completion tokens / E2E latency seconds | Higher is better |
| E2E latency | full request-response elapsed time | Lower is better |
| Streaming TTFT | first streaming chunk/token arrival time | Lower is better |
| Provider routing | observable response provider fields | Descriptive attribution only |

Reasoning output is treated as part of the response workload when the provider includes it in usage or streaming deltas. Do not create a separate reasoning leaderboard unless a future experiment explicitly defines a separate reasoning metric.

## 5. Report Architecture

Each full report should include:

1. Abstract and executive outline.
2. Research background and business value.
3. Experimental design, dataset construction, and controls.
4. Data-quality filtering and included/excluded sample counts.
5. Core metrics by routing mode.
6. Visual summaries, including conclusion overview, route-mode comparisons, radar charts, and metric curves where available.
7. Provider distribution and routing-behavior analysis.
8. Mechanism discussion with clear distinction between observed telemetry and engineering interpretation.
9. Limitations and future work.
10. Reproducibility appendices linking to datasets, code, figures, reports, and manifests.

Do not embed full raw benchmark records in report bodies. Link to repository files in the reproducibility appendix.

## 6. Bilingual Report Rules

- Chinese reports should use Chinese prose and Chinese chart labels, except for necessary model IDs, API field names, platform names, and code.
- English reports should use English prose and English chart labels.
- Keep metric terminology consistent:
  - Chinese: `端到端 E2E 时延`, `流式 TTFT`, `吞吐量`, `实际成本`, `缓存命中率`.
  - English: `E2E latency`, `Streaming TTFT`, `throughput`, `observed cost`, `cache hit rate`.
- Report titles should describe the actual study scope. Avoid stale labels such as "replication study" when the report is a broader benchmark of routing strategy, cost, cache, and performance.

## 7. Visual And HTML Release Rules

- HTML reports should include the Infron logo in the header and should keep figures self-contained when practical.
- GitHub Pages URLs should be used for online HTML report preview.
- GitHub `blob/main` URLs should be used for files.
- GitHub `tree/main` URLs should be used for directories.
- If figures are embedded as base64 SVGs in HTML, keep source SVGs in `figures/` for review and reproducibility.
- Do not let labels obscure chart marks. Prefer explicit winner labels outside bars or below chart areas.

## 8. Release Workflow

1. Finish local debug work in the local export directory.
2. Copy only finalized report-related files into `export/open-source/prompt-cache-bench`.
3. Review the staging diff:

```bash
git status --short --branch
git diff --stat
git diff --name-status
```

4. Run the release validator:

```bash
python3 scripts/validate_release.py
```

5. Fix every unexpected warning or error.
6. Commit with a narrow message.
7. Push to `main`.
8. Verify GitHub Pages HTML, Markdown previews, appendix links, logos, figures, and raw dataset paths.

## 9. Configuration Surface

Project-level configuration belongs in `.env.example` and local overrides belong in `.env`.

Configuration groups:

| Group | Variables |
| --- | --- |
| API endpoints and keys | `INFRON_BASE_URL`, `INFRON_API_KEY`, `OPENROUTER_BASE_URL`, `OPENROUTER_API_KEY` |
| Standard request headers | `PROMPT_CACHE_BENCH_USER_AGENT`, `PROMPT_CACHE_BENCH_ACCEPT`, `PROMPT_CACHE_BENCH_CONNECTION` |
| Benchmark defaults | `PROMPT_CACHE_BENCH_MODEL`, `PROMPT_CACHE_BENCH_DATASET_NAME`, `PROMPT_CACHE_BENCH_ROUTING_SORTS`, `PROMPT_CACHE_BENCH_GROUPS`, `PROMPT_CACHE_BENCH_ROUNDS`, `PROMPT_CACHE_BENCH_WORKERS`, `PROMPT_CACHE_BENCH_TIMEOUT_SECONDS`, `PROMPT_CACHE_BENCH_STREAM`, `PROMPT_CACHE_BENCH_INCLUDE_USAGE` |
| Release defaults | `PROMPT_CACHE_BENCH_REPO_URL`, `PROMPT_CACHE_BENCH_PAGES_BASE_URL`, `PROMPT_CACHE_BENCH_DEFAULT_EXPERIMENT` |

Reusable scripts should read these environment variables before falling back to hard-coded defaults. Do not store real API keys in `.env.example`.

## 10. Atomic Capabilities

| Capability | Use it when | Implementation surface |
| --- | --- | --- |
| Strict A/B pair filtering | Comparing provider outcomes | `scripts/rerun_routing_sort_cache_cost_ab.py` |
| Streaming TTFT measurement | Measuring first-token experience | benchmark runner stream path |
| Usage/cost finalization | Streaming responses return usage/cost in final chunks | benchmark runner final chunk handling |
| Anomaly exclusion | `prompt_tokens=0`, missing usage, incomplete records | benchmark runner and data-quality filters |
| Report export | Turning Markdown into self-contained HTML/PDF | `scripts/export_routing_report_pdf.py` |
| Public release validation | Before every commit/push | `scripts/validate_release.py` |
| Reproducibility appendix linking | Reports must link to data/code/assets | report authoring workflow |
| Bilingual consistency check | Publishing zh/en reports | release review and validator-assisted grep checks |
| Sensitive-data defense | Before every public commit | validator and runbook secret scans |

## 11. Safety Baseline

Never publish:

- API keys, bearer tokens, `.env`, private keys, or password files.
- Customer private text or non-benchmark production payloads.
- Unnecessary original request/response bodies inside public report prose.
- Internal-only routing traces unless explicitly approved for release.

When in doubt, publish structured benchmark artifacts under `data/` and reference them by path from the report, rather than expanding them inline.
