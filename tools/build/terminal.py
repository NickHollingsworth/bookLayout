"""
Minimal terminal output helpers.

Design goals:
- No external dependencies
- Respect NO_COLOR
- Only emit ANSI codes when output is a TTY
- Prefer semantic emphasis (bold + reverse) over hard-coded colours
- Centralize message composition (prefix/level/where) to avoid duplication
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import TextIO


@dataclass
class _TerminalConfig:
    verbose: bool = False


_config = _TerminalConfig()


def configure(*, verbose: bool) -> None:
    _config.verbose = bool(verbose)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _supports_ansi(stream: TextIO) -> bool:
    if "NO_COLOR" in os.environ:
        return False
    if not stream.isatty():
        return False
    term = os.environ.get("TERM")
    if not term or term == "dumb":
        return False
    return True


def _format_emphasis(msg: str) -> str:
    bold = "\033[1m"
    reverse = "\033[7m"
    reset = "\033[0m"
    return f"{bold}{reverse}{msg}{reset}"


def _dedupe_where(msg: str, where: str | None) -> str:
    """
    If caller passes where=..., avoid output like:
      WHERE: WHERE: message
    by stripping one copy from msg if it already begins with it.
    """
    if not where:
        return msg
    prefix = f"{where}:"
    if msg.startswith(prefix):
        # Strip exactly one leading "WHERE:" and optional following whitespace
        rest = msg[len(prefix):].lstrip()
        return rest
    return msg


def _emit(
    level: str,
    msg: str,
    *,
    where: str | None,
    prefix: str,
    stream: TextIO,
    emphasize: bool,
) -> None:
    msg = _dedupe_where(str(msg), where)

    if where:
        full = f"{prefix} {level} {where}: {msg}"
    else:
        full = f"{prefix} {level}: {msg}"

    if emphasize and _supports_ansi(stream):
        full = _format_emphasis(full)

    print(full, file=stream)


# ---------------------------------------------------------------------------
# Public API (same signature)
# ---------------------------------------------------------------------------

def error(msg: str, *, where: str | None = None, prefix: str = "[build]") -> None:
    _emit("ERROR", msg, where=where, prefix=prefix, stream=sys.stderr, emphasize=True)


def warn(msg: str, *, where: str | None = None, prefix: str = "[build]") -> None:
    _emit("WARNING", msg, where=where, prefix=prefix, stream=sys.stderr, emphasize=True)


def info(msg: str, *, where: str | None = None, prefix: str = "[build]") -> None:
    if not _config.verbose:
        return
    _emit("INFO", msg, where=where, prefix=prefix, stream=sys.stdout, emphasize=False)

