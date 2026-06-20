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
            "Usage: python3 scripts/export_routing_report_pdf.py REPORT.md OUTPUT.pdf [--relative-images] [--embed-assets] [--html-only]"
        )
    flags = set(args[2:])
    allowed_flags = {"--relative-images", "--embed-assets", "--html-only"}
    unknown_flags = sorted(flags - allowed_flags)
    if unknown_flags:
        raise SystemExit("Unknown option: " + ", ".join(unknown_flags))
    relative_images = "--relative-images" in flags
    embed_assets = "--embed-assets" in flags
    html_only = "--html-only" in flags
    source = Path(args[0]).resolve()
    output = Path(args[1]).resolve()
    html_path = output.with_suffix(".html")
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
    brand = _brand_header(html_dir=html_dir)
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
    .report-brand {{ display: flex; align-items: center; justify-content: space-between; gap: 14pt; margin: 0 0 14pt; padding: 0 0 8pt; border-bottom: 1px solid #d1d5db; color: #6b7280; font-size: 8.5pt; }}
    .report-brand img {{ width: 88pt; max-width: 88pt; margin: 0; }}
    .report-brand span {{ text-align: right; }}
  </style>
</head>
<body>
{brand}
{body}
</body>
</html>
"""


def _brand_header(*, html_dir: Path) -> str:
    logo = _find_brand_logo(html_dir)
    if not logo:
        return ""
    return (
        '<div class="report-brand">'
        f'<img src="{html.escape(_data_uri(logo))}" alt="Infron">'
        "<span>prompt-cache-bench · reproducible inference benchmark artifact</span>"
        "</div>"
    )


def _find_brand_logo(start: Path) -> Path | None:
    for directory in [start, *start.parents]:
        candidate = directory / "assets" / "brand" / "infron-logo.png"
        if candidate.exists():
            return candidate
    return None


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
