# X402 Payment Protocol Guide

## Overview

X402 is a micropayment protocol that enables **pay-per-call APIs**. Instead of requiring a frontend wallet UI, agents can programmatically handle payments using blockchain transactions.

---

## How It Works

### Flow Diagram

```
1. Agent → API: GET /premium
   ↓
2. API → Agent: 402 Payment Required
   {
     "amount": "0.01",
     "currency": "USDC",
     "recipient": "0x...",
     "network": "base"
   }
   ↓
3. Agent: Makes blockchain payment
   ↓
4. Agent → API: GET /premium
   Headers: { "X-PAYMENT": "0x_tx_hash..." }
   ↓
5. API → Agent: 200 OK + Premium Data
```

### Key Components

- **Server**: FastAPI with `x402` middleware
- **Client**: Agent with wallet that can sign transactions
- **Blockchain**: Base, Ethereum, Solana (for payment settlement)
- **Currency**: USDC, ETH, or other tokens

---

## Server Setup (Already Done in 402test.py)

```python
from fastapi import FastAPI
from x402.fastapi.middleware import require_payment

app = FastAPI()

# Protect endpoints with payment
app.middleware("http")(
    require_payment(
        price="0.01",  # 0.01 USDC per request
        pay_to_address="0x71C7656EC7ab88b098defB751B7401B5f6d8976F",
        path=["/premium", "/expensive"]  # Only these need payment
    )
)

@app.get("/health")
async def health():
    return {"status": "ok"}  # Free endpoint

@app.get("/premium")
async def premium():
    return {"data": "premium content"}  # Requires payment
```

**Run the server:**
```bash
python test/402test.py
```

---

## Client Setup (3 Options)

### Option 1: Using x402 SDK (Recommended for Production)

```bash
pip install x402 web3
```

```python
from x402 import X402Client

# Initialize client with your wallet
client = X402Client(
    private_key=os.getenv("PRIVATE_KEY"),
    network="base",
    rpc_url="https://mainnet.base.org"
)

# Payment is handled automatically
response = client.get("http://localhost:8001/premium")
print(response.json())
```

### Option 2: Using x402-langchain (For AI Agents)

```bash
pip install x402-langchain
```

```python
from x402_langchain import create_x402_agent
from langchain_openai import ChatOpenAI

# Create agent with payment capabilities
agent = create_x402_agent(
    private_key=os.getenv("PRIVATE_KEY"),
    llm=ChatOpenAI(model="gpt-4"),
    spending_limit_daily=10.0,  # Safety limit
    network="base"
)

# Agent automatically pays when needed
response = agent.fetch("http://localhost:8001/premium")
```

### Option 3: Manual Implementation (Full Control)

See `402_client.py` and `402_client_sdk.py` for complete examples.

**Key steps:**
1. Detect 402 response
2. Parse payment instructions
3. Sign & submit blockchain transaction
4. Retry with `X-PAYMENT` header containing tx hash

---

## Requirements

### Server Side
```bash
pip install fastapi uvicorn x402
```

Or if using the openlibx402 variant:
```bash
pip install openlibx402-fastapi
```

### Client Side

**For basic client:**
```bash
pip install requests web3 eth-account
```

**For x402 SDK:**
```bash
pip install x402 web3
```

**For AI agents:**
```bash
pip install x402-langchain langchain-openai
```

---

## Blockchain Setup

### 1. Get a Wallet

You need a wallet with:
- **Private key** (for signing transactions)
- **Funded with USDC** (for payments)
- **Funded with ETH** (for gas fees on Base/Ethereum)

```python
from eth_account import Account

# Create new wallet
account = Account.create()
print(f"Address: {account.address}")
print(f"Private Key: {account.key.hex()}")
```

⚠️ **Security:** Never commit private keys. Use environment variables:
```bash
export PRIVATE_KEY="0x..."
```

### 2. Fund Your Wallet

**Base Network (Recommended - Cheapest):**
1. Get Base ETH for gas: [Bridge ETH to Base](https://bridge.base.org)
2. Get USDC: Buy on [Uniswap Base](https://app.uniswap.org)

**Testnet (For Development):**
1. Use Base Sepolia testnet
2. Get free testnet ETH: [Base Sepolia Faucet](https://www.coinbase.com/faucets/base-ethereum-sepolia-faucet)
3. Get testnet USDC from faucet

### 3. Network Configuration

```python
networks = {
    "base": {
        "rpc": "https://mainnet.base.org",
        "chain_id": 8453,
        "usdc": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
    },
    "base-sepolia": {
        "rpc": "https://sepolia.base.org", 
        "chain_id": 84532,
        "usdc": "0x036CbD53842c5426634e7929541eC2318f3dCF7e"
    },
    "ethereum": {
        "rpc": "https://eth.llamarpc.com",
        "chain_id": 1,
        "usdc": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
    }
}
```

---

## Testing

### 1. Start the Server

```bash
python test/402test.py
```

Server runs on `http://localhost:8001`

### 2. Test Free Endpoint

```bash
curl http://localhost:8001/health
```

Expected: `200 OK`

### 3. Test Payment-Required Endpoint

```bash
curl http://localhost:8001/premium
```

Expected: `402 Payment Required` with payment instructions

### 4. Run Client

```bash
# Using mock client (for testing structure)
python test/402_client.py

# Using SDK (requires setup)
python test/402_client_sdk.py
```

---

## Production Checklist

- [ ] Server has valid `pay_to_address` (your wallet)
- [ ] Client wallet is funded with USDC + gas
- [ ] Private key stored in environment variable (not hardcoded)
- [ ] Using mainnet (not testnet) for production
- [ ] Payment amounts configured correctly
- [ ] Error handling for failed payments
- [ ] Logging for payment transactions
- [ ] Rate limiting to prevent abuse
- [ ] Spending limits configured for agents

---

## Troubleshooting

### Client gets 402 but can't parse payment info

**Issue:** Response format doesn't match expected structure

**Fix:** Check the actual response structure:
```python
response = requests.get("http://localhost:8001/premium")
print(response.status_code)
print(response.json())
```

### Payment sent but still getting 402

**Issue:** Payment proof not recognized by server

**Possible causes:**
1. Transaction not confirmed on blockchain
2. Wrong network (testnet vs mainnet)
3. Insufficient gas or failed transaction
4. Server's facilitator not seeing payment

**Fix:** 
- Wait for transaction confirmation
- Verify transaction on block explorer
- Check server logs for payment verification

### Out of gas / Transaction failed

**Issue:** Not enough ETH for gas fees

**Fix:** Fund wallet with more native ETH for gas

### "Insufficient funds" when paying

**Issue:** Not enough USDC in wallet

**Fix:** Add USDC to your wallet

---

## Cost Estimates

**Base Network (Cheapest):**
- Payment: 0.01 USDC (configured)
- Gas: ~$0.01 per transaction
- **Total per call: ~$0.02**

**Ethereum Mainnet:**
- Payment: 0.01 USDC (configured)
- Gas: ~$2-10 per transaction (high!)
- **Total per call: ~$2-10**

**Recommendation:** Use Base for much lower costs!

---

## Resources

- [x402 Documentation](https://x402.org)
- [Base Network Docs](https://docs.base.org)
- [Web3.py Documentation](https://web3py.readthedocs.io)
- [Coinbase Wallet](https://www.coinbase.com/wallet)

---

## Quick Start Example

```python
# 1. Set up environment
export PRIVATE_KEY="0x..."

# 2. Start server
python test/402test.py

# 3. In another terminal, run client
python test/402_client.py
```

That's it! Your agent can now programmatically pay for API access.

