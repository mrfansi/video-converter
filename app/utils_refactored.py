"""Refactored utility functions for the Video Converter project.

This module provides refactored utility functions using the Strategy pattern
for improved maintainability and extensibility.
"""

import logging
from typing import List, Optional

from app.infrastructure.frame_extractor import FrameExtractor
from app.models.video_params import (
    FrameExtractionParamBuilder,
    FrameExtractionMethod,
)

logger = logging.getLogger(__name__)


def extract_frames(
    video_path: str,
    output_dir: str,
    fps: int = 24,
    width: Optional[int] = None,
    height: Optional[int] = None,
) -> List[str]:
    """
    Extract frames from a video file at a specified FPS using the Strategy pattern.

    This is a refactored version of the original extract_frames function that uses
    the Strategy pattern for improved maintainability and extensibility.

    Args:
        video_path (str): Path to the video file
        output_dir (str): Directory to save the extracted frames
        fps (int): Frames per second to extract
        width (Optional[int]): Width to resize frames to
        height (Optional[int]): Height to resize frames to

    Returns:
        List[str]: List of paths to extracted frame images

    Raises:
        ValueError: If the input file is invalid or the extraction fails
    """
    try:
        logger.info(f"Extracting frames from {video_path} at {fps} fps")

        # Create frame extraction parameters using the builder pattern
        params = (
            FrameExtractionParamBuilder()
            .with_input_path(video_path)
            .with_output_dir(output_dir)
            .with_fps(fps)
            .with_extraction_method(FrameExtractionMethod.HYBRID)
        )

        # Add dimensions if specified
        if width is not None and height is not None:
            params.with_dimensions(width, height)

        # Build the parameters
        extraction_params = params.build()

        # Create frame extractor and extract frames
        extractor = FrameExtractor()
        frame_files = extractor.extract_frames(extraction_params)

        logger.info(f"Successfully extracted {len(frame_files)} frames")
        return frame_files

    except Exception as e:
        logger.error(f"Error extracting frames: {str(e)}")
        raise
