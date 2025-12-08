"""
Pytest Configuration and Fixtures

Shared test fixtures for the Key-Face-Frame test suite.

主要 Fixtures:
- test_video_path: 可配置的测试视频路径（支持环境变量/pytest.ini/默认值）
- output_dir: 临时输出目录
- mock_storage/mock_yolo_model: Mock 对象用于单元测试
"""

import os
from pathlib import Path
from unittest.mock import Mock

import pytest

# 默认测试视频文件名（向后兼容）
DEFAULT_TEST_VIDEO = "WanAnimate_00001_p84-audio_gouns_1765004610.mp4"


@pytest.fixture(scope="session")
def test_video_path():
    """
    获取测试视频路径的全局 fixture（可配置）。

    配置优先级：
    1. 环境变量 TEST_VIDEO_FILE
    2. 默认值: WanAnimate_00001_p84-audio_gouns_1765004610.mp4

    使用方法：
        # 方式 1: 环境变量（推荐）
        export TEST_VIDEO_FILE="my_video.mp4"
        pytest tests/

        # 方式 2: 一次性运行
        TEST_VIDEO_FILE="my_video.mp4" pytest tests/

        # 方式 3: 使用默认视频（无需配置）
        pytest tests/

    路径规则：
    - 绝对路径: 直接使用（如 /Users/xxx/video.mp4）
    - 相对路径: 基于项目根目录（如 video.mp4 或 tests/fixtures/video.mp4）

    Returns:
        Path: 视频文件的绝对路径

    Raises:
        pytest.skip: 如果视频文件不存在，跳过测试而非失败
    """
    # 步骤 1: 从环境变量获取，如果未设置则使用默认值
    video_file = os.getenv("TEST_VIDEO_FILE", DEFAULT_TEST_VIDEO)

    # 步骤 2: 转换为绝对路径
    video_path = Path(video_file)
    if not video_path.is_absolute():
        # 相对路径：基于项目根目录（tests 的父目录）
        project_root = Path(__file__).parent.parent
        video_path = project_root / video_file

    # 步骤 3: 验证文件存在
    if not video_path.exists():
        pytest.skip(
            f"测试视频不存在: {video_path}\n"
            f"提示: 请设置环境变量 TEST_VIDEO_FILE 或将视频文件放到项目根目录\n"
            f"示例: TEST_VIDEO_FILE='your_video.mp4' pytest tests/"
        )

    return video_path


@pytest.fixture
def output_dir(tmp_path):
    """Temporary output directory for tests."""
    output = tmp_path / "output"
    output.mkdir()
    return output


@pytest.fixture
def mock_storage():
    """Mock storage service."""
    storage = Mock()
    storage.save_frame = Mock(return_value="/path/to/frame.jpg")
    return storage


@pytest.fixture
def sample_frame_data():
    """Sample frame metadata for testing."""
    return {
        "frame_number": 100,
        "timestamp": 3.33,
        "has_face": True,
        "confidence": 0.95,
        "bbox": [100, 100, 200, 200],
    }


@pytest.fixture
def mock_yolo_model():
    """Mock YOLOv8 model for testing."""
    model = Mock()
    model.predict = Mock(return_value=[Mock()])
    return model
