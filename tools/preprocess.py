#!/usr/bin/env python3
"""
Preprocess Markdown before rendering.

Current behaviour (Step 1):
- Copy src/*.md -> tmp/step-1-enhanced-md/*.md
- Does NOT transform content yet

Usage:
  python tools/preprocess.py
  python tools/preprocess.py page
  python tools/preprocess.py --watch

Arguments are intentionally aligned with build.py, even if some are unused
(css/dev-js/template are accepted but ignored for now).
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

# Optional: only needed for --watch
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False


DEFAULT_SRC_DIR = "src"
DEFAULT_OUT_MD_DIR = "tmp/step-1-enhanced-md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preprocess Markdown (.md) files. Currently: copy to tmp/step-1-enhanced-md."
    )

    parser.add_argument(
        "name",
        nargs="?",
        help=(
            "Optional base name of a single markdown file to preprocess, without .md "
            "(e.g. 'page' preprocesses src/page.md). "
            "If omitted, all src/*.md are processed."
        ),
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Watch src/ for changes and re-run preprocessing.",
    )
    parser.add_argument(
        "--src-dir",
        default=DEFAULT_SRC_DIR,
        help=f"Source directory containing .md files (default: {DEFAULT_SRC_DIR}).",
    )
    parser.add_argument(
        "--build-dir",
        default=DEFAULT_OUT_MD_DIR,
        help=f"Output directory for enhanced .md files (default: {DEFAULT_OUT_MD_DIR}).",
    )

    # Accepted for CLI compatibility with build.py; unused in this step.
    parser.add_argument("--css", default=None, help=argparse.SUPPRESS)
    parser.add_argument("--dev-js", default=None, help=argparse.SUPPRESS)
    parser.add_argument("--template", default=None, help=argparse.SUPPRESS)

    return parser.parse_args()


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def copy_file(src_path: Path, out_path: Path) -> None:
    ensure_dir(out_path.parent)
    shutil.copy2(src_path, out_path)


def preprocess_one(md_path: Path, out_dir: Path) -> Path:
    if not md_path.exists():
        raise FileNotFoundError(f"Markdown file not found: {md_path}")

    out_path = out_dir / md_path.name
    print(f"[preprocess] {md_path} -> {out_path}")
    copy_file(md_path, out_path)
    return out_path


def preprocess_all(src_dir: Path, out_dir: Path) -> None:
    md_files = sorted(src_dir.glob("*.md"))
    if not md_files:
        print(f"[preprocess] No .md files found in: {src_dir}")
        return

    for md_path in md_files:
        preprocess_one(md_path, out_dir)


class MdChangeHandler(FileSystemEventHandler):
    def __init__(self, src_dir: Path, out_dir: Path, single_name: str | None) -> None:
        super().__init__()
        self.src_dir = src_dir
        self.out_dir = out_dir
        self.single_name = single_name

    def on_modified(self, event):
        if event.is_directory:
            return

        path = Path(event.src_path)
        if path.suffix.lower() != ".md":
            return

        try:
            if self.single_name:
                # only rebuild the single requested file
                target = self.src_dir / f"{self.single_name}.md"
                preprocess_one(target, self.out_dir)
            else:
                preprocess_all(self.src_dir, self.out_dir)
        except Exception as exc:
            print(f"[preprocess][watch] Error: {exc}", file=sys.stderr)


def watch(src_dir: Path, out_dir: Path, single_name: str | None) -> None:
    if not WATCHDOG_AVAILABLE:
        raise RuntimeError("watchdog is not installed. Install it with `pip install watchdog`.")

    print(f"[preprocess][watch] Watching {src_dir} for .md changes...")
    handler = MdChangeHandler(src_dir, out_dir, single_name)
    observer = Observer()
    observer.schedule(handler, str(src_dir), recursive=False)
    observer.start()

    try:
        while True:
            observer.join(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


def main() -> int:
    args = parse_args()

    src_dir = Path(args.src_dir).resolve()
    out_dir = Path(args.build_dir).resolve()

    if not src_dir.exists():
        print(f"[preprocess] Source directory does not exist: {src_dir}", file=sys.stderr)
        return 2

    try:
        if args.name:
            preprocess_one(src_dir / f"{args.name}.md", out_dir)
        else:
            preprocess_all(src_dir, out_dir)

        if args.watch:
            watch(src_dir, out_dir, args.name)

    except Exception as exc:
        print(f"[preprocess] ERROR: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

