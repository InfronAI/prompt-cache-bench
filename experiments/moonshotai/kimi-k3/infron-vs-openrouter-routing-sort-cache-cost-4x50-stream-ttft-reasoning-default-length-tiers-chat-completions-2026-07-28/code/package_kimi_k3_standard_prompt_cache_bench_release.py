#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path


MODEL = "moonshotai/kimi-k3"
DATE = "2026-07-28"
RUN_NAME = "routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_default_length_tiers_chat_completions_20260728"
SOURCE_ROOT = Path("export/kimi_k3_all_experiments")
SOURCE_RUN = SOURCE_ROOT / RUN_NAME
BENCH_ROOT = Path("export/open-source/prompt-cache-bench")
EXP_REL = Path(
    "experiments/moonshotai/kimi-k3/"
    "infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-default-length-tiers-chat-completions-2026-07-28"
)
EXP = BENCH_ROOT / EXP_REL
SLUG = (
    "routing-cache-cost-streaming-performance-ab-study__kimi-k3__infron-vs-openrouter__"
    "4x50-stream-ttft-reasoning-default-length-tiers-chat-completions__2026-07-28"
)


def main() -> int:
    summary = json.loads((SOURCE_RUN / "summary.json").read_text(encoding="utf-8"))
    for name in ("reports", "data", "figures", "code", "metadata"):
        (EXP / name).mkdir(parents=True, exist_ok=True)
    copy_data()
    copy_reports()
    copy_code()
    write_readmes(summary)
    write_manifest()
    print(json.dumps({"experiment_dir": str(EXP), "report_slug": SLUG}, ensure_ascii=False, indent=2))
    return 0


def copy_data() -> None:
    data = EXP / "data"
    for path in SOURCE_RUN.iterdir():
        if path.is_file():
            shutil.copy2(path, data / path.name)
    (data / "README.md").write_text(
        "# Dataset\n\n"
        "This directory contains the Kimi K3 standard 4x50 prompt-cache-bench dataset.\n\n"
        "- `summary.json`: aggregate benchmark summary.\n"
        "- `benchmark_pairs.csv`: paired A/B dataset.\n"
        "- `benchmark_requests.jsonl`: request-level observations.\n"
        "- `records.json`: filtered structured records.\n",
        encoding="utf-8",
    )


def copy_reports() -> None:
    reports = EXP / "reports"
    mapping = {
        SOURCE_ROOT / f"{RUN_NAME}-standard-ab-report-zh.html": reports / f"{SLUG}.zh.html",
        SOURCE_ROOT / f"{RUN_NAME}-standard-ab-report-en.html": reports / f"{SLUG}.en.html",
        SOURCE_ROOT / f"{RUN_NAME}-standard-ab-report-zh.pdf": reports / f"{SLUG}.zh.pdf",
        SOURCE_ROOT / f"{RUN_NAME}-standard-ab-report-en.pdf": reports / f"{SLUG}.en.pdf",
    }
    for src, dst in mapping.items():
        shutil.copy2(src, dst)
    summary_zh = SOURCE_ROOT / f"{RUN_NAME}-summary-zh.md"
    summary_en = SOURCE_ROOT / f"{RUN_NAME}-summary-en.md"
    full_zh = SOURCE_ROOT / f"{RUN_NAME}-report-zh.md"
    if full_zh.exists():
        (reports / f"{SLUG}.zh.md").write_text(render_summary_md("zh"), encoding="utf-8")
    elif summary_zh.exists():
        shutil.copy2(summary_zh, reports / f"{SLUG}.zh.md")
    else:
        (reports / f"{SLUG}.zh.md").write_text(render_summary_md("zh"), encoding="utf-8")
    if summary_en.exists():
        shutil.copy2(summary_en, reports / f"{SLUG}.en.md")
    else:
        (reports / f"{SLUG}.en.md").write_text(render_summary_md("en"), encoding="utf-8")


def copy_code() -> None:
    code = EXP / "code"
    for src in [
        Path("scripts/rerun_routing_sort_cache_cost_ab.py"),
        Path("scripts/render_glm52_deepseek_style_report.py"),
        Path("scripts/package_kimi_k3_standard_prompt_cache_bench_release.py"),
        Path("scripts/export_routing_report_pdf.py"),
        Path("docs/ab-report-standard.md"),
        Path("tests/test_rerun_routing_sort_cache_cost_ab.py"),
    ]:
        if src.exists():
            shutil.copy2(src, code / src.name)


