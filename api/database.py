"""
Supabase Database Client
Handles all database operations for the task queue
"""

import os
from typing import Optional, Dict, Any, List
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing Supabase credentials in .env file")

# Create Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


class TaskDatabase:
    """Database operations for task management"""
    
    @staticmethod
    def create_task(
        task_type: str,
        input_data: Dict[str, Any],
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Create a new task in the database
        
        Args:
            task_type: Type of task (uber_ride, shopify_order, shopify_search)
            input_data: Input parameters for the task
            max_retries: Maximum number of retry attempts
            
        Returns:
            Created task data including task_id
        """
        task_data = {
            "type": task_type,
            "current_status": "pending",
            "input_data": input_data,
            "max_retries": max_retries,
            "retry_count": 0
        }
        
        response = supabase.table("tasks").insert(task_data).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def get_task(task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a task by ID
        
        Args:
            task_id: UUID of the task
            
        Returns:
            Task data or None if not found
        """
        response = supabase.table("tasks").select("*").eq("id", task_id).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def get_pending_task() -> Optional[Dict[str, Any]]:
        """
        Get the oldest pending task (for worker to process)
        
        Returns:
            Task data or None if no pending tasks
        """
        response = (
            supabase.table("tasks")
            .select("*")
            .eq("current_status", "pending")
            .order("created_at")
            .limit(1)
            .execute()
        )
        return response.data[0] if response.data else None
    
    @staticmethod
    def update_task_status(
        task_id: str,
        status: str,
        result_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        worker_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update task status
        
        Args:
            task_id: UUID of the task
            status: New status (pending, processing, completed, failed)
            result_data: Result data if completed
            error_message: Error message if failed
            worker_id: ID of the worker processing the task
            
        Returns:
            Updated task data
        """
        update_data = {
            "current_status": status
        }
        
        if result_data is not None:
            update_data["result_data"] = result_data
        
        if error_message is not None:
            update_data["error_message"] = error_message
        
        if worker_id is not None:
            update_data["worker_id"] = worker_id
        
        # Set timestamps based on status
        if status == "processing":
            update_data["started_at"] = datetime.utcnow().isoformat()
        elif status in ["completed", "failed"]:
            update_data["completed_at"] = datetime.utcnow().isoformat()
        
        response = (
            supabase.table("tasks")
            .update(update_data)
            .eq("id", task_id)
            .execute()
        )
        return response.data[0] if response.data else None
    
    @staticmethod
    def increment_retry_count(task_id: str) -> Dict[str, Any]:
        """
        Increment the retry count for a task
        
        Args:
            task_id: UUID of the task
            
        Returns:
            Updated task data
        """
        # First get current retry count
        task = TaskDatabase.get_task(task_id)
        if not task:
            return None
        
        new_retry_count = task.get("retry_count", 0) + 1
        
        response = (
            supabase.table("tasks")
            .update({"retry_count": new_retry_count})
            .eq("id", task_id)
            .execute()
        )
        return response.data[0] if response.data else None
    
    @staticmethod
    def get_tasks_by_status(
        status: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get all tasks with a specific status
        
        Args:
            status: Task status to filter by
            limit: Maximum number of tasks to return
            
        Returns:
            List of task data
        """
        response = (
            supabase.table("tasks")
            .select("*")
            .eq("current_status", status)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data if response.data else []
    
    @staticmethod
    def get_all_tasks(limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get all tasks (most recent first)
        
        Args:
            limit: Maximum number of tasks to return
            
        Returns:
            List of task data
        """
        response = (
            supabase.table("tasks")
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data if response.data else []
    
    @staticmethod
    def get_stuck_tasks(minutes: int = 10) -> List[Dict[str, Any]]:
        """
        Get tasks that have been processing for too long (likely stuck)
        
        Args:
            minutes: Number of minutes to consider a task stuck
            
        Returns:
            List of stuck task data
        """
        # Calculate timestamp for stuck tasks
        from datetime import timedelta
        cutoff_time = (datetime.utcnow() - timedelta(minutes=minutes)).isoformat()
        
        response = (
            supabase.table("tasks")
            .select("*")
            .eq("current_status", "processing")
            .lt("updated_at", cutoff_time)
            .execute()
        )
        return response.data if response.data else []
    
    @staticmethod
    def reset_task_to_pending(task_id: str) -> Dict[str, Any]:
        """
        Reset a task back to pending status (for retries)
        
        Args:
            task_id: UUID of the task
            
        Returns:
            Updated task data
        """
        return TaskDatabase.update_task_status(
            task_id=task_id,
            status="pending",
            worker_id=None
        )
    
    @staticmethod
    def add_progress_update(task_id: str, message: str) -> Dict[str, Any]:
        """
        Add a progress update to the task's result_data
        Maintains a list of progress updates with timestamps
        
        Args:
            task_id: UUID of the task
            message: Progress update message
            
        Returns:
            Updated task data
        """
        # Get current task
        task = TaskDatabase.get_task(task_id)
        if not task:
            return None
        
        # Get existing result_data or create new
        result_data = task.get("result_data") or {}
        
        # Get existing progress updates or create new list
        progress = result_data.get("progress", [])
        
        # Add new progress update with timestamp
        progress.append({
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Update result_data
        result_data["progress"] = progress
        
        # Update task in database
        response = (
            supabase.table("tasks")
            .update({"result_data": result_data})
            .eq("id", task_id)
            .execute()
        )
        return response.data[0] if response.data else None

