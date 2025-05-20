"""Component strategies for video processing.

This module provides concrete implementations for video processing component strategies
following the Strategy pattern for improved maintainability and extensibility.
"""

import os
import cv2
import time
import logging
import subprocess
from typing import Dict, Any, Optional, List, Callable, Tuple

from app.domain.interfaces.video_processing import (
    IFrameProcessor,
    ILottieGenerator,
    IThumbnailGenerator,
    ICloudUploader
)
from app.infrastructure.video_processing.base_strategies import (
    BaseFrameProcessor,
    BaseLottieGenerator,
    BaseThumbnailGenerator,
    BaseCloudUploader
)

logger = logging.getLogger(__name__)


class StandardFrameProcessor(BaseFrameProcessor):
    """Standard frame processor strategy.
    
    This strategy processes video frames into SVG files using a balanced approach
    with good quality and reasonable processing time.
    """
    
    def process_frames(self, frame_paths: List[str], output_dir: str,
                      progress_callback: Optional[Callable] = None) -> List[str]:
        """Process video frames into SVG files.
        
        Args:
            frame_paths (List[str]): Paths to the video frames
            output_dir (str): Directory to save the SVG files
            progress_callback (Optional[Callable]): Callback function for progress updates
            
        Returns:
            List[str]: Paths to the generated SVG files
            
        Raises:
            ValueError: If the input files are invalid or the processing fails
        """
        try:
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Import here to avoid circular imports
            from app.lottie.image_processor_refactored import RefactoredImageProcessor
            from app.models.lottie_params import ImageTracingParamBuilder, ImageTracingStrategy
            
            svg_paths = []
            total_frames = len(frame_paths)
            
            for i, frame_path in enumerate(frame_paths):
                # Update progress
                if progress_callback:
                    progress = int((i / total_frames) * 100)
                    progress_callback(progress, f"Processing frame {i+1}/{total_frames}")
                
                # Generate output path
                frame_name = os.path.splitext(os.path.basename(frame_path))[0]
                svg_path = os.path.join(output_dir, f"{frame_name}.svg")
                
                # Trace PNG to SVG
                params = ImageTracingParamBuilder()\
                    .with_input_path(frame_path)\
                    .with_output_path(svg_path)\
                    .with_strategy(ImageTracingStrategy.STANDARD)\
                    .with_simplify_tolerance(1.0)\
                    .with_color_mode("colored")\
                    .with_embed_image(False)\
                    .build()
                
                processor = RefactoredImageProcessor()
                svg_path = processor.trace_png_to_svg(params)
                
                svg_paths.append(svg_path)
            
            # Update final progress
            if progress_callback:
                progress_callback(100, f"Processed {len(svg_paths)} frames to SVG")
                
            return svg_paths
            
        except Exception as e:
            logger.error(f"Error processing frames: {str(e)}")
            raise ValueError(f"Failed to process frames: {str(e)}")


class HighQualityFrameProcessor(BaseFrameProcessor):
    """High quality frame processor strategy.
    
    This strategy processes video frames into SVG files with higher quality
    but longer processing time.
    """
    
    def process_frames(self, frame_paths: List[str], output_dir: str,
                      progress_callback: Optional[Callable] = None) -> List[str]:
        """Process video frames into SVG files with high quality.
        
        Args:
            frame_paths (List[str]): Paths to the video frames
            output_dir (str): Directory to save the SVG files
            progress_callback (Optional[Callable]): Callback function for progress updates
            
        Returns:
            List[str]: Paths to the generated SVG files
            
        Raises:
            ValueError: If the input files are invalid or the processing fails
        """
        try:
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Import here to avoid circular imports
            from app.lottie.image_processor_refactored import RefactoredImageProcessor
            from app.models.lottie_params import ImageTracingParamBuilder, ImageTracingStrategy
            
            svg_paths = []
            total_frames = len(frame_paths)
            
            for i, frame_path in enumerate(frame_paths):
                # Update progress
                if progress_callback:
                    progress = int((i / total_frames) * 100)
                    progress_callback(progress, f"Processing frame {i+1}/{total_frames} (high quality)")
                
                # Generate output path
                frame_name = os.path.splitext(os.path.basename(frame_path))[0]
                svg_path = os.path.join(output_dir, f"{frame_name}.svg")
                
                # Trace PNG to SVG with high quality settings
                params = ImageTracingParamBuilder()\
                    .with_input_path(frame_path)\
                    .with_output_path(svg_path)\
                    .with_strategy(ImageTracingStrategy.ADVANCED)\
                    .with_simplify_tolerance(0.5)\
                    .with_color_mode("colored")\
                    .with_embed_image(False)\
                    .build()
                
                processor = RefactoredImageProcessor()
                svg_path = processor.trace_png_to_svg(params)
                
                svg_paths.append(svg_path)
            
            # Update final progress
            if progress_callback:
                progress_callback(100, f"Processed {len(svg_paths)} frames to SVG (high quality)")
                
            return svg_paths
            
        except Exception as e:
            logger.error(f"Error processing frames: {str(e)}")
            raise ValueError(f"Failed to process frames: {str(e)}")


