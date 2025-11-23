"""
Background Worker for Task Processing
Continuously polls Supabase for pending tasks and processes them
"""

import sys
import os
import asyncio
import traceback
from datetime import datetime
import socket

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from api.database import TaskDatabase

# Import task handlers
import uber.uber_api as uber_api
import shopify.main as shopify_main_module


# Custom exception for payment declined errors
class PaymentDeclinedException(Exception):
    """Exception raised when payment is declined - should not retry"""
    pass


class TaskWorker:
    """Background worker for processing tasks from the queue"""
    
    def __init__(self, worker_id: str = None, poll_interval: int = 5, max_concurrent_tasks: int = 5):
        """
        Initialize the worker
        
        Args:
            worker_id: Unique identifier for this worker (defaults to hostname)
            poll_interval: How often to check for new tasks (in seconds)
            max_concurrent_tasks: Maximum number of tasks to process concurrently
        """
        self.worker_id = worker_id or f"worker-{socket.gethostname()}-{os.getpid()}"
        self.poll_interval = poll_interval
        self.max_concurrent_tasks = max_concurrent_tasks
        self.running = False
        self.active_tasks = set()  # Track active task coroutines
        
        print(f"[{self.worker_id}] Worker initialized")
        print(f"[{self.worker_id}] Poll interval: {self.poll_interval} seconds")
        print(f"[{self.worker_id}] Max concurrent tasks: {self.max_concurrent_tasks}")
    
    async def process_uber_ride(self, task_id: str, input_data: dict) -> dict:
        """
        Process an Uber ride booking task
        
        Args:
            task_id: UUID of the task
            input_data: Task input data (from_address, to_address)
            
        Returns:
            Result data
        """
        print(f"[{self.worker_id}] Processing Uber ride task: {task_id}")
        print(f"[{self.worker_id}] From: {input_data['from_address']}")
        print(f"[{self.worker_id}] To: {input_data['to_address']}")
        
        try:
            # Initial progress update
            TaskDatabase.add_progress_update(task_id, "Starting Uber ride booking")
            
            # Step 1: Generate Uber URL with task_id for real-time updates
            uber_url = await uber_api.generate_uber_url(
                input_data['from_address'],
                input_data['to_address'],
                task_id=task_id
            )
            print(f"[{self.worker_id}] Generated URL: {uber_url}")
            
            # Step 2: Navigate to URL and book ride with task_id for real-time updates
            print(f"[{self.worker_id}] Starting browser automation...")
            
            success = await uber_api.navigate_to_auth(uber_url, task_id=task_id)
            
            if not success:
                TaskDatabase.add_progress_update(task_id, "❌ Payment declined")
                return {
                    "success": False,
                    "message": "Payment was declined or booking failed",
                    "uber_url": uber_url
                }
            
            return {
                "success": True,
                "message": "Ride booking process completed",
                "uber_url": uber_url
            }
            
        except Exception as e:
            print(f"[{self.worker_id}] Error processing Uber task: {str(e)}")
            TaskDatabase.add_progress_update(task_id, f"Error: {str(e)}")
            traceback.print_exc()
            raise
    
    async def process_shopify_order(self, task_id: str, input_data: dict) -> dict:
        """
        Process a Shopify order task
        
        Args:
            task_id: UUID of the task
            input_data: Task input data (product_url, size)
            
        Returns:
            Result data
        """
        print(f"[{self.worker_id}] Processing Shopify order task: {task_id}")
        print(f"[{self.worker_id}] Product: {input_data['product_url']}")
        print(f"[{self.worker_id}] Size: {input_data['size']}")
        
        try:
            # Initial progress update
            TaskDatabase.add_progress_update(task_id, "Starting checkout process")
            
            # Call the shopify_checkout function with task_id for real-time updates
            result = await shopify_main_module.shopify_checkout(
                input_data['product_url'],
                input_data['size'],
                task_id=task_id
            )
            
            # Check if the checkout was successful
            if result.get('success'):
                # Check if order was confirmed (Checked Out status)
                if result.get('status') == 'Checked Out':
                    TaskDatabase.add_progress_update(task_id, "✅ Order confirmed - Checked Out")
                    return {
                        "success": True,
                        "status": "Checked Out",
                        "message": "Order confirmed successfully",
                        "order_details": result
                    }
                else:
                    TaskDatabase.add_progress_update(task_id, "Order processing complete")
                    return {
                        "success": True,
                        "message": "Order placed successfully",
                        "order_details": result
                    }
            else:
                # Check if payment was declined - this should fail immediately without retry
                error = result.get('error', 'Unknown error occurred')
                if error == 'Payment Declined':
                    TaskDatabase.add_progress_update(task_id, "Payment Declined")
                    # Raise a special exception to mark as failed without retry
                    raise PaymentDeclinedException(result.get('message', 'Your card was declined'))
                
                TaskDatabase.add_progress_update(task_id, f"Checkout failed: {error}")
                return {
                    "success": False,
                    "error": error,
                    "order_details": result
                }
                
        except PaymentDeclinedException as e:
            # Payment declined - don't retry, fail immediately
            print(f"[{self.worker_id}] Payment declined for Shopify task: {str(e)}")
            TaskDatabase.add_progress_update(task_id, f"Payment Declined: {str(e)}")
            raise  # Re-raise to be caught by process_task
        except Exception as e:
            print(f"[{self.worker_id}] Error processing Shopify task: {str(e)}")
            TaskDatabase.add_progress_update(task_id, f"Error: {str(e)}")
            traceback.print_exc()
            raise
    
    async def process_task(self, task: dict):
        """
        Process a single task based on its type
        
        Args:
            task: Task data from database
        """
        task_id = task["id"]
        task_type = task["type"]
        input_data = task["input_data"]
        
        print(f"\n[{self.worker_id}] ========================================")
        print(f"[{self.worker_id}] Processing task: {task_id}")
        print(f"[{self.worker_id}] Type: {task_type}")
        print(f"[{self.worker_id}] Created at: {task['created_at']}")
        print(f"[{self.worker_id}] Active tasks: {len(self.active_tasks)}/{self.max_concurrent_tasks}")
        print(f"[{self.worker_id}] ========================================")
        
        # Add initial progress update
        TaskDatabase.add_progress_update(task_id, f"Task started by {self.worker_id}")
        
        try:
            # Route to appropriate handler
            if task_type == "uber_ride":
                result = await self.process_uber_ride(task_id, input_data)
            elif task_type == "shopify_order":
                result = await self.process_shopify_order(task_id, input_data)
            else:
                raise ValueError(f"Unknown task type: {task_type}")
            
            # Mark task as completed
            TaskDatabase.update_task_status(
                task_id=task_id,
                status="completed",
                result_data=result
            )
            
            print(f"[{self.worker_id}] ✓ Task {task_id} completed successfully")
            
        except PaymentDeclinedException as e:
            # Payment declined - mark as failed immediately without retry
            error_message = f"Payment Declined: {str(e)}"
            print(f"[{self.worker_id}] ✗ Task {task_id} failed - Payment Declined")
            
            TaskDatabase.update_task_status(
                task_id=task_id,
                status="failed",
                error_message=error_message,
                result_data={"error": "Payment Declined", "message": str(e)}
            )
            
        except Exception as e:
            error_message = f"{type(e).__name__}: {str(e)}"
            print(f"[{self.worker_id}] ✗ Task {task_id} failed: {error_message}")
            
            # Increment retry count
            TaskDatabase.increment_retry_count(task_id)
            
            # Get updated task to check retry count
            updated_task = TaskDatabase.get_task(task_id)
            retry_count = updated_task.get("retry_count", 0)
            max_retries = updated_task.get("max_retries", 3)
            
            if retry_count < max_retries:
                # Reset to pending for retry
                print(f"[{self.worker_id}] Retry {retry_count}/{max_retries} - resetting to pending")
                TaskDatabase.reset_task_to_pending(task_id)
            else:
                # Max retries reached, mark as failed
                print(f"[{self.worker_id}] Max retries reached - marking as failed")
                TaskDatabase.update_task_status(
                    task_id=task_id,
                    status="failed",
                    error_message=error_message,
                    result_data={"error": error_message}
                )
    
    async def task_wrapper(self, task: dict):
        """
        Wrapper around process_task to track active tasks
        
        Args:
            task: Task data from database
        """
        task_ref = asyncio.current_task()
        self.active_tasks.add(task_ref)
        
        try:
            await self.process_task(task)
        finally:
            self.active_tasks.discard(task_ref)
    
    async def run(self):
        """Main worker loop - continuously polls for tasks and processes them concurrently"""
        self.running = True
        
        print(f"\n[{self.worker_id}] ========================================")
        print(f"[{self.worker_id}] Worker started at {datetime.utcnow().isoformat()}")
        print(f"[{self.worker_id}] Concurrent task processing enabled (max: {self.max_concurrent_tasks})")
        print(f"[{self.worker_id}] ========================================\n")
        
        while self.running:
            try:
                # Clean up completed tasks
                self.active_tasks = {task for task in self.active_tasks if not task.done()}
                
                # Check if we can process more tasks
                if len(self.active_tasks) < self.max_concurrent_tasks:
                    # Get next pending task
                    task = TaskDatabase.get_pending_task()
                    
                    if task:
                        # Immediately mark as processing to prevent race condition
                        task_id = task["id"]
                        TaskDatabase.update_task_status(
                            task_id=task_id,
                            status="processing",
                            worker_id=self.worker_id
                        )
                        
                        # Start processing the task in the background (non-blocking)
                        print(f"[{self.worker_id}] Starting new task (active: {len(self.active_tasks)}/{self.max_concurrent_tasks})")
                        asyncio.create_task(self.task_wrapper(task))
                        # Give event loop a chance to run the spawned tasks
                        await asyncio.sleep(0.1)
                    else:
                        # No tasks available, wait before checking again
                        if len(self.active_tasks) == 0:
                            print(f"[{self.worker_id}] No pending tasks. Waiting {self.poll_interval}s...")
                        await asyncio.sleep(self.poll_interval)
                else:
                    # At max capacity, wait a bit before checking again
                    await asyncio.sleep(1)
                    
            except KeyboardInterrupt:
                print(f"\n[{self.worker_id}] Received interrupt signal. Shutting down...")
                self.running = False
                break
                
            except Exception as e:
                print(f"[{self.worker_id}] Unexpected error in main loop: {str(e)}")
                traceback.print_exc()
                print(f"[{self.worker_id}] Waiting {self.poll_interval}s before retry...")
                await asyncio.sleep(self.poll_interval)
        
        # Wait for active tasks to complete before shutting down
        if self.active_tasks:
            print(f"[{self.worker_id}] Waiting for {len(self.active_tasks)} active tasks to complete...")
            await asyncio.gather(*self.active_tasks, return_exceptions=True)
        
        print(f"[{self.worker_id}] Worker stopped at {datetime.utcnow().isoformat()}")
    
    def stop(self):
        """Stop the worker gracefully"""
        print(f"[{self.worker_id}] Stopping worker...")
        self.running = False


