"""
Background task manager for the FAIR metadata automation system.
Handles asynchronous file processing and metadata generation tasks.
"""

import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional, Set
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Status of background tasks."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BackgroundTask:
    """Represents a background task."""
    task_id: str
    task_type: str
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    progress: float = 0.0
    metadata: Optional[Dict[str, Any]] = None


class BackgroundTaskManager:
    """Manages background tasks for the FAIR system."""

    def __init__(self, max_concurrent_tasks: int = 5):
        """
        Initialize the background task manager.

        Args:
            max_concurrent_tasks: Maximum number of concurrent tasks
        """
        self.max_concurrent_tasks = max_concurrent_tasks
        self.tasks: Dict[str, BackgroundTask] = {}
        self.running_tasks: Set[str] = set()
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.semaphore = asyncio.Semaphore(max_concurrent_tasks)
        self._worker_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()

    async def start(self) -> None:
        """Start the background task manager."""
        if self._worker_task is None or self._worker_task.done():
            self._worker_task = asyncio.create_task(self._worker_loop())
            logger.info("Background task manager started")

    async def stop(self) -> None:
        """Stop the background task manager."""
        self._shutdown_event.set()
        if self._worker_task and not self._worker_task.done():
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        logger.info("Background task manager stopped")

    async def submit_task(
        self,
        task_id: str,
        task_type: str,
        func: Callable,
        *args,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """
        Submit a task for background execution.

        Args:
            task_id: Unique identifier for the task
            task_type: Type of task (e.g., "file_processing", "metadata_generation")
            func: Function to execute
            *args: Arguments for the function
            metadata: Additional metadata for the task
            **kwargs: Keyword arguments for the function

        Returns:
            Task ID
        """
        if task_id in self.tasks:
            raise ValueError(f"Task {task_id} already exists")

        task = BackgroundTask(
            task_id=task_id,
            task_type=task_type,
            status=TaskStatus.PENDING,
            created_at=datetime.now(timezone.utc),
            metadata=metadata or {}
        )

        self.tasks[task_id] = task

        # Add task to queue
        await self.task_queue.put((task_id, func, args, kwargs))

        logger.info(f"Submitted task {task_id} of type {task_type}")
        return task_id

    async def get_task_status(self, task_id: str) -> Optional[BackgroundTask]:
        """
        Get the status of a task.

        Args:
            task_id: Task identifier

        Returns:
            Task status or None if not found
        """
        return self.tasks.get(task_id)

    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a task.

        Args:
            task_id: Task identifier

        Returns:
            True if task was cancelled, False if not found or already completed
        """
        task = self.tasks.get(task_id)
        if not task:
            return False

        if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            return False

        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.now(timezone.utc)

        logger.info(f"Cancelled task {task_id}")
        return True

    async def list_tasks(
        self,
        task_type: Optional[str] = None,
        status: Optional[TaskStatus] = None,
        limit: int = 100
    ) -> List[BackgroundTask]:
        """
        List tasks with optional filtering.

        Args:
            task_type: Filter by task type
            status: Filter by status
            limit: Maximum number of tasks to return

        Returns:
            List of tasks
        """
        tasks = list(self.tasks.values())

        if task_type:
            tasks = [t for t in tasks if t.task_type == task_type]

        if status:
            tasks = [t for t in tasks if t.status == status]

        # Sort by creation time (newest first)
        tasks.sort(key=lambda t: t.created_at, reverse=True)

        return tasks[:limit]

    async def cleanup_old_tasks(self, max_age_hours: int = 24) -> int:
        """
        Clean up old completed tasks.

        Args:
            max_age_hours: Maximum age of tasks to keep

        Returns:
            Number of tasks cleaned up
        """
        cutoff_time = datetime.now(timezone.utc).timestamp() - (max_age_hours * 3600)

        tasks_to_remove = []
        for task_id, task in self.tasks.items():
            if (task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
                and task.created_at.timestamp() < cutoff_time):
                tasks_to_remove.append(task_id)

        for task_id in tasks_to_remove:
            del self.tasks[task_id]

        logger.info(f"Cleaned up {len(tasks_to_remove)} old tasks")
        return len(tasks_to_remove)

    async def _worker_loop(self) -> None:
        """Main worker loop for processing tasks."""
        logger.info("Background task worker started")

        while not self._shutdown_event.is_set():
            try:
                # Wait for a task with timeout
                try:
                    task_id, func, args, kwargs = await asyncio.wait_for(
                        self.task_queue.get(), timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue

                # Check if task was cancelled
                task = self.tasks.get(task_id)
                if not task or task.status == TaskStatus.CANCELLED:
                    continue

                # Acquire semaphore to limit concurrent tasks
                async with self.semaphore:
                    await self._execute_task(task_id, func, args, kwargs)

            except Exception as e:
                logger.error(f"Error in background task worker: {e}")
                await asyncio.sleep(1)  # Brief pause before retrying

        logger.info("Background task worker stopped")

    async def _execute_task(
        self,
        task_id: str,
        func: Callable,
        args: tuple,
        kwargs: dict
    ) -> None:
        """Execute a single task."""
        task = self.tasks.get(task_id)
        if not task:
            return

        try:
            # Update task status
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now(timezone.utc)
            self.running_tasks.add(task_id)

            logger.info(f"Starting task {task_id}")

            # Execute the function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                # Run sync function in thread pool
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, func, *args, **kwargs)

            # Update task completion
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now(timezone.utc)
            task.result = result
            task.progress = 100.0

            logger.info(f"Completed task {task_id}")

        except Exception as e:
            # Update task failure
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now(timezone.utc)
            task.error = str(e)

            logger.error(f"Task {task_id} failed: {e}")

        finally:
            self.running_tasks.discard(task_id)

    async def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the task manager."""
        total_tasks = len(self.tasks)
        running_tasks = len(self.running_tasks)
        pending_tasks = self.task_queue.qsize()

        status_counts = {}
        for task in self.tasks.values():
            status_counts[task.status.value] = status_counts.get(task.status.value, 0) + 1

        return {
            "total_tasks": total_tasks,
            "running_tasks": running_tasks,
            "pending_tasks": pending_tasks,
            "status_counts": status_counts,
            "max_concurrent_tasks": self.max_concurrent_tasks,
        }


# Global background task manager instance
_background_task_manager: Optional[BackgroundTaskManager] = None


def get_background_task_manager() -> BackgroundTaskManager:
    """Get the global background task manager instance."""
    global _background_task_manager
    if _background_task_manager is None:
        _background_task_manager = BackgroundTaskManager()
    return _background_task_manager


async def start_background_tasks() -> None:
    """Start the background task manager."""
    manager = get_background_task_manager()
    await manager.start()


async def stop_background_tasks() -> None:
    """Stop the background task manager."""
    manager = get_background_task_manager()
    await manager.stop()
