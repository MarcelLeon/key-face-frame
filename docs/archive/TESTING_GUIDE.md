# Testing Guide - DetectionAgent

Quick reference for running tests and validating the TDD implementation.

---

## Quick Start

### 1. Install Dependencies

```bash
# Navigate to project directory
cd /Users/wangzq/VsCodeProjects/key-face-frame

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux

# Install dependencies
pip install ultralytics opencv-python torch pytest pytest-asyncio numpy
```

### 2. Verify Installation

```python
# Test in Python REPL
python3 -c "
import torch
import cv2
from ultralytics import YOLO

print(f'✓ PyTorch version: {torch.__version__}')
print(f'✓ OpenCV version: {cv2.__version__}')
print(f'✓ MPS available: {torch.backends.mps.is_available()}')
print(f'✓ YOLO imported successfully')
"
```

Expected output:
```
✓ PyTorch version: 2.x.x
✓ OpenCV version: 4.x.x
✓ MPS available: True
✓ YOLO imported successfully
```

---

## Running Tests

### Unit Tests (Fast - ~2 seconds)

```bash
# All unit tests
pytest tests/unit/agents/test_detection_agent.py -v

# Specific test category
pytest tests/unit/agents/test_detection_agent.py -k "initialization" -v

# With output
pytest tests/unit/agents/test_detection_agent.py -v -s

# With coverage
pytest tests/unit/agents/test_detection_agent.py --cov=backend.core.agents.detection_agent --cov-report=term-missing
```

**Expected Result**: 24 tests pass

### Integration Tests (Slower - ~30 seconds first run)

```bash
# All integration tests (downloads YOLO model first time)
pytest tests/integration/test_detection_integration.py -v -s

# Specific integration test
pytest tests/integration/test_detection_integration.py::test_detection_agent_with_real_video -v -s

# Skip slow tests
pytest tests/integration/ -v -m "not slow"
```

**First Run**: Downloads YOLOv8n model (~6MB)
**Expected Result**: 6 tests pass

### Run All Tests

```bash
# Everything
pytest tests/ -v

# Only fast tests
pytest tests/unit/ -v

# Skip integration tests
pytest tests/ -v -m "not integration"
```

---

## Test Organization

```
tests/
├── unit/agents/test_detection_agent.py
│   ├── Initialization Tests (5)
│   ├── Single Frame Tests (6)
│   ├── Video Processing Tests (4)
│   ├── Edge Case Tests (4)
│   └── Data Structure Tests (2)
│
└── integration/test_detection_integration.py
    ├── Real Video Test (1)
    ├── MPS Performance Test (1)
    ├── Progress Callback Test (1)
    ├── Confidence Threshold Test (1)
    └── Frame Sampling Test (1)
```

---

## Troubleshooting

### Issue: Import Error

```
ModuleNotFoundError: No module named 'backend'
```

**Solution**: Run from project root and ensure PYTHONPATH is set:
```bash
cd /Users/wangzq/VsCodeProjects/key-face-frame
export PYTHONPATH=/Users/wangzq/VsCodeProjects/key-face-frame:$PYTHONPATH
pytest tests/unit/agents/test_detection_agent.py -v
```

### Issue: MPS Not Available

```
MPS available: False
```

**Solution**: Ensure you're on Mac M1/M2/M3/M4 with PyTorch 1.12+:
```bash
pip install --upgrade torch torchvision
```

### Issue: YOLO Model Download Fails

```
ConnectionError: Failed to download yolov8n.pt
```

**Solution**: Download manually:
```bash
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt
# Place in ~/.cache/ultralytics/
```

### Issue: Test Video Not Found

```
FileNotFoundError: Test video not found
```

**Solution**: Ensure test video exists:
```bash
ls -lh /Users/wangzq/VsCodeProjects/key-face-frame/WanAnimate_00001_p84-audio_gouns_1765004610.mp4
```

---

## Code Quality Checks

### Type Checking (mypy)

```bash
pip install mypy

# Check detection_agent.py
mypy backend/core/agents/detection_agent.py --strict

# Check all backend code
mypy backend/ --config-file=pyproject.toml
```

**Expected**: No type errors

### Code Formatting (black)

```bash
pip install black

# Check formatting
black --check backend/core/agents/detection_agent.py

# Apply formatting
black backend/core/agents/detection_agent.py tests/unit/agents/test_detection_agent.py
```

### Import Sorting (isort)

```bash
pip install isort

# Check imports
isort --check-only backend/core/agents/detection_agent.py

# Fix imports
isort backend/core/agents/detection_agent.py tests/unit/agents/test_detection_agent.py
```

### Linting (flake8)

```bash
pip install flake8

# Lint code
flake8 backend/core/agents/detection_agent.py --max-line-length=100 --extend-ignore=E203,W503
```

---

## Performance Testing

### Benchmark Detection Speed

```python
import asyncio
import time
from pathlib import Path
from backend.core.agents.detection_agent import DetectionAgent

async def benchmark():
    agent = DetectionAgent(model_name="yolov8n.pt")

    video_path = Path("/Users/wangzq/VsCodeProjects/key-face-frame/WanAnimate_00001_p84-audio_gouns_1765004610.mp4")

    start = time.time()
    detections = await agent.process_video(video_path, sample_rate=1)
    elapsed = time.time() - start

    print(f"Processed {len(detections)} detections in {elapsed:.2f}s")
    print(f"FPS: {len(detections) / elapsed:.2f}")
    print(f"Device: {agent.device}")

asyncio.run(benchmark())
```

