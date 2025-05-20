"""Unit tests for the image_processor module."""

import os
import pytest
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

from tests.base_test import BaseTest
from app.lottie.image_processor import trace_png_to_svg


class TestImageProcessor(BaseTest):
    """Tests for the image_processor module, focusing on the trace_png_to_svg function."""
    
    def setup_method(self, method):
        """Set up test method."""
        super().setup_method(method)
        # Create test data directory for this test
        self.test_output_dir = self.test_data_dir / "output"
        self.test_output_dir.mkdir(exist_ok=True)
    
    @pytest.fixture
    def mock_cv2(self):
        """Mock OpenCV functions."""
        with patch("app.lottie.image_processor.cv2") as mock:
            # Configure the mock to return appropriate values
            mock.imread.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
            mock.cvtColor.return_value = np.zeros((100, 100), dtype=np.uint8)
            mock.threshold.return_value = (None, np.ones((100, 100), dtype=np.uint8))
            mock.findContours.return_value = ([np.array([[[10, 10]], [[20, 10]], [[20, 20]], [[10, 20]]])], None)
            yield mock
    
    @pytest.fixture
    def mock_simplify_contours(self):
        """Mock the simplify_contours function."""
        with patch("app.lottie.image_processor.simplify_contours") as mock:
            mock.return_value = [np.array([[[10, 10]], [[20, 10]], [[20, 20]], [[10, 20]]])]
            yield mock
    
    @pytest.fixture
    def mock_contours_to_svg_paths(self):
        """Mock the contours_to_svg_paths function."""
        with patch("app.lottie.image_processor.contours_to_svg_paths") as mock:
            mock.return_value = ["M 10 10 L 20 10 L 20 20 L 10 20 Z"]
            yield mock
    
    def test_trace_png_to_svg_basic(self, temp_output_dir, mock_cv2, mock_simplify_contours, mock_contours_to_svg_paths):
        """Test basic functionality of trace_png_to_svg."""
        # Create a test PNG file
        test_png = self.test_data_dir / "test.png"
        self.create_test_file(test_png)
        
        # Call the function
        output_path = temp_output_dir / "output.svg"
        result = trace_png_to_svg(str(test_png), str(output_path))
        
        # Assertions
        assert result == str(output_path)
        self.assert_file_exists(output_path)
        
        # Verify the mocks were called correctly
        mock_cv2.imread.assert_called_once_with(str(test_png))
        mock_cv2.cvtColor.assert_called_once()
        mock_cv2.threshold.assert_called_once()
        mock_cv2.findContours.assert_called_once()
        mock_simplify_contours.assert_called_once()
        mock_contours_to_svg_paths.assert_called_once()
    
    def test_trace_png_to_svg_with_threshold(self, temp_output_dir, mock_cv2, mock_simplify_contours, mock_contours_to_svg_paths):
        """Test trace_png_to_svg with custom threshold."""
        # Create a test PNG file
        test_png = self.test_data_dir / "test.png"
        self.create_test_file(test_png)
        
        # Call the function with custom threshold
        output_path = temp_output_dir / "output_threshold.svg"
        result = trace_png_to_svg(str(test_png), str(output_path), threshold=200)
        
        # Assertions
        assert result == str(output_path)
        self.assert_file_exists(output_path)
        
        # Verify the threshold was used
        _, threshold_value = mock_cv2.threshold.call_args[0][1:3]
        assert threshold_value == 200
    
    def test_trace_png_to_svg_with_simplify(self, temp_output_dir, mock_cv2, mock_simplify_contours, mock_contours_to_svg_paths):
        """Test trace_png_to_svg with simplification options."""
        # Create a test PNG file
        test_png = self.test_data_dir / "test.png"
        self.create_test_file(test_png)
        
        # Call the function with simplification options
        output_path = temp_output_dir / "output_simplify.svg"
        result = trace_png_to_svg(
            str(test_png), 
            str(output_path), 
            simplify=True, 
            simplify_tolerance=2.0
        )
        
        # Assertions
        assert result == str(output_path)
        self.assert_file_exists(output_path)
        
        # Verify simplify_contours was called with the right parameters
        _, tolerance = mock_simplify_contours.call_args[0][1]
        assert tolerance == 2.0
    
    def test_trace_png_to_svg_with_min_contour_area(self, temp_output_dir, mock_cv2, mock_simplify_contours, mock_contours_to_svg_paths):
        """Test trace_png_to_svg with minimum contour area filtering."""
        # Create a test PNG file
        test_png = self.test_data_dir / "test.png"
        self.create_test_file(test_png)
        
        # Call the function with min_contour_area
        output_path = temp_output_dir / "output_min_area.svg"
        result = trace_png_to_svg(
            str(test_png), 
            str(output_path), 
            min_contour_area=100
        )
        
        # Assertions
        assert result == str(output_path)
        self.assert_file_exists(output_path)
    
    def test_trace_png_to_svg_error_handling(self, temp_output_dir):
        """Test error handling in trace_png_to_svg."""
        # Test with non-existent input file
        non_existent_file = self.test_data_dir / "nonexistent.png"
        output_path = temp_output_dir / "error_output.svg"
        
        with pytest.raises(FileNotFoundError):
            trace_png_to_svg(str(non_existent_file), str(output_path))
    
    @patch("app.lottie.image_processor.cv2.imread")
    def test_trace_png_to_svg_with_empty_image(self, mock_imread, temp_output_dir):
        """Test trace_png_to_svg with an empty or invalid image."""
        # Mock imread to return None (indicating failure to load image)
        mock_imread.return_value = None
        
        # Create a test PNG file
        test_png = self.test_data_dir / "empty.png"
        self.create_test_file(test_png)
        
        output_path = temp_output_dir / "empty_output.svg"
        
        with pytest.raises(ValueError, match="Failed to load image"):
            trace_png_to_svg(str(test_png), str(output_path))
