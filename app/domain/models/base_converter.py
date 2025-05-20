"""Base abstract classes for converters in the Video Converter project.

This module provides base implementations of the converter interfaces
defined in app.domain.interfaces.converter. These abstract classes implement
common functionality while leaving specific conversion logic to concrete subclasses.
"""

from abc import ABC, abstractmethod
from typing import Set, Tuple
import os
import logging

from app.domain.interfaces.converter import (
    IConverter,
    IVideoConverter,
    ILottieGenerator,
    IImageTracer,
    ConversionResult,
)
from app.models.video_params import VideoConversionParams
from app.models.lottie_params import LottieAnimationParams, SVGConversionParams


logger = logging.getLogger(__name__)


class BaseConverter(IConverter, ABC):
    """Base abstract class for all converters.

    This class provides a common implementation for the IConverter interface,
    including format support checking and validation.
    """

    def __init__(self):
        """Initialize the base converter."""
        self._supported_conversions: Set[Tuple[str, str]] = set()
        self._initialize_supported_conversions()

    @abstractmethod
    def _initialize_supported_conversions(self) -> None:
        """Initialize the set of supported conversions.

        This method should be implemented by subclasses to define which
        source and target format combinations are supported.
        """
        pass

    def can_convert(self, source_format: str, target_format: str) -> bool:
        """Check if this converter can handle the specified conversion.

        Args:
            source_format (str): Source format (e.g., "mp4", "png")
            target_format (str): Target format (e.g., "webm", "svg")

        Returns:
            bool: True if this converter can handle the conversion, False otherwise
        """
        return (
            source_format.lower(),
            target_format.lower(),
        ) in self._supported_conversions

    def _validate_input_file(self, input_path: str) -> bool:
        """Validate that the input file exists and is readable.

        Args:
            input_path (str): Path to the input file

        Returns:
            bool: True if the input file is valid, False otherwise
        """
        if not os.path.exists(input_path):
            logger.error(f"Input file does not exist: {input_path}")
            return False

        if not os.path.isfile(input_path):
            logger.error(f"Input path is not a file: {input_path}")
            return False

        if not os.access(input_path, os.R_OK):
            logger.error(f"Input file is not readable: {input_path}")
            return False

        return True

    def _ensure_output_directory(self, output_path: str) -> bool:
        """Ensure that the output directory exists.

        Args:
            output_path (str): Path to the output file

        Returns:
            bool: True if the output directory exists or was created, False otherwise
        """
        output_dir = os.path.dirname(output_path)

        if not output_dir:
            return True

        try:
            os.makedirs(output_dir, exist_ok=True)
            return True
        except Exception as e:
            logger.error(
                f"Failed to create output directory: {output_dir}. Error: {str(e)}"
            )
            return False


class BaseVideoConverter(BaseConverter, IVideoConverter, ABC):
    """Base abstract class for video converters.

    This class provides a common implementation for the IVideoConverter interface,
    including parameter validation and result handling.
    """

    def convert(self, params: VideoConversionParams) -> ConversionResult:
        """Convert a video to the specified format.

        Args:
            params (VideoConversionParams): Conversion parameters

        Returns:
            ConversionResult: Result of the conversion operation
        """
        # Validate input file
        if not self._validate_input_file(params.input_path):
            return ConversionResult.error_result(
                f"Invalid input file: {params.input_path}"
            )

        # Ensure output directory exists
        if not self._ensure_output_directory(params.output_path):
            return ConversionResult.error_result(
                f"Failed to create output directory for: {params.output_path}"
            )

        # Check if the conversion is supported
        source_format = os.path.splitext(params.input_path)[1][1:].lower()
        target_format = os.path.splitext(params.output_path)[1][1:].lower()

        if not self.can_convert(source_format, target_format):
            return ConversionResult.error_result(
                f"Unsupported conversion: {source_format} to {target_format}"
            )

        try:
            # Perform the actual conversion (implemented by subclasses)
            return self._perform_conversion(params)
        except Exception as e:
            logger.exception(f"Error during video conversion: {str(e)}")
            return ConversionResult.error_result(f"Conversion failed: {str(e)}")

    @abstractmethod
    def _perform_conversion(self, params: VideoConversionParams) -> ConversionResult:
        """Perform the actual video conversion.

        This method should be implemented by subclasses to perform the
        specific conversion logic.

        Args:
            params (VideoConversionParams): Conversion parameters

        Returns:
            ConversionResult: Result of the conversion operation
        """
        pass


