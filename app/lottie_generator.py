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

def trace_png_to_svg(png_path: str, output_dir: str) -> str:
    """
    Trace a PNG image to SVG using OpenCV contour detection
    
    Args:
        png_path (str): Path to the PNG image
        output_dir (str): Directory to save the SVG file
        
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
        
        # Add each contour as a path
        for contour in contours:
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
        
        logger.info(f"Traced PNG to SVG using OpenCV: {svg_path}")
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
    width: int = settings.DEFAULT_WIDTH,
    height: int = settings.DEFAULT_HEIGHT,
    fps: int = settings.DEFAULT_FPS
) -> Dict[str, Any]:
    """
    Create a Lottie animation from frame paths
    
    Args:
        frame_paths (List[List[Dict[str, Any]]]): List of paths for each frame
        width (int): Animation width
        height (int): Animation height
        fps (int): Animation frames per second
        
    Returns:
        Dict[str, Any]: Lottie animation JSON
    """
    try:
        # Calculate animation duration
        frame_count = len(frame_paths)
        duration_frames = frame_count
        duration_seconds = frame_count / fps
        
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
            
            # Add shapes to layer
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
        
        logger.info(f"Created Lottie animation with {frame_count} frames")
        return lottie_json
        
    except Exception as e:
        logger.error(f"Error creating Lottie animation: {str(e)}")
        raise

def save_lottie_json(lottie_json: Dict[str, Any], output_path: str) -> str:
    """
    Save Lottie JSON to file
    
    Args:
        lottie_json (Dict[str, Any]): Lottie animation JSON
        output_path (str): Path to save the JSON file
        
    Returns:
        str: Path to the saved JSON file
    """
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Write JSON to file
        with open(output_path, 'w') as f:
            json.dump(lottie_json, f)
        
        logger.info(f"Saved Lottie JSON to {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error saving Lottie JSON: {str(e)}")
        raise
