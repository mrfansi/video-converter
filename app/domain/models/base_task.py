"""Base abstract classes for tasks in the Video Converter project.

This module provides base implementations of the task interfaces
defined in app.domain.interfaces.task. These abstract classes implement
common functionality while leaving specific task processing logic to concrete subclasses.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional, List, Set, Union
import uuid
import logging

from app.domain.interfaces.task import ITask, ITaskQueue, ITaskProcessor, TaskStatus, TaskResult
from app.models.task_params import TaskParams


logger = logging.getLogger(__name__)


class BaseTask(ITask):
    """Base implementation of the ITask interface.
    
    This class provides a concrete implementation of the ITask interface,
    handling task state management and serialization.
    """
    
    def __init__(
        self,
        task_id: Optional[str] = None,
        task_type: str = None,
        params: Dict[str, Any] = None,
        status: TaskStatus = TaskStatus.PENDING,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        result: Optional[Dict[str, Any]] = None,
        progress: float = 0.0
    ):
        """Initialize a base task.
        
        Args:
            task_id (Optional[str], optional): Task ID. Defaults to None (auto-generated).
            task_type (str, optional): Task type. Defaults to None.
            params (Dict[str, Any], optional): Task parameters. Defaults to None.
            status (TaskStatus, optional): Task status. Defaults to TaskStatus.PENDING.
            created_at (Optional[datetime], optional): Creation timestamp. Defaults to None (current time).
            updated_at (Optional[datetime], optional): Update timestamp. Defaults to None (current time).
            result (Optional[Dict[str, Any]], optional): Task result. Defaults to None.
            progress (float, optional): Task progress. Defaults to 0.0.
        """
        self._id = task_id or str(uuid.uuid4())
        self._type = task_type
        self._params = params or {}
        self._status = status
        self._created_at = created_at or datetime.now()
        self._updated_at = updated_at or datetime.now()
        self._result = result
        self._progress = progress
    
    @property
    def id(self) -> str:
        """Get the task ID.
        
        Returns:
            str: Task ID
        """
        return self._id
    
    @property
    def type(self) -> str:
        """Get the task type.
        
        Returns:
            str: Task type
        """
        return self._type
    
    @property
    def status(self) -> TaskStatus:
        """Get the task status.
        
        Returns:
            TaskStatus: Current status of the task
        """
        return self._status
    
    @property
    def params(self) -> Dict[str, Any]:
        """Get the task parameters.
        
        Returns:
            Dict[str, Any]: Task parameters
        """
        return self._params
    
    @property
    def created_at(self) -> datetime:
        """Get the task creation timestamp.
        
        Returns:
            datetime: Creation timestamp
        """
        return self._created_at
    
    @property
    def updated_at(self) -> datetime:
        """Get the task update timestamp.
        
        Returns:
            datetime: Last update timestamp
        """
        return self._updated_at
    
    @property
    def result(self) -> Optional[Dict[str, Any]]:
        """Get the task result.
        
        Returns:
            Optional[Dict[str, Any]]: Task result, if available
        """
        return self._result
    
    @property
    def progress(self) -> float:
        """Get the task progress.
        
        Returns:
            float: Progress value between 0 and 1
        """
        return self._progress
    
    def update_status(self, status: TaskStatus) -> None:
        """Update the task status.
        
        Args:
            status (TaskStatus): New status
        """
        self._status = status
        self._updated_at = datetime.now()
    
    def update_progress(self, progress: float) -> None:
        """Update the task progress.
        
        Args:
            progress (float): Progress value between 0 and 1
        """
        self._progress = max(0.0, min(1.0, progress))  # Clamp to [0, 1]
        self._updated_at = datetime.now()
    
    def set_result(self, result: Dict[str, Any]) -> None:
        """Set the task result.
        
        Args:
            result (Dict[str, Any]): Task result
        """
        self._result = result
        self._updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the task to a dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the task
        """
        return {
            "id": self._id,
            "type": self._type,
            "status": self._status.name,
            "params": self._params,
            "created_at": self._created_at.isoformat(),
            "updated_at": self._updated_at.isoformat(),
            "result": self._result,
            "progress": self._progress
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseTask':
        """Create a task from a dictionary.
        
        Args:
            data (Dict[str, Any]): Dictionary representation of a task
            
        Returns:
            BaseTask: A task instance
        """
        return cls(
            task_id=data.get("id"),
            task_type=data.get("type"),
            params=data.get("params", {}),
            status=TaskStatus[data.get("status", "PENDING")],
            created_at=datetime.fromisoformat(data.get("created_at")) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data.get("updated_at")) if data.get("updated_at") else None,
            result=data.get("result"),
            progress=data.get("progress", 0.0)
        )


