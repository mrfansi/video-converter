"""
Base strategies for SVG parsing.

This module provides base implementations for SVG parsing strategies.
"""

import logging
from typing import List, Dict, Any, Tuple, Optional
from app.domain.interfaces.svg_parsing import (
    ISVGPathParsingStrategy,
    ISegmentProcessor,
    ISVGElementFilter,
    ILottiePathBuilder,
)

# Configure logging
logger = logging.getLogger(__name__)


class BaseSegmentProcessor(ISegmentProcessor):
    """
    Base implementation of ISegmentProcessor
    """

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def process_segment(
        self, segment, current_point, vertices, in_tangents, out_tangents
    ) -> Tuple[List, List, List, Any]:
        """
        Process a path segment and update vertices and tangents

        Args:
            segment: Path segment to process
            current_point: Current point in the path
            vertices: List of vertices
            in_tangents: List of in tangents
            out_tangents: List of out tangents

        Returns:
            Tuple containing updated vertices, in_tangents, out_tangents, and current_point
        """
        segment_type = segment.__class__.__name__

        if segment_type == "Move":
            return self._process_move_segment(
                segment, vertices, in_tangents, out_tangents
            )
        if segment_type == "Line":
            return self._process_line_segment(
                segment, vertices, in_tangents, out_tangents
            )
        if segment_type == "CubicBezier":
            return self._process_cubic_bezier_segment(
                segment, current_point, vertices, in_tangents, out_tangents
            )
        if segment_type == "Close" and vertices:
            return vertices, in_tangents, out_tangents, current_point

        return vertices, in_tangents, out_tangents, current_point

    # pylint: disable=too-many-arguments
    def _process_move_segment(
        self, segment, vertices, in_tangents, out_tangents
    ) -> Tuple[List, List, List, Any]:
        """
        Process a Move segment
        """
        vertices.append([segment.end.x, segment.end.y])
        in_tangents.append([0, 0])  # No tangents for move
        out_tangents.append([0, 0])
        current_point = segment.end
        return vertices, in_tangents, out_tangents, current_point

    # pylint: disable=too-many-arguments
    def _process_line_segment(
        self, segment, vertices, in_tangents, out_tangents
    ) -> Tuple[List, List, List, Any]:
        """
        Process a Line segment
        """
        vertices.append([segment.end.x, segment.end.y])
        # For lines, tangents are zero vectors
        in_tangents.append([0, 0])
        out_tangents.append([0, 0])
        current_point = segment.end
        return vertices, in_tangents, out_tangents, current_point

    # pylint: disable=too-many-arguments
    def _process_cubic_bezier_segment(
        self, segment, current_point, vertices, in_tangents, out_tangents
    ) -> Tuple[List, List, List, Any]:
        """
        Process a CubicBezier segment
        """
        vertices.append([segment.end.x, segment.end.y])

        # Calculate relative control points (Lottie format)
        if current_point:
            # Out tangent of previous point (relative to current point)
            out_dx = segment.control1.x - current_point.x
            out_dy = segment.control1.y - current_point.y
            out_tangents[-1] = [out_dx, out_dy]

            # In tangent of current point (relative to end point)
            in_dx = segment.control2.x - segment.end.x
            in_dy = segment.control2.y - segment.end.y
            in_tangents.append([in_dx, in_dy])
        else:
            in_tangents.append([0, 0])

        out_tangents.append([0, 0])  # Will be set by next segment if needed
        current_point = segment.end
        return vertices, in_tangents, out_tangents, current_point


class BaseSVGElementFilter(ISVGElementFilter):
    """
    Base implementation of ISVGElementFilter
    """

    # pylint: disable=too-few-public-methods
    def should_process(self, element) -> bool:
        """
        Determine if an SVG element should be processed

        Args:
            element: SVG element to check

        Returns:
            True if the element should be processed, False otherwise
        """
        # Default implementation processes all path elements
        try:
            # Import here to avoid circular imports
            from svgelements import (
                Path as SVGPath,
            )  # pylint: disable=import-outside-toplevel

            return isinstance(element, SVGPath)
        except ImportError:
            # If svgelements is not available, try to check if it's a path by name
            return (
                hasattr(element, "__class__") and element.__class__.__name__ == "Path"
            )


class BaseLottiePathBuilder(ILottiePathBuilder):
    """
    Base implementation of ILottiePathBuilder
    """

    # pylint: disable=too-few-public-methods
    def build_lottie_path(
        self, vertices: List, in_tangents: List, out_tangents: List, closed: bool
    ) -> Dict[str, Any]:
        """
        Build a Lottie path object from vertices and tangents

        Args:
            vertices: List of vertices
            in_tangents: List of in tangents
            out_tangents: List of out tangents
            closed: Whether the path is closed

        Returns:
            Dict representing a Lottie path
        """
        return {
            "ty": "sh",  # Type: Shape
            "ks": {  # Keyframes
                "a": 0,  # Animated: 0 for no
                "k": {  # Keyframe value
                    "c": closed,  # Closed path
                    "i": in_tangents,  # In tangents
                    "o": out_tangents,  # Out tangents
                    "v": vertices,  # Vertices
                },
            },
        }


class BaseSVGPathParsingStrategy(ISVGPathParsingStrategy):
    """
    Base implementation of ISVGPathParsingStrategy
    """

    # pylint: disable=too-few-public-methods
    def __init__(
        self, segment_processor: ISegmentProcessor, path_builder: ILottiePathBuilder
    ):
        self.segment_processor = segment_processor
        self.path_builder = path_builder

    def parse_path_element(self, element) -> Optional[Dict[str, Any]]:
        """
        Parse an SVG path element into Lottie-compatible format

        Args:
            element: SVG path element to parse

        Returns:
            Dict representing a Lottie path or None if parsing failed
        """
        try:
            # Process path to standard Lottie bezier format
            vertices: List[Dict[str, float]] = []
            in_tangents: List[Dict[str, float]] = []
            out_tangents: List[Dict[str, float]] = []
            closed = getattr(element, "closed", False)

            # Process path segments to extract points and tangents
            current_point = None
            for segment in element:
                vertices, in_tangents, out_tangents, current_point = (
                    self.segment_processor.process_segment(
                        segment, current_point, vertices, in_tangents, out_tangents
                    )
                )

            # Create standard Lottie path object
            return self.path_builder.build_lottie_path(
                vertices, in_tangents, out_tangents, closed
            )
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Error parsing SVG path element: %s", str(e))
            return None
