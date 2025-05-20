"""Video converter implementation using the Strategy pattern.

This module provides a video converter implementation that uses the Strategy pattern
for improved maintainability and extensibility.
"""

import os
import time
import logging
from typing import Dict, Any, Optional, Union

from app.domain.interfaces.video_conversion import IVideoConversionStrategy
from app.infrastructure.video_conversion.conversion_strategies import (
    StandardVideoConversionStrategy,
    HighQualityVideoConversionStrategy,
    FastVideoConversionStrategy,
)
from app.models.video_params import VideoConversionParams, VideoQuality

logger = logging.getLogger(__name__)


class VideoConverter:
    """Video converter implementation using the Strategy pattern.

    This class provides a video converter implementation that uses the Strategy pattern
    for improved maintainability and extensibility.
    """

    def __init__(self, strategy: Optional[IVideoConversionStrategy] = None):
        """Initialize the video converter.

        Args:
            strategy (Optional[IVideoConversionStrategy]): Video conversion strategy to use
        """
        self.strategy = strategy or StandardVideoConversionStrategy()

    def set_strategy(self, strategy: IVideoConversionStrategy) -> None:
        """Set the video conversion strategy.

        Args:
            strategy (IVideoConversionStrategy): Video conversion strategy to use
        """
        self.strategy = strategy

    def convert_video(self, params: VideoConversionParams) -> Dict[str, Any]:
        """Convert a video file using the configured strategy.

        Args:
            params (VideoConversionParams): Video conversion parameters

        Returns:
            Dict[str, Any]: Dictionary with output file information

        Raises:
            ValueError: If the input file is invalid or the conversion fails
        """
        logger.info(
            f"Converting video {params.input_path} to {params.output_format} with {params.quality.value} quality"
        )

        # Select the appropriate strategy based on the quality
        if params.quality == VideoQuality.HIGH and not isinstance(
            self.strategy, HighQualityVideoConversionStrategy
        ):
            self.set_strategy(HighQualityVideoConversionStrategy())
        elif params.quality == VideoQuality.LOW and not isinstance(
            self.strategy, FastVideoConversionStrategy
        ):
            self.set_strategy(FastVideoConversionStrategy())
        elif not isinstance(self.strategy, StandardVideoConversionStrategy):
            self.set_strategy(StandardVideoConversionStrategy())

        # Generate output filename
        timestamp = int(time.time())
        output_filename = f"converted_{timestamp}.{params.output_format.value}"
        output_path = os.path.join(params.output_dir, output_filename)

        # Prepare video parameters
        video_params = {}

        # Set CRF based on quality
        video_params["crf"] = params.get_quality_crf()

        # Set preset if provided
        if params.preset:
            video_params["preset"] = params.preset

        # Set bitrate if provided
        if params.bitrate:
            video_params["b:v"] = params.bitrate

        # Prepare audio parameters
        audio_params = {}
        if params.audio_bitrate:
            audio_params["b:a"] = params.audio_bitrate

        # Determine video codec based on output format
        video_codec = params.video_codec
        audio_codec = params.audio_codec

        # Convert the video using the selected strategy
        result = self.strategy.convert_video(
            params.input_path,
            output_path,
            video_codec,
            audio_codec,
            video_params,
            audio_params,
            params.resolution.width if params.resolution else None,
            params.resolution.height if params.resolution else None,
            params.progress_callback,
        )

        logger.info(f"Successfully converted video to {result['output_path']}")
        return result

    @staticmethod
    def create_strategy(quality: Union[VideoQuality, str]) -> IVideoConversionStrategy:
        """Create a video conversion strategy based on the specified quality.

        Args:
            quality (Union[VideoQuality, str]): Video quality

        Returns:
            IVideoConversionStrategy: Video conversion strategy

        Raises:
            ValueError: If the specified quality is not supported
        """
        if isinstance(quality, str):
            quality = VideoQuality(quality)

        if quality == VideoQuality.HIGH:
            return HighQualityVideoConversionStrategy()
        elif quality == VideoQuality.LOW:
            return FastVideoConversionStrategy()
        else:  # MEDIUM or any other value
            return StandardVideoConversionStrategy()
