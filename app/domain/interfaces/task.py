"""Task management interfaces for the Video Converter project.

This module defines the core interfaces for task management operations.
These interfaces follow the Interface Segregation Principle (ISP) by providing
focused interfaces for specific task operations.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum, auto
from typing import Dict, Any, Optional, List, Union
from uuid import UUID

from app.models.task_params import TaskParams


class TaskStatus(Enum):
    """Enumeration of possible task statuses."""

    PENDING = auto()
    PROCESSING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()


class TaskResult:
    """Result of a task operation.

    This class encapsulates the result of a task operation, including
    success status, task ID, and any error information.
    """

    def __init__(
        self,
        success: bool,
        task_id: Optional[Union[str, UUID]] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Initialize a task result.

        Args:
            success (bool): Whether the operation was successful
            task_id (Optional[Union[str, UUID]], optional): ID of the task. Defaults to None.
            error (Optional[str], optional): Error message if operation failed. Defaults to None.
            metadata (Optional[Dict[str, Any]], optional): Additional metadata. Defaults to None.
        """
        self.success = success
        self.task_id = str(task_id) if task_id else None
        self.error = error
        self.metadata = metadata or {}

    @classmethod
    def success_result(
        cls, task_id: Union[str, UUID], metadata: Optional[Dict[str, Any]] = None
    ) -> "TaskResult":
        """Create a successful task result.

        Args:
            task_id (Union[str, UUID]): ID of the task
            metadata (Optional[Dict[str, Any]], optional): Additional metadata. Defaults to None.

        Returns:
            TaskResult: A successful task result
        """
        return cls(True, task_id=task_id, metadata=metadata)

    @classmethod
    def error_result(
        cls, error: str, metadata: Optional[Dict[str, Any]] = None
    ) -> "TaskResult":
        """Create an error task result.

        Args:
            error (str): Error message
            metadata (Optional[Dict[str, Any]], optional): Additional metadata. Defaults to None.

        Returns:
            TaskResult: An error task result
        """
        return cls(False, error=error, metadata=metadata)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation of the result
        """
        result = {"success": self.success, "metadata": self.metadata}

        if self.task_id:
            result["task_id"] = self.task_id

        if self.error:
            result["error"] = self.error

        return result


class ITask(ABC):
    """Interface for task entities.

    This interface defines the contract for task entities in the system.
    It follows the Interface Segregation Principle by providing a focused interface
    for task operations.
    """

    @property
    @abstractmethod
    def id(self) -> str:
        """Get the task ID.

        Returns:
            str: Task ID
        """
        pass

    @property
    @abstractmethod
    def type(self) -> str:
        """Get the task type.

        Returns:
            str: Task type
        """
        pass

    @property
    @abstractmethod
    def status(self) -> TaskStatus:
        """Get the task status.

        Returns:
            TaskStatus: Current status of the task
        """
        pass

    @property
    @abstractmethod
    def params(self) -> Dict[str, Any]:
        """Get the task parameters.

        Returns:
            Dict[str, Any]: Task parameters
        """
        pass

    @property
    @abstractmethod
    def created_at(self) -> datetime:
        """Get the task creation timestamp.

        Returns:
            datetime: Creation timestamp
        """
        pass

    @property
    @abstractmethod
    def updated_at(self) -> datetime:
        """Get the task update timestamp.

        Returns:
            datetime: Last update timestamp
        """
        pass

    @property
    @abstractmethod
    def result(self) -> Optional[Dict[str, Any]]:
        """Get the task result.

        Returns:
            Optional[Dict[str, Any]]: Task result, if available
        """
        pass

    @abstractmethod
    def update_status(self, status: TaskStatus) -> None:
        """Update the task status.

        Args:
            status (TaskStatus): New status
        """
        pass

    @abstractmethod
    def update_progress(self, progress: float) -> None:
        """Update the task progress.

        Args:
            progress (float): Progress value between 0 and 1
        """
        pass

    @abstractmethod
    def set_result(self, result: Dict[str, Any]) -> None:
        """Set the task result.

        Args:
            result (Dict[str, Any]): Task result
        """
        pass

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert the task to a dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation of the task
        """
        pass


class ITaskQueue(ABC):
    """Interface for task queues.

    This interface defines the contract for task queues in the system.
    It follows the Interface Segregation Principle by providing a focused interface
    for task queue operations.
    """

    @abstractmethod
    def add_task(self, params: TaskParams) -> TaskResult:
        """Add a task to the queue.

        Args:
            params (TaskParams): Task parameters

        Returns:
            TaskResult: Result of the add operation
        """
        pass

    @abstractmethod
    def get_task(self, task_id: str) -> Optional[ITask]:
        """Get a task by ID.

        Args:
            task_id (str): Task ID

        Returns:
            Optional[ITask]: Task if found, None otherwise
        """
        pass

    @abstractmethod
    def get_tasks(
        self, status: Optional[TaskStatus] = None, limit: int = 10
    ) -> List[ITask]:
        """Get tasks, optionally filtered by status.

        Args:
            status (Optional[TaskStatus], optional): Filter by status. Defaults to None.
            limit (int, optional): Maximum number of tasks to return. Defaults to 10.

        Returns:
            List[ITask]: List of tasks
        """
        pass

    @abstractmethod
    def process_next_task(self) -> Optional[ITask]:
        """Process the next pending task.

        Returns:
            Optional[ITask]: Processed task if available, None otherwise
        """
        pass

    @abstractmethod
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a task.

        Args:
            task_id (str): Task ID

        Returns:
            bool: True if the task was cancelled, False otherwise
        """
        pass


class ITaskProcessor(ABC):
    """Interface for task processors.

    This interface defines the contract for task processors in the system.
    It follows the Interface Segregation Principle by providing a focused interface
    for task processing operations.
    """

    @abstractmethod
    def can_process(self, task_type: str) -> bool:
        """Check if this processor can handle the specified task type.

        Args:
            task_type (str): Task type

        Returns:
            bool: True if this processor can handle the task, False otherwise
        """
        pass

    @abstractmethod
    def process(self, task: ITask) -> None:
        """Process a task.

        Args:
            task (ITask): Task to process
        """
        pass
