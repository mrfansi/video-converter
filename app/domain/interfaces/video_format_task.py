"""Interfaces for video format task processing strategies.

This module defines the interfaces for video format task processing strategies
following the Strategy pattern for improved maintainability and extensibility.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable


class IVideoFormatTaskStrategy(ABC):
    """Interface for video format task processing strategies."""

    @abstractmethod
    def process_video_format_task(
        self,
        temp_dir: str,
        file_path: str,
        output_format: str,
        quality: str,
        width: Optional[int],
        height: Optional[int],
        bitrate: Optional[str],
        preset: str,
        crf: Optional[int],
        audio_codec: Optional[str],
        audio_bitrate: Optional[str],
        original_filename: Optional[str],
        task_id: Optional[str],
        progress_callback: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """Process a video format task.

        Args:
            temp_dir: Temporary directory for processing
            file_path: Path to the uploaded video file
            output_format: Desired output format (mp4, webm, etc.)
            quality: Quality preset (low, medium, high, veryhigh)
            width: Output width
            height: Output height
            bitrate: Video bitrate (e.g., "1M" for 1 Mbps)
            preset: Encoding preset (ultrafast to veryslow)
            crf: Constant Rate Factor (0-51, lower means better quality)
            audio_codec: Audio codec (aac, mp3, opus, etc.)
            audio_bitrate: Audio bitrate (e.g., "128k")
            original_filename: Original filename of the uploaded video
            task_id: Task ID for progress tracking
            progress_callback: Callback function for progress updates

        Returns:
            Dict[str, Any]: Processing result with URLs
        """
        pass


class ITaskProgressTracker(ABC):
    """Interface for task progress tracking."""

    @abstractmethod
    def update_progress(
        self,
        task_id: str,
        current_step: str,
        percent: int,
        details: Optional[str] = None,
    ) -> None:
        """Update the progress of a task.

        Args:
            task_id: Task ID for progress tracking
            current_step: Current processing step
            percent: Progress percentage (0-100)
            details: Additional details about the progress
        """
        pass


class ICloudUploader(ABC):
    """Interface for cloud uploading."""

    @abstractmethod
    def upload_file(self, file_path: str, content_type: str) -> Dict[str, Any]:
        """Upload a file to cloud storage.

        Args:
            file_path: Path to the file to upload
            content_type: Content type of the file

        Returns:
            Dict[str, Any]: Upload result with URLs
        """
        pass
