"""Unit tests for the video processing component strategies.

This module contains tests for the component strategies used in video processing.
"""

import os
import pytest
from unittest.mock import MagicMock, patch

from app.infrastructure.video_processing.component_strategies import (
    StandardFrameProcessor,
    HighQualityFrameProcessor,
    FastFrameProcessor,
    StandardLottieGenerator,
    StandardThumbnailGenerator,
)


class TestFrameProcessors:
    """Test suite for frame processor strategies."""

    @pytest.fixture
    def mock_frame_paths(self):
        """Create mock frame paths."""
        return [
            "/tmp/test/frames/frame_001.png",
            "/tmp/test/frames/frame_002.png",
            "/tmp/test/frames/frame_003.png",
        ]

    @pytest.fixture
    def mock_output_dir(self):
        """Create mock output directory."""
        return "/tmp/test/svg"

    @patch(
        "app.lottie.image_processor_refactored.RefactoredImageProcessor.trace_png_to_svg"
    )
    def test_standard_frame_processor(
        self, mock_trace_png_to_svg, mock_frame_paths, mock_output_dir
    ):
        """Test the StandardFrameProcessor."""
        # Setup mock return values
        mock_trace_png_to_svg.side_effect = [
            "/tmp/test/svg/frame_001.svg",
            "/tmp/test/svg/frame_002.svg",
            "/tmp/test/svg/frame_003.svg",
        ]

        # Create processor and process frames
        processor = StandardFrameProcessor()
        svg_paths = processor.process_frames(
            frame_paths=mock_frame_paths, output_dir=mock_output_dir
        )

        # Verify results
        assert len(svg_paths) == 3
        assert svg_paths[0] == "/tmp/test/svg/frame_001.svg"
        assert svg_paths[1] == "/tmp/test/svg/frame_002.svg"
        assert svg_paths[2] == "/tmp/test/svg/frame_003.svg"
        assert mock_trace_png_to_svg.call_count == 3

    @patch(
        "app.lottie.image_processor_refactored.RefactoredImageProcessor.trace_png_to_svg"
    )
    def test_high_quality_frame_processor(
        self, mock_trace_png_to_svg, mock_frame_paths, mock_output_dir
    ):
        """Test the HighQualityFrameProcessor."""
        # Setup mock return values
        mock_trace_png_to_svg.side_effect = [
            "/tmp/test/svg/frame_001.svg",
            "/tmp/test/svg/frame_002.svg",
            "/tmp/test/svg/frame_003.svg",
        ]

        # Create processor and process frames
        processor = HighQualityFrameProcessor()
        svg_paths = processor.process_frames(
            frame_paths=mock_frame_paths, output_dir=mock_output_dir
        )

        # Verify results
        assert len(svg_paths) == 3
        assert svg_paths[0] == "/tmp/test/svg/frame_001.svg"
        assert svg_paths[1] == "/tmp/test/svg/frame_002.svg"
        assert svg_paths[2] == "/tmp/test/svg/frame_003.svg"
        assert mock_trace_png_to_svg.call_count == 3

        # Verify that the advanced strategy was used
        for call_args in mock_trace_png_to_svg.call_args_list:
            params = call_args[0][0]
            assert params.strategy.value == "advanced"
            assert params.simplify_tolerance == 0.5  # Lower tolerance for more detail

    @patch(
        "app.lottie.image_processor_refactored.RefactoredImageProcessor.trace_png_to_svg"
    )
    def test_fast_frame_processor(
        self, mock_trace_png_to_svg, mock_frame_paths, mock_output_dir
    ):
        """Test the FastFrameProcessor."""
        # Setup mock return values
        mock_trace_png_to_svg.side_effect = [
            "/tmp/test/svg/frame_001.svg",
            "/tmp/test/svg/frame_003.svg",  # Only every other frame for speed
        ]

        # Create processor and process frames
        processor = FastFrameProcessor()
        svg_paths = processor.process_frames(
            frame_paths=mock_frame_paths, output_dir=mock_output_dir
        )

        # Verify results
        assert len(svg_paths) == 2  # Only every other frame is processed
        assert svg_paths[0] == "/tmp/test/svg/frame_001.svg"
        assert svg_paths[1] == "/tmp/test/svg/frame_003.svg"
        assert mock_trace_png_to_svg.call_count == 2

        # Verify that the basic strategy was used
        for call_args in mock_trace_png_to_svg.call_args_list:
            params = call_args[0][0]
            assert params.strategy.value == "basic"
            assert (
                params.simplify_tolerance == 2.0
            )  # Higher tolerance for less detail but faster processing


class TestLottieGenerator:
    """Test suite for Lottie generator strategies."""

    @pytest.fixture
    def mock_svg_paths(self):
        """Create mock SVG paths."""
        return [
            "/tmp/test/svg/frame_001.svg",
            "/tmp/test/svg/frame_002.svg",
            "/tmp/test/svg/frame_003.svg",
        ]

    @pytest.fixture
    def mock_output_path(self):
        """Create mock output path."""
        return "/tmp/test/output/animation.json"

    @patch("app.lottie.lottie_generator.generate_lottie_from_svgs")
    def test_standard_lottie_generator(
        self, mock_generate_lottie, mock_svg_paths, mock_output_path
    ):
        """Test the StandardLottieGenerator."""
        # Setup mock return value
        mock_generate_lottie.return_value = mock_output_path

        # Create generator and generate Lottie
        generator = StandardLottieGenerator()
        lottie_path = generator.generate_lottie(
            svg_paths=mock_svg_paths,
            output_path=mock_output_path,
            fps=24,
            width=512,
            height=512,
        )

        # Verify results
        assert lottie_path == mock_output_path
        mock_generate_lottie.assert_called_once()

        # Verify that the correct parameters were used
        params = mock_generate_lottie.call_args[0][0]
        assert params.frame_paths == mock_svg_paths
        assert params.output_path == mock_output_path
        assert params.fps == 24
        assert params.width == 512
        assert params.height == 512
        assert params.optimization_level.value == 2  # MEDIUM


class TestThumbnailGenerator:
    """Test suite for thumbnail generator strategies."""

    @pytest.fixture
    def mock_frame_path(self):
        """Create mock frame path."""
        return "/tmp/test/frames/frame_001.png"

    @pytest.fixture
    def mock_output_dir(self):
        """Create mock output directory."""
        return "/tmp/test/output"

    @patch("cv2.imread")
    @patch("cv2.resize")
    @patch("cv2.imwrite")
    def test_standard_thumbnail_generator(
        self, mock_imwrite, mock_resize, mock_imread, mock_frame_path, mock_output_dir
    ):
        """Test the StandardThumbnailGenerator."""
        # Setup mock return values
        mock_imread.return_value = MagicMock()  # Mock image
        mock_resize.return_value = MagicMock()  # Mock resized image
        mock_imwrite.return_value = True

        # Create generator and generate thumbnail
        generator = StandardThumbnailGenerator()
        thumbnail_path = generator.generate_thumbnail(
            frame_path=mock_frame_path, output_dir=mock_output_dir
        )

        # Verify results
        assert thumbnail_path == os.path.join(mock_output_dir, "thumbnail.png")
        mock_imread.assert_called_once_with(mock_frame_path)
        mock_resize.assert_called_once()
        mock_imwrite.assert_called_once_with(thumbnail_path, mock_resize.return_value)
