#!/bin/bash

# Configuration
INPUT_MD="magazine.md"
OUTPUT_HTML="preview.html"
STYLE_CSS="magazine.css"

# Ensure inotify-tools is installed
if ! command -v inotifywait &> /dev/null; then
    echo "Please install inotify-tools: sudo apt install inotify-tools"
    exit 1
fi

echo "Watching $INPUT_MD for changes..."

# Start the Watch Loop
while true; do
    # Wait for the file to be written/closed (e.g., :w in vi)
    inotifywait -e close_write "$INPUT_MD" "$STYLE_CSS"
    
    # Trigger the Python HTML Generator
    python3 md2html.py -i "$INPUT_MD" -o "$OUTPUT_HTML" -c "$STYLE_CSS"
    
    echo "[$(date +%T)] HTML Updated. Daemon will now sync PDF."
done


