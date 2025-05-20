"""Unit tests for the video_converter module."""

import pytest
from unittest.mock import patch, MagicMock

from tests.base_test import BaseTest
from app.video_converter import convert_video


class TestVideoConverter(BaseTest):
    """Tests for the video_converter module, focusing on the convert_video function."""

    def setup_method(self, method):
        """Set up test method."""
        super().setup_method(method)
        # Create test data directory for this test
        self.test_output_dir = self.test_data_dir / "output"
        self.test_output_dir.mkdir(exist_ok=True)

    @pytest.fixture
    def mock_subprocess(self):
        """Mock subprocess functions."""
        with patch("app.video_converter.subprocess") as mock:
            # Configure the mock to return appropriate values
            mock_process = MagicMock()
            mock_process.communicate.return_value = (b"output", b"")
            mock_process.returncode = 0
            mock.Popen.return_value = mock_process
            mock.PIPE = -1  # Just a placeholder
            yield mock

    @pytest.fixture
    def mock_os(self):
        """Mock os functions."""
        with patch("app.video_converter.os") as mock:
            mock.path.exists.return_value = True
            mock.makedirs.return_value = None
            mock.path.getsize.return_value = 1024  # 1KB file size
            yield mock

    @pytest.fixture
    def mock_shutil(self):
        """Mock shutil functions."""
        with patch("app.video_converter.shutil") as mock:
            mock.which.return_value = "/usr/bin/ffmpeg"  # Pretend ffmpeg is installed
            yield mock

    def test_convert_video_basic(
        self, temp_output_dir, mock_subprocess, mock_os, mock_shutil
    ):
        """Test basic functionality of convert_video."""
        # Create a test video file
        test_video = self.test_data_dir / "test.mp4"
        self.create_test_file(test_video)

        # Call the function
        result = convert_video(
            str(test_video), str(temp_output_dir), "webm", quality="medium"
        )

        # Assertions
        assert result["success"] is True
        assert "output_path" in result
        assert result["output_path"].endswith(".webm")

        # Verify the mocks were called correctly
        mock_shutil.which.assert_called_once_with("ffmpeg")
        mock_subprocess.Popen.assert_called_once()
        # Check that ffmpeg command was constructed correctly
        ffmpeg_cmd = mock_subprocess.Popen.call_args[0][0]
        assert ffmpeg_cmd[0] == "/usr/bin/ffmpeg"
        assert "-i" in ffmpeg_cmd
        assert str(test_video) in ffmpeg_cmd

    def test_convert_video_with_different_formats(
        self, temp_output_dir, mock_subprocess, mock_os, mock_shutil
    ):
        """Test convert_video with different output formats."""
        # Create a test video file
        test_video = self.test_data_dir / "test.mp4"
        self.create_test_file(test_video)

        # Test with different formats
        formats = ["mp4", "webm", "gif"]

        for fmt in formats:
            result = convert_video(
                str(test_video), str(temp_output_dir), fmt, quality="medium"
            )

            # Assertions
            assert result["success"] is True
            assert result["output_path"].endswith(f".{fmt}")

    def test_convert_video_with_quality_settings(
        self, temp_output_dir, mock_subprocess, mock_os, mock_shutil
    ):
        """Test convert_video with different quality settings."""
        # Create a test video file
        test_video = self.test_data_dir / "test.mp4"
        self.create_test_file(test_video)

        # Test with different quality settings
        qualities = ["low", "medium", "high"]

        for quality in qualities:
            result = convert_video(
                str(test_video), str(temp_output_dir), "mp4", quality=quality
            )

            # Assertions
            assert result["success"] is True

            # Check that quality parameter affected the ffmpeg command
            ffmpeg_cmd = mock_subprocess.Popen.call_args[0][0]
            if quality == "low":
                assert any(
                    "-crf 28" in " ".join(arg)
                    for arg in zip(ffmpeg_cmd, ffmpeg_cmd[1:])
                )
            elif quality == "medium":
                assert any(
                    "-crf 23" in " ".join(arg)
                    for arg in zip(ffmpeg_cmd, ffmpeg_cmd[1:])
                )
            elif quality == "high":
                assert any(
                    "-crf 18" in " ".join(arg)
                    for arg in zip(ffmpeg_cmd, ffmpeg_cmd[1:])
                )

    def test_convert_video_with_resolution(
        self, temp_output_dir, mock_subprocess, mock_os, mock_shutil
    ):
        """Test convert_video with resolution parameter."""
        # Create a test video file
        test_video = self.test_data_dir / "test.mp4"
        self.create_test_file(test_video)

        # Call the function with resolution
        result = convert_video(
            str(test_video),
            str(temp_output_dir),
            "mp4",
            quality="medium",
            resolution="720p",
        )

        # Assertions
        assert result["success"] is True

        # Check that resolution parameter affected the ffmpeg command
        ffmpeg_cmd = mock_subprocess.Popen.call_args[0][0]
        assert any(
            "-s 1280x720" in " ".join(arg) for arg in zip(ffmpeg_cmd, ffmpeg_cmd[1:])
        )

    def test_convert_video_with_framerate(
        self, temp_output_dir, mock_subprocess, mock_os, mock_shutil
    ):
        """Test convert_video with framerate parameter."""
        # Create a test video file
        test_video = self.test_data_dir / "test.mp4"
        self.create_test_file(test_video)

        # Call the function with framerate
        result = convert_video(
            str(test_video), str(temp_output_dir), "mp4", quality="medium", framerate=24
        )

        # Assertions
        assert result["success"] is True

        # Check that framerate parameter affected the ffmpeg command
        ffmpeg_cmd = mock_subprocess.Popen.call_args[0][0]
        assert any("-r 24" in " ".join(arg) for arg in zip(ffmpeg_cmd, ffmpeg_cmd[1:]))

    def test_convert_video_with_progress_callback(
        self, temp_output_dir, mock_subprocess, mock_os, mock_shutil
    ):
        """Test convert_video with progress callback."""
        # Create a test video file
        test_video = self.test_data_dir / "test.mp4"
        self.create_test_file(test_video)

        # Mock the progress callback
        mock_callback = MagicMock()

        # Mock subprocess.Popen to simulate progress output
        mock_process = MagicMock()
        mock_process.returncode = 0

        # Simulate ffmpeg progress output
        progress_output = b"""frame=  100 fps=25 q=28.0 size=    500kB time=00:00:04.00 bitrate= 1024.0kbits/s speed=1x
        frame=  200 fps=25 q=28.0 size=   1000kB time=00:00:08.00 bitrate= 1024.0kbits/s speed=1x
        frame=  300 fps=25 q=28.0 size=   1500kB time=00:00:12.00 bitrate= 1024.0kbits/s speed=1x"""

        mock_process.stdout = MagicMock()
        mock_process.stdout.readline.side_effect = [
            line + b"\n" for line in progress_output.split(b"\n")
        ] + [b""]
        mock_process.communicate.return_value = (b"", b"")

        with patch("app.video_converter.subprocess.Popen", return_value=mock_process):
            # Call the function with progress callback
            result = convert_video(
                str(test_video),
                str(temp_output_dir),
                "mp4",
                quality="medium",
                progress_callback=mock_callback,
            )

            # Assertions
            assert result["success"] is True
            assert (
                mock_callback.call_count >= 3
            )  # Should be called for each progress line

    def test_convert_video_error_handling(self, temp_output_dir, mock_os, mock_shutil):
        """Test error handling in convert_video."""
        # Test with non-existent input file
        mock_os.path.exists.return_value = False
        non_existent_file = self.test_data_dir / "nonexistent.mp4"

        result = convert_video(str(non_existent_file), str(temp_output_dir), "mp4")

        # Assertions
        assert result["success"] is False
        assert "error" in result
        assert "not found" in result["error"]

    def test_convert_video_ffmpeg_not_found(self, temp_output_dir, mock_os):
        """Test convert_video when ffmpeg is not installed."""
        # Mock shutil.which to return None (ffmpeg not found)
        with patch("app.video_converter.shutil.which", return_value=None):
            test_video = self.test_data_dir / "test.mp4"
            self.create_test_file(test_video)

            result = convert_video(str(test_video), str(temp_output_dir), "mp4")

            # Assertions
            assert result["success"] is False
            assert "error" in result
            assert "ffmpeg not found" in result["error"]

    def test_convert_video_ffmpeg_error(
        self, temp_output_dir, mock_subprocess, mock_os, mock_shutil
    ):
        """Test convert_video when ffmpeg returns an error."""
        # Create a test video file
        test_video = self.test_data_dir / "test.mp4"
        self.create_test_file(test_video)

        # Mock subprocess.Popen to return error
        mock_process = MagicMock()
        mock_process.communicate.return_value = (b"", b"Error: something went wrong")
        mock_process.returncode = 1
        mock_subprocess.Popen.return_value = mock_process

        result = convert_video(str(test_video), str(temp_output_dir), "mp4")

        # Assertions
        assert result["success"] is False
        assert "error" in result
        assert "ffmpeg error" in result["error"]
