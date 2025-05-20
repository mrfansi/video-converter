"""Test configuration for the Video Converter project."""

import os
import sys
import pytest
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

@pytest.fixture
def test_data_dir():
    """Return the path to the test data directory."""
    return Path(__file__).parent / "data"

@pytest.fixture
def temp_output_dir(tmp_path):
    """Create and return a temporary output directory."""
    output_dir = tmp_path / "output"
    output_dir.mkdir(exist_ok=True)
    return output_dir

@pytest.fixture
def sample_video_path(test_data_dir):
    """Return the path to a sample video file for testing."""
    # This is a placeholder - we'll need to create this file
    return test_data_dir / "sample.mp4"

@pytest.fixture
def sample_image_path(test_data_dir):
    """Return the path to a sample image file for testing."""
    # This is a placeholder - we'll need to create this file
    return test_data_dir / "sample.png"

@pytest.fixture
def sample_svg_path(test_data_dir):
    """Return the path to a sample SVG file for testing."""
    # This is a placeholder - we'll need to create this file
    return test_data_dir / "sample.svg"

@pytest.fixture
def mock_environment(monkeypatch):
    """Set up mock environment variables for testing."""
    env_vars = {
        "R2_ENDPOINT_URL": "https://example.com",
        "R2_ACCESS_KEY_ID": "test_access_key",
        "R2_SECRET_ACCESS_KEY": "test_secret_key",
        "R2_BUCKET_NAME": "test-bucket",
        "R2_PATH_PREFIX": "test-prefix",
        "R2_URL": "https://cdn.example.com"
    }
    
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    
    return env_vars
