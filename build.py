#!/usr/bin/env python3
"""
Preprocess plain text files into styled HTML files.

- Source files: src/*.txt
- Output files: build/*.html

Usage examples:
  python build.py            # build all src/*.txt once
  python build.py content    # build src/content.txt -> build/content.html
  python build.py --watch    # watch src/ and rebuild on changes
"""

import argparse
import html
import os
from pathlib import Path
from typing import List

# Optional: only needed for --watch
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False


# ---------------------------------------------------------------------------
# High-level build API
# ---------------------------------------------------------------------------

def build_all_sources(src_dir: Path, build_dir: Path, css_path: str, js_path: str) -> None:
    """Build HTML for all .txt files under src_dir."""
    txt_files = sorted(src_dir.glob("*.txt"))
    for txt_file in txt_files:
        build_single_source(txt_file, src_dir, build_dir, css_path, js_path)


def build_single_source(
    txt_path: Path,
    src_dir: Path,
    build_dir: Path,
    css_path: str,
    js_path: str,
) -> Path:
    """
    Build a single .txt file into an .html file under build_dir.

    Returns the path to the generated HTML file.
    """
    if not txt_path.exists():
        raise FileNotFoundError(f"Text file not found: {txt_path}")

    # Derive output path
    rel_name = txt_path.stem  # "content" for "content.txt"
    out_path = build_dir / f"{rel_name}.html"

    print(f"[build] {txt_path} -> {out_path}")
    raw_text = read_text_file(txt_path)
    paragraphs = build_paragraph_model(raw_text)
    body_html = render_paragraphs_to_html(paragraphs)
    title = derive_title_from_paragraphs(paragraphs, default=rel_name)
    full_html = wrap_in_document_shell(body_html, title, css_path, js_path, rel_name)

    write_text_file(out_path, full_html)
    return out_path


# ---------------------------------------------------------------------------
# File IO helpers
# ---------------------------------------------------------------------------

def read_text_file(path: Path) -> str:
    """Read a UTF-8 text file and return its content as a string."""
    return path.read_text(encoding="utf-8")


