from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from tools.build import terminal

PAGE_DIRECTIVE = "[[page]]"
DEFAULT_SUBST_CONFIG = Path("tools/preprocess.conf")

WHOLE_LINE_DIRECTIVE_RE = re.compile(r"^\s*(\[\[[^\]]+\]\])\s*$")
PLACEHOLDER_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


# ---------------------------------------------------------------------------
# Rule types
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SubstitutionRule:
    token: str
    replacement: str


@dataclass(frozen=True)
class ParamSpec:
    name: str
    required: bool
    default: str | None = None


@dataclass(frozen=True)
class DirectiveRule:
    name: str
    params: list[ParamSpec]
    template: str


@dataclass(frozen=True)
class PreprocessOptions:
    continue_on_error: bool = False
    embed_errors: bool = False


# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------

def list_md_files(dir_path: Path) -> list[Path]:
    return sorted(dir_path.glob("*.md"))


# ---------------------------------------------------------------------------
# Embedded error formatting (Markdown-visible)
# ---------------------------------------------------------------------------

def _format_embedded_error(where: str, message: str) -> str:
    one_line = " ".join(message.splitlines()).strip()
    return "\n".join([
        "> **BUILD ERROR**",
        f"> **Where:** {where}",
        f"> **Message:** {one_line}",
        "> (directive left unchanged)",
        ""
    ])


# ---------------------------------------------------------------------------
# CSV-ish parsing helpers
# ---------------------------------------------------------------------------

def _split_csvish(text: str, *, where: str) -> list[str]:
    tokens: list[str] = []
    buf: list[str] = []
    in_quotes = False
    escape = False

    def flush_token() -> None:
        tok = "".join(buf).strip()
        if tok == "":
            raise ValueError(f"{where}: empty token in comma-separated list")
        tokens.append(tok)

    for ch in text:
        if in_quotes:
            if escape:
                if ch not in ['"', '\\']:
                    buf.append("\\")
                buf.append(ch)
                escape = False
                continue

            if ch == "\\":
                escape = True
                continue
            if ch == '"':
                in_quotes = False
                continue

            buf.append(ch)
            continue

        if ch == '"':
            in_quotes = True
            continue

        if ch == ",":
            flush_token()
            buf = []
            continue

        buf.append(ch)

    if escape:
        buf.append("\\")

    if in_quotes:
        raise ValueError(f"{where}: unterminated double quote in list")

    flush_token()
    return tokens


def _strip_outer_brackets(directive_text: str, *, where: str) -> str:
    s = directive_text.strip()
    if not (s.startswith("[[") and s.endswith("]]")):
        raise ValueError(f"{where}: not a directive: {directive_text!r}")
    inner = s[2:-2].strip()
    if inner == "":
        raise ValueError(f"{where}: empty directive: {directive_text!r}")
    return inner


# ---------------------------------------------------------------------------
# Parse config LHS signature and Markdown invocation
# ---------------------------------------------------------------------------

def _parse_signature_lhs(lhs: str, *, where: str) -> tuple[str, list[ParamSpec]]:
    inner = _strip_outer_brackets(lhs, where=where)
    parts = _split_csvish(inner, where=where)

    name = parts[0].strip()
    if not name:
        raise ValueError(f"{where}: empty directive name in {lhs!r}")

    params: list[ParamSpec] = []
    seen: set[str] = set()
    seen_optional = False

    for raw in parts[1:]:
        if "=" in raw:
            pname, pdefault = raw.split("=", 1)
            pname = pname.strip()
            pdefault = pdefault.strip()

            if not pname:
                raise ValueError(f"{where}: empty parameter name in {lhs!r}")
            if pname in seen:
                raise ValueError(f"{where}: duplicate parameter {pname!r} in {lhs!r}")
            if pdefault == "":
                raise ValueError(f"{where}: empty default for optional parameter {pname!r} in {lhs!r}")

            seen.add(pname)
            seen_optional = True
            params.append(ParamSpec(name=pname, required=False, default=pdefault))
        else:
            pname = raw.strip()
            if not pname:
                raise ValueError(f"{where}: empty parameter name in {lhs!r}")
            if pname in seen:
                raise ValueError(f"{where}: duplicate parameter {pname!r} in {lhs!r}")
            if seen_optional:
                raise ValueError(
                    f"{where}: required parameter {pname!r} cannot appear after optional parameters in {lhs!r}"
                )

            seen.add(pname)
            params.append(ParamSpec(name=pname, required=True, default=None))

    return name, params


def _parse_invocation(inner: str, *, where: str) -> tuple[str, list[str], dict[str, str]]:
    parts = _split_csvish(inner, where=where)
    name = parts[0].strip()
    if not name:
        raise ValueError(f"{where}: empty directive name in [[{inner}]]")

    positional: list[str] = []
    named: dict[str, str] = {}

    for raw in parts[1:]:
        if "=" in raw:
            k, v = raw.split("=", 1)
            k = k.strip()
            v = v.strip()
            if not k:
                raise ValueError(f"{where}: empty named-arg key in [[{inner}]]")
            if v == "":
                raise ValueError(f"{where}: empty value for named arg {k!r} in [[{inner}]]")
            if k in named:
                raise ValueError(f"{where}: duplicate named arg {k!r} in [[{inner}]]")
            named[k] = v
        else:
            positional.append(raw)

    return name, positional, named


