#!/bin/bash

# Define actions in a single place for easy maintenance
declare -A ACTIONS=(
    [c]="Edit config"
    [s]="Start server using config"
    [b]="Start browser using config and focus on this files output"
    [p]="Start pdf viewer using config and focus on this files output"
    [r]="Refresh browser"
    [l]="Tail log"
    [f]="Focus browser and pdf viewer on this files output"
    [F]="Focus browser and pdf viewer on previous files output"
    [S]="Kill server"
    [B]="Kill browser"
    [P]="Kill pdf viewer"
    [L]="Clear log"
)

show_help() {
    echo "Usage: ./layout.sh [options/chars]"
    echo ""
    echo "Commands (can be bundled, e.g., 'srk' or '-srk'):"
    for key in "c" "s" "b" "p" "r" "l" "f" "F" "S" "B" "P" "L"; do
        printf "  %-3s %s\n" "$key" "${ACTIONS[$key]}"
    done
    echo "  -h, --help      Show this help"
}

# --- VALIDATION PHASE ---
validate_all() {
    for arg in "$@"; do
        case "$arg" in
            --help|-h) return 0 ;;
            --start-server|--kill-server|--start-browser|--kill-browser|--refresh|--log|--start-pdf|--kill-pdf|--focus-current|--focus-prev|--config|--clear-log) continue ;;
            -*) # Check bundled flags
                chars=${arg#-}
                for (( i=0; i<${#chars}; i++ )); do
                    char="${chars:$i:1}"
                    [[ -z "${ACTIONS[$char]}" ]] && return 1
                done
                ;;
            *) # Check bundled raw strings
                for (( i=0; i<${#arg}; i++ )); do
                    char="${arg:$i:1}"
                    [[ -z "${ACTIONS[$char]}" ]] && return 1
                done
                ;;
        esac
    done
    return 0
}

# Exit early if no args
[[ $# -eq 0 ]] && show_help && exit 0

# Run validation
if ! validate_all "$@"; then
    echo "Error: One or more invalid arguments detected."
    echo "No actions were performed. Use -h for a list of valid commands."
    exit 1
fi

# --- EXECUTION PHASE ---
# Only reached if all arguments passed validation
for arg in "$@"; do
    case "$arg" in
        --help|-h) show_help; exit 0 ;;
        --start-server)  
			echo "Action: ${ACTIONS[s]}" 
			;;
        --kill-server)   echo "Action: ${ACTIONS[S]}" ;;
        --start-browser) echo "Action: ${ACTIONS[b]}" ;;
        --kill-browser)  echo "Action: ${ACTIONS[B]}" ;;
        --refresh)       echo "Action: ${ACTIONS[r]}" ;;
        --log)           
			echo "Action: ${ACTIONS[l]}" 
			echo ""
			tail -20 /tmp/serve.log
			;;
        --start-pdf)     echo "Action: ${ACTIONS[p]}" ;;
        --kill-pdf)      echo "Action: ${ACTIONS[P]}" ;;
        --focus-current) echo "Action: ${ACTIONS[f]}" ;;
        --focus-prev)    echo "Action: ${ACTIONS[F]}" ;;
        --config)        echo "Action: ${ACTIONS[c]}" ;;
        --clear-log)     echo "Action: ${ACTIONS[C]}" ;;
        -*)
            chars=${arg#-}
            for (( i=0; i<${#chars}; i++ )); do echo "Action: ${ACTIONS[${chars:$i:1}]}"; done
            ;;
        *)
            for (( i=0; i<${#arg}; i++ )); do echo "Action: ${ACTIONS[${arg:$i:1}]}"; done
            ;;
    esac
done

