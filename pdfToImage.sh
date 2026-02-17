#!/bin/bash
#
# create an png image of the selected page from a pdf
#     this script does nothing the original script doesnt do
#     its just an aide memoire
#     pdftoppm -f <pagenum> -l <pagenum> -png -r <resolution> <infile> <outfile>

# Default values
PAGE_NUM=1
RESOLUTION=300

# Help function
usage() {
    echo "Usage: $(basename "$0") [OPTIONS] <input_file> <output_file>"
    echo
    echo "Arguments:"
    echo "  input_file          Path to the source file"
    echo "  output_file         Path to the destination file"
    echo
    echo "Options:"
    echo "  -p, --page-num NUM  Specify page number (Default: 1)"
    echo "  -r, --resolution R  Specify resolution (Default: 300)"
    echo "                      Keywords: 'screen' = 96, 'print' = 300"
    echo "  -h, --help          Display this help message"
    echo
    echo "Example:"
    echo "  $(basename "$0") -p 5 -r screen input.pdf output.png"
    exit 1
}

# Parse options
while [[ $# -gt 0 ]]; do
    case "$1" in
        -p|--page-num)
            PAGE_NUM="$2"
            shift 2
            ;;
        -r|--resolution)
            case "$2" in
                screen) RESOLUTION=96 ;;
                print)  RESOLUTION=300 ;;
                *)      RESOLUTION="$2" ;;
            esac
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        -*) # Handle unknown options
            echo "Unknown option: $1"
            usage
            ;;
        *) # First non-option argument is input_file, second is output_file
            if [ -z "$INPUT_FILE" ]; then
                INPUT_FILE="$1"
            elif [ -z "$OUTPUT_FILE" ]; then
                OUTPUT_FILE="$1"
            else
                echo "Error: Too many arguments."
                usage
            fi
            shift
            ;;
    esac
done

# Check if required positional arguments are present
if [ -z "$INPUT_FILE" ] || [ -z "$OUTPUT_FILE" ]; then
    echo "Error: Missing input or output file."
    usage
fi

# --- Your script logic starts here ---
echo "Extracting page ${PAGE_NUM} with resolution ${RESOLUTION} dpi"
echo "    from: ${INPUT_FILE}"
echo "    to: ${OUTPUT_FILE}"

pdftoppm -f "${PAGE_NUM}" -l "${PAGE_NUM}" -png -r "${RESOLUTION}" "${INPUT_FILE}" "${OUTPUT_FILE}"


#eg
#pdftoppm -f 3 -l 3 -png -r 300 '/home/nick/Rpgs/Shadowdark/Shadowdark RPG - V4-8-PURCHASED.pdf' out.png
