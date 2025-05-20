"""Concrete strategies for frame extraction.

This module provides concrete implementations for frame extraction strategies
following the Strategy pattern for improved maintainability and extensibility.
"""

import os
import logging
import cv2
import subprocess
from typing import List, Optional

from app.domain.interfaces.frame_extraction import (
    IFrameQualityValidator,
    IFrameResizer,
    IFrameWriter,
)
from app.infrastructure.frame_extraction.base_strategies import (
    BaseFrameExtractionStrategy,
)

logger = logging.getLogger(__name__)


class FFmpegExtractionStrategy(BaseFrameExtractionStrategy):
    """Frame extraction strategy using FFmpeg.

    This strategy uses FFmpeg for frame extraction, which is more reliable
    for most videos but provides less control over frame processing.
    """

    def __init__(
        self,
        quality_validator: Optional[IFrameQualityValidator] = None,
        frame_resizer: Optional[IFrameResizer] = None,
        frame_writer: Optional[IFrameWriter] = None,
        extra_params: Optional[List[str]] = None,
    ):
        """Initialize the FFmpeg extraction strategy.

        Args:
            quality_validator (Optional[IFrameQualityValidator]): Validator for frame quality
            frame_resizer (Optional[IFrameResizer]): Resizer for frames
            frame_writer (Optional[IFrameWriter]): Writer for frames
            extra_params (Optional[List[str]]): Additional FFmpeg parameters
        """
        super().__init__(quality_validator, frame_resizer, frame_writer)
        self.extra_params = extra_params or []

    def extract_frames(
        self,
        video_path: str,
        output_dir: str,
        fps: int = 24,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ) -> List[str]:
        """Extract frames from a video file using FFmpeg.

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
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Define output pattern for frames
        output_pattern = os.path.join(output_dir, "frame_%04d.png")

        # Build scaling option if dimensions are provided
        scale_option = ""
        if width is not None and height is not None:
            scale_option = f",scale={width}:{height}"

        # Build FFmpeg command
        ffmpeg_cmd = [
            "ffmpeg",
            "-i",
            video_path,
            "-vf",
            f"fps={fps}{scale_option}",
            "-pix_fmt",
            "rgb24",
            "-q:v",
            "1",  # High quality
            output_pattern,
            "-y",  # Overwrite existing files
        ]

        # Add any extra parameters
        if self.extra_params:
            ffmpeg_cmd.extend(self.extra_params)

        # Run FFmpeg command
        logger.info(f"Running FFmpeg command: {' '.join(ffmpeg_cmd)}")
        process = subprocess.run(
            ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        # Check if FFmpeg succeeded
        if process.returncode != 0:
            error_msg = f"FFmpeg extraction failed: {process.stderr}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Get the extracted frames
        frame_files = sorted(
            [
                os.path.join(output_dir, f)
                for f in os.listdir(output_dir)
                if f.startswith("frame_") and f.endswith(".png")
            ]
        )

        # Validate frames
        valid_frames = []
        for frame_file in frame_files:
            if self.quality_validator.validate_frame_file(frame_file):
                valid_frames.append(frame_file)
            else:
                logger.warning(f"Removing invalid frame: {frame_file}")
                os.remove(frame_file)

        # Check if we have valid frames
        if not valid_frames:
            error_msg = "FFmpeg extraction produced no valid frames"
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info(f"Successfully extracted {len(valid_frames)} frames using FFmpeg")
        return valid_frames


class OpenCVExtractionStrategy(BaseFrameExtractionStrategy):
    """Frame extraction strategy using OpenCV.

    This strategy uses OpenCV for frame extraction, which provides more
    control over frame processing but may be less reliable for some videos.
    """

    def extract_frames(
        self,
        video_path: str,
        output_dir: str,
        fps: int = 24,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ) -> List[str]:
        """Extract frames from a video file using OpenCV.

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
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Open the video file
        logger.info(f"Opening video file with OpenCV: {video_path}")
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            error_msg = f"Could not open video file: {video_path}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        try:
            # Get video properties
            video_fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            original_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            original_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            # Use provided dimensions or original video dimensions
            target_width = width if width is not None else original_width
            target_height = height if height is not None else original_height

            logger.info(
                f"Video properties: {total_frames} frames, {video_fps} fps, {original_width}x{original_height}"
            )
            logger.info(f"Target dimensions: {target_width}x{target_height}")

            # Calculate frame interval based on desired fps
            frame_interval = max(1, int(video_fps / fps))

            # Extract frames
            frame_files = []

            # Use frame positions to extract evenly spaced frames
            num_frames = min(total_frames, int(total_frames / frame_interval))
            logger.info(f"Extracting {num_frames} frames at interval {frame_interval}")

            for i in range(num_frames):
                # Set position to exact frame we want
                frame_pos = i * frame_interval
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)

                # Read the frame
                ret, frame = cap.read()
                if not ret:
                    logger.warning(f"Failed to read frame at position {frame_pos}")
                    continue

                # Validate frame quality
                if not self.quality_validator.validate_frame(frame):
                    continue

                # Resize frame if needed
                if target_width != original_width or target_height != original_height:
                    frame = self.frame_resizer.resize_frame(
                        frame, target_width, target_height
                    )

                # Save the frame
                frame_file = os.path.join(output_dir, f"frame_{i:04d}.png")
                self.frame_writer.write_frame(frame, frame_file)
                frame_files.append(frame_file)

                # Log progress
                if i % 10 == 0:
                    logger.info(f"Extracted frame {i} at position {frame_pos}")

            # Check if we have valid frames
            if not frame_files:
                error_msg = "Failed to extract any valid frames from video"
                logger.error(error_msg)
                raise ValueError(error_msg)

            logger.info(
                f"Successfully extracted {len(frame_files)} frames using OpenCV"
            )
            return frame_files

        finally:
            # Release the video capture object
            cap.release()


