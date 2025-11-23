"""
FastAPI Server with Async Task Queue
Combines Uber ride booking and Shopify search/ordering endpoints
All long-running tasks are queued and processed by workers
"""

import sys
import os

# Add parent directory to path for imports (must be before other imports)
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from fastapi import FastAPI, HTTPException
from typing import Optional

# Import models
from api.models import (
    UberRideRequest, ShopifySearchRequest, ShopifyOrderRequest,
    CoinbaseOnrampRequest, CoinbaseOnrampResponse,
    TaskResponse, TaskStatusResponse, TaskListResponse
)

# Import database
from api.database import TaskDatabase

# Import Shopify search (synchronous, no queue needed)
import shopify.shopifysearch as shopify_search_module

# Import Coinbase functionality (synchronous, no queue needed)
import coinbase.onramp as coinbase_onramp

app = FastAPI(
    title="Manual Script API (Async Task Queue)",
    description="API for Uber rides, Shopify search, and Shopify checkout with async task processing",
    version="2.0.0"
)

# ============================================================================
# Uber Endpoints (Task-based)
# ============================================================================

@app.post("/uber/book-ride", response_model=TaskResponse)
async def book_uber_ride(request: UberRideRequest):
    """
    Create an Uber ride booking task
    
    Args:
        from_address: Starting location
        to_address: Destination location
    
    Returns:
        TaskResponse with task_id and status
    """
    try:
        # Create task in database
        task = TaskDatabase.create_task(
            task_type="uber_ride",
            input_data={
                "from_address": request.from_address,
                "to_address": request.to_address
            }
        )
        
        return TaskResponse(
            task_id=task["id"],
            status=task["current_status"],
            type=task["type"],
            message="Uber ride booking task created. Use the task_id to check status."
        )
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error creating task: {str(e)}")

# ============================================================================
# Shopify Endpoints
# ============================================================================

