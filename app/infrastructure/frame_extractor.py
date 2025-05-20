"""Frame extractor implementation using the Strategy pattern.

This module provides a frame extractor implementation that uses the Strategy pattern
for improved maintainability and extensibility.
"""

import logging
from typing import List, Optional, Union

from app.domain.interfaces.frame_extraction import IFrameExtractionStrategy
from app.infrastructure.frame_extraction.extraction_strategies import (
    FFmpegExtractionStrategy,
    OpenCVExtractionStrategy,
    HybridExtractionStrategy,
)
from app.models.video_params import FrameExtractionParams, FrameExtractionMethod

logger = logging.getLogger(__name__)


class FrameExtractor:
    """Frame extractor implementation using the Strategy pattern.

    This class provides a frame extractor implementation that uses the Strategy pattern
    for improved maintainability and extensibility.
    """

    def __init__(self, strategy: Optional[IFrameExtractionStrategy] = None):
        """Initialize the frame extractor.

        Args:
            strategy (Optional[IFrameExtractionStrategy]): Frame extraction strategy to use
        """
        self.strategy = strategy or HybridExtractionStrategy()

    def set_strategy(self, strategy: IFrameExtractionStrategy) -> None:
        """Set the frame extraction strategy.

        Args:
            strategy (IFrameExtractionStrategy): Frame extraction strategy to use
        """
        self.strategy = strategy

    def extract_frames(self, params: FrameExtractionParams) -> List[str]:
        """Extract frames from a video file using the configured strategy.

        Args:
            params (FrameExtractionParams): Frame extraction parameters

        Returns:
            List[str]: List of paths to extracted frame images

        Raises:
            ValueError: If the input file is invalid or the extraction fails
        """
        logger.info(
            f"Extracting frames from {params.input_path} with {params.extraction_method.value} strategy"
        )

        # Select the appropriate strategy based on the extraction method
        if params.extraction_method == FrameExtractionMethod.FFMPEG and not isinstance(
            self.strategy, FFmpegExtractionStrategy
        ):
            self.set_strategy(
                FFmpegExtractionStrategy(extra_params=params.extra_ffmpeg_params)
            )
        elif (
            params.extraction_method == FrameExtractionMethod.OPENCV
            and not isinstance(self.strategy, OpenCVExtractionStrategy)
        ):
            self.set_strategy(OpenCVExtractionStrategy())
        elif (
            params.extraction_method == FrameExtractionMethod.HYBRID
            and not isinstance(self.strategy, HybridExtractionStrategy)
        ):
            self.set_strategy(
                HybridExtractionStrategy(extra_ffmpeg_params=params.extra_ffmpeg_params)
            )

        # Extract frames using the selected strategy
        return self.strategy.extract_frames(
            params.input_path,
            params.output_dir,
            params.fps,
            params.width,
            params.height,
        )

    @staticmethod
    def create_strategy(
        method: Union[FrameExtractionMethod, str],
        extra_ffmpeg_params: Optional[List[str]] = None,
    ) -> IFrameExtractionStrategy:
        """Create a frame extraction strategy based on the specified method.

        Args:
            method (Union[FrameExtractionMethod, str]): Frame extraction method
            extra_ffmpeg_params (Optional[List[str]]): Additional FFmpeg parameters

        Returns:
            IFrameExtractionStrategy: Frame extraction strategy

        Raises:
            ValueError: If the specified method is not supported
        """
        if isinstance(method, str):
            method = FrameExtractionMethod(method)

        if method == FrameExtractionMethod.FFMPEG:
            return FFmpegExtractionStrategy(extra_params=extra_ffmpeg_params)
        elif method == FrameExtractionMethod.OPENCV:
            return OpenCVExtractionStrategy()
        elif method == FrameExtractionMethod.HYBRID:
            return HybridExtractionStrategy(extra_ffmpeg_params=extra_ffmpeg_params)
        else:
            raise ValueError(f"Unsupported frame extraction method: {method}")