class HybridExtractionStrategy(BaseFrameExtractionStrategy):
    """Hybrid frame extraction strategy.

    This strategy tries FFmpeg first and falls back to OpenCV if FFmpeg fails.
    It combines the reliability of FFmpeg with the flexibility of OpenCV.
    """

    def __init__(
        self,
        quality_validator: Optional[IFrameQualityValidator] = None,
        frame_resizer: Optional[IFrameResizer] = None,
        frame_writer: Optional[IFrameWriter] = None,
        extra_ffmpeg_params: Optional[List[str]] = None,
    ):
        """Initialize the hybrid extraction strategy.

        Args:
            quality_validator (Optional[IFrameQualityValidator]): Validator for frame quality
            frame_resizer (Optional[IFrameResizer]): Resizer for frames
            frame_writer (Optional[IFrameWriter]): Writer for frames
            extra_ffmpeg_params (Optional[List[str]]): Additional FFmpeg parameters
        """
        super().__init__(quality_validator, frame_resizer, frame_writer)
        self.ffmpeg_strategy = FFmpegExtractionStrategy(
            quality_validator, frame_resizer, frame_writer, extra_ffmpeg_params
        )
        self.opencv_strategy = OpenCVExtractionStrategy(
            quality_validator, frame_resizer, frame_writer
        )

    def extract_frames(
        self,
        video_path: str,
        output_dir: str,
        fps: int = 24,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ) -> List[str]:
        """Extract frames from a video file using a hybrid approach.

        This method tries FFmpeg first and falls back to OpenCV if FFmpeg fails.

        Args:
            video_path (str): Path to the video file
            output_dir (str): Directory to save the extracted frames
            fps (int): Frames per second to extract
            width (Optional[int]): Width to resize frames to
            height (Optional[int]): Height to resize frames to

        Returns:
            List[str]: List of paths to extracted frame images

        Raises:
            ValueError: If both extraction methods fail
        """
        try:
            # Try FFmpeg first
            logger.info("Attempting frame extraction with FFmpeg")
            return self.ffmpeg_strategy.extract_frames(
                video_path, output_dir, fps, width, height
            )

        except Exception as e:
            # If FFmpeg fails, try OpenCV
            logger.warning(
                f"FFmpeg extraction failed: {str(e)}. Falling back to OpenCV."
            )

            # Clean up any partial FFmpeg output
            for f in os.listdir(output_dir):
                if f.startswith("frame_") and f.endswith(".png"):
                    try:
                        os.remove(os.path.join(output_dir, f))
                    except Exception as rm_error:
                        logger.warning(f"Failed to remove file {f}: {str(rm_error)}")

            try:
                # Try OpenCV
                return self.opencv_strategy.extract_frames(
                    video_path, output_dir, fps, width, height
                )

            except Exception as opencv_error:
                # If both methods fail, raise a comprehensive error
                error_msg = f"Both FFmpeg and OpenCV extraction failed. FFmpeg error: {str(e)}. OpenCV error: {str(opencv_error)}"
                logger.error(error_msg)
                raise ValueError(error_msg)