def write_readmes(summary: dict) -> None:
    (EXP / "README.md").write_text(
        f"""# {EXP.name}

Public artifacts for the `{MODEL}` Infron vs OpenRouter routing, prompt caching, cost, throughput, E2E latency, Streaming TTFT, default reasoning behavior, prompt length tier, and `/v1/chat/completions` A/B benchmark.

- Reports: [`reports/`](reports/)
- Data: [`data/`](data/)
- Figures: [`figures/`](figures/)
- Code snapshot: [`code/`](code/)
- Manifest: [`metadata/manifest.json`](metadata/manifest.json)

## Data Quality

- Groups: {summary["groups"]}
- Rounds per group: {summary["rounds_per_group"]}
- Request records: {line_count(EXP / "data" / "benchmark_requests.jsonl")}
- Paired rows: {max(0, line_count(EXP / "data" / "benchmark_pairs.csv") - 1)}
- Excluded records: {summary.get("excluded_records", {}).get("total", 0)}
""",
        encoding="utf-8",
    )
    (EXP / "reports" / "README.md").write_text(
        f"""# Reports

- [Chinese HTML]({SLUG}.zh.html)
- [English HTML]({SLUG}.en.html)
- [Chinese Markdown]({SLUG}.zh.md)
- [English Markdown]({SLUG}.en.md)
- [Chinese PDF]({SLUG}.zh.pdf)
- [English PDF]({SLUG}.en.pdf)
""",
        encoding="utf-8",
    )


