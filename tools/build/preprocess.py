from __future__ import annotations

import shutil
from pathlib import Path

PAGE_DIRECTIVE = "[[page]]"


def list_md_files(dir_path: Path) -> list[Path]:
    return sorted(dir_path.glob("*.md"))


def preprocess_text_add_pages(md_text: str) -> str:
    """
    Convert [[page]] directives into <section class="page" ...> wrappers.

    Output is still Markdown, but includes raw HTML block tags which
    markdown-it will preserve as HTML blocks.
    """
    lines = md_text.splitlines()
    out: list[str] = []

    page_num = 1
    out.append(f'<section class="page" data-page="{page_num}">')

    for line in lines:
        if line.strip() == PAGE_DIRECTIVE:
            # Close current page, open next
            out.append("</section>")
            page_num += 1
            out.append(f'<section class="page" data-page="{page_num}">')
        else:
            out.append(line)

    out.append("</section>")

    # Preserve trailing newline for nicer diffs
    return "\n".join(out).rstrip() + "\n"


def preprocess_file(src_path: Path, dst_path: Path) -> None:
    if not src_path.exists():
        raise FileNotFoundError(f"Markdown file not found: {src_path}")

    raw = src_path.read_text(encoding="utf-8")
    enhanced = preprocess_text_add_pages(raw)

    dst_path.parent.mkdir(parents=True, exist_ok=True)
    dst_path.write_text(enhanced, encoding="utf-8")


def preprocess_all(src_dir: Path, preprocess_dir: Path) -> int:
    """
    Preprocess all markdown files.

    Current behaviour:
      - Copy content with transformation:
        [[page]] -> </section><section class="page"...>
    """
    md_files = list_md_files(src_dir)
    if not md_files:
        print(f"[preprocess] No .md files found in: {src_dir}")
        return 0

    preprocess_dir.mkdir(parents=True, exist_ok=True)

    for src in md_files:
        dst = preprocess_dir / src.name
        print(f"[preprocess] {src} -> {dst}")
        preprocess_file(src, dst)

    return 0


def preprocess_one(src_dir: Path, preprocess_dir: Path, name: str) -> int:
    src = src_dir / f"{name}.md"
    if not src.exists():
        raise FileNotFoundError(f"Markdown file not found: {src}")

    preprocess_dir.mkdir(parents=True, exist_ok=True)
    dst = preprocess_dir / src.name
    print(f"[preprocess] {src} -> {dst}")
    preprocess_file(src, dst)
    return 0

