import logging
from typing import List, Dict, Any
from svgelements import SVG, Path as SVGPath
from app.lottie.interfaces import ISVGParser

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SVGElementsParser(ISVGParser):
    """
    Implementation of ISVGParser using svgelements library
    """
    
    def parse_svg_to_paths(self, svg_path: str) -> List[Dict[str, Any]]:
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
    
    def parse_svg_paths_to_lottie_format(self, svg_paths: List[str]) -> List[List[Dict[str, Any]]]:
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
            paths = self.parse_svg_to_paths(svg_path)
            frame_paths.append(paths)
        
        return frame_paths
