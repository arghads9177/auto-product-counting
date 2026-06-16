#!/bin/bash
# Start MediaMTX native binary with configuration

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Starting MediaMTX..."
echo "Config: $SCRIPT_DIR/mediamtx.yml"

# Download MediaMTX if not present (optional, assumes binary is in PATH or current directory)
if ! command -v mediamtx &> /dev/null; then
    echo "MediaMTX not found in PATH"
    echo "Download from: https://github.com/bluenviron/mediamtx/releases"
    echo "Or add to your PATH"
    exit 1
fi

# Run MediaMTX with the config file
mediamtx "$SCRIPT_DIR/mediamtx.yml"
