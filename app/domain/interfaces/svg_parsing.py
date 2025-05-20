from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple, Optional


class ISVGPathParsingStrategy(ABC):
    """
    Interface for SVG path parsing strategies
    """

    @abstractmethod
    def parse_path_element(self, element) -> Optional[Dict[str, Any]]:
        """
        Parse an SVG path element into Lottie-compatible format

        Args:
            element: SVG path element to parse

        Returns:
            Dict representing a Lottie path or None if parsing failed
        """
        pass


class ISegmentProcessor(ABC):
    """
    Interface for processing individual path segments
    """

    @abstractmethod
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
        pass


class ISVGParser(ABC):
    """
    Interface for SVG parsing and conversion to Lottie format
    """

    @abstractmethod
    def parse_svg_to_paths(self, svg_path: str) -> List[Dict[str, Any]]:
        """
        Parse SVG file and extract paths in Lottie-compatible format

        Args:
            svg_path: Path to the SVG file

        Returns:
            List of paths in Lottie format
        """
        pass

    @abstractmethod
    def parse_svg_paths_to_lottie_format(
        self, svg_paths: List[str]
    ) -> List[List[Dict[str, Any]]]:
        """
        Parse multiple SVG files and extract paths in Lottie-compatible format

        Args:
            svg_paths: List of paths to SVG files

        Returns:
            List of frames, each containing a list of paths in Lottie format
        """
        pass


class ISVGElementFilter(ABC):
    """
    Interface for filtering SVG elements
    """

    @abstractmethod
    def should_process(self, element) -> bool:
        """
        Determine if an SVG element should be processed

        Args:
            element: SVG element to check

        Returns:
            True if the element should be processed, False otherwise
        """
        pass


class ILottiePathBuilder(ABC):
    """
    Interface for building Lottie path objects
    """

    @abstractmethod
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
        pass
