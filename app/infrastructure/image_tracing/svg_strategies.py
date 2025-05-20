"""Concrete implementations of SVG generation strategies.

This module provides concrete implementations of the SVG generation
interfaces defined in app.domain.interfaces.image_tracing.
"""

from typing import List, Tuple, Optional, Dict, Any
import numpy as np
import cv2
import logging
import base64
from io import BytesIO
from PIL import Image
import os

from app.domain.models.image_tracing import BaseSVGGenerationStrategy

logger = logging.getLogger(__name__)


class BasicSVGStrategy(BaseSVGGenerationStrategy):
    """Basic SVG generation strategy.
    
    This strategy generates a simple SVG with contours as paths,
    without embedding the original image.
    """
    
    def _generate_svg_content(self, image: np.ndarray, contours: List[np.ndarray], colors: List[Tuple[int, int, int]]) -> str:
        """Generate the content of the SVG.
        
        Args:
            image (np.ndarray): Original image (OpenCV format)
            contours (List[np.ndarray]): Contours to include in the SVG
            colors (List[Tuple[int, int, int]]): Colors for each contour (RGB)
            
        Returns:
            str: SVG content (without header and footer)
        """
        svg_content = ""
        height, width = image.shape[:2]
        
        # Add paths for each contour
        for i, contour in enumerate(contours):
            # Skip very small contours
            area = cv2.contourArea(contour)
            if area < 5:
                continue
            
            # Convert contour to SVG path
            path = "M"
            for j, point in enumerate(contour):
                x, y = point[0]
                if j == 0:
                    path += f"{x},{y}"
                else:
                    path += f" L{x},{y}"
            
            # Close path
            path += " Z"
            
            # Get color for this contour
            if i < len(colors):
                r, g, b = colors[i]
            else:
                r, g, b = 0, 0, 0  # Default to black
            
            # Add path to SVG with appropriate styling
            svg_content += f'<path d="{path}" fill="none" stroke="rgb({r},{g},{b})" stroke-width="1" id="path{i}" />'
        
        return svg_content


class EmbeddedImageSVGStrategy(BaseSVGGenerationStrategy):
    """SVG generation strategy with embedded image.
    
    This strategy generates an SVG with the original image embedded as a base64 data URI,
    and contours overlaid as paths.
    """
    
    def __init__(self, image_quality: int = 90, optimize: bool = True):
        """Initialize the embedded image SVG strategy.
        
        Args:
            image_quality (int, optional): Image quality (0-100). Defaults to 90.
            optimize (bool, optional): Whether to optimize the embedded image. Defaults to True.
        """
        self.image_quality = image_quality
        self.optimize = optimize
    
    def _generate_svg_content(self, image: np.ndarray, contours: List[np.ndarray], colors: List[Tuple[int, int, int]]) -> str:
        """Generate the content of the SVG.
        
        Args:
            image (np.ndarray): Original image (OpenCV format)
            contours (List[np.ndarray]): Contours to include in the SVG
            colors (List[Tuple[int, int, int]]): Colors for each contour (RGB)
            
        Returns:
            str: SVG content (without header and footer)
        """
        svg_content = ""
        height, width = image.shape[:2]
        
        # Convert to RGB (from BGR)
        img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Embed the original image as a base64 data URI
        # Convert OpenCV image to PIL Image
        pil_img = Image.fromarray(img_rgb)
        
        # Save PIL Image to BytesIO object with optimized settings
        buffered = BytesIO()
        pil_img.save(buffered, format="PNG", optimize=self.optimize, quality=self.image_quality)
        
        # Get base64 encoded string
        img_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        # Add the image to the SVG
        svg_content += f'<image width="{width}" height="{height}" href="data:image/png;base64,{img_base64}" />'
        
        # Add paths for each contour with semi-transparent styling
        for i, contour in enumerate(contours):
            # Skip very small contours
            area = cv2.contourArea(contour)
            if area < 5:
                continue
            
            # Convert contour to SVG path
            path = "M"
            for j, point in enumerate(contour):
                x, y = point[0]
                if j == 0:
                    path += f"{x},{y}"
                else:
                    path += f" L{x},{y}"
            
            # Close path
            path += " Z"
            
            # Get color for this contour
            if i < len(colors):
                r, g, b = colors[i]
            else:
                r, g, b = 0, 0, 0  # Default to black
            
            # Determine if this contour should be filled or stroked based on size
            if area > 200:  # Larger contours
                fill_opacity = min(0.3, area / (width * height * 5))  # Adaptive opacity based on size
                stroke_opacity = 0.5
                fill_attr = f'fill="rgba({r},{g},{b},{fill_opacity:.2f})"'
            else:  # Smaller contours
                stroke_opacity = 0.7
                fill_attr = 'fill="none"'
            
            # Add path to SVG with appropriate styling
            svg_content += f'<path d="{path}" {fill_attr} stroke="rgba({r},{g},{b},{stroke_opacity})" stroke-width="1" id="path{i}" />'
        
        return svg_content


