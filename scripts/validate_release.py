#!/usr/bin/env python3
"""Validate public prompt-cache-bench release artifacts.

The script intentionally uses only the Python standard library so it can run in a
fresh clone before committing or publishing benchmark reports.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse


DEFAULT_REPO_URL = "https://github.com/InfronAI/prompt-cache-bench"
DEFAULT_EXPERIMENT = (
    "experiments/deepseek/deepseek-v4-flash/"
    "infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-2026-06-27"
)

SECRET_PATTERNS = [
    re.compile(r"ghp_[A-Za-z0-9_]+"),
    re.compile(r"github_pat_[A-Za-z0-9_]+"),
    re.compile(r"GITHUB_TOKEN\s*=\s*[^\\s]+"),
    re.compile(r"CLICKHOUSE_PASSWORD\s*=\s*[^\\s]+"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"Bearer\s+[A-Za-z0-9._-]{20,}"),
    re.compile(r"(OPENAI_API_KEY|INFRON_API_KEY|OPENROUTER_API_KEY)\s*=\s*(?!your_)[^\\s]+"),
]

ALLOWED_SECRET_MATCHES = (
    ".env.example",
    "README.md",
    "docs/report-release-runbook.md",
)

TEXT_EXTENSIONS = {
    ".cff",
    ".css",
    ".csv",
    ".html",
    ".json",
    ".jsonl",
    ".md",
    ".py",
    ".svg",
    ".toml",
    ".txt",
    ".webmanifest",
    ".yaml",
    ".yml",
}


def load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values


def load_config(root: Path) -> dict[str, str]:
    config = load_env_file(root / ".env.example")
    config.update(load_env_file(root / ".env"))
    for key, value in os.environ.items():
        if key.startswith("PROMPT_CACHE_BENCH_"):
            config[key] = value
    return config


def iter_text_files(root: Path):
    for path in root.rglob("*"):
        if ".git" in path.parts or not path.is_file():
            continue
        if path.suffix in TEXT_EXTENSIONS or path.name in {"LICENSE", "AGENTS.md"}:
            yield path


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def check_secrets(root: Path) -> list[str]:
    issues: list[str] = []
    for path in iter_text_files(root):
        text = read_text(path)
        relpath = rel(path, root)
        for pattern in SECRET_PATTERNS:
            for match in pattern.finditer(text):
                if relpath in ALLOWED_SECRET_MATCHES:
                    continue
                line = text.count("\n", 0, match.start()) + 1
                issues.append(f"{relpath}:{line}: possible secret matched `{pattern.pattern}`")
    return issues


def github_url_to_local_path(url: str, repo_url: str) -> tuple[str, bool] | None:
    parsed = urlparse(url)
    repo = urlparse(repo_url.rstrip("/"))
    prefix = repo.path.rstrip("/") + "/"
    if parsed.netloc != repo.netloc or not parsed.path.startswith(prefix):
        return None
    rest = parsed.path[len(prefix) :]
    if rest.startswith("blob/main/"):
        return unquote(rest[len("blob/main/") :]), False
    if rest.startswith("tree/main/"):
        return unquote(rest[len("tree/main/") :]), True
    return None


def check_github_links(root: Path, experiment_dir: Path, repo_url: str) -> list[str]:
    issues: list[str] = []
    reports_dir = experiment_dir / "reports"
    urls_seen = 0
    escaped_repo = re.escape(repo_url.rstrip("/"))
    for path in reports_dir.glob("*.*"):
        if path.suffix not in {".md", ".html"} or not (path.name.endswith(".zh.md") or path.name.endswith(".en.md") or path.name.endswith(".zh.html") or path.name.endswith(".en.html")):
            continue
        text = read_text(path)
        for url in re.findall(rf"{escaped_repo}/(?:blob|tree)/main/[^\s)\"<>]+", text):
            urls_seen += 1
            converted = github_url_to_local_path(url, repo_url)
            if converted is None:
                issues.append(f"{rel(path, root)}: invalid GitHub URL shape: {url}")
                continue
            local, is_dir = converted
            target = root / local
            if is_dir and not target.is_dir():
                issues.append(f"{rel(path, root)}: linked directory does not exist: {local}")
            if not is_dir and not target.is_file():
                issues.append(f"{rel(path, root)}: linked file does not exist: {local}")
        if path.suffix == ".html" and "](" in text:
            issues.append(f"{rel(path, root)}: HTML contains unrendered Markdown link syntax")
    if urls_seen == 0:
        issues.append(f"{rel(reports_dir, root)}: no GitHub reproducibility links found")
    return issues


def check_experiment_shape(root: Path, experiment_dir: Path) -> list[str]:
    issues: list[str] = []
    required_dirs = ["reports", "data", "figures", "code", "metadata"]
    for name in required_dirs:
        if not (experiment_dir / name).is_dir():
            issues.append(f"{rel(experiment_dir, root)}: missing `{name}/`")

    required_files = [
        "data/benchmark_pairs.csv",
        "data/benchmark_requests.jsonl",
        "data/records.json",
        "data/records_excluded.json",
        "data/summary.json",
        "metadata/manifest.json",
    ]
    for name in required_files:
        if not (experiment_dir / name).is_file():
            issues.append(f"{rel(experiment_dir / name, root)}: missing required file")

    report_files = list((experiment_dir / "reports").glob("*.html")) + list((experiment_dir / "reports").glob("*.md"))
    if not any(p.name.endswith(".zh.html") for p in report_files):
        issues.append(f"{rel(experiment_dir / 'reports', root)}: missing Chinese HTML report")
    if not any(p.name.endswith(".en.html") for p in report_files):
        issues.append(f"{rel(experiment_dir / 'reports', root)}: missing English HTML report")
    if not any(p.name.endswith(".zh.md") for p in report_files):
        issues.append(f"{rel(experiment_dir / 'reports', root)}: missing Chinese Markdown report")
    if not any(p.name.endswith(".en.md") for p in report_files):
        issues.append(f"{rel(experiment_dir / 'reports', root)}: missing English Markdown report")
    return issues


def check_report_basics(root: Path, experiment_dir: Path, repo_url: str) -> list[str]:
    issues: list[str] = []
    for html_report in (experiment_dir / "reports").glob("*.html"):
        if not (html_report.name.endswith(".zh.html") or html_report.name.endswith(".en.html")):
            continue
        text = read_text(html_report)
        if '<div class="report-brand">' not in text:
            issues.append(f"{rel(html_report, root)}: missing report-brand header")
        if 'alt="Infron"' not in text:
            issues.append(f"{rel(html_report, root)}: missing Infron logo alt text")
        if "data:image/svg+xml;base64," not in text:
            issues.append(f"{rel(html_report, root)}: no embedded SVG figures found")
        if "<h2>12." not in text:
            issues.append(f"{rel(html_report, root)}: missing reproducibility appendix")

    for md_report in (experiment_dir / "reports").glob("*.md"):
        if not (md_report.name.endswith(".zh.md") or md_report.name.endswith(".en.md")):
            continue
        text = read_text(md_report)
        if "## 12." not in text:
            issues.append(f"{rel(md_report, root)}: missing reproducibility appendix")
        if repo_url not in text:
            issues.append(f"{rel(md_report, root)}: missing GitHub reproducibility links")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate prompt-cache-bench release artifacts.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument(
        "--experiment",
        default=None,
        help="Experiment directory to validate. Defaults to PROMPT_CACHE_BENCH_DEFAULT_EXPERIMENT.",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    config = load_config(root)
    repo_url = config.get("PROMPT_CACHE_BENCH_REPO_URL", DEFAULT_REPO_URL).rstrip("/")
    experiment = args.experiment or config.get("PROMPT_CACHE_BENCH_DEFAULT_EXPERIMENT", DEFAULT_EXPERIMENT)
    experiment_dir = (root / experiment).resolve()

    if not (root / ".git").exists():
        print(f"error: {root} does not look like a git repository root", file=sys.stderr)
        return 2
    if not experiment_dir.exists():
        print(f"error: experiment directory does not exist: {experiment_dir}", file=sys.stderr)
        return 2

    checks = [
        ("secret scan", check_secrets(root)),
        ("experiment shape", check_experiment_shape(root, experiment_dir)),
        ("report basics", check_report_basics(root, experiment_dir, repo_url)),
        ("GitHub links", check_github_links(root, experiment_dir, repo_url)),
    ]

    failed = False
    for name, issues in checks:
        if issues:
            failed = True
            print(f"[FAIL] {name}")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print(f"[ OK ] {name}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
