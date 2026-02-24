#!/bin/bash
CONFIG_FILE="config.json"
VENV_PYTHON="/home/nick/bookLayout/.venv/bin/python3"

# 1. Define internal mapping from single char to long-form command
declare -A KEY_TO_LONG=(
    [c]="--show-config"      [C]="--edit-config"   
	[s]="--start-server"     [b]="--start-browser"    [w]="--start-watch-and-build"    [p]="--start-pdf-viewer"
	[r]="--refresh"       
	[l]="--show-log"         [L]="--clear-log"
    [f]="--focus-on-current" [F]="--focus-on-prev"
	[S]="--kill-server"      [B]="--kill-browser"     [W]="--kill-watch-and-build"    [P]="--kill-pdf-viewer"
)

# 2. Define descriptions for help and display
declare -A DESC=(
    ["--show-config"]="Show config"
    ["--edit-config"]="Edit config"
    ["--start-server"]="Start server using config"
    ["--start-browser"]="Start browser using config and focus output"
    ["--start-watch-and-build"]="Start watching files and build on change"
    ["--start-pdf-viewer"]="Start pdf viewer using config and focus output"
    ["--refresh"]="Refresh browser"
    ["--show-log"]="Tail log"
    ["--focus-on-current"]="Focus browser and pdf on this file"
    ["--focus-on-prev"]="Focus browser and pdf on previous file"
    ["--kill-server"]="Kill server"
    ["--kill-browser"]="Kill browser"
    ["--kill-watch-and-build"]="Stop watching files and building on change"
    ["--kill-pdf-viewer"]="Kill pdf viewer"
    ["--clear-log"]="Clear log"
)

show_help() {
    echo "Usage: ./layout.sh [options/chars]"
    echo ""
    echo "Commands (can be bundled like 'srk' or '-srk'):"
    # Sort keys for consistent help output
    for char in c s b w p r l f F S B W P L; do
        long=${KEY_TO_LONG[$char]}
        printf "  %-2s, %-16s %s\n" "$char" "$long" "${DESC[$long]}"
    done
    echo "  -h, --help             Show this help"
}

# --- EXPANSION & VALIDATION PHASE ---
FINAL_COMMANDS=()

