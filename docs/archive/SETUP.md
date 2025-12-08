# Setup Guide - Key-Face-Frame

Complete installation and setup instructions for macOS (M4 Apple Silicon).

---

## Prerequisites

Before you begin, ensure you have the following installed:

### Required Software

- **Python 3.10+** (3.10, 3.11, or 3.12 recommended)
- **Redis Server** (for Celery task queue)
- **Git** (for cloning repository)

### Optional but Recommended

- **Homebrew** (macOS package manager)
- **FFmpeg** (for advanced video processing)

---

## Step 1: Install System Dependencies

### Install Homebrew (if not already installed)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Install Redis

```bash
brew install redis
```

### Install Python 3.10+ (if needed)

```bash
brew install python@3.10
```

### Verify Installation

```bash
python3 --version  # Should be 3.10+
redis-server --version  # Should show Redis version
```

---

## Step 2: Clone Repository

```bash
cd ~/VsCodeProjects
git clone <repository-url> key-face-frame
cd key-face-frame
```

---

## Step 3: Create Virtual Environment

### Create Virtual Environment

```bash
python3 -m venv .venv
```

### Activate Virtual Environment

```bash
source .venv/bin/activate
```

**Note**: You should see `(.venv)` prefix in your terminal prompt.

### Verify Activation

```bash
which python  # Should point to .venv/bin/python
```

---

## Step 4: Install Python Dependencies

### Install Production Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This installs:
- FastAPI (web framework)
- Celery (task queue)
- Redis (cache/broker)
- SQLAlchemy (database ORM)
- Ultralytics (YOLO)
- OpenCV (computer vision)
- PyTorch (deep learning)

**Installation Time**: 5-10 minutes (depending on network speed)

### Install Development Dependencies

```bash
pip install -r requirements-dev.txt
```

This installs:
- pytest (testing framework)
- black (code formatter)
- flake8 (linter)
- mypy (type checker)
- coverage (code coverage)

**Installation Time**: 1-2 minutes

---

## Step 5: Download YOLO Model

The system requires a YOLO model for person detection. We recommend YOLOv8n (nano) for testing and YOLOv8m (medium) for production.

### Option 1: Auto-Download (Recommended)

The model will be downloaded automatically on first run. Just ensure you have internet connection.

### Option 2: Manual Download

```bash
# Download YOLOv8n (faster, 6MB)
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt

# OR download YOLOv8m (more accurate, 50MB)
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8m.pt
```

---

## Step 6: Configure Environment

### Copy Environment Template

```bash
cp .env.example .env
```

### Edit Configuration (Optional)

```bash
nano .env  # or use your preferred editor
```

Default configuration should work for most setups. Key settings:

```bash
# Database
DATABASE_URL=sqlite:///./keyframe.db

# Redis
REDIS_URL=redis://localhost:6379/0

# Output Directory
OUTPUT_DIR=./output

# YOLO Model
YOLO_MODEL_NAME=yolov8n.pt
```

---

## Step 7: Initialize Database

```bash
# Create database tables
python -c "from backend.models.video import Base; from sqlalchemy import create_engine; engine = create_engine('sqlite:///./keyframe.db'); Base.metadata.create_all(engine)"
```

Or simply run the application once (it will auto-create tables).

---

## Step 8: Verify Installation

### Run Unit Tests

```bash
pytest tests/unit/ -v
```

**Expected Output**:
```
================================ test session starts =================================
...
tests/unit/agents/test_detection_agent.py ........                            [ 25%]
tests/unit/agents/test_keyframe_agent.py ..........                           [ 50%]
tests/unit/agents/test_lead_agent.py ..............                           [ 75%]
tests/unit/api/test_video_routes.py ......                                    [100%]

================================ 30+ passed in 15.23s ================================
```

If all tests pass, your installation is successful!

---

## Step 9: Start Services

You need to run three services in separate terminal windows/tabs.

### Terminal 1: Start Redis Server

```bash
redis-server
```

**Expected Output**:
```
                _._
           _.-``__ ''-._
      _.-``    `.  `_.  ''-._
  .-`` .-```.  ```\/    _.,_ ''-._
 (    '      ,       .-`  | `,    )
 |`-._`-...-` __...-.``-._|'` _.-'|
 |    `-._   `._    /     _.-'    |
  `-._    `-._  `-./  _.-'    _.-'
      `-._    `-.__.-'    _.-'
          `-._        _.-'
              `-.__.-'

Ready to accept connections
```

