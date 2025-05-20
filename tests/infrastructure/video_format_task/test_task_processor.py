"""Unit tests for the VideoFormatTaskProcessor class.

This module contains unit tests for the VideoFormatTaskProcessor class
and its strategies.
"""

from typing import Optional
import os
import pytest
from unittest.mock import patch
from typing import Dict, Any, List

from app.infrastructure.video_format_task import (
    VideoFormatTaskProcessor,
    VideoFormatTaskStrategy,
    StandardVideoFormatTaskStrategy,
    OptimizedVideoFormatTaskStrategy,
    FallbackVideoFormatTaskStrategy,
)
from app.models.video_format_params import VideoFormatTaskParamBuilder
from app.domain.interfaces.video_format_task import ITaskProgressTracker, ICloudUploader


class MockTaskProgressTracker(ITaskProgressTracker):
    """Mock implementation of task progress tracking for testing."""

    def __init__(self):
        self.updates = []

    def update_progress(
        self,
        task_id: str,
        current_step: str,
        percent: int,
        details: Optional[str] = None,
    ) -> None:
        """Record progress updates for testing."""
        self.updates.append(
            {
                "task_id": task_id,
                "current_step": current_step,
                "percent": percent,
                "details": details,
            }
        )


class MockCloudUploader(ICloudUploader):
    """Mock implementation of cloud uploading for testing."""

    def __init__(self, success: bool = True):
        self.uploads: List[Dict[str, str]] = []
        self.success = success

    def upload_file(self, file_path: str, content_type: str) -> Dict[str, Any]:
        """Record file uploads for testing."""
        self.uploads.append({"file_path": file_path, "content_type": content_type})

        if self.success:
            return {
                "success": True,
                "url": f"https://example.com/{os.path.basename(file_path)}",
                "object_key": os.path.basename(file_path),
            }
        else:
            return {"success": False, "error": "Upload failed"}


@pytest.fixture
def mock_progress_tracker():
    """Fixture for mock progress tracker."""
    return MockTaskProgressTracker()


@pytest.fixture
def mock_cloud_uploader():
    """Fixture for mock cloud uploader."""
    return MockCloudUploader()


@pytest.fixture
def mock_video_info():
    """Fixture for mock video info."""
    return {"width": 1280, "height": 720, "duration": 10.5, "fps": 30, "codec": "h264"}


@pytest.fixture
def mock_conversion_result():
    """Fixture for mock conversion result."""
    return {
        "output_path": "/tmp/test/converted_123456.mp4",
        "size_bytes": 1024 * 1024,  # 1 MB
        "duration": 10.5,
    }


