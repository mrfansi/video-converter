"""Concrete strategies for video conversion.

This module provides concrete implementations for video conversion strategies
following the Strategy pattern for improved maintainability and extensibility.
"""

import os
import time
import logging
import ffmpeg
from typing import Dict, Any, Optional, List, Callable, Tuple

from app.domain.interfaces.video_conversion import (
    IVideoConversionStrategy,
    IVideoCodecSelector,
    IAudioCodecSelector,
    IVideoScaler,
    IProgressTracker
)
from app.infrastructure.video_conversion.base_strategies import (
    BaseVideoConversionStrategy,
    BaseVideoCodecSelector,
    BaseAudioCodecSelector,
    BaseVideoScaler,
    BaseProgressTracker
)

logger = logging.getLogger(__name__)


class StandardVideoConversionStrategy(BaseVideoConversionStrategy):
    """Standard video conversion strategy using FFmpeg.
    
    This strategy uses FFmpeg for video conversion with standard settings,
    suitable for most video conversion tasks.
    """
    
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
        try:
            # Set up ffmpeg input
            input_stream = ffmpeg.input(input_path)
            
            # Apply scaling if needed
            video_stream = self.video_scaler.scale_video(input_stream.video, width, height)
            
            # Build the output arguments
            output_args = {
                "c:v": video_codec,
                **video_params
            }
            
            # Add audio parameters if audio codec is specified
            if audio_codec:
                output_args.update({
                    "c:a": audio_codec,
                    **audio_params
                })
                # Create output stream with audio
                output = ffmpeg.output(video_stream, input_stream.audio, output_path, **output_args)
            else:
                # Create output stream without audio (e.g., for GIF)
                output = ffmpeg.output(video_stream, output_path, **output_args)
            
            # Get video duration for progress tracking
            total_duration = None
            task_id = None
            
            if progress_callback and isinstance(progress_callback, Callable):
                # Extract task_id from the first argument of progress_callback
                if hasattr(progress_callback, "__code__") and progress_callback.__code__.co_varnames:
                    if progress_callback.__code__.co_varnames[0] == "task_id":
                        # This is a progress callback that expects a task_id
                        task_id = "task_id"  # Placeholder, will be provided by the caller
                
                total_duration = self.get_video_duration(input_path)
            
            # Run the conversion
            if task_id and progress_callback and total_duration and total_duration > 0:
                # Custom progress tracking
                cmd = ffmpeg.compile(output, overwrite_output=True)
                process = ffmpeg.run_async(cmd, pipe_stdout=True, pipe_stderr=True)
                
                # Track progress
                self.progress_tracker.track_progress(process, total_duration, task_id, progress_callback)
                
                # Wait for completion
                process.wait()
                
                # Check for errors
                if process.returncode != 0:
                    stderr = process.stderr.read().decode('utf8', errors='replace')
                    raise RuntimeError(f"FFmpeg process failed: {stderr}")
            else:
                # Simple run without progress tracking
                output = output.overwrite_output()
                output.run(quiet=True)
            
            # Return information about the converted file
            file_stats = os.stat(output_path)
            return {
                "output_path": output_path,
                "format": os.path.splitext(output_path)[1][1:],  # Extract format from file extension
                "size_bytes": file_stats.st_size,
                "duration": total_duration
            }
            
        except ffmpeg.Error as e:
            error_message = e.stderr.decode() if hasattr(e, 'stderr') else str(e)
            logger.error(f"Error converting video: {error_message}")
            raise ValueError(f"Failed to convert video: {error_message}")
        except Exception as e:
            logger.error(f"Unexpected error converting video: {str(e)}")
            raise


class HighQualityVideoConversionStrategy(BaseVideoConversionStrategy):
    """High quality video conversion strategy.
    
    This strategy uses FFmpeg for video conversion with high quality settings,
    suitable for archival or professional use cases.
    """
    
    def convert_video(self, input_path: str, output_path: str, 
                     video_codec: str, audio_codec: str,
                     video_params: Dict[str, Any], audio_params: Dict[str, Any],
                     width: Optional[int] = None, height: Optional[int] = None,
                     progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Convert a video file to another format with high quality settings.
        
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
        try:
            # Override video parameters for high quality
            high_quality_video_params = video_params.copy()
            
            # Set higher quality parameters
            if video_codec == "libx264" or video_codec == "libx265":
                # Lower CRF means higher quality
                high_quality_video_params["crf"] = min(high_quality_video_params.get("crf", 23), 18)
                # Use slower preset for better compression
                high_quality_video_params["preset"] = "slow"
            elif video_codec == "libvpx-vp9":
                high_quality_video_params["crf"] = min(high_quality_video_params.get("crf", 31), 24)
                high_quality_video_params["deadline"] = "good"
            
            # Override audio parameters for high quality
            high_quality_audio_params = audio_params.copy()
            
            # Set higher quality audio parameters
            if audio_codec == "aac":
                high_quality_audio_params["b:a"] = high_quality_audio_params.get("b:a", "192k")
            elif audio_codec == "libopus":
                high_quality_audio_params["b:a"] = high_quality_audio_params.get("b:a", "128k")
            
            # Use the standard strategy with high quality parameters
            standard_strategy = StandardVideoConversionStrategy(
                self.codec_selector,
                self.audio_codec_selector,
                self.video_scaler,
                self.progress_tracker
            )
            
            return standard_strategy.convert_video(
                input_path, output_path,
                video_codec, audio_codec,
                high_quality_video_params, high_quality_audio_params,
                width, height,
                progress_callback
            )
            
        except Exception as e:
            logger.error(f"Error in high quality conversion: {str(e)}")
            raise


class FastVideoConversionStrategy(BaseVideoConversionStrategy):
    """Fast video conversion strategy.
    
    This strategy uses FFmpeg for video conversion with fast settings,
    sacrificing some quality for speed, suitable for quick previews or drafts.
    """
    
    def convert_video(self, input_path: str, output_path: str, 
                     video_codec: str, audio_codec: str,
                     video_params: Dict[str, Any], audio_params: Dict[str, Any],
                     width: Optional[int] = None, height: Optional[int] = None,
                     progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Convert a video file to another format with fast settings.
        
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
        try:
            # Override video parameters for fast conversion
            fast_video_params = video_params.copy()
            
            # Set faster parameters
            if video_codec == "libx264" or video_codec == "libx265":
                # Higher CRF means lower quality but faster encoding
                fast_video_params["crf"] = max(fast_video_params.get("crf", 23), 28)
                # Use faster preset
                fast_video_params["preset"] = "veryfast"
            elif video_codec == "libvpx-vp9":
                fast_video_params["crf"] = max(fast_video_params.get("crf", 31), 35)
                fast_video_params["deadline"] = "realtime"
            
            # Override audio parameters for faster conversion
            fast_audio_params = audio_params.copy()
            
            # Set lower quality audio parameters for speed
            if audio_codec == "aac":
                fast_audio_params["b:a"] = "96k"
            elif audio_codec == "libopus":
                fast_audio_params["b:a"] = "64k"
            
            # Use the standard strategy with fast parameters
            standard_strategy = StandardVideoConversionStrategy(
                self.codec_selector,
                self.audio_codec_selector,
                self.video_scaler,
                self.progress_tracker
            )
            
            return standard_strategy.convert_video(
                input_path, output_path,
                video_codec, audio_codec,
                fast_video_params, fast_audio_params,
                width, height,
                progress_callback
            )
            
        except Exception as e:
            logger.error(f"Error in fast conversion: {str(e)}")
            raise
