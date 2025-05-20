import os
import json
import logging
import tempfile
from typing import List, Dict, Any, Tuple, Optional
import cv2
import numpy as np
from pathlib import Path
from svgelements import SVG, Path as SVGPath

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import python-lottie library
try:
    import lottie
    from lottie import objects
    from lottie.parsers.svg import parse_svg_file
    from lottie.exporters.core import export_lottie
    from lottie.objects import ShapeElement, Group, Fill, Stroke, Path
    from lottie.objects import easing
    from lottie import NVector
    LOTTIE_AVAILABLE = True
    logger.info("python-lottie library available, using it for Lottie generation")
except ImportError:
    logger.warning("python-lottie library not available, falling back to manual JSON generation")
    LOTTIE_AVAILABLE = False

from app.config import settings


def trace_png_to_svg(png_path: str, output_dir: str, simplify_tolerance: float = 1.0) -> str:
    """
    Trace a PNG image to SVG using OpenCV contour detection with path simplification
    
    Args:
        png_path (str): Path to the PNG image
        output_dir (str): Directory to save the SVG file
        simplify_tolerance (float): Tolerance for path simplification (higher = more simplification)
        
    Returns:
        str: Path to the SVG file
    """
    try:
        # Read image
        img = cv2.imread(png_path, cv2.IMREAD_UNCHANGED)
        if img is None:
            raise ValueError(f"Could not read image: {png_path}")
            
        logger.info(f"Processing image: {png_path} with shape {img.shape}")
        
        # Convert to grayscale if needed
        if len(img.shape) > 2 and img.shape[2] > 1:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img
        
        # Apply adaptive threshold to get better results with varying brightness
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                      cv2.THRESH_BINARY_INV, 11, 2)
        
        # Optional: Apply morphological operations to clean up the image
        kernel = np.ones((3, 3), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        # Find contours - use RETR_TREE to get hierarchical contours
        contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_TC89_KCOS)
        
        logger.info(f"Found {len(contours)} contours")
        
        # Get image dimensions
        height, width = img.shape[:2]
        
        # Create SVG content
        svg_content = f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
        
        # Add paths for each contour
        valid_paths = 0
        for i, contour in enumerate(contours):
            # Skip very small contours (noise)
            area = cv2.contourArea(contour)
            if area < 20:  # Increased minimum area
                continue
                
            # Skip very large contours (background)
            if area > 0.9 * width * height:
                continue
            
            # Simplify contour if requested
            if simplify_tolerance > 0:
                epsilon = simplify_tolerance * cv2.arcLength(contour, True)
                contour = cv2.approxPolyDP(contour, epsilon, True)
            
            # Skip contours with too few points
            if len(contour) < 3:
                continue
                
            # Convert contour to SVG path
            path = "M"
            for i, point in enumerate(contour):
                x, y = point[0]
                if i == 0:
                    path += f"{x},{y}"
                else:
                    path += f" L{x},{y}"
            
            # Close path
            path += " Z"
            
            # Add path to SVG with a unique ID
            svg_content += f'<path d="{path}" fill="black" id="path{i}" />'
            valid_paths += 1
        
        # If no valid paths were found, create a simple rectangle as fallback
        if valid_paths == 0:
            logger.warning(f"No valid contours found in {png_path}, creating fallback shape")
            # Create a simple rectangle in the middle of the image
            rect_width = width // 2
            rect_height = height // 2
            x = (width - rect_width) // 2
            y = (height - rect_height) // 2
            svg_content += f'<rect x="{x}" y="{y}" width="{rect_width}" height="{rect_height}" fill="black" id="fallback" />'
        
        # Close SVG
        svg_content += '</svg>'
        
        # Save SVG file
        os.makedirs(output_dir, exist_ok=True)
        svg_filename = os.path.basename(png_path).replace('.png', '.svg')
        svg_path = os.path.join(output_dir, svg_filename)
        
        with open(svg_path, 'w') as f:
            f.write(svg_content)
        
        logger.info(f"Traced PNG to SVG: {svg_path} with {valid_paths} paths")
        return svg_path
        
    except Exception as e:
        logger.error(f"Error tracing PNG to SVG: {str(e)}")
        raise


