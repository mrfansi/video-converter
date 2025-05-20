"""Parameter objects for the Video Converter project.

This package provides parameter objects that replace complex function signatures
with well-structured, validated objects. This approach improves code readability,
maintainability, and type safety while reducing the number of parameters passed
between functions.
"""

from app.models.base_params import BaseParams, ParamBuilder
from app.models.video_params import (
    VideoQuality, VideoResolution, VideoFormat,
    VideoConversionParams, VideoConversionParamBuilder
)
from app.models.lottie_params import (
    LottieColorMode, LottieOptimizationLevel,
    LottieAnimationParams, LottieAnimationParamBuilder,
    SVGConversionParams, SVGConversionParamBuilder
)
from app.models.task_params import (
    TaskStatus, TaskType,
    TaskParams, TaskParamBuilder,
    TaskUpdateParams, TaskUpdateParamBuilder
)

__all__ = [
    # Base classes
    'BaseParams', 'ParamBuilder',
    
    # Video conversion
    'VideoQuality', 'VideoResolution', 'VideoFormat',
    'VideoConversionParams', 'VideoConversionParamBuilder',
    
    # Lottie animation
    'LottieColorMode', 'LottieOptimizationLevel',
    'LottieAnimationParams', 'LottieAnimationParamBuilder',
    'SVGConversionParams', 'SVGConversionParamBuilder',
    
    # Task queue
    'TaskStatus', 'TaskType',
    'TaskParams', 'TaskParamBuilder',
    'TaskUpdateParams', 'TaskUpdateParamBuilder'
]
