import os
import time
import json
import logging
import threading
from typing import Dict, Any, List, Optional, Callable
from queue import Queue, Empty
from dataclasses import dataclass, field
from enum import Enum

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task status enum"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Task:
    """Task data structure"""

    id: str
    task_type: str
    params: Dict[str, Any]
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    progress: Dict[str, Any] = field(
        default_factory=lambda: {
            "percent": 0,
            "current_step": "",
            "total_steps": 0,
            "completed_steps": 0,
            "details": "",
        }
    )
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary"""
        return {
            "id": self.id,
            "task_type": self.task_type,
            "params": self.params,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "progress": self.progress,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """Create task from dictionary"""
        status_value = data.get("status", TaskStatus.PENDING.value)
        status = (
            TaskStatus(status_value)
            if isinstance(status_value, str)
            else TaskStatus.PENDING
        )

        # Get progress or use default
        progress = data.get(
            "progress",
            {
                "percent": 0,
                "current_step": "",
                "total_steps": 0,
                "completed_steps": 0,
                "details": "",
            },
        )

        return cls(
            id=data["id"],
            task_type=data["task_type"],
            params=data["params"],
            status=status,
            result=data.get("result"),
            error=data.get("error"),
            progress=progress,
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time()),
        )


class TaskQueue:
    """Simple in-memory task queue"""

    def __init__(self, workers: int = 2):
        """Initialize task queue"""
        self.queue: Queue[str] = Queue()
        self.tasks: Dict[str, Task] = {}
        self.workers = workers
        self.worker_threads: List[threading.Thread] = []
        self.handlers: Dict[str, Callable] = {}
        self.running = False

        # Create storage directory for task data
        self.storage_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "data", "tasks"
        )
        os.makedirs(self.storage_dir, exist_ok=True)

        # Load existing tasks from storage
        self._load_tasks()

    def register_handler(self, task_type: str, handler: Callable) -> None:
        """Register a handler for a task type"""
        self.handlers[task_type] = handler
        logger.info(f"Registered handler for task type: {task_type}")

    def start(self) -> None:
        """Start the task queue workers"""
        if self.running:
            return

        self.running = True

        # Start worker threads
        for i in range(self.workers):
            thread = threading.Thread(target=self._worker, daemon=True)
            thread.start()
            self.worker_threads.append(thread)

        logger.info(f"Started {self.workers} worker threads")

    def stop(self) -> None:
        """Stop the task queue workers"""
        self.running = False

        # Wait for worker threads to finish
        for thread in self.worker_threads:
            if thread.is_alive():
                thread.join(timeout=1.0)

        self.worker_threads = []
        logger.info("Stopped all worker threads")

    def add_task(self, task_id: str, task_type: str, params: Dict[str, Any]) -> Task:
        """Add a task to the queue"""
        task = Task(id=task_id, task_type=task_type, params=params)
        self.tasks[task_id] = task
        self.queue.put(task_id)

        # Save task to storage
        self._save_task(task)

        logger.info(f"Added task {task_id} of type {task_type} to queue")
        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID"""
        return self.tasks.get(task_id)

    def update_progress(
        self,
        task_id: str,
        current_step: str,
        percent: Optional[int] = None,
        total_steps: Optional[int] = None,
        completed_steps: Optional[int] = None,
        details: Optional[str] = None,
    ) -> None:
        """
        Update the progress of a task

        Args:
            task_id (str): ID of the task to update
            current_step (str): Current processing step
            percent (int, optional): Overall completion percentage (0-100)
            total_steps (int, optional): Total number of steps in the process
            completed_steps (int, optional): Number of completed steps
            details (str, optional): Additional details about the current step
        """
        task = self.tasks.get(task_id)
        if not task:
            logger.warning(f"Cannot update progress: Task {task_id} not found")
            return

        # Update progress information
        task.progress["current_step"] = current_step

        if percent is not None:
            task.progress["percent"] = max(0, min(100, percent))  # Ensure 0-100 range

        if total_steps is not None:
            task.progress["total_steps"] = total_steps

        if completed_steps is not None:
            task.progress["completed_steps"] = completed_steps
            # Auto-calculate percentage if not provided
            if percent is None and task.progress["total_steps"] > 0:
                task.progress["percent"] = int(
                    (completed_steps / task.progress["total_steps"]) * 100
                )

        if details is not None:
            task.progress["details"] = details

        # Update timestamp
        task.updated_at = time.time()

        # Save task to storage
        self._save_task(task)

        logger.info(
            f"Updated progress for task {task_id}: {current_step} ({task.progress['percent']}%)"
        )

    def _worker(self) -> None:
        """Worker thread function"""
        while self.running:
            try:
                # Get a task from the queue with timeout
                try:
                    task_id = self.queue.get(timeout=1.0)
                except Empty:
                    continue

                # Get the task
                task = self.tasks.get(task_id)
                if not task:
                    logger.warning(f"Task {task_id} not found")
                    self.queue.task_done()
                    continue

                # Update task status
                task.status = TaskStatus.PROCESSING
                task.updated_at = time.time()
                self._save_task(task)

                # Get the handler for the task type
                handler = self.handlers.get(task.task_type)
                if not handler:
                    logger.warning(f"No handler for task type {task.task_type}")
                    task.status = TaskStatus.FAILED
                    task.error = f"No handler for task type {task.task_type}"
                    task.updated_at = time.time()
                    self._save_task(task)
                    self.queue.task_done()
                    continue

                # Execute the handler
                try:
                    logger.info(f"Executing task {task_id} of type {task.task_type}")
                    result = handler(**task.params)

                    # Update task status
                    task.status = TaskStatus.COMPLETED
                    task.result = result
                    task.updated_at = time.time()
                    logger.info(f"Task {task_id} completed successfully")
                except Exception as e:
                    logger.exception(f"Error executing task {task_id}: {str(e)}")
                    task.status = TaskStatus.FAILED
                    task.error = str(e)
                    task.updated_at = time.time()

                # Save task to storage
                self._save_task(task)

                # Mark task as done
                self.queue.task_done()

            except Exception as e:
                logger.exception(f"Error in worker thread: {str(e)}")

    def _save_task(self, task: Task) -> None:
        """Save task to storage"""
        try:
            task_path = os.path.join(self.storage_dir, f"{task.id}.json")
            with open(task_path, "w") as f:
                json.dump(task.to_dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Error saving task {task.id}: {str(e)}")

    def _load_tasks(self) -> None:
        """Load tasks from storage"""
        try:
            # Get all task files
            task_files = [
                f for f in os.listdir(self.storage_dir) if f.endswith(".json")
            ]

            # Load each task
            for task_file in task_files:
                try:
                    task_path = os.path.join(self.storage_dir, task_file)
                    with open(task_path, "r") as f:
                        task_data = json.load(f)

                    task = Task.from_dict(task_data)
                    self.tasks[task.id] = task

                    # Add pending tasks back to the queue
                    if (
                        task.status == TaskStatus.PENDING
                        or task.status == TaskStatus.PROCESSING
                    ):
                        self.queue.put(task.id)

                except Exception as e:
                    logger.error(f"Error loading task from {task_file}: {str(e)}")

            logger.info(f"Loaded {len(self.tasks)} tasks from storage")

        except Exception as e:
            logger.error(f"Error loading tasks: {str(e)}")


# Singleton instance
task_queue = TaskQueue()