def write_text_file(path: Path, content: str) -> None:
    """Write a UTF-8 text file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Text → paragraph model
# ---------------------------------------------------------------------------

class Paragraph:
    """Represents a single paragraph or heading in the document."""

    def __init__(self, kind: str, text: str) -> None:
        """
        kind: "paragraph" or "heading1" (more kinds can be added later)
        text: raw text content (unescaped)
        """
        self.kind = kind
        self.text = text

    def __repr__(self) -> str:
        return f"Paragraph(kind={self.kind!r}, text={self.text!r})"


def split_into_blocks(raw_text: str) -> List[str]:
    """
    Split text into logical blocks:

    - Normalise line endings.
    - Blank lines separate blocks.
    - Each block is a list of non-blank lines joined by spaces.
    """
    normalised = raw_text.replace("\r\n", "\n")
    lines = normalised.split("\n")

    blocks: List[str] = []
    buffer: List[str] = []

    def flush_buffer() -> None:
        nonlocal buffer
        if not buffer:
            return
        combined = " ".join(line.strip() for line in buffer).strip()
        buffer = []
        if combined:
            blocks.append(combined)

    for line in lines:
        if line.strip() == "":
            flush_buffer()
        else:
            buffer.append(line)

    flush_buffer()
    return blocks


def interpret_block(block: str) -> Paragraph:
    """
    Interpret a block of text and create a Paragraph object.

    Rules:
      - If block begins with "H1" and whitespace, create heading1.
      - Otherwise, create a normal paragraph.
    """
    stripped = block.lstrip()

    if stripped.startswith("H1 "):
        # "H1 X..." → heading1 with text "X..."
        heading_text = stripped[3:].strip()
        return Paragraph(kind="heading1", text=heading_text)

    # Default: simple paragraph
    return Paragraph(kind="paragraph", text=block)


def build_paragraph_model(raw_text: str) -> List[Paragraph]:
    """Convert raw text into a list of Paragraph objects."""
    blocks = split_into_blocks(raw_text)
    paragraphs = [interpret_block(block) for block in blocks]
    return paragraphs


# ---------------------------------------------------------------------------
# Paragraph model → HTML
# ---------------------------------------------------------------------------

def html_escape(text: str) -> str:
    """HTML-escape a string."""
    return html.escape(text, quote=True)


def render_paragraph(paragraph: Paragraph) -> str:
    """Render a single Paragraph object as HTML."""
    escaped = html_escape(paragraph.text)

    if paragraph.kind == "heading1":
        return f"<h1>{escaped}</h1>"

    # Default paragraph
    return f"<p>{escaped}</p>"


def render_paragraphs_to_html(paragraphs: List[Paragraph]) -> str:
    """
    Render a list of Paragraphs to HTML suitable for inserting into <main>.
    """
    rendered = [render_paragraph(p) for p in paragraphs]
    return "\n".join(rendered)


# ---------------------------------------------------------------------------
# Full document shell
# ---------------------------------------------------------------------------

def derive_title_from_paragraphs(paragraphs: List[Paragraph], default: str) -> str:
    """
    Use the first heading1 as the HTML <title> if present, otherwise a default.
    """
    for p in paragraphs:
        if p.kind == "heading1" and p.text.strip():
            return p.text.strip()
    return default


def wrap_in_document_shell(
    body_html: str,
    title: str,
    css_href: str,
    js_href: str,
    source_basename: str,
) -> str:
    """
    Wrap the rendered body HTML in a full HTML document.

    css_href: path/URL to the shared CSS file (e.g. "../style.css" or "/style.css")
    js_href:  path/URL to the shared dev reload JS file (e.g. "../dev-reload.js")
    source_basename: e.g. "content" (used in a small header at top of page)
    """
    escaped_title = html_escape(title)
    escaped_source = html_escape(source_basename)

    # You can adjust these hrefs and the structure as needed later.
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{escaped_title}</title>
  <link rel="stylesheet" href="{css_href}">
  <script src="{js_href}" defer></script>
</head>
<body>
  <header id="doc-header">
    <div>Source: {escaped_source}.txt</div>
  </header>
  <main id="content">
{body_html}
  </main>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Watch mode (optional)
# ---------------------------------------------------------------------------

class TxtChangeHandler(FileSystemEventHandler):
    """Watchdog handler that rebuilds on any .txt change."""

    def __init__(self, src_dir: Path, build_dir: Path, css_path: str, js_path: str) -> None:
        super().__init__()
        self.src_dir = src_dir
        self.build_dir = build_dir
        self.css_path = css_path
        self.js_path = js_path

    def on_modified(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix.lower() == ".txt":
            # Rebuild just the changed file
            try:
                build_single_source(path, self.src_dir, self.build_dir, self.css_path, self.js_path)
            except Exception as exc:
                print(f"[watch] Error rebuilding {path}: {exc}")


def watch_sources(src_dir: Path, build_dir: Path, css_path: str, js_path: str) -> None:
    """Watch src_dir for changes to .txt files and rebuild on modification."""
    if not WATCHDOG_AVAILABLE:
        raise RuntimeError(
            "watchdog is not installed. Install it with `pip install watchdog`."
        )

    print(f"[watch] Watching {src_dir} for changes...")
    event_handler = TxtChangeHandler(src_dir, build_dir, css_path, js_path)
    observer = Observer()
    observer.schedule(event_handler, str(src_dir), recursive=False)
    observer.start()

    try:
        while True:
            # Just keep running
            observer.join(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build HTML from plain text files.")
    parser.add_argument(
        "name",
        nargs="?",
        help=(
            "Optional base name of a single text file to build, without .txt "
            "(e.g. 'content' builds src/content.txt). "
            "If omitted, all src/*.txt are built."
        ),
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Watch src/ for changes and rebuild automatically.",
    )
    parser.add_argument(
        "--src-dir",
        default="src",
        help="Source directory containing .txt files (default: src).",
    )
    parser.add_argument(
        "--build-dir",
        default="build",
        help="Output directory for .html files (default: build).",
    )
    parser.add_argument(
        "--css",
        default="../style.css",
        help="Path/URL to CSS file as used in generated HTML (default: ../style.css).",
    )
    parser.add_argument(
        "--dev-js",
        default="../dev-reload.js",
        help="Path/URL to dev reload JS in generated HTML (default: ../dev-reload.js).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    src_dir = Path(args.src_dir).resolve()
    build_dir = Path(args.build_dir).resolve()

    if args.name:
        txt_path = src_dir / f"{args.name}.txt"
        build_single_source(txt_path, src_dir, build_dir, args.css, args.dev_js)
    else:
        build_all_sources(src_dir, build_dir, args.css, args.dev_js)

    if args.watch:
        watch_sources(src_dir, build_dir, args.css, args.dev_js)


if __name__ == "__main__":
    main()

