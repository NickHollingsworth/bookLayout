from __future__ import annotations

import shutil
from pathlib import Path


def list_md_files(dir_path: Path) -> list[Path]:
    return sorted(dir_path.glob("*.md"))


def preprocess_all(src_dir: Path, preprocess_dir: Path) -> int:
    """
    Preprocess all markdown files.

    Current behaviour: copy src_dir/*.md -> preprocess_dir/*.md
    """
    md_files = list_md_files(src_dir)
    if not md_files:
        print(f"[preprocess] No .md files found in: {src_dir}")
        return 0

    preprocess_dir.mkdir(parents=True, exist_ok=True)

    for src in md_files:
        dst = preprocess_dir / src.name
        print(f"[preprocess] {src} -> {dst}")
        shutil.copy2(src, dst)

    return 0


def preprocess_one(src_dir: Path, preprocess_dir: Path, name: str) -> int:
    """
    Preprocess one markdown file by base name (without .md).
    """
    src = src_dir / f"{name}.md"
    if not src.exists():
        raise FileNotFoundError(f"Markdown file not found: {src}")

    preprocess_dir.mkdir(parents=True, exist_ok=True)
    dst = preprocess_dir / src.name
    print(f"[preprocess] {src} -> {dst}")
    shutil.copy2(src, dst)
    return 0

