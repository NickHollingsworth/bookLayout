from __future__ import annotations

import re
from pathlib import Path

from .io_utils import read_text_file, write_text_file, list_md_files
from .markdown_to_html import render_markdown_to_html
from .template import wrap_in_document_shell


def derive_title_from_markdown(markdown_text: str, default: str) -> str:
    """
    Use the first ATX heading as the HTML <title>, if present.
    """
    for line in markdown_text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("#"):
            continue

        m = re.match(r"^#+\s+(.*)$", stripped)
        if not m:
            continue

        heading = m.group(1).strip()
        heading = re.sub(r"\s+#+\s*$", "", heading).strip()
        if heading:
            return heading

    return default


def render_one(
    md_path: Path,
    build_dir: Path,
    css_href: str,
    js_href: str,
    template_path: Path,
) -> Path:
    """
    Render a single Markdown file to an HTML file under build_dir.
    """
    if not md_path.exists():
        raise FileNotFoundError(f"Markdown file not found: {md_path}")

    rel_name = md_path.stem
    out_path = build_dir / f"{rel_name}.html"

    print(f"[build] {md_path} -> {out_path}")

    raw_text = read_text_file(md_path)
    body_html = render_markdown_to_html(raw_text)
    title = derive_title_from_markdown(raw_text, default=rel_name)

    full_html = wrap_in_document_shell(
        body_html=body_html,
        title=title,
        css_href=css_href,
        js_href=js_href,
        template_path=template_path,
    )

    write_text_file(out_path, full_html)
    return out_path


def render_all(
    preprocess_dir: Path,
    build_dir: Path,
    css_href: str,
    js_href: str,
    template_path: Path,
) -> int:
    """
    Render all *.md files in preprocess_dir to *.html in build_dir.
    """
    md_files = list_md_files(preprocess_dir)
    if not md_files:
        print(f"[build] No .md files found in: {preprocess_dir}")
        return 0

    for md_path in md_files:
        render_one(md_path, build_dir, css_href, js_href, template_path)

    return 0

