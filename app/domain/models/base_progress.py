"""Base abstract classes for progress tracking in the Video Converter project.

This module provides base implementations of the progress tracking interfaces
defined in app.domain.interfaces.progress. These abstract classes implement
common functionality while leaving specific progress tracking logic to concrete subclasses.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable, Dict, Set
import logging
from datetime import datetime

from app.domain.interfaces.progress import IProgressTracker, IProgressCallback


logger = logging.getLogger(__name__)


class ProgressData:
    """Data class for progress information.
    
    This class encapsulates progress information for a task, including
    start time, current progress, and status messages.
    """
    
    def __init__(self, task_id: str, total_steps: int = 100):
        """Initialize progress data.
        
        Args:
            task_id (str): ID of the task
            total_steps (int, optional): Total number of steps. Defaults to 100.
        """
        self.task_id = task_id
        self.total_steps = max(1, total_steps)  # Ensure at least 1 step
        self.current_step = 0
        self.start_time = datetime.now()
        self.last_update_time = self.start_time
        self.complete_time = None
        self.status = "pending"  # pending, processing, completed, failed
        self.message = None
        self.error = None
    
    @property
    def progress(self) -> float:
        """Get the progress as a value between 0 and 1.
        
        Returns:
            float: Progress value between 0 and 1
        """
        if self.status == "completed":
            return 1.0
        
        return min(1.0, max(0.0, self.current_step / self.total_steps))
    
    @property
    def elapsed_time(self) -> float:
        """Get the elapsed time in seconds.
        
        Returns:
            float: Elapsed time in seconds
        """
        end_time = self.complete_time or datetime.now()
        return (end_time - self.start_time).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the progress data to a dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the progress data
        """
        result = {
            "task_id": self.task_id,
            "progress": self.progress,
            "status": self.status,
            "elapsed_time": self.elapsed_time,
            "total_steps": self.total_steps,
            "current_step": self.current_step,
            "start_time": self.start_time.isoformat(),
            "last_update_time": self.last_update_time.isoformat()
        }
        
        if self.complete_time:
            result["complete_time"] = self.complete_time.isoformat()
            
        if self.message:
            result["message"] = self.message
            
        if self.error:
            result["error"] = self.error
            
        return result


