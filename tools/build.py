#!/usr/bin/env python3
"""
Build pipeline for print-oriented docs.

Step 1: preprocess (currently: copy)
  src_dir/*.md -> preprocess_dir/*.md

Step 2: render
  preprocess_dir/*.md -> build_dir/*.html

Default behaviour (no flags): run Step 1 then Step 2.

Flags:
  --preprocess-only   Run Step 1 only
  --render-only       Run Step 2 only (expects preprocess_dir populated)

Config:
  Plain text key=value file, default tools/build.conf
  CLI overrides config.

Watch:
  --watch with default (both): watches src_dir and runs both steps
  --watch --preprocess-only: watches src_dir and runs preprocess only
  --watch --render-only: watches preprocess_dir and runs render only
"""

from __future__ import annotations

import argparse
import html
import re
import shutil
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from build.config import BuildConfig, load_build_config, require_nonempty
from build.markdown_to_html import render_markdown_to_html
from build.template import wrap_in_document_shell


# Optional: only needed for --watch
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False


# ---------------------------------------------------------------------------
# IO helpers
# ---------------------------------------------------------------------------

def read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def list_md_files(dir_path: Path) -> list[Path]:
    return sorted(dir_path.glob("*.md"))


# ---------------------------------------------------------------------------
# Step 1: preprocess (currently: copy)
# ---------------------------------------------------------------------------

def preprocess_all(src_dir: Path, preprocess_dir: Path) -> int:
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
    src = src_dir / f"{name}.md"
    if not src.exists():
        raise FileNotFoundError(f"Markdown file not found: {src}")

    preprocess_dir.mkdir(parents=True, exist_ok=True)
    dst = preprocess_dir / src.name
    print(f"[preprocess] {src} -> {dst}")
    shutil.copy2(src, dst)
    return 0


# ---------------------------------------------------------------------------
# Step 2: render
# ---------------------------------------------------------------------------

def derive_title_from_markdown(markdown_text: str, default: str) -> str:
    for line in markdown_text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("#"):
            continue
        m = re.match(r"^#+\s+(.*)$", stripped)
        if not m:
            continue
        heading = re.sub(r"\s+#+\s*$", "", m.group(1).strip()).strip()
        if heading:
            return heading
    return default


def render_all(
    preprocess_dir: Path,
    build_dir: Path,
    css_href: str,
    js_href: str,
    template_path: Path,
) -> int:
    md_files = list_md_files(preprocess_dir)
    if not md_files:
        print(f"[build] No .md files found in: {preprocess_dir}")
        return 0

    for md_path in md_files:
        render_one(md_path, build_dir, css_href, js_href, template_path)
    return 0


def render_one(
    md_path: Path,
    build_dir: Path,
    css_href: str,
    js_href: str,
    template_path: Path,
) -> Path:
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


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def run_steps(
    *,
    name: str | None,
    do_preprocess: bool,
    do_render: bool,
    src_dir: Path,
    preprocess_dir: Path,
    build_dir: Path,
    css_href: str,
    js_href: str,
    template_path: Path,
) -> int:
    if do_preprocess:
        if name:
            preprocess_one(src_dir, preprocess_dir, name)
        else:
            preprocess_all(src_dir, preprocess_dir)

    if do_render:
        # Render reads from preprocess_dir by design
        if name:
            render_one(preprocess_dir / f"{name}.md", build_dir, css_href, js_href, template_path)
        else:
            render_all(preprocess_dir, build_dir, css_href, js_href, template_path)

    return 0


# ---------------------------------------------------------------------------
# Watch mode
# ---------------------------------------------------------------------------

class DebouncedRunner:
    def __init__(self, min_interval_s: float = 0.25) -> None:
        self.min_interval_s = min_interval_s
        self._last_run = 0.0

    def should_run(self) -> bool:
        now = time.time()
        if now - self._last_run < self.min_interval_s:
            return False
        self._last_run = now
        return True


