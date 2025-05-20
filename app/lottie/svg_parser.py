import logging
from typing import List, Dict, Any
from app.lottie.interfaces import ISVGParser
from app.models.svg_parsing_params import SVGParsingParams, SVGParsingStrategy
from app.infrastructure.svg_parsing.svg_parser import SVGParserProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SVGElementsParser(ISVGParser):
    """
    Implementation of ISVGParser using the Strategy pattern
    """
    
    def __init__(self):
        self._parser_processor = SVGParserProcessor()
    
    def parse_svg_to_paths(self, svg_path: str) -> List[Dict[str, Any]]:
        """
        Parse SVG file and extract paths in Lottie-compatible format
        
        Args:
            svg_path (str): Path to the SVG file
            
        Returns:
            List[Dict[str, Any]]: List of paths in Lottie format
        """
        # Create default parameters
        params = SVGParsingParams(
            svg_path=svg_path,
            strategy=SVGParsingStrategy.STANDARD,
            error_handling="raise"
        )
        
        # Use the processor to parse the SVG
        return self._parser_processor.parse_svg_to_paths(svg_path, params)
    
    def parse_svg_paths_to_lottie_format(self, svg_paths: List[str]) -> List[List[Dict[str, Any]]]:
        """
        Parse multiple SVG files and extract paths in Lottie-compatible format
        
        Args:
            svg_paths (List[str]): List of paths to SVG files
            
        Returns:
            List[List[Dict[str, Any]]]: List of frames, each containing a list of paths in Lottie format
        """
        # Create default parameters
        params = SVGParsingParams(
            svg_path="",  # Will be updated for each SVG path
            strategy=SVGParsingStrategy.STANDARD,
            error_handling="raise"
        )
        
        # Use the processor to parse the SVG paths
        return self._parser_processor.parse_svg_paths_to_lottie_format(svg_paths, params)
