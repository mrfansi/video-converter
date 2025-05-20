"""Unit tests for the video processing strategies.

This module contains tests for the main video processing strategies.
"""

import os
import pytest
from unittest.mock import MagicMock, patch
from typing import Dict, Any, List

from app.infrastructure.video_processing.processing_strategies import StandardVideoProcessingStrategy
from app.infrastructure.video_processing.high_quality_strategy import HighQualityVideoProcessingStrategy
from app.infrastructure.video_processing.fast_strategy import FastVideoProcessingStrategy


class TestStandardVideoProcessingStrategy:
    """Test suite for the StandardVideoProcessingStrategy."""
    
    @pytest.fixture
    def mock_frame_processor(self):
        """Create a mock frame processor."""
        processor = MagicMock()
        processor.process_frames.return_value = [
            "/tmp/test/svg/frame_001.svg",
            "/tmp/test/svg/frame_002.svg",
            "/tmp/test/svg/frame_003.svg"
        ]
        return processor
    
    @pytest.fixture
    def mock_lottie_generator(self):
        """Create a mock Lottie generator."""
        generator = MagicMock()
        generator.generate_lottie.return_value = "/tmp/test/output/animation.json"
        return generator
    
    @pytest.fixture
    def mock_thumbnail_generator(self):
        """Create a mock thumbnail generator."""
        generator = MagicMock()
        generator.generate_thumbnail.return_value = "/tmp/test/output/thumbnail.png"
        return generator
    
    @pytest.fixture
    def mock_cloud_uploader(self):
        """Create a mock cloud uploader."""
        uploader = MagicMock()
        uploader.upload_file.return_value = {
            "url": "https://example.com/test.json",
            "object_key": "test.json"
        }
        return uploader
    
    @patch('app.infrastructure.frame_extractor.FrameExtractor.extract_frames')
    def test_process_video(self, mock_extract_frames, mock_frame_processor, mock_lottie_generator, mock_thumbnail_generator, mock_cloud_uploader):
        """Test the process_video method."""
        # Setup mock return values
        mock_extract_frames.return_value = [
            "/tmp/test/frames/frame_001.png",
            "/tmp/test/frames/frame_002.png",
            "/tmp/test/frames/frame_003.png"
        ]
        
        # Create strategy
        strategy = StandardVideoProcessingStrategy(
            frame_processor=mock_frame_processor,
            lottie_generator=mock_lottie_generator,
            thumbnail_generator=mock_thumbnail_generator,
            cloud_uploader=mock_cloud_uploader
        )
        
        # Process video
        result = strategy.process_video(
            file_path="/path/to/video.mp4",
            output_dir="/tmp/test/output",
            temp_dir="/tmp/test",
            fps=24,
            width=512,
            height=512,
            original_filename="video.mp4"
        )
        
        # Verify results
        assert result["lottie_path"] == "/tmp/test/output/animation.json"
        assert result["thumbnail_path"] == "/tmp/test/output/thumbnail.png"
        assert result["frame_count"] == 3
        assert result["duration"] == 3 / 24  # 3 frames at 24 fps
        
        # Verify method calls
        mock_extract_frames.assert_called_once()
        mock_frame_processor.process_frames.assert_called_once()
        mock_lottie_generator.generate_lottie.assert_called_once()
        mock_thumbnail_generator.generate_thumbnail.assert_called_once()
        
        # Verify cloud uploads if uploader is provided
        assert mock_cloud_uploader.upload_file.call_count == 2  # Lottie and thumbnail


