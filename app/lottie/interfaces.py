from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class IImageProcessor(ABC):
    """
    Interface for image processing and SVG conversion
    """
    @abstractmethod
    def trace_png_to_svg(self, png_path: str, output_dir: str, simplify_tolerance: float = 1.0) -> str:
        """
        Trace a PNG image to SVG
        
        Args:
            png_path: Path to the PNG image
            output_dir: Directory to save the SVG file
            simplify_tolerance: Tolerance for path simplification
            
        Returns:
            Path to the SVG file
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
    def parse_svg_paths_to_lottie_format(self, svg_paths: List[str]) -> List[List[Dict[str, Any]]]:
        """
        Parse multiple SVG files and extract paths in Lottie-compatible format
        
        Args:
            svg_paths: List of paths to SVG files
            
        Returns:
            List of frames, each containing a list of paths in Lottie format
        """
        pass

class ILottieGenerator(ABC):
    """
    Interface for Lottie animation generation
    """
    @abstractmethod
    def create_lottie_animation(self, 
                               frame_paths: List[List[Dict[str, Any]]], 
                               fps: int = 30,
                               width: Optional[int] = None,
                               height: Optional[int] = None,
                               max_frames: int = 100,
                               optimize: bool = True) -> Dict[str, Any]:
        """
        Create a Lottie animation from parsed SVG paths
        
        Args:
            frame_paths: List of frames, each containing a list of paths
            fps: Frames per second
            width: Width of the animation
            height: Height of the animation
            max_frames: Maximum number of frames to include
            optimize: Whether to apply optimizations
            
        Returns:
            Lottie animation JSON
        """
        pass
    
    @abstractmethod
    def save_lottie_json(self, lottie_json: Dict[str, Any], output_path: str, compress: bool = True) -> str:
        """
        Save Lottie JSON to file with optional compression
        
        Args:
            lottie_json: Lottie animation JSON
            output_path: Path to save the JSON file
            compress: Whether to compress the JSON output
            
        Returns:
            Path to the saved JSON file
        """
        pass
