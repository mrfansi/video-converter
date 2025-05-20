"""Base abstract classes for image tracing strategies in the Video Converter project.

This module provides base implementations of the image tracing interfaces
defined in app.domain.interfaces.image_tracing. These abstract classes implement
common functionality while leaving specific tracing logic to concrete subclasses.
"""

from abc import ABC, abstractmethod
from typing import List, Tuple
import numpy as np
import logging
import cv2

from app.domain.interfaces.image_tracing import (
    IImageTracingStrategy,
    IContourExtractionStrategy,
    IColorExtractionStrategy,
    ISVGGenerationStrategy,
    IFallbackStrategy,
    TracingResult,
)

logger = logging.getLogger(__name__)


class BaseImageTracingStrategy(IImageTracingStrategy, ABC):
    """Base abstract class for image tracing strategies.

    This class provides a common implementation for the IImageTracingStrategy interface,
    including error handling and result generation.
    """

    def __init__(
        self,
        contour_strategy: IContourExtractionStrategy,
        color_strategy: IColorExtractionStrategy,
        svg_strategy: ISVGGenerationStrategy,
        fallback_strategy: IFallbackStrategy,
    ):
        """Initialize the base image tracing strategy.

        Args:
            contour_strategy (IContourExtractionStrategy): Strategy for contour extraction
            color_strategy (IColorExtractionStrategy): Strategy for color extraction
            svg_strategy (ISVGGenerationStrategy): Strategy for SVG generation
            fallback_strategy (IFallbackStrategy): Strategy for fallback generation
        """
        self.contour_strategy = contour_strategy
        self.color_strategy = color_strategy
        self.svg_strategy = svg_strategy
        self.fallback_strategy = fallback_strategy

    def trace_image(
        self, image: np.ndarray, simplify_tolerance: float = 1.0
    ) -> TracingResult:
        """Trace an image to SVG.

        Args:
            image (np.ndarray): Image to trace (OpenCV format)
            simplify_tolerance (float, optional): Tolerance for path simplification. Defaults to 1.0.

        Returns:
            TracingResult: Result of the tracing operation
        """
        try:
            # Extract contours using the contour strategy
            contours, processed_image = self.contour_strategy.extract_contours(image)

            # If no contours were found, use the fallback strategy
            if not contours:
                logger.warning("No contours found, using fallback strategy")
                return self.fallback_strategy.generate_fallback(image)

            # Extract colors using the color strategy
            colors = self.color_strategy.extract_colors(image, contours)

            # Generate SVG using the SVG strategy
            svg_content = self.svg_strategy.generate_svg(image, contours, colors)

            # Return success result
            return TracingResult.success_result(
                svg_content=svg_content,
                path_count=len(contours),
                metadata={
                    "simplify_tolerance": simplify_tolerance,
                    "image_shape": image.shape,
                },
            )
        except Exception as e:
            logger.error(f"Error tracing image: {str(e)}")
            # Use fallback strategy in case of error
            return self.fallback_strategy.generate_fallback(image)


class BaseContourExtractionStrategy(IContourExtractionStrategy, ABC):
    """Base abstract class for contour extraction strategies.

    This class provides a common implementation for the IContourExtractionStrategy interface,
    including basic contour filtering and validation.
    """

    def extract_contours(
        self, image: np.ndarray
    ) -> Tuple[List[np.ndarray], np.ndarray]:
        """Extract contours from an image.

        Args:
            image (np.ndarray): Image to extract contours from (OpenCV format)

        Returns:
            Tuple[List[np.ndarray], np.ndarray]: Tuple of (contours, processed_image)
        """
        # Validate image
        if image is None or image.size == 0:
            raise ValueError("Invalid image")

        # Perform contour extraction (implemented by subclasses)
        contours, processed_image = self._extract_contours(image)

        # Filter contours (basic filtering, can be overridden by subclasses)
        filtered_contours = self._filter_contours(contours, image.shape)

        return filtered_contours, processed_image

    @abstractmethod
    def _extract_contours(
        self, image: np.ndarray
    ) -> Tuple[List[np.ndarray], np.ndarray]:
        """Extract contours from an image.

        This method should be implemented by subclasses to perform the
        specific contour extraction logic.

        Args:
            image (np.ndarray): Image to extract contours from (OpenCV format)

        Returns:
            Tuple[List[np.ndarray], np.ndarray]: Tuple of (contours, processed_image)
        """
        pass

    def _filter_contours(
        self, contours: List[np.ndarray], image_shape: Tuple[int, ...]
    ) -> List[np.ndarray]:
        """Filter contours based on basic criteria.

        Args:
            contours (List[np.ndarray]): Contours to filter
            image_shape (Tuple[int, ...]): Shape of the original image

        Returns:
            List[np.ndarray]: Filtered contours
        """
        height, width = image_shape[:2]
        filtered_contours = []

        for contour in contours:
            # Skip very small contours
            area = cv2.contourArea(contour)
            if area < 5:
                continue

            # Skip very large contours (likely background)
            if area > 0.9 * width * height:
                continue

            filtered_contours.append(contour)

        return filtered_contours


