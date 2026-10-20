#!/bin/sh
# Run the packager from anywhere: tools/vnpack.sh path/to/project -o build
PYTHONPATH="$(cd "$(dirname "$0")" && pwd)${PYTHONPATH:+:$PYTHONPATH}" exec python3 -m vnpack "$@"
