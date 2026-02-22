#!/bin/bash

# --- CONFIGURATION ---
VENV_PYTHON="/home/nick/bookLayout/.venv/bin/python3"
PORT=8000
TARGET_URL="http://localhost:$PORT"
DEBUG_PORT=9222
USER_DATA="/tmp/chrome-debug"

# NEW: Automatically kill any old server on this port before starting
fuser -k $PORT/tcp 2>/dev/null

# 1. Start the Web Server
$VENV_PYTHON -m http.server $PORT --directory ./ &
SERVER_PID=$!

# 2. Launch Chrome with SECURITY UNLOCKED
if ! lsof -i:$DEBUG_PORT > /dev/null; then
    google-chrome \
      --remote-debugging-port=$DEBUG_PORT \
      --user-data-dir="$USER_DATA" \
      --remote-allow-origins="*" \
      --no-first-run \
      --no-default-browser-check \
      "$TARGET_URL" &
    sleep 2
fi

# 3. Watcher with FILE FILTERING (Regex for .md and .css)
echo "Watching for changes to .md and .css files..."
inotifywait -m -r \
	-e modify -e move -e delete -e close_write \
	"./" --format '%w%f' \
	| while read FILE
do
    # Only proceed if the file ends in .md or .css
    if [[ "$FILE" =~ \.(md|css)$ ]]; then
        sleep 0.2
        echo "File updated: $FILE. Signaling Chrome..."
        
        WS_URL=$(curl -s "http://localhost:$DEBUG_PORT/json" | jq -r ".[] | select(.url | contains(\"$TARGET_URL\")) | .webSocketDebuggerUrl" | head -n 1)

        if [ -n "$WS_URL" ] && [ "$WS_URL" != "null" ]; then
            $VENV_PYTHON chrome_trigger.py "$WS_URL"
        fi
    fi
done

trap "kill $SERVER_PID" EXIT

