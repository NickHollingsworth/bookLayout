from __future__ import annotations

from pathlib import Path


def read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def list_md_files(dir_path: Path) -> list[Path]:
    return sorted(dir_path.glob("*.md"))