class BaseLottieGenerator(BaseConverter, ILottieGenerator, ABC):
    """Base abstract class for Lottie animation generators.

    This class provides a common implementation for the ILottieGenerator interface,
    including parameter validation and result handling.
    """

    def generate_from_frames(self, params: LottieAnimationParams) -> ConversionResult:
        """Generate a Lottie animation from image frames.

        Args:
            params (LottieAnimationParams): Animation generation parameters

        Returns:
            ConversionResult: Result of the generation operation
        """
        # Validate input directory
        if not os.path.exists(params.frames_dir):
            return ConversionResult.error_result(
                f"Input frames directory does not exist: {params.frames_dir}"
            )

        if not os.path.isdir(params.frames_dir):
            return ConversionResult.error_result(
                f"Input frames path is not a directory: {params.frames_dir}"
            )

        # Ensure output directory exists
        if not self._ensure_output_directory(params.output_path):
            return ConversionResult.error_result(
                f"Failed to create output directory for: {params.output_path}"
            )

        try:
            # Perform the actual generation (implemented by subclasses)
            return self._perform_frames_generation(params)
        except Exception as e:
            logger.exception(f"Error during Lottie generation from frames: {str(e)}")
            return ConversionResult.error_result(f"Lottie generation failed: {str(e)}")

    def generate_from_svgs(self, params: SVGConversionParams) -> ConversionResult:
        """Generate a Lottie animation from SVG files.

        Args:
            params (SVGConversionParams): SVG conversion parameters

        Returns:
            ConversionResult: Result of the generation operation
        """
        # Validate input directory
        if not os.path.exists(params.svg_dir):
            return ConversionResult.error_result(
                f"Input SVG directory does not exist: {params.svg_dir}"
            )

        if not os.path.isdir(params.svg_dir):
            return ConversionResult.error_result(
                f"Input SVG path is not a directory: {params.svg_dir}"
            )

        # Ensure output directory exists
        if not self._ensure_output_directory(params.output_path):
            return ConversionResult.error_result(
                f"Failed to create output directory for: {params.output_path}"
            )

        try:
            # Perform the actual generation (implemented by subclasses)
            return self._perform_svg_generation(params)
        except Exception as e:
            logger.exception(f"Error during Lottie generation from SVGs: {str(e)}")
            return ConversionResult.error_result(f"Lottie generation failed: {str(e)}")

    @abstractmethod
    def _perform_frames_generation(
        self, params: LottieAnimationParams
    ) -> ConversionResult:
        """Perform the actual Lottie generation from frames.

        This method should be implemented by subclasses to perform the
        specific generation logic.

        Args:
            params (LottieAnimationParams): Animation generation parameters

        Returns:
            ConversionResult: Result of the generation operation
        """
        pass

    @abstractmethod
    def _perform_svg_generation(self, params: SVGConversionParams) -> ConversionResult:
        """Perform the actual Lottie generation from SVGs.

        This method should be implemented by subclasses to perform the
        specific generation logic.

        Args:
            params (SVGConversionParams): SVG conversion parameters

        Returns:
            ConversionResult: Result of the generation operation
        """
        pass


class BaseImageTracer(BaseConverter, IImageTracer, ABC):
    """Base abstract class for image tracers.

    This class provides a common implementation for the IImageTracer interface,
    including parameter validation and result handling.
    """

    def trace_image(self, input_path: str, output_path: str, **options) -> str:
        """Trace a raster image to a vector format.

        Args:
            input_path (str): Path to the input image
            output_path (str): Path to save the output vector file
            **options: Additional options for the tracing operation

        Returns:
            str: Path to the output vector file
        """
        # Validate input file
        if not self._validate_input_file(input_path):
            raise ValueError(f"Invalid input file: {input_path}")

        # Ensure output directory exists
        if not self._ensure_output_directory(output_path):
            raise ValueError(f"Failed to create output directory for: {output_path}")

        # Check if the conversion is supported
        source_format = os.path.splitext(input_path)[1][1:].lower()
        target_format = os.path.splitext(output_path)[1][1:].lower()

        if not self.can_convert(source_format, target_format):
            raise ValueError(
                f"Unsupported conversion: {source_format} to {target_format}"
            )

        # Perform the actual tracing (implemented by subclasses)
        return self._perform_tracing(input_path, output_path, **options)

    @abstractmethod
    def _perform_tracing(self, input_path: str, output_path: str, **options) -> str:
        """Perform the actual image tracing.

        This method should be implemented by subclasses to perform the
        specific tracing logic.

        Args:
            input_path (str): Path to the input image
            output_path (str): Path to save the output vector file
            **options: Additional options for the tracing operation

        Returns:
            str: Path to the output vector file
        """
        pass
