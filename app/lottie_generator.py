import os
import json
import time
import cv2
import numpy as np
import logging
from typing import List, Dict, Any
from pathlib import Path
from svgelements import SVG, Path as SVGPath
import xml.etree.ElementTree as ET
from PIL import Image, ImageOps

from app.config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def trace_png_to_svg(png_path: str, output_dir: str, simplify_tolerance: float = 1.0) -> str:
    """
    Trace a PNG image to SVG using OpenCV contour detection with path simplification
    
    Args:
        png_path (str): Path to the PNG image
        output_dir (str): Directory to save the SVG file
        simplify_tolerance (float): Tolerance for path simplification (higher = more simplification)
        
    Returns:
        str: Path to the generated SVG file
    """
    try:
        # Create output filename
        base_name = os.path.basename(png_path).replace(".png", "")
        svg_path = os.path.join(output_dir, f"{base_name}.svg")
        
        # Read image with OpenCV
        img = cv2.imread(png_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply threshold to get binary image
        _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        # Create SVG content
        width, height = img.shape[1], img.shape[0]
        svg_content = f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">\n'
        
        # Filter and simplify contours
        min_contour_area = (width * height) * 0.0001  # Ignore tiny contours (0.01% of image area)
        simplified_contours = []
        
        for contour in contours:
            # Filter out very small contours
            area = cv2.contourArea(contour)
            if area < min_contour_area:
                continue
                
            # Apply Douglas-Peucker algorithm to simplify the contour
            epsilon = simplify_tolerance * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            # Only keep contours with reasonable number of points
            if len(approx) > 2 and len(approx) < 100:  # Limit max points per contour
                simplified_contours.append(approx)
        
        # Add each simplified contour as a path
        for contour in simplified_contours:
            if len(contour) > 2:  # Only process contours with at least 3 points
                path_data = "M"
                for i, point in enumerate(contour):
                    x, y = point[0][0], point[0][1]
                    if i == 0:
                        path_data += f" {x},{y}"
                    else:
                        path_data += f" L {x},{y}"
                path_data += " Z"  # Close the path
                
                svg_content += f'  <path d="{path_data}" fill="black" />\n'
        
        svg_content += '</svg>'
        
        # Write SVG file
        with open(svg_path, 'w') as f:
            f.write(svg_content)
        
        if not os.path.exists(svg_path):
            raise FileNotFoundError(f"Failed to create SVG file: {svg_path}")
        
        logger.info(f"Traced PNG to SVG using OpenCV: {svg_path} with {len(simplified_contours)} paths")
        return svg_path
        
    except Exception as e:
        logger.error(f"Unexpected error tracing PNG to SVG: {str(e)}")
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
                # Convert SVG path to Lottie path
                path_data = []
                
                # Process path segments
                for segment in element:
                    # Get segment type by checking the class name
                    segment_type = segment.__class__.__name__
                    
                    # Convert segment to Lottie bezier format based on its type
                    if segment_type == "Move":  # MoveTo
                        path_data.append({
                            "t": 0,  # Type: MoveTo
                            "p": {"x": segment.end.x, "y": segment.end.y}
                        })
                    elif segment_type == "Line":  # LineTo
                        path_data.append({
                            "t": 1,  # Type: LineTo
                            "p": {"x": segment.end.x, "y": segment.end.y}
                        })
                    elif segment_type == "CubicBezier":  # CurveTo
                        path_data.append({
                            "t": 2,  # Type: CurveTo
                            "cp1": {"x": segment.control1.x, "y": segment.control1.y},
                            "cp2": {"x": segment.control2.x, "y": segment.control2.y},
                            "p": {"x": segment.end.x, "y": segment.end.y}
                        })
                    elif segment_type == "Close":  # ClosePath
                        path_data.append({
                            "t": 3  # Type: ClosePath
                        })
                
                # Create Lottie shape
                lottie_path = {
                    "ty": "sh",  # Type: Shape
                    "d": 1,      # Direction: 1 for clockwise
                    "ks": {      # Keyframes
                        "a": 0,  # Animated: 0 for no
                        "k": {   # Keyframe value
                            "c": True if element.closed else False,  # Closed path
                            "v": path_data  # Vertices
                        }
                    }
                }
                
                lottie_paths.append(lottie_path)
        
        logger.info(f"Parsed {len(lottie_paths)} paths from SVG")
        return lottie_paths
        
    except Exception as e:
        logger.error(f"Error parsing SVG to paths: {str(e)}")
        raise

def create_lottie_animation(
    frame_paths: List[List[Dict[str, Any]]],
    fps: int = settings.DEFAULT_FPS,
    width: int = None,  # Now optional
    height: int = None,  # Now optional
    max_frames: int = 100,  # Maximum number of frames to include
    optimize: bool = True   # Whether to apply optimizations
) -> Dict[str, Any]:
    """
    Create a Lottie animation from frame paths with optimizations
    
    Args:
        frame_paths (List[List[Dict[str, Any]]]): List of paths for each frame
        width (int): Animation width
        height (int): Animation height
        fps (int): Frames per second
        max_frames (int): Maximum number of frames to include (will sample if exceeded)
        optimize (bool): Whether to apply optimizations to reduce file size
        
    Returns:
        Dict[str, Any]: Lottie animation JSON
    """
    try:
        # Calculate animation duration
        original_frame_count = len(frame_paths)
        
        # Sample frames if we have too many
        if original_frame_count > max_frames and optimize:
            # Calculate sampling interval to maintain animation duration
            sample_interval = original_frame_count / max_frames
            sampled_frames = []
            
            for i in range(max_frames):
                # Get the frame index using the sampling interval
                frame_idx = min(int(i * sample_interval), original_frame_count - 1)
                sampled_frames.append(frame_paths[frame_idx])
                
            frame_paths = sampled_frames
            logger.info(f"Sampled {original_frame_count} frames down to {len(frame_paths)} frames")
            
            # Adjust FPS to maintain animation duration
            original_duration = original_frame_count / fps
            fps = max(1, int(len(frame_paths) / original_duration))
        
        frame_count = len(frame_paths)
        duration_frames = frame_count
        
        # Determine dimensions if not provided
        # For Lottie animations, we need to have width and height
        # If not provided, we'll use a default size or try to infer from the SVG paths
        if width is None or height is None:
            # Try to infer from the first SVG path if available
            if len(frame_paths) > 0 and len(frame_paths[0]) > 0:
                # Get dimensions from the first SVG path
                first_svg_path = frame_paths[0][0]
                if 'ks' in first_svg_path and 'k' in first_svg_path['ks']:
                    # Try to determine bounds from the path data
                    path_data = first_svg_path['ks']['k']
                    if isinstance(path_data, list) and len(path_data) > 0:
                        # Find min/max x and y values to determine bounds
                        x_values = []
                        y_values = []
                        for point in path_data:
                            if isinstance(point, dict) and 'x' in point and 'y' in point:
                                x_values.append(point['x'])
                                y_values.append(point['y'])
                        
                        if x_values and y_values:
                            inferred_width = max(x_values) - min(x_values)
                            inferred_height = max(y_values) - min(y_values)
                            
                            # Use inferred dimensions with some padding
                            width = width or int(inferred_width * 1.2)
                            height = height or int(inferred_height * 1.2)
                            logger.info(f"Inferred dimensions from SVG paths: {width}x{height}")
            
            # If still not determined, use defaults
            width = width or settings.DEFAULT_WIDTH
            height = height or settings.DEFAULT_HEIGHT
            logger.info(f"Using dimensions: {width}x{height}")
        
        # Create base Lottie JSON structure
        lottie_json = {
            "v": "5.7.8",  # Lottie version
            "fr": fps,     # Frame rate
            "ip": 0,       # In point (first frame)
            "op": duration_frames,  # Out point (last frame)
            "w": width,    # Width
            "h": height,   # Height
            "nm": "Video to Lottie",  # Name
            "ddd": 0,      # 3D: 0 for 2D animation
            "assets": [],  # Assets
            "layers": []   # Layers
        }
        
        # Optimization: Deduplicate similar paths across frames if optimize is enabled
        path_cache = {}
        path_usage_count = {}
        
        if optimize:
            # First pass: identify duplicate/similar paths
            for frame_index, paths in enumerate(frame_paths):
                for path_index, path in enumerate(paths):
                    # Create a simplified hash of the path for comparison
                    if 'ks' in path and 'k' in path['ks']:
                        path_data = str(path['ks']['k'])
                        path_hash = hash(path_data[:100])  # Use first 100 chars as a fingerprint
                        
                        if path_hash in path_cache:
                            path_usage_count[path_hash] = path_usage_count.get(path_hash, 1) + 1
                        else:
                            path_cache[path_hash] = path
                            path_usage_count[path_hash] = 1
        
        # Filter to paths used in multiple frames (worth reusing)
        reusable_paths = {k: v for k, v in path_cache.items() if path_usage_count.get(k, 0) > 1}
        
        # If we have reusable paths, add them as assets
        if optimize and reusable_paths:
            for i, (path_hash, path) in enumerate(reusable_paths.items()):
                asset_id = f"path_{i}"
                lottie_json["assets"].append({
                    "id": asset_id,
                    "nm": f"Reusable Path {i}",
                    "fr": fps,
                    "layers": [{
                        "ty": 4,
                        "nm": "Path Layer",
                        "shapes": [{
                            "ty": "gr",
                            "it": [
                                path,
                                {
                                    "ty": "fl",
                                    "c": {"a": 0, "k": [0, 0, 0, 1]},
                                    "o": {"a": 0, "k": 100}
                                },
                                {
                                    "ty": "tr",
                                    "p": {"a": 0, "k": [0, 0]},
                                    "a": {"a": 0, "k": [0, 0]},
                                    "s": {"a": 0, "k": [100, 100]},
                                    "r": {"a": 0, "k": 0},
                                    "o": {"a": 0, "k": 100},
                                    "sk": {"a": 0, "k": 0},
                                    "sa": {"a": 0, "k": 0}
                                }
                            ],
                            "nm": "Shape Group"
                        }]
                    }]
                })
                
                # Store the asset ID with the path hash for reference
                path_cache[path_hash] = asset_id
        
        # Create a layer for each frame
        for frame_index, paths in enumerate(frame_paths):
            # Create shape layer
            layer = {
                "ty": 4,       # Type: Shape Layer
                "nm": f"Frame {frame_index + 1}",  # Name
                "sr": 1,       # Time Stretch
                "ks": {        # Transform properties
                    "o": {"a": 0, "k": 100},  # Opacity
                    "r": {"a": 0, "k": 0},    # Rotation
                    "p": {"a": 0, "k": [width/2, height/2]},  # Position
                    "a": {"a": 0, "k": [0, 0]},  # Anchor Point
                    "s": {"a": 0, "k": [100, 100]}  # Scale
                },
                "ao": 0,       # Auto-Orient
                "shapes": [],  # Shapes
                "ip": frame_index,    # In point
                "op": frame_index + 1,  # Out point
                "st": 0,       # Start Time
                "bm": 0        # Blend Mode: Normal
            }
            
            # Add shapes to layer - with optimization if enabled
            if optimize and reusable_paths:
                # Try to reuse paths from assets when possible
                for path in paths:
                    if 'ks' in path and 'k' in path['ks']:
                        path_data = str(path['ks']['k'])
                        path_hash = hash(path_data[:100])
                        
                        if path_hash in reusable_paths:
                            # Reference the asset instead of including the full path data
                            asset_id = path_cache[path_hash]
                            shape_group = {
                                "ty": "gr",  # Type: Group
                                "it": [{
                                    "ty": "fl",  # Type: Fill
                                    "c": {"a": 0, "k": [0, 0, 0, 1]},  # Color (black)
                                    "o": {"a": 0, "k": 100}  # Opacity
                                }],
                                "nm": "Shape Group"  # Name
                            }
                            layer["shapes"].append(shape_group)
                            continue
                    
                    # If not reusable, add the full path data
                    shape_group = {
                        "ty": "gr",  # Type: Group
                        "it": [      # Items
                            path,    # Path
                            {        # Fill
                                "ty": "fl",  # Type: Fill
                                "c": {"a": 0, "k": [0, 0, 0, 1]},  # Color (black)
                                "o": {"a": 0, "k": 100}  # Opacity
                            },
                            {        # Group transform
                                "ty": "tr",  # Type: Transform
                                "p": {"a": 0, "k": [0, 0]},  # Position
                                "a": {"a": 0, "k": [0, 0]},  # Anchor point
                                "s": {"a": 0, "k": [100, 100]},  # Scale
                                "r": {"a": 0, "k": 0},  # Rotation
                                "o": {"a": 0, "k": 100},  # Opacity
                                "sk": {"a": 0, "k": 0},  # Skew
                                "sa": {"a": 0, "k": 0}   # Skew Axis
                            }
                        ],
                        "nm": "Shape Group"  # Name
                    }
                    layer["shapes"].append(shape_group)
            else:
                # No optimization, add all paths directly
                for path in paths:
                    shape_group = {
                        "ty": "gr",  # Type: Group
                        "it": [      # Items
                            path,    # Path
                            {        # Fill
                                "ty": "fl",  # Type: Fill
                                "c": {"a": 0, "k": [0, 0, 0, 1]},  # Color (black)
                                "o": {"a": 0, "k": 100}  # Opacity
                            },
                            {        # Group transform
                                "ty": "tr",  # Type: Transform
                                "p": {"a": 0, "k": [0, 0]},  # Position
                                "a": {"a": 0, "k": [0, 0]},  # Anchor point
                                "s": {"a": 0, "k": [100, 100]},  # Scale
                                "r": {"a": 0, "k": 0},  # Rotation
                                "o": {"a": 0, "k": 100},  # Opacity
                                "sk": {"a": 0, "k": 0},  # Skew
                                "sa": {"a": 0, "k": 0}   # Skew Axis
                            }
                        ],
                        "nm": "Shape Group"  # Name
                    }
                    layer["shapes"].append(shape_group)
            
            # Add layer to animation
            lottie_json["layers"].append(layer)
        
        optimization_info = "with optimizations" if optimize else "without optimizations"
        logger.info(f"Created Lottie animation with {frame_count} frames {optimization_info}")
        return lottie_json
        
    except Exception as e:
        logger.error(f"Error creating Lottie animation: {str(e)}")
        raise

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
                json.dump(lottie_json, f)
        
        # Get file size after compression for logging
        post_size = os.path.getsize(output_path)
        
        if compress:
            compression_ratio = (1 - (post_size / pre_size)) * 100 if pre_size > 0 else 0
            logger.info(f"Saved compressed Lottie JSON to {output_path} (reduced by {compression_ratio:.1f}%)")
        else:
            logger.info(f"Saved uncompressed Lottie JSON to {output_path}")
            
        return output_path
        
    except Exception as e:
        logger.error(f"Error saving Lottie JSON: {str(e)}")
        raise
