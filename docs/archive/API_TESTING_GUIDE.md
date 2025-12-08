# API Testing Guide

## Quick Start

This guide explains how to test the FastAPI + Celery video keyframe extraction system.

## Prerequisites

1. **Redis** must be running (for Celery broker/backend)
2. **Python virtual environment** activated
3. **Dependencies installed**

## Starting the Services

You need **3 terminals** to run the complete system:

### Terminal 1: Start Redis

```bash
# If using Homebrew on macOS
redis-server

# Or using Docker
docker run -d -p 6379:6379 redis:latest
```

### Terminal 2: Start FastAPI Server

```bash
cd /Users/wangzq/VsCodeProjects/key-face-frame
source .venv/bin/activate
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

Access API docs at: http://localhost:8000/docs

### Terminal 3: Start Celery Worker

```bash
cd /Users/wangzq/VsCodeProjects/key-face-frame
source .venv/bin/activate
celery -A backend.workers.tasks worker --loglevel=info
```

You should see:
```
[tasks]
  . backend.workers.tasks.process_video_task

[INFO/MainProcess] Connected to redis://localhost:6379/0
[INFO/MainProcess] Ready to receive tasks
```

## Testing the API

### 1. Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "healthy"}
```

### 2. Upload Video

```bash
# Upload the test video with custom parameters
curl -X POST "http://localhost:8000/api/videos/upload" \
  -F "file=@WanAnimate_00001_p84-audio_gouns_1765004610.mp4" \
  -F "sample_rate=2" \
  -F "max_frames=50" \
  -F "confidence_threshold=0.6"
```

Expected response:
```json
{
  "video_id": "abc123-uuid-here",
  "filename": "WanAnimate_00001_p84-audio_gouns_1765004610.mp4",
  "status": "pending",
  "message": "Video queued for processing. Use video_id 'abc123-uuid-here' to check status."
}
```

**Important:** Save the `video_id` from the response!

### 3. Check Processing Status

Replace `{video_id}` with the actual ID from step 2:

```bash
curl http://localhost:8000/api/videos/{video_id}/status
```

**While processing:**
```json
{
  "video_id": "abc123-uuid-here",
  "filename": "WanAnimate_00001_p84-audio_gouns_1765004610.mp4",
  "status": "processing",
  "progress": 50,
  "stage": "detection",
  "created_at": "2025-12-07T14:30:00",
  "started_at": "2025-12-07T14:30:01",
  ...
}
```

**After completion:**
```json
{
  "video_id": "abc123-uuid-here",
  "filename": "WanAnimate_00001_p84-audio_gouns_1765004610.mp4",
  "status": "completed",
  "progress": 100,
  "stage": "complete",
  "total_frames": 300,
  "total_detections": 150,
  "keyframes_extracted": 25,
  "processing_time_seconds": 12.5,
  "output_dir": "/Users/wangzq/VsCodeProjects/key-face-frame/output/video-abc123-uuid-here",
  "metadata_path": "/Users/wangzq/VsCodeProjects/key-face-frame/output/video-abc123-uuid-here/metadata.json",
  "keyframes": [
    {
      "frame_index": 10,
      "timestamp": 0.33,
      "score": 0.95,
      "bbox": [100, 100, 200, 300],
      "filename": "keyframe_0010.jpg"
    },
    ...
  ],
  "created_at": "2025-12-07T14:30:00",
  "started_at": "2025-12-07T14:30:01",
  "completed_at": "2025-12-07T14:30:13"
}
```

### 4. Get Keyframes

```bash
curl http://localhost:8000/api/videos/{video_id}/keyframes
```

Expected response:
```json
{
  "video_id": "abc123-uuid-here",
  "count": 25,
  "keyframes": [
    {
      "frame_index": 10,
      "timestamp": 0.33,
      "score": 0.95,
      "bbox": [100, 100, 200, 300],
      "filename": "keyframe_0010.jpg"
    },
    ...
  ],
  "output_dir": "/Users/wangzq/VsCodeProjects/key-face-frame/output/video-abc123-uuid-here"
}
```

## Verify Output Files

After processing completes, check the output directory:

```bash
ls -la output/video-{video_id}/keyframes/
```

You should see:
- `keyframe_0001.jpg`
- `keyframe_0002.jpg`
- ... (JPEG images of extracted keyframes)

And metadata:
```bash
cat output/video-{video_id}/metadata.json
```

## Using the Interactive API Docs

Visit http://localhost:8000/docs for Swagger UI where you can:
- Test all endpoints interactively
- Upload files via web interface
- See request/response schemas
- Try different parameter combinations

## Error Handling

### Invalid file type:
```bash
curl -X POST "http://localhost:8000/api/videos/upload" \
  -F "file=@test.txt"
```
Response (400):
```json
{
  "detail": "Invalid file type. Allowed: .mp4, .mov, .avi, .mkv"
}
```

### Video not found:
```bash
curl http://localhost:8000/api/videos/nonexistent-id/status
```
Response (404):
```json
{
  "detail": "Video not found: nonexistent-id"
}
```

### Validation error:
```bash
curl -X POST "http://localhost:8000/api/videos/upload" \
  -F "file=@video.mp4" \
  -F "sample_rate=99"  # Too high (max is 10)
```
Response (422):
```json
{
  "detail": [
    {
      "loc": ["body", "sample_rate"],
      "msg": "ensure this value is less than or equal to 10",
      "type": "value_error.number.not_le"
    }
  ]
}
```

## Running Automated Tests

```bash
# All API tests (12 tests)
pytest tests/unit/api/test_video_routes.py -v

# All worker tests (7 tests)
pytest tests/unit/workers/test_tasks.py -v

# All tests with coverage
pytest tests/unit/ -v --cov=backend
```

## Monitoring

### Check Celery Task Queue

```bash
# In Python shell
python
>>> from backend.workers.tasks import celery_app
>>> celery_app.control.inspect().active()
>>> celery_app.control.inspect().stats()
```

### Check Database

```bash
# View database records
sqlite3 keyframe.db
sqlite> SELECT id, filename, status, progress FROM videos;
```

## Troubleshooting

### Redis not running
```
Error: [Errno 61] Connection refused
```
Solution: Start Redis server

### Celery worker not running
Uploads succeed but status stays at "pending"
Solution: Start Celery worker in Terminal 3

### Port already in use
```
ERROR:    [Errno 48] Address already in use
```
Solution: Use different port or kill existing process
```bash
lsof -ti:8000 | xargs kill -9
```

## Success Criteria Checklist

- [x] Health endpoint returns 200
- [x] Can upload video via curl
- [x] Video queued in database with "pending" status
- [x] Celery task starts processing
- [x] Status endpoint shows real-time progress
- [x] Processing completes successfully
- [x] Keyframes saved to output directory
- [x] Metadata JSON created
- [x] Status endpoint returns complete results
- [x] Keyframes endpoint returns image paths
- [x] Error handling returns proper HTTP codes
- [x] All API tests pass (12/12)

## Next Steps

After backend verification:
1. Frontend integration (lower priority per user requirements)
2. Add authentication/authorization
3. Deploy to production environment
4. Add S3 storage for keyframes
5. Implement video streaming endpoints
