#!/usr/bin/env python3
"""Prepare a bilingual benchmark report release.

This script codifies the local-to-GitHub release workflow:

1. Optionally copy finalized local artifacts into the open-source experiment dir.
2. Normalize report favicons to the public Infron CDN icon used by GitHub Pages.
3. Check Chinese/English report language boundaries.
4. Update manifest checksums and sizes.
5. Verify README/index links for GitHub Pages and GitHub source paths.
6. Run the repository release validator.

It intentionally uses only the Python standard library.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path


DEFAULT_REPO_URL = "https://github.com/InfronAI/prompt-cache-bench"
DEFAULT_PAGES_BASE_URL = "https://infronai.github.io/prompt-cache-bench"
DEFAULT_EXPERIMENT = (
    "experiments/deepseek/deepseek-v4-flash/"
    "infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-none-2026-06-29"
)
INFRON_ICON_URL = "https://framerusercontent.com/images/jYZGKXX6mcMkU1qAXZQeevZRY.png"

TEXT_EXTENSIONS = {
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
    ".yaml",
    ".yml",
}

SECRET_PATTERNS = [
    re.compile(r"ghp_[A-Za-z0-9_]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]+"),
    re.compile(r"GITHUB_TOKEN\s*=\s*[^\s]+"),
    re.compile(r"CLICKHOUSE_PASSWORD\s*=\s*[^\s]+"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"Bearer\s+[A-Za-z0-9._-]{20,}"),
    re.compile(r"(OPENAI_API_KEY|INFRON_API_KEY|OPENROUTER_API_KEY)\s*=\s*(?!your_)[^\s]+"),
]

ALLOWED_SECRET_MATCHES = {
    ".env.example",
    "README.md",
    "docs/report-release-runbook.md",
}


class VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.skip_depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:  # type: ignore[no-untyped-def]
        if tag in {"script", "style"}:
            self.skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self.skip_depth:
            self.skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self.skip_depth:
            self.parts.append(data)

    @property
    def text(self) -> str:
        return " ".join(self.parts)


def load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def load_config(root: Path) -> dict[str, str]:
    config = load_env_file(root / ".env.example")
    config.update(load_env_file(root / ".env"))
    for key, value in os.environ.items():
        if key.startswith("PROMPT_CACHE_BENCH_"):
            config[key] = value
    return config


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def iter_text_files(root: Path):
    for path in root.rglob("*"):
        if ".git" in path.parts or not path.is_file():
            continue
        if path.suffix in TEXT_EXTENSIONS or path.name in {"AGENTS.md", "LICENSE"}:
            yield path


def copy_local_artifacts(source: Path, experiment_dir: Path) -> list[str]:
    copied: list[str] = []
    for name in ["README.md", "reports", "data", "figures", "code", "metadata"]:
        src = source / name
        dst = experiment_dir / name
        if not src.exists():
            continue
        if src.is_dir():
            dst.mkdir(parents=True, exist_ok=True)
            for item in src.rglob("*"):
                if item.is_file():
                    target = dst / item.relative_to(src)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, target)
                    copied.append(rel(target, experiment_dir))
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            copied.append(rel(dst, experiment_dir))
    return copied


def normalize_html_icons(experiment_dir: Path) -> list[str]:
    icon = (
        f'\n  <link href="{INFRON_ICON_URL}" rel="icon" media="(prefers-color-scheme: light)">'
        f'\n  <link href="{INFRON_ICON_URL}" rel="icon" media="(prefers-color-scheme: dark)">'
        f'\n  <link rel="apple-touch-icon" href="{INFRON_ICON_URL}">'
    )
    changed: list[str] = []
    for path in sorted((experiment_dir / "reports").glob("*.html")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        original = text
        text = re.sub(
            r'\s*<link rel="icon" type="image/png" href="data:image/png;base64,[^"]+">',
            "",
            text,
            count=1,
        )
        text = re.sub(
            rf'\n\s*<link href="{re.escape(INFRON_ICON_URL)}" rel="icon" media="\(\s*prefers-color-scheme:\s*light\s*\)">',
            "",
            text,
        )
        text = re.sub(
            rf'\n\s*<link href="{re.escape(INFRON_ICON_URL)}" rel="icon" media="\(\s*prefers-color-scheme:\s*dark\s*\)">',
            "",
            text,
        )
        text = re.sub(
            rf'\n\s*<link rel="apple-touch-icon" href="{re.escape(INFRON_ICON_URL)}">',
            "",
            text,
        )
        if '<meta charset="utf-8">' in text:
            text = text.replace('<meta charset="utf-8">', '<meta charset="utf-8">' + icon, 1)
        elif '<meta charset="UTF-8">' in text:
            text = text.replace('<meta charset="UTF-8">', '<meta charset="UTF-8">' + icon, 1)
        elif "<head>" in text:
            text = text.replace("<head>", "<head>" + icon, 1)
        else:
            raise RuntimeError(f"{path}: cannot find <head> or charset for favicon injection")
        if text != original:
            path.write_text(text, encoding="utf-8")
            changed.append(rel(path, experiment_dir))
    return changed


def visible_html_text(path: Path) -> str:
    parser = VisibleTextParser()
    parser.feed(path.read_text(encoding="utf-8", errors="ignore"))
    return parser.text


def check_languages(experiment_dir: Path) -> list[str]:
    issues: list[str] = []
    for path in sorted((experiment_dir / "reports").glob("*")):
        if path.suffix not in {".html", ".md"}:
            continue
        text = visible_html_text(path) if path.suffix == ".html" else path.read_text(encoding="utf-8", errors="ignore")
        cjk_count = len(re.findall(r"[\u4e00-\u9fff]", text))
        if path.name.endswith(".en.html") or path.name.endswith(".en.md"):
            if cjk_count:
                issues.append(f"{rel(path, experiment_dir)}: English report contains {cjk_count} CJK characters")
        if path.name.endswith(".zh.html") or path.name.endswith(".zh.md"):
            if cjk_count < 50:
                issues.append(f"{rel(path, experiment_dir)}: Chinese report appears to contain too little Chinese text")
            suspicious = re.findall(
                r"\b(Abstract|Conclusion Overview|Research Background|Experimental Design|Figure\s+\d|Table\s+\d)\b",
                text,
            )
            if suspicious:
                issues.append(
                    f"{rel(path, experiment_dir)}: Chinese report contains English section labels: "
                    + ", ".join(sorted(set(suspicious))[:8])
                )
    return issues


def check_report_pairing(experiment_dir: Path) -> list[str]:
    reports = experiment_dir / "reports"
    issues: list[str] = []
    zh_html = sorted(reports.glob("*.zh.html"))
    en_html = sorted(reports.glob("*.en.html"))
    zh_md = sorted(reports.glob("*.zh.md"))
    en_md = sorted(reports.glob("*.en.md"))
    if not zh_html or not en_html:
        issues.append("reports/: missing Chinese or English HTML report")
    if not zh_md or not en_md:
        issues.append("reports/: missing Chinese or English Markdown report")
    if zh_html and en_html:
        zh = zh_html[0].read_text(encoding="utf-8", errors="ignore")
        en = en_html[0].read_text(encoding="utf-8", errors="ignore")
        for marker in ["echarts", "report-brand", "Reproducibility", "GitHub"]:
            if marker == "Reproducibility":
                zh_has = "可复现性" in zh or "Reproducibility" in zh
                en_has = "Reproducibility" in en
            else:
                zh_has = marker in zh
                en_has = marker in en
            if zh_has != en_has:
                issues.append(f"reports/: HTML report structure mismatch around `{marker}`")
    return issues


def update_manifest(experiment_dir: Path) -> None:
    manifest = experiment_dir / "metadata" / "manifest.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    if manifest.exists():
        data = json.loads(manifest.read_text(encoding="utf-8"))
    else:
        data = {
            "experiment_id": experiment_dir.name,
            "model": None,
            "updated_at": None,
            "files": [],
        }
    existing_by_path = {item.get("path"): item for item in data.get("files", []) if item.get("path")}
    files: list[dict[str, object]] = []
    for subdir in ["reports", "data", "code", "figures"]:
        directory = experiment_dir / subdir
        if not directory.exists():
            continue
        for path in sorted(directory.rglob("*")):
            if not path.is_file():
                continue
            relative = rel(path, experiment_dir)
            item = dict(existing_by_path.get(relative, {"path": relative}))
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            item["sha256"] = digest
            if "bytes" in item and "size_bytes" not in item:
                item["bytes"] = path.stat().st_size
            else:
                item["size_bytes"] = path.stat().st_size
            files.append(item)
    data["files"] = files
    manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def check_homepage_and_readme(root: Path, experiment: str, repo_url: str, pages_base: str) -> list[str]:
    issues: list[str] = []
    experiment_dir = root / experiment
    reports = experiment_dir / "reports"
    expected = []
    for path in sorted(reports.glob("*.*")):
        if path.name.endswith(".zh.html") or path.name.endswith(".en.html"):
            expected.append(f"{pages_base.rstrip('/')}/{experiment}/reports/{path.name}")
        if path.name.endswith(".zh.md") or path.name.endswith(".en.md"):
            expected.append(f"{repo_url.rstrip('/')}/blob/main/{experiment}/reports/{path.name}")
    expected.append(f"{repo_url.rstrip('/')}/tree/main/{experiment}/data")
    for page_name in ["README.md", "index.html"]:
        page = root / page_name
        if not page.exists():
            issues.append(f"{page_name}: file is missing")
            continue
        text = page.read_text(encoding="utf-8", errors="ignore")
        missing = [url for url in expected if url not in text and not (page_name == "README.md" and url.startswith(repo_url))]
        if missing:
            issues.append(f"{page_name}: missing expected release links: {', '.join(missing[:4])}")
    return issues


def check_secrets(root: Path) -> list[str]:
    issues: list[str] = []
    for path in iter_text_files(root):
        text = path.read_text(encoding="utf-8", errors="ignore")
        relpath = rel(path, root)
        for pattern in SECRET_PATTERNS:
            for match in pattern.finditer(text):
                if relpath in ALLOWED_SECRET_MATCHES:
                    continue
                line = text.count("\n", 0, match.start()) + 1
                issues.append(f"{relpath}:{line}: possible secret matched `{pattern.pattern}`")
    return issues


def run_validator(root: Path, experiment: str) -> int:
    return subprocess.call(
        [sys.executable, "scripts/validate_release.py", "--experiment", experiment],
        cwd=root,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync and validate bilingual benchmark report release artifacts.")
    parser.add_argument("--root", default=".", help="Open-source repository root. Defaults to current directory.")
    parser.add_argument("--experiment", default=None, help="Experiment path under the repository root.")
    parser.add_argument(
        "--local-experiment-dir",
        default=None,
        help="Optional finalized local experiment directory to copy from before validation.",
    )
    parser.add_argument("--copy-local", action="store_true", help="Copy reports/data/figures/code/metadata from --local-experiment-dir.")
    parser.add_argument("--skip-validator", action="store_true", help="Skip scripts/validate_release.py.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    config = load_config(root)
    experiment = args.experiment or config.get("PROMPT_CACHE_BENCH_DEFAULT_EXPERIMENT", DEFAULT_EXPERIMENT)
    repo_url = config.get("PROMPT_CACHE_BENCH_REPO_URL", DEFAULT_REPO_URL)
    pages_base = config.get("PROMPT_CACHE_BENCH_PAGES_BASE_URL", DEFAULT_PAGES_BASE_URL)
    experiment_dir = root / experiment

    if not (root / ".git").exists():
        print(f"error: {root} is not a git repository root", file=sys.stderr)
        return 2

    print(f"[sync] repository root: {root}")
    print(f"[sync] target experiment: {experiment}")

    if args.copy_local:
        if not args.local_experiment_dir:
            print("error: --copy-local requires --local-experiment-dir", file=sys.stderr)
            return 2
        copied = copy_local_artifacts(Path(args.local_experiment_dir).resolve(), experiment_dir)
        print(f"[sync] copied {len(copied)} files from local experiment directory")

    if not experiment_dir.exists():
        print(f"error: experiment directory does not exist: {experiment_dir}", file=sys.stderr)
        return 2

    changed_icons = normalize_html_icons(experiment_dir)
    print(f"[sync] normalized HTML icons: {len(changed_icons)} files")

    update_manifest(experiment_dir)
    print("[sync] updated manifest checksums")

    checks = {
        "language checks": check_languages(experiment_dir),
        "report pairing": check_report_pairing(experiment_dir),
        "homepage/readme links": check_homepage_and_readme(root, experiment, repo_url, pages_base),
        "secret scan": check_secrets(root),
    }

    failed = False
    for name, issues in checks.items():
        if issues:
            failed = True
            print(f"[FAIL] {name}")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print(f"[ OK ] {name}")

    if not args.skip_validator:
        if run_validator(root, experiment) != 0:
            failed = True

    print("\nNext steps:")
    print("  git status --short")
    print("  git diff --stat")
    print("  git add <intended files>")
    print('  git commit -m "Update benchmark report release"')
    print("  git push origin main")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
