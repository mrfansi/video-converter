"""Concrete implementations of fallback strategies.

This module provides concrete implementations of the fallback
interfaces defined in app.domain.interfaces.image_tracing.
"""

from typing import List, Tuple, Optional
import numpy as np
import cv2
import logging
import base64
from io import BytesIO
from PIL import Image

from app.domain.models.image_tracing import BaseFallbackStrategy

logger = logging.getLogger(__name__)


class SimpleEmbedFallbackStrategy(BaseFallbackStrategy):
    """Simple fallback strategy that embeds the original image.
    
    This strategy creates a simple SVG with just the embedded image,
    used when more advanced tracing strategies fail.
    """
    
    def __init__(self, image_quality: int = 90):
        """Initialize the simple embed fallback strategy.
        
        Args:
            image_quality (int, optional): Image quality (0-100). Defaults to 90.
        """
        self.image_quality = image_quality
    
    def _generate_fallback_content(self, image: np.ndarray) -> str:
        """Generate fallback SVG content.
        
        Args:
            image (np.ndarray): Original image (OpenCV format)
            
        Returns:
            str: SVG content
        """
        height, width = image.shape[:2]
        
        # Convert to RGB (from BGR)
        img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Convert OpenCV image to PIL Image
        pil_img = Image.fromarray(img_rgb)
        
        # Save PIL Image to BytesIO object with optimized settings
        buffered = BytesIO()
        pil_img.save(buffered, format="PNG", optimize=True, quality=self.image_quality)
        
        # Get base64 encoded string
        img_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        # Create SVG with just the image
        svg_content = f'<image width="{width}" height="{height}" href="data:image/png;base64,{img_base64}" />'
        
        logger.warning("Used simple embed fallback strategy")
        return svg_content


class GridFallbackStrategy(BaseFallbackStrategy):
    """Grid-based fallback strategy.
    
    This strategy creates a grid-based SVG representation of the image,
    used when more advanced tracing strategies fail.
    """
    
    def __init__(self, grid_size: int = 10):
        """Initialize the grid fallback strategy.
        
        Args:
            grid_size (int, optional): Grid size (number of cells per side). Defaults to 10.
        """
        self.grid_size = grid_size
    
    def _generate_fallback_content(self, image: np.ndarray) -> str:
        """Generate fallback SVG content.
        
        Args:
            image (np.ndarray): Original image (OpenCV format)
            
        Returns:
            str: SVG content
        """
        height, width = image.shape[:2]
        
        # Convert to RGB (from BGR)
        img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # First embed the original image with low opacity as background
        pil_img = Image.fromarray(img_rgb)
        buffered = BytesIO()
        pil_img.save(buffered, format="PNG", optimize=True, quality=70)
        img_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        # Create SVG content with the image
        svg_content = f'<image width="{width}" height="{height}" href="data:image/png;base64,{img_base64}" style="opacity:0.3" />'
        
        # Calculate cell dimensions
        cell_width = width / self.grid_size
        cell_height = height / self.grid_size
        
        # Create a grid of rectangles with colors sampled from the image
        for row in range(self.grid_size):
            for col in range(self.grid_size):
                # Calculate cell boundaries
                x = col * cell_width
                y = row * cell_height
                
                # Sample color from the center of the cell
                center_x = int(x + cell_width / 2)
                center_y = int(y + cell_height / 2)
                
                # Ensure coordinates are within image bounds
                center_x = min(max(0, center_x), width - 1)
                center_y = min(max(0, center_y), height - 1)
                
                # Get color at the center (BGR format)
                b, g, r = image[center_y, center_x]
                
                # Add rectangle to SVG
                svg_content += f'<rect x="{x}" y="{y}" width="{cell_width}" height="{cell_height}" '
                svg_content += f'fill="rgba({r},{g},{b},0.5)" stroke="rgba({r},{g},{b},0.8)" stroke-width="1" />'
        
        logger.warning("Used grid fallback strategy")
        return svg_content


class HybridFallbackStrategy(BaseFallbackStrategy):
    """Hybrid fallback strategy.
    
    This strategy combines multiple fallback approaches,
    selecting the most appropriate one based on image characteristics.
    """
    
    def __init__(
        self,
        simple_strategy: Optional[SimpleEmbedFallbackStrategy] = None,
        grid_strategy: Optional[GridFallbackStrategy] = None
    ):
        """Initialize the hybrid fallback strategy.
        
        Args:
            simple_strategy (Optional[SimpleEmbedFallbackStrategy], optional): Simple embed strategy. Defaults to None.
            grid_strategy (Optional[GridFallbackStrategy], optional): Grid strategy. Defaults to None.
        """
        self.simple_strategy = simple_strategy or SimpleEmbedFallbackStrategy()
        self.grid_strategy = grid_strategy or GridFallbackStrategy()
    
    def _generate_fallback_content(self, image: np.ndarray) -> str:
        """Generate fallback SVG content.
        
        Args:
            image (np.ndarray): Original image (OpenCV format)
            
        Returns:
            str: SVG content
        """
        # Analyze image complexity to determine which fallback to use
        complexity = np.std(image, axis=(0, 1)).mean()
        
        # Use grid strategy for more complex images, simple embed for simpler ones
        if complexity > 30:  # Higher complexity threshold
            logger.info(f"Using grid fallback for complex image (complexity: {complexity:.2f})")
            return self.grid_strategy._generate_fallback_content(image)
        else:
            logger.info(f"Using simple embed fallback for simple image (complexity: {complexity:.2f})")
            return self.simple_strategy._generate_fallback_content(image)