class TestHighQualityVideoProcessingStrategy:
    """Test suite for the HighQualityVideoProcessingStrategy."""
    
    @patch('app.infrastructure.frame_extractor.FrameExtractor.extract_frames')
    @patch('app.infrastructure.video_processing.component_strategies.HighQualityFrameProcessor.process_frames')
    @patch('app.infrastructure.video_processing.component_strategies.StandardLottieGenerator.generate_lottie')
    @patch('app.infrastructure.video_processing.component_strategies.StandardThumbnailGenerator.generate_thumbnail')
    def test_process_video(self, mock_generate_thumbnail, mock_generate_lottie, mock_process_frames, mock_extract_frames):
        """Test the process_video method."""
        # Setup mock return values
        mock_extract_frames.return_value = [
            "/tmp/test/frames/frame_001.png",
            "/tmp/test/frames/frame_002.png",
            "/tmp/test/frames/frame_003.png"
        ]
        mock_process_frames.return_value = [
            "/tmp/test/svg/frame_001.svg",
            "/tmp/test/svg/frame_002.svg",
            "/tmp/test/svg/frame_003.svg"
        ]
        mock_generate_lottie.return_value = "/tmp/test/output/animation.json"
        mock_generate_thumbnail.return_value = "/tmp/test/output/thumbnail.png"
        
        # Create strategy
        strategy = HighQualityVideoProcessingStrategy()
        
        # Process video
        result = strategy.process_video(
            file_path="/path/to/video.mp4",
            output_dir="/tmp/test/output",
            temp_dir="/tmp/test",
            fps=24,
            width=512,
            height=512,
            original_filename="video.mp4"
        )
        
        # Verify results
        assert result["lottie_path"] == "/tmp/test/output/animation.json"
        assert result["thumbnail_path"] == "/tmp/test/output/thumbnail.png"
        assert result["frame_count"] == 3
        assert result["duration"] == 3 / 24  # 3 frames at 24 fps
        assert result["quality"] == "high"
        
        # Verify method calls
        mock_extract_frames.assert_called_once()
        mock_process_frames.assert_called_once()
        mock_generate_lottie.assert_called_once()
        mock_generate_thumbnail.assert_called_once()


class TestFastVideoProcessingStrategy:
    """Test suite for the FastVideoProcessingStrategy."""
    
    @patch('app.infrastructure.frame_extractor.FrameExtractor.extract_frames')
    @patch('app.infrastructure.video_processing.component_strategies.FastFrameProcessor.process_frames')
    @patch('app.infrastructure.video_processing.component_strategies.StandardLottieGenerator.generate_lottie')
    @patch('app.infrastructure.video_processing.component_strategies.StandardThumbnailGenerator.generate_thumbnail')
    def test_process_video(self, mock_generate_thumbnail, mock_generate_lottie, mock_process_frames, mock_extract_frames):
        """Test the process_video method."""
        # Setup mock return values
        mock_extract_frames.return_value = [
            "/tmp/test/frames/frame_001.png",
            "/tmp/test/frames/frame_002.png"
        ]
        mock_process_frames.return_value = [
            "/tmp/test/svg/frame_001.svg",
            "/tmp/test/svg/frame_002.svg"
        ]
        mock_generate_lottie.return_value = "/tmp/test/output/animation.json"
        mock_generate_thumbnail.return_value = "/tmp/test/output/thumbnail.png"
        
        # Create strategy
        strategy = FastVideoProcessingStrategy()
        
        # Process video
        result = strategy.process_video(
            file_path="/path/to/video.mp4",
            output_dir="/tmp/test/output",
            temp_dir="/tmp/test",
            fps=24,
            width=512,
            height=512,
            original_filename="video.mp4"
        )
        
        # Verify results
        assert result["lottie_path"] == "/tmp/test/output/animation.json"
        assert result["thumbnail_path"] == "/tmp/test/output/thumbnail.png"
        assert result["frame_count"] == 2
        assert result["duration"] == 2 / 12  # 2 frames at adjusted fps (24/2)
        assert result["quality"] == "fast"
        
        # Verify method calls
        mock_extract_frames.assert_called_once()
        mock_process_frames.assert_called_once()
        mock_generate_lottie.assert_called_once()
        mock_generate_thumbnail.assert_called_once()
