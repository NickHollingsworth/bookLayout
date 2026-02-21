import argparse
import sys
from markdown_it import MarkdownIt
from mdit_py_plugins.front_matter import front_matter_plugin
from mdit_py_plugins.attrs import attrs_plugin
from mdit_py_plugins.container import container_plugin

def main():
    parser = argparse.ArgumentParser(description="Magazine HTML Generator")
    parser.add_argument("-i", "--input", required=True, help="Input Markdown file")
    parser.add_argument("-o", "--output", required=True, help="Output HTML file")
    # This was the missing line causing the AttributeError
    parser.add_argument("-c", "--css", default="magazine.css", help="CSS file to link")
    
    args = parser.parse_args()

    # Initialize parser with all required plugins
    md = (
        MarkdownIt("commonmark", {"typographer": True})
        .use(front_matter_plugin)
        .use(attrs_plugin)
        .use(container_plugin, name="magazine-page")
        .use(container_plugin, name="sidebar") # Added for your sidebar grid
    )

    try:
        with open(args.input, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: {args.input} not found.")
        sys.exit(1)

    env = {}
    html_body = md.render(content, env)
    
    # Extract title from YAML front-matter if it exists
    meta = env.get("front_matter", {})
    title = meta.get("title", "Magazine Preview")

    # Wrap in HTML5 boilerplate and link the CSS
    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <link rel="stylesheet" href="{args.css}">
</head>
<body>
{html_body}
</body>
</html>"""

    with open(args.output, 'w') as f:
        f.write(full_html)
    
    print(f"[{args.input}] -> [{args.output}] using style [{args.css}]")

if __name__ == "__main__":
    main()

