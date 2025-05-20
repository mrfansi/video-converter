"""SVG parser implementation using the Strategy pattern.

This module provides the main SVG parser implementation that uses the Strategy pattern
to parse SVG files into Lottie-compatible paths.
"""

import logging
from typing import List, Dict, Any, Optional
from svgelements import SVG, Path as SVGPath

from app.domain.interfaces.svg_parsing import ISVGPathParsingStrategy
from app.models.svg_parsing_params import SVGParsingParams
from app.infrastructure.svg_parsing.parsing_strategies import (
    StandardSVGPathParsingStrategy,
    OptimizedSVGPathParsingStrategy,
    SimplifiedSVGPathParsingStrategy,
    EnhancedSVGPathParsingStrategy,
    FallbackSVGPathParsingStrategy,
)

# Configure logging
logger = logging.getLogger(__name__)


class SVGParserProcessor:
    """SVG Parser that uses the Strategy pattern for parsing SVG files.

    This class implements the Strategy pattern to provide flexible SVG parsing
    with different strategies for various use cases and requirements.
    """

    def __init__(self):
        # Initialize default strategies
        self.standard_strategy = StandardSVGPathParsingStrategy()
        self.optimized_strategy = OptimizedSVGPathParsingStrategy()
        self.simplified_strategy = SimplifiedSVGPathParsingStrategy()
        self.enhanced_strategy = EnhancedSVGPathParsingStrategy()
        self.fallback_strategy = FallbackSVGPathParsingStrategy()

        # Default to standard strategy
        self.current_strategy = self.standard_strategy

    def select_strategy(
        self,
        params: Optional[SVGParsingParams] = None,
    ) -> ISVGPathParsingStrategy:
        """Select the appropriate parsing strategy based on parameters.

        Args:
            params: SVG parsing parameters

        Returns:
            The selected SVG path parsing strategy
        """
        if not params:
            logger.info("No parameters provided, using standard strategy")
            return self.standard_strategy

        strategy_name = str(params.strategy).lower() if params.strategy else "standard"

        if strategy_name == "optimized":
            logger.info("Using optimized SVG parsing strategy")
            return self.optimized_strategy
        if strategy_name == "simplified":
            logger.info("Using simplified SVG parsing strategy")
            return self.simplified_strategy
        if strategy_name == "enhanced":
            logger.info("Using enhanced SVG parsing strategy")
            return self.enhanced_strategy
        if strategy_name == "fallback":
            logger.info("Using fallback SVG parsing strategy")
            return self.fallback_strategy

        logger.info("Unknown strategy '%s', using standard strategy", strategy_name)
        return self.standard_strategy

    # pylint: disable=too-many-locals,too-many-branches

    def parse_svg_to_paths(
        self,
        svg_path: str,
        params: Optional[SVGParsingParams] = None,
    ) -> List[Dict[str, Any]]:
        """Parse an SVG file into a list of Lottie-compatible paths.

        Args:
            svg_path: Path to the SVG file
            params: SVG parsing parameters

        Returns:
            List of Lottie-compatible path objects
        """
        try:
            # Select the appropriate strategy based on parameters
            self.current_strategy = self.select_strategy(params)

            # Parse the SVG file
            logger.info("Parsing SVG file: %s", svg_path)
            svg = SVG.parse(svg_path)

            # Extract paths from the SVG
            paths = []
            for element in svg.elements():
                if isinstance(element, SVGPath):
                    path = self.current_strategy.parse_path_element(element)
                    if path:
                        paths.append(path)

            if not paths:
                logger.warning("No paths found in SVG file: %s", svg_path)
                # Try fallback strategy if no paths were found
                if self.current_strategy != self.fallback_strategy:
                    logger.info("Trying fallback strategy")
                    self.current_strategy = self.fallback_strategy

                    # Try again with fallback strategy
                    for element in svg.elements():
                        if isinstance(element, SVGPath):
                            path = self.current_strategy.parse_path_element(element)
                            if path:
                                paths.append(path)

            logger.info("Extracted %d paths from SVG file", len(paths))
            return paths
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Error parsing SVG file: %s", str(e))
            if self.current_strategy != self.fallback_strategy:
                logger.info("Trying fallback strategy after error")
                self.current_strategy = self.fallback_strategy

                # Try again with fallback strategy
                try:
                    svg = SVG.parse(svg_path)
                    paths = []

                    for element in svg.elements():
                        if isinstance(element, SVGPath):
                            path = self.current_strategy.parse_path_element(element)
                            if path:
                                paths.append(path)

                    logger.info("Fallback strategy extracted %d paths", len(paths))
                    return paths
                except Exception as e2:  # pylint: disable=broad-exception-caught
                    logger.error("Fallback strategy also failed: %s", str(e2))

            # If all strategies fail, return an empty list
            return []

    def parse_svg_paths_to_lottie_format(
        self,
        svg_paths: List[str],
        params: Optional[SVGParsingParams] = None,
    ) -> List[List[Dict[str, Any]]]:
        """Parse multiple SVG files and extract paths in Lottie-compatible format.

        Args:
            svg_paths: List of paths to SVG files
            params: Optional parameters for parsing

        Returns:
            List of frames, each containing a list of paths in Lottie format
        """
        frame_paths = []

        for svg_path in svg_paths:
            # Parse SVG file and extract paths
            paths = self.parse_svg_to_paths(svg_path, params)
            frame_paths.append(paths)

        return frame_paths