class BaseColorExtractionStrategy(IColorExtractionStrategy, ABC):
    """Base abstract class for color extraction strategies.

    This class provides a common implementation for the IColorExtractionStrategy interface,
    including basic color validation and normalization.
    """

    def extract_colors(
        self, image: np.ndarray, contours: List[np.ndarray]
    ) -> List[Tuple[int, int, int]]:
        """Extract colors for contours.

        Args:
            image (np.ndarray): Image to extract colors from (OpenCV format)
            contours (List[np.ndarray]): Contours to extract colors for

        Returns:
            List[Tuple[int, int, int]]: List of RGB colors for each contour
        """
        # Validate image and contours
        if image is None or image.size == 0:
            raise ValueError("Invalid image")

        if not contours:
            return []

        # Perform color extraction (implemented by subclasses)
        colors = self._extract_colors(image, contours)

        # Normalize colors
        normalized_colors = []
        for color in colors:
            r, g, b = color
            r = max(0, min(255, r))
            g = max(0, min(255, g))
            b = max(0, min(255, b))
            normalized_colors.append((r, g, b))

        return normalized_colors

    @abstractmethod
    def _extract_colors(
        self, image: np.ndarray, contours: List[np.ndarray]
    ) -> List[Tuple[int, int, int]]:
        """Extract colors for contours.

        This method should be implemented by subclasses to perform the
        specific color extraction logic.

        Args:
            image (np.ndarray): Image to extract colors from (OpenCV format)
            contours (List[np.ndarray]): Contours to extract colors for

        Returns:
            List[Tuple[int, int, int]]: List of RGB colors for each contour
        """
        pass


class BaseSVGGenerationStrategy(ISVGGenerationStrategy, ABC):
    """Base abstract class for SVG generation strategies.

    This class provides a common implementation for the ISVGGenerationStrategy interface,
    including SVG header and footer generation.
    """

    def generate_svg(
        self,
        image: np.ndarray,
        contours: List[np.ndarray],
        colors: List[Tuple[int, int, int]],
    ) -> str:
        """Generate SVG from contours and colors.

        Args:
            image (np.ndarray): Original image (OpenCV format)
            contours (List[np.ndarray]): Contours to include in the SVG
            colors (List[Tuple[int, int, int]]): Colors for each contour (RGB)

        Returns:
            str: SVG content
        """
        # Validate inputs
        if image is None or image.size == 0:
            raise ValueError("Invalid image")

        if not contours:
            raise ValueError("No contours provided")

        if len(colors) < len(contours):
            # Extend colors if needed
            colors.extend([(0, 0, 0)] * (len(contours) - len(colors)))

        # Get image dimensions
        height, width = image.shape[:2]

        # Create SVG header
        svg_content = f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'

        # Generate SVG content (implemented by subclasses)
        svg_content += self._generate_svg_content(image, contours, colors)

        # Add SVG footer
        svg_content += "</svg>"

        return svg_content

    @abstractmethod
    def _generate_svg_content(
        self,
        image: np.ndarray,
        contours: List[np.ndarray],
        colors: List[Tuple[int, int, int]],
    ) -> str:
        """Generate the content of the SVG.

        This method should be implemented by subclasses to perform the
        specific SVG content generation logic.

        Args:
            image (np.ndarray): Original image (OpenCV format)
            contours (List[np.ndarray]): Contours to include in the SVG
            colors (List[Tuple[int, int, int]]): Colors for each contour (RGB)

        Returns:
            str: SVG content (without header and footer)
        """
        pass


class BaseFallbackStrategy(IFallbackStrategy, ABC):
    """Base abstract class for fallback strategies.

    This class provides a common implementation for the IFallbackStrategy interface,
    including error handling and result generation.
    """

    def generate_fallback(self, image: np.ndarray) -> TracingResult:
        """Generate a fallback result when primary strategies fail.

        Args:
            image (np.ndarray): Original image (OpenCV format)

        Returns:
            TracingResult: Fallback tracing result
        """
        try:
            # Validate image
            if image is None or image.size == 0:
                return TracingResult.error_result("Invalid image")

            # Perform fallback generation (implemented by subclasses)
            svg_content = self._generate_fallback_content(image)

            # Return success result
            return TracingResult.success_result(
                svg_content=svg_content,
                path_count=0,  # No paths in fallback SVG
                metadata={"fallback": True},
            )
        except Exception as e:
            logger.error(f"Error generating fallback: {str(e)}")
            return TracingResult.error_result(f"Fallback generation failed: {str(e)}")

    @abstractmethod
    def _generate_fallback_content(self, image: np.ndarray) -> str:
        """Generate fallback SVG content.

        This method should be implemented by subclasses to perform the
        specific fallback generation logic.

        Args:
            image (np.ndarray): Original image (OpenCV format)

        Returns:
            str: SVG content
        """
        pass
