import requests
from urllib.parse import urlparse
import json
from playwright.async_api import async_playwright
import asyncio
from anthropic import AsyncAnthropic
from dotenv import load_dotenv

load_dotenv()


async def find_size_match_with_claude(user_size, available_sizes):
    """
    Use Claude to find the best size match if exact match wasn't found.
    Only returns a match if it's the same size in a different format.
    Returns None if the size is not available.
    
    Args:
        user_size: The size the user requested
        available_sizes: List of available sizes from the product
    
    Returns:
        str: Matched size from available_sizes, or None if not available
    """
    try:
        client = AsyncAnthropic()
        
        prompt = f"""You are helping match a user-requested size with available product sizes.

User requested size: "{user_size}"
Available sizes: {available_sizes}

Your task:
1. Check if the user's requested size matches any of the available sizes, but in a different format (e.g., "M" vs "Medium", "7" vs "7.0", "Wide (EE) / 7" vs "7 Wide")
2. If it's the SAME size in a different format, return ONLY the exact string from the available_sizes list that matches
3. If it's a DIFFERENT size (not just a format difference), return "NOT_AVAILABLE"

Important rules:
- Only return a match if it's the same size in a different format
- If the size doesn't exist (even in different formats), return "NOT_AVAILABLE"
- Return ONLY the exact string from available_sizes, nothing else
- If not available, return exactly "NOT_AVAILABLE"

Examples:
- User: "M", Available: ["S", "M", "L"] → Return: "M"
- User: "Medium", Available: ["S", "M", "L"] → Return: "M"
- User: "7", Available: ["6", "7", "8"] → Return: "7"
- User: "7 Wide", Available: ["7", "7 Wide", "8"] → Return: "7 Wide"
- User: "Wide (EE) / 7", Available: ["7", "7 Wide", "8"] → Return: "7 Wide"
- User: "XL", Available: ["S", "M", "L"] → Return: "NOT_AVAILABLE"
- User: "10", Available: ["7", "8", "9"] → Return: "NOT_AVAILABLE"

Return your response now:"""

        message = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=100,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        response_text = message.content[0].text.strip()
        
        if response_text == "NOT_AVAILABLE":
            print(f"Claude determined: Size '{user_size}' is not available")
            return None
        else:
            # Verify the response is in the available sizes list
            response_lower = response_text.lower()
            for avail_size in available_sizes:
                if avail_size.lower() == response_lower:
                    print(f"Claude matched: '{user_size}' → '{avail_size}'")
                    return avail_size
            
            # If Claude returned something not in the list, treat as not available
            print(f"Claude returned '{response_text}' which is not in available sizes. Treating as not available.")
            return None
            
    except Exception as e:
        print(f"Error calling Claude for size matching: {str(e)}")
        return None


# Test data structure based on screenshot
CHECKOUT_DATA = {
    'email': 'aryanolegshivam@gmail.com',
    'country_region': 'United States',
    'first_name': 'Aryan',
    'last_name': 'Parekh',
    'address': '305 Jacaranda Drive',
    'suite_apt': '',  # Empty as shown in screenshot
    'city': 'Fremont',
    'state': 'California',
    'zip_code': '94539',
    'phone': '(510) 647-4689',
    'card_number': '4000000000009995',  # Left blank
    'expiry': '11/30',  # Left blank
    'cvv': '030'  # Left blank
}


