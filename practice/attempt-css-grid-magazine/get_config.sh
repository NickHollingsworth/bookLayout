# --- 0. Load Configuration ---
CONFIG_FILE="$1"

# Extracting values from JSON
VENV_PYTHON="/home/nick/bookLayout/.venv/bin/python3"
SERVER_PORT=$(jq -r '.server_port' $CONFIG_FILE)
SERVER_LOG=$(jq -r '.server_log' $CONFIG_FILE)
DEBUG_PORT=$(jq -r '.debug_port' $CONFIG_FILE)
TARGET_URL=$(jq -r '.target_url' $CONFIG_FILE)
USER_DATA=$(jq -r '.user_data' $CONFIG_FILE)
DEBOUNCE=$(jq -r '.debounce' $CONFIG_FILE)
WATCH_DIRS=$(jq -r '.watch_dirs | join(" ")' $CONFIG_FILE)
# Create a regex like \.(md|css|js|html)$ from the array
EXT_REGEX=$(jq -r '.file_extensions | join("|")' $CONFIG_FILE)
EXT_REGEX="\\.($EXT_REGEX)\$"

