# Manual Script API v3.0 - Documentation

**Pay-per-use API with X402 Protocol**

---

## Table of Contents

- [Overview](#overview)
- [Payment Protection (X402)](#payment-protection-x402)
- [Endpoints](#endpoints)
  - [Protected Endpoints (Require Payment)](#protected-endpoints-require-payment)
  - [Free Endpoints](#free-endpoints)
- [Getting Started](#getting-started)
- [Client Examples](#client-examples)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

---

## Overview

This API provides:
- **Uber Ride Booking** (async tasks)
- **Shopify Product Search** (instant)
- **Shopify Order Placement** (async tasks)
- **Coinbase Onramp Generation** (instant)

**Architecture:** Async task queue with Supabase backend

**Base URL:** `http://localhost:8000`

**Payment:** X402 protocol on Base network

---

## Payment Protection (X402)

### What is X402?

X402 is a micropayment protocol that enables **pay-per-call API access**. Clients make blockchain payments programmatically to access protected endpoints.

### Payment Details

- **Protected Endpoint:** `POST /tasks/create`
- **Cost:** 0.001 ETH (~$2-3 USD)
- **Network:** Base (Ethereum L2)
- **Recipient:** `0xda2964669a27ae905d4b114c52eb63ba2fab6d7f`

### How It Works

```
1. Client → API: POST /tasks/create
   ↓
2. API → Client: 402 Payment Required
   {
     "amount": "0.001",
     "currency": "ETH",
     "network": "base",
     "recipient": "0xda2964669a27ae905d4b114c52eb63ba2fab6d7f"
   }
   ↓
3. Client: Makes 0.001 ETH payment on Base
   ↓
4. Client → API: POST /tasks/create
   Headers: { "X-PAYMENT": "0x_transaction_hash..." }
   ↓
5. API → Client: 200 OK + Task Created
```

---

## Endpoints

### Protected Endpoints (Require Payment)

#### 1. Create Task

**Endpoint:** `POST /tasks/create`  
**Payment Required:** ✅ 0.001 ETH  
**Description:** Create a new async task (Uber ride or Shopify order)

**Request Body:**

```json
{
  "task_type": "uber_ride" | "shopify_order",
  "input_data": {
    // Task-specific data
  }
}
```

**Task Types:**

##### Uber Ride

```json
{
  "task_type": "uber_ride",
  "input_data": {
    "from_address": "123 Main St, San Francisco, CA",
    "to_address": "456 Market St, San Francisco, CA"
  }
}
```

##### Shopify Order

```json
{
  "task_type": "shopify_order",
  "input_data": {
    "product_url": "https://kith.com/products/item",
    "size": "Medium"
  }
}
```

**Response (200 OK):**

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "type": "uber_ride",
  "message": "Uber ride booking task created. Use the task_id to check status."
}
```

**Response (402 Payment Required):**

```json
{
  "detail": "Payment required",
  "amount": "0.001",
  "currency": "ETH",
  "network": "base",
  "recipient": "0xda2964669a27ae905d4b114c52eb63ba2fab6d7f"
}
```

---

### Free Endpoints

#### 2. Health Check

**Endpoint:** `GET /health`  
**Payment Required:** ❌ Free  
**Description:** Check API health status

**Response:**

```json
{
  "status": "healthy",
  "version": "2.0.0",
  "architecture": "async_task_queue"
}
```

**Curl:**

```bash
curl http://localhost:8000/health
```

---

#### 3. Get Task Status

**Endpoint:** `GET /tasks/{task_id}`  
**Payment Required:** ❌ Free  
**Description:** Check status and progress of a task

**Response:**

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "type": "uber_ride",
  "current_status": "processing",
  "input_data": {
    "from_address": "123 Main St",
    "to_address": "456 Market St"
  },
  "result_data": {
    "progress": [
      {
        "timestamp": "2024-01-01T12:00:00",
        "message": "Booking Uber ride..."
      }
    ]
  },
  "created_at": "2024-01-01T12:00:00",
  "updated_at": "2024-01-01T12:00:05"
}
```

**Task Statuses:**
- `pending` - Task created, waiting for worker
- `processing` - Worker is processing the task
- `completed` - Task finished successfully
- `failed` - Task failed with error

**Curl:**

```bash
curl http://localhost:8000/tasks/550e8400-e29b-41d4-a716-446655440000
```

---

#### 4. List Tasks

**Endpoint:** `GET /tasks`  
**Payment Required:** ❌ Free  
**Description:** List all tasks (optionally filter by status)

**Query Parameters:**
- `status` (optional): Filter by status (pending, processing, completed, failed)
- `limit` (optional): Max number of results (default: 50)

**Response:**

```json
{
  "tasks": [
    {
      "task_id": "550e8400-e29b-41d4-a716-446655440000",
      "type": "uber_ride",
      "current_status": "completed",
      "created_at": "2024-01-01T12:00:00"
    }
  ],
  "count": 1
}
```

**Curl:**

```bash
# List all tasks
curl http://localhost:8000/tasks

# Filter by status
curl "http://localhost:8000/tasks?status=completed&limit=10"
```

---

#### 5. Shopify Search

**Endpoint:** `POST /shopify/search`  
**Payment Required:** ❌ Free  
**Description:** Search for Shopify products using Exa API (instant results)

**Request Body:**

```json
{
  "query": "black tshirt",
  "num_results": 5
}
```

**Response:**

```json
{
  "success": true,
  "results": [
    {
      "url": "https://kith.com/products/black-tee",
      "title": "Black T-Shirt",
      "description": "Premium cotton tee"
    }
  ],
  "count": 5
}
```

**Curl:**

```bash
curl -X POST http://localhost:8000/shopify/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "black tshirt",
    "num_results": 5
  }'
```

---

#### 6. Coinbase Onramp

**Endpoint:** `POST /coinbase/onramp`  
**Payment Required:** ❌ Free  
**Description:** Generate a Coinbase onramp URL for crypto purchases

**⚠️ Important:** Each URL is single-use only!

**Request Body:**

```json
{
  "destination_address": "0x...",
  "destination_network": "base",
  "purchase_currency": "USDC",
  "payment_amount": "100.00",
  "payment_currency": "USD",
  "payment_method": "CARD",
  "country": "US",
  "subdivision": "CA",
  "client_ip": "1.2.3.4",
  "redirect_url": "https://yoursite.com/success",
  "partner_user_ref": "user123"
}
```

**Response:**

```json
{
  "success": true,
  "onramp_url": "https://pay.coinbase.com/buy/select-asset?sessionToken=...",
  "message": "⚠️ This URL is single-use only. Call this endpoint again to generate a new URL."
}
```

**Curl:**

```bash
curl -X POST http://localhost:8000/coinbase/onramp \
  -H "Content-Type: application/json" \
  -d '{
    "destination_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    "destination_network": "base",
    "purchase_currency": "USDC",
    "payment_amount": "100.00",
    "payment_currency": "USD",
    "payment_method": "CARD",
    "country": "US"
  }'
```

---

## Getting Started

### 1. Installation

```bash
cd /Users/aryanparekh/Downloads/manual-script
pip install -r requirements.txt
```

### 2. Start the Server

```bash
python -m api.server
```

Server runs on: `http://localhost:8000`

### 3. Start the Worker (for async tasks)

```bash
python -m api.worker
```

The worker processes tasks from the queue.

---

## Client Examples

### Option 1: Using cURL (Manual Payment)

```bash
# Step 1: Try to create task (will get 402)
curl -X POST http://localhost:8000/tasks/create \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "uber_ride",
    "input_data": {
      "from_address": "123 Main St",
      "to_address": "456 Market St"
    }
  }'

# Step 2: Make payment on Base network (0.001 ETH)
# Use MetaMask, web3.py, or other wallet to send payment

# Step 3: Retry with payment proof
curl -X POST http://localhost:8000/tasks/create \
  -H "Content-Type: application/json" \
  -H "X-PAYMENT: 0x_your_transaction_hash_here" \
  -d '{
    "task_type": "uber_ride",
    "input_data": {
      "from_address": "123 Main St",
      "to_address": "456 Market St"
    }
  }'
```

---

### Option 2: Using x402 Python SDK (Automatic Payment)

```python
from x402 import X402Client
import os

# Initialize client with your wallet
client = X402Client(
    private_key=os.getenv("PRIVATE_KEY"),
    network="base",
    rpc_url="https://mainnet.base.org"
)

# Payment is handled automatically!
response = client.post(
    "http://localhost:8000/tasks/create",
    json={
        "task_type": "uber_ride",
        "input_data": {
            "from_address": "123 Main St, San Francisco, CA",
            "to_address": "456 Market St, San Francisco, CA"
        }
    }
)

task = response.json()
print(f"Task created: {task['task_id']}")

# Check status (free endpoint)
status = client.get(f"http://localhost:8000/tasks/{task['task_id']}")
print(status.json())
```

---

### Option 3: Using x402-langchain (For AI Agents)

```python
from x402_langchain import create_x402_agent
from langchain_openai import ChatOpenAI
import os

# Create agent with payment capabilities
agent = create_x402_agent(
    private_key=os.getenv("PRIVATE_KEY"),
    llm=ChatOpenAI(model="gpt-4"),
    spending_limit_daily=10.0,  # Max $10/day in payments
    network="base"
)

# Agent automatically handles payments
response = agent.fetch(
    "http://localhost:8000/tasks/create",
    method="POST",
    json={
        "task_type": "uber_ride",
        "input_data": {
            "from_address": "123 Main St",
            "to_address": "456 Market St"
        }
    }
)

print(f"Task created: {response}")
```

---

### Option 4: Using Python requests (Manual Payment)

```python
import requests
from web3 import Web3
from eth_account import Account
import os

# Setup
base_url = "http://localhost:8000"
w3 = Web3(Web3.HTTPProvider("https://mainnet.base.org"))
account = Account.from_key(os.getenv("PRIVATE_KEY"))

# Step 1: Try to create task
response = requests.post(
    f"{base_url}/tasks/create",
    json={
        "task_type": "uber_ride",
        "input_data": {
            "from_address": "123 Main St",
            "to_address": "456 Market St"
        }
    }
)

if response.status_code == 402:
    payment_info = response.json()
    print(f"Payment required: {payment_info}")
    
    # Step 2: Make payment
    tx = {
        'to': w3.to_checksum_address(payment_info['recipient']),
        'value': w3.to_wei(float(payment_info['amount']), 'ether'),
        'gas': 21000,
        'gasPrice': w3.eth.gas_price,
        'nonce': w3.eth.get_transaction_count(account.address),
        'chainId': 8453  # Base mainnet
    }
    
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    
    print(f"Payment sent: {tx_hash.hex()}")
    
    # Wait for confirmation
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"Confirmed in block: {receipt['blockNumber']}")
    
    # Step 3: Retry with payment proof
    response = requests.post(
        f"{base_url}/tasks/create",
        headers={"X-PAYMENT": tx_hash.hex()},
        json={
            "task_type": "uber_ride",
            "input_data": {
                "from_address": "123 Main St",
                "to_address": "456 Market St"
            }
        }
    )
    
    task = response.json()
    print(f"Task created: {task}")
```

---

## Testing

### Quick Test Script

```bash
# Make script executable
chmod +x test/test_commands.sh

# Run all tests
./test/test_commands.sh
```

### Manual Tests

**1. Test free endpoint:**

```bash
curl http://localhost:8000/health
# Expected: 200 OK
```

**2. Test protected endpoint:**

```bash
curl -X POST http://localhost:8000/tasks/create \
  -H "Content-Type: application/json" \
  -d '{"task_type": "uber_ride", "input_data": {"from_address": "A", "to_address": "B"}}'
# Expected: 402 Payment Required
```

**3. Test Shopify search (free):**

```bash
curl -X POST http://localhost:8000/shopify/search \
  -H "Content-Type: application/json" \
  -d '{"query": "black tshirt", "num_results": 3}'
# Expected: 200 OK with results
```

---

## Troubleshooting

### "402 Payment Required" on every request

**Issue:** Client not including payment proof

**Fix:** 
- Use x402 SDK for automatic payment
- Or include `X-PAYMENT` header with transaction hash
- Ensure payment transaction is confirmed on blockchain

---

### Payment not recognized

**Issue:** Transaction not confirmed or wrong network

**Fix:**
- Wait 2-5 seconds for transaction confirmation
- Verify transaction on [BaseScan](https://basescan.org)
- Ensure using Base network (chain ID 8453)
- Check payment sent to correct address: `0xda2964669a27ae905d4b114c52eb63ba2fab6d7f`

---

### "Insufficient funds" error

**Issue:** Not enough ETH in wallet

**Fix:**
- Add ETH to your wallet for payment (0.001 ETH per task)
- Add ETH for gas fees (~0.00001 ETH per transaction)
- Bridge ETH to Base: https://bridge.base.org

---

### Task stuck in "pending" status

**Issue:** Worker not running

**Fix:**
```bash
# Start the worker
python -m api.worker
```

---

### Import error: "No module named 'x402'"

**Issue:** x402 package not installed

**Fix:**
```bash
pip install -r requirements.txt
```

---

## Cost Breakdown

### Per Task Creation:
- **Payment:** 0.001 ETH (~$2-3 USD at current prices)
- **Gas fee:** ~$0.01 (Base network is very cheap)
- **Total:** ~$2-3 per task

### Free Operations:
- Check task status: **Free**
- List tasks: **Free**
- Shopify search: **Free**
- Coinbase onramp: **Free**
- Health check: **Free**

**You only pay for task creation!**

---

## API Workflow

```
┌─────────────────────────────────────────────────┐
│                   CLIENT                        │
└───────────────────┬─────────────────────────────┘
                    │
                    │ POST /tasks/create
                    ▼
┌─────────────────────────────────────────────────┐
│              X402 MIDDLEWARE                    │
│  ├─ Check for X-PAYMENT header                  │
│  ├─ Validate payment on blockchain              │
│  └─ Allow/Deny request                          │
└───────────────────┬─────────────────────────────┘
                    │
                    │ 200 OK / 402 Payment Required
                    ▼
┌─────────────────────────────────────────────────┐
│              FASTAPI SERVER                     │
│  ├─ Create task in Supabase                     │
│  └─ Return task_id                              │
└───────────────────┬─────────────────────────────┘
                    │
                    │ Task in database
                    ▼
┌─────────────────────────────────────────────────┐
│              WORKER PROCESS                     │
│  ├─ Poll for pending tasks                      │
│  ├─ Execute task (Uber/Shopify)                 │
│  └─ Update task status                          │
└─────────────────────────────────────────────────┘
```

---

## Summary

- **Payment Protection:** Only `/tasks/create` requires payment (0.001 ETH)
- **Free Endpoints:** Status checks, search, listing all free
- **Network:** Base (cheap gas fees)
- **Integration:** Use x402 SDK for automatic payment handling
- **AI Agents:** Use x402-langchain for autonomous payments

**Your API is now monetized with pay-per-use pricing! 💰**

---

## Support

For issues or questions:
1. Check the troubleshooting section
2. Verify your wallet has sufficient ETH
3. Ensure Base network is selected
4. Check transaction status on BaseScan

## Links

- [X402 Documentation](https://x402.org)
- [Base Network](https://base.org)
- [BaseScan Explorer](https://basescan.org)
- [Bridge to Base](https://bridge.base.org)

