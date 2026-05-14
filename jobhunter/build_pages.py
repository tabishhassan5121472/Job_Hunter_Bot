#!/usr/bin/env python3
"""
Build a static HTML site from the markdown reports in reports/.
Output goes to ./_site/ which the GitHub Actions workflow uploads
as a Pages artifact and deploys.

No external markdown library — we render manually to keep deps tiny.
"""
from __future__ import annotations
import html
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPORTS = HERE / "reports"
OUT = HERE / "_site"

CSS = """
:root {
  color-scheme: dark;
  --bg:#0f1115; --surface:#181b22; --border:#2a2f3a;
  --text:#e6e9ef; --dim:#9aa3b2; --accent:#6aa6ff;
}
* { box-sizing: border-box; }
body {
  margin:0; background:var(--bg); color:var(--text);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
  line-height:1.55;
}
.wrap { max-width: 860px; margin: 0 auto; padding: 32px 20px 64px; }
h1 { font-size: 28px; margin: 0 0 4px; letter-spacing: -0.02em; }
.sub { color: var(--dim); font-size: 14px; margin-bottom: 28px; }
h2 { font-size: 18px; margin: 28px 0 8px; }
h3 { font-size: 16px; margin: 18px 0 6px; }
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
ul.runs { list-style: none; padding: 0; margin: 0; }
ul.runs li {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 14px 16px;
  margin-bottom: 8px;
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}
ul.runs .meta { color: var(--dim); font-size: 12.5px; }
.report-body { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 22px; }
.report-body pre { background: #0c0d11; padding: 12px; border-radius: 6px; overflow: auto; }
.back { display: inline-block; margin-bottom: 16px; font-size: 13px; }
hr { border: 0; border-top: 1px solid var(--border); margin: 24px 0; }
"""

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>{title}</title>
<style>{css}</style>
</head>
<body>
<div class="wrap">{body}</div>
</body>
</html>
"""


def render_markdown(md: str) -> str:
    """Minimal markdown → HTML converter.
    Handles: # headings, **bold**, *italic*, [text](url), code blocks ```, paragraphs."""
    lines = md.splitlines()
    out: list[str] = []
    in_code = False
    para: list[str] = []

    def flush_para():
        if para:
            out.append("<p>" + " ".join(para) + "</p>")
            para.clear()

    def inline(s: str) -> str:
        # Escape HTML first, then re-apply markdown
        s = html.escape(s)
        s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"\*(.+?)\*", r"<em>\1</em>", s)
        s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
        s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)",
                   r'<a href="\2" target="_blank" rel="noopener">\1</a>', s)
        # Auto-link bare URLs
        s = re.sub(r"(?<!\")(https?://[^\s<)]+)",
                   r'<a href="\1" target="_blank" rel="noopener">\1</a>', s)
        return s

    for raw in lines:
        line = raw.rstrip()
        if line.startswith("```"):
            flush_para()
            if in_code:
                out.append("</pre>")
                in_code = False
            else:
                out.append("<pre>")
                in_code = True
            continue
        if in_code:
            out.append(html.escape(raw))
            continue
        if not line.strip():
            flush_para()
            continue
        if line.startswith("# "):
            flush_para()
            out.append(f"<h1>{inline(line[2:].strip())}</h1>")
            continue
        if line.startswith("## "):
            flush_para()
            out.append(f"<h2>{inline(line[3:].strip())}</h2>")
            continue
        if line.startswith("### "):
            flush_para()
            out.append(f"<h3>{inline(line[4:].strip())}</h3>")
            continue
        if line.startswith("- ") or line.startswith("* "):
            flush_para()
            out.append(f"<div>• {inline(line[2:].strip())}</div>")
            continue
        para.append(inline(line))
    flush_para()
    if in_code:
        out.append("</pre>")
    return "\n".join(out)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    reports = []
    if REPORTS.exists():
        reports = sorted(
            (p for p in REPORTS.glob("*.md") if p.is_file()),
            key=lambda p: p.name,
            reverse=True,
        )

    # Per-report pages
    for md_path in reports:
        slug = md_path.stem
        body = (
            f'<a href="./" class="back">← All runs</a>'
            f'<div class="report-body">{render_markdown(md_path.read_text(encoding="utf-8"))}</div>'
        )
        (OUT / f"{slug}.html").write_text(
            PAGE.format(title=f"JobHunter · {slug}", css=CSS, body=body),
            encoding="utf-8",
        )

    # Index page
    items = []
    for md_path in reports:
        slug = md_path.stem
        size_kb = md_path.stat().st_size // 1024
        items.append(
            f'<li><a href="./{slug}.html">{html.escape(slug)}</a>'
            f'<span class="meta">{size_kb} KB</span></li>'
        )

    body = (
        "<h1>JobHunter</h1>"
        f'<p class="sub">{len(reports)} run(s) · newest first · '
        "auto-built from the latest GitHub Actions run.</p>"
        + ("<ul class='runs'>" + "".join(items) + "</ul>"
           if items else "<p>No reports yet — wait for the first scheduled run.</p>")
    )
    (OUT / "index.html").write_text(
        PAGE.format(title="JobHunter", css=CSS, body=body),
        encoding="utf-8",
    )

    print(f"[build_pages] wrote {len(reports) + 1} files to {OUT}")


if __name__ == "__main__":
    main()
