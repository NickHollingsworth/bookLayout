#!/bin/bash
#This script coordinates Pandoc, Chrome, and the Preflight checks.
# 1. Markdown -> HTML (Injects the JS checker)
pandoc spike.md --metadata-file=metadata.yaml --css style.css \
    --include-in-header=check.js -s -o preview.html

# 2. HTML -> PDF (Headless Chrome)
google-chrome --headless=new --disable-gpu --print-to-pdf=final.pdf preview.html

# 3. Preflight: Font Embedding Check
echo "--- PREFLIGHT: FONT CHECK ---"
gs -q -dNODISPLAY -dNODisplay -c "(final.pdf) (r) file runpdfbegin 1 1 pdfpagecount { pdfgetpage /Resources get /Font gets { exch == (Embedded: ) print dup /FontDescriptor known { /FontDescriptor get /FontFile known } { false } ifelse == } forall } for"

