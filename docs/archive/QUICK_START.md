# Quick Start Guide

## 1-Minute Setup

### Start All Services (3 Terminals)

**Terminal 1: Redis**
```bash
redis-server
```

**Terminal 2: FastAPI**
```bash
cd /Users/wangzq/VsCodeProjects/key-face-frame
source .venv/bin/activate
uvicorn backend.main:app --reload
```

**Terminal 3: Celery**
```bash
cd /Users/wangzq/VsCodeProjects/key-face-frame
source .venv/bin/activate
celery -A backend.workers.tasks worker --loglevel=info
```

## Test the API

### Option 1: Automated Test (Recommended)
```bash
./test_api.sh
```

### Option 2: Manual curl Commands

**1. Health Check**
```bash
curl http://localhost:8000/health
```

**2. Upload Video**
```bash
curl -X POST "http://localhost:8000/api/videos/upload" \
  -F "file=@WanAnimate_00001_p84-audio_gouns_1765004610.mp4" \
  -F "sample_rate=2" \
  -F "max_frames=50"
```
Save the `video_id` from response!

**3. Check Status**
```bash
# Replace {video_id} with actual ID
curl http://localhost:8000/api/videos/{video_id}/status
```

**4. Get Keyframes (after completion)**
```bash
curl http://localhost:8000/api/videos/{video_id}/keyframes
```

### Option 3: Interactive API Docs
Open browser: http://localhost:8000/docs

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/videos/upload` | Upload video & start processing |
| GET | `/api/videos/{id}/status` | Get processing status |
| GET | `/api/videos/{id}/keyframes` | Get extracted keyframes |

## Configuration Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `sample_rate` | int | 1 | 1-10 | Frame sampling rate |
| `max_frames` | int | 100 | 10-500 | Max keyframes to extract |
| `confidence_threshold` | float | 0.5 | 0.1-0.9 | Detection confidence |

## Output Location

After processing, check:
```bash
ls -la output/video-{video_id}/keyframes/
cat output/video-{video_id}/metadata.json
```

## Troubleshooting

**Redis not running?**
```bash
# Install via Homebrew (macOS)
brew install redis
redis-server
```

**Port 8000 in use?**
```bash
# Use different port
uvicorn backend.main:app --reload --port 8001
```

**Dependencies missing?**
```bash
pip install fastapi uvicorn celery redis sqlalchemy pydantic-settings python-multipart
```

## Next Steps

- ✅ Backend complete - Test with `./test_api.sh`
- 🔲 Frontend integration (lower priority)
- 🔲 Production deployment

## Documentation

- **Full Testing Guide:** `API_TESTING_GUIDE.md`
- **Implementation Summary:** `API_IMPLEMENTATION_SUMMARY.md`
- **API Docs (Interactive):** http://localhost:8000/docs

## Support

Questions? Check the documentation files or run:
```bash
pytest tests/unit/api/ -v  # Run all API tests
```
