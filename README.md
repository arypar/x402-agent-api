# Manual Script API

**Pay-per-use API with X402 micropayments** 🚀

Automated API for Uber rides, Shopify orders, product search, and Coinbase onramp integration with built-in payment protection.

---

## 🎯 What's This?

An async task-based API that lets you:
- 🚗 **Book Uber rides** programmatically
- 🛍️ **Order Shopify products** automatically  
- 🔍 **Search Shopify stores** instantly
- 💳 **Generate Coinbase onramp URLs** for crypto purchases

**With X402 payment protection:** Pay 0.001 ETH per task creation on Base network.

---

## 💰 Pricing

| Endpoint | Cost | Speed |
|----------|------|-------|
| `POST /tasks/create` | ✅ **0.001 ETH** (~$2-3) | Async |
| `GET /tasks/*` | ❌ **Free** | Instant |
| `POST /shopify/search` | ❌ **Free** | Instant |
| `POST /coinbase/onramp` | ❌ **Free** | Instant |
| `GET /health` | ❌ **Free** | Instant |

**You only pay when creating tasks!**

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start Services

```bash
# Terminal 1: API Server
python -m api.server

# Terminal 2: Worker (for async tasks)
python -m api.worker
```

### 3. Test It

```bash
# Test free endpoint
curl http://localhost:8000/health

# Test protected endpoint (returns 402 Payment Required)
curl -X POST http://localhost:8000/tasks/create \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "uber_ride",
    "input_data": {
      "from_address": "123 Main St, San Francisco, CA",
      "to_address": "456 Market St, San Francisco, CA"
    }
  }'
```

---

## 🔐 Payment Setup

### For Programmatic Access (Recommended)

```python
from x402 import X402Client
import os

# Client automatically handles payments
client = X402Client(
    private_key=os.getenv("PRIVATE_KEY"),
    network="base"
)

# Payment happens automatically!
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

task = response.json()
print(f"Task created: {task['task_id']}")
```

### For AI Agents

```python
from x402_langchain import create_x402_agent
from langchain_openai import ChatOpenAI

agent = create_x402_agent(
    private_key=os.getenv("PRIVATE_KEY"),
    llm=ChatOpenAI(model="gpt-4"),
    spending_limit_daily=10.0,  # Safety limit
    network="base"
)

# Agent autonomously pays when needed
response = agent.fetch("http://localhost:8000/tasks/create", ...)
```

---

## 📚 Documentation

- **[Quick Reference](QUICK_REFERENCE.md)** - Common commands and examples
- **[Full API Docs](API_DOCUMENTATION_V3.md)** - Complete endpoint documentation
- **[X402 Guide](test/X402_GUIDE.md)** - Payment protocol details
- **[Comparison Guide](test/COMPARISON.md)** - Frontend vs programmatic payments

---

## 📁 Project Structure

```
manual-script/
├── api/
│   ├── server.py          # FastAPI server (with x402 protection)
│   ├── worker.py          # Background task worker
│   ├── database.py        # Supabase integration
│   └── models.py          # Pydantic models
├── test/
│   ├── 402test.py         # Simple x402 test server
│   ├── 402_client.py      # Example programmatic client
│   ├── test_commands.sh   # Automated test script
│   └── X402_GUIDE.md      # Payment protocol guide
├── uber/
│   └── uber_api.py        # Uber automation
├── shopify/
│   └── shopifysearch.py   # Shopify search
├── coinbase/
│   └── onramp.py          # Coinbase onramp integration
└── requirements.txt       # Python dependencies
```

---

## 🔧 Configuration

### Payment Settings (in `api/server.py`)

```python
app.middleware("http")(
    require_payment(
        price="0.001",  # 0.001 ETH per task
        pay_to_address="0xda2964669a27ae905d4b114c52eb63ba2fab6d7f",
        path=["/tasks/create"],  # Protected endpoints
        network="base"  # Base mainnet
    )
)
```

### Change Price

Edit `price="0.001"` in `api/server.py` to your desired amount.

### Add More Protected Endpoints

```python
path=["/tasks/create", "/shopify/search", "/other-endpoint"]
```

---

## 🧪 Testing

### Automated Tests

```bash
chmod +x test/test_commands.sh
./test/test_commands.sh
```

### Manual Tests