**Keep this terminal running.**

### Terminal 2: Start FastAPI Server

```bash
# Make sure virtual environment is activated
source .venv/bin/activate

# Start server
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected Output**:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Keep this terminal running.**

**Test API**: Open browser to http://localhost:8000/docs

### Terminal 3: Start Celery Worker

```bash
# Make sure virtual environment is activated
source .venv/bin/activate

# Start Celery worker
celery -A backend.workers.tasks worker --loglevel=info
```

**Expected Output**:
```
 -------------- celery@MacBook-Pro.local v5.3.6
---- **** -----
--- * ***  * -- Darwin-24.6.0-arm64-arm-64bit
-- * - **** ---
- ** ---------- [config]
- ** ---------- .> app:         tasks:0x1047a8c90
- ** ---------- .> transport:   redis://localhost:6379/0
- ** ---------- .> results:     disabled://
*** --- * --- .> concurrency: 8
-- ******* ---- .> task events: OFF
--- ***** -----

[tasks]
  . backend.workers.tasks.process_video_task

[2025-12-07 15:30:00,000: INFO/MainProcess] Connected to redis://localhost:6379/0
[2025-12-07 15:30:00,001: INFO/MainProcess] mingle: searching for neighbors
[2025-12-07 15:30:01,012: INFO/MainProcess] mingle: all alone
[2025-12-07 15:30:01,023: INFO/MainProcess] celery@MacBook-Pro.local ready.
```

**Keep this terminal running.**

---

## Step 10: Test the System

### Test via Python Script

Create a test script `test_process.py`:

```python
import asyncio
from pathlib import Path
from backend.core.agents import DetectionAgent, KeyframeAgent, LeadAgent

async def main():
    # Initialize agents
    detection_agent = DetectionAgent(model_name="yolov8n.pt")
    keyframe_agent = KeyframeAgent(output_dir=Path("output"))
    lead_agent = LeadAgent(detection_agent, keyframe_agent)

    # Process test video
    video_path = Path("WanAnimate_00001_p84-audio_gouns_1765004610.mp4")

    if not video_path.exists():
        print(f"Error: Test video not found at {video_path}")
        return

    print(f"Processing video: {video_path}")
    result = await lead_agent.process_video(
        video_path=video_path,
        video_id="test-001",
        config={"sample_rate": 5, "max_frames": 20}
    )

    print(f"\n✓ Processing complete!")
    print(f"  - Detections: {result.total_detections}")
    print(f"  - Keyframes: {result.keyframes_extracted}")
    print(f"  - Output: {result.keyframe_dir}")
    print(f"  - Time: {result.processing_time_seconds:.2f}s")

if __name__ == "__main__":
    asyncio.run(main())
```

Run it:

```bash
python test_process.py
```

**Expected Output**:
```
Processing video: WanAnimate_00001_p84-audio_gouns_1765004610.mp4

✓ Processing complete!
  - Detections: 42
  - Keyframes: 15
  - Output: output/video-test-001/keyframes
  - Time: 8.45s
```

### Test via API

```bash
# Upload video
curl -X POST "http://localhost:8000/api/videos/upload" \
  -F "file=@WanAnimate_00001_p84-audio_gouns_1765004610.mp4"

# Response:
# {"video_id":"abc123","status":"pending","message":"Video uploaded successfully"}

# Check status
curl "http://localhost:8000/api/videos/abc123/status"

# Response:
# {"video_id":"abc123","status":"completed","keyframes_count":15}
```

---

## Step 11: Run Full Test Suite

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=backend --cov-report=html

# View coverage report
open htmlcov/index.html
```

---

## Troubleshooting

### Issue: `ModuleNotFoundError: No module named 'backend'`

**Solution**: Ensure virtual environment is activated and PYTHONPATH is set:

```bash
source .venv/bin/activate
export PYTHONPATH=/Users/wangzq/VsCodeProjects/key-face-frame:$PYTHONPATH
```

### Issue: `redis.exceptions.ConnectionError: Error 61 connecting to localhost:6379`

