from __future__ import annotations

import html
import base64
import mimetypes
import os
import re
import sys
from pathlib import Path
from subprocess import run


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) < 2:
        raise SystemExit(
            "Usage: python3 scripts/export_routing_report_pdf.py REPORT.md OUTPUT.pdf [--relative-images] [--embed-assets] [--html-only] [--html-output OUTPUT.html]"
        )
    flag_args = args[2:]
    html_output: Path | None = None
    if "--html-output" in flag_args:
        index = flag_args.index("--html-output")
        if index + 1 >= len(flag_args):
            raise SystemExit("--html-output requires an output HTML path")
        html_output = Path(flag_args[index + 1]).resolve()
        del flag_args[index : index + 2]
    flags = set(flag_args)
    allowed_flags = {"--relative-images", "--embed-assets", "--html-only"}
    unknown_flags = sorted(flags - allowed_flags)
    if unknown_flags:
        raise SystemExit("Unknown option: " + ", ".join(unknown_flags))
    relative_images = "--relative-images" in flags
    embed_assets = "--embed-assets" in flags
    html_only = "--html-only" in flags
    source = Path(args[0]).resolve()
    output = Path(args[1]).resolve()
    html_path = html_output or output.with_suffix(".html")
    markdown = source.read_text(encoding="utf-8")
    document = _render_html(
        markdown,
        base_dir=source.parent,
        html_dir=html_path.parent,
        relative_images=relative_images,
        embed_assets=embed_assets,
    )
    html_path.write_text(document, encoding="utf-8")
    if html_only:
        print({"html": str(html_path), "pdf": None})
        return 0
    run(["weasyprint", str(html_path), str(output)], check=True)
    print({"html": str(html_path), "pdf": str(output)})
    return 0


