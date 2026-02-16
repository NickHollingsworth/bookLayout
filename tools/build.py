#!/usr/bin/env python3
"""
Build pipeline for print-oriented docs.

Step 1: preprocess
  src_dir/*.md -> preprocess_dir/*.md

Step 2: render
  preprocess_dir/*.md -> build_dir/*.html

Default behaviour (no flags): run Step 1 then Step 2.

Flags:
  --preprocess-only      Run Step 1 only
  --render-only          Run Step 2 only (expects preprocess_dir populated)
  --continue-on-error    Keep going on directive/preprocess errors where possible
  --embed-errors         Also embed errors into the enhanced Markdown output

Watch:
  --watch with default (both): watches src_dir and runs both steps
  --watch --preprocess-only: watches src_dir and runs preprocess only
  --watch --render-only: watches preprocess_dir and runs render only

In --watch mode:
  - errors stop the watcher unless --continue-on-error is set.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.build.config import load_build_config, require_nonempty
from tools.build.preprocess import preprocess_all, preprocess_one
from tools.build.render import render_all, render_one
from tools.build.watch import watch_md_dir
from tools.build import terminal


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
    continue_on_error: bool,
    embed_errors: bool,
) -> int:
    """
    Returns number of errors encountered during preprocess.
    Raises on fatal errors unless continue_on_error is in effect within preprocess.
    """
    errors = 0

    if do_preprocess:
        if name:
            errors += preprocess_one(
                src_dir,
                preprocess_dir,
                name,
                continue_on_error=continue_on_error,
                embed_errors=embed_errors,
            )
        else:
            errors += preprocess_all(
                src_dir,
                preprocess_dir,
                continue_on_error=continue_on_error,
                embed_errors=embed_errors,
            )

    if do_render:
        # Render reads from preprocess_dir by design
        if name:
            render_one(preprocess_dir / f"{name}.md", build_dir, css_href, js_href, template_path)
        else:
            render_all(preprocess_dir, build_dir, css_href, js_href, template_path)

    return errors


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build pipeline: preprocess and/or render HTML.")
    p.add_argument("name", nargs="?", help="Optional single file base name (without .md).")

    p.add_argument("-w", "--watch", action="store_true", help="Watch for changes and rebuild.")
    p.add_argument("-v", "--verbose", action="store_true", help="Verbose output.")

    mode = p.add_mutually_exclusive_group()
    mode.add_argument("-p", "--preprocess-only", action="store_true", help="Run preprocess step only.")
    mode.add_argument("-r", "--render-only", action="store_true", help="Run render step only.")

    p.add_argument("-c", "--continue-on-error", action="store_true",
                   help="Continue after preprocess/directive errors where possible.")
    p.add_argument("-e", "--embed-errors", action="store_true",
                   help="Embed preprocess/directive errors into enhanced Markdown output.")

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
    terminal.configure(verbose=args.verbose)

    # Load config
    try:
        cfg = load_build_config(Path(args.config).resolve())
    except Exception as exc:
        terminal.error(f"loading config: {exc}", prefix="[build]")
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
        terminal.error(str(exc), prefix="[build]")
        return 2

    src_dir = Path(src_dir_str).resolve()
    preprocess_dir = Path(preprocess_dir_str).resolve()
    build_dir = Path(build_dir_str).resolve()
    template_path = Path(template_str).resolve()

    if not src_dir.exists():
        terminal.error(f"source directory does not exist: {src_dir}", prefix="[build]")
        return 2

    do_preprocess = not args.render_only
    do_render = not args.preprocess_only

    had_errors = False

    def run_now() -> None:
        nonlocal had_errors
        errors = run_steps(
            name=args.name,
            do_preprocess=do_preprocess,
            do_render=do_render,
            src_dir=src_dir,
            preprocess_dir=preprocess_dir,
            build_dir=build_dir,
            css_href=css_href,
            js_href=js_href,
            template_path=template_path,
            continue_on_error=args.continue_on_error,
            embed_errors=args.embed_errors,
        )
        if errors:
            had_errors = True
            terminal.error(f"{errors} error(s) during preprocess", prefix="[build]")

    # One-shot run
    try:
        run_now()
    except Exception as exc:
        terminal.error(str(exc), prefix="[build]")
        return 1

    # Watch mode
    if args.watch:
        if args.preprocess_only:
            watch_dir = src_dir
        elif args.render_only:
            watch_dir = preprocess_dir
        else:
            watch_dir = src_dir

        if args.continue_on_error:
            def run_now_watch() -> None:
                try:
                    run_now()
                except Exception as exc:
                    # swallow to keep watcher alive
                    terminal.error(str(exc), prefix="[build]")

            watch_md_dir(watch_dir, run_now_watch)
        else:
            # Let exceptions propagate: watcher stops on first error
            watch_md_dir(watch_dir, run_now)

        return 0

    # Non-watch: exit non-zero if any errors happened (even if continued)
    return 1 if had_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

