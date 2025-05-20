"""Parameter objects for Lottie animation generation functionality.

This module provides parameter objects for Lottie animation generation operations,
reducing function parameter complexity and improving code readability.
"""

from enum import Enum
from typing import Dict, Any, Optional, List, Union, Callable, Tuple
from pydantic import Field, validator

from app.models.base_params import BaseParams, ParamBuilder


class LottieColorMode(str, Enum):
    """Color modes for Lottie animations."""
    COLORED = "colored"
    MONOCHROME = "monochrome"
    GRAYSCALE = "grayscale"


class LottieOptimizationLevel(int, Enum):
    """Optimization levels for Lottie animations."""
    NONE = 0
    BASIC = 1
    MEDIUM = 2
    AGGRESSIVE = 3


class LottieAnimationParams(BaseParams):
    """Parameters for Lottie animation generation.
    
    This parameter object encapsulates all options for creating Lottie animations,
    replacing the need for numerous function parameters.
    """
    # Required parameters
    frame_paths: List[str] = Field(..., description="List of paths to frame images")
    output_path: str = Field(..., description="Path to save the output Lottie animation")
    
    # Optional parameters with defaults
    width: int = Field(default=512, description="Width of the Lottie animation")
    height: int = Field(default=512, description="Height of the Lottie animation")
    fps: int = Field(default=24, description="Frames per second")
    color_mode: LottieColorMode = Field(default=LottieColorMode.COLORED, description="Color mode")
    background_color: Optional[str] = Field(default=None, description="Background color in hex format")
    optimization_level: LottieOptimizationLevel = Field(
        default=LottieOptimizationLevel.MEDIUM, 
        description="Optimization level for the animation"
    )
    simplify_shapes: bool = Field(default=True, description="Whether to simplify shapes")
    simplify_tolerance: float = Field(default=1.0, description="Tolerance for shape simplification")
    
    # Callback for progress tracking
    progress_callback: Optional[Callable[[int], None]] = Field(
        default=None, 
        description="Callback function for progress updates"
    )
    
    @validator('frame_paths')
    def validate_frame_paths(cls, v):
        """Validate that frame paths list is not empty."""
        if not v:
            raise ValueError("Frame paths list cannot be empty")
        return v
    
    @validator('output_path')
    def validate_output_path(cls, v):
        """Validate that output path is not empty."""
        if not v or not v.strip():
            raise ValueError("Output path cannot be empty")
        return v
    
    @validator('width', 'height')
    def validate_dimensions(cls, v):
        """Validate that dimensions are positive."""
        if v <= 0:
            raise ValueError("Dimensions must be positive")
        return v
    
    @validator('fps')
    def validate_fps(cls, v):
        """Validate that fps is positive."""
        if v <= 0:
            raise ValueError("FPS must be positive")
        return v
    
    @validator('background_color')
    def validate_background_color(cls, v):
        """Validate background color format."""
        if v is not None and not (v.startswith('#') and len(v) in [4, 7, 9]):
            raise ValueError("Background color must be in hex format (e.g., #RRGGBB)")
        return v
    
    @validator('simplify_tolerance')
    def validate_simplify_tolerance(cls, v):
        """Validate that simplify tolerance is positive."""
        if v <= 0:
            raise ValueError("Simplify tolerance must be positive")
        return v


class LottieAnimationParamBuilder(ParamBuilder[LottieAnimationParams]):
    """Builder for LottieAnimationParams.
    
    Provides a fluent interface for building Lottie animation parameters.
    """
    
    def __init__(self):
        """Initialize the builder with the LottieAnimationParams class."""
        super().__init__(LottieAnimationParams)
    
    def with_frame_paths(self, frame_paths: List[str]) -> 'LottieAnimationParamBuilder':
        """Set the frame paths."""
        return self.with_param("frame_paths", frame_paths)
    
    def with_output_path(self, output_path: str) -> 'LottieAnimationParamBuilder':
        """Set the output path."""
        return self.with_param("output_path", output_path)
    
    def with_dimensions(self, width: int, height: int) -> 'LottieAnimationParamBuilder':
        """Set the animation dimensions."""
        self.with_param("width", width)
        return self.with_param("height", height)
    
    def with_fps(self, fps: int) -> 'LottieAnimationParamBuilder':
        """Set the frames per second."""
        return self.with_param("fps", fps)
    
    def with_color_mode(self, color_mode: Union[LottieColorMode, str]) -> 'LottieAnimationParamBuilder':
        """Set the color mode."""
        if isinstance(color_mode, str):
            color_mode = LottieColorMode(color_mode)
        return self.with_param("color_mode", color_mode)
    
    def with_background_color(self, color: str) -> 'LottieAnimationParamBuilder':
        """Set the background color."""
        return self.with_param("background_color", color)
    
    def with_optimization_level(self, level: Union[LottieOptimizationLevel, int]) -> 'LottieAnimationParamBuilder':
        """Set the optimization level."""
        if isinstance(level, int):
            level = LottieOptimizationLevel(level)
        return self.with_param("optimization_level", level)
    
    def with_shape_simplification(self, simplify: bool, tolerance: float = 1.0) -> 'LottieAnimationParamBuilder':
        """Set shape simplification options."""
        self.with_param("simplify_shapes", simplify)
        return self.with_param("simplify_tolerance", tolerance)
    
    def with_progress_callback(self, callback: Callable[[int], None]) -> 'LottieAnimationParamBuilder':
        """Set the progress callback function."""
        return self.with_param("progress_callback", callback)


