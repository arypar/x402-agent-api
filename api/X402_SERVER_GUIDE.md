# X402 Payment Protection on API Server

## What's Been Added

Your main API server (`api/server.py`) now requires **0.001 ETH payment** on Base network to create tasks.

### Protected Endpoint

- **`POST /tasks/create`** - Requires payment
  - Cost: 0.001 ETH
  - Network: Base
  - Payment Address: `0xda2964669a27ae905d4b114c52eb63ba2fab6d7f`

### Free Endpoints (No Payment Required)

- `GET /health` - Health check
- `GET /` - API documentation
- `GET /tasks/{task_id}` - Check task status
- `GET /tasks` - List tasks
- `POST /shopify/search` - Search products
- `POST /coinbase/onramp` - Generate onramp URL

---

## How It Works

### 1. Without Payment (First Request)

```bash
curl -X POST http://localhost:8000/tasks/create \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "uber_ride",
    "input_data": {
      "from_address": "123 Main St",
      "to_address": "456 Market St"
    }
  }'
```

**Response: 402 Payment Required**
```json
{
  "amount": "0.001",
  "currency": "ETH",
  "network": "base",
  "recipient": "0xda2964669a27ae905d4b114c52eb63ba2fab6d7f",
  "message": "Payment required to access this endpoint"
}
```

### 2. With Payment (Retry with Proof)

```bash
curl -X POST http://localhost:8000/tasks/create \
  -H "Content-Type: application/json" \
  -H "X-PAYMENT: 0x_transaction_hash_here" \
  -d '{
    "task_type": "uber_ride",
    "input_data": {
      "from_address": "123 Main St",
      "to_address": "456 Market St"
    }
  }'
```

**Response: 200 OK**
```json
{
  "task_id": "uuid-here",
  "status": "pending",
  "type": "uber_ride",
  "message": "Uber ride booking task created."
}
```

---

## Installation

Update your dependencies:

```bash
pip install -r requirements.txt
```

This will install the new `x402` package.

---

## Using with Programmatic Clients

### Option 1: Using x402 SDK

```python
from x402 import X402Client
import os

client = X402Client(
    private_key=os.getenv("PRIVATE_KEY"),
    network="base",
    rpc_url="https://mainnet.base.org"
)

# Payment handled automatically
response = client.post(
    "http://localhost:8000/tasks/create",
    json={
        "task_type": "uber_ride",
        "input_data": {
            "from_address": "123 Main St",
            "to_address": "456 Market St"
        }
    }
)

print(response.json())
```

### Option 2: Using x402-langchain (For AI Agents)

```python
from x402_langchain import create_x402_agent
from langchain_openai import ChatOpenAI

agent = create_x402_agent(
    private_key=os.getenv("PRIVATE_KEY"),
    llm=ChatOpenAI(model="gpt-4"),
    spending_limit_daily=10.0,
    network="base"
)

# Agent automatically pays 0.001 ETH when creating tasks
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
```

### Option 3: Manual Implementation

See `/test/402_client.py` for a complete manual implementation example.

---

## Testing

### 1. Start the Server

```bash
cd /Users/aryanparekh/Downloads/manual-script
python -m api.server
```

Server runs on `http://localhost:8000`

### 2. Test Free Endpoint

```bash
curl http://localhost:8000/health
```

Expected: `200 OK` (no payment required)

### 3. Test Protected Endpoint

```bash
curl -X POST http://localhost:8000/tasks/create \
  -H "Content-Type: application/json" \
  -d '{"task_type": "uber_ride", "input_data": {"from_address": "A", "to_address": "B"}}'
```

Expected: `402 Payment Required` with payment instructions

### 4. Use Programmatic Client

```bash
# Set up your wallet
export PRIVATE_KEY="0x..."

# Run client example
python test/402_client_sdk.py
```

---

## Cost Breakdown

**Per Task Creation:**
- Payment: 0.001 ETH (~$2-3 USD at current prices)
- Gas fees: ~$0.01 (Base network is cheap!)
- **Total: ~$2-3 per task**

**Wallet Requirements:**
- ETH for payment: 0.001 ETH per task
- ETH for gas: ~0.00001 ETH per transaction
- Recommended: Keep at least 0.01 ETH in wallet

---

## Configuration

You can modify the payment settings in `api/server.py`:

```python
app.middleware("http")(
    require_payment(
        price="0.001",  # Change amount here
        pay_to_address="0xda2964669a27ae905d4b114c52eb63ba2fab6d7f",  # Your wallet
        path=["/tasks/create"],  # Endpoints to protect
        network="base",  # Blockchain network
        currency="ETH"  # Payment currency
    )
)
```

### To Protect Additional Endpoints:

```python
path=["/tasks/create", "/shopify/search", "/coinbase/onramp"]
```

### To Use USDC Instead of ETH:

```python
currency="USDC",
price="5.00"  # 5 USDC
```

---

## Security Notes

1. **Payment Address**: `0xda2964669a27ae905d4b114c52eb63ba2fab6d7f` is YOUR wallet
2. **Verify Ownership**: Make sure you control this wallet address
3. **Monitor Payments**: Check your wallet regularly for incoming payments
4. **Gas Fees**: Users pay gas fees in addition to the 0.001 ETH payment

---

## Troubleshooting

### "402 Payment Required" on every request

**Issue:** Client not including payment proof

**Fix:** Use x402 SDK or include `X-PAYMENT` header with transaction hash

### Payment not recognized

**Issue:** Transaction not confirmed or wrong network

**Fix:**
- Wait for transaction confirmation (~2 seconds on Base)
- Verify transaction on [BaseScan](https://basescan.org)
- Ensure using Base network (not Ethereum mainnet)

### Import error: "No module named 'x402'"

**Issue:** x402 package not installed

**Fix:**
```bash
pip install -r requirements.txt
```

---

## Monitoring Payments

Check your wallet balance:

```bash
# Using cast (foundry)
cast balance 0xda2964669a27ae905d4b114c52eb63ba2fab6d7f --rpc-url https://mainnet.base.org

# Or check on BaseScan
# https://basescan.org/address/0xda2964669a27ae905d4b114c52eb63ba2fab6d7f
```

---

## Next Steps

1. ✅ x402 payment protection added to `/tasks/create`
2. Install dependencies: `pip install -r requirements.txt`
3. Test with free endpoints first
4. Set up client wallet with ETH on Base
5. Use programmatic client to create paid tasks
6. Monitor incoming payments in your wallet

**Your API now has built-in monetization! 💰**