class TestVideoFormatTaskProcessor:
    """Test cases for the VideoFormatTaskProcessor class."""

    @patch("app.video_converter.get_video_info")
    @patch("app.video_converter.convert_video")
    def test_standard_strategy(
        self,
        mock_convert_video,
        mock_get_video_info,
        mock_progress_tracker,
        mock_cloud_uploader,
        mock_video_info,
        mock_conversion_result,
    ):
        """Test the standard strategy for video format task processing."""
        # Set up mocks
        mock_get_video_info.return_value = mock_video_info
        mock_convert_video.return_value = mock_conversion_result

        # Create a standard strategy with mocks
        strategy = StandardVideoFormatTaskStrategy(
            progress_tracker=mock_progress_tracker, cloud_uploader=mock_cloud_uploader
        )

        # Create the processor with the strategy
        processor = VideoFormatTaskProcessor(strategy)

        # Process a video format task
        result = processor.process_video_format_task(
            temp_dir="/tmp/test",
            file_path="/tmp/test/input.mp4",
            output_format="mp4",
            quality="medium",
            width=1280,
            height=720,
            task_id="test-task-id",
        )

        # Verify the result
        assert result["success"] is True
        assert "url" in result
        assert result["output_format"] == "mp4"

        # Verify the mocks were called correctly
        mock_get_video_info.assert_called_once_with("/tmp/test/input.mp4")
        mock_convert_video.assert_called_once()

        # Verify progress updates were made
        assert len(mock_progress_tracker.updates) > 0
        assert mock_progress_tracker.updates[-1]["percent"] == 100

        # Verify file was uploaded
        assert len(mock_cloud_uploader.uploads) == 1
        assert (
            mock_cloud_uploader.uploads[0]["file_path"]
            == mock_conversion_result["output_path"]
        )

    @patch("app.video_converter.get_video_info")
    @patch("app.video_converter.convert_video")
    def test_optimized_strategy(
        self,
        mock_convert_video,
        mock_get_video_info,
        mock_progress_tracker,
        mock_cloud_uploader,
        mock_video_info,
        mock_conversion_result,
    ):
        """Test the optimized strategy for video format task processing."""
        # Set up mocks
        mock_get_video_info.return_value = mock_video_info
        mock_convert_video.return_value = mock_conversion_result

        # Create an optimized strategy with mocks
        strategy = OptimizedVideoFormatTaskStrategy(
            progress_tracker=mock_progress_tracker, cloud_uploader=mock_cloud_uploader
        )

        # Create the processor with the strategy
        processor = VideoFormatTaskProcessor(strategy)

        # Process a video format task
        result = processor.process_video_format_task(
            temp_dir="/tmp/test",
            file_path="/tmp/test/input.mp4",
            output_format="mp4",
            quality="high",
            width=1920,
            height=1080,
            task_id="test-task-id",
        )

        # Verify the result
        assert result["success"] is True
        assert "url" in result
        assert result["strategy"] == "optimized"

        # Verify the mocks were called correctly
        mock_get_video_info.assert_called_once_with("/tmp/test/input.mp4")
        mock_convert_video.assert_called_once()

        # Verify progress updates were made
        assert len(mock_progress_tracker.updates) > 0

        # Verify file was uploaded
        assert len(mock_cloud_uploader.uploads) == 1

    @patch("app.video_converter.convert_video")
    def test_fallback_strategy(
        self,
        mock_convert_video,
        mock_progress_tracker,
        mock_cloud_uploader,
        mock_conversion_result,
    ):
        """Test the fallback strategy for video format task processing."""
        # Set up mocks
        mock_convert_video.return_value = mock_conversion_result

        # Create a fallback strategy with mocks
        strategy = FallbackVideoFormatTaskStrategy(
            progress_tracker=mock_progress_tracker, cloud_uploader=mock_cloud_uploader
        )

        # Create the processor with the strategy
        processor = VideoFormatTaskProcessor(strategy)

        # Process a video format task
        result = processor.process_video_format_task(
            temp_dir="/tmp/test",
            file_path="/tmp/test/input.mp4",
            output_format="mp4",
            quality="medium",
            task_id="test-task-id",
        )

        # Verify the result
        assert result["success"] is True
        assert "url" in result
        assert result["strategy"] == "fallback"

        # Verify the mocks were called correctly
        mock_convert_video.assert_called_once()

        # Verify progress updates were made
        assert len(mock_progress_tracker.updates) > 0

        # Verify file was uploaded
        assert len(mock_cloud_uploader.uploads) == 1

    @patch("app.video_converter.get_video_info")
    @patch("app.video_converter.convert_video")
    def test_strategy_selection(
        self,
        mock_convert_video,
        mock_get_video_info,
        mock_progress_tracker,
        mock_cloud_uploader,
        mock_video_info,
        mock_conversion_result,
    ):
        """Test strategy selection based on strategy_type parameter."""
        # Set up mocks
        mock_get_video_info.return_value = mock_video_info
        mock_convert_video.return_value = mock_conversion_result

        # Create the processor with default strategy
        processor = VideoFormatTaskProcessor()

        # Test with standard strategy
        processor.process_video_format_task(
            temp_dir="/tmp/test",
            file_path="/tmp/test/input.mp4",
            output_format="mp4",
            quality="medium",
            strategy_type=VideoFormatTaskStrategy.STANDARD,
        )
        assert isinstance(processor.strategy, StandardVideoFormatTaskStrategy)

        # Test with optimized strategy
        processor.process_video_format_task(
            temp_dir="/tmp/test",
            file_path="/tmp/test/input.mp4",
            output_format="mp4",
            quality="high",
            strategy_type=VideoFormatTaskStrategy.OPTIMIZED,
        )
        assert isinstance(processor.strategy, OptimizedVideoFormatTaskStrategy)

        # Test with fallback strategy
        processor.process_video_format_task(
            temp_dir="/tmp/test",
            file_path="/tmp/test/input.mp4",
            output_format="mp4",
            quality="low",
            strategy_type=VideoFormatTaskStrategy.FALLBACK,
        )
        assert isinstance(processor.strategy, FallbackVideoFormatTaskStrategy)

    @patch("app.video_converter.get_video_info")
    @patch("app.video_converter.convert_video")
    def test_with_parameter_builder(
        self,
        mock_convert_video,
        mock_get_video_info,
        mock_progress_tracker,
        mock_cloud_uploader,
        mock_video_info,
        mock_conversion_result,
    ):
        """Test using the parameter builder with the processor."""
        # Set up mocks
        mock_get_video_info.return_value = mock_video_info
        mock_convert_video.return_value = mock_conversion_result

        # Create a standard strategy with mocks
        strategy = StandardVideoFormatTaskStrategy(
            progress_tracker=mock_progress_tracker, cloud_uploader=mock_cloud_uploader
        )

        # Create the processor with the strategy
        processor = VideoFormatTaskProcessor(strategy)

        # Create parameters using builder
        params_builder = VideoFormatTaskParamBuilder()
        params_builder.with_temp_dir("/tmp/test")
        params_builder.with_file_path("/tmp/test/input.mp4")
        params_builder.with_output_format("mp4")
        params_builder.with_quality("medium")
        params_builder.with_dimensions(1280, 720)
        params_builder.with_task_id("test-task-id")
        params = params_builder.build()

        # Process a video format task using parameters
        result = processor.process_video_format_task(
            temp_dir=params.temp_dir,
            file_path=params.file_path,
            output_format=params.output_format,
            quality=params.quality,
            width=params.width,
            height=params.height,
            task_id=params.task_id,
        )

        # Verify the result
        assert result["success"] is True
        assert "url" in result

        # Verify the mocks were called correctly
        mock_get_video_info.assert_called_once_with("/tmp/test/input.mp4")
        mock_convert_video.assert_called_once()

    @patch("app.video_converter.get_video_info")
    @patch("app.video_converter.convert_video")
    def test_error_handling(
        self,
        mock_convert_video,
        mock_get_video_info,
        mock_progress_tracker,
        mock_cloud_uploader,
    ):
        """Test error handling in the processor."""
        # Set up mocks to raise an exception
        mock_get_video_info.side_effect = Exception("Test error")

        # Create a standard strategy with mocks
        strategy = StandardVideoFormatTaskStrategy(
            progress_tracker=mock_progress_tracker, cloud_uploader=mock_cloud_uploader
        )

        # Create the processor with the strategy
        processor = VideoFormatTaskProcessor(strategy)

        # Process a video format task and expect an exception
        with pytest.raises(Exception):
            processor.process_video_format_task(
                temp_dir="/tmp/test",
                file_path="/tmp/test/input.mp4",
                output_format="mp4",
                quality="medium",
                task_id="test-task-id",
            )

        # Verify error progress update was made
        assert len(mock_progress_tracker.updates) > 0
        assert mock_progress_tracker.updates[-1]["current_step"] == "Error"
        assert mock_progress_tracker.updates[-1]["percent"] == 0
