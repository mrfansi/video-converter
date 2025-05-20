"""Domain interfaces for video conversion strategies.

This module defines the interfaces for video conversion strategies following
the Strategy pattern for improved maintainability and extensibility.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable


class IVideoConversionStrategy(ABC):
    """Interface for video conversion strategies.

    This interface defines the contract for video conversion strategies
    that can convert video files to different formats with various optimization options.
    """

    @abstractmethod
    def convert_video(
        self,
        input_path: str,
        output_path: str,
        video_codec: str,
        audio_codec: str,
        video_params: Dict[str, Any],
        audio_params: Dict[str, Any],
        width: Optional[int] = None,
        height: Optional[int] = None,
        progress_callback: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """Convert a video file to another format with optimization options.

        Args:
            input_path (str): Path to the input video file
            output_path (str): Path to the output video file
            video_codec (str): Video codec to use
            audio_codec (str): Audio codec to use
            video_params (Dict[str, Any]): Video parameters
            audio_params (Dict[str, Any]): Audio parameters
            width (Optional[int]): Output width
            height (Optional[int]): Output height
            progress_callback (Optional[Callable]): Callback function for progress updates

        Returns:
            Dict[str, Any]: Dictionary with output file information

        Raises:
            ValueError: If the input file is invalid or the conversion fails
        """
        pass


class IVideoCodecSelector(ABC):
    """Interface for video codec selection strategies.

    This interface defines the contract for strategies that select
    appropriate video codecs based on the output format.
    """

    @abstractmethod
    def select_video_codec(self, output_format: str) -> str:
        """Select a video codec based on the output format.

        Args:
            output_format (str): Output format (mp4, webm, mov, avi, etc.)

        Returns:
            str: Selected video codec
        """
        pass


class IAudioCodecSelector(ABC):
    """Interface for audio codec selection strategies.

    This interface defines the contract for strategies that select
    appropriate audio codecs based on the output format.
    """

    @abstractmethod
    def select_audio_codec(self, output_format: str) -> str | None:
        """Select an audio codec based on the output format.

        Args:
            output_format (str): Output format (mp4, webm, mov, avi, etc.)

        Returns:
            str | None: Selected audio codec (None for formats without audio)
        """
        pass


class IVideoScaler(ABC):
    """Interface for video scaling strategies.

    This interface defines the contract for strategies that scale
    videos to specific dimensions.
    """

    @abstractmethod
    def scale_video(
        self, video_stream, width: Optional[int] = None, height: Optional[int] = None
    ):
        """Scale a video stream to specific dimensions.

        Args:
            video_stream: The video stream to scale
            width (Optional[int]): Output width
            height (Optional[int]): Output height

        Returns:
            The scaled video stream
        """
        pass


class IProgressTracker(ABC):
    """Interface for progress tracking strategies.

    This interface defines the contract for strategies that track
    the progress of video conversion.
    """

    @abstractmethod
    def track_progress(
        self, process, total_duration: float, task_id: str, progress_callback: Callable
    ) -> None:
        """Track the progress of a video conversion process.

        Args:
            process: The ffmpeg process
            total_duration (float): Total duration of the video in seconds
            task_id (str): Task ID for progress tracking
            progress_callback (Callable): Callback function for progress updates
        """
        pass
