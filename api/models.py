"""
Pydantic Models for API Request/Response
"""

from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


# ============================================================================
# Task Models
# ============================================================================

class CreateTaskRequest(BaseModel):
    """Request to create a new task"""
    task_type: str  # "uber_ride" or "shopify_order"
    input_data: Dict[str, Any]  # Task-specific input data

class TaskResponse(BaseModel):
    """Response when creating a new task"""
    task_id: str
    status: str
    type: str
    message: str


class TaskStatusResponse(BaseModel):
    """Response when checking task status"""
    task_id: str
    type: str
    current_status: str
    input_data: Dict[str, Any]
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    retry_count: int
    created_at: str
    updated_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class TaskListResponse(BaseModel):
    """Response for listing multiple tasks"""
    tasks: list[TaskStatusResponse]
    count: int


# ============================================================================
# Uber Models
# ============================================================================

class UberRideRequest(BaseModel):
    from_address: str
    to_address: str


class UberRideResponse(BaseModel):
    success: bool
    message: str
    uber_url: Optional[str] = None


# ============================================================================
# Shopify Models
# ============================================================================

class ShopifySearchRequest(BaseModel):
    query: str
    num_results: Optional[int] = 5


class ShopifySearchResponse(BaseModel):
    success: bool
    results: list[str]
    count: int


class ShopifyOrderRequest(BaseModel):
    product_url: str
    size: str


class ShopifyOrderResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    order_details: Optional[Dict[str, Any]] = None


# ============================================================================
# Coinbase Models
# ============================================================================

class CoinbaseOnrampRequest(BaseModel):
    destination_address: str
    destination_network: str
    purchase_currency: str
    payment_amount: str
    payment_currency: str
    payment_method: str
    country: str
    subdivision: str
    client_ip: str
    redirect_url: str
    partner_user_ref: str


class CoinbaseOnrampResponse(BaseModel):
    success: bool
    onramp_url: Optional[str] = None
    error: Optional[str] = None
    session_data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None