@app.post("/shopify/search")
async def shopify_search(request: ShopifySearchRequest):
    """
    Search for Shopify products using Exa API (synchronous, no queue)
    
    Args:
        query: Search query (e.g., "black tshirt")
        num_results: Number of results to return (default: 5)
    
    Returns:
        ShopifySearchResponse with list of product URLs
    """
    try:
        num_results = request.num_results if request.num_results else 5
        
        print(f"Searching for: {request.query} (limit: {num_results})")
        results = shopify_search_module.search_shopify_products(request.query, num_results=num_results)
        
        if not results:
            return {
                "success": False,
                "results": [],
                "count": 0
            }
        
        # Limit to requested number of results
        limited_results = results[:num_results]
        
        return {
            "success": True,
            "results": limited_results,
            "count": len(limited_results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching Shopify: {str(e)}")


@app.post("/shopify/order", response_model=TaskResponse)
async def shopify_order(request: ShopifyOrderRequest):
    """
    Create a Shopify order task
    
    Args:
        product_url: URL of the Shopify product
        size: Size to order (e.g., "M", "7", "Large")
    
    Returns:
        TaskResponse with task_id and status
    """
    try:
        # Create task in database
        task = TaskDatabase.create_task(
            task_type="shopify_order",
            input_data={
                "product_url": request.product_url,
                "size": request.size
            }
        )
        
        return TaskResponse(
            task_id=task["id"],
            status=task["current_status"],
            type=task["type"],
            message="Shopify order task created. Use the task_id to check status."
        )
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error creating task: {str(e)}")

# ============================================================================
# Coinbase Endpoints (No queue needed - instant)
# ============================================================================

@app.post("/coinbase/onramp", response_model=CoinbaseOnrampResponse)
async def create_coinbase_onramp(request: CoinbaseOnrampRequest):
    """
    Generate a Coinbase onramp URL for crypto purchases
    
    ⚠️ IMPORTANT: Each onramp URL is SINGLE-USE ONLY!
    - Once used to launch Coinbase Onramp, the URL becomes invalid
    - Call this endpoint again to generate a fresh URL for each new transaction
    - Do NOT cache, reuse, or share the generated URLs
    
    Args:
        destination_address: Wallet address to receive crypto
        destination_network: Blockchain network (base, ethereum, polygon, etc.)
        purchase_currency: Crypto to purchase (USDC, ETH, etc.)
        payment_amount: Amount to pay (e.g., "100.00")
        payment_currency: Fiat currency (USD, EUR, etc.)
        payment_method: Payment method (CARD, ACH, etc.)
        country: Two-letter country code
        subdivision: State/province code (optional)
        client_ip: Client IP address (optional)
        redirect_url: URL to redirect after completion (optional)
        partner_user_ref: Partner user reference (optional)
    
    Returns:
        CoinbaseOnrampResponse with onramp URL (single-use only)
    """
    try:
        # Build session config from request (all fields required)
        session_config = {
            "destinationAddress": request.destination_address,
            "destinationNetwork": request.destination_network,
            "purchaseCurrency": request.purchase_currency,
            "paymentAmount": request.payment_amount,
            "paymentCurrency": request.payment_currency,
            "paymentMethod": request.payment_method,
            "country": request.country,
            "subdivision": request.subdivision,
            "clientIp": request.client_ip,
            "redirectUrl": request.redirect_url,
            "partnerUserRef": request.partner_user_ref
        }
        
        print("⚠️ Generating NEW single-use Coinbase onramp URL")
        print(f"Config: {session_config}")
        
        # Generate JWT (fresh token for this request)
        jwt_token = coinbase_onramp.generate_jwt("POST", coinbase_onramp.API_PATH)
        
        # Create onramp session (generates fresh sessionToken)
        session_data = coinbase_onramp.create_onramp_session(jwt_token, session_config)
        
        # Extract onramp URL
        onramp_url = session_data.get('session', {}).get('onrampUrl')
        
        if not onramp_url:
            return CoinbaseOnrampResponse(
                success=False,
                error="Onramp URL not found in response",
                session_data=session_data
            )
        
        print(f"✓ Generated fresh onramp URL (single-use): {onramp_url[:50]}...")
        
        return CoinbaseOnrampResponse(
            success=True,
            onramp_url=onramp_url,
            session_data=session_data,
            message="⚠️ This URL is single-use only. Call this endpoint again to generate a new URL."
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        error_msg = str(e)
        
        # Check if it's the session token reuse error
        if "sessionToken" in error_msg and "already been used" in error_msg:
            error_msg = "Session token already used. This should not happen - a fresh token is generated for each request. Please check your implementation."
        
        return CoinbaseOnrampResponse(
            success=False,
            error=error_msg
        )

# ============================================================================
# Task Management Endpoints
# ============================================================================

@app.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    Get the status of a task by ID
    
    Returns the complete task data including:
    - current_status: pending, processing, completed, or failed
    - result_data: Full JSONB column value from Supabase including:
      - progress: Array of progress updates with timestamps
      - Final result data when completed
    - input_data: Original request parameters
    - Timestamps: created_at, started_at, completed_at
    
    Args:
        task_id: UUID of the task
    
    Returns:
        TaskStatusResponse with complete task data including full result_data column
    """
    try:
        # Get complete task data from Supabase (SELECT *)
        task = TaskDatabase.get_task(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Return complete result_data column as-is from Supabase
        return TaskStatusResponse(
            task_id=task["id"],
            type=task["type"],
            current_status=task["current_status"],
            input_data=task["input_data"],
            result_data=task.get("result_data"),  # Complete JSONB column value
            error_message=task.get("error_message"),
            retry_count=task.get("retry_count", 0),
            created_at=task["created_at"],
            updated_at=task["updated_at"],
            started_at=task.get("started_at"),
            completed_at=task.get("completed_at")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error getting task status: {str(e)}")


@app.get("/tasks", response_model=TaskListResponse)
async def list_tasks(
    status: Optional[str] = None,
    limit: int = 50
):
    """
    List tasks, optionally filtered by status
    
    Args:
        status: Filter by status (pending, processing, completed, failed)
        limit: Maximum number of tasks to return (default: 50)
    
    Returns:
        TaskListResponse with list of tasks
    """
    try:
        if status:
            tasks = TaskDatabase.get_tasks_by_status(status, limit)
        else:
            tasks = TaskDatabase.get_all_tasks(limit)
        
        task_responses = [
            TaskStatusResponse(
                task_id=task["id"],
                type=task["type"],
                current_status=task["current_status"],
                input_data=task["input_data"],
                result_data=task.get("result_data"),
                error_message=task.get("error_message"),
                retry_count=task.get("retry_count", 0),
                created_at=task["created_at"],
                updated_at=task["updated_at"],
                started_at=task.get("started_at"),
                completed_at=task.get("completed_at")
            )
            for task in tasks
        ]
        
        return TaskListResponse(
            tasks=task_responses,
            count=len(task_responses)
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error listing tasks: {str(e)}")

# ============================================================================
# Health Check
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "architecture": "async_task_queue",
        "endpoints": {
            "uber": "/uber/book-ride (task-based)",
            "shopify_search": "/shopify/search (instant)",
            "shopify_order": "/shopify/order (task-based)",
            "coinbase_onramp": "/coinbase/onramp (instant)",
            "task_status": "/tasks/{task_id}",
            "list_tasks": "/tasks"
        }
    }


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Manual Script API",
        "version": "2.0.0",
        "architecture": "Async Task Queue with Supabase",
        "endpoints": {
            "uber_ride": {
                "path": "/uber/book-ride",
                "method": "POST",
                "description": "Create Uber ride booking task",
                "type": "async (returns task_id)"
            },
            "shopify_search": {
                "path": "/shopify/search",
                "method": "POST",
                "description": "Search for Shopify products",
                "type": "synchronous (instant)"
            },
            "shopify_order": {
                "path": "/shopify/order",
                "method": "POST",
                "description": "Create Shopify order task",
                "type": "async (returns task_id)"
            },
            "coinbase_onramp": {
                "path": "/coinbase/onramp",
                "method": "POST",
                "description": "Generate Coinbase onramp URL",
                "type": "synchronous (instant)"
            },
            "task_status": {
                "path": "/tasks/{task_id}",
                "method": "GET",
                "description": "Check task status by ID"
            },
            "list_tasks": {
                "path": "/tasks",
                "method": "GET",
                "description": "List all tasks (optionally filter by status)"
            },
            "health": {
                "path": "/health",
                "method": "GET",
                "description": "Health check"
            }
        },
        "workflow": {
            "1": "Submit task via POST endpoint → Get task_id",
            "2": "Poll GET /tasks/{task_id} to check status",
            "3": "When status is 'completed', result_data contains the output"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