expand_and_validate() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --help|-h) 
				show_help; 
				exit 0 
				;;
            --start-browser)
                FINAL_COMMANDS+=("--start-browser")
                # If the next arg doesn't start with '-', it's our URL
                if [[ -n "$2" && "$2" != -* ]]; then
                    FOCUS_URL="$2"
                    shift # consume the URL arg
                fi
                ;;
            --focus-on-current)
                FINAL_COMMANDS+=("--focus-on-current")
                # If the next arg doesn't start with '-', it's our URL
                if [[ -n "$2" && "$2" != -* ]]; then
                    FOCUS_URL="$2"
                    shift # consume the URL arg
                fi
                ;;
            --*) # Other direct long commands
                if [[ -n "${DESC[$1]}" ]]; then
                    FINAL_COMMANDS+=("$1")
                else
                    return 1
                fi
                ;;

			*) # Bundled chars or -flags
                chars=${1#-}
                for (( i=0; i<${#chars}; i++ )); do
                    char="${chars:$i:1}"
                    long=${KEY_TO_LONG[$char]}
                    if [[ -n "$long" ]]; then
                        FINAL_COMMANDS+=("$long")

                        # if passed s or f or b arg $2 may be present
                        if [[ "$char" == "f" || "$char" == "s" || "$char" == "b" ]]; then
                            if [[ -n "$2" && "$2" != -* ]]; then
                                if [[ "$char" == "s" ]]; then
                                    SERVER_PORT="$2"
                                else
                                    # Both 'f' and 'b' consume the URL/filename
                                    FOCUS_URL="$2"
                                fi
                                shift # This 'eats' the 'tmp' so the outer loop doesn't see it
                            fi
                        fi
                    else
                        return 1
                    fi
                done
                ;;

        esac
        shift # Move to next arg
    done
}


#expand_and_validate() {
#    for arg in "$@"; do
#        case "$arg" in
#            --help|-h) show_help; exit 0 ;;
#            --*) # Direct long command
#                if [[ -n "${DESC[$arg]}" ]]; then
#                    FINAL_COMMANDS+=("$arg")
#                else
#                    return 1
#                fi
#                ;;
#            *) # Bundled chars or -flags
#                chars=${arg#-}
#                for (( i=0; i<${#chars}; i++ )); do
#                    char="${chars:$i:1}"
#                    long=${KEY_TO_LONG[$char]}
#                    if [[ -n "$long" ]]; then
#                        FINAL_COMMANDS+=("$long")
#                    else
#                        return 1
#                    fi
#                done
#                ;;
#        esac
#    done
#}

# Exit if no args
[[ $# -eq 0 ]] && show_help && exit 0

# Run expansion
if ! expand_and_validate "$@"; then
    echo "Error: Invalid argument detected. No actions performed."
    echo "Run with -h for usage."
    exit 1
fi

# ====== EXECUTION PHASE ======

# load config from json
. get_config.sh ${CONFIG_FILE}

# iterate over the validated long-form commands
for cmd in "${FINAL_COMMANDS[@]}"; do
    echo "Action: ${DESC[$cmd]}"
    
    case "$cmd" in
        --show-config)
			echo ""
			echo "Showing Config File - ${CONFIG_FILE}"
			cat ${CONFIG_FILE}
            ;;
        --edit-config)
			echo ""
			echo "Editing Config File - ${CONFIG_FILE}"
			vi ${CONFIG_FILE}
            ;;
        --start-server)  
			echo ""
			echo "Starting server"
			echo "    on port: ${SERVER_PORT}"
			echo "    to log:  ${SERVER_LOG}"

			echo "===== `date` ===== Start Server =====" >> ${SERVER_LOG}
			$VENV_PYTHON -m http.server ${SERVER_PORT} \
				2>> ${SERVER_LOG} >> ${SERVER_LOG} & 
            ;;
        --start-browser)
            echo ""
            echo "Starting browser on: $FOCUS_URL"

			start_dev.sh ${FOCUS_URL}&

            ;;
		--start-watch-and-build)
			echo ""
			echo "to be implemented: --start-watch-and-build"
			exit 1
            ;;
        --start-pdf-viewer)
			echo ""
			echo "to be implemented: --start-pdf-viewer"
			exit 1
            ;;
        --refresh)
			echo ""
			echo "Refreshing Browser"
	
			WS_URL=$(curl -s localhost:${DEBUG_PORT}/json \
				| jq -r '.[0].webSocketDebuggerUrl')
			$VENV_PYTHON chrome_trigger.py "$WS_URL" reload

            ;;
        --show-log)           
			echo ""
			echo "Showing tail of server log"

			tail -20 ${SERVER_LOG}
            ;;

        --focus-on-current)
			# If FOCUS_URL is set, append it to TARGET_URL with a slash.
            # If not set, just use TARGET_URL.
            if [[ -n "$FOCUS_URL" ]]
			then
                URL_TO_USE="${TARGET_URL}/${FOCUS_URL}"
            else
                URL_TO_USE="${TARGET_URL}"
            fi

            echo ""
            echo "Focusing browser on: $URL_TO_USE"

            WS_URL=$(curl -s localhost:${DEBUG_PORT}/json \
                | jq -r '.[0].webSocketDebuggerUrl')
            
            if [[ -n "$WS_URL" && "$WS_URL" != "null" ]]; then
                $VENV_PYTHON chrome_trigger.py "$WS_URL" goto "$URL_TO_USE"
            else
                echo "Error: Browser not found on port ${DEBUG_PORT}"
            fi
			;;

        --focus-on-prev)
			echo ""
			echo "to be implemented: --focus-on-prev"
			exit 1
            ;;
        --kill-server)
			echo ""
			echo "Killing Server"

			echo "===== `date` ===== Kill Server =====" >> ${SERVER_LOG}
			fuser -k ${SERVER_PORT}/tcp #2>/dev/null
            ;;
        --kill-browser)
			echo ""
			echo "Killing Browser"

			WS_URL=$(curl -s localhost:${DEBUG_PORT}/json \
				| jq -r '.[0].webSocketDebuggerUrl')
			$VENV_PYTHON chrome_trigger.py "$WS_URL" close

            ;;
		--kill-watch-and-build)
			echo ""
			echo "to be implemented: --kill-watch-and-build"
			exit 1
            ;;
        --kill-pdf-viewer)
			echo ""
			echo "to be implemented: --kill-pdf-viewer"
			exit 1
            ;;
        --clear-log)
			echo ""
			echo "Clearing out server log"

			echo "===== `date` ===== Cleared Log =====" > ${SERVER_LOG}
            ;;
    esac
done

