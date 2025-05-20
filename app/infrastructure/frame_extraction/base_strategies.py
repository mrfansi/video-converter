"""Base strategies for frame extraction.

This module provides base implementations for frame extraction strategies
following the Strategy pattern for improved maintainability and extensibility.
"""

import os
import logging
import cv2
import numpy as np
from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.interfaces.frame_extraction import (
    IFrameExtractionStrategy,
    IFrameQualityValidator,
    IFrameResizer,
    IFrameWriter,
)

logger = logging.getLogger(__name__)


class BaseFrameQualityValidator(IFrameQualityValidator):
    """Base implementation of frame quality validator.

    This class provides a base implementation for validating frame quality,
    detecting blank or corrupted frames.
    """

    def __init__(self, mean_threshold: float = 5.0, std_threshold: float = 3.0):
        """Initialize the frame quality validator.

        Args:
            mean_threshold (float): Mean pixel value threshold for blank frame detection
            std_threshold (float): Standard deviation threshold for blank frame detection
        """
        self.mean_threshold = mean_threshold
        self.std_threshold = std_threshold

    def validate_frame(self, frame) -> bool:
        """Validate the quality of a frame.

        Args:
            frame: The frame to validate (OpenCV image)

        Returns:
            bool: True if the frame is valid, False otherwise
        """
        if frame is None:
            return False

        mean_val = np.mean(frame)
        std_val = np.std(frame)

        if mean_val < self.mean_threshold or std_val < self.std_threshold:
            logger.warning(f"Frame appears blank (mean={mean_val}, std={std_val})")
            return False

        return True

    def validate_frame_file(self, frame_path: str) -> bool:
        """Validate the quality of a frame file.

        Args:
            frame_path (str): Path to the frame file

        Returns:
            bool: True if the frame is valid, False otherwise
        """
        if not os.path.exists(frame_path):
            return False

        img = cv2.imread(frame_path)
        return self.validate_frame(img)


class BaseFrameResizer(IFrameResizer):
    """Base implementation of frame resizer.

    This class provides a base implementation for resizing frames.
    """

    def resize_frame(self, frame, target_width: int, target_height: int):
        """Resize a frame to the target dimensions.

        Args:
            frame: The frame to resize (OpenCV image)
            target_width (int): Target width
            target_height (int): Target height

        Returns:
            The resized frame
        """
        if frame is None:
            return None

        if target_width is None or target_height is None:
            return frame

        # Get current dimensions
        height, width = frame.shape[:2]

        # Skip resizing if dimensions already match
        if width == target_width and height == target_height:
            return frame

        # Resize the frame
        return cv2.resize(frame, (target_width, target_height))


class BaseFrameWriter(IFrameWriter):
    """Base implementation of frame writer.

    This class provides a base implementation for writing frames to disk.
    """

    def __init__(self, quality: int = 90):
        """Initialize the frame writer.

        Args:
            quality (int): Quality of the output image (1-100)
        """
        self.quality = quality

    def write_frame(self, frame, output_path: str) -> str:
        """Write a frame to disk.

        Args:
            frame: The frame to write (OpenCV image)
            output_path (str): Path to write the frame to

        Returns:
            str: Path to the written frame
        """
        if frame is None:
            raise ValueError("Cannot write None frame")

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Write the frame
        params = [cv2.IMWRITE_PNG_COMPRESSION, min(9, max(0, 100 - self.quality) // 10)]
        success = cv2.imwrite(output_path, frame, params)

        if not success:
            raise IOError(f"Failed to write frame to {output_path}")

        return output_path


class BaseFrameExtractionStrategy(IFrameExtractionStrategy, ABC):
    """Base implementation of frame extraction strategy.

    This abstract class provides common functionality for frame extraction strategies.
    """

    def __init__(
        self,
        quality_validator: Optional[IFrameQualityValidator] = None,
        frame_resizer: Optional[IFrameResizer] = None,
        frame_writer: Optional[IFrameWriter] = None,
    ):
        """Initialize the frame extraction strategy.

        Args:
            quality_validator (Optional[IFrameQualityValidator]): Validator for frame quality
            frame_resizer (Optional[IFrameResizer]): Resizer for frames
            frame_writer (Optional[IFrameWriter]): Writer for frames
        """
        self.quality_validator = quality_validator or BaseFrameQualityValidator()
        self.frame_resizer = frame_resizer or BaseFrameResizer()
        self.frame_writer = frame_writer or BaseFrameWriter()

    @abstractmethod
    def extract_frames(
        self,
        video_path: str,
        output_dir: str,
        fps: int = 24,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ) -> List[str]:
        """Extract frames from a video file.

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
        pass
