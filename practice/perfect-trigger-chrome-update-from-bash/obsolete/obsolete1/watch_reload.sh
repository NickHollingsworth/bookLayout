#!/bin/bash

# --- CONFIGURATION ---
WATCH_DIR="./"                               # Folder to monitor
TARGET_URL="localhost:8000"                  # The URL of your project tab
DEBUG_PORT=9222                              # Chrome's debugging port
VENV_PYTHON="./venv/bin/python3"             # PATH TO YOUR VENV PYTHON
DEBOUNCE_DELAY=0.2                           # Delay to prevent "double-reloads"

echo "Watching $WATCH_DIR... (Target: $TARGET_URL)"

# 1. Use inotifywait to watch for file saves (close_write)
inotifywait -m -r -e close_write "$WATCH_DIR" --format '%w%f' | while read FILE
do
    # 2. DEBOUNCE: Wait a tiny bit for the file system to settle
    sleep $DEBOUNCE_DELAY

    echo "File changed: $FILE. Finding Chrome tab..."

    # 3. Ask Chrome for the list of tabs and extract the WebSocket URL for our target
    # Uses 'jq' to parse the JSON and find the URL that contains our project address
    WS_URL=$(curl -s "http://localhost:$DEBUG_PORT/json" | \
             jq -r ".[] | select(.url | contains(\"$TARGET_URL\")) | .webSocketDebuggerUrl" | head -n 1)

    if [ -n "$WS_URL" ] && [ "$WS_URL" != "null" ]; then
        # 4. Trigger the Python agent using your VENV's python
        $VENV_PYTHON chrome_trigger.py "$WS_URL"
    else
        echo "Error: Matching Chrome tab not found at http://localhost:$DEBUG_PORT/json"
    fi
done

