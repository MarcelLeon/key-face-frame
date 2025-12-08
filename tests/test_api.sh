#!/bin/bash
# API Testing Script
# Tests the complete video processing pipeline
#
# 配置视频文件的方法：
#   1. 环境变量: TEST_VIDEO_FILE="my_video.mp4" ./test_api.sh
#   2. 直接修改下面的默认值
#   3. 使用默认值: WanAnimate_00001_p84-audio_gouns_1765004610.mp4

set -e  # Exit on error

API_URL="http://localhost:8000"

# 从环境变量读取视频文件路径，如果未设置则使用默认值
VIDEO_FILE="${TEST_VIDEO_FILE:-WanAnimate_00001_p84-audio_gouns_1765004610.mp4}"

# 如果是相对路径，转换为绝对路径（基于项目根目录）
if [[ ! "$VIDEO_FILE" = /* ]]; then
    # 获取脚本所在目录（tests/）
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    # 获取项目根目录（tests 的父目录）
    PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
    # 构建绝对路径
    VIDEO_FILE="${PROJECT_ROOT}/${VIDEO_FILE}"
fi

echo "========================================="
echo "Key-Face-Frame API Test Script"
echo "========================================="
echo "Video file: $VIDEO_FILE"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test 1: Health Check
echo -e "${YELLOW}[Test 1/5]${NC} Testing health check endpoint..."
HEALTH_RESPONSE=$(curl -s "${API_URL}/health")
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo -e "${GREEN}✓ Health check passed${NC}"
else
    echo -e "${RED}✗ Health check failed${NC}"
    echo "Response: $HEALTH_RESPONSE"
    exit 1
fi
echo ""

# Test 2: Upload Video
echo -e "${YELLOW}[Test 2/5]${NC} Uploading video..."
if [ ! -f "$VIDEO_FILE" ]; then
    echo -e "${RED}✗ Video file not found: $VIDEO_FILE${NC}"
    exit 1
fi

UPLOAD_RESPONSE=$(curl -s -X POST "${API_URL}/api/videos/upload" \
    -F "file=@${VIDEO_FILE}" \
    -F "sample_rate=2" \
    -F "max_frames=50" \
    -F "confidence_threshold=0.6")

VIDEO_ID=$(echo "$UPLOAD_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('video_id', ''))" 2>/dev/null || echo "")

if [ -z "$VIDEO_ID" ]; then
    echo -e "${RED}✗ Video upload failed${NC}"
    echo "Response: $UPLOAD_RESPONSE"
    exit 1
fi

echo -e "${GREEN}✓ Video uploaded successfully${NC}"
echo "  Video ID: $VIDEO_ID"
echo ""

# Test 3: Check Status (initial)
echo -e "${YELLOW}[Test 3/5]${NC} Checking initial status..."
STATUS_RESPONSE=$(curl -s "${API_URL}/api/videos/${VIDEO_ID}/status")
STATUS=$(echo "$STATUS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', ''))" 2>/dev/null || echo "")

echo -e "${GREEN}✓ Status retrieved${NC}"
echo "  Status: $STATUS"
echo ""

# Test 4: Wait for Processing
echo -e "${YELLOW}[Test 4/5]${NC} Monitoring processing progress..."
MAX_ATTEMPTS=60
ATTEMPT=0
LAST_STATUS=""
LAST_PROGRESS=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    sleep 2
    STATUS_RESPONSE=$(curl -s "${API_URL}/api/videos/${VIDEO_ID}/status")
    CURRENT_STATUS=$(echo "$STATUS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', ''))" 2>/dev/null || echo "")
    CURRENT_PROGRESS=$(echo "$STATUS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('progress', 0))" 2>/dev/null || echo "0")
    CURRENT_STAGE=$(echo "$STATUS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('stage', 'N/A'))" 2>/dev/null || echo "N/A")

    if [ "$CURRENT_STATUS" != "$LAST_STATUS" ] || [ "$CURRENT_PROGRESS" != "$LAST_PROGRESS" ]; then
        echo "  Status: $CURRENT_STATUS | Progress: $CURRENT_PROGRESS% | Stage: $CURRENT_STAGE"
        LAST_STATUS="$CURRENT_STATUS"
        LAST_PROGRESS="$CURRENT_PROGRESS"
    fi

    if [ "$CURRENT_STATUS" = "completed" ]; then
        echo -e "${GREEN}✓ Processing completed${NC}"

        # Extract results
        TOTAL_FRAMES=$(echo "$STATUS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('total_frames', 'N/A'))" 2>/dev/null || echo "N/A")
        TOTAL_DETECTIONS=$(echo "$STATUS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('total_detections', 'N/A'))" 2>/dev/null || echo "N/A")
        KEYFRAMES=$(echo "$STATUS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('keyframes_extracted', 'N/A'))" 2>/dev/null || echo "N/A")
        PROC_TIME=$(echo "$STATUS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('processing_time_seconds', 'N/A'))" 2>/dev/null || echo "N/A")
        OUTPUT_DIR=$(echo "$STATUS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('output_dir', 'N/A'))" 2>/dev/null || echo "N/A")

        echo ""
        echo "  Results:"
        echo "  - Total frames: $TOTAL_FRAMES"
        echo "  - Total detections: $TOTAL_DETECTIONS"
        echo "  - Keyframes extracted: $KEYFRAMES"
        echo "  - Processing time: ${PROC_TIME}s"
        echo "  - Output directory: $OUTPUT_DIR"
        break
    elif [ "$CURRENT_STATUS" = "failed" ]; then
        echo -e "${RED}✗ Processing failed${NC}"
        ERROR_MSG=$(echo "$STATUS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('error_message', 'Unknown error'))" 2>/dev/null || echo "Unknown error")
        echo "  Error: $ERROR_MSG"
        exit 1
    fi

    ATTEMPT=$((ATTEMPT + 1))
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    echo -e "${RED}✗ Timeout waiting for processing${NC}"
    exit 1
fi
echo ""

# Test 5: Get Keyframes
echo -e "${YELLOW}[Test 5/5]${NC} Retrieving keyframes..."
KEYFRAMES_RESPONSE=$(curl -s "${API_URL}/api/videos/${VIDEO_ID}/keyframes")
KEYFRAME_COUNT=$(echo "$KEYFRAMES_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('count', 0))" 2>/dev/null || echo "0")

if [ "$KEYFRAME_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓ Keyframes retrieved${NC}"
    echo "  Count: $KEYFRAME_COUNT keyframes"

    # Show first keyframe details
    echo ""
    echo "  First keyframe:"
    echo "$KEYFRAMES_RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data.get('keyframes'):
    kf = data['keyframes'][0]
    print(f\"    - Frame: {kf.get('frame_index')}\"  )
    print(f\"    - Timestamp: {kf.get('timestamp'):.2f}s\")
    print(f\"    - Score: {kf.get('score'):.2f}\")
    print(f\"    - Filename: {kf.get('filename')}\")
" 2>/dev/null
else
    echo -e "${RED}✗ No keyframes found${NC}"
fi
echo ""

# Summary
echo "========================================="
echo -e "${GREEN}All tests passed!${NC}"
echo "========================================="
echo ""
echo "Summary:"
echo "  Video ID: $VIDEO_ID"
echo "  Keyframes: $KEYFRAME_COUNT"
echo "  Output: $OUTPUT_DIR"
echo ""
echo "View keyframes:"
echo "  ls -la $OUTPUT_DIR/keyframes/"
echo ""
echo "View metadata:"
echo "  cat $OUTPUT_DIR/metadata.json | python3 -m json.tool"
echo ""
