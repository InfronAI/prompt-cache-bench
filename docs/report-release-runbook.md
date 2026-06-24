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
3. Confirm HTML assets are self-contained or referenced through stable public URLs.
4. Confirm report appendices reference raw datasets and code by path instead of embedding large raw records in the report body.
5. Confirm all figures, metadata, and reproducibility files required by the report are present.

Recommended local checks:

```bash
rg -n "TODO|FIXME|占位符|待补充" <local-report-dir>
rg -n "完整嵌入|不省略|100% 原始|request_json|original_response_json|provider_cost_breakdown" <local-report-dir>
```

The first command identifies unfinished drafting notes. The second command helps catch report text that may still describe embedded raw data or expose unnecessary raw-request fields.

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
git status --short --branch
git diff --stat
git diff --name-status
```

The diff should contain only files intended for the public release. If unrelated files appear, stop and isolate the report update before committing.

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

The validator reads release defaults from `.env.example`, local `.env`, and `PROMPT_CACHE_BENCH_*` environment variables. Use `PROMPT_CACHE_BENCH_DEFAULT_EXPERIMENT` when validating a newly published run directory, or pass `--experiment <path>`.

The validator checks:

- required experiment directories and files;
- Chinese/English HTML and Markdown report presence;
- Infron HTML report header and embedded figure basics;
- GitHub `blob/main` and `tree/main` links in reproducibility appendices;
- unrendered Markdown links inside HTML reports;
- common secret and API key patterns.

## 8. Commit And Push

Commit only after the diff and scans are clean:

```bash
git add <report-files> <data-files> <figure-files> <metadata-files> <code-files>
git commit -m "Update <model-id> benchmark report"
git push origin main
```

If `git push` is rejected because the remote has newer commits, do not force push. Fetch and rebase or use a fresh clone:

```bash
git fetch origin main
git rebase origin/main
git push origin main
```

When a local staging repository has diverged too much from the remote, create a fresh clone under `export/open-source/`, apply only the intended report files, then commit from that clean copy.

## 9. Post-Push Verification

After pushing:

1. Open the GitHub commit and confirm the changed file list is expected.
2. Open the GitHub Pages report URL.
3. Verify figures, logo, favicon, and embedded assets render correctly.
4. Verify Markdown links to code and datasets resolve to existing GitHub paths.
5. Verify the public report does not display secrets, internal-only text, or unnecessary raw records.

## 10. Release Checklist

Use this checklist for every public report update:

- [ ] Final local report reviewed.
- [ ] Final report files copied into `export/open-source/prompt-cache-bench/`.
- [ ] Required datasets, figures, code snapshots, and metadata staged together.
- [ ] `git diff --name-status` contains only intended files.
- [ ] Secret scan is clean or contains placeholders only.
- [ ] Raw-data exposure scan is reviewed.
- [ ] Report references data/code by GitHub path instead of embedding large raw records.
- [ ] Hashes and paths in the report match committed files.
- [ ] Commit created from the open-source staging repository.
- [ ] Push completed without force-pushing.
- [ ] GitHub Pages and Markdown previews checked after push.
