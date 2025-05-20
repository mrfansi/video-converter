"""Converter interfaces for the Video Converter project.

This module defines the core interfaces for video and animation conversion operations.
These interfaces follow the Interface Segregation Principle (ISP) by providing
focused interfaces for specific conversion types.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Callable

from app.models.video_params import VideoConversionParams
from app.models.lottie_params import LottieAnimationParams, SVGConversionParams


class ConversionResult:
    """Result of a conversion operation.
    
    This class encapsulates the result of a conversion operation, including
    success status, output path, and any error information.
    """
    
    def __init__(
        self, 
        success: bool, 
        output_path: Optional[str] = None, 
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Initialize a conversion result.
        
        Args:
            success (bool): Whether the conversion was successful
            output_path (Optional[str], optional): Path to the output file. Defaults to None.
            error (Optional[str], optional): Error message if conversion failed. Defaults to None.
            metadata (Optional[Dict[str, Any]], optional): Additional metadata. Defaults to None.
        """
        self.success = success
        self.output_path = output_path
        self.error = error
        self.metadata = metadata or {}
    
    @classmethod
    def success_result(cls, output_path: str, metadata: Optional[Dict[str, Any]] = None) -> 'ConversionResult':
        """Create a successful conversion result.
        
        Args:
            output_path (str): Path to the output file
            metadata (Optional[Dict[str, Any]], optional): Additional metadata. Defaults to None.
            
        Returns:
            ConversionResult: A successful conversion result
        """
        return cls(True, output_path=output_path, metadata=metadata)
    
    @classmethod
    def error_result(cls, error: str, metadata: Optional[Dict[str, Any]] = None) -> 'ConversionResult':
        """Create an error conversion result.
        
        Args:
            error (str): Error message
            metadata (Optional[Dict[str, Any]], optional): Additional metadata. Defaults to None.
            
        Returns:
            ConversionResult: An error conversion result
        """
        return cls(False, error=error, metadata=metadata)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the result
        """
        result = {
            "success": self.success,
            "metadata": self.metadata
        }
        
        if self.output_path:
            result["output_path"] = self.output_path
            
        if self.error:
            result["error"] = self.error
            
        return result


class IConverter(ABC):
    """Base interface for all converters.
    
    This interface defines the common contract for all converters in the system.
    It follows the Interface Segregation Principle by providing a minimal interface
    that all converters must implement.
    """
    
    @abstractmethod
    def can_convert(self, source_format: str, target_format: str) -> bool:
        """Check if this converter can handle the specified conversion.
        
        Args:
            source_format (str): Source format (e.g., "mp4", "png")
            target_format (str): Target format (e.g., "webm", "svg")
            
        Returns:
            bool: True if this converter can handle the conversion, False otherwise
        """
        pass


class IVideoConverter(IConverter):
    """Interface for video format converters.
    
    This interface defines the contract for converters that handle video format
    conversions (e.g., MP4 to WebM, MP4 to GIF).
    """
    
    @abstractmethod
    def convert(self, params: VideoConversionParams) -> ConversionResult:
        """Convert a video to the specified format.
        
        Args:
            params (VideoConversionParams): Conversion parameters
            
        Returns:
            ConversionResult: Result of the conversion operation
        """
        pass


class ILottieGenerator(IConverter):
    """Interface for Lottie animation generators.
    
    This interface defines the contract for converters that generate Lottie
    animations from various sources (e.g., video frames, SVG files).
    """
    
    @abstractmethod
    def generate_from_frames(self, params: LottieAnimationParams) -> ConversionResult:
        """Generate a Lottie animation from image frames.
        
        Args:
            params (LottieAnimationParams): Animation generation parameters
            
        Returns:
            ConversionResult: Result of the generation operation
        """
        pass
    
    @abstractmethod
    def generate_from_svgs(self, params: SVGConversionParams) -> ConversionResult:
        """Generate a Lottie animation from SVG files.
        
        Args:
            params (SVGConversionParams): SVG conversion parameters
            
        Returns:
            ConversionResult: Result of the generation operation
        """
        pass


class IImageTracer(IConverter):
    """Interface for image tracers.
    
    This interface defines the contract for converters that trace raster images
    to vector formats (e.g., PNG to SVG).
    """
    
    @abstractmethod
    def trace_image(self, input_path: str, output_path: str, **options) -> str:
        """Trace a raster image to a vector format.
        
        Args:
            input_path (str): Path to the input image
            output_path (str): Path to save the output vector file
            **options: Additional options for the tracing operation
            
        Returns:
            str: Path to the output vector file
        """
        pass