# ---------------------------------------------------------------------------
# Argument resolution + template substitution
# ---------------------------------------------------------------------------

def _resolve_args(rule: DirectiveRule, positional: list[str], named: dict[str, str], *, where: str) -> dict[str, str]:
    param_set = {p.name for p in rule.params}

    unknown = sorted(set(named.keys()) - param_set)
    if unknown:
        raise ValueError(f"{where}: unknown named arg(s) for {rule.name}: {', '.join(unknown)}")

    resolved: dict[str, str] = {}
    assigned: set[str] = set()

    # Defaults
    for p in rule.params:
        if not p.required and p.default is not None:
            resolved[p.name] = p.default

    # Named overrides
    for k, v in named.items():
        resolved[k] = v
        assigned.add(k)

    # Positional fill, skipping named-assigned params
    pos_i = 0
    for p in rule.params:
        if pos_i >= len(positional):
            break
        if p.name in assigned:
            continue
        resolved[p.name] = positional[pos_i]
        assigned.add(p.name)
        pos_i += 1

    if pos_i < len(positional):
        raise ValueError(
            f"{where}: too many positional args for {rule.name} "
            f"(got {len(positional)}, signature has {len(rule.params)})"
        )

    missing = [p.name for p in rule.params if p.required and p.name not in resolved]
    if missing:
        raise ValueError(f"{where}: missing required arg(s) for {rule.name}: {', '.join(missing)}")

    return resolved


def _substitute_placeholders(template: str, values: dict[str, str], *, where: str) -> str:
    unknown: set[str] = set()

    def repl(m: re.Match) -> str:
        k = m.group(1)
        if k not in values:
            unknown.add(k)
            return m.group(0)
        return values[k]

    out = PLACEHOLDER_RE.sub(repl, template)

    if unknown:
        raise ValueError(f"{where}: template references unknown placeholder(s): {', '.join(sorted(unknown))}")

    return out


# ---------------------------------------------------------------------------
# Whole-line directive expansion
# ---------------------------------------------------------------------------

def expand_whole_line_directives(
    md_text: str,
    directive_rules: dict[str, DirectiveRule],
    *,
    source_path: Path | None = None,
    options: PreprocessOptions = PreprocessOptions(),
) -> tuple[str, int]:
    """
    Expand only whole-line directives.

    - Recognized directive names expand.
    - Unrecognized directives are left unchanged.
    - On error:
        * if options.continue_on_error: report + leave directive unchanged + continue
        * else: raise
    Returns (expanded_text, error_count).
    """
    lines = md_text.splitlines()
    out: list[str] = []
    errors = 0

    for lineno, line in enumerate(lines, start=1):
        m = WHOLE_LINE_DIRECTIVE_RE.match(line)
        if not m:
            out.append(line)
            continue

        directive_text = m.group(1)
        where = f"{source_path}:{lineno}" if source_path else f"line {lineno}"

        try:
            inner = _strip_outer_brackets(directive_text, where=where)
            name, positional, named = _parse_invocation(inner, where=where)

            rule = directive_rules.get(name)
            if rule is None:
                out.append(line)  # unrecognized -> unchanged
                continue

            values = _resolve_args(rule, positional, named, where=where)
            expanded = _substitute_placeholders(rule.template, values, where=where)
            out.extend(expanded.splitlines())

        except Exception as exc:
            errors += 1

            if options.continue_on_error:
                terminal.error(str(exc), where=where, prefix="[preprocess]")

                if options.embed_errors:
                    out.extend(_format_embedded_error(where, str(exc)).splitlines())

                out.append(line)
                continue

            raise

    result = "\n".join(out) + ("\n" if md_text.endswith("\n") else "")
    return result, errors


# ---------------------------------------------------------------------------
# Config parsing
# ---------------------------------------------------------------------------

def _split_config_assignment(line: str, *, where: str) -> tuple[str, str]:
    close = line.find("]]")
    if close == -1:
        raise ValueError(f"{where}: expected directive LHS ending with ']]': {line!r}")

    lhs = line[: close + 2].strip()
    rest = line[close + 2 :].lstrip()

    if not rest.startswith("="):
        raise ValueError(f"{where}: expected '=' after directive LHS: {line!r}")

    rhs = rest[1:].strip()
    if rhs == "":
        raise ValueError(f"{where}: empty RHS for {lhs!r}")

    return lhs, rhs


