from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path

PAGE_DIRECTIVE = "[[page]]"
DEFAULT_SUBST_CONFIG = Path("tools/preprocess.conf")

# Matches a whole-line directive of the form [[SOMETHING]]
WHOLE_LINE_DIRECTIVE_RE = re.compile(r"^\s*(\[\[[^\]]+\]\])\s*$")


@dataclass(frozen=True)
class SubstitutionRule:
    token: str
    replacement: str


def list_md_files(dir_path: Path) -> list[Path]:
    return sorted(dir_path.glob("*.md"))


def _parse_subst_config(config_path: Path) -> dict[str, SubstitutionRule]:
    """
    Parse a simple substitutions config file.

    Format:
      [[TOKEN]] = replacement text
      [[TOKEN]] = @file:relative/path.html

    Rules:
      - blank lines ignored
      - lines starting with # ignored
      - split on first '='
      - key/value trimmed
      - duplicates are errors
    """
    if not config_path.exists():
        return {}

    rules: dict[str, SubstitutionRule] = {}
    base_dir = config_path.parent

    lines = config_path.read_text(encoding="utf-8").splitlines()
    for lineno, raw in enumerate(lines, start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue

        if "=" not in line:
            raise ValueError(f"{config_path}:{lineno}: expected '[[TOKEN]] = replacement' (missing '='): {raw!r}")

        key, value = line.split("=", 1)
        token = key.strip()
        rhs = value.strip()

        if not token:
            raise ValueError(f"{config_path}:{lineno}: empty token in line: {raw!r}")
        if rhs == "":
            raise ValueError(f"{config_path}:{lineno}: empty replacement for token {token!r}")

        if token in rules:
            raise ValueError(f"{config_path}:{lineno}: duplicate token {token!r}")

        if rhs.startswith("@file:"):
            rel = rhs[len("@file:"):].strip()
            if not rel:
                raise ValueError(f"{config_path}:{lineno}: @file: requires a path for token {token!r}")

            inc_path = (base_dir / rel).resolve()
            if not inc_path.exists():
                raise FileNotFoundError(f"{config_path}:{lineno}: include file not found for {token!r}: {inc_path}")

            replacement = inc_path.read_text(encoding="utf-8")
        else:
            replacement = rhs

        rules[token] = SubstitutionRule(token=token, replacement=replacement)

    return rules

def apply_sed_like_substitutions(md_text: str, rules: dict[str, SubstitutionRule]) -> str:

    if not rules:
        return md_text

    out = md_text
    for token, rule in rules.items():
        out = out.replace(token, rule.replacement)

    # Keep trailing newline stable for diffs
    return out.rstrip()


def preprocess_text_add_pages(md_text: str) -> str:
    """
    Convert [[page]] directives into <section class="page" ...> wrappers.

    Ensures blank lines around HTML block boundaries so Markdown parses correctly.
    """
    lines = md_text.splitlines()
    out: list[str] = []

    page_num = 1

    # Open first page
    out.append(f'<section class="page" data-page="{page_num}">')
    out.append("")  # blank line to end HTML block

    for line in lines:
        if line.strip() == PAGE_DIRECTIVE:
            # Close current page
            out.append("")
            out.append("</section>")
            out.append("")

            # Open next page
            page_num += 1
            out.append(f'<section class="page" data-page="{page_num}">')
            out.append("")
        else:
            out.append(line)

    # Close final page
    out.append("")
    out.append("</section>")

    return "\n".join(out) + "\n"


def preprocess_file(src_path: Path, dst_path: Path, subst_rules: dict[str, SubstitutionRule]) -> None:
    if not src_path.exists():
        raise FileNotFoundError(f"Markdown file not found: {src_path}")

    raw = src_path.read_text(encoding="utf-8")

    # Step A: simple config-driven substitutions
    enhanced = apply_sed_like_substitutions(raw, subst_rules)

    # Step B: structural directives (code handlers)
    enhanced = preprocess_text_add_pages(enhanced)

    dst_path.parent.mkdir(parents=True, exist_ok=True)
    dst_path.write_text(enhanced, encoding="utf-8")


def preprocess_all(src_dir: Path, preprocess_dir: Path) -> int:
    md_files = list_md_files(src_dir)
    if not md_files:
        print(f"[preprocess] No .md files found in: {src_dir}")
        return 0

    subst_rules = _parse_subst_config(DEFAULT_SUBST_CONFIG)

    preprocess_dir.mkdir(parents=True, exist_ok=True)
    for src in md_files:
        dst = preprocess_dir / src.name
        print(f"[preprocess] {src} -> {dst}")
        preprocess_file(src, dst, subst_rules)

    return 0


def preprocess_one(src_dir: Path, preprocess_dir: Path, name: str) -> int:
    src = src_dir / f"{name}.md"
    if not src.exists():
        raise FileNotFoundError(f"Markdown file not found: {src}")

    subst_rules = _parse_subst_config(DEFAULT_SUBST_CONFIG)

    preprocess_dir.mkdir(parents=True, exist_ok=True)
    dst = preprocess_dir / src.name
    print(f"[preprocess] {src} -> {dst}")
    preprocess_file(src, dst, subst_rules)
    return 0

