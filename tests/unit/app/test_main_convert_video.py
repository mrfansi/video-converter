"""Unit tests for the convert_video_format_task function in the main module."""

import pytest
from unittest.mock import patch, MagicMock, ANY

from tests.base_test import BaseTest


class TestConvertVideoFormatTask(BaseTest):
    """Tests for the convert_video_format_task function in the main module."""

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
                "type": "convert_video_format",
                "params": {
                    "video_path": "/tmp/test.mp4",
                    "output_format": "webm",
                    "quality": "medium",
                    "resolution": "720p",
                    "framerate": 30,
                },
                "status": "pending",
            }
            mock_instance.update_task_status.return_value = None
            mock_instance.update_task_progress.return_value = None
            mock_instance.update_task_result.return_value = None
            mock.return_value = mock_instance
            yield mock

    @pytest.fixture
    def mock_video_converter(self):
        """Mock the convert_video function."""
        with patch("app.main.convert_video") as mock:
            mock.return_value = {"success": True, "output_path": "/tmp/output.webm"}
            yield mock

    @pytest.fixture
    def mock_uploader(self):
        """Mock the CloudflareR2Uploader class."""
        with patch("app.main.CloudflareR2Uploader") as mock:
            mock_instance = MagicMock()
            mock_instance.upload_file.return_value = {
                "key": "test-key",
                "url": "https://cdn.example.com/test-key",
            }
            mock.return_value = mock_instance
            yield mock

    @pytest.fixture
    def mock_utils(self):
        """Mock the utils module functions."""
        with patch("app.main.utils") as mock:
            mock.create_temp_dir.return_value = "/tmp/temp_dir"
            mock.cleanup_temp_files.return_value = None
            yield mock

    @pytest.fixture
    def mock_os(self):
        """Mock os functions."""
        with patch("app.main.os") as mock:
            mock.path.exists.return_value = True
            mock.makedirs.return_value = None
            yield mock

    def test_convert_video_format_task_basic(
        self, mock_task_queue, mock_video_converter, mock_uploader, mock_utils, mock_os
    ):
        """Test basic functionality of convert_video_format_task."""
        # Import here to avoid circular import issues with mocks
        from app.main import convert_video_format_task

        # Call the function
        result = convert_video_format_task("test-task-id")

        # Assertions
        assert result is not None
        assert "success" in result
        assert result["success"] is True
        assert "output_url" in result
        assert result["output_url"] == "https://cdn.example.com/test-key"

        # Verify the mocks were called correctly
        mock_task_queue.return_value.get_task.assert_called_once_with("test-task-id")
        mock_task_queue.return_value.update_task_status.assert_any_call(
            "test-task-id", "processing"
        )
        mock_task_queue.return_value.update_task_status.assert_any_call(
            "test-task-id", "completed"
        )
        mock_video_converter.assert_called_once_with(
            "/tmp/test.mp4",
            ANY,  # Temp directory
            "webm",
            quality="medium",
            resolution="720p",
            framerate=30,
            progress_callback=ANY,
        )
        mock_uploader.return_value.upload_file.assert_called_once()

    def test_convert_video_format_task_with_different_formats(
        self, mock_task_queue, mock_video_converter, mock_uploader, mock_utils, mock_os
    ):
        """Test convert_video_format_task with different output formats."""
        # Import here to avoid circular import issues with mocks
        from app.main import convert_video_format_task

        # Test with different formats
        formats = ["mp4", "webm", "gif"]

        for fmt in formats:
            # Update the mock task with the current format
            mock_task = mock_task_queue.return_value.get_task.return_value.copy()
            mock_task["params"]["output_format"] = fmt
            mock_task_queue.return_value.get_task.return_value = mock_task

            # Update the mock converter output path
            mock_video_converter.return_value = {
                "success": True,
                "output_path": f"/tmp/output.{fmt}",
            }

            # Call the function
            result = convert_video_format_task("test-task-id")

            # Assertions
            assert result is not None
            assert "success" in result
            assert result["success"] is True

            # Verify the converter was called with the correct format
            mock_video_converter.assert_called_with(
                "/tmp/test.mp4",
                ANY,  # Temp directory
                fmt,
                quality="medium",
                resolution="720p",
                framerate=30,
                progress_callback=ANY,
            )

    def test_convert_video_format_task_error_handling(
        self, mock_task_queue, mock_video_converter, mock_utils, mock_os
    ):
        """Test error handling in convert_video_format_task."""
        # Mock the converter to return an error
        mock_video_converter.return_value = {
            "success": False,
            "error": "Conversion failed",
        }

        # Import here to avoid circular import issues with mocks
        from app.main import convert_video_format_task

        # Call the function
        result = convert_video_format_task("test-task-id")

        # Assertions
        assert result is not None
        assert "success" in result
        assert result["success"] is False
        assert "error" in result
        assert "Conversion failed" in result["error"]

        # Verify the task status was updated to failed
        mock_task_queue.return_value.update_task_status.assert_any_call(
            "test-task-id", "failed"
        )

    def test_convert_video_format_task_invalid_input(
        self, mock_task_queue, mock_video_converter, mock_utils, mock_os
    ):
        """Test convert_video_format_task with invalid input file."""
        # Mock os.path.exists to return False (file doesn't exist)
        mock_os.path.exists.return_value = False

        # Import here to avoid circular import issues with mocks
        from app.main import convert_video_format_task

        # Call the function
        result = convert_video_format_task("test-task-id")

        # Assertions
        assert result is not None
        assert "success" in result
        assert result["success"] is False
        assert "error" in result
        assert "not found" in result["error"]

    def test_convert_video_format_task_progress_tracking(
        self, mock_task_queue, mock_video_converter, mock_uploader, mock_utils, mock_os
    ):
        """Test progress tracking in convert_video_format_task."""
        # Capture the progress callback
        progress_callback = None

        def capture_callback(*args, **kwargs):
            nonlocal progress_callback
            for key, value in kwargs.items():
                if key == "progress_callback":
                    progress_callback = value
            return mock_video_converter.return_value

        mock_video_converter.side_effect = capture_callback

        # Import here to avoid circular import issues with mocks
        from app.main import convert_video_format_task

        # Call the function
        result = convert_video_format_task("test-task-id")

        # Assertions
        assert result is not None
        assert "success" in result
        assert result["success"] is True

        # Verify progress callback was passed
        assert progress_callback is not None

        # Test the progress callback
        progress_callback(25)
        mock_task_queue.return_value.update_task_progress.assert_called_with(
            "test-task-id", 25
        )

        progress_callback(50)
        mock_task_queue.return_value.update_task_progress.assert_called_with(
            "test-task-id", 50
        )

        progress_callback(100)
        mock_task_queue.return_value.update_task_progress.assert_called_with(
            "test-task-id", 100
        )