class WatchHandler(FileSystemEventHandler):
    def __init__(self, on_change, debounce: DebouncedRunner) -> None:
        super().__init__()
        self.on_change = on_change
        self.debounce = debounce

    def on_modified(self, event):
        if event.is_directory:
            return
        p = str(event.src_path).lower()
        if not p.endswith(".md"):
            return
        if self.debounce.should_run():
            self.on_change()

    # some editors trigger "created" rather than "modified"
    def on_created(self, event):
        self.on_modified(event)


def watch(
    *,
    watch_dir: Path,
    on_change,
) -> None:
    if not WATCHDOG_AVAILABLE:
        raise RuntimeError("watchdog is not installed. Install it with `pip install watchdog`.")

    print(f"[watch] Watching {watch_dir} for .md changes...")
    debounce = DebouncedRunner()
    handler = WatchHandler(on_change, debounce)

    observer = Observer()
    observer.schedule(handler, str(watch_dir), recursive=False)
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
    p = argparse.ArgumentParser(description="Build pipeline: preprocess and/or render HTML.")
    p.add_argument("name", nargs="?", help="Optional single file base name (without .md).")
    p.add_argument("--watch", action="store_true", help="Watch for changes and rebuild.")

    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--preprocess-only", action="store_true", help="Run preprocess step only.")
    mode.add_argument("--render-only", action="store_true", help="Run render step only.")

    p.add_argument("--config", default="tools/build.conf", help="Path to config file.")

    # Overrides (CLI wins over config)
    p.add_argument("--src-dir", default=None, help="Override source directory.")
    p.add_argument("--preprocess-dir", default=None, help="Override preprocess output directory.")
    p.add_argument("--build-dir", default=None, help="Override HTML output directory.")
    p.add_argument("--css", default=None, help="Override CSS href.")
    p.add_argument("--dev-js", default=None, help="Override dev reload JS href.")
    p.add_argument("--template", default=None, help="Override HTML template path.")

    return p.parse_args()


def main() -> int:
    args = parse_args()

    # Load config
    try:
        cfg = load_build_config(Path(args.config).resolve())
    except Exception as exc:
        print(f"[build] ERROR loading config: {exc}", file=sys.stderr)
        return 2

    # Merge config + CLI
    try:
        src_dir_str = require_nonempty("src_dir", args.src_dir or cfg.src_dir)
        preprocess_dir_str = require_nonempty("preprocess_dir", args.preprocess_dir or cfg.preprocess_dir)
        build_dir_str = require_nonempty("build_dir", args.build_dir or cfg.build_dir)
        css_href = require_nonempty("css", args.css or cfg.css)
        js_href = require_nonempty("dev_js", args.dev_js or cfg.dev_js)
        template_str = require_nonempty("template", args.template or cfg.template)
    except Exception as exc:
        print(f"[build] ERROR: {exc}", file=sys.stderr)
        return 2

    src_dir = Path(src_dir_str).resolve()
    preprocess_dir = Path(preprocess_dir_str).resolve()
    build_dir = Path(build_dir_str).resolve()
    template_path = Path(template_str).resolve()

    if not src_dir.exists():
        print(f"[build] ERROR: source directory does not exist: {src_dir}", file=sys.stderr)
        return 2

    do_preprocess = not args.render_only
    do_render = not args.preprocess_only

    def run_now():
        try:
            run_steps(
                name=args.name,
                do_preprocess=do_preprocess,
                do_render=do_render,
                src_dir=src_dir,
                preprocess_dir=preprocess_dir,
                build_dir=build_dir,
                css_href=css_href,
                js_href=js_href,
                template_path=template_path,
            )
        except Exception as exc:
            print(f"[build] ERROR: {exc}", file=sys.stderr)

    # One-shot run
    try:
        run_now()
    except Exception as exc:
        print(f"[build] ERROR: {exc}", file=sys.stderr)
        return 1

    # Watch mode
    if args.watch:
        if args.preprocess_only:
            watch_dir = src_dir
        elif args.render_only:
            watch_dir = preprocess_dir
        else:
            # both: watch src and run both to avoid double-trigger loops
            watch_dir = src_dir

        try:
            watch(watch_dir=watch_dir, on_change=run_now)
        except Exception as exc:
            print(f"[watch] ERROR: {exc}", file=sys.stderr)
            return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

