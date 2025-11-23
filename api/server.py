"""
FastAPI Server
Combines Uber ride booking and Shopify search/ordering endpoints
"""

import sys
import os

# Add parent directory to path for imports (must be before other imports)
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

# Import Uber functionality (from uber folder)
import uber.uber_api as uber_api

# Import Shopify functionality (from shopify folder)
import shopify.shopifysearch as shopify_search_module
import shopify.main as shopify_main_module

# Import Coinbase functionality (from coinbase folder)
import coinbase.onramp as coinbase_onramp

app = FastAPI(
    title="Manual Script API",
    description="API for Uber rides, Shopify search, and Shopify checkout",
    version="1.0.0"
)

# ============================================================================
# Request/Response Models
# ============================================================================

class UberRideRequest(BaseModel):
    from_address: str
    to_address: str

class UberRideResponse(BaseModel):
    success: bool
    message: str
    uber_url: Optional[str] = None

class ShopifySearchRequest(BaseModel):
    query: str
    num_results: Optional[int] = 5

class ShopifySearchResponse(BaseModel):
    success: bool
    results: List[str]
    count: int

class ShopifyOrderRequest(BaseModel):
    product_url: str
    size: str

class ShopifyOrderResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    order_details: Optional[Dict[str, Any]] = None

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

# ============================================================================
# Uber Endpoints
# ============================================================================

@app.post("/uber/book-ride", response_model=UberRideResponse)
async def book_uber_ride(request: UberRideRequest):
    """
    Book an Uber ride from one address to another
    
    Args:
        from_address: Starting location
        to_address: Destination location
    
    Returns:
        UberRideResponse with success status and Uber URL
    """
    try:
        # Step 1: Generate Uber URL
        print(f"Generating Uber URL for {request.from_address} to {request.to_address}")
        uber_url = await uber_api.generate_uber_url(request.from_address, request.to_address)
        print(f"Generated URL: {uber_url}")
        
        # Step 2: Navigate to URL and book ride
        print("Starting browser automation to book ride...")
        success = await uber_api.navigate_to_auth(uber_url)
        
        if not success:
            return UberRideResponse(
                success=False,
                message="Payment was declined or booking failed",
                uber_url=uber_url
            )
        
        return UberRideResponse(
            success=True,
            message="Ride booking process completed",
            uber_url=uber_url
        )
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error booking ride: {str(e)}")

# ============================================================================
# Shopify Endpoints
# ============================================================================

@app.post("/shopify/search", response_model=ShopifySearchResponse)
async def shopify_search(request: ShopifySearchRequest):
    """
    Search for Shopify products using Exa API
    
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
            return ShopifySearchResponse(
                success=False,
                results=[],
                count=0
            )
        
        # Limit to requested number of results
        limited_results = results[:num_results]
        
        return ShopifySearchResponse(
            success=True,
            results=limited_results,
            count=len(limited_results)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching Shopify: {str(e)}")

@app.post("/shopify/order", response_model=ShopifyOrderResponse)
async def shopify_order(request: ShopifyOrderRequest):
    """
    Place an order on a Shopify store
    
    Args:
        product_url: URL of the Shopify product
        size: Size to order (e.g., "M", "7", "Large")
    
    Returns:
        ShopifyOrderResponse with order status and details
    """
    try:
        print(f"Processing Shopify order for: {request.product_url}, size: {request.size}")
        
        # Call the shopify_checkout function
        result = await shopify_main_module.shopify_checkout(request.product_url, request.size)
        
        # Check if the checkout was successful
        if result.get('success'):
            return ShopifyOrderResponse(
                success=True,
                message="Order placed successfully",
                order_details=result
            )
        else:
            return ShopifyOrderResponse(
                success=False,
                error=result.get('error', 'Unknown error occurred'),
                order_details=result
            )
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error placing Shopify order: {str(e)}")

# ============================================================================
# Coinbase Endpoints
# ============================================================================

@app.post("/coinbase/onramp", response_model=CoinbaseOnrampResponse)
async def create_coinbase_onramp(request: CoinbaseOnrampRequest):
    """
    Generate a Coinbase onramp URL for crypto purchases
    
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
        
        print(f"Generating Coinbase onramp URL with config: {session_config}")
        
        # Generate JWT
        jwt_token = coinbase_onramp.generate_jwt("POST", coinbase_onramp.API_PATH)
        
        # Create onramp session
        session_data = coinbase_onramp.create_onramp_session(jwt_token, session_config)
        
        # Extract onramp URL
        onramp_url = session_data.get('session', {}).get('onrampUrl')
        
        if not onramp_url:
            return CoinbaseOnrampResponse(
                success=False,
                error="Onramp URL not found in response",
                session_data=session_data
            )
        
        return CoinbaseOnrampResponse(
            success=True,
            onramp_url=onramp_url,
            session_data=session_data
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return CoinbaseOnrampResponse(
            success=False,
            error=str(e)
        )

# ============================================================================
# Health Check
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "endpoints": {
            "uber": "/uber/book-ride",
            "shopify_search": "/shopify/search",
            "shopify_order": "/shopify/order",
            "coinbase_onramp": "/coinbase/onramp"
        }
    }

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Manual Script API",
        "version": "1.0.0",
        "endpoints": {
            "uber_ride": {
                "path": "/uber/book-ride",
                "method": "POST",
                "description": "Book an Uber ride"
            },
            "shopify_search": {
                "path": "/shopify/search",
                "method": "POST",
                "description": "Search for Shopify products"
            },
            "shopify_order": {
                "path": "/shopify/order",
                "method": "POST",
                "description": "Place an order on Shopify"
            },
            "coinbase_onramp": {
                "path": "/coinbase/onramp",
                "method": "POST",
                "description": "Generate Coinbase onramp URL"
            },
            "health": {
                "path": "/health",
                "method": "GET",
                "description": "Health check"
            }
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

