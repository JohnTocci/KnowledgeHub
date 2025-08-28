"""
Background processing and async task management for KnowledgeHub.
"""
import asyncio
import threading
import time
import uuid
from typing import Callable, Any, Dict, Optional
from dataclasses import dataclass
from enum import Enum
import streamlit as st


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskResult:
    task_id: str
    status: TaskStatus
    result: Any = None
    error: Exception = None
    progress: float = 0.0
    message: str = ""
    start_time: float = 0.0
    end_time: float = 0.0


class BackgroundTaskManager:
    """Manages background tasks with progress tracking."""
    
    def __init__(self):
        self.tasks: Dict[str, TaskResult] = {}
        self._executor = None
    
    def submit_task(self, func: Callable, *args, **kwargs) -> str:
        """Submit a task for background execution."""
        task_id = str(uuid.uuid4())
        
        # Create task result
        task_result = TaskResult(
            task_id=task_id,
            status=TaskStatus.PENDING,
            start_time=time.time()
        )
        self.tasks[task_id] = task_result
        
        # Start task in background thread
        thread = threading.Thread(
            target=self._run_task,
            args=(task_id, func, args, kwargs),
            daemon=True
        )
        thread.start()
        
        return task_id
    
    def _run_task(self, task_id: str, func: Callable, args: tuple, kwargs: dict):
        """Run task in background thread."""
        task_result = self.tasks[task_id]
        
        try:
            task_result.status = TaskStatus.RUNNING
            task_result.message = "Starting task..."
            
            # Execute the function
            result = func(*args, **kwargs)
            
            task_result.result = result
            task_result.status = TaskStatus.COMPLETED
            task_result.message = "Task completed successfully"
            task_result.end_time = time.time()
            
        except Exception as e:
            task_result.error = e
            task_result.status = TaskStatus.FAILED
            task_result.message = f"Task failed: {str(e)}"
            task_result.end_time = time.time()
    
    def get_task_status(self, task_id: str) -> Optional[TaskResult]:
        """Get current status of a task."""
        return self.tasks.get(task_id)
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending or running task."""
        if task_id in self.tasks:
            task_result = self.tasks[task_id]
            if task_result.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
                task_result.status = TaskStatus.CANCELLED
                task_result.message = "Task cancelled by user"
                task_result.end_time = time.time()
                return True
        return False
    
    def cleanup_completed_tasks(self, max_age_hours: int = 24):
        """Remove old completed tasks."""
        current_time = time.time()
        to_remove = []
        
        for task_id, task_result in self.tasks.items():
            if (task_result.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED] and
                task_result.end_time > 0 and
                (current_time - task_result.end_time) > (max_age_hours * 3600)):
                to_remove.append(task_id)
        
        for task_id in to_remove:
            del self.tasks[task_id]


# Global task manager instance
task_manager = BackgroundTaskManager()


def create_progress_callback(task_id: str):
    """Create a progress callback for a task."""
    def update_progress(progress: float, message: str = ""):
        if task_id in task_manager.tasks:
            task_manager.tasks[task_id].progress = progress
            if message:
                task_manager.tasks[task_id].message = message
    
    return update_progress


def display_task_progress(task_id: str, container=None) -> bool:
    """Display task progress in Streamlit. Returns True if task is complete."""
    if container is None:
        container = st
    
    task_result = task_manager.get_task_status(task_id)
    if not task_result:
        container.error("Task not found")
        return True
    
    # Display progress based on status
    if task_result.status == TaskStatus.PENDING:
        container.info("⏳ Task is pending...")
        return False
    
    elif task_result.status == TaskStatus.RUNNING:
        # Show progress bar and message
        progress_bar = container.progress(task_result.progress)
        status_text = container.empty()
        status_text.text(task_result.message or "Processing...")
        
        # Add cancel button
        if container.button("⏹️ Cancel Task", key=f"cancel_{task_id}"):
            task_manager.cancel_task(task_id)
            container.warning("Task cancellation requested...")
        
        return False
    
    elif task_result.status == TaskStatus.COMPLETED:
        container.success("✅ Task completed successfully!")
        duration = task_result.end_time - task_result.start_time
        container.info(f"Processing time: {duration:.1f} seconds")
        return True
    
    elif task_result.status == TaskStatus.FAILED:
        container.error(f"❌ Task failed: {task_result.message}")
        if task_result.error:
            with container.expander("Error Details"):
                container.code(str(task_result.error))
        return True
    
    elif task_result.status == TaskStatus.CANCELLED:
        container.warning("⏹️ Task was cancelled")
        return True
    
    return True


class StreamlitProgressCallback:
    """Progress callback that works with Streamlit components."""
    
    def __init__(self, task_id: str, progress_bar=None, status_text=None):
        self.task_id = task_id
        self.progress_bar = progress_bar
        self.status_text = status_text
    
    def update(self, progress: float, message: str = ""):
        """Update progress and message."""
        # Update task manager
        if self.task_id in task_manager.tasks:
            task_manager.tasks[self.task_id].progress = progress
            if message:
                task_manager.tasks[self.task_id].message = message
        
        # Update Streamlit components if provided
        if self.progress_bar:
            self.progress_bar.progress(progress)
        
        if self.status_text and message:
            self.status_text.text(message)


def run_with_progress(func: Callable, task_name: str = "Processing", 
                     show_progress: bool = True) -> Any:
    """
    Run a function with progress tracking in Streamlit.
    
    Args:
        func: Function to run (should accept a progress_callback parameter)
        task_name: Name to display for the task
        show_progress: Whether to show progress UI
    
    Returns:
        The result of the function or None if failed
    """
    if not show_progress:
        # Run synchronously without progress tracking
        try:
            return func(lambda p, m="": None)  # Dummy progress callback
        except Exception as e:
            st.error(f"Error: {str(e)}")
            return None
    
    # For now, run synchronously with progress UI since background tasks are complex in Streamlit
    progress_bar = st.progress(0.0)
    status_text = st.empty()
    
    def progress_callback(progress: float, message: str = ""):
        progress_bar.progress(progress)
        status_text.text(message or f"{task_name}...")
    
    try:
        result = func(progress_callback)
        progress_bar.progress(1.0)
        status_text.text("Complete!")
        time.sleep(0.5)  # Brief pause to show completion
        progress_bar.empty()
        status_text.empty()
        return result
    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        raise e