def parse_svg_to_paths(svg_path: str) -> List[Dict[str, Any]]:
    """
    Parse SVG file and extract paths in Lottie-compatible format
    
    Args:
        svg_path (str): Path to the SVG file
        
    Returns:
        List[Dict[str, Any]]: List of paths in Lottie format
    """
    try:
        # Parse SVG file
        svg = SVG.parse(svg_path)
        
        # Extract paths
        lottie_paths = []
        
        for element in svg.elements():
            if isinstance(element, SVGPath):
                # Process path to standard Lottie bezier format
                vertices = []
                in_tangents = []
                out_tangents = []
                closed = element.closed
                
                # Process path segments to extract points and tangents
                current_point = None
                for segment in element:
                    segment_type = segment.__class__.__name__
                    
                    if segment_type == "Move":
                        vertices.append([segment.end.x, segment.end.y])
                        in_tangents.append([0, 0])  # No tangents for move
                        out_tangents.append([0, 0])
                        current_point = segment.end
                    elif segment_type == "Line":
                        vertices.append([segment.end.x, segment.end.y])
                        # For lines, tangents are zero vectors
                        in_tangents.append([0, 0])
                        out_tangents.append([0, 0])
                        current_point = segment.end
                    elif segment_type == "CubicBezier":
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
                    elif segment_type == "Close" and vertices:
                        # For closed paths, connect back to the first point
                        # No need to add a new vertex, just set the closed flag
                        closed = True
                
                # Create standard Lottie path object
                lottie_path = {
                    "ty": "sh",  # Type: Shape
                    "ks": {      # Keyframes
                        "a": 0,  # Animated: 0 for no
                        "k": {   # Keyframe value
                            "c": closed,  # Closed path
                            "i": in_tangents,  # In tangents
                            "o": out_tangents,  # Out tangents
                            "v": vertices  # Vertices
                        }
                    }
                }
                
                lottie_paths.append(lottie_path)
        
        logger.info(f"Parsed {len(lottie_paths)} paths from SVG")
        return lottie_paths
        
    except Exception as e:
        logger.error(f"Error parsing SVG to paths: {str(e)}")
        raise


def parse_svg_paths_to_lottie_format(svg_paths: List[str]) -> List[List[Dict[str, Any]]]:
    """
    Parse multiple SVG files and extract paths in Lottie-compatible format
    
    Args:
        svg_paths (List[str]): List of paths to SVG files
        
    Returns:
        List[List[Dict[str, Any]]]: List of frames, each containing a list of paths in Lottie format
    """
    frame_paths = []
    
    for svg_path in svg_paths:
        # Parse SVG file and extract paths
        paths = parse_svg_to_paths(svg_path)
        frame_paths.append(paths)
    
    return frame_paths


