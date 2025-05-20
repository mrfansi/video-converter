"""Video format task processor using the Strategy pattern.

This module provides a video format task processor implementation that uses the Strategy pattern
for improved maintainability and extensibility.
"""

import logging
from enum import Enum
from typing import Dict, Any, Optional, Callable, Union

from app.domain.interfaces.video_format_task import IVideoFormatTaskStrategy
from app.infrastructure.video_format_task.task_strategies import (
    StandardVideoFormatTaskStrategy,
    OptimizedVideoFormatTaskStrategy,
    FallbackVideoFormatTaskStrategy
)

logger = logging.getLogger(__name__)


class VideoFormatTaskStrategy(Enum):
    """Enum for video format task processing strategies."""
    STANDARD = "standard"
    OPTIMIZED = "optimized"
    FALLBACK = "fallback"


class VideoFormatTaskProcessor:
    """Video format task processor using the Strategy pattern.
    
    This class provides a video format task processor implementation that uses the Strategy pattern
    for improved maintainability and extensibility.
    """
    
    def __init__(self, strategy: Optional[IVideoFormatTaskStrategy] = None):
        """Initialize the video format task processor.
        
        Args:
            strategy: Video format task processing strategy to use
        """
        self.strategy = strategy or StandardVideoFormatTaskStrategy()
    
    def set_strategy(self, strategy: IVideoFormatTaskStrategy) -> None:
        """Set the video format task processing strategy.
        
        Args:
            strategy: Video format task processing strategy to use
        """
        self.strategy = strategy
    
    def process_video_format_task(self, temp_dir: str, file_path: str, output_format: str,
                                quality: str, width: Optional[int] = None, height: Optional[int] = None,
                                bitrate: Optional[str] = None, preset: str = "medium", crf: Optional[int] = None,
                                audio_codec: Optional[str] = None, audio_bitrate: Optional[str] = None,
                                original_filename: Optional[str] = None, task_id: Optional[str] = None,
                                strategy_type: Optional[Union[VideoFormatTaskStrategy, str]] = None,
                                progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
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
            strategy_type: Strategy type to use
            progress_callback: Callback function for progress updates
            
        Returns:
            Dict[str, Any]: Processing result with URLs
        """
        # Select the appropriate strategy based on the strategy_type
        if strategy_type is not None:
            if isinstance(strategy_type, str):
                strategy_type = VideoFormatTaskStrategy(strategy_type)
            
            if strategy_type == VideoFormatTaskStrategy.OPTIMIZED:
                self.set_strategy(OptimizedVideoFormatTaskStrategy())
            elif strategy_type == VideoFormatTaskStrategy.FALLBACK:
                self.set_strategy(FallbackVideoFormatTaskStrategy())
            else:  # STANDARD or any other value
                self.set_strategy(StandardVideoFormatTaskStrategy())
        
        # Process the video format task using the selected strategy
        return self.strategy.process_video_format_task(
            temp_dir=temp_dir,
            file_path=file_path,
            output_format=output_format,
            quality=quality,
            width=width,
            height=height,
            bitrate=bitrate,
            preset=preset,
            crf=crf,
            audio_codec=audio_codec,
            audio_bitrate=audio_bitrate,
            original_filename=original_filename,
            task_id=task_id,
            progress_callback=progress_callback
        )
    
    @staticmethod
    def create_strategy(strategy_type: Union[VideoFormatTaskStrategy, str]) -> IVideoFormatTaskStrategy:
        """Create a video format task processing strategy based on the specified type.
        
        Args:
            strategy_type: Strategy type to create
            
        Returns:
            IVideoFormatTaskStrategy: Video format task processing strategy
            
        Raises:
            ValueError: If the specified strategy type is not supported
        """
        if isinstance(strategy_type, str):
            strategy_type = VideoFormatTaskStrategy(strategy_type)
        
        if strategy_type == VideoFormatTaskStrategy.OPTIMIZED:
            return OptimizedVideoFormatTaskStrategy()
        elif strategy_type == VideoFormatTaskStrategy.FALLBACK:
            return FallbackVideoFormatTaskStrategy()
        else:  # STANDARD or any other value
            return StandardVideoFormatTaskStrategy()
