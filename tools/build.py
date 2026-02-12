#!/usr/bin/env python3
"""
Preprocess plain text (GitHub-flavoured Markdown) into HTML.

- Source files:  src/*.md
- HTML template: tools/templates/page.html
- CSS styling :  ../../tools/style/style.html
- js runtime scripts:  ../../tools/scripts/reload.js
- Output files:  tmp/step-2-resulting-html/*.html

Usage examples:
  python build.py
      Build all src/*.md once -> tmp/step-2-resulting-html/*.html

  python build.py content
      Build src/content.md -> tmp/step-2-resulting-html/content.html

  python build.py --watch
      Watch src/ for .md changes and rebuild automatically

Required packages (in your venv):
  pip install markdown-it-py mdit-py-plugins linkify-it-py uc-micro-py watchdog
"""

import argparse
import html
import re
from pathlib import Path

from markdown_it import MarkdownIt
from mdit_py_plugins.footnote import footnote_plugin
from mdit_py_plugins.deflist import deflist_plugin
from mdit_py_plugins.tasklists import tasklists_plugin
from mdit_py_plugins.attrs import attrs_plugin, attrs_block_plugin

# Optional: only needed for --watch
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False


# ---------------------------------------------------------------------------
# Markdown configuration
# ---------------------------------------------------------------------------

def create_markdown_parser() -> MarkdownIt:
    """
    Create a MarkdownIt parser configured for GitHub-flavoured style Markdown.

    - Base: "gfm-like" (tables, strikethrough, linkify)
    - linkify: auto-detect bare URLs (requires linkify-it-py + uc-micro-py)
    - typographer: smart quotes, dashes
    - footnotes, definition lists, task lists via mdit-py-plugins
    - attrs_plugin: inline attributes, e.g. ![alt](url){.right}
    - attrs_block_plugin: block attributes on their own line, e.g.
        {.intro}
        A paragraph...
    """
    md = MarkdownIt(
        "gfm-like",
        {
            "linkify": True,
            "typographer": True,
        },
    )

    # Footnotes: [^1]
    md.use(footnote_plugin)

    # Definition lists:
    # Term
    # : Definition
    md.use(deflist_plugin)

    # Task lists:
    # - [ ] todo
    # - [x] done
    # enabled=False => checkboxes are disabled in HTML, similar to GitHub.
    md.use(tasklists_plugin, enabled=False, label=True, label_after=False)

    # Inline attributes after certain inline elements (images, code_inline, links, spans)
    # Example: ![alt](url){#id .class key=value}
    md.use(attrs_plugin)

    # Block attributes on a line by themselves, applying to the block BELOW.
    # Example:
    #   {.intro #top}
    #   # Heading
    md.use(attrs_block_plugin)

    return md


MD_PARSER = create_markdown_parser()


def render_markdown_to_html(markdown_text: str) -> str:
    """Render Markdown source to HTML using the configured parser."""
    return MD_PARSER.render(markdown_text)


# ---------------------------------------------------------------------------
# High-level build API
# ---------------------------------------------------------------------------

def build_all_sources(
    src_dir: Path,
    build_dir: Path,
    css_path: str,
    js_path: str,
    template_path: Path,
) -> None:
    """Build HTML for all .md files under src_dir."""
    md_files = sorted(src_dir.glob("*.md"))
    for md_file in md_files:
        build_single_source(md_file, src_dir, build_dir, css_path, js_path, template_path)


def build_single_source(
    md_path: Path,
    src_dir: Path,
    build_dir: Path,
    css_path: str,
    js_path: str,
    template_path: Path,
) -> Path:
    """
    Build a single .md (Markdown) file into an .html file under build_dir.

    Returns the path to the generated HTML file.
    """
    if not md_path.exists():
        raise FileNotFoundError(f"Text file not found: {md_path}")

    rel_name = md_path.stem  # "content" for "content.md"
    out_path = build_dir / f"{rel_name}.html"

    print(f"[build] {md_path} -> {out_path}")

    raw_text = read_text_file(md_path)
    body_html = render_markdown_to_html(raw_text)
    title = derive_title_from_markdown(raw_text, default=rel_name)

    full_html = wrap_in_document_shell(
        body_html=body_html,
        title=title,
        css_href=css_path,
        js_href=js_path,
        template_path=template_path,
    )

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
# Title derivation from Markdown
# ---------------------------------------------------------------------------

def derive_title_from_markdown(markdown_text: str, default: str) -> str:
    """
    Use the first ATX-style heading line as the HTML <title>, if present.

    Examples that will be used as the title:
      "# My Title"
      "## My Title ##"
    """
    for line in markdown_text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("#"):
            continue

        # Match "#" or "##" etc, then at least one space, then text.
        m = re.match(r"^#+\s+(.*)$", stripped)
        if not m:
            continue

        heading = m.group(1).strip()
        if not heading:
            continue

        # Strip any trailing " ###" style hashes if present.
        heading = re.sub(r"\s+#+\s*$", "", heading).strip()
        if heading:
            return heading

    return default


