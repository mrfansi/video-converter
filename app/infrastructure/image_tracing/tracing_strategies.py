"""Concrete implementations of image tracing strategies.

This module provides concrete implementations of the image tracing
interfaces defined in app.domain.interfaces.image_tracing.
"""

from typing import List, Tuple, Optional, Dict, Any
import numpy as np
import cv2
import logging
import os

from app.domain.models.image_tracing import BaseImageTracingStrategy
from app.domain.interfaces.image_tracing import TracingResult
from app.infrastructure.image_tracing.contour_strategies import (
    AdaptiveThresholdStrategy,
    ColorBasedSegmentationStrategy,
    CannyEdgeStrategy,
    HybridContourStrategy
)
from app.infrastructure.image_tracing.color_strategies import (
    DominantColorStrategy,
    CentroidColorStrategy,
    AverageColorStrategy,
    HybridColorStrategy
)
from app.infrastructure.image_tracing.svg_strategies import (
    BasicSVGStrategy,
    EmbeddedImageSVGStrategy,
    AdaptiveSVGStrategy
)
from app.infrastructure.image_tracing.fallback_strategies import (
    SimpleEmbedFallbackStrategy,
    GridFallbackStrategy,
    HybridFallbackStrategy
)

logger = logging.getLogger(__name__)


class BasicImageTracingStrategy(BaseImageTracingStrategy):
    """Basic image tracing strategy.
    
    This strategy uses simple contour extraction and SVG generation,
    suitable for simple images with clear contours.
    """
    
    def __init__(self):
        """Initialize the basic image tracing strategy."""
        super().__init__(
            contour_strategy=AdaptiveThresholdStrategy(),
            color_strategy=CentroidColorStrategy(),
            svg_strategy=BasicSVGStrategy(),
            fallback_strategy=SimpleEmbedFallbackStrategy()
        )


class StandardImageTracingStrategy(BaseImageTracingStrategy):
    """Standard image tracing strategy.
    
    This strategy uses more advanced contour extraction and SVG generation,
    suitable for most images.
    """
    
    def __init__(self):
        """Initialize the standard image tracing strategy."""
        super().__init__(
            contour_strategy=ColorBasedSegmentationStrategy(),
            color_strategy=DominantColorStrategy(),
            svg_strategy=EmbeddedImageSVGStrategy(),
            fallback_strategy=SimpleEmbedFallbackStrategy()
        )


class AdvancedImageTracingStrategy(BaseImageTracingStrategy):
    """Advanced image tracing strategy.
    
    This strategy uses the most advanced contour extraction and SVG generation,
    suitable for complex images with varying characteristics.
    """
    
    def __init__(self, simplify_tolerance: float = 1.0):
        """Initialize the advanced image tracing strategy.
        
        Args:
            simplify_tolerance (float, optional): Tolerance for path simplification. Defaults to 1.0.
        """
        super().__init__(
            contour_strategy=HybridContourStrategy(),
            color_strategy=HybridColorStrategy(),
            svg_strategy=AdaptiveSVGStrategy(simplify_tolerance=simplify_tolerance),
            fallback_strategy=HybridFallbackStrategy()
        )


class ImageTracingStrategyFactory:
    """Factory for creating image tracing strategies.
    
    This factory creates image tracing strategies based on the specified type,
    following the Factory pattern.
    """
    
    @staticmethod
    def create_strategy(strategy_type: str, **kwargs) -> BaseImageTracingStrategy:
        """Create an image tracing strategy.
        
        Args:
            strategy_type (str): Type of strategy to create (basic, standard, advanced)
            **kwargs: Additional arguments for the strategy
            
        Returns:
            BaseImageTracingStrategy: Image tracing strategy
            
        Raises:
            ValueError: If the strategy type is invalid
        """
        if strategy_type.lower() == "basic":
            return BasicImageTracingStrategy()
        elif strategy_type.lower() == "standard":
            return StandardImageTracingStrategy()
        elif strategy_type.lower() == "advanced":
            simplify_tolerance = kwargs.get("simplify_tolerance", 1.0)
            return AdvancedImageTracingStrategy(simplify_tolerance=simplify_tolerance)
        else:
            raise ValueError(f"Invalid strategy type: {strategy_type}")