class BaseProgressTracker(IProgressTracker):
    """Base abstract class for progress trackers.
    
    This class provides a common implementation for the IProgressTracker interface,
    including progress data management and callback handling.
    """
    
    def __init__(self):
        """Initialize the base progress tracker."""
        self._progress_data: Dict[str, ProgressData] = {}
        self._callbacks: Dict[str, Set[IProgressCallback]] = {}
    
    def start(self, task_id: str, total_steps: int = 100) -> None:
        """Start tracking progress for a task.
        
        Args:
            task_id (str): ID of the task to track
            total_steps (int, optional): Total number of steps. Defaults to 100.
        """
        self._progress_data[task_id] = ProgressData(task_id, total_steps)
        self._progress_data[task_id].status = "processing"
        self._notify_callbacks(task_id)
        self._persist_progress(task_id)
    
    def update(self, task_id: str, current_step: int, message: Optional[str] = None) -> None:
        """Update progress for a task.
        
        Args:
            task_id (str): ID of the task to update
            current_step (int): Current step number
            message (Optional[str], optional): Progress message. Defaults to None.
        """
        if task_id not in self._progress_data:
            logger.warning(f"Attempting to update progress for unknown task: {task_id}")
            return
        
        progress_data = self._progress_data[task_id]
        
        if progress_data.status not in ["pending", "processing"]:
            logger.warning(f"Attempting to update progress for {progress_data.status} task: {task_id}")
            return
        
        progress_data.current_step = current_step
        progress_data.last_update_time = datetime.now()
        progress_data.message = message
        
        self._notify_callbacks(task_id)
        self._persist_progress(task_id)
    
    def complete(self, task_id: str, message: Optional[str] = None) -> None:
        """Mark a task as complete.
        
        Args:
            task_id (str): ID of the task to complete
            message (Optional[str], optional): Completion message. Defaults to None.
        """
        if task_id not in self._progress_data:
            logger.warning(f"Attempting to complete unknown task: {task_id}")
            return
        
        progress_data = self._progress_data[task_id]
        progress_data.status = "completed"
        progress_data.current_step = progress_data.total_steps
        progress_data.complete_time = datetime.now()
        progress_data.message = message
        
        self._notify_callbacks(task_id, is_complete=True)
        self._persist_progress(task_id)
    
    def fail(self, task_id: str, error: str) -> None:
        """Mark a task as failed.
        
        Args:
            task_id (str): ID of the task that failed
            error (str): Error message
        """
        if task_id not in self._progress_data:
            logger.warning(f"Attempting to fail unknown task: {task_id}")
            return
        
        progress_data = self._progress_data[task_id]
        progress_data.status = "failed"
        progress_data.complete_time = datetime.now()
        progress_data.error = error
        
        self._notify_callbacks(task_id, is_error=True)
        self._persist_progress(task_id)
    
    def get_progress(self, task_id: str) -> Dict[str, Any]:
        """Get the current progress for a task.
        
        Args:
            task_id (str): ID of the task
            
        Returns:
            Dict[str, Any]: Progress information
        """
        if task_id not in self._progress_data:
            return {"task_id": task_id, "error": "Task not found", "status": "unknown"}
        
        return self._progress_data[task_id].to_dict()
    
    def register_callback(self, task_id: str, callback: IProgressCallback) -> None:
        """Register a callback for a task.
        
        Args:
            task_id (str): ID of the task
            callback (IProgressCallback): Callback to register
        """
        if task_id not in self._callbacks:
            self._callbacks[task_id] = set()
        
        self._callbacks[task_id].add(callback)
    
    def unregister_callback(self, task_id: str, callback: IProgressCallback) -> None:
        """Unregister a callback for a task.
        
        Args:
            task_id (str): ID of the task
            callback (IProgressCallback): Callback to unregister
        """
        if task_id in self._callbacks:
            self._callbacks[task_id].discard(callback)
    
    def _notify_callbacks(self, task_id: str, is_complete: bool = False, is_error: bool = False) -> None:
        """Notify callbacks for a task.
        
        Args:
            task_id (str): ID of the task
            is_complete (bool, optional): Whether the task is complete. Defaults to False.
            is_error (bool, optional): Whether the task has failed. Defaults to False.
        """
        if task_id not in self._callbacks:
            return
        
        progress_data = self._progress_data[task_id]
        
        for callback in self._callbacks[task_id]:
            try:
                if is_error and progress_data.error:
                    callback.on_error(progress_data.error)
                elif is_complete:
                    callback.on_complete(progress_data.message)
                else:
                    callback.on_progress(progress_data.progress, progress_data.message)
            except Exception as e:
                logger.exception(f"Error in progress callback: {str(e)}")
    
    @abstractmethod
    def _persist_progress(self, task_id: str) -> None:
        """Persist progress data for a task.
        
        This method should be implemented by subclasses to persist
        progress data to a storage backend.
        
        Args:
            task_id (str): ID of the task
        """
        pass


class BaseProgressCallback(IProgressCallback):
    """Base implementation of the IProgressCallback interface.
    
    This class provides a concrete implementation of the IProgressCallback interface,
    with default implementations for all callback methods.
    """
    
    def on_progress(self, progress: float, message: Optional[str] = None) -> None:
        """Called when progress is updated.
        
        Args:
            progress (float): Progress value between 0 and 1
            message (Optional[str], optional): Progress message. Defaults to None.
        """
        pass  # Default implementation does nothing
    
    def on_complete(self, message: Optional[str] = None) -> None:
        """Called when the operation is complete.
        
        Args:
            message (Optional[str], optional): Completion message. Defaults to None.
        """
        pass  # Default implementation does nothing
    
    def on_error(self, error: str) -> None:
        """Called when an error occurs.
        
        Args:
            error (str): Error message
        """
        pass  # Default implementation does nothing