class AdaptiveSVGStrategy(BaseSVGGenerationStrategy):
    """Adaptive SVG generation strategy.
    
    This strategy adapts the SVG generation based on the characteristics of the image and contours,
    using different approaches for different types of content.
    """
    
    def __init__(self, simplify_tolerance: float = 1.0):
        """Initialize the adaptive SVG strategy.
        
        Args:
            simplify_tolerance (float, optional): Tolerance for path simplification. Defaults to 1.0.
        """
        self.simplify_tolerance = simplify_tolerance
    
    def _generate_svg_content(self, image: np.ndarray, contours: List[np.ndarray], colors: List[Tuple[int, int, int]]) -> str:
        """Generate the content of the SVG.
        
        Args:
            image (np.ndarray): Original image (OpenCV format)
            contours (List[np.ndarray]): Contours to include in the SVG
            colors (List[Tuple[int, int, int]]): Colors for each contour (RGB)
            
        Returns:
            str: SVG content (without header and footer)
        """
        svg_content = ""
        height, width = image.shape[:2]
        
        # Convert to RGB (from BGR)
        img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Embed the original image as a base64 data URI
        # Convert OpenCV image to PIL Image
        pil_img = Image.fromarray(img_rgb)
        
        # Save PIL Image to BytesIO object with optimized settings
        buffered = BytesIO()
        pil_img.save(buffered, format="PNG", optimize=True, quality=90)
        
        # Get base64 encoded string
        img_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        # Add the image to the SVG
        svg_content += f'<image width="{width}" height="{height}" href="data:image/png;base64,{img_base64}" />'
        
        # Add paths for each contour with adaptive styling
        valid_paths = 0
        for i, contour in enumerate(contours):
            # Skip very small contours
            area = cv2.contourArea(contour)
            if area < 5:
                continue
            
            # Skip very large contours (background)
            if area > 0.9 * width * height:
                continue
            
            # Adaptive contour simplification based on size
            area_ratio = area / (width * height)
            
            # Adaptive simplification based on contour size
            if area_ratio < 0.001:  # Very small details
                adaptive_tolerance = self.simplify_tolerance * 0.5  # Less simplification
            elif area_ratio < 0.01:  # Small details
                adaptive_tolerance = self.simplify_tolerance * 0.8
            elif area_ratio < 0.05:  # Medium details
                adaptive_tolerance = self.simplify_tolerance * 1.0
            else:  # Large objects
                adaptive_tolerance = self.simplify_tolerance * 1.5  # More simplification
            
            epsilon = adaptive_tolerance * cv2.arcLength(contour, True)
            simplified_contour = cv2.approxPolyDP(contour, epsilon, True)
            
            # Skip contours with too few points
            min_points = 3
            if area < 50:  # For very small contours
                min_points = 2  # Allow simpler shapes for small details
            
            if len(simplified_contour) < min_points:
                continue
            
            # Convert contour to SVG path
            path = "M"
            for j, point in enumerate(simplified_contour):
                x, y = point[0]
                if j == 0:
                    path += f"{x},{y}"
                else:
                    path += f" L{x},{y}"
            
            # Close path
            path += " Z"
            
            # Get color for this contour
            if i < len(colors):
                r, g, b = colors[i]
            else:
                r, g, b = 0, 0, 0  # Default to black
            
            # Determine styling based on contour characteristics
            if area > 200:  # Larger contours
                fill_opacity = min(0.3, area / (width * height * 5))  # Adaptive opacity based on size
                stroke_opacity = 0.5
                fill_attr = f'fill="rgba({r},{g},{b},{fill_opacity:.2f})"'
            else:  # Smaller contours
                stroke_opacity = 0.7
                fill_attr = 'fill="none"'
            
            # Add path to SVG with appropriate styling
            svg_content += f'<path d="{path}" {fill_attr} stroke="rgba({r},{g},{b},{stroke_opacity})" stroke-width="1" id="path{i}" />'
            valid_paths += 1
        
        # If no valid paths were found, create artificial contours
        if valid_paths == 0:
            logger.warning("No valid contours found, creating artificial contours")
            svg_content += self._create_artificial_contours(image)
        
        return svg_content
    
    def _create_artificial_contours(self, image: np.ndarray) -> str:
        """Create artificial contours when no valid contours are found.
        
        Args:
            image (np.ndarray): Original image (OpenCV format)
            
        Returns:
            str: SVG content with artificial contours
        """
        height, width = image.shape[:2]
        svg_content = ""
        
        # Analyze image complexity to determine optimal grid density
        complexity = np.std(image, axis=(0, 1)).mean()
        
        # Adaptive grid size based on image complexity
        base_grid_size = 3
        max_grid_size = 6
        complexity_threshold = 60
        
        # Calculate grid size (higher complexity = more regions)
        grid_size = base_grid_size + int(min(complexity / complexity_threshold * (max_grid_size - base_grid_size), max_grid_size - base_grid_size))
        logger.info(f"Using adaptive grid size: {grid_size}x{grid_size} (complexity: {complexity:.2f})")
        
        region_width = width // grid_size
        region_height = height // grid_size
        
        # For each region, create a contour based on color analysis
        for row in range(grid_size):
            for col in range(grid_size):
                # Define region boundaries
                x1 = col * region_width
                y1 = row * region_height
                x2 = (col + 1) * region_width
                y2 = (row + 1) * region_height
                
                # Extract region from image
                region = image[y1:y2, x1:x2]
                
                # Skip if region is empty
                if region.size == 0:
                    continue
                
                # Calculate average color for the region
                avg_color = np.mean(region, axis=(0, 1)).astype(int)
                b, g, r = avg_color
                
                # Create a rectangular contour for this region with some randomness
                jitter = 5
                points = [
                    [x1 + np.random.randint(-jitter, jitter), y1 + np.random.randint(-jitter, jitter)],
                    [x2 + np.random.randint(-jitter, jitter), y1 + np.random.randint(-jitter, jitter)],
                    [x2 + np.random.randint(-jitter, jitter), y2 + np.random.randint(-jitter, jitter)],
                    [x1 + np.random.randint(-jitter, jitter), y2 + np.random.randint(-jitter, jitter)]
                ]
                
                # Convert to SVG path
                path = "M"
                for j, point in enumerate(points):
                    x, y = point
                    # Ensure coordinates are within image bounds
                    x = max(0, min(x, width - 1))
                    y = max(0, min(y, height - 1))
                    if j == 0:
                        path += f"{x},{y}"
                    else:
                        path += f" L{x},{y}"
                path += " Z"
                
                # Add path to SVG with color from the region
                opacity = 0.3
                svg_content += f'<path d="{path}" fill="rgba({r},{g},{b},{opacity})" stroke="rgba({r},{g},{b},0.8)" stroke-width="1" id="path_grid_{row}_{col}" />'
        
        return svg_content
