"""Video processor using the Strategy pattern.

This module provides a VideoProcessor class that uses the Strategy pattern
for video processing, improving maintainability and extensibility.
"""

import os
import logging
from typing import Dict, Any, Optional, Callable, Union

from app.domain.interfaces.video_processing import IVideoProcessingStrategy
from app.models.lottie_params import VideoProcessingParams, VideoProcessingStrategy
from app.infrastructure.video_processing.processing_strategies import StandardVideoProcessingStrategy
from app.infrastructure.video_processing.high_quality_strategy import HighQualityVideoProcessingStrategy
from app.infrastructure.video_processing.fast_strategy import FastVideoProcessingStrategy

logger = logging.getLogger(__name__)


class VideoProcessor:
    """Video processor using the Strategy pattern.
    
    This class processes video files into Lottie animations using different strategies
    based on the specified quality requirements.
    """
    
    def __init__(self, cloud_uploader: Optional[Any] = None):
        """Initialize the video processor.
        
        Args:
            cloud_uploader (Optional[Any]): Cloud uploader to use for file uploads
        """
        self.cloud_uploader = cloud_uploader
        self.strategies = {
            VideoProcessingStrategy.STANDARD: StandardVideoProcessingStrategy(),
            VideoProcessingStrategy.HIGH_QUALITY: HighQualityVideoProcessingStrategy(),
            VideoProcessingStrategy.FAST: FastVideoProcessingStrategy()
        }
        
        # Set the cloud uploader for all strategies
        for strategy in self.strategies.values():
            strategy.cloud_uploader = cloud_uploader
    
    def get_strategy(self, strategy_type: Union[VideoProcessingStrategy, str]) -> IVideoProcessingStrategy:
        """Get the appropriate strategy based on the strategy type.
        
        Args:
            strategy_type (Union[VideoProcessingStrategy, str]): Strategy type to use
            
        Returns:
            IVideoProcessingStrategy: The selected strategy
        """
        if isinstance(strategy_type, str):
            try:
                strategy_type = VideoProcessingStrategy(strategy_type)
            except ValueError:
                logger.warning(f"Invalid strategy type: {strategy_type}. Using STANDARD instead.")
                strategy_type = VideoProcessingStrategy.STANDARD
        
        return self.strategies.get(strategy_type, self.strategies[VideoProcessingStrategy.STANDARD])
    
    def process_video(self, params: VideoProcessingParams) -> Dict[str, Any]:
        """Process a video file into a Lottie animation.
        
        Args:
            params (VideoProcessingParams): Parameters for video processing
            
        Returns:
            Dict[str, Any]: Processing result with URLs
            
        Raises:
            ValueError: If the input file is invalid or the processing fails
        """
        try:
            # Validate parameters
            if not os.path.exists(params.file_path):
                raise ValueError(f"Video file does not exist: {params.file_path}")
            
            if not os.path.isdir(params.temp_dir):
                os.makedirs(params.temp_dir, exist_ok=True)
            
            # Create output directory if it doesn't exist
            output_dir = os.path.join(params.temp_dir, "output")
            os.makedirs(output_dir, exist_ok=True)
            
            # Get the appropriate strategy
            strategy = self.get_strategy(params.strategy)
            
            # Process the video
            result = strategy.process_video(
                file_path=params.file_path,
                output_dir=output_dir,
                temp_dir=params.temp_dir,
                fps=params.fps,
                width=params.width,
                height=params.height,
                original_filename=params.original_filename,
                progress_callback=params.progress_callback
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing video: {str(e)}")
            raise ValueError(f"Failed to process video: {str(e)}")


def process_video_task(params: VideoProcessingParams) -> Dict[str, Any]:
    """Process a video file into a Lottie animation.
    
    This function is a wrapper around the VideoProcessor class that simplifies
    the interface for video processing.
    
    Args:
        params (VideoProcessingParams): Parameters for video processing
        
    Returns:
        Dict[str, Any]: Processing result with URLs
        
    Raises:
        ValueError: If the input file is invalid or the processing fails
    """
    processor = VideoProcessor()
    return processor.process_video(params)
