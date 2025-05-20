import logging
from typing import List, Dict, Any, Optional
from svgelements import SVG, Path as SVGPath

from app.domain.interfaces.svg_parsing import (
    ISVGPathParsingStrategy,
    ISVGElementFilter,
    ILottiePathBuilder
)
from app.infrastructure.svg_parsing.base_strategies import (
    BaseSegmentProcessor,
    BaseSVGElementFilter,
    BaseLottiePathBuilder,
    BaseSVGPathParsingStrategy
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StandardSegmentProcessor(BaseSegmentProcessor):
    """
    Standard implementation of segment processor
    """
    pass  # Uses base implementation


class OptimizedSegmentProcessor(BaseSegmentProcessor):
    """
    Optimized implementation of segment processor with path simplification
    """
    def __init__(self, simplify_tolerance: float = 0.1):
        self.simplify_tolerance = simplify_tolerance
    
    def process_segment(self, segment, current_point, vertices, in_tangents, out_tangents):
        """
        Process a path segment with optimization
        """
        # First use the base implementation
        vertices, in_tangents, out_tangents, current_point = super().process_segment(
            segment, current_point, vertices, in_tangents, out_tangents
        )
        
        # Apply simplification if needed
        if self.simplify_tolerance > 0 and len(vertices) > 2:
            # Simple distance-based simplification
            # Only keep points that are at least tolerance distance apart
            simplified_vertices = [vertices[0]]
            simplified_in_tangents = [in_tangents[0]]
            simplified_out_tangents = [out_tangents[0]]
            
            last_kept = 0
            for i in range(1, len(vertices)):
                # Calculate distance between points
                last_x, last_y = vertices[last_kept]
                curr_x, curr_y = vertices[i]
                distance = ((curr_x - last_x) ** 2 + (curr_y - last_y) ** 2) ** 0.5
                
                if distance >= self.simplify_tolerance:
                    simplified_vertices.append(vertices[i])
                    simplified_in_tangents.append(in_tangents[i])
                    simplified_out_tangents.append(out_tangents[i])
                    last_kept = i
            
            # Always keep the last point
            if last_kept < len(vertices) - 1:
                simplified_vertices.append(vertices[-1])
                simplified_in_tangents.append(in_tangents[-1])
                simplified_out_tangents.append(out_tangents[-1])
            
            return simplified_vertices, simplified_in_tangents, simplified_out_tangents, current_point
        
        return vertices, in_tangents, out_tangents, current_point


class SimplifiedSegmentProcessor(BaseSegmentProcessor):
    """
    Simplified segment processor that converts all curves to lines for better performance
    """
    def process_segment(self, segment, current_point, vertices, in_tangents, out_tangents):
        """
        Process a path segment with simplification (convert curves to lines)
        """
        segment_type = segment.__class__.__name__
        
        if segment_type == "Move":
            return self._process_move_segment(segment, vertices, in_tangents, out_tangents)
        elif segment_type == "Line":
            return self._process_line_segment(segment, vertices, in_tangents, out_tangents)
        elif segment_type == "CubicBezier":
            # Convert cubic bezier to line for simplification
            return self._process_line_segment(segment, vertices, in_tangents, out_tangents)
        elif segment_type == "Close" and vertices:
            return vertices, in_tangents, out_tangents, current_point
        
        return vertices, in_tangents, out_tangents, current_point


class StandardSVGElementFilter(BaseSVGElementFilter):
    """
    Standard implementation of SVG element filter
    """
    pass  # Uses base implementation


class AdvancedSVGElementFilter(BaseSVGElementFilter):
    """
    Advanced implementation of SVG element filter that can filter by attributes
    """
    def __init__(self, include_groups: bool = False, include_hidden: bool = False):
        self.include_groups = include_groups
        self.include_hidden = include_hidden
    
    def should_process(self, element) -> bool:
        """
        Determine if an SVG element should be processed with advanced filtering
        """
        # First check if it's a path
        is_path = super().should_process(element)
        
        if not is_path:
            # If it's not a path but we want to include groups, check if it's a group
            if self.include_groups and hasattr(element, "__class__") and element.__class__.__name__ == "Group":
                return True
            return False
        
        # Check visibility
        if not self.include_hidden:
            # Check if the element has a style attribute with display:none or visibility:hidden
            if hasattr(element, "values") and isinstance(element.values, dict):
                style = element.values.get("style", "")
                if "display:none" in style or "visibility:hidden" in style:
                    return False
        
        return True


class StandardLottiePathBuilder(BaseLottiePathBuilder):
    """
    Standard implementation of Lottie path builder
    """
    pass  # Uses base implementation


class EnhancedLottiePathBuilder(BaseLottiePathBuilder):
    """
    Enhanced implementation of Lottie path builder that includes additional properties
    """
    def build_lottie_path(self, vertices: List, in_tangents: List, out_tangents: List, closed: bool) -> Dict[str, Any]:
        """
        Build an enhanced Lottie path object with additional properties
        """
        # Get the base Lottie path
        lottie_path = super().build_lottie_path(vertices, in_tangents, out_tangents, closed)
        
        # Add additional properties
        lottie_path["nm"] = "Path"  # Name
        lottie_path["hd"] = False  # Hidden
        
        return lottie_path


class StandardSVGPathParsingStrategy(BaseSVGPathParsingStrategy):
    """
    Standard implementation of SVG path parsing strategy
    """
    def __init__(self):
        super().__init__(
            segment_processor=StandardSegmentProcessor(),
            path_builder=StandardLottiePathBuilder()
        )


class OptimizedSVGPathParsingStrategy(BaseSVGPathParsingStrategy):
    """
    Optimized implementation of SVG path parsing strategy
    """
    def __init__(self, simplify_tolerance: float = 0.1):
        super().__init__(
            segment_processor=OptimizedSegmentProcessor(simplify_tolerance),
            path_builder=StandardLottiePathBuilder()
        )


class SimplifiedSVGPathParsingStrategy(BaseSVGPathParsingStrategy):
    """
    Simplified implementation of SVG path parsing strategy
    """
    def __init__(self):
        super().__init__(
            segment_processor=SimplifiedSegmentProcessor(),
            path_builder=StandardLottiePathBuilder()
        )


class EnhancedSVGPathParsingStrategy(BaseSVGPathParsingStrategy):
    """
    Enhanced implementation of SVG path parsing strategy with additional properties
    """
    def __init__(self, simplify_tolerance: float = 0.1):
        super().__init__(
            segment_processor=OptimizedSegmentProcessor(simplify_tolerance),
            path_builder=EnhancedLottiePathBuilder()
        )


class FallbackSVGPathParsingStrategy(BaseSVGPathParsingStrategy):
    """
    Fallback implementation of SVG path parsing strategy for handling problematic SVGs
    """
    def __init__(self):
        super().__init__(
            segment_processor=SimplifiedSegmentProcessor(),
            path_builder=StandardLottiePathBuilder()
        )
    
    def parse_path_element(self, element) -> Optional[Dict[str, Any]]:
        """
        Parse an SVG path element with robust error handling
        """
        try:
            return super().parse_path_element(element)
        except Exception as e:
            logger.warning(f"Error in primary parsing strategy, using fallback: {str(e)}")
            try:
                # Fallback to a very simple representation
                # Just extract start and end points to create a simple line
                if hasattr(element, "first_point") and hasattr(element, "current_point"):
                    vertices = [
                        [element.first_point.x, element.first_point.y],
                        [element.current_point.x, element.current_point.y]
                    ]
                    in_tangents = [[0, 0], [0, 0]]
                    out_tangents = [[0, 0], [0, 0]]
                    closed = False
                    
                    return self.path_builder.build_lottie_path(vertices, in_tangents, out_tangents, closed)
                return None
            except Exception as e2:
                logger.error(f"Fallback parsing also failed: {str(e2)}")
                return None
