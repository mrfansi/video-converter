"""Base strategies for video processing.

This module provides base implementations for video processing strategies
following the Strategy pattern for improved maintainability and extensibility.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Callable

from app.domain.interfaces.video_processing import (
    IVideoProcessingStrategy,
    IFrameProcessor,
    ILottieGenerator,
    IThumbnailGenerator,
    ICloudUploader,
)

logger = logging.getLogger(__name__)


class BaseFrameProcessor(IFrameProcessor, ABC):
    """Base implementation of frame processor.

    This abstract class provides common functionality for frame processing strategies.
    """

    def __init__(self):
        """Initialize the frame processor."""
        pass

    @abstractmethod
    def process_frames(
        self,
        frame_paths: List[str],
        output_dir: str,
        progress_callback: Optional[Callable] = None,
    ) -> List[str]:
        """Process video frames into SVG files.

        Args:
            frame_paths (List[str]): Paths to the video frames
            output_dir (str): Directory to save the SVG files
            progress_callback (Optional[Callable]): Callback function for progress updates

        Returns:
            List[str]: Paths to the generated SVG files

        Raises:
            ValueError: If the input files are invalid or the processing fails
        """
        pass


class BaseLottieGenerator(ILottieGenerator, ABC):
    """Base implementation of Lottie generator.

    This abstract class provides common functionality for Lottie generation strategies.
    """

    def __init__(self):
        """Initialize the Lottie generator."""
        pass

    @abstractmethod
    def generate_lottie(
        self,
        svg_paths: List[str],
        output_path: str,
        fps: int,
        width: int,
        height: int,
        max_frames: int = 100,
        optimize: bool = True,
        compress: bool = True,
    ) -> str:
        """Generate a Lottie animation from SVG files.

        Args:
            svg_paths (List[str]): Paths to the SVG files
            output_path (str): Path to save the Lottie animation
            fps (int): Frames per second for the animation
            width (int): Width of the animation
            height (int): Height of the animation
            max_frames (int): Maximum number of frames to include
            optimize (bool): Whether to optimize the animation
            compress (bool): Whether to compress the animation

        Returns:
            str: Path to the generated Lottie animation

        Raises:
            ValueError: If the input files are invalid or the generation fails
        """
        pass


class BaseThumbnailGenerator(IThumbnailGenerator, ABC):
    """Base implementation of thumbnail generator.

    This abstract class provides common functionality for thumbnail generation strategies.
    """

    def __init__(self):
        """Initialize the thumbnail generator."""
        pass

    @abstractmethod
    def generate_thumbnail(
        self,
        frame_path: str,
        output_dir: str,
        source_dimensions: Optional[tuple[Any, ...]] = None,
        maintain_aspect_ratio: bool = True,
    ) -> str:
        """Generate a thumbnail from a video frame.

        Args:
            frame_path (str): Path to the video frame
            output_dir (str): Directory to save the thumbnail
            source_dimensions (tuple): Source dimensions (width, height)
            maintain_aspect_ratio (bool): Whether to maintain aspect ratio

        Returns:
            str: Path to the generated thumbnail

        Raises:
            ValueError: If the input file is invalid or the generation fails
        """
        pass


class BaseCloudUploader(ICloudUploader, ABC):
    """Base implementation of cloud uploader.

    This abstract class provides common functionality for cloud upload strategies.
    """

    def __init__(self):
        """Initialize the cloud uploader."""
        pass

    @abstractmethod
    def upload_file(
        self,
        file_path: str,
        content_type: Optional[str] = None,
        custom_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Upload a file to cloud storage.

        Args:
            file_path (str): Path to the file to upload
            content_type (str): Content type of the file
            custom_key (str): Custom key for the file

        Returns:
            Dict[str, Any]: Upload result with URL

        Raises:
            ValueError: If the upload fails
        """
        pass


class BaseVideoProcessingStrategy(IVideoProcessingStrategy, ABC):
    """Base implementation of video processing strategy.

    This abstract class provides common functionality for video processing strategies.
    """

    def __init__(
        self,
        frame_processor: Optional[IFrameProcessor] = None,
        lottie_generator: Optional[ILottieGenerator] = None,
        thumbnail_generator: Optional[IThumbnailGenerator] = None,
        cloud_uploader: Optional[ICloudUploader] = None,
    ):
        """Initialize the video processing strategy.

        Args:
            frame_processor (Optional[IFrameProcessor]): Frame processor to use
            lottie_generator (Optional[ILottieGenerator]): Lottie generator to use
            thumbnail_generator (Optional[IThumbnailGenerator]): Thumbnail generator to use
            cloud_uploader (Optional[ICloudUploader]): Cloud uploader to use
        """
        self.frame_processor = frame_processor
        self.lottie_generator = lottie_generator
        self.thumbnail_generator = thumbnail_generator
        self.cloud_uploader = cloud_uploader

    def update_progress(
        self,
        task_id: str,
        current_step: str,
        completed_steps: Optional[int] = None,
        total_steps: Optional[int] = None,
        percent: Optional[int] = None,
        details: Optional[str] = None,
    ):
        """Update the progress of a task.

        Args:
            task_id (str): Task ID for progress tracking
            current_step (str): Current step name
            completed_steps (int): Number of completed steps
            total_steps (int): Total number of steps
            percent (int): Percentage of completion
            details (str): Additional details
        """
        # This is a placeholder for the actual progress update mechanism
        # In a real implementation, this would call the task queue's update_progress method
        if hasattr(self, "task_queue") and hasattr(self.task_queue, "update_progress"):
            kwargs = {"task_id": task_id, "current_step": current_step}
            if completed_steps is not None:
                kwargs["completed_steps"] = str(completed_steps)
            if total_steps is not None:
                kwargs["total_steps"] = str(total_steps)
            if percent is not None:
                kwargs["percent"] = str(percent)
            if details is not None:
                kwargs["details"] = details

            self.task_queue.update_progress(**kwargs)
        else:
            logger.info(f"Progress update: {current_step} - {details} ({percent}%)")

    def cleanup_temp_files(self, temp_dir: str):
        """Clean up temporary files.

        Args:
            temp_dir (str): Temporary directory to clean up
        """
        try:
            # This is a placeholder for the actual cleanup mechanism
            # In a real implementation, this would delete temporary files
            logger.info(f"Cleaning up temporary files in {temp_dir}")
        except Exception as e:
            logger.warning(f"Error cleaning up temporary files: {str(e)}")

    @abstractmethod
    def process_video(
        self,
        file_path: str,
        output_dir: str,
        temp_dir: str,
        fps: int,
        width: Optional[int] = None,
        height: Optional[int] = None,
        original_filename: Optional[str] = None,
        progress_callback: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """Process a video file into a Lottie animation.

        Args:
            file_path (str): Path to the video file
            output_dir (str): Directory to save the output files
            temp_dir (str): Temporary directory for processing
            fps (int): Frames per second for the animation
            width (Optional[int]): Width of the animation
            height (Optional[int]): Height of the animation
            original_filename (Optional[str]): Original filename of the uploaded video
            progress_callback (Optional[Callable]): Callback function for progress updates

        Returns:
            Dict[str, Any]: Processing result with URLs

        Raises:
            ValueError: If the input file is invalid or the processing fails
        """
        pass
