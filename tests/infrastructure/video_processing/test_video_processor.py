"""Unit tests for the VideoProcessor class.

This module contains tests for the VideoProcessor class and its strategies.
"""

import pytest
from unittest.mock import MagicMock, patch

from app.models.lottie_params import (
    VideoProcessingParamBuilder,
    VideoProcessingStrategy,
)
from app.infrastructure.video_processor import VideoProcessor


class TestVideoProcessor:
    """Test suite for the VideoProcessor class."""

    @pytest.fixture
    def mock_cloud_uploader(self):
        """Create a mock cloud uploader."""
        uploader = MagicMock()
        uploader.upload_file.return_value = {
            "success": True,
            "url": "https://example.com/test.json",
            "object_key": "test.json",
        }
        return uploader

    @pytest.fixture
    def test_params(self):
        """Create test parameters for video processing."""
        return (
            VideoProcessingParamBuilder()
            .with_file_path("/path/to/video.mp4")
            .with_temp_dir("/tmp/test")
            .with_fps(24)
            .with_dimensions(512, 512)
            .with_original_filename("video.mp4")
            .with_strategy(VideoProcessingStrategy.STANDARD)
            .with_max_frames(100)
            .with_optimization(True, True)
            .build()
        )

    def test_get_strategy(self, mock_cloud_uploader):
        """Test the get_strategy method."""
        processor = VideoProcessor(cloud_uploader=mock_cloud_uploader)

        # Test with enum value
        strategy = processor.get_strategy(VideoProcessingStrategy.STANDARD)
        assert strategy is not None
        assert strategy == processor.strategies[VideoProcessingStrategy.STANDARD]

        # Test with string value
        strategy = processor.get_strategy("high_quality")
        assert strategy is not None
        assert strategy == processor.strategies[VideoProcessingStrategy.HIGH_QUALITY]

        # Test with invalid string value (should default to STANDARD)
        strategy = processor.get_strategy("invalid")
        assert strategy is not None
        assert strategy == processor.strategies[VideoProcessingStrategy.STANDARD]

    @patch(
        "app.infrastructure.video_processing.processing_strategies.StandardVideoProcessingStrategy.process_video"
    )
    def test_process_video_standard(
        self, mock_process_video, mock_cloud_uploader, test_params
    ):
        """Test the process_video method with standard strategy."""
        # Setup mock return value
        expected_result = {
            "lottie_path": "/tmp/test/output/animation.json",
            "thumbnail_path": "/tmp/test/output/thumbnail.png",
            "frame_count": 24,
            "duration": 1.0,
        }
        mock_process_video.return_value = expected_result

        # Create processor and process video
        processor = VideoProcessor(cloud_uploader=mock_cloud_uploader)
        result = processor.process_video(test_params)

        # Verify results
        assert result == expected_result
        mock_process_video.assert_called_once()

    @patch(
        "app.infrastructure.video_processing.high_quality_strategy.HighQualityVideoProcessingStrategy.process_video"
    )
    def test_process_video_high_quality(self, mock_process_video, mock_cloud_uploader):
        """Test the process_video method with high quality strategy."""
        # Setup test parameters with high quality strategy
        params = (
            VideoProcessingParamBuilder()
            .with_file_path("/path/to/video.mp4")
            .with_temp_dir("/tmp/test")
            .with_fps(24)
            .with_dimensions(512, 512)
            .with_original_filename("video.mp4")
            .with_strategy(VideoProcessingStrategy.HIGH_QUALITY)
            .with_max_frames(100)
            .with_optimization(True, True)
            .build()
        )

        # Setup mock return value
        expected_result = {
            "lottie_path": "/tmp/test/output/animation.json",
            "thumbnail_path": "/tmp/test/output/thumbnail.png",
            "frame_count": 24,
            "duration": 1.0,
            "quality": "high",
        }
        mock_process_video.return_value = expected_result

        # Create processor and process video
        processor = VideoProcessor(cloud_uploader=mock_cloud_uploader)
        result = processor.process_video(params)

        # Verify results
        assert result == expected_result
        mock_process_video.assert_called_once()

    @patch(
        "app.infrastructure.video_processing.fast_strategy.FastVideoProcessingStrategy.process_video"
    )
    def test_process_video_fast(self, mock_process_video, mock_cloud_uploader):
        """Test the process_video method with fast strategy."""
        # Setup test parameters with fast strategy
        params = (
            VideoProcessingParamBuilder()
            .with_file_path("/path/to/video.mp4")
            .with_temp_dir("/tmp/test")
            .with_fps(24)
            .with_dimensions(512, 512)
            .with_original_filename("video.mp4")
            .with_strategy(VideoProcessingStrategy.FAST)
            .with_max_frames(50)
            .with_optimization(True, True)
            .build()
        )

        # Setup mock return value
        expected_result = {
            "lottie_path": "/tmp/test/output/animation.json",
            "thumbnail_path": "/tmp/test/output/thumbnail.png",
            "frame_count": 12,
            "duration": 1.0,
            "quality": "fast",
        }
        mock_process_video.return_value = expected_result

        # Create processor and process video
        processor = VideoProcessor(cloud_uploader=mock_cloud_uploader)
        result = processor.process_video(params)

        # Verify results
        assert result == expected_result
        mock_process_video.assert_called_once()

    def test_process_video_file_not_found(self, mock_cloud_uploader):
        """Test the process_video method with a non-existent file."""
        # Setup test parameters with non-existent file
        params = (
            VideoProcessingParamBuilder()
            .with_file_path("/path/to/nonexistent.mp4")
            .with_temp_dir("/tmp/test")
            .with_fps(24)
            .with_dimensions(512, 512)
            .with_original_filename("nonexistent.mp4")
            .with_strategy(VideoProcessingStrategy.STANDARD)
            .with_max_frames(100)
            .with_optimization(True, True)
            .build()
        )

        # Create processor
        processor = VideoProcessor(cloud_uploader=mock_cloud_uploader)

        # Process video should raise ValueError
        with pytest.raises(ValueError) as excinfo:
            processor.process_video(params)

        # Verify error message
        assert "does not exist" in str(excinfo.value)
