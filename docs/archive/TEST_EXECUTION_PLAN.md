# Test Execution Plan

## Overview

This document provides a comprehensive test execution plan for the Key-Face-Frame video keyframe extraction system. Follow this guide to validate all components before production deployment.

---

## Test Categories

### 1. Unit Tests

**Purpose**: Validate individual components in isolation

**Location**: `/Users/wangzq/VsCodeProjects/key-face-frame/tests/unit/`

**Components Tested**:
- Detection Agent (YOLO person detection)
- Keyframe Agent (keyframe extraction and scoring)
- Lead Agent (pipeline orchestration)
- API Routes (FastAPI endpoints)
- Celery Tasks (async job processing)

**Test Files**:
```
tests/unit/
├── agents/
│   ├── test_detection_agent.py
│   ├── test_keyframe_agent.py
│   └── test_lead_agent.py
├── api/
│   └── test_video_routes.py
└── workers/
    └── test_tasks.py
```

**Execution**:
```bash
pytest tests/unit/ -v
```

**Expected Results**:
- All unit tests should pass (green)
- Coverage should be >= 80% for core modules
- No mock failures
- Execution time: < 30 seconds

---

### 2. Integration Tests

**Purpose**: Validate component interactions with real dependencies

**Location**: `/Users/wangzq/VsCodeProjects/key-face-frame/tests/integration/`

**Components Tested**:
- Detection Agent with actual YOLO model
- Keyframe Agent with real video frames
- Full pipeline (Detection → Keyframe Extraction)

**Test Files**:
```
tests/integration/
├── test_detection_integration.py
├── test_keyframe_integration.py
├── test_pipeline.py
└── test_full_pipeline.py
```

**Prerequisites**:
- YOLO model downloaded (yolov8n.pt or yolov8m.pt)
- Test video file available
- Sufficient disk space for output files

**Execution**:
```bash
pytest tests/integration/ -v --slow
```

**Expected Results**:
- All integration tests pass
- Real detections generated from test video
- Keyframe images saved to output directory
- Execution time: 1-5 minutes (depending on video size)

---

### 3. End-to-End (E2E) Tests

**Purpose**: Validate complete workflow with real video processing

**Location**: `/Users/wangzq/VsCodeProjects/key-face-frame/tests/e2e/`

**Components Tested**:
- Complete video processing pipeline
- Real video file (`WanAnimate_00001_p84-audio_gouns_1765004610.mp4`)
- Output directory structure
- Metadata.json generation

**Test Files**:
```
tests/e2e/
└── test_complete_workflow.py
```

**Prerequisites**:
- Test video at: `/Users/wangzq/VsCodeProjects/key-face-frame/WanAnimate_00001_p84-audio_gouns_1765004610.mp4`
- YOLO model (yolov8n.pt recommended for speed)
- Output directory writeable

**Execution**:
```bash
pytest tests/e2e/ -v --slow -s
```

**Expected Results**:
- Video successfully processed
- At least 1 person detection
- At least 1 keyframe extracted
- Output files:
  - `output/video-test-e2e-001/keyframes/*.jpg`
  - `output/video-test-e2e-001/metadata.json`
- Execution time: 30 seconds - 2 minutes

---

### 4. API Tests

**Purpose**: Validate REST API endpoints

**Location**: Built-in API testing via curl/httpx

**Components Tested**:
- Video upload endpoint
- Video status endpoint
- Video results endpoint
- Error handling

**Prerequisites**:
- Redis server running: `redis-server`
- FastAPI server running: `uvicorn backend.main:app --reload`
- Celery worker running: `celery -A backend.workers.tasks worker --loglevel=info`

**Execution**:
```bash
# Use provided test script
./test_api.sh

# Or manual curl commands
curl -X POST "http://localhost:8000/api/videos/upload" \
  -F "file=@WanAnimate_00001_p84-audio_gouns_1765004610.mp4"

curl "http://localhost:8000/api/videos/{video_id}/status"
```

