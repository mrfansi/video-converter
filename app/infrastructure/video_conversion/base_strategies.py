"""Base strategies for video conversion.

This module provides base implementations for video conversion strategies
following the Strategy pattern for improved maintainability and extensibility.
"""

import os
import time
import logging
import ffmpeg
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Callable, Tuple

from app.domain.interfaces.video_conversion import (
    IVideoConversionStrategy,
    IVideoCodecSelector,
    IAudioCodecSelector,
    IVideoScaler,
    IProgressTracker
)

logger = logging.getLogger(__name__)


class BaseVideoCodecSelector(IVideoCodecSelector):
    """Base implementation of video codec selector.
    
    This class provides a base implementation for selecting video codecs
    based on the output format.
    """
    
    def select_video_codec(self, output_format: str) -> str:
        """Select a video codec based on the output format.
        
        Args:
            output_format (str): Output format (mp4, webm, mov, avi, etc.)
            
        Returns:
            str: Selected video codec
        """
        format_to_codec = {
            "mp4": "libx264",
            "webm": "libvpx-vp9",
            "mov": "libx264",
            "avi": "libx264",
            "mkv": "libx264",
            "flv": "flv",
            "gif": "gif"
        }
        return format_to_codec.get(output_format.lower(), "libx264")


class BaseAudioCodecSelector(IAudioCodecSelector):
    """Base implementation of audio codec selector.
    
    This class provides a base implementation for selecting audio codecs
    based on the output format.
    """
    
    def select_audio_codec(self, output_format: str) -> str:
        """Select an audio codec based on the output format.
        
        Args:
            output_format (str): Output format (mp4, webm, mov, avi, etc.)
            
        Returns:
            str: Selected audio codec
        """
        format_to_audio = {
            "mp4": "aac",
            "webm": "libopus",
            "mov": "aac",
            "avi": "aac",
            "mkv": "aac",
            "flv": "aac",
            "gif": None  # GIF has no audio
        }
        return format_to_audio.get(output_format.lower(), "aac")


class BaseVideoScaler(IVideoScaler):
    """Base implementation of video scaler.
    
    This class provides a base implementation for scaling videos
    to specific dimensions.
    """
    
    def scale_video(self, video_stream, width: Optional[int] = None, height: Optional[int] = None):
        """Scale a video stream to specific dimensions.
        
        Args:
            video_stream: The video stream to scale
            width (Optional[int]): Output width
            height (Optional[int]): Output height
            
        Returns:
            The scaled video stream
        """
        if not width and not height:
            return video_stream
        
        scale_params = {}
        if width:
            scale_params["width"] = width
        if height:
            scale_params["height"] = height
            
        # If only one dimension is specified, maintain aspect ratio
        if width and not height:
            scale_params["height"] = -1
        elif height and not width:
            scale_params["width"] = -1
            
        return video_stream.filter("scale", **scale_params)


class BaseProgressTracker(IProgressTracker):
    """Base implementation of progress tracker.
    
    This class provides a base implementation for tracking the progress
    of video conversion.
    """
    
    def track_progress(self, process, total_duration: float, task_id: str, 
                      progress_callback: Callable) -> None:
        """Track the progress of a video conversion process.
        
        Args:
            process: The ffmpeg process
            total_duration (float): Total duration of the video in seconds
            task_id (str): Task ID for progress tracking
            progress_callback (Callable): Callback function for progress updates
        """
        if not total_duration or total_duration <= 0:
            logger.warning("Cannot track progress: invalid duration")
            return
        
        last_progress = 0
        while process.poll() is None:
            stderr_line = process.stderr.readline().decode('utf8', errors='replace')
            if 'time=' in stderr_line:
                time_str = stderr_line.split('time=')[1].split()[0]
                # Convert HH:MM:SS.MS to seconds
                parts = time_str.split(':')  
                if len(parts) == 3:
                    hours, minutes, seconds = parts
                    seconds = float(seconds)
                    current_time = float(hours) * 3600 + float(minutes) * 60 + seconds
                    progress = min(int((current_time / total_duration) * 100), 100)
                    
                    # Only update if progress has changed significantly
                    if progress - last_progress >= 5:
                        progress_callback(
                            task_id=task_id,
                            current_step="Converting video",
                            percent=progress,
                            details=f"Processing: {progress}% complete"
                        )
                        last_progress = progress


class BaseVideoConversionStrategy(IVideoConversionStrategy, ABC):
    """Base implementation of video conversion strategy.
    
    This abstract class provides common functionality for video conversion strategies.
    """
    
    def __init__(self, 
                 codec_selector: Optional[IVideoCodecSelector] = None,
                 audio_codec_selector: Optional[IAudioCodecSelector] = None,
                 video_scaler: Optional[IVideoScaler] = None,
                 progress_tracker: Optional[IProgressTracker] = None):
        """Initialize the video conversion strategy.
        
        Args:
            codec_selector (Optional[IVideoCodecSelector]): Video codec selector
            audio_codec_selector (Optional[IAudioCodecSelector]): Audio codec selector
            video_scaler (Optional[IVideoScaler]): Video scaler
            progress_tracker (Optional[IProgressTracker]): Progress tracker
        """
        self.codec_selector = codec_selector or BaseVideoCodecSelector()
        self.audio_codec_selector = audio_codec_selector or BaseAudioCodecSelector()
        self.video_scaler = video_scaler or BaseVideoScaler()
        self.progress_tracker = progress_tracker or BaseProgressTracker()
    
    def get_video_duration(self, input_path: str) -> float:
        """Get the duration of a video file.
        
        Args:
            input_path (str): Path to the video file
            
        Returns:
            float: Duration of the video in seconds
        """
        try:
            probe = ffmpeg.probe(input_path)
            video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
            return float(video_info.get('duration', 0))
        except Exception as e:
            logger.warning(f"Failed to get video duration: {str(e)}")
            return 0.0
    
    @abstractmethod
    def convert_video(self, input_path: str, output_path: str, 
                     video_codec: str, audio_codec: str,
                     video_params: Dict[str, Any], audio_params: Dict[str, Any],
                     width: Optional[int] = None, height: Optional[int] = None,
                     progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
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