async def check_stuck_tasks(worker: TaskWorker):
    """
    Periodically check for stuck tasks and reset them
    
    Args:
        worker: TaskWorker instance
    """
    while worker.running:
        try:
            # Check every 5 minutes
            await asyncio.sleep(300)
            
            # Get tasks stuck for more than 10 minutes
            stuck_tasks = TaskDatabase.get_stuck_tasks(minutes=10)
            
            if stuck_tasks:
                print(f"[{worker.worker_id}] Found {len(stuck_tasks)} stuck tasks")
                
                for task in stuck_tasks:
                    task_id = task["id"]
                    print(f"[{worker.worker_id}] Resetting stuck task: {task_id}")
                    
                    # Increment retry count and reset to pending
                    TaskDatabase.increment_retry_count(task_id)
                    updated_task = TaskDatabase.get_task(task_id)
                    
                    retry_count = updated_task.get("retry_count", 0)
                    max_retries = updated_task.get("max_retries", 3)
                    
                    if retry_count < max_retries:
                        TaskDatabase.reset_task_to_pending(task_id)
                    else:
                        TaskDatabase.update_task_status(
                            task_id=task_id,
                            status="failed",
                            error_message="Task stuck in processing state (timeout)"
                        )
                        
        except Exception as e:
            print(f"[{worker.worker_id}] Error checking stuck tasks: {str(e)}")


async def main():
    """Main entry point for the worker"""
    # Get configuration from environment or use defaults
    worker_id = os.getenv("WORKER_ID")
    poll_interval = int(os.getenv("POLL_INTERVAL", "5"))
    max_concurrent_tasks = int(os.getenv("MAX_CONCURRENT_TASKS", "5"))
    
    # Create and start worker
    worker = TaskWorker(
        worker_id=worker_id,
        poll_interval=poll_interval,
        max_concurrent_tasks=max_concurrent_tasks
    )
    
    # Start stuck task checker in background
    asyncio.create_task(check_stuck_tasks(worker))
    
    try:
        # Run the worker
        await worker.run()
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
        worker.stop()


if __name__ == "__main__":
    # Run the worker
    asyncio.run(main())