class FastFrameProcessor(BaseFrameProcessor):
    """Fast frame processor strategy.
    
    This strategy processes video frames into SVG files quickly
    with lower quality.
    """
    
    def process_frames(self, frame_paths: List[str], output_dir: str,
                      progress_callback: Optional[Callable] = None) -> List[str]:
        """Process video frames into SVG files quickly.
        
        Args:
            frame_paths (List[str]): Paths to the video frames
            output_dir (str): Directory to save the SVG files
            progress_callback (Optional[Callable]): Callback function for progress updates
            
        Returns:
            List[str]: Paths to the generated SVG files
            
        Raises:
            ValueError: If the input files are invalid or the processing fails
        """
        try:
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Import here to avoid circular imports
            from app.lottie.image_processor_refactored import RefactoredImageProcessor
            from app.models.lottie_params import ImageTracingParamBuilder, ImageTracingStrategy
            
            svg_paths = []
            total_frames = len(frame_paths)
            
            # Process only every other frame for speed
            frame_paths = frame_paths[::2] if len(frame_paths) > 10 else frame_paths
            
            for i, frame_path in enumerate(frame_paths):
                # Update progress
                if progress_callback:
                    progress = int((i / len(frame_paths)) * 100)
                    progress_callback(progress, f"Processing frame {i+1}/{len(frame_paths)} (fast mode)")
                
                # Generate output path
                frame_name = os.path.splitext(os.path.basename(frame_path))[0]
                svg_path = os.path.join(output_dir, f"{frame_name}.svg")
                
                # Trace PNG to SVG with fast settings
                params = (ImageTracingParamBuilder()
                    .with_input_path(frame_path)
                    .with_output_path(svg_path)
                    .with_strategy(ImageTracingStrategy.BASIC)
                    .with_simplify_tolerance(2.0)  # Higher tolerance for less detail but faster processing
                    .with_color_mode("colored")
                    .with_embed_image(False)
                    .build())
                
                processor = RefactoredImageProcessor()
                svg_path = processor.trace_png_to_svg(params)
                
                svg_paths.append(svg_path)
            
            # Update final progress
            if progress_callback:
                progress_callback(100, f"Processed {len(svg_paths)} frames to SVG (fast mode)")
                
            return svg_paths
            
        except Exception as e:
            logger.error(f"Error processing frames: {str(e)}")
            raise ValueError(f"Failed to process frames: {str(e)}")


class StandardLottieGenerator(BaseLottieGenerator):
    """Standard Lottie generator strategy.
    
    This strategy generates Lottie animations with a balanced approach
    to quality and file size.
    """
    
    def generate_lottie(self, svg_paths: List[str], output_path: str,
                       fps: int, width: int, height: int,
                       max_frames: int = 100, optimize: bool = True,
                       compress: bool = True) -> str:
        """Generate a Lottie animation from SVG files.
        
        Args:
            svg_paths (List[str]): Paths to the SVG files
            output_path (str): Path to save the Lottie animation
            fps (int): Frames per second for the animation
            width (int): Width of the animation
            height (int): Height of the animation
            max_frames (int): Maximum number of frames to include
            optimize (bool): Whether to optimize the animation
            compress (bool): Whether to compress the animation
            
        Returns:
            str: Path to the generated Lottie animation
            
        Raises:
            ValueError: If the input files are invalid or the generation fails
        """
        try:
            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Import here to avoid circular imports
            from app.lottie.lottie_generator import generate_lottie_from_svgs
            from app.models.lottie_params import LottieAnimationParamBuilder, LottieOptimizationLevel
            
            # Limit the number of frames
            svg_paths = svg_paths[:min(len(svg_paths), max_frames)]
            
            # Generate Lottie animation
            params = LottieAnimationParamBuilder()\
                .with_frame_paths(svg_paths)\
                .with_output_path(output_path)\
                .with_dimensions(width, height)\
                .with_fps(fps)\
                .with_optimization_level(LottieOptimizationLevel.MEDIUM if optimize else LottieOptimizationLevel.NONE)\
                .build()
            
            lottie_path = generate_lottie_from_svgs(params)
            
            # Compress the animation if requested
            if compress and os.path.exists(lottie_path):
                # Placeholder for compression logic
                # In a real implementation, this would compress the JSON file
                pass
            
            return lottie_path
            
        except Exception as e:
            logger.error(f"Error generating Lottie animation: {str(e)}")
            raise ValueError(f"Failed to generate Lottie animation: {str(e)}")


class StandardThumbnailGenerator(BaseThumbnailGenerator):
    """Standard thumbnail generator strategy.
    
    This strategy generates thumbnails with a balanced approach
    to quality and file size.
    """
    
    def generate_thumbnail(self, frame_path: str, output_dir: str,
                          source_dimensions: tuple = None,
                          maintain_aspect_ratio: bool = True) -> str:
        """Generate a thumbnail from a video frame.
        
        Args:
            frame_path (str): Path to the video frame
            output_dir (str): Directory to save the thumbnail
            source_dimensions (tuple): Source dimensions (width, height)
            maintain_aspect_ratio (bool): Whether to maintain aspect ratio
            
        Returns:
            str: Path to the generated thumbnail
            
        Raises:
            ValueError: If the input file is invalid or the generation fails
        """
        try:
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate output path
            thumbnail_path = os.path.join(output_dir, "thumbnail.png")
            
            # Read the image
            img = cv2.imread(frame_path)
            if img is None:
                raise ValueError(f"Failed to read image: {frame_path}")
            
            # Resize the image
            target_width = 256
            target_height = 256
            
            if maintain_aspect_ratio and source_dimensions is not None:
                src_width, src_height = source_dimensions
                if src_width and src_height:
                    aspect_ratio = src_width / src_height
                    if aspect_ratio > 1:  # Wider than tall
                        target_height = int(target_width / aspect_ratio)
                    else:  # Taller than wide
                        target_width = int(target_height * aspect_ratio)
            
            img_resized = cv2.resize(img, (target_width, target_height), interpolation=cv2.INTER_AREA)
            
            # Save the thumbnail
            cv2.imwrite(thumbnail_path, img_resized)
            
            return thumbnail_path
            
        except Exception as e:
            logger.error(f"Error generating thumbnail: {str(e)}")
            raise ValueError(f"Failed to generate thumbnail: {str(e)}")
