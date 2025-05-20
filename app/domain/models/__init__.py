"""Domain models for the Video Converter project.

This package contains the core domain models and base abstract classes
that implement the domain interfaces.
"""

from app.domain.models.base_converter import (
    BaseConverter,
    BaseVideoConverter,
    BaseLottieGenerator,
    BaseImageTracer,
)
from app.domain.models.base_storage import BaseStorage
from app.domain.models.base_task import BaseTask, BaseTaskQueue, BaseTaskProcessor
from app.domain.models.base_progress import (
    BaseProgressTracker,
    BaseProgressCallback,
    ProgressData,
)

__all__ = [
    "BaseConverter",
    "BaseVideoConverter",
    "BaseLottieGenerator",
    "BaseImageTracer",
    "BaseStorage",
    "BaseTask",
    "BaseTaskQueue",
    "BaseTaskProcessor",
    "BaseProgressTracker",
    "BaseProgressCallback",
    "ProgressData",
]
