"""Domain interfaces for the Video Converter project.

This package contains the core domain interfaces that define the contracts
that the rest of the application must adhere to.
"""

from app.domain.interfaces.converter import (
    IConverter,
    IVideoConverter,
    ILottieGenerator,
    IImageTracer,
    ConversionResult,
)
from app.domain.interfaces.storage import IStorage, StorageResult
from app.domain.interfaces.task import (
    ITask,
    ITaskQueue,
    ITaskProcessor,
    TaskStatus,
    TaskResult,
)
from app.domain.interfaces.progress import IProgressTracker, IProgressCallback

__all__ = [
    "IConverter",
    "IVideoConverter",
    "ILottieGenerator",
    "IImageTracer",
    "ConversionResult",
    "IStorage",
    "StorageResult",
    "ITask",
    "ITaskQueue",
    "ITaskProcessor",
    "TaskStatus",
    "TaskResult",
    "IProgressTracker",
    "IProgressCallback",
]