class SVGConversionParams(BaseParams):
    """Parameters for SVG conversion to Lottie.
    
    This parameter object encapsulates all options for converting SVG files to Lottie,
    replacing the need for numerous function parameters.
    """
    # Required parameters
    svg_paths: List[str] = Field(..., description="List of paths to SVG files")
    output_path: str = Field(..., description="Path to save the output Lottie animation")
    
    # Optional parameters with defaults
    width: int = Field(default=512, description="Width of the Lottie animation")
    height: int = Field(default=512, description="Height of the Lottie animation")
    fps: int = Field(default=24, description="Frames per second")
    background_color: Optional[str] = Field(default=None, description="Background color in hex format")
    optimize: bool = Field(default=True, description="Whether to optimize the Lottie file")
    optimize_shapes: bool = Field(default=True, description="Whether to optimize shapes")
    combine_paths: bool = Field(default=True, description="Whether to combine paths where possible")
    duration: float = Field(default=1.0, description="Duration of each frame in seconds")
    
    # Callback for progress tracking
    progress_callback: Optional[Callable[[int], None]] = Field(
        default=None, 
        description="Callback function for progress updates"
    )
    
    @validator('svg_paths')
    def validate_svg_paths(cls, v):
        """Validate that SVG paths list is not empty."""
        if not v:
            raise ValueError("SVG paths list cannot be empty")
        return v
    
    @validator('output_path')
    def validate_output_path(cls, v):
        """Validate that output path is not empty."""
        if not v or not v.strip():
            raise ValueError("Output path cannot be empty")
        return v
    
    @validator('width', 'height')
    def validate_dimensions(cls, v):
        """Validate that dimensions are positive."""
        if v <= 0:
            raise ValueError("Dimensions must be positive")
        return v
    
    @validator('fps')
    def validate_fps(cls, v):
        """Validate that fps is positive."""
        if v <= 0:
            raise ValueError("FPS must be positive")
        return v
    
    @validator('duration')
    def validate_duration(cls, v):
        """Validate that duration is positive."""
        if v <= 0:
            raise ValueError("Duration must be positive")
        return v


class SVGConversionParamBuilder(ParamBuilder[SVGConversionParams]):
    """Builder for SVGConversionParams.
    
    Provides a fluent interface for building SVG conversion parameters.
    """
    
    def __init__(self):
        """Initialize the builder with the SVGConversionParams class."""
        super().__init__(SVGConversionParams)
    
    def with_svg_paths(self, svg_paths: List[str]) -> 'SVGConversionParamBuilder':
        """Set the SVG paths."""
        return self.with_param("svg_paths", svg_paths)
    
    def with_output_path(self, output_path: str) -> 'SVGConversionParamBuilder':
        """Set the output path."""
        return self.with_param("output_path", output_path)
    
    def with_dimensions(self, width: int, height: int) -> 'SVGConversionParamBuilder':
        """Set the animation dimensions."""
        self.with_param("width", width)
        return self.with_param("height", height)
    
    def with_fps(self, fps: int) -> 'SVGConversionParamBuilder':
        """Set the frames per second."""
        return self.with_param("fps", fps)
    
    def with_background_color(self, color: str) -> 'SVGConversionParamBuilder':
        """Set the background color."""
        return self.with_param("background_color", color)
    
    def with_optimization(self, optimize: bool, optimize_shapes: bool = True) -> 'SVGConversionParamBuilder':
        """Set optimization options."""
        self.with_param("optimize", optimize)
        return self.with_param("optimize_shapes", optimize_shapes)
    
    def with_path_combining(self, combine_paths: bool) -> 'SVGConversionParamBuilder':
        """Set whether to combine paths."""
        return self.with_param("combine_paths", combine_paths)
    
    def with_duration(self, duration: float) -> 'SVGConversionParamBuilder':
        """Set the frame duration."""
        return self.with_param("duration", duration)
    
    def with_progress_callback(self, callback: Callable[[int], None]) -> 'SVGConversionParamBuilder':
        """Set the progress callback function."""
        return self.with_param("progress_callback", callback)