**Expected Results**:
- 200 OK responses
- Valid JSON responses
- Video ID returned
- Status transitions: pending → processing → completed
- Keyframe files saved to correct directory

---

### 5. Code Quality Tests

**Purpose**: Ensure code quality standards

**Tools**:
- Black (code formatting)
- Flake8 (linting)
- isort (import sorting)
- mypy (type checking)

**Execution**:
```bash
# Check formatting
black --check backend/ tests/

# Lint code
flake8 backend/ --max-line-length=100

# Check imports
isort --check-only backend/ tests/

# Type checking
mypy backend/ --ignore-missing-imports
```

**Expected Results**:
- No formatting violations
- No linting errors
- Imports properly sorted
- No type errors (with ignore-missing-imports for 3rd party)

---

## Complete Test Suite Execution

### Option 1: Automated Test Runner

```bash
./run_tests.sh
```

This script runs:
1. Code quality checks (black, flake8, isort)
2. Type checking (mypy)
3. Unit tests with coverage
4. Integration tests

**Total Time**: 2-5 minutes

---

### Option 2: Manual Step-by-Step

```bash
# 1. Code quality
black --check backend/ tests/
flake8 backend/ --max-line-length=100
isort --check-only backend/ tests/

# 2. Type checking
mypy backend/ --ignore-missing-imports

# 3. Unit tests
pytest tests/unit/ -v --cov=backend --cov-report=term-missing

# 4. Integration tests
pytest tests/integration/ -v --slow

# 5. E2E tests
pytest tests/e2e/ -v --slow -s

# 6. All tests with coverage
pytest -v --cov=backend --cov-report=html
```

---

## Test Markers

The project uses pytest markers to categorize tests:

```bash
# Run only unit tests
pytest -m unit -v

# Run only integration tests
pytest -m integration -v

# Run only slow tests
pytest -m slow -v

# Run only tests requiring ML models
pytest -m requires_model -v

# Skip slow tests
pytest -m "not slow" -v
```

---

## Prerequisites Checklist

Before running tests, ensure:

- [ ] Python 3.10+ installed
- [ ] Virtual environment activated: `source .venv/bin/activate`
- [ ] Dependencies installed: `pip install -r requirements.txt requirements-dev.txt`
- [ ] Redis server running (for API tests)
- [ ] Test video file available
- [ ] YOLO model downloaded (yolov8n.pt or yolov8m.pt)
- [ ] Output directory writeable
- [ ] Sufficient disk space (> 500MB)

---

## Expected Test Counts

| Category          | Test Count | Expected Pass | Execution Time |
|-------------------|------------|---------------|----------------|
| Unit Tests        | 30+        | 100%          | < 30s          |
| Integration Tests | 8+         | 100%          | 1-5 min        |
| E2E Tests         | 1          | 100%          | 30s-2min       |
| **Total**         | **39+**    | **100%**      | **2-8 min**    |

---

## Pass Criteria

### Minimum Acceptance Criteria

- [ ] All unit tests pass (100%)
- [ ] All integration tests pass (100%)
- [ ] E2E test passes with real video
- [ ] Code coverage >= 80%
- [ ] No Black formatting violations
- [ ] No Flake8 linting errors
- [ ] No critical type errors

### Quality Criteria

- [ ] Code coverage >= 85%
- [ ] All type hints added to public APIs
- [ ] All docstrings present
- [ ] No TODO comments in production code
- [ ] Performance benchmarks met (< 2 min for test video)

---

## Interpreting Results

### Success Indicators

```
✓ All tests passed
✓ Coverage: 85%
✓ No linting errors
✓ No type errors
```

**Action**: Ready for production deployment

### Warning Indicators

```
⚠ Tests passed but coverage < 80%
⚠ Some type hints missing
⚠ Non-critical linting warnings
```

