"""Parameter objects for task queue functionality.

This module provides parameter objects for task queue operations,
reducing function parameter complexity and improving code readability.
"""

from enum import Enum
from typing import Dict, Any, Optional, Union
from datetime import datetime
from pydantic import Field, validator

from app.models.base_params import BaseParams, ParamBuilder


class TaskStatus(str, Enum):
    """Task status values."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(str, Enum):
    """Task types supported by the system."""

    PROCESS_VIDEO = "process_video"
    CONVERT_VIDEO_FORMAT = "convert_video_format"
    GENERATE_LOTTIE = "generate_lottie"
    CUSTOM = "custom"


class TaskParams(BaseParams):
    """Parameters for task operations.

    This parameter object encapsulates all options for task operations,
    replacing the need for numerous function parameters.
    """

    # Required parameters
    task_id: str = Field(..., description="Unique identifier for the task")
    task_type: TaskType = Field(..., description="Type of the task")

    # Optional parameters with defaults
    params: Dict[str, Any] = Field(
        default_factory=dict, description="Task-specific parameters"
    )
    status: TaskStatus = Field(
        default=TaskStatus.PENDING, description="Current status of the task"
    )
    progress: int = Field(default=0, description="Progress percentage (0-100)")
    result: Optional[Dict[str, Any]] = Field(
        default=None, description="Task result data"
    )
    error: Optional[str] = Field(
        default=None, description="Error message if task failed"
    )
    created_at: datetime = Field(
        default_factory=datetime.now, description="Task creation timestamp"
    )
    updated_at: Optional[datetime] = Field(
        default=None, description="Task last update timestamp"
    )

    @validator("task_id")
    def validate_task_id(cls, v):
        """Validate that task ID is not empty."""
        if not v or not v.strip():
            raise ValueError("Task ID cannot be empty")
        return v

    @validator("progress")
    def validate_progress(cls, v):
        """Validate that progress is between 0 and 100."""
        if not 0 <= v <= 100:
            raise ValueError("Progress must be between 0 and 100")
        return v

    @validator("updated_at")
    def validate_updated_at(cls, v, values):
        """Validate that updated_at is after created_at if provided."""
        if v and "created_at" in values and v < values["created_at"]:
            raise ValueError("Updated timestamp cannot be before creation timestamp")
        return v

    def is_complete(self) -> bool:
        """Check if the task is complete (either completed or failed).

        Returns:
            bool: True if the task is complete, False otherwise
        """
        return self.status in [
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        ]

    def is_active(self) -> bool:
        """Check if the task is active (pending or processing).

        Returns:
            bool: True if the task is active, False otherwise
        """
        return self.status in [TaskStatus.PENDING, TaskStatus.PROCESSING]

    def update_progress(self, progress: int) -> None:
        """Update the task progress.

        Args:
            progress (int): New progress value (0-100)
        """
        if not 0 <= progress <= 100:
            raise ValueError("Progress must be between 0 and 100")
        self.progress = progress
        self.updated_at = datetime.now()

    def update_status(self, status: Union[TaskStatus, str]) -> None:
        """Update the task status.

        Args:
            status (Union[TaskStatus, str]): New status value
        """
        if isinstance(status, str):
            status = TaskStatus(status)
        self.status = status
        self.updated_at = datetime.now()

    def set_result(self, result: Dict[str, Any]) -> None:
        """Set the task result.

        Args:
            result (Dict[str, Any]): Task result data
        """
        self.result = result
        self.updated_at = datetime.now()

    def set_error(self, error: str) -> None:
        """Set the task error.

        Args:
            error (str): Error message
        """
        self.error = error
        self.status = TaskStatus.FAILED
        self.updated_at = datetime.now()


class TaskParamBuilder(ParamBuilder[TaskParams]):
    """Builder for TaskParams.

    Provides a fluent interface for building task parameters.
    """

    def __init__(self):
        """Initialize the builder with the TaskParams class."""
        super().__init__(TaskParams)

    def with_task_id(self, task_id: str) -> "TaskParamBuilder":
        """Set the task ID."""
        return self.with_param("task_id", task_id)

    def with_task_type(self, task_type: Union[TaskType, str]) -> "TaskParamBuilder":
        """Set the task type."""
        if isinstance(task_type, str):
            task_type = TaskType(task_type)
        return self.with_param("task_type", task_type)

    def with_params(self, params: Dict[str, Any]) -> "TaskParamBuilder":
        """Set the task-specific parameters."""
        return self.with_param("params", params)

    def with_status(self, status: Union[TaskStatus, str]) -> "TaskParamBuilder":
        """Set the task status."""
        if isinstance(status, str):
            status = TaskStatus(status)
        return self.with_param("status", status)

    def with_progress(self, progress: int) -> "TaskParamBuilder":
        """Set the task progress."""
        return self.with_param("progress", progress)

    def with_result(self, result: Dict[str, Any]) -> "TaskParamBuilder":
        """Set the task result."""
        return self.with_param("result", result)

    def with_error(self, error: str) -> "TaskParamBuilder":
        """Set the task error."""
        return self.with_param("error", error)

    def with_timestamps(
        self, created_at: datetime, updated_at: Optional[datetime] = None
    ) -> "TaskParamBuilder":
        """Set the task timestamps."""
        self.with_param("created_at", created_at)
        if updated_at:
            self.with_param("updated_at", updated_at)
        return self


class TaskUpdateParams(BaseParams):
    """Parameters for task update operations.

    This parameter object encapsulates all options for updating tasks,
    replacing the need for numerous function parameters.
    """

    # Required parameters
    task_id: str = Field(..., description="Unique identifier for the task")

    # Optional update parameters
    status: Optional[TaskStatus] = Field(
        default=None, description="New status of the task"
    )
    progress: Optional[int] = Field(
        default=None, description="New progress percentage (0-100)"
    )
    result: Optional[Dict[str, Any]] = Field(
        default=None, description="Task result data"
    )
    error: Optional[str] = Field(
        default=None, description="Error message if task failed"
    )

    @validator("task_id")
    def validate_task_id(cls, v):
        """Validate that task ID is not empty."""
        if not v or not v.strip():
            raise ValueError("Task ID cannot be empty")
        return v

    @validator("progress")
    def validate_progress(cls, v):
        """Validate that progress is between 0 and 100 if provided."""
        if v is not None and not 0 <= v <= 100:
            raise ValueError("Progress must be between 0 and 100")
        return v

    def has_updates(self) -> bool:
        """Check if the update params contain any updates.

        Returns:
            bool: True if there are updates, False otherwise
        """
        return any(
            v is not None for v in [self.status, self.progress, self.result, self.error]
        )


class TaskUpdateParamBuilder(ParamBuilder[TaskUpdateParams]):
    """Builder for TaskUpdateParams.

    Provides a fluent interface for building task update parameters.
    """

    def __init__(self):
        """Initialize the builder with the TaskUpdateParams class."""
        super().__init__(TaskUpdateParams)

    def with_task_id(self, task_id: str) -> "TaskUpdateParamBuilder":
        """Set the task ID."""
        return self.with_param("task_id", task_id)

    def with_status(self, status: Union[TaskStatus, str]) -> "TaskUpdateParamBuilder":
        """Set the new task status."""
        if isinstance(status, str):
            status = TaskStatus(status)
        return self.with_param("status", status)

    def with_progress(self, progress: int) -> "TaskUpdateParamBuilder":
        """Set the new task progress."""
        return self.with_param("progress", progress)

    def with_result(self, result: Dict[str, Any]) -> "TaskUpdateParamBuilder":
        """Set the task result."""
        return self.with_param("result", result)

    def with_error(self, error: str) -> "TaskUpdateParamBuilder":
        """Set the task error."""
        return self.with_param("error", error)
