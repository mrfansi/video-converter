"""Refactored image processor implementation for the Video Converter project.

This module provides a refactored implementation of the image processor
using the Strategy pattern for improved maintainability and extensibility.
"""

import os
import logging
import cv2
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from PIL import Image
from io import BytesIO
import base64

from app.lottie.interfaces import IImageProcessor
from app.domain.interfaces.converter import IImageTracer
from app.infrastructure.image_tracer import OpenCVImageTracer
from app.models.lottie_params import ImageTracingParams, ImageTracingParamBuilder, ImageTracingStrategy

logger = logging.getLogger(__name__)


class RefactoredImageProcessor(IImageProcessor):
    """Refactored implementation of the image processor using the Strategy pattern.
    
    This class implements the IImageProcessor interface using the Strategy pattern
    for improved maintainability and extensibility.
    """
    
    def __init__(self, image_tracer: Optional[IImageTracer] = None):
        """Initialize the refactored image processor.
        
        Args:
            image_tracer (Optional[IImageTracer], optional): Image tracer to use. Defaults to None.
        """
        self.image_tracer = image_tracer or OpenCVImageTracer()
    
    def trace_png_to_svg(self, png_path: str, output_dir: str, simplify_tolerance: float = 1.0) -> str:
        """Trace a PNG image to SVG using the Strategy pattern.
        
        This method uses the Strategy pattern to delegate the image tracing to the
        appropriate strategy based on the image characteristics.
        
        Args:
            png_path (str): Path to the PNG image
            output_dir (str): Directory to save the SVG file
            simplify_tolerance (float, optional): Tolerance for path simplification. Defaults to 1.0.
            
        Returns:
            str: Path to the SVG file
            
        Raises:
            ValueError: If the input file is invalid or the conversion fails
        """
        logger.info(f"Tracing PNG to SVG: {png_path} with simplify_tolerance={simplify_tolerance}")
        
        try:
            # Ensure output directory exists
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate output path
            svg_filename = os.path.basename(png_path).replace('.png', '.svg')
            svg_path = os.path.join(output_dir, svg_filename)
            
            # Create tracing parameters using the builder pattern
            params = (ImageTracingParamBuilder()
                .with_input_path(png_path)
                .with_output_path(svg_path)
                .with_strategy(ImageTracingStrategy.ADVANCED)
                .with_simplify_tolerance(simplify_tolerance)
                .with_embed_image(True, quality=90)
                .build())
            
            # Trace the image using the image tracer
            result = self.image_tracer.trace_image(
                params.input_path,
                params.output_path,
                strategy=params.strategy.value,
                simplify_tolerance=params.simplify_tolerance,
                embed_image=params.embed_image,
                image_quality=params.image_quality
            )
            
            logger.info(f"Traced PNG to SVG: {result}")
            return result
        except Exception as e:
            logger.error(f"Error tracing PNG to SVG: {str(e)}")
            # Try with a simpler strategy if the advanced one fails
            try:
                # Create fallback parameters using the builder pattern
                fallback_params = (ImageTracingParamBuilder()
                    .with_input_path(png_path)
                    .with_output_path(svg_path)
                    .with_strategy(ImageTracingStrategy.BASIC)
                    .with_simplify_tolerance(simplify_tolerance)
                    .with_embed_image(True, quality=90)
                    .build())
                
                result = self.image_tracer.trace_image(
                    fallback_params.input_path,
                    fallback_params.output_path,
                    strategy=fallback_params.strategy.value,
                    simplify_tolerance=fallback_params.simplify_tolerance,
                    embed_image=fallback_params.embed_image,
                    image_quality=fallback_params.image_quality
                )
                logger.warning(f"Used fallback strategy for tracing: {result}")
                return result
            except Exception as fallback_error:
                logger.error(f"Fallback tracing also failed: {str(fallback_error)}")
                raise ValueError(f"Error tracing PNG to SVG: {str(e)}")