# ---------------------------------------------------------------------------
# Template + document shell
# ---------------------------------------------------------------------------

def html_escape(text: str) -> str:
    """HTML-escape a string."""
    return html.escape(text, quote=True)


def load_template(path: Path) -> str:
    """Load an HTML template file."""
    if not path.exists():
        raise FileNotFoundError(f"Template file not found: {path}")
    return path.read_text(encoding="utf-8")


def wrap_in_document_shell(
    body_html: str,
    title: str,
    css_href: str,
    js_href: str,
    template_path: Path,
) -> str:
    """
    Load the HTML template and substitute placeholders.

    The template must contain:
      {{title}}   - document title
      {{css}}     - href to CSS file
      {{dev_js}}  - src to reload JS file
      {{body}}    - rendered Markdown HTML
    """
    template = load_template(template_path)

    final_html = (
        template
        .replace("{{title}}", html_escape(title))
        .replace("{{css}}", css_href)
        .replace("{{dev_js}}", js_href)
        .replace("{{body}}", body_html)
    )
    return final_html


# ---------------------------------------------------------------------------
# Watch mode (optional)
# ---------------------------------------------------------------------------

class TxtChangeHandler(FileSystemEventHandler):
    """Watchdog handler that rebuilds on any .md change."""

    def __init__(
        self,
        src_dir: Path,
        build_dir: Path,
        css_path: str,
        js_path: str,
        template_path: Path,
    ) -> None:
        super().__init__()
        self.src_dir = src_dir
        self.build_dir = build_dir
        self.css_path = css_path
        self.js_path = js_path
        self.template_path = template_path

    def on_modified(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix.lower() == ".md":
            try:
                build_single_source(
                    md_path=path,
                    src_dir=self.src_dir,
                    build_dir=self.build_dir,
                    css_path=self.css_path,
                    js_path=self.js_path,
                    template_path=self.template_path,
                )
            except Exception as exc:
                print(f"[watch] Error rebuilding {path}: {exc}")


def watch_sources(
    src_dir: Path,
    build_dir: Path,
    css_path: str,
    js_path: str,
    template_path: Path,
) -> None:
    """Watch src_dir for changes to .md files and rebuild on modification."""
    if not WATCHDOG_AVAILABLE:
        raise RuntimeError(
            "watchdog is not installed. Install it with `pip install watchdog`."
        )

    print(f"[watch] Watching {src_dir} for changes...")
    event_handler = TxtChangeHandler(src_dir, build_dir, css_path, js_path, template_path)
    observer = Observer()
    observer.schedule(event_handler, str(src_dir), recursive=False)
    observer.start()

    try:
        while True:
            observer.join(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build HTML from Markdown (.md) files using an HTML template."
    )

    parser.add_argument(
        "name",
        nargs="?",
        help=(
            "Optional base name of a single text file to build, without .md "
            "(e.g. 'content' builds src/content.md). "
            "If omitted, all src/*.md are built."
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
        help="Source directory containing .md files (default: src).",
    )
    parser.add_argument(
        "--build-dir",
        default="tmp/step-2-resulting-html",
        help="Output directory for .html files (default: tmp/step-2-resulting-html).",
    )
    parser.add_argument(
        "--css",
        default="../../tools/style/style.css",
        help="Path/URL to CSS file as used in generated HTML (default: ../../tools/style/style.css).",
    )
    parser.add_argument(
        "--dev-js",
        default="../../tools/scripts/reload.js",
        help="Path/URL to dev reload JS in generated HTML (default: ../../tools/scripts/reload.js).",
    )
    parser.add_argument(
        "--template",
        default="tools/templates/page.html",
        help="HTML template used to wrap rendered Markdown (default: tools/templates/page.html).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    src_dir = Path(args.src_dir).resolve()
    build_dir = Path(args.build_dir).resolve()
    template_path = Path(args.template).resolve()

    if args.name:
        md_path = src_dir / f"{args.name}.md"
        build_single_source(
            md_path=md_path,
            src_dir=src_dir,
            build_dir=build_dir,
            css_path=args.css,
            js_path=args.dev_js,
            template_path=template_path,
        )
    else:
        build_all_sources(
            src_dir=src_dir,
            build_dir=build_dir,
            css_path=args.css,
            js_path=args.dev_js,
            template_path=template_path,
        )

    if args.watch:
        watch_sources(
            src_dir=src_dir,
            build_dir=build_dir,
            css_path=args.css,
            js_path=args.dev_js,
            template_path=template_path,
        )


if __name__ == "__main__":
    main()

