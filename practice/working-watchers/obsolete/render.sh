#!/bin/bash

# Function to display usage and exit with a specific code
usage() {
    local exit_code=$1
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -i, --input FILE    Input Markdown file (required)"
    echo "  -o, --output FILE   Output HTML file (required)"
    echo "  -h, --help          Display this help message"
    echo ""
    echo "Example:"
    echo "  $0 -i article.md -o article.html"
    exit "$exit_code"
}

INPUT=""
OUTPUT=""

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    -i|--input)
      if [[ -z "$2" || "$2" == -* ]]; then echo "Error: -i requires an argument"; usage 1; fi
      INPUT="$2"
      shift 2
      ;;
    -o|--output)
      if [[ -z "$2" || "$2" == -* ]]; then echo "Error: -o requires an argument"; usage 1; fi
      OUTPUT="$2"
      shift 2
      ;;
    -h|--help)
      usage 0  # Success exit code for explicit help request
      ;;
    *)
      echo "Error: Unknown option $1"
      usage 1  # Error exit code for invalid options
      ;;
  esac
done

# Fail if required arguments are missing
if [[ -z "$INPUT" || -z "$OUTPUT" ]]; then
    echo "Error: Missing required arguments."
    usage 1
fi

# Call the python converter
python3 converter.py --input "$INPUT" --output "$OUTPUT"

