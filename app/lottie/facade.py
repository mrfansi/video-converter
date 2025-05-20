import logging
from typing import List, Optional
from app.lottie.interfaces import IImageProcessor, ISVGParser, ILottieGenerator
from app.lottie.image_processor import OpenCVImageProcessor
from app.lottie.svg_parser import SVGElementsParser
from app.lottie.lottie_generator import LottieGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LottieGeneratorFacade:
    """
    Facade class that provides a simplified API for the Lottie generation process.
    Follows the Facade design pattern to hide the complexity of the subsystems.
    """

    def __init__(
        self,
        image_processor: Optional[IImageProcessor] = None,
        svg_parser: Optional[ISVGParser] = None,
        lottie_generator: Optional[ILottieGenerator] = None,
    ):
        """
        Initialize the facade with optional custom implementations of the components

        Args:
            image_processor: Custom implementation of IImageProcessor
            svg_parser: Custom implementation of ISVGParser
            lottie_generator: Custom implementation of ILottieGenerator
        """
        # Use provided implementations or defaults
        self.image_processor = image_processor or OpenCVImageProcessor()
        self.svg_parser = svg_parser or SVGElementsParser()
        self.lottie_generator = lottie_generator or LottieGenerator()

    def convert_video_frames_to_lottie(
        self,
        png_frames: List[str],
        output_dir: str,
        output_path: str,
        fps: int = 30,
        width: Optional[int] = None,
        height: Optional[int] = None,
        max_frames: int = 100,
        optimize: bool = True,
        simplify_tolerance: float = 1.0,
        compress: bool = True,
    ) -> str:
        """
        Convert a sequence of PNG frames to a Lottie animation

        Args:
            png_frames: List of paths to PNG frame images
            output_dir: Directory to save intermediate SVG files
            output_path: Path to save the final Lottie JSON file
            fps: Frames per second
            width: Width of the animation (optional)
            height: Height of the animation (optional)
            max_frames: Maximum number of frames to include
            optimize: Whether to apply optimizations
            simplify_tolerance: Tolerance for path simplification
            compress: Whether to compress the JSON output

        Returns:
            Path to the saved Lottie JSON file
        """
        try:
            logger.info(f"Converting {len(png_frames)} PNG frames to Lottie animation")

            # Step 1: Trace PNG frames to SVG
            svg_paths = []
            for png_path in png_frames:
                svg_path = self.image_processor.trace_png_to_svg(
                    png_path, output_dir, simplify_tolerance
                )
                svg_paths.append(svg_path)

            # Step 2: Parse SVG paths to Lottie format
            frame_paths = self.svg_parser.parse_svg_paths_to_lottie_format(svg_paths)

            # Step 3: Create Lottie animation
            lottie_json = self.lottie_generator.create_lottie_animation(
                frame_paths,
                fps=fps,
                width=width,
                height=height,
                max_frames=max_frames,
                optimize=optimize,
            )

            # Step 4: Save Lottie JSON to file
            output_file = self.lottie_generator.save_lottie_json(
                lottie_json, output_path, compress=compress
            )

            logger.info(
                f"Successfully converted PNG frames to Lottie animation: {output_file}"
            )
            return output_file

        except Exception as e:
            logger.error(f"Error converting PNG frames to Lottie animation: {str(e)}")
            raise

    def trace_png_to_svg(
        self, png_path: str, output_dir: str, simplify_tolerance: float = 1.0
    ) -> str:
        """
        Trace a PNG image to SVG

        Args:
            png_path: Path to the PNG image
            output_dir: Directory to save the SVG file
            simplify_tolerance: Tolerance for path simplification

        Returns:
            Path to the SVG file
        """
        return self.image_processor.trace_png_to_svg(
            png_path, output_dir, simplify_tolerance
        )

    def create_lottie_from_svgs(
        self,
        svg_paths: List[str],
        output_path: str,
        fps: int = 30,
        width: Optional[int] = None,
        height: Optional[int] = None,
        max_frames: int = 100,
        optimize: bool = True,
        compress: bool = True,
    ) -> str:
        """
        Create a Lottie animation from a list of SVG files

        Args:
            svg_paths: List of paths to SVG files
            output_path: Path to save the Lottie JSON file
            fps: Frames per second
            width: Width of the animation (optional)
            height: Height of the animation (optional)
            max_frames: Maximum number of frames to include
            optimize: Whether to apply optimizations
            compress: Whether to compress the JSON output

        Returns:
            Path to the saved Lottie JSON file
        """
        try:
            # Parse SVG paths to Lottie format
            frame_paths = self.svg_parser.parse_svg_paths_to_lottie_format(svg_paths)

            # Create Lottie animation
            lottie_json = self.lottie_generator.create_lottie_animation(
                frame_paths,
                fps=fps,
                width=width,
                height=height,
                max_frames=max_frames,
                optimize=optimize,
            )

            # Save Lottie JSON to file
            return self.lottie_generator.save_lottie_json(
                lottie_json, output_path, compress
            )

        except Exception as e:
            logger.error(f"Error creating Lottie from SVGs: {str(e)}")
            raise
