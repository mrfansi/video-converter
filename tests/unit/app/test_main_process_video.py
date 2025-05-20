"""Unit tests for the process_video_task function in the main module."""

import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, call, ANY

from tests.base_test import BaseTest


class TestProcessVideoTask(BaseTest):
    """Tests for the process_video_task function in the main module."""
    
    def setup_method(self, method):
        """Set up test method."""
        super().setup_method(method)
        # Create test data directory for this test
        self.test_output_dir = self.test_data_dir / "output"
        self.test_output_dir.mkdir(exist_ok=True)
    
    @pytest.fixture
    def mock_task_queue(self):
        """Mock the TaskQueue class."""
        with patch("app.main.TaskQueue") as mock:
            mock_instance = MagicMock()
            mock_instance.get_task.return_value = {
                "id": "test-task-id",
                "type": "process_video",
                "params": {
                    "video_url": "https://example.com/test.mp4",
                    "output_format": "lottie",
                    "quality": "medium",
                    "frame_rate": 12
                },
                "status": "pending"
            }
            mock_instance.update_task_status.return_value = None
            mock_instance.update_task_progress.return_value = None
            mock_instance.update_task_result.return_value = None
            mock.return_value = mock_instance
            yield mock
    
    @pytest.fixture
    def mock_downloader(self):
        """Mock the download_file function."""
        with patch("app.main.download_file") as mock:
            mock.return_value = "/tmp/downloaded_test.mp4"
            yield mock
    
    @pytest.fixture
    def mock_utils(self):
        """Mock the utils module functions."""
        with patch("app.main.utils") as mock:
            mock.extract_frames.return_value = ["/tmp/frame_001.png", "/tmp/frame_002.png"]
            mock.create_temp_dir.return_value = "/tmp/temp_dir"
            mock.cleanup_temp_files.return_value = None
            yield mock
    
    @pytest.fixture
    def mock_lottie_generator(self):
        """Mock the LottieGenerator class."""
        with patch("app.main.LottieGenerator") as mock:
            mock_instance = MagicMock()
            mock_instance.generate_lottie_from_frames.return_value = "/tmp/output.json"
            mock.return_value = mock_instance
            yield mock
    
    @pytest.fixture
    def mock_uploader(self):
        """Mock the CloudflareR2Uploader class."""
        with patch("app.main.CloudflareR2Uploader") as mock:
            mock_instance = MagicMock()
            mock_instance.upload_file.return_value = {
                "key": "test-key",
                "url": "https://cdn.example.com/test-key"
            }
            mock.return_value = mock_instance
            yield mock
    
    @pytest.fixture
    def mock_os(self):
        """Mock os functions."""
        with patch("app.main.os") as mock:
            mock.path.exists.return_value = True
            mock.makedirs.return_value = None
            yield mock
    
    def test_process_video_task_lottie(self, mock_task_queue, mock_downloader, mock_utils, 
                                      mock_lottie_generator, mock_uploader, mock_os):
        """Test process_video_task function with Lottie output format."""
        # Import here to avoid circular import issues with mocks
        from app.main import process_video_task
        
        # Call the function
        result = process_video_task("test-task-id")
        
        # Assertions
        assert result is not None
        assert "success" in result
        assert result["success"] is True
        assert "output_url" in result
        assert result["output_url"] == "https://cdn.example.com/test-key"
        
        # Verify the mocks were called correctly
        mock_task_queue.return_value.get_task.assert_called_once_with("test-task-id")
        mock_task_queue.return_value.update_task_status.assert_any_call("test-task-id", "processing")
        mock_task_queue.return_value.update_task_status.assert_any_call("test-task-id", "completed")
        mock_downloader.assert_called_once()
        mock_utils.extract_frames.assert_called_once()
        mock_lottie_generator.return_value.generate_lottie_from_frames.assert_called_once()
        mock_uploader.return_value.upload_file.assert_called_once()
    
    def test_process_video_task_video_format(self, mock_task_queue, mock_downloader, mock_utils, mock_uploader, mock_os):
        """Test process_video_task function with video output format."""
        # Mock the task to request video format conversion
        mock_task_queue.return_value.get_task.return_value = {
            "id": "test-task-id",
            "type": "process_video",
            "params": {
                "video_url": "https://example.com/test.mp4",
                "output_format": "webm",
                "quality": "medium"
            },
            "status": "pending"
        }
        
        # Mock the video converter
        with patch("app.main.convert_video") as mock_converter:
            mock_converter.return_value = {
                "success": True,
                "output_path": "/tmp/output.webm"
            }
            
            # Import here to avoid circular import issues with mocks
            from app.main import process_video_task
            
            # Call the function
            result = process_video_task("test-task-id")
            
            # Assertions
            assert result is not None
            assert "success" in result
            assert result["success"] is True
            assert "output_url" in result
            
            # Verify the mocks were called correctly
            mock_converter.assert_called_once()
            mock_uploader.return_value.upload_file.assert_called_once()
    
    def test_process_video_task_error_handling(self, mock_task_queue, mock_downloader, mock_utils, mock_os):
        """Test error handling in process_video_task."""
        # Mock the downloader to raise an exception
        mock_downloader.side_effect = Exception("Download failed")
        
        # Import here to avoid circular import issues with mocks
        from app.main import process_video_task
        
        # Call the function
        result = process_video_task("test-task-id")
        
        # Assertions
        assert result is not None
        assert "success" in result
        assert result["success"] is False
        assert "error" in result
        assert "Download failed" in result["error"]
        
        # Verify the task status was updated to failed
        mock_task_queue.return_value.update_task_status.assert_any_call("test-task-id", "failed")
    
    def test_process_video_task_invalid_format(self, mock_task_queue, mock_downloader, mock_utils, mock_os):
        """Test process_video_task with invalid output format."""
        # Mock the task to request an invalid format
        mock_task_queue.return_value.get_task.return_value = {
            "id": "test-task-id",
            "type": "process_video",
            "params": {
                "video_url": "https://example.com/test.mp4",
                "output_format": "invalid_format",
                "quality": "medium"
            },
            "status": "pending"
        }
        
        # Import here to avoid circular import issues with mocks
        from app.main import process_video_task
        
        # Call the function
        result = process_video_task("test-task-id")
        
        # Assertions
        assert result is not None
        assert "success" in result
        assert result["success"] is False
        assert "error" in result
        assert "Unsupported output format" in result["error"]
    
    def test_process_video_task_progress_tracking(self, mock_task_queue, mock_downloader, mock_utils, 
                                                mock_lottie_generator, mock_uploader, mock_os):
        """Test progress tracking in process_video_task."""
        # Import here to avoid circular import issues with mocks
        from app.main import process_video_task
        
        # Call the function
        result = process_video_task("test-task-id")
        
        # Assertions
        assert result is not None
        assert "success" in result
        assert result["success"] is True
        
        # Verify progress updates were called
        assert mock_task_queue.return_value.update_task_progress.call_count >= 3
