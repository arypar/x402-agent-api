from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from browser_use import Agent, Browser, ChatAnthropic
from anthropic import AsyncAnthropic
from dotenv import load_dotenv
import asyncio
import json
import os
from typing import Optional

load_dotenv()

app = FastAPI(title="Uber Ride Booking API")

COOKIE_FILE = "uber_cookies.json"
UBER_EMAIL = "aryanmparekh@gmail.com"
UBER_PASSWORD = "ethglobalba123!"

class RideRequest(BaseModel):
    from_address: str
    to_address: str

class RideResponse(BaseModel):
    success: bool
    message: str
    uber_url: Optional[str] = None

def save_cookies(cookies, filepath=COOKIE_FILE):
    """Save cookies to a JSON file"""
    try:
        with open(filepath, 'w') as f:
            json.dump(cookies, f, indent=2)
    except Exception as e:
        print(f"⚠️  Failed to save cookies: {e}")

def load_cookies(filepath=COOKIE_FILE):
    """Load cookies from a JSON file"""
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, 'r') as f:
            cookies = json.load(f)
        return cookies
    except Exception as e:
        print(f"⚠️  Failed to load cookies: {e}")
        return None

async def generate_uber_url(from_address: str, to_address: str, llm: ChatAnthropic) -> str:
    """Use Claude to generate an Uber URL from addresses using /looking endpoint"""
    import urllib.parse
    
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
        import json
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

async def check_cookies_valid(browser: Browser, cookies: list) -> bool:
    """Check if cookies are still valid"""
    if not cookies:
        return False
    
    try:
        if not hasattr(browser, 'context') or browser.context is None:
            await browser.start()
        
        await browser.context.add_cookies(cookies)
        page = await browser.context.new_page()
        await page.goto("https://m.uber.com", wait_until="domcontentloaded", timeout=10000)
        await asyncio.sleep(2)
        
        current_url = page.url.lower()
        page_content = await page.content()
        await page.close()
        
        # Check for login indicators
        if any(indicator in current_url for indicator in ["/login", "/sign-in", "/signin", "auth"]):
            return False
        
        logged_in_indicators = ["product-selection", "book a ride", "where to?"]
        content_lower = page_content.lower()
        return any(indicator in content_lower for indicator in logged_in_indicators)
        
    except Exception as e:
        print(f"Error checking cookies: {e}")
        return False

async def login_and_save_cookies(browser: Browser, llm: ChatAnthropic, uber_url: str):
    """Perform login using browser_use and save cookies"""
    task = f"""Navigate to this uber URL: {uber_url}

Login with email: {UBER_EMAIL} and password: {UBER_PASSWORD}

If uber asks to log in with a code, click more options and log in with password.

After logging in successfully, wait for the page to fully load showing the ride selection.
"""
    
    agent = Agent(
        task=task,
        llm=llm,
        browser=browser,
        max_actions=20
    )
    
    await agent.run()
    
    # Wait for cookies to be set
    await asyncio.sleep(5)
    
    # Extract cookies
    cookies = None
    try:
        # Check if context attribute exists
        if not hasattr(browser, 'context'):
            print("ERROR: Browser object has no 'context' attribute")
            print(f"Browser type: {type(browser)}")
            print(f"Browser attributes: {dir(browser)}")
            return None
        
        # Check if context is None
        if browser.context is None:
            print("ERROR: Browser context is None")
            return None
        
        # Get pages from context
        try:
            pages = browser.context.pages if hasattr(browser.context, 'pages') else []
        except Exception as e:
            print(f"Error accessing context.pages: {e}")
            pages = []
        
        if pages:
            current_page = pages[0]
            current_url = current_page.url
            try:
                await current_page.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                pass
            cookies = await browser.context.cookies([current_url])
        
        if not cookies:
            cookies = await browser.context.cookies()
        
        if cookies:
            save_cookies(cookies)
            return cookies
    except AttributeError as e:
        print(f"AttributeError extracting cookies: {e}")
        print(f"Browser object: {browser}")
        print(f"Has context attr: {hasattr(browser, 'context')}")
        if hasattr(browser, 'context'):
            print(f"Context value: {browser.context}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"Error extracting cookies: {e}")
        import traceback
        traceback.print_exc()
    
    return None

async def book_ride(browser: Browser, llm: ChatAnthropic, uber_url: str) -> bool:
    """Book a ride using the Uber URL"""
    task = f"""Use this uber URL to call an uber ride: {uber_url}

You should already be logged in. If you see a login page, the session expired.

Click the "Request" or "Confirm" button to book the ride using the default payment method.

Wait for ride options to load, and book a ride

"""
    
    agent = Agent(
        task=task,
        llm=llm,
        browser=browser,
        max_actions=15
    )
    
    try:
        result = await agent.run()
        # Check if result indicates success
        result_lower = str(result).lower()
        success_indicators = ["success", "confirmed", "booked", "requested", "ride booked"]
        return any(indicator in result_lower for indicator in success_indicators)
    except Exception as e:
        print(f"Error booking ride: {e}")
        return False

@app.post("/book-ride", response_model=RideResponse)
async def book_uber_ride(request: RideRequest):
    """Book an Uber ride from one address to another"""
    llm = ChatAnthropic(model='claude-sonnet-4-0', temperature=0.0)
    browser = Browser(headless=False)  # Set to False to see browser window
    
    try:
        # Step 1: Generate Uber URL
        print(f"Generating Uber URL for {request.from_address} to {request.to_address}")
        uber_url = await generate_uber_url(request.from_address, request.to_address, llm)
        print(f"Generated URL: {uber_url}")
        
        # Step 2: Start browser
        await browser.start()
        
        # Step 3: Check/load cookies
        cookies = load_cookies()
        if cookies:
            is_valid = await check_cookies_valid(browser, cookies)
            if not is_valid:
                cookies = await login_and_save_cookies(browser, llm, uber_url)
            else:
                await browser.context.add_cookies(cookies)
        else:
            cookies = await login_and_save_cookies(browser, llm, uber_url)
        
        if not cookies:
            await browser.kill()
            raise HTTPException(status_code=500, detail="Failed to authenticate with Uber")
        
        # Step 4: Book the ride
        print("Booking ride...")
        success = await book_ride(browser, llm, uber_url)
        
        await browser.kill()
        
        if success:
            return RideResponse(
                success=True,
                message="Ride booked successfully",
                uber_url=uber_url
            )
        else:
            return RideResponse(
                success=False,
                message="Failed to book ride - check browser logs for details",
                uber_url=uber_url
            )
            
    except Exception as e:
        try:
            await browser.kill()
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Error booking ride: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

