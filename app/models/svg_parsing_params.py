from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class SVGParsingStrategy(str, Enum):
    """
    Enum for SVG parsing strategies
    """
    STANDARD = "standard"  # Standard SVG parsing strategy
    OPTIMIZED = "optimized"  # Optimized SVG parsing with advanced features
    SIMPLIFIED = "simplified"  # Simplified SVG parsing for better performance
    FALLBACK = "fallback"  # Fallback strategy for handling problematic SVGs


class SVGParsingParams(BaseModel):
    """
    Parameters for SVG parsing
    """
    svg_path: str = Field(..., description="Path to the SVG file")
    strategy: SVGParsingStrategy = Field(
        default=SVGParsingStrategy.STANDARD,
        description="Strategy to use for parsing SVG"
    )
    simplify_tolerance: Optional[float] = Field(
        default=None,
        description="Tolerance for path simplification (lower = more accurate, higher = more simplified)"
    )
    ignore_transforms: bool = Field(
        default=False,
        description="Whether to ignore transforms in the SVG"
    )
    extract_colors: bool = Field(
        default=True,
        description="Whether to extract colors from the SVG"
    )
    max_paths: Optional[int] = Field(
        default=None,
        description="Maximum number of paths to extract (None = no limit)"
    )
    error_handling: str = Field(
        default="raise",
        description="How to handle errors: 'raise', 'log', or 'ignore'"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata for the SVG parsing process"
    )


class SVGParsingParamBuilder:
    """
    Builder for SVGParsingParams
    """
    def __init__(self):
        self._svg_path = None
        self._strategy = SVGParsingStrategy.STANDARD
        self._simplify_tolerance = None
        self._ignore_transforms = False
        self._extract_colors = True
        self._max_paths = None
        self._error_handling = "raise"
        self._metadata = None

    def with_svg_path(self, svg_path: str) -> 'SVGParsingParamBuilder':
        """
        Set the SVG path
        """
        self._svg_path = svg_path
        return self

    def with_strategy(self, strategy: SVGParsingStrategy) -> 'SVGParsingParamBuilder':
        """
        Set the SVG parsing strategy
        """
        self._strategy = strategy
        return self

    def with_simplify_tolerance(self, tolerance: float) -> 'SVGParsingParamBuilder':
        """
        Set the simplify tolerance
        """
        self._simplify_tolerance = tolerance
        return self

    def with_ignore_transforms(self, ignore: bool) -> 'SVGParsingParamBuilder':
        """
        Set whether to ignore transforms
        """
        self._ignore_transforms = ignore
        return self

    def with_extract_colors(self, extract: bool) -> 'SVGParsingParamBuilder':
        """
        Set whether to extract colors
        """
        self._extract_colors = extract
        return self

    def with_max_paths(self, max_paths: int) -> 'SVGParsingParamBuilder':
        """
        Set the maximum number of paths to extract
        """
        self._max_paths = max_paths
        return self

    def with_error_handling(self, handling: str) -> 'SVGParsingParamBuilder':
        """
        Set the error handling strategy
        """
        self._error_handling = handling
        return self

    def with_metadata(self, metadata: Dict[str, Any]) -> 'SVGParsingParamBuilder':
        """
        Set additional metadata
        """
        self._metadata = metadata
        return self

    def build(self) -> SVGParsingParams:
        """
        Build the SVGParsingParams object
        """
        if not self._svg_path:
            raise ValueError("SVG path is required")

        return SVGParsingParams(
            svg_path=self._svg_path,
            strategy=self._strategy,
            simplify_tolerance=self._simplify_tolerance,
            ignore_transforms=self._ignore_transforms,
            extract_colors=self._extract_colors,
            max_paths=self._max_paths,
            error_handling=self._error_handling,
            metadata=self._metadata
        )
