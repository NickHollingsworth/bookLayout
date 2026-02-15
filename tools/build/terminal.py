"""
Minimal terminal formatting helpers.

Design goals:
- No external dependencies
- Respect NO_COLOR
- Only emit ANSI codes when output is a TTY
- Prefer semantic emphasis (bold + reverse) over hard-coded colours
"""

from __future__ import annotations

import os
import sys
from typing import TextIO
from dataclasses import dataclass

@dataclass
class _TerminalConfig:
    verbose: bool = False

_config = _TerminalConfig()

def configure(*, verbose: bool) -> None:
    _config.verbose = verbose


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _supports_ansi(stream: TextIO) -> bool:
    """
    Return True if we should emit ANSI sequences to this stream.
    """
    if "NO_COLOR" in os.environ:
        return False

    if not stream.isatty():
        return False

    term = os.environ.get("TERM")
    if not term or term == "dumb":
        return False

    return True


def _format_emphasis(msg: str) -> str:
    """
    Format a message with bold + reverse video.
    """
    bold = "\033[1m"
    reverse = "\033[7m"
    reset = "\033[0m"
    return f"{bold}{reverse}{msg}{reset}"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def info(msg: str) -> None:
    """
    Print informational message to stdout.
    """
    if _config.verbose:
        print(msg, file=sys.stdout)

def error(msg: str) -> None:
    """
    Print an error message to stderr in highlighted form.
    """
    if _supports_ansi(sys.stderr):
        print(_format_emphasis(msg), file=sys.stderr)
    else:
        print(msg, file=sys.stderr)


def warn(msg: str) -> None:
    """
    Print a warning message to stderr (bold only).
    """
    if _supports_ansi(sys.stderr):
        bold = "\033[1m"
        reset = "\033[0m"
        print(f"{bold}{msg}{reset}", file=sys.stderr)
    else:
        print(msg, file=sys.stderr)