def _render_html(markdown: str, *, base_dir: Path, html_dir: Path, relative_images: bool, embed_assets: bool) -> str:
    body = _markdown_to_html(
        markdown,
        base_dir=base_dir,
        html_dir=html_dir,
        relative_images=relative_images,
        embed_assets=embed_assets,
    )
    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    @page {{ size: A4; margin: 18mm 14mm; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans CJK SC", "PingFang SC", sans-serif; color: #111827; font-size: 10.5pt; line-height: 1.55; }}
    h1 {{ font-size: 22pt; margin: 0 0 14pt; border-bottom: 2px solid #111827; padding-bottom: 8pt; }}
    h2 {{ font-size: 16pt; margin: 22pt 0 8pt; page-break-after: avoid; }}
    h3 {{ font-size: 12.5pt; margin: 16pt 0 8pt; page-break-after: avoid; }}
    p {{ margin: 7pt 0; }}
    code {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; background: #f3f4f6; padding: 1px 4px; border-radius: 3px; font-size: 9pt; }}
    table {{ width: 100%; border-collapse: collapse; margin: 8pt 0 13pt; font-size: 8.3pt; page-break-inside: auto; }}
    th, td {{ border: 1px solid #d1d5db; padding: 4pt 5pt; vertical-align: top; }}
    th {{ background: #f3f4f6; font-weight: 700; }}
    tr {{ page-break-inside: avoid; }}
    .provider-label {{ display: inline-block; width: 58pt; font-weight: 800; color: #374151; }}
    ul {{ margin: 7pt 0 10pt 15pt; padding: 0; }}
    li {{ margin: 3pt 0; }}
    img {{ display: block; max-width: 100%; margin: 8pt auto 16pt; }}
    pre.code {{ background: #0f172a; color: #e5e7eb; padding: 10pt; border-radius: 5pt; font-size: 8pt; line-height: 1.45; white-space: pre-wrap; overflow-wrap: anywhere; }}
    pre.code code {{ background: transparent; color: inherit; padding: 0; font-size: inherit; }}
    strong {{ font-weight: 800; }}

    .echarts-academic-panel {{ margin: 12pt 0 18pt; padding: 12pt; border: 1px solid #d8d3c7; background: #fffefa; page-break-inside: avoid; }}
    .echarts-academic-note {{ margin: 0 0 10pt; color: #4b5563; font-size: 9pt; }}
    .echarts-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12pt; }}
    .echarts-figure {{ border: 1px solid #e2ded4; background: #fffefa; padding: 10pt; page-break-inside: avoid; }}
    .echarts-figure.wide {{ grid-column: 1 / -1; }}
    .echarts-title {{ margin: 0 0 3pt; font-size: 10.5pt; font-weight: 800; color: #111827; }}
    .echarts-caption {{ margin: 0 0 7pt; font-size: 8.5pt; color: #5f6368; }}
    .echarts-chart {{ width: 100%; height: 300pt; }}
    .echarts-figure.wide .echarts-chart {{ height: 360pt; }}
    .route-detail-panel {{ margin-top: 10pt; }}
    .route-detail-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12pt; }}
    .route-mode-chart {{ height: 330pt; }}
    @media (max-width: 900px) {{ .route-detail-grid {{ grid-template-columns: 1fr; }} }}

    @media print {{ .echarts-academic-panel {{ break-inside: avoid; }} .echarts-chart {{ height: 260pt; }} .echarts-figure.wide .echarts-chart {{ height: 320pt; }} }}
    @media (max-width: 900px) {{ .echarts-grid {{ grid-template-columns: 1fr; }} .echarts-figure.wide {{ grid-column: auto; }} }}

    .impossible-panel {{ margin-top: 10pt; }}
    .impossible-chart {{ height: 520pt; }}

    .conclusion-overview {{ margin: 12pt 0 16pt; padding: 12pt; border: 1px solid #d8d3c7; background: #fffefa; page-break-inside: avoid; }}
    .conclusion-overview-title {{ margin: 0 0 4pt; font-size: 12pt; font-weight: 800; color: #111827; }}
    .conclusion-overview-note {{ margin: 0 0 10pt; color: #5f6368; font-size: 8.7pt; }}
    .metric-card-grid {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 7pt; margin-bottom: 10pt; }}
    .metric-card {{ border: 1px solid #e2ded4; background: #ffffff; padding: 8pt; min-height: 58pt; }}
    .metric-card strong {{ display: block; font-size: 8.8pt; margin-bottom: 4pt; color: #111827; }}
    .metric-card .winner-infron {{ color: #2468d8; font-weight: 800; }}
    .metric-card .winner-openrouter {{ color: #d9822b; font-weight: 800; }}
    .metric-card span {{ display: block; font-size: 7.6pt; line-height: 1.35; color: #5f6368; }}
    .winner-matrix {{ width: 100%; border-collapse: collapse; margin: 0; font-size: 7.9pt; }}
    .winner-matrix th, .winner-matrix td {{ border: 1px solid #d8d3c7; padding: 5pt 4pt; vertical-align: middle; text-align: center; }}
    .winner-matrix th {{ background: #f5f1e8; font-weight: 800; color: #111827; }}
    .winner-matrix td:first-child, .winner-matrix th:first-child {{ text-align: left; width: 15%; }}
    .winner-cell {{ background: #ffffff; }}
    .winner-cell.goal-cell.goal-infron {{ background: #eef6ff; box-shadow: inset 0 0 0 1.5px #93c5fd; }}
    .winner-cell.goal-cell.goal-openrouter {{ background: #fff4cc; box-shadow: inset 0 0 0 1.5px #d9a300; }}
    .winner-cell .name {{ display: block; font-weight: 900; }}
    .winner-cell .name.infron {{ color: #2468d8; }}
    .winner-cell .name.openrouter {{ color: #d9822b; }}
    .winner-cell .delta {{ display: block; margin-top: 2pt; color: #5f6368; font-size: 7.2pt; }}
    .route-conclusion-table {{ table-layout: fixed; width: 100%; }}
    .route-conclusion-table th:nth-child(1), .route-conclusion-table td:nth-child(1) {{ width: 18%; }}
    .route-conclusion-table th:nth-child(2), .route-conclusion-table td:nth-child(2) {{ width: 57%; }}
    .route-conclusion-table th:nth-child(3), .route-conclusion-table td:nth-child(3) {{ width: 25%; }}
    .route-conclusion-table td:nth-child(2) {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; line-height: 1.65; }}
    @media (max-width: 900px) {{ .metric-card-grid {{ grid-template-columns: 1fr; }} .winner-matrix {{ font-size: 7.2pt; }} }}

    .method-diagram {{ margin: 10pt 0 14pt; padding: 12pt; border: 1px solid #d8d3c7; background: #fffefa; page-break-inside: avoid; }}
    .architecture-diagram {{ margin: 10pt 0 14pt; padding: 12pt; border: 1px solid #d8d3c7; background: #fffefa; page-break-inside: avoid; }}
    .architecture-title {{ margin: 0 0 8pt; font-size: 10.5pt; font-weight: 800; color: #111827; }}
    .architecture-flow {{ display: grid; grid-template-columns: 1fr 24pt 1.1fr 24pt 1.2fr 24pt 1fr; gap: 8pt; align-items: center; }}
    .architecture-stack {{ display: grid; gap: 7pt; }}
    .architecture-node {{ min-height: 42pt; padding: 8pt 9pt; border: 1px solid #d8d3c7; background: #ffffff; display: flex; flex-direction: column; justify-content: center; }}
    .architecture-node.primary {{ border-color: #8bb6f1; background: #eef6ff; }}
    .architecture-node.policy {{ border-color: #efb26d; background: #fff7ed; }}
    .architecture-node.cache {{ border-color: #f2cc60; background: #fff9db; }}
    .architecture-node.provider {{ border-color: #93d8aa; background: #f0fdf4; }}
    .architecture-node.telemetry {{ border-color: #c4b5fd; background: #f5f3ff; }}
    .architecture-node strong {{ display: block; font-size: 9pt; color: #111827; }}
    .architecture-node span {{ display: block; margin-top: 2pt; font-size: 7.7pt; color: #5f6368; line-height: 1.35; }}
    .architecture-arrow {{ text-align: center; color: #6b7280; font-size: 15pt; font-weight: 800; }}
    .architecture-note-row {{ margin-top: 9pt; display: grid; grid-template-columns: repeat(3, 1fr); gap: 7pt; }}
    .architecture-note {{ padding: 7pt; border: 1px solid #e2ded4; background: #ffffff; font-size: 7.7pt; color: #374151; line-height: 1.35; }}
    @media (max-width: 900px) {{ .architecture-flow, .architecture-note-row {{ grid-template-columns: 1fr; }} .architecture-arrow {{ transform: rotate(90deg); }} }}

    .method-diagram-title {{ margin: 0 0 8pt; font-size: 10.5pt; font-weight: 800; color: #111827; }}
    .method-flow {{ display: grid; grid-template-columns: 1fr 28pt 1.15fr 28pt 1fr 28pt 1.05fr; align-items: center; gap: 8pt; }}
    .method-stack {{ display: grid; gap: 7pt; }}
    .method-node {{ min-height: 40pt; padding: 8pt 9pt; border: 1px solid #d8d3c7; background: #ffffff; display: flex; flex-direction: column; justify-content: center; }}
    .method-node.primary {{ border-color: #8bb6f1; background: #eef6ff; }}
    .method-node.accent {{ border-color: #efb26d; background: #fff7ed; }}
    .method-node.good {{ border-color: #93d8aa; background: #f0fdf4; }}
    .method-node.warn {{ border-color: #f2cc60; background: #fff9db; }}
    .method-node strong {{ display: block; font-size: 9.2pt; color: #111827; }}
    .method-node span {{ display: block; margin-top: 2pt; font-size: 7.8pt; color: #5f6368; line-height: 1.35; }}
    .method-arrow {{ text-align: center; color: #6b7280; font-size: 16pt; font-weight: 700; }}
    .method-filter {{ display: grid; grid-template-columns: 1fr 22pt 1fr 22pt 1fr; gap: 8pt; align-items: stretch; }}
    .method-rule-list {{ margin-top: 10pt; display: grid; grid-template-columns: repeat(4, 1fr); gap: 7pt; }}
    .method-rule {{ padding: 7pt; border: 1px solid #e2ded4; background: #ffffff; font-size: 7.8pt; color: #374151; }}
    @media (max-width: 900px) {{ .method-flow, .method-filter, .method-rule-list {{ grid-template-columns: 1fr; }} .method-arrow {{ transform: rotate(90deg); }} }}
  </style>
</head>
<body>
{body}
</body>
</html>
"""


def _markdown_to_html(markdown: str, *, base_dir: Path, html_dir: Path, relative_images: bool, embed_assets: bool) -> str:
    lines = markdown.splitlines()
    output: list[str] = []
    paragraph: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if line.startswith("```"):
            _flush_paragraph(output, paragraph)
            language = line.strip().strip("`")
            code_lines = []
            index += 1
            while index < len(lines) and not lines[index].startswith("```"):
                code_lines.append(lines[index])
                index += 1
            if index < len(lines):
                index += 1
            output.append(
                f'<pre class="code {html.escape(language)}"><code>{html.escape(chr(10).join(code_lines))}</code></pre>'
            )
            continue
        if not line.strip():
            _flush_paragraph(output, paragraph)
            index += 1
            continue
        if line.startswith("#"):
            _flush_paragraph(output, paragraph)
            level = len(line) - len(line.lstrip("#"))
            text = line[level:].strip()
            output.append(f"<h{level}>{_inline(text)}</h{level}>")
            index += 1
            continue
        if line.startswith("|") and index + 1 < len(lines) and _is_table_separator(lines[index + 1]):
            _flush_paragraph(output, paragraph)
            table_lines = [line]
            index += 2
            while index < len(lines) and lines[index].startswith("|"):
                table_lines.append(lines[index])
                index += 1
            output.append(_table_to_html(table_lines))
            continue
        if line.startswith("- "):
            _flush_paragraph(output, paragraph)
            items = []
            while index < len(lines) and lines[index].startswith("- "):
                items.append(lines[index][2:].strip())
                index += 1
            output.append("<ul>" + "".join(f"<li>{_inline(item)}</li>" for item in items) + "</ul>")
            continue
        image = re.fullmatch(r"!\[(.*?)\]\((.*?)\)", line.strip())
        if image:
            _flush_paragraph(output, paragraph)
            alt, src = image.groups()
            image_path = (base_dir / src).resolve()
            if embed_assets:
                image_src = _data_uri(image_path)
            elif relative_images:
                image_src = os.path.relpath(image_path, html_dir).replace(os.sep, "/")
            else:
                image_src = image_path.as_uri()
            output.append(f'<img src="{html.escape(image_src)}" alt="{html.escape(alt)}">')
            index += 1
            continue
        paragraph.append(line.strip())
        index += 1
    _flush_paragraph(output, paragraph)
    return "\n".join(output)


def _data_uri(path: Path) -> str:
    mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    payload = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{payload}"


def _flush_paragraph(output: list[str], paragraph: list[str]) -> None:
    if not paragraph:
        return
    output.append(f"<p>{_inline(' '.join(paragraph))}</p>")
    paragraph.clear()


def _is_table_separator(line: str) -> bool:
    cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def _table_to_html(lines: list[str]) -> str:
    rows = [[cell.strip() for cell in line.strip().strip("|").split("|")] for line in lines]
    header, body = rows[0], rows[1:]
    parts = ["<table><thead><tr>"]
    parts.extend(f"<th>{_inline(cell)}</th>" for cell in header)
    parts.append("</tr></thead><tbody>")
    for row in body:
        parts.append("<tr>")
        parts.extend(f"<td>{_inline(cell)}</td>" for cell in row)
        parts.append("</tr>")
    parts.append("</tbody></table>")
    return "".join(parts)


def _inline(text: str) -> str:
    escaped = html.escape(text)
    escaped = escaped.replace("&lt;br&gt;", "<br>")
    escaped = escaped.replace('&lt;span class=&quot;provider-label&quot;&gt;', '<span class="provider-label">')
    escaped = escaped.replace("&lt;/span&gt;", "</span>")
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    return escaped


if __name__ == "__main__":
    raise SystemExit(main())
