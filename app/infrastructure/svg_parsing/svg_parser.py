import logging
from typing import List, Dict, Any, Optional
from svgelements import SVG

from app.domain.interfaces.svg_parsing import ISVGParser, ISVGElementFilter
from app.models.svg_parsing_params import SVGParsingParams, SVGParsingStrategy
from app.infrastructure.svg_parsing.parsing_strategies import (
    StandardSVGPathParsingStrategy,
    OptimizedSVGPathParsingStrategy,
    SimplifiedSVGPathParsingStrategy,
    EnhancedSVGPathParsingStrategy,
    FallbackSVGPathParsingStrategy,
    StandardSVGElementFilter,
    AdvancedSVGElementFilter
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SVGParserProcessor(ISVGParser):
    """
    Implementation of ISVGParser using the Strategy pattern
    """
    def __init__(self):
        self._strategies = {
            SVGParsingStrategy.STANDARD: StandardSVGPathParsingStrategy(),
            SVGParsingStrategy.OPTIMIZED: OptimizedSVGPathParsingStrategy(),
            SVGParsingStrategy.SIMPLIFIED: SimplifiedSVGPathParsingStrategy(),
            SVGParsingStrategy.FALLBACK: FallbackSVGPathParsingStrategy()
        }
        self._element_filter = StandardSVGElementFilter()
    
    def _get_strategy(self, strategy_type: SVGParsingStrategy):
        """
        Get the appropriate strategy based on the strategy type
        """
        if strategy_type not in self._strategies:
            logger.warning(f"Strategy {strategy_type} not found, using STANDARD")
            return self._strategies[SVGParsingStrategy.STANDARD]
        return self._strategies[strategy_type]
    
    def _get_element_filter(self, params: SVGParsingParams) -> ISVGElementFilter:
        """
        Get the appropriate element filter based on the parameters
        """
        if params.strategy == SVGParsingStrategy.OPTIMIZED:
            return AdvancedSVGElementFilter(include_groups=False, include_hidden=False)
        return self._element_filter
    
    def parse_svg_to_paths(self, svg_path: str, params: Optional[SVGParsingParams] = None) -> List[Dict[str, Any]]:
        """
        Parse SVG file and extract paths in Lottie-compatible format using the Strategy pattern
        
        Args:
            svg_path: Path to the SVG file
            params: Optional parameters for parsing
            
        Returns:
            List of paths in Lottie format
        """
        # If no params are provided, create default params
        if params is None:
            params = SVGParsingParams(svg_path=svg_path)
        
        # Get the appropriate strategy and element filter
        strategy = self._get_strategy(params.strategy)
        element_filter = self._get_element_filter(params)
        
        try:
            # Parse SVG file
            svg = SVG.parse(svg_path)
            
            # Extract paths
            lottie_paths = []
            
            # Process each element
            for element in svg.elements():
                if element_filter.should_process(element):
                    lottie_path = strategy.parse_path_element(element)
                    if lottie_path is not None:
                        lottie_paths.append(lottie_path)
                        
                        # Check if we've reached the maximum number of paths
                        if params.max_paths is not None and len(lottie_paths) >= params.max_paths:
                            logger.info(f"Reached maximum number of paths: {params.max_paths}")
                            break
            
            logger.info(f"Parsed {len(lottie_paths)} paths from SVG using {params.strategy} strategy")
            return lottie_paths
            
        except Exception as e:
            error_message = f"Error parsing SVG to paths: {str(e)}"
            logger.error(error_message)
            
            # Handle errors based on the error_handling parameter
            if params.error_handling == "raise":
                raise
            elif params.error_handling == "log":
                logger.error(error_message)
                return []
            else:  # "ignore"
                return []
    
    def parse_svg_paths_to_lottie_format(self, svg_paths: List[str], params: Optional[SVGParsingParams] = None) -> List[List[Dict[str, Any]]]:
        """
        Parse multiple SVG files and extract paths in Lottie-compatible format
        
        Args:
            svg_paths: List of paths to SVG files
            params: Optional parameters for parsing
            
        Returns:
            List of frames, each containing a list of paths in Lottie format
        """
        frame_paths = []
        
        for svg_path in svg_paths:
            # Create params for this specific SVG if none provided
            current_params = params
            if current_params is None:
                current_params = SVGParsingParams(svg_path=svg_path)
            else:
                # Update the SVG path in the params
                current_params = SVGParsingParams(
                    svg_path=svg_path,
                    strategy=current_params.strategy,
                    simplify_tolerance=current_params.simplify_tolerance,
                    ignore_transforms=current_params.ignore_transforms,
                    extract_colors=current_params.extract_colors,
                    max_paths=current_params.max_paths,
                    error_handling=current_params.error_handling,
                    metadata=current_params.metadata
                )
            
            # Parse SVG file and extract paths
            paths = self.parse_svg_to_paths(svg_path, current_params)
            frame_paths.append(paths)
        
        return frame_paths
