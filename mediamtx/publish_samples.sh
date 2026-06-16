#!/bin/bash
# Publish sample video clips to MediaMTX as RTSP streams

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
SAMPLES_DIR="$PROJECT_DIR/samples"

# Configuration
MEDIAMTX_HOST="${MEDIAMTX_HOST:-localhost}"
MEDIAMTX_PORT="${MEDIAMTX_PORT:-8554}"

# Check for sample videos
if [ ! -d "$SAMPLES_DIR" ] || [ -z "$(ls "$SAMPLES_DIR"/*.mp4 2>/dev/null)" ]; then
    echo "No sample .mp4 files found in $SAMPLES_DIR"
    echo "Create or add sample videos first."
    exit 1
fi

# Function to publish a single sample
publish_sample() {
    local sample_file="$1"
    local camera_id="$2"
    local rtsp_url="rtsp://$MEDIAMTX_HOST:$MEDIAMTX_PORT/$camera_id"

    echo "Publishing $sample_file to $rtsp_url"

    # Use ffmpeg to loop the sample video and push to RTSP
    ffmpeg -re \
        -stream_loop -1 \
        -i "$sample_file" \
        -c:v copy \
        -c:a copy \
        -f rtsp \
        "$rtsp_url" &

    local pid=$!
    echo "Published $camera_id (PID: $pid)"
}

# Publish samples to cam01 and cam02
SAMPLES=($(ls "$SAMPLES_DIR"/*.mp4 2>/dev/null || echo ""))

if [ ${#SAMPLES[@]} -eq 0 ]; then
    echo "No sample files found"
    exit 1
fi

# Publish first sample to cam01
publish_sample "${SAMPLES[0]}" "cam01"

# If we have a second sample, publish to cam02, otherwise reuse the first
if [ ${#SAMPLES[@]} -ge 2 ]; then
    publish_sample "${SAMPLES[1]}" "cam02"
else
    publish_sample "${SAMPLES[0]}" "cam02"
fi

echo "Sample feeds are being published to:"
echo "  cam01: rtsp://$MEDIAMTX_HOST:$MEDIAMTX_PORT/cam01"
echo "  cam02: rtsp://$MEDIAMTX_HOST:$MEDIAMTX_PORT/cam02"
echo ""
echo "Press Ctrl+C to stop streaming"

# Wait for background jobs
wait
