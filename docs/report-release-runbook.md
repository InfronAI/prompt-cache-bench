# Report Release Runbook

This runbook defines the release flow for moving a locally debugged benchmark report into the open-source `prompt-cache-bench` repository.

The goal is to keep local experimentation fast while making public releases reproducible, reviewable, and safe from accidental key or sensitive-data exposure.

## 1. Working Directories

Use two separate areas:

| Area | Purpose | Example |
| --- | --- | --- |
| Local debug export | Iteration workspace for draft reports, temporary charts, PDFs, and intermediate experiment outputs | `export/deepseek_v4_flash_all_experiments/` |
| Open-source staging | Clean repository mirror used for public GitHub commits | `export/open-source/prompt-cache-bench/` |

Do not push directly from the local debug export. Always copy finalized report artifacts into `export/open-source/prompt-cache-bench/`, review the diff there, then commit and push.

Hard rule: public A/B benchmark reports are published only from the `InfronAI/prompt-cache-bench` repository. The product/debug repository may contain draft reports for iteration, but it is not the public release target for benchmark artifacts.

Before staging or committing a public report, confirm the repository identity from the open-source staging root:

```bash
cd export/open-source/prompt-cache-bench
git remote -v
git rev-parse --show-toplevel
```

The remote must resolve to `https://github.com/InfronAI/prompt-cache-bench.git` or `git@github.com:InfronAI/prompt-cache-bench.git`. If it points to another repository, stop and switch to the correct staging checkout before committing.

## 2. Target Repository Layout

Each finalized experiment should live under:

```text
experiments/<model-family>/<model-id>/<ab-pair-and-run-id>/
├── reports/       # Final HTML and Markdown reports
├── data/          # Benchmark datasets required for reproduction
├── figures/       # Report figures when not embedded directly
├── code/          # Exact experiment code snapshot when needed
└── metadata/      # Manifest, checksums, and run metadata
```

Example:

```text
experiments/deepseek/deepseek-v4-flash/
└── infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-2026-06-19/
    ├── reports/
    ├── data/
    ├── figures/
    ├── code/
    └── metadata/
```

## 3. Finalize Local Debug Report

Before copying files into the open-source staging repository:

1. Confirm the report is the final reviewed version.
2. Confirm terminology is consistent across text, tables, and charts.
3. Generate both language variants:
   - Chinese report: every narrative section, table heading, chart title, chart label, tooltip, and diagram label should be Chinese. Keep only necessary English proper nouns and API/model terms such as `Infron`, `OpenRouter`, `TTFT`, `provider.sort`, `usage.prompt_tokens`, and model IDs.
   - English report: every narrative section, table heading, chart title, chart label, tooltip, and diagram label should be English. Do not leave Chinese fallback labels in ECharts options, SVG text, table cells, or appendices.
4. Confirm Chinese and English reports have the same report architecture, chart set, reproducibility appendix, favicon/logo treatment, and source/data links.
5. Confirm HTML assets are self-contained or referenced through stable public URLs.
6. Confirm report appendices reference raw datasets and code by path instead of embedding large raw records in the report body.
7. Confirm all figures, metadata, and reproducibility files required by the report are present.

Recommended local checks:

```bash
rg -n "TODO|FIXME|占位符|待补充" <local-report-dir>
rg -n "完整嵌入|不省略|100% 原始|request_json|original_response_json|provider_cost_breakdown" <local-report-dir>
```

The first command identifies unfinished drafting notes. The second command helps catch report text that may still describe embedded raw data or expose unnecessary raw-request fields.

Recommended language checks:

```bash
python3 - <<'PY'
from pathlib import Path
import re
for path in Path("export/open-source/prompt-cache-bench/experiments").glob("**/reports/*.*"):
    if path.name.endswith((".en.html", ".en.md")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        cjk = len(re.findall(r"[\u4e00-\u9fff]", text))
        print(path, "CJK chars:", cjk)
PY
```

English reports should have `0` CJK characters. Chinese reports should be reviewed manually for accidental English section labels such as `Abstract`, `Conclusion Overview`, `Figure`, or `Table`, except where those words are intentional technical terms.

## 4. Stage Files In `export/open-source`

Copy finalized files from the local debug export into the open-source staging repository.

Example:

```bash
cp export/deepseek_v4_flash_all_experiments/reports_academic/final-report.zh.html \
  export/open-source/prompt-cache-bench/experiments/deepseek/deepseek-v4-flash/<run-id>/reports/final-report.zh.html
```

If the report depends on datasets, figures, code snapshots, or metadata files, copy those files in the same release batch.

After copying, inspect the staging diff from the open-source repository root:

```bash
cd export/open-source/prompt-cache-bench
git remote -v
git status --short --branch
git diff --stat
git diff --name-status
```