class ImageTracingStrategy(str, Enum):
    """Strategies for image tracing."""
    BASIC = "basic"
    STANDARD = "standard"
    ADVANCED = "advanced"


class ImageTracingParams(BaseParams):
    """Parameters for image tracing.
    
    This parameter object encapsulates all options for tracing raster images to vector formats,
    replacing the need for numerous function parameters.
    """
    # Required parameters
    input_path: str = Field(..., description="Path to the input image")
    output_path: str = Field(..., description="Path to save the output vector file")
    
    # Optional parameters with defaults
    strategy: ImageTracingStrategy = Field(
        default=ImageTracingStrategy.ADVANCED, 
        description="Tracing strategy to use"
    )
    simplify_tolerance: float = Field(
        default=1.0, 
        description="Tolerance for path simplification (higher = more simplification)"
    )
    color_mode: LottieColorMode = Field(
        default=LottieColorMode.COLORED, 
        description="Color mode for the traced output"
    )
    embed_image: bool = Field(
        default=True, 
        description="Whether to embed the original image in the output"
    )
    image_quality: int = Field(
        default=90, 
        description="Quality of the embedded image (0-100)"
    )
    
    # Callback for progress tracking
    progress_callback: Optional[Callable[[float, Optional[str]], None]] = Field(
        default=None, 
        description="Callback function for progress updates"
    )
    
    @validator('input_path', 'output_path')
    def validate_paths(cls, v):
        """Validate that paths are not empty."""
        if not v or not v.strip():
            raise ValueError("Path cannot be empty")
        return v
    
    @validator('simplify_tolerance')
    def validate_simplify_tolerance(cls, v):
        """Validate that simplify tolerance is positive."""
        if v <= 0:
            raise ValueError("Simplify tolerance must be positive")
        return v
    
    @validator('image_quality')
    def validate_image_quality(cls, v):
        """Validate that image quality is between 0 and 100."""
        if v < 0 or v > 100:
            raise ValueError("Image quality must be between 0 and 100")
        return v


class ImageTracingParamBuilder(ParamBuilder[ImageTracingParams]):
    """Builder for ImageTracingParams.
    
    Provides a fluent interface for building image tracing parameters.
    """
    
    def __init__(self):
        """Initialize the builder with the ImageTracingParams class."""
        super().__init__(ImageTracingParams)
    
    def with_input_path(self, input_path: str) -> 'ImageTracingParamBuilder':
        """Set the input path."""
        return self.with_param("input_path", input_path)
    
    def with_output_path(self, output_path: str) -> 'ImageTracingParamBuilder':
        """Set the output path."""
        return self.with_param("output_path", output_path)
    
    def with_strategy(self, strategy: Union[ImageTracingStrategy, str]) -> 'ImageTracingParamBuilder':
        """Set the tracing strategy."""
        if isinstance(strategy, str):
            strategy = ImageTracingStrategy(strategy)
        return self.with_param("strategy", strategy)
    
    def with_simplify_tolerance(self, tolerance: float) -> 'ImageTracingParamBuilder':
        """Set the simplify tolerance."""
        return self.with_param("simplify_tolerance", tolerance)
    
    def with_color_mode(self, color_mode: Union[LottieColorMode, str]) -> 'ImageTracingParamBuilder':
        """Set the color mode."""
        if isinstance(color_mode, str):
            color_mode = LottieColorMode(color_mode)
        return self.with_param("color_mode", color_mode)
    
    def with_embed_image(self, embed: bool, quality: int = 90) -> 'ImageTracingParamBuilder':
        """Set whether to embed the original image and its quality."""
        self.with_param("embed_image", embed)
        return self.with_param("image_quality", quality)
    
    def with_progress_callback(self, callback: Callable[[float, Optional[str]], None]) -> 'ImageTracingParamBuilder':
        """Set the progress callback function."""
        return self.with_param("progress_callback", callback)