**Action**: Address warnings before production

### Failure Indicators

```
✗ Tests failed
✗ Linting errors
✗ Type errors
✗ Coverage < 60%
```

**Action**: Fix errors immediately, do NOT deploy

---

## Debugging Failed Tests

### Unit Test Failures

```bash
# Run specific test with verbose output
pytest tests/unit/agents/test_lead_agent.py::test_process_video_returns_result -v -s

# Run with debugger
pytest tests/unit/agents/test_lead_agent.py --pdb
```

### Integration Test Failures

```bash
# Check YOLO model exists
ls -lh yolov8*.pt

# Check test video exists
ls -lh WanAnimate_00001_p84-audio_gouns_1765004610.mp4

# Run with detailed output
pytest tests/integration/test_full_pipeline.py -v -s --log-cli-level=DEBUG
```

### API Test Failures

```bash
# Check services running
ps aux | grep redis
ps aux | grep uvicorn
ps aux | grep celery

# Test Redis connection
redis-cli ping

# Test API directly
curl http://localhost:8000/health
```

---

## Coverage Reports

### Terminal Coverage

```bash
pytest --cov=backend --cov-report=term-missing
```

Shows line-by-line coverage in terminal.

### HTML Coverage Report

```bash
pytest --cov=backend --cov-report=html
open htmlcov/index.html
```

Interactive HTML report with highlighting.

---

## Continuous Integration

For CI/CD pipelines (GitHub Actions, GitLab CI, etc.):

```yaml
# .github/workflows/test.yml
- name: Run tests
  run: |
    pip install -r requirements.txt -r requirements-dev.txt
    ./run_tests.sh
```

---

## Performance Benchmarks

| Operation                    | Expected Time | Max Acceptable |
|------------------------------|---------------|----------------|
| Unit test suite              | 10-30s        | 1 min          |
| Integration test suite       | 1-3 min       | 5 min          |
| E2E test (sample video)      | 30s-1min      | 2 min          |
| Full test suite              | 2-5 min       | 10 min         |
| Single video processing      | 10s-2min      | 5 min          |

---

## Test Data

### Test Video Specifications

**File**: `WanAnimate_00001_p84-audio_gouns_1765004610.mp4`

- **Size**: ~6.1 MB
- **Duration**: ~5 seconds
- **Resolution**: Standard HD
- **Expected Detections**: 10-50 person detections
- **Expected Keyframes**: 5-20 keyframes

### Mock Data

Unit tests use mocked data to avoid external dependencies. See `/Users/wangzq/VsCodeProjects/key-face-frame/tests/conftest.py` for fixtures.

---

## Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'backend'`
```bash
# Solution: Ensure PYTHONPATH includes project root
export PYTHONPATH=/Users/wangzq/VsCodeProjects/key-face-frame:$PYTHONPATH
```

**Issue**: `FileNotFoundError: YOLO model not found`
```bash
# Solution: Download YOLO model
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt
```

**Issue**: `redis.exceptions.ConnectionError`
```bash
# Solution: Start Redis server
redis-server
```

**Issue**: Tests timeout or hang
```bash
# Solution: Use pytest timeout
pytest --timeout=300 tests/integration/
```

---

## Next Steps After Testing

1. **Review Coverage Report**: `open htmlcov/index.html`
2. **Fix Any Failures**: Address red tests immediately
3. **Review Quality Metrics**: See `QUALITY_METRICS.md`
4. **User Acceptance Testing**: Process real production videos
5. **Performance Testing**: Test with large videos (> 1GB)
6. **Load Testing**: Test concurrent API requests

---

## Support

For issues or questions:
- Check test output for detailed error messages
- Review logs: `tail -f celery.log`
- Inspect output directory: `ls -R output/`
- Enable debug logging: `--log-cli-level=DEBUG`

---

**Last Updated**: 2025-12-07
**Version**: 1.0.0