**Solution**: Start Redis server:

```bash
redis-server
```

### Issue: `FileNotFoundError: [Errno 2] No such file or directory: 'yolov8n.pt'`

**Solution**: Download YOLO model:

```bash
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt
```

### Issue: PyTorch not using Apple Silicon GPU (MPS)

**Solution**: Verify MPS availability:

```python
import torch
print(torch.backends.mps.is_available())  # Should be True
```

If False, reinstall PyTorch for Apple Silicon:

```bash
pip install --upgrade torch torchvision
```

### Issue: Tests are very slow

**Solution**: Use faster YOLO model (yolov8n) and reduce test video size:

```bash
pytest -m "not slow"  # Skip slow tests
pytest tests/unit/  # Run only fast unit tests
```

### Issue: Permission denied on output directory

**Solution**: Create output directory with correct permissions:

```bash
mkdir -p output
chmod 755 output
```

---

## Directory Structure After Setup

```
key-face-frame/
├── .venv/                      # Virtual environment
├── backend/                    # Source code
│   ├── api/                    # FastAPI routes
│   ├── core/                   # Business logic
│   │   └── agents/             # Agent implementations
│   ├── models/                 # Database models
│   └── workers/                # Celery tasks
├── tests/                      # Test suite
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   └── e2e/                    # End-to-end tests
├── output/                     # Generated keyframes
├── yolov8n.pt                 # YOLO model (downloaded)
├── WanAnimate_*.mp4           # Test video
├── keyframe.db                # SQLite database
├── requirements.txt           # Production dependencies
├── requirements-dev.txt       # Development dependencies
├── pytest.ini                 # Pytest configuration
├── pyproject.toml             # Project metadata
└── README.md                  # Project documentation
```

---

## Quick Start Commands

### Daily Development Workflow

```bash
# 1. Activate environment
source .venv/bin/activate

# 2. Start services (in separate terminals)
redis-server &
uvicorn backend.main:app --reload &
celery -A backend.workers.tasks worker --loglevel=info &

# 3. Run tests
pytest

# 4. Process a video
python test_process.py
```

---

## Performance Tips

### For Mac M4 (Apple Silicon)

1. **Use MPS acceleration**: PyTorch automatically uses Metal Performance Shaders
2. **Use YOLOv8n for testing**: Faster inference
3. **Use YOLOv8m for production**: Better accuracy
4. **Adjust sample_rate**: Higher = faster but less thorough
5. **Limit max_frames**: Reduce for faster processing

### Memory Optimization

```python
# Process video with memory optimization
config = {
    "sample_rate": 5,      # Process every 5th frame
    "max_frames": 50,      # Limit keyframes
    "batch_size": 8,       # Smaller batch size for M4
}
```

---

## Next Steps

After successful setup:

1. **Read Documentation**: `README.md` and `TEST_EXECUTION_PLAN.md`
2. **Run Full Test Suite**: `./run_tests.sh`
3. **Process Test Video**: Verify keyframes in `output/` directory
4. **Explore API**: http://localhost:8000/docs
5. **Review Code**: Start with `backend/core/agents/`

---

## Maintenance

### Update Dependencies

```bash
pip install --upgrade -r requirements.txt
```

### Clean Up

```bash
# Remove output files
rm -rf output/*

# Remove cache
rm -rf .pytest_cache __pycache__ .mypy_cache

# Remove database
rm keyframe.db test.db
```

### Deactivate Virtual Environment

```bash
deactivate
```

---

## System Requirements

### Minimum

- **CPU**: Apple M1 or later
- **RAM**: 8 GB
- **Storage**: 2 GB free space
- **Network**: Internet (for model download)

### Recommended

- **CPU**: Apple M4
- **RAM**: 16 GB
- **Storage**: 10 GB free space
- **Network**: Fast internet (for faster model download)

---

## Support

If you encounter any issues:

1. Check the **Troubleshooting** section above
2. Review error messages in terminal
3. Check service logs (Redis, Uvicorn, Celery)
4. Verify all prerequisites are met
5. Ensure virtual environment is activated

---

**Last Updated**: 2025-12-07
**Version**: 1.0.0
**Platform**: macOS (M4 Apple Silicon)
