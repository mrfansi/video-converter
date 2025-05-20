"""Progress tracking interfaces for the Video Converter project.

This module defines the core interfaces for progress tracking operations.
These interfaces follow the Interface Segregation Principle (ISP) by providing
focused interfaces for specific progress tracking operations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable


class IProgressTracker(ABC):
    """Interface for progress trackers.
    
    This interface defines the contract for progress trackers in the system.
    It follows the Interface Segregation Principle by providing a focused interface
    for progress tracking operations.
    """
    
    @abstractmethod
    def start(self, task_id: str, total_steps: int = 100) -> None:
        """Start tracking progress for a task.
        
        Args:
            task_id (str): ID of the task to track
            total_steps (int, optional): Total number of steps. Defaults to 100.
        """
        pass
    
    @abstractmethod
    def update(self, task_id: str, current_step: int, message: Optional[str] = None) -> None:
        """Update progress for a task.
        
        Args:
            task_id (str): ID of the task to update
            current_step (int): Current step number
            message (Optional[str], optional): Progress message. Defaults to None.
        """
        pass
    
    @abstractmethod
    def complete(self, task_id: str, message: Optional[str] = None) -> None:
        """Mark a task as complete.
        
        Args:
            task_id (str): ID of the task to complete
            message (Optional[str], optional): Completion message. Defaults to None.
        """
        pass
    
    @abstractmethod
    def fail(self, task_id: str, error: str) -> None:
        """Mark a task as failed.
        
        Args:
            task_id (str): ID of the task that failed
            error (str): Error message
        """
        pass
    
    @abstractmethod
    def get_progress(self, task_id: str) -> Dict[str, Any]:
        """Get the current progress for a task.
        
        Args:
            task_id (str): ID of the task
            
        Returns:
            Dict[str, Any]: Progress information
        """
        pass


class IProgressCallback(ABC):
    """Interface for progress callbacks.
    
    This interface defines the contract for progress callbacks in the system.
    It follows the Interface Segregation Principle by providing a focused interface
    for progress callback operations.
    """
    
    @abstractmethod
    def on_progress(self, progress: float, message: Optional[str] = None) -> None:
        """Called when progress is updated.
        
        Args:
            progress (float): Progress value between 0 and 1
            message (Optional[str], optional): Progress message. Defaults to None.
        """
        pass
    
    @abstractmethod
    def on_complete(self, message: Optional[str] = None) -> None:
        """Called when the operation is complete.
        
        Args:
            message (Optional[str], optional): Completion message. Defaults to None.
        """
        pass
    
    @abstractmethod
    def on_error(self, error: str) -> None:
        """Called when an error occurs.
        
        Args:
            error (str): Error message
        """
        pass
