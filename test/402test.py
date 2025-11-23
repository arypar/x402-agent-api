from fastapi import FastAPI
from x402.fastapi.middleware import require_payment  # from x402 SDK

app = FastAPI()

# x402 paywall on specific routes only
app.middleware("http")(
    require_payment(
        price="0.001",  # 0.001 ETH per request
        pay_to_address="0x71C7656EC7ab88b098defB751B7401B5f6d8976F",
        path=["/premium", "/expensive"],  # <- only these endpoints are paid
        network="base"  # Base mainnet
    )
)

@app.get("/health")
async def health():
    return {"status": "ok", "paid": False}  # free endpoint

@app.get("/premium")
async def premium():
    # Only reached after a valid x402 payment
    return {"data": "premium stuff"}

@app.get("/expensive")
async def expensive():
    return {"data": "super premium stuff"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