class BaseTaskQueue(ITaskQueue, ABC):
    """Base abstract class for task queues.
    
    This class provides a common implementation for the ITaskQueue interface,
    including task validation and result handling.
    """
    
    def add_task(self, params: TaskParams) -> TaskResult:
        """Add a task to the queue.
        
        Args:
            params (TaskParams): Task parameters
            
        Returns:
            TaskResult: Result of the add operation
        """
        try:
            # Validate task parameters
            if not self._validate_task_params(params):
                return TaskResult.error_result("Invalid task parameters")
            
            # Create and store the task
            task = self._create_task(params)
            
            # Return success result
            return TaskResult.success_result(task.id)
        except Exception as e:
            logger.exception(f"Error adding task: {str(e)}")
            return TaskResult.error_result(f"Failed to add task: {str(e)}")
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a task.
        
        Args:
            task_id (str): Task ID
            
        Returns:
            bool: True if the task was cancelled, False otherwise
        """
        task = self.get_task(task_id)
        
        if not task:
            logger.warning(f"Task not found for cancellation: {task_id}")
            return False
        
        if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            logger.warning(f"Cannot cancel task with status {task.status}: {task_id}")
            return False
        
        try:
            task.update_status(TaskStatus.CANCELLED)
            self._update_task(task)
            return True
        except Exception as e:
            logger.exception(f"Error cancelling task: {str(e)}")
            return False
    
    @abstractmethod
    def _validate_task_params(self, params: TaskParams) -> bool:
        """Validate task parameters.
        
        This method should be implemented by subclasses to validate
        task parameters before creating a task.
        
        Args:
            params (TaskParams): Task parameters
            
        Returns:
            bool: True if the parameters are valid, False otherwise
        """
        pass
    
    @abstractmethod
    def _create_task(self, params: TaskParams) -> ITask:
        """Create and store a new task.
        
        This method should be implemented by subclasses to create
        and store a new task based on the provided parameters.
        
        Args:
            params (TaskParams): Task parameters
            
        Returns:
            ITask: The created task
        """
        pass
    
    @abstractmethod
    def _update_task(self, task: ITask) -> None:
        """Update a task in storage.
        
        This method should be implemented by subclasses to update
        a task in the storage backend.
        
        Args:
            task (ITask): Task to update
        """
        pass


class BaseTaskProcessor(ITaskProcessor, ABC):
    """Base abstract class for task processors.
    
    This class provides a common implementation for the ITaskProcessor interface,
    including task type validation and error handling.
    """
    
    def __init__(self):
        """Initialize the base task processor."""
        self._supported_task_types: Set[str] = set()
        self._initialize_supported_task_types()
    
    @abstractmethod
    def _initialize_supported_task_types(self) -> None:
        """Initialize the set of supported task types.
        
        This method should be implemented by subclasses to define which
        task types are supported by this processor.
        """
        pass
    
    def can_process(self, task_type: str) -> bool:
        """Check if this processor can handle the specified task type.
        
        Args:
            task_type (str): Task type
            
        Returns:
            bool: True if this processor can handle the task, False otherwise
        """
        return task_type in self._supported_task_types
    
    def process(self, task: ITask) -> None:
        """Process a task.
        
        Args:
            task (ITask): Task to process
        """
        if not self.can_process(task.type):
            task.update_status(TaskStatus.FAILED)
            task.set_result({"error": f"Unsupported task type: {task.type}"})
            return
        
        try:
            # Update task status to processing
            task.update_status(TaskStatus.PROCESSING)
            
            # Process the task (implemented by subclasses)
            result = self._process_task(task)
            
            # Update task status and result
            task.update_status(TaskStatus.COMPLETED)
            task.set_result(result)
        except Exception as e:
            logger.exception(f"Error processing task {task.id}: {str(e)}")
            task.update_status(TaskStatus.FAILED)
            task.set_result({"error": str(e)})
    
    @abstractmethod
    def _process_task(self, task: ITask) -> Dict[str, Any]:
        """Process a task and return the result.
        
        This method should be implemented by subclasses to perform the
        specific task processing logic.
        
        Args:
            task (ITask): Task to process
            
        Returns:
            Dict[str, Any]: Task result
        """
        pass
