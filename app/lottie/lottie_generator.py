import os
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from svgelements import SVG
from app.lottie.interfaces import ILottieGenerator
from app.lottie.json_encoder import LottieJSONEncoder

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

class LottieGenerator(ILottieGenerator):
    """
    Implementation of ILottieGenerator using python-lottie library (if available)
    or falling back to manual JSON generation
    """
    
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
        try:
            # Determine dimensions if not provided
            if width is None or height is None:
                # Use defaults
                width = width or 1920
                height = height or 1080
            
            # Use the manual JSON generation method which is more reliable
            logger.info(f"Creating Lottie animation with {len(frame_paths)} frames, dimensions: {width}x{height}")
            
            # Delegate to the manual generator
            manual_generator = ManualLottieGenerator()
            return manual_generator.create_lottie_animation(
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
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Get file size before compression for logging
            try:
                pre_size = len(json.dumps(lottie_json, cls=LottieJSONEncoder))
            except:
                # If we can't serialize for size calculation, just use a default value
                pre_size = 0
                logger.warning("Could not calculate pre-compression size")
            
            # Apply optimizations to reduce file size if compress is True
            if compress:
                # Remove unnecessary precision from floating point numbers
                lottie_json = self._round_floats(lottie_json)
            
            # Write JSON to file with minimal whitespace if compress is True
            with open(output_path, 'w') as f:
                if compress:
                    json.dump(lottie_json, f, separators=(',', ':'), cls=LottieJSONEncoder)  # Remove whitespace
                else:
                    json.dump(lottie_json, f, indent=2, cls=LottieJSONEncoder)
            
            # Get file size after compression for logging
            post_size = os.path.getsize(output_path)
            
            if compress:
                compression_ratio = (1 - (post_size / pre_size)) * 100 if pre_size > 0 else 0
                logger.info(f"Compressed Lottie JSON from {pre_size} to {post_size} bytes ({compression_ratio:.2f}% reduction)")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error saving Lottie JSON: {str(e)}")
            raise
    
    def _round_floats(self, obj, precision=2):
        """
        Recursively round floating point values in a nested structure to reduce file size
        
        Args:
            obj: Object to process
            precision: Number of decimal places to keep
            
        Returns:
            Processed object with rounded floats
        """
        if isinstance(obj, float):
            return round(obj, precision)
        elif isinstance(obj, dict):
            return {k: self._round_floats(v, precision) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._round_floats(i, precision) for i in obj]
        return obj


class ManualLottieGenerator(ILottieGenerator):
    """
    Implementation of ILottieGenerator using manual JSON construction
    """
    
    def create_lottie_animation(self, 
                               frame_paths: List[List[Dict[str, Any]]], 
                               fps: int = 30,
                               width: Optional[int] = None,
                               height: Optional[int] = None,
                               max_frames: int = 100,
                               optimize: bool = True) -> Dict[str, Any]:
        """
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
        try:
            # Ensure width and height are set
            width = width or 1920
            height = height or 1080
            
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
        # Delegate to the parent class implementation
        generator = LottieGenerator()
        return generator.save_lottie_json(lottie_json, output_path, compress)
