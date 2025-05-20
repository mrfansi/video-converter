"""Refactored video converter implementation for the Video Converter project.

This module provides refactored video conversion functions using the Strategy pattern
for improved maintainability and extensibility.
"""

import os
import time
import logging
from typing import Dict, Any, Optional, List, Callable

from app.infrastructure.video_converter import VideoConverter
from app.models.video_params import VideoConversionParams, VideoConversionParamBuilder, VideoFormat, VideoQuality

logger = logging.getLogger(__name__)


def convert_video(
    input_path: str,
    output_dir: str,
    output_format: str,
    quality: str = "medium",
    width: Optional[int] = None,
    height: Optional[int] = None,
    bitrate: Optional[str] = None,
    preset: str = "medium",
    crf: Optional[int] = None,
    audio_codec: Optional[str] = None,
    audio_bitrate: Optional[str] = None,
    task_id: Optional[str] = None,
    progress_callback: Optional[callable] = None
) -> Dict[str, Any]:
    """
    Convert a video file to another format with optimization options using the Strategy pattern.
    
    This is a refactored version of the original convert_video function that uses
    the Strategy pattern for improved maintainability and extensibility.
    
    Args:
        input_path (str): Path to the input video file
        output_dir (str): Directory to save the output video
        output_format (str): Output format (mp4, webm, mov, avi, etc.)
        quality (str): Quality preset (low, medium, high, veryhigh)
        width (Optional[int]): Output width
        height (Optional[int]): Output height
        bitrate (Optional[str]): Video bitrate (e.g., "1M" for 1 Mbps)
        preset (str): Encoding preset (ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow)
        crf (Optional[int]): Constant Rate Factor (0-51, lower means better quality)
        audio_codec (Optional[str]): Audio codec (aac, mp3, opus, etc.)
        audio_bitrate (Optional[str]): Audio bitrate (e.g., "128k")
        task_id (Optional[str]): Task ID for progress tracking
        progress_callback (Optional[callable]): Callback function for progress updates
        
    Returns:
        Dict[str, Any]: Dictionary with output file information
    """
    try:
        logger.info(f"Converting video {input_path} to {output_format} with {quality} quality")
        
        # Create video conversion parameters using the builder pattern
        params_builder = (VideoConversionParamBuilder()
            .with_input_path(input_path)
            .with_output_dir(output_dir)
            .with_format(output_format)
            .with_quality(quality))
        
        # Add optional parameters if specified
        if width is not None and height is not None:
            params_builder.with_resolution(f"{width}x{height}")
        if bitrate is not None:
            params_builder.with_bitrates(bitrate, audio_bitrate)
        if preset is not None:
            params_builder.with_param("preset", preset)
        if crf is not None:
            params_builder.with_param("crf", crf)
        if audio_codec is not None:
            params_builder.with_codecs(None, audio_codec)
        if task_id is not None and progress_callback is not None:
            params_builder.with_progress_callback(progress_callback)
        
        # Build the parameters
        params = params_builder.build()
        
        # Create video converter and convert video
        converter = VideoConverter()
        result = converter.convert_video(params)
        
        logger.info(f"Successfully converted video to {result['output_path']}")
        return result
        
    except Exception as e:
        logger.error(f"Error converting video: {str(e)}")
        raise
