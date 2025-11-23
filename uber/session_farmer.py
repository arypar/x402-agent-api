from playwright.async_api import async_playwright
import json
import os
import asyncio
import threading

COOKIE_FILE = os.path.join(os.path.dirname(__file__), "uber_cookies.json")
AUTH_URL = "https://auth.uber.com/v2/"

def save_cookies(cookies, filepath=COOKIE_FILE):
    """Save cookies to a JSON file"""
    try:
        with open(filepath, 'w') as f:
            json.dump(cookies, f, indent=2)
        print(f"✓ Cookies saved to {filepath}")
        print(f"✓ Saved {len(cookies)} cookies")
    except Exception as e:
        print(f"⚠️  Failed to save cookies: {e}")

async def session_farmer():
    """Open browser for manual login and save cookies when done"""
    print("\n" + "="*50)
    print("Uber Session Farmer")
    print("="*50)
    print("Browser will open for you to log in manually.")
    print("\nAfter logging in:")
    print("  Option 1: Press ENTER in this terminal to save cookies and close")
    print("  Option 2: Close the browser window, then press ENTER")
    print("="*50 + "\n")
    
    browser = None
    context = None
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            
            # Navigate to auth page
            print(f"Opening {AUTH_URL}...")
            await page.goto(AUTH_URL)
            print("✓ Browser opened. Please log in manually.\n")
            print("After you're logged in, come back here and press ENTER...")
            
            # Wait for user to press Enter in terminal
            def wait_for_enter():
                input()  # This blocks until Enter is pressed
            
            # Run the input in a separate thread so we can also monitor browser
            enter_pressed = threading.Event()
            
            def input_thread():
                try:
                    input()  # Wait for Enter
                    enter_pressed.set()
                except Exception:
                    pass
            
            thread = threading.Thread(target=input_thread, daemon=True)
            thread.start()
            
            # Monitor both Enter key and browser status
            browser_closed = False
            cookies_saved = False
            
            while not enter_pressed.is_set() and not browser_closed:
                await asyncio.sleep(0.5)
                try:
                    if not browser.is_connected():
                        browser_closed = True
                        print("\n✓ Browser window was closed")
                except Exception:
                    browser_closed = True
            
            # Save cookies IMMEDIATELY when Enter is pressed (browser still open)
            if enter_pressed.is_set() and not cookies_saved:
                print("\n✓ Enter pressed. Saving cookies...")
                try:
                    if context and browser.is_connected():
                        cookies = await context.cookies()
                        if cookies:
                            save_cookies(cookies)
                            print(f"✓ Successfully saved {len(cookies)} cookies!")
                            cookies_saved = True
                        else:
                            print("⚠️  No cookies found to save")
                            print("   Make sure you completed the login process")
                    else:
                        print("⚠️  Browser/context not available. Cannot save cookies.")
                except Exception as e:
                    print(f"⚠️  Error saving cookies: {e}")
                    import traceback
                    traceback.print_exc()
            
            # If browser was closed but cookies not saved yet, try one more time
            if browser_closed and not cookies_saved:
                print("\nBrowser was closed. Attempting to save cookies...")
                try:
                    if context:
                        cookies = await context.cookies()
                        if cookies:
                            save_cookies(cookies)
                            cookies_saved = True
                except Exception as e:
                    print(f"⚠️  Could not save cookies after browser close: {e}")
                    print("   Next time, press ENTER before closing the browser.")
            
    except KeyboardInterrupt:
        print("\n\nProgram interrupted. Saving cookies...")
        if context:
            try:
                cookies = await context.cookies()
                if cookies:
                    save_cookies(cookies)
            except Exception as e:
                print(f"⚠️  Error saving cookies: {e}")
    except Exception as e:
        print(f"\n⚠️  Error: {e}")
    finally:
        # Close browser if still open
        if browser and browser.is_connected():
            try:
                await browser.close()
            except Exception:
                pass

async def main():
    await session_farmer()
    print("\n✓ Session farmer completed. Cookies saved!")

if __name__ == "__main__":
    asyncio.run(main())

