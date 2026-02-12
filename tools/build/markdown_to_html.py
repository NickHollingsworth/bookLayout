from __future__ import annotations

from markdown_it import MarkdownIt
from mdit_py_plugins.footnote import footnote_plugin
from mdit_py_plugins.deflist import deflist_plugin
from mdit_py_plugins.tasklists import tasklists_plugin
from mdit_py_plugins.attrs import attrs_plugin, attrs_block_plugin


def create_markdown_parser() -> MarkdownIt:
    """
    MarkdownIt parser configured for GitHub-flavoured style Markdown.

    - Base: "gfm-like"
    - linkify: auto-detect bare URLs
    - typographer: smart quotes, dashes
    - plugins: footnotes, deflists, tasklists, attrs
    """
    md = MarkdownIt(
        "gfm-like",
        {
            "linkify": True,
            "typographer": True,
        },
    )

    md.use(footnote_plugin)
    md.use(deflist_plugin)
    md.use(tasklists_plugin, enabled=False, label=True, label_after=False)
    md.use(attrs_plugin)
    md.use(attrs_block_plugin)

    return md


# Create once; reuse for all renders
_MD = create_markdown_parser()


def render_markdown_to_html(markdown_text: str) -> str:
    """Render Markdown text to HTML."""
    return _MD.render(markdown_text)