def save_lottie_json(lottie_json: Dict[str, Any], output_path: str, compress: bool = True) -> str:
    """
    Save Lottie JSON to file with optional compression
    
    Args:
        lottie_json (Dict[str, Any]): Lottie animation JSON
        output_path (str): Path to save the JSON file
        compress (bool): Whether to compress the JSON output
        
    Returns:
        str: Path to the saved JSON file
    """
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Get file size before compression for logging
        pre_size = len(json.dumps(lottie_json))
        
        # Apply optimizations to reduce file size if compress is True
        if compress:
            # Remove unnecessary precision from floating point numbers
            def round_floats(obj, precision=2):
                if isinstance(obj, float):
                    return round(obj, precision)
                elif isinstance(obj, dict):
                    return {k: round_floats(v, precision) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [round_floats(i, precision) for i in obj]
                return obj
            
            # Apply float rounding to reduce precision and file size
            lottie_json = round_floats(lottie_json)
        
        # Write JSON to file with minimal whitespace if compress is True
        with open(output_path, 'w') as f:
            if compress:
                json.dump(lottie_json, f, separators=(',', ':'))  # Remove whitespace
            else:
                json.dump(lottie_json, f, indent=2)
        
        # Get file size after compression for logging
        post_size = os.path.getsize(output_path)
        
        if compress:
            compression_ratio = (1 - (post_size / pre_size)) * 100 if pre_size > 0 else 0
            logger.info(f"Compressed Lottie JSON from {pre_size} to {post_size} bytes ({compression_ratio:.2f}% reduction)")
        
        return output_path
        
    except Exception as e:
        logger.error(f"Error saving Lottie JSON: {str(e)}")
        raise


def create_lottie_animation(
    svg_paths: List[str],  # List of SVG file paths
    fps: int = 30,
    width: int = None,  # Now optional
    height: int = None,  # Now optional
    max_frames: int = 100,  # Maximum number of frames to include
    optimize: bool = True,  # Whether to apply optimizations
) -> Dict[str, Any]:
    """
    Create a Lottie animation from a list of SVG files
    
    Args:
        svg_paths (List[str]): List of SVG file paths
        fps (int): Frames per second
        width (int): Width of the animation (optional, will use SVG dimensions if not provided)
        height (int): Height of the animation (optional, will use SVG dimensions if not provided)
        max_frames (int): Maximum number of frames to include
        optimize (bool): Whether to apply optimizations
        
    Returns:
        Dict[str, Any]: Lottie animation JSON
    """
    try:
        # Parse SVG paths to Lottie format
        frame_paths = parse_svg_paths_to_lottie_format(svg_paths)
        
        # Determine dimensions from SVG if not provided
        if width is None or height is None:
            try:
                # Try to get dimensions from first SVG
                first_svg = SVG.parse(svg_paths[0])
                width = width or int(first_svg.width)
                height = height or int(first_svg.height)
            except Exception as e:
                logger.warning(f"Could not get dimensions from SVG: {str(e)}")
                # Use defaults if SVG doesn't specify dimensions
                width = width or 1920
                height = height or 1080
        
        # Use the manual JSON generation method which is more reliable
        logger.info(f"Creating Lottie animation with {len(svg_paths)} frames, dimensions: {width}x{height}")
        return create_lottie_animation_manual(
            frame_paths,
            fps=fps,
            width=width,
            height=height,
            max_frames=max_frames,
            optimize=optimize
        )
    except Exception as e:
        logger.error(f"Error creating Lottie animation: {str(e)}")
        raise


def create_lottie_animation_manual(
    frame_paths: List[List[Dict[str, Any]]],
    fps: int = 30,
    width: int = 1920,
    height: int = 1080,
    max_frames: int = 100,
    optimize: bool = True,
) -> Dict[str, Any]:
    """
    Create a Lottie animation from parsed SVG paths manually (fallback method)
    
    Args:
        frame_paths (List[List[Dict[str, Any]]]): List of frames, each containing a list of paths
        fps (int): Frames per second
        width (int): Width of the animation
        height (int): Height of the animation
        max_frames (int): Maximum number of frames to include
        optimize (bool): Whether to apply optimizations
        
    Returns:
        Dict[str, Any]: Lottie animation JSON
    """
    try:
        # Sample frames if needed to reduce size
        original_frame_count = len(frame_paths)
        sampled_frame_paths = frame_paths
        
        if original_frame_count > max_frames and optimize:
            # Calculate sampling interval to maintain animation duration
            sample_interval = original_frame_count / max_frames
            sampled_indices = [int(i * sample_interval) for i in range(max_frames)]
            # Ensure last frame is included
            if original_frame_count - 1 not in sampled_indices:
                sampled_indices[-1] = original_frame_count - 1
            sampled_frame_paths = [frame_paths[i] for i in sampled_indices]
            logger.info(f"Sampled {len(sampled_frame_paths)} frames from {original_frame_count} original frames")
        
        # Create base Lottie JSON structure
        lottie_json = {
            "v": "5.7.1",  # Lottie version
            "fr": fps,
            "ip": 0,
            "op": len(sampled_frame_paths),
            "w": width,
            "h": height,
            "nm": "Video Animation",
            "ddd": 0,  # 3D flag (0 = 2D)
            "assets": [],
            "layers": [],
            "markers": []
        }
        
        # Create a shape layer for each frame
        for i, paths in enumerate(sampled_frame_paths):
            # Create a layer for this frame
            layer = {
                "ty": 4,  # Shape layer
                "nm": f"Frame {i}",
                "sr": 1,  # Time stretch
                "ks": {  # Transform properties
                    "o": {"a": 0, "k": 100},  # Opacity
                    "r": {"a": 0, "k": 0},  # Rotation
                    "p": {"a": 0, "k": [width/2, height/2]},  # Position
                    "a": {"a": 0, "k": [0, 0]},  # Anchor point
                    "s": {"a": 0, "k": [100, 100]}  # Scale
                },
                "ao": 0,  # Auto-Orient
                "shapes": [],
                "ip": i,  # In point (frame number)
                "op": i + 1,  # Out point (next frame)
                "st": 0,  # Start time
                "bm": 0  # Blend mode
            }
            
            # Add shapes to the layer
            for path in paths:
                # Create a group for each path
                shape_group = {
                    "ty": "gr",  # Group
                    "it": [
                        path,  # The path shape
                        {
                            "ty": "fl",  # Fill
                            "c": {"a": 0, "k": [0, 0, 0, 1]},  # Color (black)
                            "o": {"a": 0, "k": 100}  # Opacity
                        },
                        {
                            "ty": "tr",  # Transform
                            "p": {"a": 0, "k": [0, 0]},  # Position
                            "a": {"a": 0, "k": [0, 0]},  # Anchor point
                            "s": {"a": 0, "k": [100, 100]},  # Scale
                            "r": {"a": 0, "k": 0},  # Rotation
                            "o": {"a": 0, "k": 100},  # Opacity
                            "sk": {"a": 0, "k": 0},  # Skew
                            "sa": {"a": 0, "k": 0}  # Skew axis
                        }
                    ],
                    "nm": "Shape Group"
                }
                
                # Add shape group to layer
                layer["shapes"].append(shape_group)
            
            # Add layer to animation
            lottie_json["layers"].append(layer)
        
        logger.info(f"Created Lottie animation manually with {len(sampled_frame_paths)} frames")
        return lottie_json
        
    except Exception as e:
        logger.error(f"Error creating Lottie animation manually: {str(e)}")
        raise
