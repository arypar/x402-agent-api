# Manual Script API Documentation

**Version**: 2.0.0  
**Base URL**: `https://undecorously-uncongestive-cindy.ngrok-free.dev`  
**Architecture**: Async Task Queue with Supabase  

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Task-Based Endpoints](#task-based-endpoints)
   - [Book Uber Ride](#1-book-uber-ride)
   - [Place Shopify Order](#2-place-shopify-order)
4. [Instant Endpoints](#instant-endpoints)
   - [Search Shopify Products](#3-search-shopify-products)
   - [Generate Coinbase Onramp URL](#4-generate-coinbase-onramp-url)
5. [Task Management Endpoints](#task-management-endpoints)
   - [Get Task Status](#5-get-task-status)
   - [List Tasks](#6-list-tasks)
6. [Utility Endpoints](#utility-endpoints)
   - [Health Check](#7-health-check)
   - [API Info](#8-api-info)
7. [Task Status Flow](#task-status-flow)
8. [Progress Tracking](#progress-tracking)
9. [Error Handling](#error-handling)
10. [Rate Limits](#rate-limits)
11. [Implementation Examples](#implementation-examples)

---

## Overview

The Manual Script API provides automated services for:
- 🚗 **Uber Ride Booking** - Automated ride booking with browser automation
- 🛍️ **Shopify Orders** - Automated product checkout and ordering
- 🔍 **Product Search** - Find Shopify products using AI-powered search
- 💰 **Coinbase Onramp** - Generate crypto purchase URLs

### API Types

**Task-Based (Async)**:
- Returns immediately with a `task_id`
- Task processes in background
- Poll status endpoint to check progress
- Used for long-running operations (1-5 minutes)

**Instant (Sync)**:
- Returns result immediately
- No task queue
- Used for quick operations (<5 seconds)

---

## Authentication

Currently, the API does not require authentication. All endpoints are publicly accessible.

> ⚠️ **Security Note**: In production, implement API key authentication or OAuth.

---

## Task-Based Endpoints

These endpoints return a `task_id` immediately. Tasks are processed asynchronously in the background.

### 1. Book Uber Ride

Book an Uber ride from one location to another.

**Endpoint**: `POST /uber/book-ride`

#### Request

```http
POST https://undecorously-uncongestive-cindy.ngrok-free.dev/uber/book-ride
Content-Type: application/json

{
  "from_address": "123 Main St, San Francisco, CA",
  "to_address": "456 Market St, San Francisco, CA"
}
```

**Body Parameters**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `from_address` | string | Yes | Starting location (full address) |
| `to_address` | string | Yes | Destination location (full address) |

#### Response

**Success (202 Accepted)**:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "type": "uber_ride",
  "message": "Uber ride booking task created. Use the task_id to check status."
}
```

**Error (400 Bad Request)**:
```json
{
  "detail": "Field required: from_address"
}
```

**Error (500 Internal Server Error)**:
```json
{
  "detail": "Error creating task: database connection failed"
}
```

#### Task Processing

Average processing time: **2-5 minutes**

Progress updates:
1. Task started by worker-{id}
2. Generating Uber ride URL
3. Opening Uber app
4. Authenticating with Uber
5. Confirming ride details
6. Booking ride
7. Ride booked successfully

#### Example

```bash
curl -X POST "https://undecorously-uncongestive-cindy.ngrok-free.dev/uber/book-ride" \
  -H "Content-Type: application/json" \
  -d '{
    "from_address": "1 Apple Park Way, Cupertino, CA",
    "to_address": "1600 Amphitheatre Parkway, Mountain View, CA"
  }'
```

---

### 2. Place Shopify Order

Automatically place an order on a Shopify store.

**Endpoint**: `POST /shopify/order`

#### Request

```http
POST https://undecorously-uncongestive-cindy.ngrok-free.dev/shopify/order
Content-Type: application/json

{
  "product_url": "https://kith.com/products/hp-p020-051-1",
  "size": "Medium"
}
```

**Body Parameters**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `product_url` | string | Yes | Full URL to Shopify product page |
| `size` | string | Yes | Size to order (e.g., "M", "Medium", "7", "Large") |

#### Response

**Success (202 Accepted)**:
```json
{
  "task_id": "660e8400-e29b-41d4-a716-446655440001",
  "status": "pending",
  "type": "shopify_order",
  "message": "Shopify order task created. Use the task_id to check status."
}
```

**Error (400 Bad Request)**:
```json
{
  "detail": "Field required: product_url"
}
```

#### Task Processing

Average processing time: **1-3 minutes**

Progress updates:
1. Task started by worker-{id}
2. Opening product page
3. Selecting size: {size}
4. Adding product to cart
5. Navigating to checkout
6. Filling shipping information
7. Processing payment
8. Order placed successfully

#### Example

```bash
curl -X POST "https://undecorously-uncongestive-cindy.ngrok-free.dev/shopify/order" \
  -H "Content-Type: application/json" \
  -d '{
    "product_url": "https://kith.com/products/hp-p020-051-1",
    "size": "Medium"
  }'
```

---

## Instant Endpoints

These endpoints return results immediately.

### 3. Search Shopify Products

Search for Shopify products using AI-powered search.

**Endpoint**: `POST /shopify/search`

#### Request

```http
POST https://undecorously-uncongestive-cindy.ngrok-free.dev/shopify/search
Content-Type: application/json

{
  "query": "black leather jacket",
  "num_results": 5
}
```

**Body Parameters**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `query` | string | Yes | - | Search query (e.g., "black tshirt") |
| `num_results` | integer | No | 5 | Number of results to return (1-50) |

#### Response

**Success (200 OK)**:
```json
{
  "success": true,
  "results": [
    "https://store1.com/products/black-leather-jacket",
    "https://store2.com/products/leather-jacket-black",
    "https://store3.com/products/mens-black-jacket"
  ],
  "count": 3
}
```

**No Results (200 OK)**:
```json
{
  "success": false,
  "results": [],
  "count": 0
}
```

**Error (500 Internal Server Error)**:
```json
{
  "detail": "Error searching Shopify: API timeout"
}
```

#### Example

```bash
curl -X POST "https://undecorously-uncongestive-cindy.ngrok-free.dev/shopify/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "black leather jacket",
    "num_results": 10
  }'
```

---

### 4. Generate Coinbase Onramp URL

Generate a single-use Coinbase onramp URL for crypto purchases.

**Endpoint**: `POST /coinbase/onramp`

#### Request

```http
POST https://undecorously-uncongestive-cindy.ngrok-free.dev/coinbase/onramp
Content-Type: application/json

{
  "destination_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
  "destination_network": "ethereum",
  "purchase_currency": "ETH",
  "payment_amount": "100.00",
  "payment_currency": "USD",
  "payment_method": "CARD",
  "country": "US",
  "subdivision": "CA",
  "client_ip": "192.168.1.1",
  "redirect_url": "https://yoursite.com/success",
  "partner_user_ref": "user-123"
}
```

**Body Parameters**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `destination_address` | string | Yes | Wallet address to receive crypto |
| `destination_network` | string | Yes | Blockchain network (ethereum, base, polygon, etc.) |
| `purchase_currency` | string | Yes | Crypto to purchase (ETH, USDC, BTC, etc.) |
| `payment_amount` | string | Yes | Amount to pay (e.g., "100.00") |
| `payment_currency` | string | Yes | Fiat currency (USD, EUR, GBP, etc.) |
| `payment_method` | string | Yes | Payment method (CARD, ACH, etc.) |
| `country` | string | Yes | Two-letter country code (US, UK, etc.) |
| `subdivision` | string | Yes | State/province code (CA, NY, etc.) |
| `client_ip` | string | Yes | Client IP address |
| `redirect_url` | string | Yes | URL to redirect after completion |
| `partner_user_ref` | string | Yes | Your user reference ID |

#### Response

**Success (200 OK)**:
```json
{
  "success": true,
  "onramp_url": "https://pay.coinbase.com/buy/select-asset?sessionToken=abc123...",
  "message": "⚠️ This URL is single-use only. Call this endpoint again to generate a new URL.",
  "session_data": {
    "session": {
      "onrampUrl": "https://pay.coinbase.com/buy/select-asset?sessionToken=abc123...",
      "sessionToken": "abc123..."
    }
  }
}
```

**Error (200 OK with error)**:
```json
{
  "success": false,
  "error": "Invalid destination address",
  "onramp_url": null,
  "session_data": null
}
```

> ⚠️ **IMPORTANT**: Each onramp URL is **SINGLE-USE ONLY**. Once used to launch Coinbase Onramp, the URL becomes invalid. Call this endpoint again to generate a fresh URL for each new transaction.

#### Example

```bash
curl -X POST "https://undecorously-uncongestive-cindy.ngrok-free.dev/coinbase/onramp" \
  -H "Content-Type: application/json" \
  -d '{
    "destination_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    "destination_network": "ethereum",
    "purchase_currency": "ETH",
    "payment_amount": "100.00",
    "payment_currency": "USD",
    "payment_method": "CARD",
    "country": "US",
    "subdivision": "CA",
    "client_ip": "192.168.1.1",
    "redirect_url": "https://yoursite.com/success",
    "partner_user_ref": "user-123"
  }'
```

---

## Task Management Endpoints

### 5. Get Task Status

Check the status and progress of a task.

**Endpoint**: `GET /tasks/{task_id}`

#### Request

```http
GET https://undecorously-uncongestive-cindy.ngrok-free.dev/tasks/550e8400-e29b-41d4-a716-446655440000
```

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `task_id` | string (UUID) | Yes | The task ID returned when creating the task |

#### Response

**Success (200 OK)**:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "type": "shopify_order",
  "current_status": "processing",
  "input_data": {
    "product_url": "https://kith.com/products/hp-p020-051-1",
    "size": "Medium"
  },
  "result_data": {
    "progress": [
      {
        "message": "Task started by worker-1",
        "timestamp": "2025-11-23T10:00:00.123456"
      },
      {
        "message": "Opening product page",
        "timestamp": "2025-11-23T10:00:01.234567"
      },
      {
        "message": "Selecting size: Medium",
        "timestamp": "2025-11-23T10:00:02.345678"
      },
      {
        "message": "Adding product to cart",
        "timestamp": "2025-11-23T10:00:05.456789"
      }
    ]
  },
  "error_message": null,
  "retry_count": 0,
  "created_at": "2025-11-23T10:00:00Z",
  "updated_at": "2025-11-23T10:00:05Z",
  "started_at": "2025-11-23T10:00:00Z",
  "completed_at": null
}
```

**Task Not Found (404 Not Found)**:
```json
{
  "detail": "Task not found"
}
```

#### Status Values

| Status | Description |
|--------|-------------|
| `pending` | Task is queued and waiting to be processed |
| `processing` | Task is currently being executed |
| `completed` | Task finished successfully (check `result_data`) |
| `failed` | Task failed after max retries (check `error_message`) |
| `cancelled` | Task was cancelled |

#### Example

```bash
# Check task status
curl "https://undecorously-uncongestive-cindy.ngrok-free.dev/tasks/550e8400-e29b-41d4-a716-446655440000"

# With jq for pretty output
curl "https://undecorously-uncongestive-cindy.ngrok-free.dev/tasks/550e8400-e29b-41d4-a716-446655440000" | jq .
```

---

### 6. List Tasks

Get a list of all tasks, optionally filtered by status.

**Endpoint**: `GET /tasks`

#### Request

```http
GET https://undecorously-uncongestive-cindy.ngrok-free.dev/tasks?status=completed&limit=10
```

**Query Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `status` | string | No | (all) | Filter by status (pending, processing, completed, failed) |
| `limit` | integer | No | 50 | Maximum number of tasks to return (1-50) |

#### Response

**Success (200 OK)**:
```json
{
  "tasks": [
    {
      "task_id": "550e8400-e29b-41d4-a716-446655440000",
      "type": "shopify_order",
      "current_status": "completed",
      "input_data": {
        "product_url": "https://kith.com/products/item",
        "size": "M"
      },
      "result_data": {
        "success": true,
        "message": "Order placed successfully",
        "order_details": {}
      },
      "error_message": null,
      "retry_count": 0,
      "created_at": "2025-11-23T10:00:00Z",
      "updated_at": "2025-11-23T10:03:00Z",
      "started_at": "2025-11-23T10:00:01Z",
      "completed_at": "2025-11-23T10:03:00Z"
    }
  ],
  "count": 1
}
```

#### Examples

```bash
# Get all tasks
curl "https://undecorously-uncongestive-cindy.ngrok-free.dev/tasks"

# Get only pending tasks
curl "https://undecorously-uncongestive-cindy.ngrok-free.dev/tasks?status=pending"

# Get only completed tasks, limit to 20
curl "https://undecorously-uncongestive-cindy.ngrok-free.dev/tasks?status=completed&limit=20"

# Get only failed tasks
curl "https://undecorously-uncongestive-cindy.ngrok-free.dev/tasks?status=failed"
```

---

## Utility Endpoints

### 7. Health Check

Check if the API is running.

**Endpoint**: `GET /health`

#### Request

```http
GET https://undecorously-uncongestive-cindy.ngrok-free.dev/health
```

#### Response

**Success (200 OK)**:
```json
{
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
```

#### Example

```bash
curl "https://undecorously-uncongestive-cindy.ngrok-free.dev/health"
```

---

### 8. API Info

Get API information and available endpoints.

**Endpoint**: `GET /`

#### Request

```http
GET https://undecorously-uncongestive-cindy.ngrok-free.dev/
```

#### Response

**Success (200 OK)**:
```json
{
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
```

#### Example

```bash
curl "https://undecorously-uncongestive-cindy.ngrok-free.dev/"
```

---

## Task Status Flow

### Task Lifecycle

```
1. CREATE TASK
   ↓
   POST /uber/book-ride or /shopify/order
   ↓
   Returns: task_id

2. TASK QUEUED
   ↓
   Status: "pending"
   ↓
   Task stored in database

3. TASK PICKED UP
   ↓
   Status: "processing"
   ↓
   Worker starts executing
   ↓
   Progress updates in result_data

4. TASK COMPLETE
   ↓
   Status: "completed" or "failed"
   ↓
   result_data contains output
```

### Polling for Status

**Recommended polling interval**: 2-5 seconds

```python
import requests
import time

# 1. Create task
response = requests.post(
    "https://undecorously-uncongestive-cindy.ngrok-free.dev/uber/book-ride",
    json={
        "from_address": "123 Main St, SF",
        "to_address": "456 Market St, SF"
    }
)
task_id = response.json()["task_id"]

# 2. Poll for completion
while True:
    status = requests.get(
        f"https://undecorously-uncongestive-cindy.ngrok-free.dev/tasks/{task_id}"
    ).json()
    
    print(f"Status: {status['current_status']}")
    
    if status["current_status"] in ["completed", "failed"]:
        break
    
    time.sleep(3)  # Wait 3 seconds before checking again

# 3. Get result
if status["current_status"] == "completed":
    print("Success!", status["result_data"])
else:
    print("Failed!", status["error_message"])
```

---

## Progress Tracking

All task-based endpoints provide real-time progress updates in the `result_data.progress` array.

### Progress Format

```json
{
  "result_data": {
    "progress": [
      {
        "message": "Task started by worker-1",
        "timestamp": "2025-11-23T10:00:00.123456"
      },
      {
        "message": "Opening product page",
        "timestamp": "2025-11-23T10:00:01.234567"
      }
    ]
  }
}
```

### Viewing Progress

```bash
# Get task status
curl "https://undecorously-uncongestive-cindy.ngrok-free.dev/tasks/{task_id}"

# Extract just progress with jq
curl "https://undecorously-uncongestive-cindy.ngrok-free.dev/tasks/{task_id}" \
  | jq '.result_data.progress'
```

### Progress Updates by Task Type

**Uber Ride**:
- Task started by worker-{id}
- Generating Uber ride URL
- Opening Uber app
- Authenticating with Uber
- Confirming ride details
- Booking ride
- Ride booked successfully

**Shopify Order**:
- Task started by worker-{id}
- Opening product page
- Selecting size: {size}
- Adding product to cart
- Navigating to checkout
- Filling shipping information
- Processing payment
- Order placed successfully

---

## Error Handling

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success (instant endpoints) |
| 202 | Accepted (task created, will process async) |
| 400 | Bad Request (invalid parameters) |
| 404 | Not Found (task doesn't exist) |
| 500 | Internal Server Error |

### Error Response Format

```json
{
  "detail": "Error description here"
}
```

### Task Failures

When a task fails, check the `error_message` field:

```json
{
  "task_id": "abc-123",
  "current_status": "failed",
  "error_message": "ValueError: Product not found",
  "result_data": {
    "error": "ValueError: Product not found",
    "progress": [
      {
        "message": "Opening product page",
        "timestamp": "2025-11-23T10:00:00Z"
      },
      {
        "message": "Error: Product not found",
        "timestamp": "2025-11-23T10:00:05Z"
      }
    ]
  }
}
```

### Retry Logic

- Tasks automatically retry up to **3 times** on failure
- Check `retry_count` field to see current attempt
- After max retries, task status becomes `failed`

---

## Rate Limits

Currently, there are no enforced rate limits. However, recommended limits:

- **Task creation**: 10 requests/minute
- **Status checks**: 20 requests/minute
- **Search**: 30 requests/minute

> ⚠️ Excessive requests may result in temporary blocking in the future.

---

## Implementation Examples

### Python

#### Create Task and Wait for Completion

```python
import requests
import time

BASE_URL = "https://undecorously-uncongestive-cindy.ngrok-free.dev"

def create_uber_ride(from_addr, to_addr):
    # Create task
    response = requests.post(
        f"{BASE_URL}/uber/book-ride",
        json={
            "from_address": from_addr,
            "to_address": to_addr
        }
    )
    response.raise_for_status()
    
    task_id = response.json()["task_id"]
    print(f"Task created: {task_id}")
    
    # Poll for completion
    while True:
        status_response = requests.get(f"{BASE_URL}/tasks/{task_id}")
        status_response.raise_for_status()
        task = status_response.json()
        
        current_status = task["current_status"]
        print(f"Status: {current_status}")
        
        # Show progress
        progress = task.get("result_data", {}).get("progress", [])
        if progress:
            latest = progress[-1]
            print(f"  Latest: {latest['message']}")
        
        if current_status == "completed":
            return task["result_data"]
        elif current_status == "failed":
            raise Exception(f"Task failed: {task['error_message']}")
        
        time.sleep(3)

# Usage
result = create_uber_ride(
    "123 Main St, San Francisco, CA",
    "456 Market St, San Francisco, CA"
)
print("Success!", result)
```

#### Place Shopify Order

```python
def place_shopify_order(product_url, size):
    response = requests.post(
        f"{BASE_URL}/shopify/order",
        json={
            "product_url": product_url,
            "size": size
        }
    )
    response.raise_for_status()
    
    task_id = response.json()["task_id"]
    
    # Poll for completion
    while True:
        task = requests.get(f"{BASE_URL}/tasks/{task_id}").json()
        
        if task["current_status"] == "completed":
            return task["result_data"]
        elif task["current_status"] == "failed":
            raise Exception(task["error_message"])
        
        time.sleep(3)

# Usage
order = place_shopify_order(
    "https://kith.com/products/hp-p020-051-1",
    "Medium"
)
```

#### Search Products

```python
def search_products(query, num_results=5):
    response = requests.post(
        f"{BASE_URL}/shopify/search",
        json={
            "query": query,
            "num_results": num_results
        }
    )
    response.raise_for_status()
    
    data = response.json()
    if data["success"]:
        return data["results"]
    else:
        return []

# Usage
products = search_products("black leather jacket", num_results=10)
for url in products:
    print(url)
```

### JavaScript/TypeScript

```javascript
const BASE_URL = "https://undecorously-uncongestive-cindy.ngrok-free.dev";

async function createUberRide(fromAddress, toAddress) {
  // Create task
  const createResponse = await fetch(`${BASE_URL}/uber/book-ride`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      from_address: fromAddress,
      to_address: toAddress
    })
  });
  
  const { task_id } = await createResponse.json();
  console.log(`Task created: ${task_id}`);
  
  // Poll for completion
  while (true) {
    const statusResponse = await fetch(`${BASE_URL}/tasks/${task_id}`);
    const task = await statusResponse.json();
    
    console.log(`Status: ${task.current_status}`);
    
    // Show progress
    const progress = task.result_data?.progress || [];
    if (progress.length > 0) {
      const latest = progress[progress.length - 1];
      console.log(`  Latest: ${latest.message}`);
    }
    
    if (task.current_status === 'completed') {
      return task.result_data;
    } else if (task.current_status === 'failed') {
      throw new Error(`Task failed: ${task.error_message}`);
    }
    
    // Wait 3 seconds before checking again
    await new Promise(resolve => setTimeout(resolve, 3000));
  }
}

// Usage
const result = await createUberRide(
  "123 Main St, San Francisco, CA",
  "456 Market St, San Francisco, CA"
);
console.log("Success!", result);
```

### cURL

```bash
#!/bin/bash

BASE_URL="https://undecorously-uncongestive-cindy.ngrok-free.dev"

# Create Uber ride task
RESPONSE=$(curl -s -X POST "$BASE_URL/uber/book-ride" \
  -H "Content-Type: application/json" \
  -d '{
    "from_address": "123 Main St, SF",
    "to_address": "456 Market St, SF"
  }')

TASK_ID=$(echo $RESPONSE | jq -r '.task_id')
echo "Task created: $TASK_ID"

# Poll for completion
while true; do
  STATUS=$(curl -s "$BASE_URL/tasks/$TASK_ID")
  CURRENT_STATUS=$(echo $STATUS | jq -r '.current_status')
  
  echo "Status: $CURRENT_STATUS"
  
  if [ "$CURRENT_STATUS" = "completed" ] || [ "$CURRENT_STATUS" = "failed" ]; then
    echo $STATUS | jq .
    break
  fi
  
  sleep 3
done
```

---

## Interactive API Documentation

**Swagger UI**: `https://undecorously-uncongestive-cindy.ngrok-free.dev/docs`  
**ReDoc**: `https://undecorously-uncongestive-cindy.ngrok-free.dev/redoc`

These provide interactive documentation where you can test endpoints directly in your browser.

---

## Quick Reference

### Base URL
```
https://undecorously-uncongestive-cindy.ngrok-free.dev
```

### Task-Based Endpoints (Async)
```bash
POST /uber/book-ride          # Book Uber ride
POST /shopify/order           # Place Shopify order
```

### Instant Endpoints (Sync)
```bash
POST /shopify/search          # Search products
POST /coinbase/onramp         # Generate onramp URL
```

### Task Management
```bash
GET  /tasks/{task_id}         # Get task status
GET  /tasks                   # List tasks
```

### Utility
```bash
GET  /health                  # Health check
GET  /                        # API info
```

---

## Support

For issues or questions:
1. Check the [interactive docs](https://undecorously-uncongestive-cindy.ngrok-free.dev/docs)
2. Review error messages in `error_message` field
3. Check task progress in `result_data.progress`

---

**API Version**: 2.0.0  
**Last Updated**: November 23, 2025  
**Base URL**: https://undecorously-uncongestive-cindy.ngrok-free.dev

