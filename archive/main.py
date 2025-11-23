import requests
import time
import asyncio
import re
from bs4 import BeautifulSoup
from browser_use import Agent, Browser, ChatAnthropic

from dotenv import load_dotenv

load_dotenv()

def extract_authenticity_token(html_content):
    """Extract authenticity token from HTML response
    
    Args:
        html_content (str): HTML content from the response
        
    Returns:
        str: The authenticity token value
        
    Raises:
        ValueError: If token cannot be found
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Look for the hidden input field with name="authenticity_token"
        token_input = soup.find('input', {'name': 'authenticity_token', 'type': 'hidden'})
        
        if token_input and token_input.get('value'):
            token = token_input.get('value')
            print(f"✓ Extracted authenticity token: {token[:20]}...")
            return token
        
        # Fallback: Try to find it using regex
        token_match = re.search(r'name="authenticity_token"\s+value="([^"]+)"', html_content)
        if token_match:
            token = token_match.group(1)
            print(f"✓ Extracted authenticity token (via regex): {token[:20]}...")
            return token
        
        raise ValueError("Authenticity token not found in HTML response")
        
    except Exception as e:
        raise ValueError(f"Failed to extract authenticity token: {str(e)}")

def run_authentication_flow():
    """Run the authentication and cart flow using requests.Session()"""
    print("="*50)
    print("Starting Authentication Flow...")
    print("="*50)
    
    try:
        # Create a session for efficient request handling
        session = requests.Session()
        
        # First request - GET password page
        print("\n[Step 1/5] Fetching password page...")
        url = "https://mimik-ai-3.myshopify.com/password"
        headers = {
          'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
          'accept-language': 'en-US,en;q=0.9',
          'cache-control': 'max-age=0',
          'priority': 'u=0, i',
          'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
          'sec-ch-ua-mobile': '?0',
          'sec-ch-ua-platform': '"macOS"',
          'sec-fetch-dest': 'document',
          'sec-fetch-mode': 'navigate',
          'sec-fetch-site': 'none',
          'sec-fetch-user': '?1',
          'upgrade-insecure-requests': '1',
          'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36'
        }
        
        try:
            response = session.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            print(f"✓ Fetched password page (Status: {response.status_code})")
        except requests.exceptions.Timeout:
            raise Exception("Request timed out while fetching password page")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to fetch password page: {str(e)}")
        
        # Extract authenticity token from response
        print("\n[Step 2/5] Extracting authenticity token...")
        try:
            authenticity_token = extract_authenticity_token(response.text)
        except ValueError as e:
            raise Exception(f"Failed to extract token: {str(e)}")
        
        # Second request - POST with authentication
        print("\n[Step 3/5] Authenticating with password...")
        url2 = "https://mimik-ai-3.myshopify.com/password"
        
        # URL encode the token and password
        from urllib.parse import urlencode
        payload2 = urlencode({
            'authenticity_token': authenticity_token,
            'password': 'aryanparekh'
        })
        
        headers2 = {
          'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
          'accept-language': 'en-US,en;q=0.9',
          'cache-control': 'max-age=0',
          'content-type': 'application/x-www-form-urlencoded',
          'origin': 'https://mimik-ai-3.myshopify.com',
          'priority': 'u=0, i',
          'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
          'sec-ch-ua-mobile': '?0',
          'sec-ch-ua-platform': '"macOS"',
          'sec-fetch-dest': 'document',
          'sec-fetch-mode': 'navigate',
          'sec-fetch-site': 'same-origin',
          'sec-fetch-user': '?1',
          'upgrade-insecure-requests': '1',
          'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36'
        }
        
        try:
            response2 = session.post(url2, headers=headers2, data=payload2, timeout=10, allow_redirects=True)
            response2.raise_for_status()
            print(f"✓ Authenticated (Status: {response2.status_code})")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Authentication failed: {str(e)}")
        
        # Third request - GET product page
        print("\n[Step 4/5] Fetching product page...")
        url3 = "https://mimik-ai-3.myshopify.com/products/the-collection-snowboard-liquid"
        headers3 = {
          'Referer': 'https://mimik-ai-3.myshopify.com/',
          'Upgrade-Insecure-Requests': '1',
          'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
          'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
          'sec-ch-ua-mobile': '?0',
          'sec-ch-ua-platform': '"macOS"'
        }
        
        try:
            response3 = session.get(url3, headers=headers3, timeout=10)
            response3.raise_for_status()
            print(f"✓ Fetched product page (Status: {response3.status_code})")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to fetch product page: {str(e)}")
        
        # Fourth request - Add product to cart
        print("\n[Step 5/5] Adding product to cart...")
        url4 = "https://mimik-ai-3.myshopify.com/cart/add"
        payload4 = {
          'form_type': 'product',
          'utf8': '✓',
          'id': '51009883865301',
          'product-id': '8875566891221',
          'section-id': 'template--18714050855125__main',
          'sections': 'cart-drawer,cart-icon-bubble',
          'sections_url': '/products/the-collection-snowboard-liquid',
          'selling_plan': ''
        }
        headers4 = {
          'accept': 'application/javascript',
          'accept-language': 'en-US,en;q=0.9',
          'origin': 'https://mimik-ai-3.myshopify.com',
          'priority': 'u=1, i',
          'referer': 'https://mimik-ai-3.myshopify.com/products/the-collection-snowboard-liquid',
          'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
          'sec-ch-ua-mobile': '?0',
          'sec-ch-ua-platform': '"macOS"',
          'sec-fetch-dest': 'empty',
          'sec-fetch-mode': 'cors',
          'sec-fetch-site': 'same-origin',
          'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
          'x-requested-with': 'XMLHttpRequest'
        }
        
        try:
            response4 = session.post(url4, headers=headers4, data=payload4, timeout=10)
            response4.raise_for_status()
            print(f"✓ Added product to cart (Status: {response4.status_code})")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to add product to cart: {str(e)}")
        
        # Fifth request - Proceed to checkout and get checkout URL
        print("\n[Step 6/6] Proceeding to checkout...")
        url5 = "https://mimik-ai-3.myshopify.com/cart"
        payload5 = 'updates%5B%5D=1&checkout='
        headers5 = {
          'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
          'accept-language': 'en-US,en;q=0.9',
          'cache-control': 'max-age=0',
          'content-type': 'application/x-www-form-urlencoded',
          'origin': 'https://mimik-ai-3.myshopify.com',
          'priority': 'u=0, i',
          'referer': 'https://mimik-ai-3.myshopify.com/products/the-multi-location-snowboard',
          'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
          'sec-ch-ua-mobile': '?0',
          'sec-ch-ua-platform': '"macOS"',
          'sec-fetch-dest': 'document',
          'sec-fetch-mode': 'navigate',
          'sec-fetch-site': 'same-origin',
          'sec-fetch-user': '?1',
          'upgrade-insecure-requests': '1',
          'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36'
        }
        
        try:
            response5 = session.post(url5, headers=headers5, data=payload5, timeout=10, allow_redirects=True)
            response5.raise_for_status()
            print(f"✓ Proceeded to checkout (Status: {response5.status_code})")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to proceed to checkout: {str(e)}")
        
        # Print the final redirect URL
        print("\n" + "="*50)
        print("Checkout URL Generated:")
        print(response5.url)
        print("="*50)
        
        # Print all session cookies
        print("\n" + "="*50)
        print("Session Cookies (will be transferred to browser):")
        print("="*50)
        for cookie in session.cookies:
            print(f"{cookie.name}: {cookie.value[:30]}..." if len(cookie.value) > 30 else f"{cookie.name}: {cookie.value}")
        print("="*50)
        
        # Extract cookies for browser-use
        cookies_for_browser = []
        for cookie in session.cookies:
            cookie_dict = {
                'name': cookie.name,
                'value': cookie.value,
                'domain': cookie.domain if cookie.domain else '.mimik-ai-3.myshopify.com',
                'path': cookie.path if cookie.path else '/',
            }
            cookies_for_browser.append(cookie_dict)
        
        return str(response5.url), cookies_for_browser
        
    except Exception as e:
        print(f"\n❌ Error in authentication flow: {str(e)}")
        raise


async def complete_checkout_with_browser_use(checkout_url, cookies):
    """Use browser-use to complete the checkout form"""
    print("\n" + "="*50)
    print("Starting Browser-Use to complete checkout...")
    print("="*50)
    
    # Initialize the LLM (Claude Sonnet 4)
    # Browser-Use's ChatAnthropic wrapper
    llm = ChatAnthropic(model='claude-sonnet-4-20250514', temperature=0.0)
    
    # Generate random email
    random_email = f"test{time.time_ns() % 10000}@example.com"
    
    # Create the task for the agent
    task = f"""
    I need you to complete a Shopify checkout form. The checkout page is already loaded with authentication cookies.
    
    Fill out the checkout form with these details:
    
    Contact Information:
    - Email: {random_email}
    
    Shipping Address:
    - First Name: John
    - Last Name: Doe
    - Address: 123 Main Street
    - Apartment/Suite: Apt 4B
    - City: New York
    - State/Province: New York
    - ZIP/Postal Code: 10001
    - Country: United States
    - Phone: 5551234567
    
    Complete these steps:
    1. Fill out the contact email field
    2. Fill out all shipping address fields (first name, last name, address, city, state, zip, phone)
    3. Click "Continue to shipping" or similar button to proceed
    4. If there's a shipping method selection page, choose the first available shipping option
    5. Click continue to proceed to payment
    6. STOP when you reach the payment page - DO NOT enter any credit card or payment details
    
    Important: Do NOT enter any credit card or payment information. Stop at the payment page.
    """
    
    # Convert cookies to the format expected by playwright
    playwright_cookies = []
    for cookie in cookies:
        playwright_cookie = {
            'name': cookie['name'],
            'value': cookie['value'],
            'domain': cookie.get('domain', '.mimik-ai-3.myshopify.com'),
            'path': cookie.get('path', '/'),
            'secure': True,
            'httpOnly': True,
            'sameSite': 'Lax'
        }
        playwright_cookies.append(playwright_cookie)
    
    print(f"✓ Checkout URL: {checkout_url}")
    print(f"✓ Using email: {random_email}")
    print(f"✓ Cookies prepared for transfer")
    
    # Create a custom browser with cookies
    browser = Browser(headless=False)
    
    try:
        print("\n⏳ Initializing browser and injecting cookies...")
        
        # Initialize the browser session
        await browser.init()
        
        # Add cookies to the browser context
        await browser.context.add_cookies(playwright_cookies)
        print(f"✓ Added authenticated cookies to browser")
        
        # Navigate to the checkout URL
        page = await browser.context.new_page()
        await page.goto(checkout_url)
        print(f"✓ Navigated to checkout page")
        
        print("\nAgent is now completing the checkout form...")
        print("(This may take 1-3 minutes)")
        
        # Create agent with the browser
        agent = Agent(
            task=task,
            llm=llm,
            browser=browser,
            max_actions=30
        )
        
        # Run the agent
        result = await agent.run()
        
        print("\n" + "="*50)
        print("Checkout Completion Result:")
        print("="*50)
        print(result)
        print("="*50)
        
        print("\n✓ Checkout form completed!")
        print("  Browser will stay open for inspection.")
        print("  Press Ctrl+C to close.")
        
        # Keep browser open for manual inspection
        try:
            await asyncio.sleep(300)  # Keep alive for 5 minutes
        except KeyboardInterrupt:
            print("\n\nClosing browser...")
        
    except Exception as e:
        print(f"\n❌ Error during checkout: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        if browser:
            await browser.close()


async def main():
    """Main entry point"""
    # Step 1: Run authentication flow with requests
    checkout_url, cookies = run_authentication_flow()
    
    # Step 2: Use browser-use to complete checkout
    await complete_checkout_with_browser_use(checkout_url, cookies)


if __name__ == "__main__":
    asyncio.run(main())
