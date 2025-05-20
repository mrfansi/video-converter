"""Image tracer implementation for the Video Converter project.

This module provides a concrete implementation of the image tracer interface
defined in app.domain.interfaces.converter.
"""

import numpy as np
import cv2
import logging
import os

from app.domain.interfaces.converter import IImageTracer
from app.domain.interfaces.image_tracing import TracingResult
from app.infrastructure.image_tracing.tracing_strategies import (
    ImageTracingStrategyFactory,
    BaseImageTracingStrategy,
)

logger = logging.getLogger(__name__)


class OpenCVImageTracer(IImageTracer):
    """OpenCV-based image tracer.

    This class implements the IImageTracer interface using OpenCV for image processing
    and the Strategy pattern for different tracing approaches.
    """

    def __init__(self, default_strategy: str = "advanced"):
        """Initialize the OpenCV image tracer.

        Args:
            default_strategy (str, optional): Default tracing strategy. Defaults to "advanced".
        """
        self._supported_conversions = {("png", "svg"), ("jpg", "svg"), ("jpeg", "svg")}
        self.default_strategy = default_strategy
        self.strategy_factory = ImageTracingStrategyFactory()

    def _initialize_supported_conversions(self) -> None:
        """Initialize the set of supported conversions."""
        # Already initialized in constructor
        pass

    def can_convert(self, source_format: str, target_format: str) -> bool:
        """Check if this converter can handle the specified conversion.

        Args:
            source_format (str): Source format (e.g., "png", "jpg")
            target_format (str): Target format (e.g., "svg")

        Returns:
            bool: True if this converter can handle the conversion, False otherwise
        """
        return (
            source_format.lower(),
            target_format.lower(),
        ) in self._supported_conversions

    def trace_image(self, input_path: str, output_path: str, **options) -> str:
        """Trace a raster image to a vector format.

        Args:
            input_path (str): Path to the input image
            output_path (str): Path to save the output vector file
            **options: Additional options for the tracing operation

        Returns:
            str: Path to the output vector file

        Raises:
            ValueError: If the input file is invalid or the conversion fails
        """
        # Validate input file
        if not os.path.exists(input_path):
            raise ValueError(f"Input file does not exist: {input_path}")

        if not os.path.isfile(input_path):
            raise ValueError(f"Input path is not a file: {input_path}")

        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        # Check if the conversion is supported
        source_format = os.path.splitext(input_path)[1][1:].lower()
        target_format = os.path.splitext(output_path)[1][1:].lower()

        if not self.can_convert(source_format, target_format):
            raise ValueError(
                f"Unsupported conversion: {source_format} to {target_format}"
            )

        # Get tracing options
        strategy_type = options.get("strategy", self.default_strategy)
        simplify_tolerance = options.get("simplify_tolerance", 1.0)

        # Create the appropriate strategy
        strategy = self.strategy_factory.create_strategy(
            strategy_type, simplify_tolerance=simplify_tolerance
        )

        # Read the image
        try:
            image = cv2.imread(input_path, cv2.IMREAD_COLOR)
            if image is None:
                raise ValueError(f"Could not read image: {input_path}")
        except Exception as e:
            logger.error(f"Error reading image: {str(e)}")
            raise ValueError(f"Error reading image: {str(e)}")

        # Trace the image using the selected strategy
        result = self._trace_with_strategy(strategy, image, simplify_tolerance)

        # Check if tracing was successful
        if not result.success or not result.svg_content:
            raise ValueError(f"Tracing failed: {result.error or 'Unknown error'}")

        # Save the SVG content to the output file
        try:
            with open(output_path, "w") as f:
                f.write(result.svg_content)
        except Exception as e:
            logger.error(f"Error saving SVG: {str(e)}")
            raise ValueError(f"Error saving SVG: {str(e)}")

        logger.info(
            f"Traced {input_path} to {output_path} with {result.path_count} paths"
        )
        return output_path

    def _trace_with_strategy(
        self,
        strategy: BaseImageTracingStrategy,
        image: np.ndarray,
        simplify_tolerance: float,
    ) -> TracingResult:
        """Trace an image using the specified strategy.

        Args:
            strategy (BaseImageTracingStrategy): Tracing strategy to use
            image (np.ndarray): Image to trace
            simplify_tolerance (float): Tolerance for path simplification

        Returns:
            TracingResult: Result of the tracing operation
        """
        try:
            return strategy.trace_image(image, simplify_tolerance)
        except Exception as e:
            logger.error(
                f"Error tracing image with strategy {strategy.__class__.__name__}: {str(e)}"
            )
            # Try fallback strategy if the primary strategy fails
            try:
                fallback_strategy = self.strategy_factory.create_strategy("basic")
                return fallback_strategy.trace_image(image, simplify_tolerance)
            except Exception as fallback_error:
                logger.error(f"Fallback strategy also failed: {str(fallback_error)}")
                return TracingResult.error_result(f"Tracing failed: {str(e)}")