async def make_request_with_retry(session, method, url, step_name, expected_status=200, max_retries=5, **kwargs):
    """
    Make a request with retry logic and status code validation
    
    Args:
        session: requests.Session object
        method: HTTP method ('get' or 'post')
        url: URL to request
        step_name: Name of the step for error reporting
        expected_status: Expected status code (default: 200)
        max_retries: Maximum number of retries (default: 5)
        **kwargs: Additional arguments to pass to request method
    
    Returns:
        requests.Response object
    
    Raises:
        Exception: If all retries fail
    """
    for attempt in range(1, max_retries + 1):
        try:
            if method.lower() == 'get':
                response = session.get(url, **kwargs)
            elif method.lower() == 'post':
                response = session.post(url, **kwargs)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            if response.status_code == expected_status:
                return response
            else:
                print(f"⚠️  Attempt {attempt}/{max_retries}: {step_name} returned status {response.status_code}, expected {expected_status}")
                if attempt < max_retries:
                    await asyncio.sleep(1)  # Wait 1 second before retry
                    continue
                else:
                    error_msg = f"{step_name} failed after {max_retries} attempts. Expected status {expected_status}, got {response.status_code}"
                    raise Exception(error_msg)
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Attempt {attempt}/{max_retries}: {step_name} request failed: {str(e)}")
            if attempt < max_retries:
                await asyncio.sleep(1)  # Wait 1 second before retry
                continue
            else:
                error_msg = f"{step_name} failed after {max_retries} attempts. Error: {str(e)}"
                raise Exception(error_msg)
    
    # Should never reach here, but just in case
    raise Exception(f"{step_name} failed after {max_retries} attempts")