See [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for curl commands.

---

## 🌐 Endpoints

### Task Management

- `POST /tasks/create` - Create task (✅ **0.001 ETH**)
- `GET /tasks/{task_id}` - Get task status (❌ Free)
- `GET /tasks` - List tasks (❌ Free)

### Instant Operations

- `POST /shopify/search` - Search products (❌ Free)
- `POST /coinbase/onramp` - Generate onramp URL (❌ Free)
- `GET /health` - Health check (❌ Free)

See [API_DOCUMENTATION_V3.md](API_DOCUMENTATION_V3.md) for full details.

---

## 💡 Use Cases

### 1. AI Agent Automation

```python
agent = create_x402_agent(...)
agent.run("Book me an Uber from home to office")
# Agent automatically pays and creates the task
```

### 2. Batch Processing

```python
client = X402Client(...)
for ride in ride_list:
    client.post("/tasks/create", json=ride)
    # Each request: 0.001 ETH
```

### 3. API Integration

```bash
# Other services can call your API
curl -X POST https://your-domain.com/tasks/create \
  -H "X-PAYMENT: 0x_transaction_hash" \
  -d '{"task_type": "uber_ride", ...}'
```

---

## 🛡️ Security

- ✅ Payment verification via blockchain
- ✅ Non-replayable transactions
- ✅ Configurable spending limits (for agents)
- ✅ Environment variables for private keys
- ✅ Supabase backend with RLS

**Never commit private keys!**

```bash
export PRIVATE_KEY="0x..."  # Use env vars
```

---

## 🌍 Networks

| Network | Chain ID | RPC | Use Case |
|---------|----------|-----|----------|
| Base Mainnet | 8453 | `https://mainnet.base.org` | Production |
| Base Sepolia | 84532 | `https://sepolia.base.org` | Testing |

**Recommended:** Use Base mainnet for low gas fees (~$0.01 per tx).

---

## 📊 Cost Analysis

### Per Task Creation

- Payment: 0.001 ETH (~$2-3)
- Gas: ~$0.01 (Base is cheap!)
- **Total: ~$2-3 per task**

### Free Operations

- Status checks: Unlimited
- List tasks: Unlimited  
- Search products: Unlimited
- Generate onramp URLs: Unlimited

---

## 🔍 Monitoring

### Check Your Wallet Balance

```bash
# Via BaseScan
https://basescan.org/address/0xda2964669a27ae905d4b114c52eb63ba2fab6d7f

# Via CLI (requires foundry)
cast balance 0xda2964669a27ae905d4b114c52eb63ba2fab6d7f \
  --rpc-url https://mainnet.base.org
```

### View Tasks

```bash
# All tasks
curl http://localhost:8000/tasks

# Completed tasks
curl "http://localhost:8000/tasks?status=completed"

# Failed tasks
curl "http://localhost:8000/tasks?status=failed"
```

---

## 🐛 Troubleshooting

### "402 Payment Required"

**Issue:** Client not paying  
**Fix:** Use x402 SDK or include `X-PAYMENT` header

### Task Stuck in "pending"

**Issue:** Worker not running  
**Fix:** Start worker: `python -m api.worker`

### Payment Not Recognized

**Issue:** Wrong network or unconfirmed tx  
**Fix:** 
- Use Base network (chain ID 8453)
- Wait 5 seconds for confirmation
- Check tx on BaseScan

See [API_DOCUMENTATION_V3.md](API_DOCUMENTATION_V3.md#troubleshooting) for more.

---

## 🚦 Requirements

### System

- Python 3.10+
- PostgreSQL (via Supabase)
- Playwright browsers

### Wallet

- Funded with ETH on Base
- Private key for signing
- ~0.01 ETH recommended for testing

### Environment Variables

```bash
# Required
export PRIVATE_KEY="0x..."  # Your wallet private key

# Optional (for Supabase integration)
export SUPABASE_URL="https://..."
export SUPABASE_KEY="..."
```

---

## 📦 Dependencies

```txt
fastapi>=0.104.0
uvicorn>=0.24.0
x402>=0.1.0         # Payment protocol
web3>=6.0.0         # Blockchain interaction
supabase>=2.0.0     # Database
browser-use>=0.9.0  # Browser automation
playwright>=1.40.0  # Web automation
```

Full list in [requirements.txt](requirements.txt).

---

## 🎓 Learn More

- [X402 Protocol](https://x402.org) - Payment protocol docs
- [Base Network](https://base.org) - L2 blockchain
- [BaseScan](https://basescan.org) - Block explorer
- [Bridge to Base](https://bridge.base.org) - Transfer ETH

---

## 🤝 Contributing

This is a private automation project. For commercial use, adjust payment rates and security settings accordingly.

---

## 📄 License

Private use only.

---

## 🎉 Summary

**What you get:**
- ✅ Pay-per-use API with built-in payments
- ✅ Async task processing
- ✅ Uber ride automation
- ✅ Shopify order automation
- ✅ Product search (free)
- ✅ Coinbase onramp (free)
- ✅ AI agent compatible
- ✅ Fully programmatic

**Cost:** Only 0.001 ETH (~$2-3) per task creation. Everything else is free!

**Get started:** [QUICK_REFERENCE.md](QUICK_REFERENCE.md)

---

Made with X402 protocol 💳 | Running on Base ⚡ | Powered by FastAPI 🚀

