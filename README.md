# Text → Markdown → HTML Viewer/Builder

This project lets you:

- Write plain text files (treated as **GitHub-flavoured Markdown**).
- Automatically build them into HTML files using a shared HTML template.
- View the generated HTML in a browser.
- Optionally run in a “dev” mode where:
  - Saving a `.txt` file triggers a rebuild (via a watcher).
  - The browser auto-reloads the page while preserving scroll position.
- Keep the HTML as a permanent, debug-friendly artifact that can be printed to PDF.

The core pipeline:

src/*.txt  --(Markdown + template)-->  build/*.html  -->  browser / PDF

# Setup

```
cd /path/to/project

# Create the virtual environment
python3 -m venv .venv

# Activate it (Bash / Zsh)
source .venv/bin/activate

pip install \
  markdown-it-py \
  mdit-py-plugins \
  linkify-it-py \
  uc-micro-py \
  watchdog
```

# Auto browser reload

dev-reload.js is a small script that automatically reloads the page if its changed:

. Checks the URL for ?dev=1.

. If present, periodically checks the current page’s headers (e.g. Last-Modified).

. If the file has changed, it remembers scroll position, reloads the page, and restores scroll.

This lets you see rebuilt HTML as soon as build.py writes it, without manual refresh.

The HTML template must include:
```
<script src="{{dev_js}}" defer></script>
```

# Building the html

With the virtual environment activated, from the project root:

To build all documents once;
'''
python build.py
'''
This reads all src/*.txt and generates corresponding build/*.html.

To build one document
'''
python build.py content
'''
This builds only src/content.txt → build/content.html.

## Useful command-line options

--src-dir – where to read .txt files from (default: src).

--build-dir – where to write .html files (default: build).

--css – path/URL used in <link rel="stylesheet" href="...">
Default: ../style.css (correct when serving the project root).

--dev-js – path/URL to dev-reload.js used in <script src="...">
Default: ../dev-reload.js.

--template – path to HTML template (default: templates/page.html).

Example overriding the template directory:

python build.py --template other-templates/alt-page.html

# Watch mode (auto rebuild on save)

To rebuild HTML when you save a .txt file, run:
```
python build.py --watch
```

This:

. Watches the src/ directory for changes to *.txt.

. Rebuilds only the changed file into build/ when it’s modified.

. You will typically run this in one terminal, and the HTTP server (below) in another.

# Serving the files for browser viewing

The simplest option is Python’s built-in HTTP server.

From the project root:
```
python -m http.server 8000
```

Then in your browser:

Stable (no auto-reload): http://localhost:8000/build/content.html

Dev mode (auto-reload, scroll preserved): http://localhost:8000/build/content.html?dev=1