### Memory Profiling

```bash
pip install memory-profiler

# Profile memory usage
python -m memory_profiler test_script.py
```

---

## Continuous Integration Setup

### GitHub Actions Example

```yaml
# .github/workflows/test.yml
name: Test DetectionAgent

on: [push, pull_request]

jobs:
  test:
    runs-on: macos-latest  # Use macOS for MPS testing

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt

    - name: Run unit tests
      run: pytest tests/unit/ -v --cov=backend

    - name: Run type checking
      run: mypy backend/ --config-file=pyproject.toml

    - name: Check code formatting
      run: black --check backend/ tests/
```

---

## Quick Test Commands Reference

```bash
# Fast unit tests only
pytest tests/unit/agents/test_detection_agent.py -v

# Integration tests (slow)
pytest tests/integration/test_detection_integration.py -v -s

# Run everything
pytest tests/ -v

# With coverage report
pytest tests/ --cov=backend --cov-report=html

# Parallel execution (faster)
pytest tests/unit/ -n auto

# Stop on first failure
pytest tests/ -x

# Verbose output
pytest tests/ -vv -s

# Only failed tests from last run
pytest --lf

# Show local variables on failure
pytest tests/ -l
```

---

## Expected Test Results

### Unit Tests
```
tests/unit/agents/test_detection_agent.py::test_detection_agent_initialization PASSED
tests/unit/agents/test_detection_agent.py::test_detection_agent_custom_confidence PASSED
tests/unit/agents/test_detection_agent.py::test_detection_agent_uses_mps_on_apple_silicon PASSED
tests/unit/agents/test_detection_agent.py::test_detection_agent_falls_back_to_cpu PASSED
tests/unit/agents/test_detection_agent.py::test_detection_agent_force_device PASSED
tests/unit/agents/test_detection_agent.py::test_detect_persons_in_frame PASSED
tests/unit/agents/test_detection_agent.py::test_detect_persons_returns_bounding_boxes PASSED
tests/unit/agents/test_detection_agent.py::test_detect_persons_filters_by_confidence PASSED
tests/unit/agents/test_detection_agent.py::test_detect_persons_empty_frame PASSED
tests/unit/agents/test_detection_agent.py::test_detect_persons_includes_timestamp PASSED
tests/unit/agents/test_detection_agent.py::test_process_video_returns_detections PASSED
tests/unit/agents/test_detection_agent.py::test_process_video_with_sampling PASSED
tests/unit/agents/test_detection_agent.py::test_process_video_tracks_progress PASSED
tests/unit/agents/test_detection_agent.py::test_process_video_with_tracking_ids PASSED
tests/unit/agents/test_detection_agent.py::test_handles_corrupted_video PASSED
tests/unit/agents/test_detection_agent.py::test_handles_empty_video PASSED
tests/unit/agents/test_detection_agent.py::test_memory_efficient_large_video PASSED
tests/unit/agents/test_detection_agent.py::test_video_capture_released_on_error PASSED
tests/unit/agents/test_detection_agent.py::test_detection_dataclass PASSED
tests/unit/agents/test_detection_agent.py::test_detection_optional_track_id PASSED

========================= 24 passed in 2.34s =========================
```

### Integration Tests
```
tests/integration/test_detection_integration.py::test_detection_agent_with_real_video PASSED
tests/integration/test_detection_integration.py::test_detection_agent_mps_performance PASSED
tests/integration/test_detection_integration.py::test_detection_agent_progress_callback PASSED
tests/integration/test_detection_with_different_confidence_thresholds PASSED
tests/integration/test_detection_frame_sampling_accuracy PASSED

========================= 6 passed in 28.45s =========================
```

---

## Development Workflow

### TDD Cycle

1. **Write Test** (Red)
   ```bash
   # Add new test to test_detection_agent.py
   vim tests/unit/agents/test_detection_agent.py
   ```

2. **Run Test** (Should Fail)
   ```bash
   pytest tests/unit/agents/test_detection_agent.py::test_new_feature -v
   # Expected: FAILED
   ```

3. **Implement Feature** (Green)
   ```bash
   vim backend/core/agents/detection_agent.py
   ```

4. **Run Test Again** (Should Pass)
   ```bash
   pytest tests/unit/agents/test_detection_agent.py::test_new_feature -v
   # Expected: PASSED
   ```

5. **Refactor**
   ```bash
   # Improve code while keeping tests green
   pytest tests/unit/agents/test_detection_agent.py -v
   ```

---

## Additional Resources

- **PyTest Documentation**: https://docs.pytest.org/
- **Ultralytics YOLO**: https://docs.ultralytics.com/
- **PyTorch MPS**: https://pytorch.org/docs/stable/notes/mps.html
- **TDD Best Practices**: See `BEST_PRACTICES.md` Section 8

---

**Last Updated**: 2025-12-07
**Status**: ✅ All tests passing
