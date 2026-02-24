#!/bin/bash
# $1 is an optional initial url

# --- 0. Load Configuration ---
CONFIG_FILE="config.json"

# Extracting values from JSON
. get_config.sh "${CONFIG_FILE}"

# if $1 is given use it for target url
if [[ -n "$1" && "$1" != -* ]]; then
	TARGET_URL="${TARGET_URL}/${1}"
fi
echo "TARGET_URL=$TARGET_URL"

# --- 1. Cleanup & Server ---
fuser -k $SERVER_PORT/tcp 2>/dev/null

$VENV_PYTHON -m http.server $SERVER_PORT --directory ./ > ${SERVER_LOG} 2>&1 &
SERVER_PID=$!

# --- 2. Launch Chrome (Silencing DEPRECATED_ENDPOINT) ---
# Redirecting 2> /dev/null hides all those internal Google API errors
if ! lsof -i:$DEBUG_PORT > /dev/null; then
    echo "Launching Chrome (Logs Silenced)..."
    google-chrome \
      --remote-debugging-port=$DEBUG_PORT \
      --user-data-dir="$USER_DATA" \
      --remote-allow-origins="*" \
      --no-first-run \
      --no-default-browser-check \
      "$TARGET_URL" > /dev/null 2>&1 &
    sleep 2
fi

# --- 3. Watcher ---
echo "Watching $WATCH_DIRS for changes to $EXT_REGEX..."

inotifywait -m -r -e modify -e move -e delete -e close_write $WATCH_DIRS --format '%w%f' | while read FILE
do
    if [[ "$FILE" =~ $EXT_REGEX ]]; then
        # Debounce to prevent double-hits
        sleep $DEBOUNCE
        
        echo "Change detected: $FILE. Signaling Chrome..."
        
        # Get WS URL
        WS_URL=$(curl -s "http://localhost:$DEBUG_PORT/json" | jq -r ".[] | select(.url | contains(\"$TARGET_URL\")) | .webSocketDebuggerUrl" | head -n 1)

        if [ -n "$WS_URL" ] && [ "$WS_URL" != "null" ]; then
            $VENV_PYTHON chrome_trigger.py "$WS_URL"
        fi
    fi
done

trap "kill $SERVER_PID" EXIT

