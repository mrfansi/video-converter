"""Unit tests for the utils module."""

import os
import pytest
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock, call

from tests.base_test import BaseTest
from app.utils import extract_frames


class TestUtils(BaseTest):
    """Tests for the utils module, focusing on the extract_frames function."""
    
    def setup_method(self, method):
        """Set up test method."""
        super().setup_method(method)
        # Create test data directory for this test
        self.test_output_dir = self.test_data_dir / "output"
        self.test_output_dir.mkdir(exist_ok=True)
    
    @pytest.fixture
    def mock_cv2(self):
        """Mock OpenCV functions."""
        with patch("app.utils.cv2") as mock:
            # Configure the mock to return appropriate values
            mock.VideoCapture.return_value = MagicMock()
            mock.VideoCapture.return_value.isOpened.return_value = True
            mock.VideoCapture.return_value.get.side_effect = lambda prop: {
                7: 100,  # Frame count
                5: 30,   # FPS
                3: 640,  # Width
                4: 480,  # Height
            }.get(prop, 0)
            
            # Mock read to return 5 frames then False
            mock.VideoCapture.return_value.read.side_effect = [
                (True, np.zeros((480, 640, 3), dtype=np.uint8)) for _ in range(5)
            ] + [(False, None)]
            
            # Mock imwrite
            mock.imwrite.return_value = True
            
            yield mock
    
    @pytest.fixture
    def mock_os(self):
        """Mock os functions."""
        with patch("app.utils.os") as mock:
            mock.path.exists.return_value = True
            mock.makedirs.return_value = None
            yield mock
    
    def test_extract_frames_basic(self, temp_output_dir, mock_cv2, mock_os):
        """Test basic functionality of extract_frames."""
        # Create a test video file
        test_video = self.test_data_dir / "test.mp4"
        self.create_test_file(test_video)
        
        # Call the function
        result = extract_frames(
            str(test_video),
            str(temp_output_dir),
            frame_rate=1
        )
        
        # Assertions
        assert len(result) == 5  # Should have extracted 5 frames
        assert all(Path(frame).name.startswith("frame_") for frame in result)
        
        # Verify the mocks were called correctly
        mock_cv2.VideoCapture.assert_called_once_with(str(test_video))
        assert mock_cv2.imwrite.call_count == 5
    
    def test_extract_frames_with_custom_prefix(self, temp_output_dir, mock_cv2, mock_os):
        """Test extract_frames with custom filename prefix."""
        # Create a test video file
        test_video = self.test_data_dir / "test.mp4"
        self.create_test_file(test_video)
        
        # Call the function with custom prefix
        result = extract_frames(
            str(test_video),
            str(temp_output_dir),
            frame_rate=1,
            filename_prefix="custom_"
        )
        
        # Assertions
        assert len(result) == 5
        assert all(Path(frame).name.startswith("custom_") for frame in result)
    
    def test_extract_frames_with_frame_rate(self, temp_output_dir, mock_cv2, mock_os):
        """Test extract_frames with different frame rates."""
        # Create a test video file
        test_video = self.test_data_dir / "test.mp4"
        self.create_test_file(test_video)
        
        # Call the function with higher frame rate (should extract fewer frames)
        with patch.object(mock_cv2.VideoCapture.return_value, "get", return_value=30):
            result = extract_frames(
                str(test_video),
                str(temp_output_dir),
                frame_rate=10  # Extract at 1/3 of the video's frame rate
            )
            
            # With frame_rate=10 and video FPS=30, we should extract every 3rd frame
            # Since our mock provides 5 frames, we should get 2 frames (0th and 3rd)
            assert len(result) <= 2
    
    def test_extract_frames_with_max_frames(self, temp_output_dir, mock_cv2, mock_os):
        """Test extract_frames with max_frames limit."""
        # Create a test video file
        test_video = self.test_data_dir / "test.mp4"
        self.create_test_file(test_video)
        
        # Call the function with max_frames=2
        result = extract_frames(
            str(test_video),
            str(temp_output_dir),
            frame_rate=1,
            max_frames=2
        )
        
        # Assertions
        assert len(result) == 2  # Should have extracted only 2 frames
    
    def test_extract_frames_with_resize(self, temp_output_dir, mock_cv2, mock_os):
        """Test extract_frames with resize option."""
        # Create a test video file
        test_video = self.test_data_dir / "test.mp4"
        self.create_test_file(test_video)
        
        # Call the function with resize
        result = extract_frames(
            str(test_video),
            str(temp_output_dir),
            frame_rate=1,
            resize=(320, 240)
        )
        
        # Assertions
        assert len(result) == 5
        
        # Verify resize was called
        assert mock_cv2.resize.call_count == 5
        # Check the resize dimensions
        _, size = mock_cv2.resize.call_args[0]
        assert size == (320, 240)
    
    def test_extract_frames_error_handling(self, temp_output_dir, mock_os):
        """Test error handling in extract_frames."""
        # Test with non-existent input file
        with patch("app.utils.cv2.VideoCapture") as mock_capture:
            mock_capture.return_value = MagicMock()
            mock_capture.return_value.isOpened.return_value = False
            
            non_existent_file = self.test_data_dir / "nonexistent.mp4"
            
            with pytest.raises(ValueError, match="Could not open video file"):
                extract_frames(str(non_existent_file), str(temp_output_dir))
    
    def test_extract_frames_with_output_format(self, temp_output_dir, mock_cv2, mock_os):
        """Test extract_frames with different output formats."""
        # Create a test video file
        test_video = self.test_data_dir / "test.mp4"
        self.create_test_file(test_video)
        
        # Call the function with JPEG format
        result = extract_frames(
            str(test_video),
            str(temp_output_dir),
            frame_rate=1,
            output_format="jpg"
        )
        
        # Assertions
        assert len(result) == 5
        assert all(frame.endswith(".jpg") for frame in result)
