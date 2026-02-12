from __future__ import annotations

import html
from pathlib import Path

from .config import require_nonempty


def load_template(path: Path) -> str:
    """Load an HTML template file."""
    if not path.exists():
        raise FileNotFoundError(f"Template file not found: {path}")
    return path.read_text(encoding="utf-8")


def wrap_in_document_shell(
    *,
    body_html: str,
    title: str,
    css_href: str,
    js_href: str,
    template_path: Path,
) -> str:
    """
    Substitute placeholders into the template.

    Required placeholders:
      {{title}}, {{css}}, {{dev_js}}, {{body}}
    """
    template = load_template(template_path)

    css_href = require_nonempty("css", css_href)
    js_href = require_nonempty("dev_js", js_href)

    return (
        template
        .replace("{{title}}", html.escape(title, quote=True))
        .replace("{{css}}", css_href)
        .replace("{{dev_js}}", js_href)
        .replace("{{body}}", body_html)
    )

