#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"

print_file () {
  local f="$1"
  if [[ -f "$f" ]]; then
    echo "================================================================"
    echo "FILE: $f"
    echo "================================================================"
    echo
    cat "$f"
    echo
  fi
}

# Core pipeline
print_file tools/build.py
print_file tools/build/config.py
print_file tools/build/preprocess.py
print_file tools/build/render.py
print_file tools/build/watch.py

# Config
print_file tools/build.conf
print_file tools/preprocess.conf
print_file tools/snippets/example.html
print_file tools/templates/page.html
print_file tools/style/style.css
print_file tools/scripts/reload.js

# Example input (adjust if needed)
print_file src/page.md

