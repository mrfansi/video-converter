"""Image tracing interfaces for the Video Converter project.

This module defines the core interfaces for image tracing operations.
These interfaces follow the Interface Segregation Principle (ISP) by providing
focused interfaces for specific image tracing strategies.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple
import numpy as np


class TracingResult:
    """Result of an image tracing operation.
    
    This class encapsulates the result of an image tracing operation, including
    the SVG content, paths, and any error information.
    """
    
    def __init__(
        self, 
        success: bool, 
        svg_content: Optional[str] = None,
        path_count: int = 0,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Initialize a tracing result.
        
        Args:
            success (bool): Whether the tracing was successful
            svg_content (Optional[str], optional): SVG content. Defaults to None.
            path_count (int, optional): Number of paths in the SVG. Defaults to 0.
            error (Optional[str], optional): Error message if tracing failed. Defaults to None.
            metadata (Optional[Dict[str, Any]], optional): Additional metadata. Defaults to None.
        """
        self.success = success
        self.svg_content = svg_content
        self.path_count = path_count
        self.error = error
        self.metadata = metadata or {}
    
    @classmethod
    def success_result(cls, svg_content: str, path_count: int = 0, metadata: Optional[Dict[str, Any]] = None) -> 'TracingResult':
        """Create a successful tracing result.
        
        Args:
            svg_content (str): SVG content
            path_count (int, optional): Number of paths in the SVG. Defaults to 0.
            metadata (Optional[Dict[str, Any]], optional): Additional metadata. Defaults to None.
            
        Returns:
            TracingResult: A successful tracing result
        """
        return cls(True, svg_content=svg_content, path_count=path_count, metadata=metadata)
    
    @classmethod
    def error_result(cls, error: str, metadata: Optional[Dict[str, Any]] = None) -> 'TracingResult':
        """Create an error tracing result.
        
        Args:
            error (str): Error message
            metadata (Optional[Dict[str, Any]], optional): Additional metadata. Defaults to None.
            
        Returns:
            TracingResult: An error tracing result
        """
        return cls(False, error=error, metadata=metadata)


class IImageTracingStrategy(ABC):
    """Interface for image tracing strategies.
    
    This interface defines the contract for image tracing strategies in the system.
    It follows the Interface Segregation Principle by providing a focused interface
    for image tracing operations.
    """
    
    @abstractmethod
    def trace_image(self, image: np.ndarray, simplify_tolerance: float = 1.0) -> TracingResult:
        """Trace an image to SVG.
        
        Args:
            image (np.ndarray): Image to trace (OpenCV format)
            simplify_tolerance (float, optional): Tolerance for path simplification. Defaults to 1.0.
            
        Returns:
            TracingResult: Result of the tracing operation
        """
        pass


class IContourExtractionStrategy(ABC):
    """Interface for contour extraction strategies.
    
    This interface defines the contract for contour extraction strategies in the system.
    It follows the Interface Segregation Principle by providing a focused interface
    for contour extraction operations.
    """
    
    @abstractmethod
    def extract_contours(self, image: np.ndarray) -> Tuple[List[np.ndarray], np.ndarray]:
        """Extract contours from an image.
        
        Args:
            image (np.ndarray): Image to extract contours from (OpenCV format)
            
        Returns:
            Tuple[List[np.ndarray], np.ndarray]: Tuple of (contours, processed_image)
        """
        pass


class IColorExtractionStrategy(ABC):
    """Interface for color extraction strategies.
    
    This interface defines the contract for color extraction strategies in the system.
    It follows the Interface Segregation Principle by providing a focused interface
    for color extraction operations.
    """
    
    @abstractmethod
    def extract_colors(self, image: np.ndarray, contours: List[np.ndarray]) -> List[Tuple[int, int, int]]:
        """Extract colors for contours.
        
        Args:
            image (np.ndarray): Image to extract colors from (OpenCV format)
            contours (List[np.ndarray]): Contours to extract colors for
            
        Returns:
            List[Tuple[int, int, int]]: List of RGB colors for each contour
        """
        pass


class ISVGGenerationStrategy(ABC):
    """Interface for SVG generation strategies.
    
    This interface defines the contract for SVG generation strategies in the system.
    It follows the Interface Segregation Principle by providing a focused interface
    for SVG generation operations.
    """
    
    @abstractmethod
    def generate_svg(self, image: np.ndarray, contours: List[np.ndarray], colors: List[Tuple[int, int, int]]) -> str:
        """Generate SVG from contours and colors.
        
        Args:
            image (np.ndarray): Original image (OpenCV format)
            contours (List[np.ndarray]): Contours to include in the SVG
            colors (List[Tuple[int, int, int]]): Colors for each contour (RGB)
            
        Returns:
            str: SVG content
        """
        pass


class IFallbackStrategy(ABC):
    """Interface for fallback strategies.
    
    This interface defines the contract for fallback strategies in the system.
    It follows the Interface Segregation Principle by providing a focused interface
    for fallback operations when primary strategies fail.
    """
    
    @abstractmethod
    def generate_fallback(self, image: np.ndarray) -> TracingResult:
        """Generate a fallback result when primary strategies fail.
        
        Args:
            image (np.ndarray): Original image (OpenCV format)
            
        Returns:
            TracingResult: Fallback tracing result
        """
        pass