async def shopify_checkout(product_url, size, visit_base_site=False):
    """
    Shopify cart add flow:
    1. Uses requests session to visit base site (optional), then product .js endpoint
    2. Extracts product ID and variant ID from JSON response
    3. Posts to /cart/add with extracted IDs
    4. Proceeds to checkout and gets checkout URL
    5. Extracts cookies from session and opens checkout URL in Playwright
    6. Fills out checkout form fields and clicks checkout button
    
    Args:
        product_url: URL of the Shopify product page
        size: Size to add to cart
        visit_base_site: Whether to visit the base site first (default: True)
    """
    
    # Step 1: Use requests session to visit base site first, then product .js endpoint
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    })
    
    # Track all URL:status_code pairs
    request_log = []
    
    try:
        # Extract base site URL from product URL
        parsed = urlparse(product_url)
        shop_domain = f"{parsed.scheme}://{parsed.netloc}"
        
        # Visit base site first (if enabled)
        if visit_base_site:
            print(f"Visiting base site: {shop_domain}")
            try:
                base_response = await make_request_with_retry(session, 'get', shop_domain, 'Step 1: Visit base site', expected_status=200)
                request_log.append(f"{shop_domain}: {base_response.status_code}")
                print("✓ Base site visited")
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e),
                    'step': 'Step 1: Visit base site',
                    'url': shop_domain,
                    'request_log': request_log
                }
        else:
            print("Skipping base site visit (visit_base_site=False)")
        
        # Extract product slug from URL and visit .js endpoint
        product_slug = product_url.split('/products/')[-1].split('?')[0]
        product_js_url = f"{shop_domain}/products/{product_slug}.js"
        
        print(f"Fetching product data from: {product_js_url}")
        try:
            product_response = await make_request_with_retry(session, 'get', product_js_url, 'Step 2: Fetch product data', expected_status=200)
            request_log.append(f"{product_js_url}: {product_response.status_code}")
            product_data = product_response.json()
            print("✓ Product data fetched")
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'step': 'Step 2: Fetch product data',
                'url': product_js_url,
                'request_log': request_log
            }
        
        # Extract product ID
        product_id = product_data['id']
        print(f"✓ Product ID: {product_id}")
        
        # Find variant ID by matching size
        variant_id = None
        size_lower = size.lower()
        
        print(f"Looking for variant with size: {size}")
        for variant in product_data.get('variants', []):
            variant_title = variant.get('title', '').lower()
            if variant_title == size_lower:
                variant_id = variant['id']
                print(f"✓ Found variant ID: {variant_id} for size: {variant.get('title')}")
                break
        
        # If no exact match, use Claude to find best match
        if not variant_id:
            available_sizes = [v.get('title') for v in product_data.get('variants', [])]
            print(f"No exact match found. Available sizes: {available_sizes}")
            print("Asking Claude to find best match...")
            
            matched_size = await find_size_match_with_claude(size, available_sizes)
            
            if matched_size:
                # Find variant with the matched size
                for variant in product_data.get('variants', []):
                    if variant.get('title', '').lower() == matched_size.lower():
                        variant_id = variant['id']
                        print(f"✓ Found variant ID: {variant_id} for matched size: {variant.get('title')}")
                        break
            else:
                raise ValueError(f"Size '{size}' is not available. Available sizes: {available_sizes}")
        
        # Step 3: Post to /cart/add with extracted IDs
        cart_add_url = f"{shop_domain}/cart/add"

        payload = {
            'form_type': 'product',
            'utf8': '✓',
            'id': str(variant_id),
            'quantity': '1',
            'product-id': str(product_id),
        }
        
        # Use specific headers for cart/add request
        cart_headers = {
            'accept': 'application/javascript',
            'accept-language': 'en-US,en;q=0.9',
            'origin': shop_domain,
            'priority': 'u=1, i',
            'referer': product_url,
            'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
            'x-requested-with': 'XMLHttpRequest',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        print(f"Posting to {cart_add_url} with payload: {payload}")
        try:
            cart_response = await make_request_with_retry(session, 'post', cart_add_url, 'Step 3: Add to cart', expected_status=200, data=payload, headers=cart_headers)
            request_log.append(f"{cart_add_url}: {cart_response.status_code}")
            print(f"✓ Cart add response status: {cart_response.status_code}")
            
            # Parse and print as JSON only
            response_json = cart_response.json()
            print(json.dumps(response_json, indent=2))
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'step': 'Step 3: Add to cart',
                'url': cart_add_url,
                'request_log': request_log
            }
        
        # Step 4: Proceed to checkout and get checkout URL
        print("\n[Step 4] Proceeding to checkout...")
        cart_url = f"{shop_domain}/cart"
        checkout_payload = 'updates[]=1&checkout='
        
        checkout_headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-US,en;q=0.9',
            'cache-control': 'max-age=0',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': shop_domain,
            'priority': 'u=0, i',
            'referer': product_url,
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
            checkout_response = await make_request_with_retry(session, 'post', cart_url, 'Step 4: Proceed to checkout', expected_status=200, headers=checkout_headers, data=checkout_payload, allow_redirects=True)
            request_log.append(f"{cart_url}: {checkout_response.status_code}")
            # Also log the final redirect URL if different
            if checkout_response.url != cart_url:
                request_log.append(f"{checkout_response.url}: {checkout_response.status_code} (redirect)")
            print(f"✓ Proceeded to checkout (Status: {checkout_response.status_code})")
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'step': 'Step 4: Proceed to checkout',
                'url': cart_url,
                'request_log': request_log
            }
        
        # Print the final checkout URL
        checkout_url = checkout_response.url
        print("\n" + "="*50)
        print("Checkout URL Generated:")
        print(checkout_url)
        print("="*50)
        
        # Step 5: Extract cookies and open checkout URL in Playwright
        print("\n[Step 5] Extracting cookies and opening checkout in Playwright...")
        
        # Extract cookies from session and convert to Playwright format
        cookies = []
        for cookie in session.cookies:
            domain = cookie.domain.lstrip('.') if cookie.domain else None
            
            cookie_dict = {
                'name': cookie.name,
                'value': cookie.value,
                'domain': domain,
                'path': cookie.path or '/',
                'expires': cookie.expires if cookie.expires and cookie.expires > 0 else -1,
                'httpOnly': hasattr(cookie, 'has_nonstandard_attr') and cookie.has_nonstandard_attr('HttpOnly'),
                'secure': cookie.secure if hasattr(cookie, 'secure') else False,
                'sameSite': 'Lax'
            }
            cookies.append(cookie_dict)
        
        print(f"✓ Extracted {len(cookies)} cookies from requests session")
        
        # Print all request logs before opening browser
        print("\n" + "="*50)
        print("Request Summary (URL: Status Code):")
        print("="*50)
        for log_entry in request_log:
            print(log_entry)
        print("="*50)
        
        # Open Playwright with cookies
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            
            try:
                context = await browser.new_context()
                
                # Add cookies from requests session
                await context.add_cookies(cookies)
                print(f"✓ Loaded {len(cookies)} cookies into Playwright")
                
                page = await context.new_page()
                
                # Navigate to checkout URL
                print(f"Opening checkout URL: {checkout_url}")
                await page.goto(checkout_url, wait_until="domcontentloaded", timeout=60000)
                print("✓ Checkout page opened in browser")
                
                # Wait a moment for page to start rendering
                await asyncio.sleep(2)
                
                # Wait for the email field to appear (this is more reliable than networkidle)
                print("Waiting for checkout form to load...")
                
                # Fill checkout form fields
                print("\nFilling out checkout form...")
                
                # Email - wait for it to be visible first
                try:
                    print("Waiting for email field...")
                    await page.wait_for_selector('#email', state='visible', timeout=30000)
                    await page.fill('#email', CHECKOUT_DATA['email'])
                    print("✓ Email filled")
                except Exception as e:
                    print(f"⚠️  Email field not found: {str(e)}")
                
                # Country/Region
                try:
                    print("Waiting for country/region field...")
                    await page.wait_for_selector('select[name="countryCode"]', state='visible', timeout=10000)
                    await page.select_option('select[name="countryCode"]', CHECKOUT_DATA['country_region'])
                    print("✓ Country/Region selected")
                    await asyncio.sleep(0.1)
                except Exception as e:
                    print(f"⚠️  Country/Region field not found: {str(e)}")
                
                # First name
                try:
                    print("Waiting for first name field...")
                    await page.wait_for_selector('input[name="firstName"]', state='visible', timeout=10000)
                    await page.fill('input[name="firstName"]', CHECKOUT_DATA['first_name'])
                    print("✓ First name filled")
                    await asyncio.sleep(0.1)
                except Exception as e:
                    print(f"⚠️  First name field not found: {str(e)}")
                
                # Last name
                try:
                    print("Waiting for last name field...")
                    await page.wait_for_selector('input[name="lastName"]', state='visible', timeout=10000)
                    await page.fill('input[name="lastName"]', CHECKOUT_DATA['last_name'])
                    print("✓ Last name filled")
                    await asyncio.sleep(0.1)
                except Exception as e:
                    print(f"⚠️  Last name field not found: {str(e)}")
                
                # Address
                try:
                    print("Waiting for address field...")
                    await page.wait_for_selector('input[name="address1"]', state='visible', timeout=10000)
                    await asyncio.sleep(0.3)  # Extra delay before filling address
                    await page.fill('input[name="address1"]', CHECKOUT_DATA['address'])
                    print("✓ Address filled")
                    await asyncio.sleep(0.3)  # Extra delay after filling address
                except Exception as e:
                    print(f"⚠️  Address field not found: {str(e)}")
                
                # Suite/Apt (optional - may be empty)
                if CHECKOUT_DATA['suite_apt']:
                    try:
                        print("Waiting for suite/apt field...")
                        await page.wait_for_selector('input[name="address2"]', state='visible', timeout=10000)
                        await page.fill('input[name="address2"]', CHECKOUT_DATA['suite_apt'])
                        print("✓ Suite/Apt filled")
                        await asyncio.sleep(0.1)
                    except Exception as e:
                        print(f"⚠️  Suite/Apt field not found: {str(e)}")
                
                # City
                try:
                    print("Waiting for city field...")
                    await page.wait_for_selector('input[name="city"]', state='visible', timeout=10000)
                    await page.fill('input[name="city"]', CHECKOUT_DATA['city'])
                    print("✓ City filled")
                    await asyncio.sleep(0.1)
                except Exception as e:
                    print(f"⚠️  City field not found: {str(e)}")
                
                # State
                try:
                    print("Waiting for state field...")
                    await page.wait_for_selector('select[name="zone"]', state='visible', timeout=10000)
                    await page.select_option('select[name="zone"]', CHECKOUT_DATA['state'])
                    print("✓ State selected")
                    await asyncio.sleep(0.1)
                except Exception as e:
                    print(f"⚠️  State field not found: {str(e)}")
                
                # Zipcode
                try:
                    print("Waiting for zipcode field...")
                    await page.wait_for_selector('input[name="postalCode"]', state='visible', timeout=10000)
                    await page.fill('input[name="postalCode"]', CHECKOUT_DATA['zip_code'])
                    print("✓ Zipcode filled")
                    await asyncio.sleep(0.1)
                except Exception as e:
                    print(f"⚠️  Zipcode field not found: {str(e)}")
                
                # Phone
                try:
                    print("Waiting for phone field...")
                    await page.wait_for_selector('input[name="phone"]', state='visible', timeout=10000)
                    await page.fill('input[name="phone"]', CHECKOUT_DATA['phone'])
                    print("✓ Phone filled")
                    await asyncio.sleep(0.1)
                except Exception as e:
                    print(f"⚠️  Phone field not found: {str(e)}")
                
                # Wait a second for loading
                await asyncio.sleep(1)
                print("Waiting for payment form to load...")
                
                # Credit card number - try both direct and iframe
                if CHECKOUT_DATA['card_number']:
                    try:
                        print("Waiting for credit card number field...")
                        # Try direct selector first
                        try:
                            await page.wait_for_selector('#number', state='visible', timeout=5000)
                            await page.fill('#number', CHECKOUT_DATA['card_number'])
                            print("✓ Credit card number filled")
                        except Exception:
                            # Try iframe
                            frames = page.frames
                            for frame in frames:
                                try:
                                    card_input = frame.locator('#number, input[name="number"], input[id="number"]')
                                    if await card_input.count() > 0:
                                        await card_input.fill(CHECKOUT_DATA['card_number'])
                                        print("✓ Credit card number filled (in iframe)")
                                        break
                                except Exception:
                                    continue
                            else:
                                # Try with frame_locator
                                card_iframe = page.frame_locator('iframe').first
                                await card_iframe.locator('#number, input[name="number"]').fill(CHECKOUT_DATA['card_number'])
                                print("✓ Credit card number filled (via frame_locator)")
                        await asyncio.sleep(0.1)
                    except Exception as e:
                        print(f"⚠️  Credit card number field not found: {str(e)}")
                
                # Expiration date - try both direct and iframe
                if CHECKOUT_DATA['expiry']:
                    try:
                        print("Waiting for expiration date field...")
                        # Try direct selector first
                        try:
                            await page.wait_for_selector('#expiry', state='visible', timeout=5000)
                            await page.fill('#expiry', CHECKOUT_DATA['expiry'])
                            print("✓ Expiration date filled")
                        except Exception:
                            # Try iframe
                            frames = page.frames
                            for frame in frames:
                                try:
                                    expiry_input = frame.locator('#expiry, input[name="expiry"], input[id="expiry"]')
                                    if await expiry_input.count() > 0:
                                        await expiry_input.fill(CHECKOUT_DATA['expiry'])
                                        print("✓ Expiration date filled (in iframe)")
                                        break
                                except Exception:
                                    continue
                            else:
                                # Try with frame_locator
                                card_iframe = page.frame_locator('iframe').first
                                await card_iframe.locator('#expiry, input[name="expiry"]').fill(CHECKOUT_DATA['expiry'])
                                print("✓ Expiration date filled (via frame_locator)")
                        await asyncio.sleep(0.1)
                    except Exception as e:
                        print(f"⚠️  Expiration date field not found: {str(e)}")
                
                # CVV - try both direct and iframe
                if CHECKOUT_DATA['cvv']:
                    try:
                        print("Waiting for CVV field...")
                        # Try direct selector first
                        try:
                            await page.wait_for_selector('#verification_value', state='visible', timeout=5000)
                            await page.fill('#verification_value', CHECKOUT_DATA['cvv'])
                            print("✓ CVV filled")
                        except Exception:
                            # Try iframe
                            frames = page.frames
                            for frame in frames:
                                try:
                                    cvv_input = frame.locator('#verification_value, input[name="verification_value"], input[id="verification_value"]')
                                    if await cvv_input.count() > 0:
                                        await cvv_input.fill(CHECKOUT_DATA['cvv'])
                                        print("✓ CVV filled (in iframe)")
                                        break
                                except Exception:
                                    continue
                            else:
                                # Try with frame_locator
                                card_iframe = page.frame_locator('iframe').first
                                await card_iframe.locator('#verification_value, input[name="verification_value"]').fill(CHECKOUT_DATA['cvv'])
                                print("✓ CVV filled (via frame_locator)")
                        await asyncio.sleep(0.1)
                    except Exception as e:
                        print(f"⚠️  CVV field not found: {str(e)}")
                
                # Wait a second
                await asyncio.sleep(1)
                print("Waiting before clicking checkout button...")
                
                # Uncheck RememberMe checkbox
                try:
                    remember_checkbox = page.locator('#RememberMe-RememberMeCheckbox')
                    if await remember_checkbox.count() > 0:
                        is_checked = await remember_checkbox.is_checked()
                        if is_checked:
                            await remember_checkbox.uncheck()
                            print("✓ RememberMe checkbox unchecked")
                            await asyncio.sleep(0.1)
                        else:
                            print("✓ RememberMe checkbox already unchecked")
                    else:
                        print("⚠️  RememberMe checkbox not found")
                except Exception as e:
                    print(f"⚠️  Could not uncheck RememberMe checkbox: {str(e)}")
                
                # Refill address field (sometimes it gets deleted before checkout)
                try:
                    print("Refilling address field before checkout...")
                    address_field = page.locator('input[name="address1"]')
                    if await address_field.count() > 0:
                        current_value = await address_field.input_value()
                        if not current_value or current_value != CHECKOUT_DATA['address']:
                            await asyncio.sleep(0.3)  # Extra delay before refilling address
                            await address_field.fill(CHECKOUT_DATA['address'])
                            print(f"✓ Address field refilled: {CHECKOUT_DATA['address']}")
                            await asyncio.sleep(0.3)  # Extra delay after refilling address
                        else:
                            print("✓ Address field already has correct value")
                    else:
                        print("⚠️  Address field not found for refill")
                except Exception as e:
                    print(f"⚠️  Could not refill address field: {str(e)}")
                
                # Click checkout button
                try:
                    checkout_button = page.locator('#checkout-pay-button')
                    await checkout_button.wait_for(state='visible', timeout=10000)
                    await asyncio.sleep(1)  # Wait 1 second before clicking pay button
                    await checkout_button.click()
                    print("✓ Checkout button clicked")
                except Exception:
                    print("⚠️  Checkout button not found or could not be clicked")
                
                # Keep browser open - user closes manually
                print("\nBrowser is open. Close manually when done.")
                # Wait indefinitely until user closes browser or script is interrupted
                try:
                    while True:
                        await asyncio.sleep(60)  # Check every minute
                except KeyboardInterrupt:
                    print("\nClosing browser...")
                    await browser.close()
                    print("Browser closed")
                
            finally:
                # Only close if not already closed
                try:
                    await browser.close()
                except Exception:
                    pass
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        error_info = {
            'success': False,
            'error': str(e),
            'step': 'Unknown step',
            'request_log': request_log if 'request_log' in locals() else []
        }
        print(f"Error: {str(e)}")
        return error_info


# Example usage
if __name__ == "__main__":
    import asyncio
    asyncio.run(shopify_checkout(
        "https://thursdayboots.com/products/mens-premier-low-top-sneaker-black-matte",
        "7"
    ))