def write_manifest() -> None:
    files = []
    for path in sorted(EXP.rglob("*")):
        if path.is_file() and path.relative_to(EXP).as_posix() != "metadata/manifest.json":
            files.append({"path": path.relative_to(EXP).as_posix(), "sha256": sha256(path), "size_bytes": path.stat().st_size})
    manifest = {"experiment_id": EXP.name, "model": MODEL, "updated_at": DATE, "files": files}
    (EXP / "metadata" / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def render_summary_md(language: str) -> str:
    summary = json.loads((SOURCE_RUN / "summary.json").read_text(encoding="utf-8"))
    if language == "zh":
        lines = [
            f"# Infron 与 OpenRouter A/B 实验报告：{MODEL}",
            "",
            "本报告是本次实验的短版摘要；完整标准中英文 HTML、PDF、summary JSON、配对 CSV 和请求级 JSONL 均保存在同一 export 目录。",
            "",
            f"- 模型：`{MODEL}`",
            "- API：`/v1/chat/completions`",
            "- 实验规模：4 组 x 50 轮 x 4 个 routing sort x 2 平台 x first/second replay",
            "- Reasoning / Thinking：平台默认行为，payload 未显式设置 `reasoning.effort`",
            f"- 有效配对：{pair_rows()}；请求级记录：{line_count(SOURCE_RUN / 'benchmark_requests.jsonl')}",
            f"- 排除记录：{summary.get('excluded_records', {}).get('total', 0)}",
            f"- 报告日期：{DATE}",
            "",
            "## 路由模式结果摘要",
            "",
            "| 路由模式 | 配对数 | 缓存胜出 | 成本胜出 | 吞吐胜出 | E2E 时延胜出 | TTFT 胜出 |",
            "| --- | ---: | --- | --- | --- | --- | --- |",
        ]
        for sort, label in [("throughput", "Throughput First"), ("price", "Price First"), ("latency", "Latency First"), ("ttft", "TTFT First")]:
            lines.append(summary_row(summary, sort, label, zh=True))
        lines.extend(artifact_lines(zh=True))
        return "\n".join(lines) + "\n"
    lines = [
        f"# Infron vs OpenRouter A/B Test Report: {MODEL}",
        "",
        "This report is the short summary for the experiment; the complete standard Chinese/English HTML, PDFs, summary JSON, paired CSV, and request-level JSONL are saved in the same export directory.",
        "",
        f"- Model: `{MODEL}`",
        "- API: `/v1/chat/completions`",
        "- Experiment size: 4 groups x 50 rounds x 4 routing sorts x 2 platforms x first/second replay",
        "- Reasoning / Thinking: platform defaults; payload does not explicitly set `reasoning.effort`",
        f"- Effective pairs: {pair_rows()}; request-level records: {line_count(SOURCE_RUN / 'benchmark_requests.jsonl')}",
        f"- Excluded records: {summary.get('excluded_records', {}).get('total', 0)}",
        f"- Report date: {DATE}",
        "",
        "## Routing Mode Summary",
        "",
        "| Routing mode | Pairs | Cache winner | Cost winner | Throughput winner | E2E latency winner | TTFT winner |",
        "| --- | ---: | --- | --- | --- | --- | --- |",
    ]
    for sort, label in [("throughput", "Throughput First"), ("price", "Price First"), ("latency", "Latency First"), ("ttft", "TTFT First")]:
        lines.append(summary_row(summary, sort, label, zh=False))
    lines.extend(artifact_lines(zh=False))
    return "\n".join(lines) + "\n"


def summary_row(summary: dict, sort: str, label: str, *, zh: bool) -> str:
    a = summary["results"][sort]
    i = a["infron"]["aggregate"]
    o = a["openrouter"]["aggregate"]
    pairs = min(int(i["rounds"]), int(o["rounds"]))
    cache = winner_text(i["token_cache_hit_rate"], o["token_cache_hit_rate"], higher=True, fmt=lambda v: f"{v*100:.2f}%")
    cost = winner_text(i["total_actual_cost_usd"], o["total_actual_cost_usd"], higher=False, fmt=lambda v: f"${v:.6f}")
    throughput = winner_text(i["avg_throughput_output_tokens_per_second"], o["avg_throughput_output_tokens_per_second"], higher=True, fmt=lambda v: f"{v:.3f} tok/s")
    latency = winner_text(i["avg_request_latency_ms"], o["avg_request_latency_ms"], higher=False, fmt=lambda v: f"{v:.2f} ms")
    ttft = winner_text(i["avg_ttft_ms"], o["avg_ttft_ms"], higher=False, fmt=lambda v: f"{v:.2f} ms")
    return f"| {label} | {pairs} | {cache} | {cost} | {throughput} | {latency} | {ttft} |"


def winner_text(infron: float, openrouter: float, *, higher: bool, fmt) -> str:
    if infron == openrouter:
        winner = "Tie"
    elif (infron > openrouter) == higher:
        winner = "Infron"
    else:
        winner = "OpenRouter"
    return f"{winner} ({fmt(infron)} / {fmt(openrouter)})"


def artifact_lines(*, zh: bool) -> list[str]:
    if zh:
        return [
            "",
            "## 数据与报告工件",
            "",
            "| 工件 | 路径 |",
            "| --- | --- |",
            f"| 中文摘要 Markdown | `{SLUG}.zh.md` |",
            f"| English summary Markdown | `{SLUG}.en.md` |",
            f"| 标准中文 HTML | `{SLUG}.zh.html` |",
            f"| Standard English HTML | `{SLUG}.en.html` |",
            "| Summary JSON | `data/summary.json` |",
            "| Paired CSV | `data/benchmark_pairs.csv` |",
            "| Request JSONL | `data/benchmark_requests.jsonl` |",
        ]
    return [
        "",
        "## Data And Report Artifacts",
        "",
        "| Artifact | Path |",
        "| --- | --- |",
        f"| Chinese summary Markdown | `{SLUG}.zh.md` |",
        f"| English summary Markdown | `{SLUG}.en.md` |",
        f"| Standard Chinese HTML | `{SLUG}.zh.html` |",
        f"| Standard English HTML | `{SLUG}.en.html` |",
        "| Summary JSON | `data/summary.json` |",
        "| Paired CSV | `data/benchmark_pairs.csv` |",
        "| Request JSONL | `data/benchmark_requests.jsonl` |",
    ]


def pair_rows() -> int:
    return max(0, line_count(SOURCE_RUN / "benchmark_pairs.csv") - 1)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def line_count(path: Path) -> int:
    with path.open(encoding="utf-8") as handle:
        return sum(1 for _ in handle)


if __name__ == "__main__":
    raise SystemExit(main())
