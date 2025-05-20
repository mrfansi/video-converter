import os
import json
import logging
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the new SOLID-based implementation
from app.lottie import LottieGeneratorFacade

# Create a global facade instance for compatibility
_facade = LottieGeneratorFacade()

# This file serves as a compatibility layer for existing code
# that still imports from the original lottie_generator.py file.
# It forwards all calls to the new SOLID-based implementation.
logger.info("Using SOLID-based Lottie generator implementation via compatibility layer")


def trace_png_to_svg(png_path: str, output_dir: str, simplify_tolerance: float = 1.0) -> str:
    """
    Compatibility function that forwards to the new SOLID-based implementation.
    Traces a PNG image to SVG using OpenCV contour detection.
    
    Args:
        png_path: Path to the PNG image
        output_dir: Directory to save the SVG file
        simplify_tolerance: Tolerance for path simplification
        
    Returns:
        Path to the SVG file
    """
    return _facade.trace_png_to_svg(png_path, output_dir, simplify_tolerance)


def parse_svg_to_paths(svg_path: str) -> List[Dict[str, Any]]:
    """
    Compatibility function that forwards to the new SOLID-based implementation.
    Parse SVG file and extract paths in Lottie-compatible format
    
    Args:
        svg_path: Path to the SVG file
        
    Returns:
        List of paths in Lottie format
    """
    return _facade.svg_parser.parse_svg_to_paths(svg_path)


def parse_svg_paths_to_lottie_format(svg_paths: List[str]) -> List[List[Dict[str, Any]]]:
    """
    Compatibility function that forwards to the new SOLID-based implementation.
    Parse multiple SVG files and extract paths in Lottie-compatible format
    
    Args:
        svg_paths: List of paths to SVG files
        
    Returns:
        List of frames, each containing a list of paths in Lottie format
    """
    return _facade.svg_parser.parse_svg_paths_to_lottie_format(svg_paths)


def save_lottie_json(lottie_json: Dict[str, Any], output_path: str, compress: bool = True) -> str:
    """
    Compatibility function that forwards to the new SOLID-based implementation.
    Save Lottie JSON to file with optional compression
    
    Args:
        lottie_json: Lottie animation JSON
        output_path: Path to save the JSON file
        compress: Whether to compress the JSON output
        
    Returns:
        Path to the saved JSON file
    """
    return _facade.lottie_generator.save_lottie_json(lottie_json, output_path, compress)


def create_lottie_animation(
    svg_paths: List[str],
    fps: int = 30,
    width: Optional[int] = None,
    height: Optional[int] = None,
    max_frames: int = 100,
    optimize: bool = True,
) -> Dict[str, Any]:
    """
    Compatibility function that forwards to the new SOLID-based implementation.
    Create a Lottie animation from a list of SVG files
    
    Args:
        svg_paths: List of SVG file paths
        fps: Frames per second
        width: Width of the animation (optional)
        height: Height of the animation (optional)
        max_frames: Maximum number of frames to include
        optimize: Whether to apply optimizations
        
    Returns:
        Lottie animation JSON
    """
    # Parse SVG paths to get frame data
    frame_paths = _facade.svg_parser.parse_svg_paths_to_lottie_format(svg_paths)
    
    # Create Lottie animation
    return _facade.lottie_generator.create_lottie_animation(
        frame_paths,
        fps=fps,
        width=width,
        height=height,
        max_frames=max_frames,
        optimize=optimize
    )


def create_lottie_animation_manual(
    frame_paths: List[List[Dict[str, Any]]],
    fps: int = 30,
    width: int = 1920,
    height: int = 1080,
    max_frames: int = 100,
    optimize: bool = True,
) -> Dict[str, Any]:
    """
    Compatibility function that forwards to the new SOLID-based implementation.
    Create a Lottie animation from parsed SVG paths manually
    
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
    # Use the manual generator directly
    return _facade.lottie_generator.create_lottie_animation(
        frame_paths,
        fps=fps,
        width=width,
        height=height,
        max_frames=max_frames,
        optimize=optimize
    )