def _parse_subst_config(config_path: Path) -> tuple[dict[str, SubstitutionRule], dict[str, DirectiveRule]]:
    if not config_path.exists():
        return {}, {}

    subst_rules: dict[str, SubstitutionRule] = {}
    directive_rules: dict[str, DirectiveRule] = {}
    base_dir = config_path.parent

    lines = config_path.read_text(encoding="utf-8").splitlines()
    i = 0

    while i < len(lines):
        raw = lines[i]
        lineno = i + 1
        line = raw.strip()
        where = f"{config_path}:{lineno}"

        if not line or line.startswith("#"):
            i += 1
            continue

        lhs, rhs = _split_config_assignment(line, where=where)
        name, params = _parse_signature_lhs(lhs, where=where)

        # RHS: fenced multi-line
        if rhs.startswith("```"):
            open_lineno = lineno
            i += 1
            block_lines: list[str] = []

            while i < len(lines):
                if lines[i] == "```":
                    break
                block_lines.append(lines[i])
                i += 1

            if i >= len(lines):
                raise ValueError(
                    f"{config_path}:{open_lineno}: unterminated fenced block for {lhs!r} (expected closing line ```)"
                )

            template = "\n".join(block_lines)
            i += 1  # consume closing fence

        # RHS: @file include
        elif rhs.startswith("@file:"):
            rel = rhs[len("@file:"):].strip()
            if not rel:
                raise ValueError(f"{config_path}:{lineno}: @file: requires a path for {lhs!r}")

            inc_path = (base_dir / rel).resolve()
            if not inc_path.exists():
                raise FileNotFoundError(f"{config_path}:{lineno}: include file not found for {lhs!r}: {inc_path}")

            template = inc_path.read_text(encoding="utf-8")
            i += 1

        # RHS: single-line
        else:
            template = rhs
            i += 1

        if name in directive_rules:
            raise ValueError(f"{config_path}:{lineno}: duplicate directive name {name!r}")

        directive_rules[name] = DirectiveRule(name=name, params=params, template=template)

        # Back-compat: zero-arg directives also become simple literal tokens [[NAME]]
        if not params:
            token = f"[[{name}]]"
            if token in subst_rules:
                raise ValueError(f"{config_path}:{lineno}: duplicate token {token!r}")
            subst_rules[token] = SubstitutionRule(token=token, replacement=template)

    return subst_rules, directive_rules


# ---------------------------------------------------------------------------
# Simple sed-like substitution (global)
# ---------------------------------------------------------------------------

def apply_sed_like_substitutions(md_text: str, rules: dict[str, SubstitutionRule]) -> str:
    if not rules:
        return md_text

    out = md_text
    for token, rule in rules.items():
        out = out.replace(token, rule.replacement)

    return out.rstrip()


# ---------------------------------------------------------------------------
# Page directive handling
# ---------------------------------------------------------------------------

def preprocess_text_add_pages(md_text: str) -> str:
    lines = md_text.splitlines()
    out: list[str] = []

    page_num = 1
    out.append(f'<section class="page" data-page="{page_num}">')
    out.append("")

    for line in lines:
        if line.strip() == PAGE_DIRECTIVE:
            out.append("")
            out.append("</section>")
            out.append("")

            page_num += 1
            out.append(f'<section class="page" data-page="{page_num}">')
            out.append("")
        else:
            out.append(line)

    out.append("")
    out.append("</section>")

    return "\n".join(out) + "\n"


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def preprocess_file(src_path: Path, dst_path: Path, *, options: PreprocessOptions) -> int:
    if not src_path.exists():
        raise FileNotFoundError(f"Markdown file not found: {src_path}")

    raw = src_path.read_text(encoding="utf-8")

    subst_rules, directive_rules = _parse_subst_config(DEFAULT_SUBST_CONFIG)

    enhanced, errors = expand_whole_line_directives(
        raw,
        directive_rules,
        source_path=src_path,
        options=options,
    )

    enhanced = apply_sed_like_substitutions(enhanced, subst_rules)
    enhanced = preprocess_text_add_pages(enhanced)

    dst_path.parent.mkdir(parents=True, exist_ok=True)
    dst_path.write_text(enhanced, encoding="utf-8")
    return errors


def preprocess_all(
    src_dir: Path,
    preprocess_dir: Path,
    *,
    continue_on_error: bool = False,
    embed_errors: bool = False,
) -> int:
    md_files = list_md_files(src_dir)
    if not md_files:
        terminal.info(f"No .md files found in: {src_dir}", prefix="[preprocess]")
        return 0

    options = PreprocessOptions(continue_on_error=continue_on_error, embed_errors=embed_errors)

    preprocess_dir.mkdir(parents=True, exist_ok=True)
    errors = 0

    for src in md_files:
        dst = preprocess_dir / src.name
        terminal.info(f"{src} -> {dst}", prefix="[preprocess]")
        errors += preprocess_file(src, dst, options=options)

    return errors


def preprocess_one(
    src_dir: Path,
    preprocess_dir: Path,
    name: str,
    *,
    continue_on_error: bool = False,
    embed_errors: bool = False,
) -> int:
    src = src_dir / f"{name}.md"
    if not src.exists():
        raise FileNotFoundError(f"Markdown file not found: {src}")

    options = PreprocessOptions(continue_on_error=continue_on_error, embed_errors=embed_errors)

    preprocess_dir.mkdir(parents=True, exist_ok=True)
    dst = preprocess_dir / src.name
    terminal.info(f"{src} -> {dst}", prefix="[preprocess]")
    return preprocess_file(src, dst, options=options)

