#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


DEFAULT_SRC_DIR = "src"
DEFAULT_STEP1_DIR = "tmp/step-1-enhanced-md"
DEFAULT_STEP2_DIR = "tmp/step-2-resulting-html"

DEFAULT_CSS = "../../tools/style/style.css"
DEFAULT_DEV_JS = "../../tools/scripts/reload.js"
DEFAULT_TEMPLATE = "tools/templates/page.html"


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run preprocess then build.")
    p.add_argument("name", nargs="?", help="Optional single file base name (without .md).")
    p.add_argument("--watch", action="store_true", help="(Not implemented in this pipeline yet.)")
    p.add_argument("--src-dir", default=DEFAULT_SRC_DIR)
    p.add_argument("--build-dir", default=DEFAULT_STEP2_DIR)
    p.add_argument("--css", default=DEFAULT_CSS)
    p.add_argument("--dev-js", default=DEFAULT_DEV_JS)
    p.add_argument("--template", default=DEFAULT_TEMPLATE)
    return p.parse_args()


def run_cmd(label: str, argv: list[str]) -> None:
    print(f"[pipeline] {label}: {' '.join(argv)}")

    # Capture so we can print on failure, but keep it visible.
    res = subprocess.run(argv, text=True, capture_output=True)

    if res.stdout:
        print(res.stdout, end="")
    if res.stderr:
        print(res.stderr, end="", file=sys.stderr)

    if res.returncode != 0:
        raise RuntimeError(f"{label} failed (exit code {res.returncode})")


def assert_any_html(html_dir: Path) -> None:
    html_files = list(html_dir.glob("*.html"))
    if not html_files:
        raise RuntimeError(
            "Build step completed but produced no .html files.\n"
            f"Expected output directory: {html_dir}\n"
            "Likely causes:\n"
            "- build.py was pointed at the wrong --src-dir\n"
            "- build.py ran in a different working directory than you expected\n"
        )


def main() -> int:
    args = parse_args()
    root = project_root()

    python = sys.executable  # IMPORTANT: uses the same interpreter you invoked pipeline with

    preprocess_py = root / "tools" / "preprocess.py"
    build_py = root / "tools" / "build.py"

    raw_src_dir = (root / args.src_dir).resolve()
    step1_dir = (root / DEFAULT_STEP1_DIR).resolve()
    step2_dir = (root / args.build_dir).resolve()
    template_path = (root / args.template).resolve()

    try:
        # Step 1
        cmd1 = [
            python, str(preprocess_py),
            *( [args.name] if args.name else [] ),
            "--src-dir", str(raw_src_dir),
            "--build-dir", str(step1_dir),
        ]
        run_cmd("preprocess", cmd1)

        # Step 2
        cmd2 = [
            python, str(build_py),
            *( [args.name] if args.name else [] ),
            "--src-dir", str(step1_dir),
            "--build-dir", str(step2_dir),
            "--css", args.css,
            "--dev-js", args.dev_js,
            "--template", str(template_path),
        ]
        run_cmd("build", cmd2)

        assert_any_html(step2_dir)
        return 0

    except Exception as e:
        print(f"[pipeline] ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