The remote must be `InfronAI/prompt-cache-bench`, and the diff should contain only files intended for the public release. If unrelated files appear, or if the remote is not the benchmark repository, stop and isolate the report update before committing.

### 4.1 Standard Sync Script

Use `scripts/sync_report_release.py` from the open-source repository root to codify the release preparation steps:

```bash
cd export/open-source/prompt-cache-bench
python3 scripts/sync_report_release.py \
  --experiment experiments/deepseek/deepseek-v4-flash/<run-id>
```

The script:

- prints the target experiment path so stale `.env` defaults are visible;
- optionally copies finalized local artifacts when `--copy-local --local-experiment-dir <dir>` is provided;
- normalizes all HTML report favicons to the Infron CDN icon used by GitHub Pages;
- checks that `.en.html` and `.en.md` contain no Chinese characters;
- checks that `.zh.html` and `.zh.md` contain substantial Chinese text and no obvious English section labels;
- checks that Chinese and English HTML reports share core structural markers;
- updates `metadata/manifest.json` checksums and file sizes;
- verifies that `README.md` and `index.html` include the expected GitHub Pages and GitHub source links;
- runs the repository validator unless `--skip-validator` is passed.

If `.env` exists, it overrides `.env.example`. Before running the sync script, confirm:

```bash
rg -n "PROMPT_CACHE_BENCH_DEFAULT_EXPERIMENT" .env .env.example
```

The value should point to the report you are publishing. A stale `.env` is the most common cause of syncing an old report directory.

## 5. Defensive Secret Scan

Run a defensive scan before every commit:

```bash
rg -n "ghp_|github_pat_|GITHUB_TOKEN|CLICKHOUSE_PASSWORD|AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9]|Bearer [A-Za-z0-9._-]+|OPENAI_API_KEY=.+|INFRON_API_KEY=.+|OPENROUTER_API_KEY=.+" -S .
```

Expected allowed matches:

- `.env.example` placeholders
- README examples such as `INFRON_API_KEY=your_infron_api_key_here`

Unexpected matches must be removed before commit.

Also check for local environment or credential files:

```bash
find . -name ".env" -o -name "*.pem" -o -name "*secret*" -o -name "*credential*"
```

No real `.env`, private key, secret, or credential file should be committed.

## 6. Defensive Raw-Data Exposure Scan

Reports should reference raw benchmark datasets by repository path unless the release explicitly requires a small excerpt.

Run:

```bash
rg -n "完整嵌入|不省略|100% 原始|request_json|original_response_json|provider_cost_breakdown|Authorization|api_key|apikey|password" experiments/
```

Review every match. Public reports should avoid embedding unnecessary request bodies, original responses, authorization headers, customer text, or internal-only fields.

When raw benchmark files are intentionally published under `data/`, confirm they contain benchmark telemetry and synthetic/approved benchmark payloads only.

## 7. Reproducibility Checks

For each release, verify that the report points to the actual committed paths:

```bash
find experiments/<model-family>/<model-id>/<run-id> -maxdepth 3 -type f | sort
```

Reproducibility appendix path policy:

- Local debug/export reports may use repository-relative or local `export/...` paths.
- Public GitHub and GitHub Pages reports must use online-accessible GitHub links: `blob/main` URLs for files, `tree/main` URLs for directories, and GitHub Pages URLs for published HTML reports.
- Do not leave unqualified local filesystem paths in public report appendices unless they are explicitly labeled as local-only.

Check that these files exist when referenced by the report:

- HTML report
- Markdown report when published
- benchmark pair dataset
- request-level telemetry dataset when published
- summary or manifest
- figure files, if not embedded
- exact experiment code snapshot or shared script path

If hashes are shown in the report, recompute them before release:

```bash
shasum -a 256 <file>
```

Run the repository validator before committing:

```bash
python3 scripts/validate_release.py
```

For the full bilingual report-release check, run:

```bash
python3 scripts/sync_report_release.py \
  --experiment experiments/<model-family>/<model-id>/<run-id>
```

The validator reads release defaults from `.env.example`, local `.env`, and `PROMPT_CACHE_BENCH_*` environment variables. Use `PROMPT_CACHE_BENCH_DEFAULT_EXPERIMENT` when validating a newly published run directory, or pass `--experiment <path>`.

The validator checks:

- required experiment directories and files;
- Chinese/English HTML and Markdown report presence;
- Infron HTML report header and embedded figure basics;
- GitHub `blob/main` and `tree/main` links in reproducibility appendices;
- unrendered Markdown links inside HTML reports;
- common secret and API key patterns.

## 8. Homepage Registry Entry Standard

The GitHub Pages homepage contains bilingual Experiment Registry tables. Every published experiment must use the same table shape in both language sections.

Canonical columns:

