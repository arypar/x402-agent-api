from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from anthropic import AsyncAnthropic
from dotenv import load_dotenv
from playwright.async_api import async_playwright
import urllib.parse
import json
import asyncio
import os

load_dotenv()

app = FastAPI(title="Uber Ride Booking API")

COOKIE_FILE = os.path.join(os.path.dirname(__file__), "uber_cookies.json")

def save_cookies(cookies, filepath=COOKIE_FILE):
    """Save cookies to a JSON file"""
    try:
        with open(filepath, 'w') as f:
            json.dump(cookies, f, indent=2)
        print(f"✓ Cookies saved to {filepath}")
    except Exception as e:
        print(f"⚠️  Failed to save cookies: {e}")

def load_cookies(filepath=COOKIE_FILE):
    """Load cookies from a JSON file"""
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, 'r') as f:
            cookies = json.load(f)
        print(f"✓ Loaded {len(cookies)} cookies from {filepath}")
        return cookies
    except Exception as e:
        print(f"⚠️  Failed to load cookies: {e}")
        return []

async def generate_uber_url(from_address: str, to_address: str) -> str:
    """Use Claude to generate an Uber URL from addresses using /looking endpoint"""
    
    prompt = f"""Given these two addresses, provide the latitude and longitude coordinates for each:

Pickup address: {from_address}
Destination address: {to_address}

Return the coordinates in this exact JSON format:
{{
  "pickup": {{
    "latitude": <latitude>,
    "longitude": <longitude>
  }},
  "drop": {{
    "latitude": <latitude>,
    "longitude": <longitude>
  }}
}}

Return ONLY the JSON, nothing else. No explanations, no markdown formatting."""

    try:
        # Use Anthropic API directly to get coordinates
        client = AsyncAnthropic()
        message = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        response_text = message.content[0].text.strip()
        
        # Clean up the response if it has markdown formatting
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1]) if len(lines) > 2 else response_text
        response_text = response_text.strip().strip("`").strip()
        
        # Parse JSON response
        coords = json.loads(response_text)
        
        pickup_lat = coords["pickup"]["latitude"]
        pickup_lng = coords["pickup"]["longitude"]
        drop_lat = coords["drop"]["latitude"]
        drop_lng = coords["drop"]["longitude"]
        
        # Build the Uber /looking URL (compact JSON without spaces)
        pickup_data = json.dumps({"latitude": pickup_lat, "longitude": pickup_lng}, separators=(',', ':'))
        drop_data = json.dumps({"latitude": drop_lat, "longitude": drop_lng}, separators=(',', ':'))
        
        pickup_encoded = urllib.parse.quote(pickup_data)
        drop_encoded = urllib.parse.quote(drop_data)
        
        url = f"https://m.uber.com/looking?pickup={pickup_encoded}&drop%5B0%5D={drop_encoded}"
        
        return url
    except Exception as e:
        print(f"Error generating Uber URL: {e}")
        import traceback
        traceback.print_exc()
        raise

async def navigate_to_auth(uber_url: str) -> bool:
    """Navigate to generated Uber URL and book ride (assumes cookies are ready from session farmer)
    Returns True if successful, False if payment was declined"""
    # Load cookies from session farmer
    cookies = load_cookies()
    
    if not cookies:
        raise Exception("No cookies found! Please run session_farmer.py first to log in.")
    
    async with async_playwright() as p:
        # Launch browser with basic settings
        browser = await p.chromium.launch(headless=False)
        
        try:
            # Create basic context
            context = await browser.new_context()
            
            # Add cookies from session farmer
            await context.add_cookies(cookies)
            print(f"✓ Loaded {len(cookies)} cookies from session farmer")
            
            page = await context.new_page()
            
            # Navigate to the generated Uber URL
            print(f"Navigating to: {uber_url}")
            await page.goto(uber_url, wait_until="domcontentloaded", timeout=60000)
            print("✓ Page loaded")
            
            # Wait for the request trip button and click it
            try:
                print("Waiting for request trip button...")
                request_button = page.locator('[data-testid="request_trip_button"]')
                await request_button.wait_for(state='visible', timeout=30000)
                print("✓ Request trip button found. Waiting 0.5 seconds before clicking...")
                await asyncio.sleep(0.5)
                await request_button.click()
                print("✓ Clicked request trip button - Ride requested!")
                
                # Wait for page to finish loading after clicking
                print("Waiting for page to finish loading...")
                await page.wait_for_load_state("networkidle", timeout=30000)
                await asyncio.sleep(2)  # Give it a moment to render any error messages
                
                # Check if payment was declined
                page_text = await page.inner_text("body")
                if "Payment was declined" in page_text:
                    print("❌ Payment was declined - returning failed")
                    return False
                
                # Wait 10 minutes before closing
                print("Waiting 10 minutes before closing browser...")
                await asyncio.sleep(600)  # 10 minutes = 600 seconds
                print("10 minutes elapsed, closing browser...")
            except Exception as e:
                print(f"⚠️  Error clicking request trip button: {e}")
                raise
            
            # Save updated cookies before closing
            try:
                updated_cookies = await context.cookies()
                if updated_cookies:
                    save_cookies(updated_cookies)
                    print("✓ Cookies updated and saved")
            except Exception as e:
                print(f"⚠️  Error saving cookies: {e}")
            
        finally:
            # Close browser
            try:
                await browser.close()
                print("Browser closed")
            except Exception as e:
                print(f"⚠️  Error closing browser: {e}")
    
    return True

class RideRequest(BaseModel):
    from_address: str
    to_address: str

class RideResponse(BaseModel):
    success: bool
    message: str
    uber_url: Optional[str] = None

@app.post("/book-ride", response_model=RideResponse)
async def book_uber_ride(request: RideRequest):
    """Book an Uber ride from one address to another"""
    try:
        # Step 1: Generate Uber URL
        print(f"Generating Uber URL for {request.from_address} to {request.to_address}")
        uber_url = await generate_uber_url(request.from_address, request.to_address)
        print(f"Generated URL: {uber_url}")
        
        # Step 2: Navigate to URL and book ride
        print("Starting browser automation to book ride...")
        success = await navigate_to_auth(uber_url)
        
        if not success:
            return RideResponse(
                success=False,
                message="Payment was declined",
                uber_url=uber_url
            )
        
        return RideResponse(
            success=True,
            message="Ride booking process completed",
            uber_url=uber_url
        )
        
    except Exception as e:
        print(f"Error booking ride: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error booking ride: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

