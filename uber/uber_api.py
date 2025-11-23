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

def add_progress(message, task_id=None):
    """Helper function to add progress updates if task_id is provided"""
    if task_id:
        try:
            # Import here to avoid circular dependency
            import sys
            import os
            parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if parent_dir not in sys.path:
                sys.path.insert(0, parent_dir)
            from api.database import TaskDatabase
            TaskDatabase.add_progress_update(task_id, message)
        except Exception as e:
            print(f"Warning: Could not add progress update: {str(e)}")
    print(f"Progress: {message}")


async def generate_uber_url(from_address: str, to_address: str, task_id: str = None) -> str:
    """Use Claude to generate an Uber URL from addresses using /looking endpoint"""
    
    add_progress("Converting addresses to coordinates", task_id)
    
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
        
        add_progress("Generating Uber ride URL", task_id)
        
        # Build the Uber /looking URL (compact JSON without spaces)
        pickup_data = json.dumps({"latitude": pickup_lat, "longitude": pickup_lng}, separators=(',', ':'))
        drop_data = json.dumps({"latitude": drop_lat, "longitude": drop_lng}, separators=(',', ':'))
        
        pickup_encoded = urllib.parse.quote(pickup_data)
        drop_encoded = urllib.parse.quote(drop_data)
        
        url = f"https://m.uber.com/looking?pickup={pickup_encoded}&drop%5B0%5D={drop_encoded}"
        
        add_progress("Uber URL generated successfully", task_id)
        
        return url
    except Exception as e:
        print(f"Error generating Uber URL: {e}")
        import traceback
        traceback.print_exc()
        raise

async def navigate_to_auth(uber_url: str, task_id: str = None) -> bool:
    """Navigate to generated Uber URL and book ride (assumes cookies are ready from session farmer)
    Returns True if successful, False if payment was declined"""
    
    add_progress("Loading authentication session", task_id)
    
    # Load cookies from session farmer
    cookies = load_cookies()
    
    if not cookies:
        add_progress("Authentication failed - No session found", task_id)
        raise Exception("No cookies found! Please run session_farmer.py first to log in.")
    
    async with async_playwright() as p:
        # Launch browser with basic settings
        add_progress("Opening Uber app", task_id)
        browser = await p.chromium.launch(headless=False)
        
        try:
            # Create basic context
            context = await browser.new_context()
            
            # Add cookies from session farmer
            await context.add_cookies(cookies)
            print(f"✓ Loaded {len(cookies)} cookies from session farmer")
            
            page = await context.new_page()
            
            # Navigate to the generated Uber URL
            add_progress("Loading ride details", task_id)
            print(f"Navigating to: {uber_url}")
            await page.goto(uber_url, wait_until="domcontentloaded", timeout=60000)
            print("✓ Page loaded")
            add_progress("Ride details loaded", task_id)
            
            # Wait for the request trip button and click it
            try:
                add_progress("Waiting for ride options to load", task_id)
                print("Waiting for request trip button...")
                request_button = page.locator('[data-testid="request_trip_button"]')
                await request_button.wait_for(state='visible', timeout=30000)
                print("✓ Request trip button found. Waiting 0.5 seconds before clicking...")
                await asyncio.sleep(0.5)
                
                add_progress("Requesting ride", task_id)
                await request_button.click()
                print("✓ Clicked request trip button - Ride requested!")
                
                # Stage 1: Monitor for payment errors OR ride confirmation (first 10 seconds)
                add_progress("Processing ride request", task_id)
                print("Stage 1: Monitoring for payment errors or ride confirmation for 10 seconds...")
                
                payment_failed = False
                ride_confirmed = False
                start_time = asyncio.get_event_loop().time()
                
                while (asyncio.get_event_loop().time() - start_time) < 10:
                    # Get full HTML content (includes hidden fields)
                    page_content = await page.content()
                    
                    # Check for payment errors first
                    if "Try another payment method" in page_content:
                        add_progress("❌ Payment method failed", task_id)
                        print("❌ Try another payment method detected - closing browser and failing task")
                        payment_failed = True
                        break
                    
                    if "Payment was declined" in page_content:
                        add_progress("❌ Payment declined", task_id)
                        print("❌ Payment was declined - closing browser and failing task")
                        payment_failed = True
                        break
                    
                    if "PAYMENT_AUTH_DECLINED" in page_content:
                        add_progress("❌ Payment authorization declined", task_id)
                        print("❌ PAYMENT_AUTH_DECLINED detected - closing browser and failing task")
                        payment_failed = True
                        break
                    
                    # Check for ride confirmation messages
                    if "Confirming your ride" in page_content or "Ride Requested" in page_content:
                        add_progress("✅ Ride request confirmed", task_id)
                        print("✓ Ride confirmed - moving to driver matching stage")
                        ride_confirmed = True
                        break
                    
                    # Wait 0.5 seconds before checking again
                    await asyncio.sleep(0.5)
                
                if payment_failed:
                    await browser.close()
                    return False
                
                if not ride_confirmed:
                    print("⚠️ No explicit confirmation detected, but no payment error either - proceeding")
                    add_progress("Ride processing", task_id)
                
                # Stage 2: Wait for driver matching (monitor for status updates)
                print("Stage 2: Waiting for driver matching...")
                add_progress("Finding available drivers", task_id)
                
                # Monitor for up to 5 minutes for driver matching
                driver_found_timeout = 300  # 5 minutes
                driver_start_time = asyncio.get_event_loop().time()
                
                while (asyncio.get_event_loop().time() - driver_start_time) < driver_found_timeout:
                    page_content = await page.content()
                    current_url = page.url
                    
                    # Check if "Pickup in..." appears (driver assigned)
                    if "Pickup in" in page_content:
                        add_progress("✅ Driver assigned - Pickup confirmed", task_id)
                        print("✓ Pickup confirmed - ride successfully booked!")
                        await browser.close()
                        return True
                    
                    # Check for "Finding available drivers" status
                    if "Finding available drivers" in page_content:
                        print("Status: Finding available drivers...")
                        # Update status every 10 seconds to show we're still working
                        elapsed = int(asyncio.get_event_loop().time() - driver_start_time)
                        if elapsed > 0 and elapsed % 10 == 0:
                            add_progress("Finding available drivers", task_id)
                    
                    # Check if redirected to a different page
                    if "looking" not in current_url and current_url != uber_url:
                        add_progress(f"✅ Redirected to: {current_url}", task_id)
                        print(f"✓ Redirected to: {current_url}")
                        await browser.close()
                        return True
                    
                    # Wait 2 seconds before checking again
                    await asyncio.sleep(2)
                
                # If we timeout waiting for driver, still consider it successful
                # (the ride was requested, just no driver found yet)
                add_progress("✅ Ride requested successfully (waiting for driver assignment)", task_id)
                print("✓ Ride requested - exiting after timeout waiting for driver")
                await browser.close()
                return True
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