| English column | Chinese column | Required content |
| --- | --- | --- |
| Status | 状态 | Published / 已发布 badge for released experiments |
| Model | 模型 | Exact model ID in `<code>` |
| A/B Pair | A/B Pair | Comparison target, normally `Infron vs OpenRouter` |
| Design | 实验设计 | Compact experiment settings sentence |
| Reports | 报告 | Fixed ordered report links |
| Data | 数据 | Dataset directory link |

Registry rows must follow these rules:

- Use one `<tr>` per published experiment.
- Do not split Chinese and English reports into separate rows.
- Do not use `rowspan` in the homepage registry.
- Keep the same row order in English and Chinese registries.
- Keep the `Design` cell concise and comparable across all rows: groups x rounds, streaming, routing sort modes, reasoning/thinking behavior, prompt-length tiers, and API protocol scope.
- Use online-accessible links only.

The `Reports` column must use this exact order:

- English registry: `EN HTML · ZH HTML · EN MD · ZH MD · Reports`
- Chinese registry: `中文 HTML · EN HTML · 中文 MD · EN MD · 报告目录`

The `Data` column must link to the committed `data/` directory:

- English registry label: `Dataset`
- Chinese registry label: `数据集`

Link targets:

- HTML reports: GitHub Pages URLs.
- Markdown reports: GitHub `blob/main` URLs.
- Reports directory: GitHub `tree/main` URL for `reports/`.
- Data directory: GitHub `tree/main` URL for `data/`.

Before committing a homepage update, inspect both registry table snippets and run:

```bash
python3 scripts/sync_report_release.py \
  --experiment experiments/<model-family>/<model-id>/<run-id>
```

After pushing, verify the live GitHub Pages homepage no longer contains stale two-row or `rowspan` registry entries for the released model.

## 9. Commit And Push

Commit only after the diff and scans are clean:

```bash
git remote -v
git add <report-files> <data-files> <figure-files> <metadata-files> <code-files>
git commit -m "Update <model-id> benchmark report"
git push origin main
```

Never commit or push a public A/B benchmark release from the product/debug repository by accident. The commit should be created from `export/open-source/prompt-cache-bench`, and `git remote -v` should show `InfronAI/prompt-cache-bench` immediately before `git add`.

If `git push` is rejected because the remote has newer commits, do not force push. Fetch and rebase or use a fresh clone:

```bash
git fetch origin main
git rebase origin/main
git push origin main
```

When a local staging repository has diverged too much from the remote, create a fresh clone under `export/open-source/`, apply only the intended report files, then commit from that clean copy.

## 10. Post-Push Verification

After pushing:

1. Open the GitHub commit and confirm the changed file list is expected.
2. Confirm the remote branch points at the pushed commit:

```bash
git ls-remote origin refs/heads/main
```

3. Open both GitHub Pages report URLs:
   - `.../<report>.zh.html`
   - `.../<report>.en.html`
4. Verify the URLs use the `https://infronai.github.io/prompt-cache-bench/` base path. A URL under another GitHub Pages site is a release-target error.
5. Verify the Chinese report is Chinese and the English report is English across text, tables, charts, ECharts controls, diagrams, and appendices.
6. Verify figures, logo, favicon, and embedded assets render correctly.
7. Verify Markdown links to code and datasets resolve to existing GitHub paths.
8. Verify `index.html` links to the current report pair and dataset.
9. Verify the public report does not display secrets, internal-only text, or unnecessary raw records.

## 10. Release Checklist

Use this checklist for every public report update:

- [ ] Final local report reviewed.
- [ ] Chinese and English reports generated with matching structure and language-specific chart/table text.
- [ ] Current shell is inside `export/open-source/prompt-cache-bench/`.
- [ ] `git remote -v` points to `InfronAI/prompt-cache-bench`.
- [ ] Final report files copied into `export/open-source/prompt-cache-bench/`.
- [ ] Required datasets, figures, code snapshots, and metadata staged together.
- [ ] `.env` and `.env.example` `PROMPT_CACHE_BENCH_DEFAULT_EXPERIMENT` point to the intended report, or `--experiment` is passed explicitly.
- [ ] `python3 scripts/sync_report_release.py --experiment <path>` passes.
- [ ] `git diff --name-status` contains only intended files.
- [ ] Secret scan is clean or contains placeholders only.
- [ ] Raw-data exposure scan is reviewed.
- [ ] Report references data/code by GitHub path instead of embedding large raw records.
- [ ] Hashes and paths in the report match committed files.
- [ ] `README.md` and `index.html` link to the current Chinese HTML, English HTML, reports directory, data directory, and manifest.
- [ ] All public links use `github.com/InfronAI/prompt-cache-bench` or `infronai.github.io/prompt-cache-bench`.
- [ ] Commit created from the open-source staging repository.
- [ ] Push completed without force-pushing.
- [ ] GitHub Pages and Markdown previews checked after push.
