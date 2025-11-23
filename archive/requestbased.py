import requests
import re
import json
from bs4 import BeautifulSoup


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
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Look for the hidden input field with name="authenticity_token"
        token_input = soup.find('input', {'name': 'authenticity_token', 'type': 'hidden'})
        
        if token_input and token_input.get('value'):
            token = token_input.get('value')
            print(f"✓ Successfully extracted authenticity token: {token[:30]}...")
            return token
        
        # Fallback: Try to find it using regex
        token_match = re.search(r'name="authenticity_token"\s+value="([^"]+)"', html_content)
        if token_match:
            token = token_match.group(1)
            print(f"✓ Successfully extracted authenticity token (via regex): {token[:30]}...")
            return token
        
        raise ValueError("Authenticity token not found in HTML response")
        
    except Exception as e:
        raise ValueError(f"Failed to extract authenticity token: {str(e)}")


def main():
    """Main function to demonstrate requests session with token scraping"""
    print("="*60)
    print("Starting Request-Based Authentication Flow")
    print("="*60)
    
    try:
        # Create a session to persist cookies and headers
        session = requests.Session()
        
        # URL to fetch
        url = "https://mimik-ai-3.myshopify.com/password"
        
        # Headers for the GET request
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
        
        # Step 1: Make GET request to password page
        print("\n[Step 1] Fetching password page...")
        try:
            response = session.get(url, headers=headers, timeout=10)
            response.raise_for_status()  # Raise exception for 4xx/5xx status codes
            print(f"✓ Successfully fetched page (Status: {response.status_code})")
        except requests.exceptions.Timeout:
            print("✗ Error: Request timed out")
            return
        except requests.exceptions.ConnectionError:
            print("✗ Error: Failed to connect to server")
            return
        except requests.exceptions.HTTPError as e:
            print(f"✗ HTTP Error: {e}")
            return
        except requests.exceptions.RequestException as e:
            print(f"✗ Request Error: {e}")
            return
        
        # Step 2: Extract authenticity token from response
        print("\n[Step 2] Extracting authenticity token from HTML...")
        try:
            authenticity_token = extract_authenticity_token(response.text)
        except ValueError as e:
            print(f"✗ Error: {e}")
            return
        
        # Step 3: POST authentication with extracted token
        print("\n[Step 3] Authenticating with password...")
        
        # URL encode the token and password
        from urllib.parse import urlencode
        payload = urlencode({
            'authenticity_token': authenticity_token,
            'password': 'aryanparekh'
        })
        
        # Headers for POST request
        post_headers = {
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
            response2 = session.post(url, headers=post_headers, data=payload, timeout=10, allow_redirects=True)
            response2.raise_for_status()
            print(f"✓ Authentication successful (Status: {response2.status_code})")
            print(f"✓ Redirected to: {response2.url}")
        except requests.exceptions.RequestException as e:
            print(f"✗ Authentication failed: {e}")
            return None, None
        
        # Step 4: Navigate to product page
        print("\n[Step 4] Navigating to product page...")
        product_url = "https://mimik-ai-3.myshopify.com/products/the-collection-snowboard-liquid"
        product_headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'accept-language': 'en-US,en;q=0.9',
            'referer': 'https://mimik-ai-3.myshopify.com/',
            'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36'
        }
        
        try:
            response3 = session.get(product_url, headers=product_headers, timeout=10)
            response3.raise_for_status()
            print(f"✓ Product page loaded (Status: {response3.status_code})")
        except requests.exceptions.RequestException as e:
            print(f"✗ Failed to load product page: {e}")
            return None, None
        
        # Step 5: Add product to cart
        print("\n[Step 5] Adding product to cart...")
        cart_add_url = "https://mimik-ai-3.myshopify.com/cart/add"
        cart_payload = {
            'form_type': 'product',
            'utf8': '✓',
            'id': '51009883865301',
            'product-id': '8875566891221',
            'section-id': 'template--18714050855125__main',
            'sections': 'cart-drawer,cart-icon-bubble',
            'sections_url': '/products/the-collection-snowboard-liquid',
            'selling_plan': ''
        }
        
        cart_headers = {
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
            # Use POST instead of GET for adding to cart
            response4 = session.post(cart_add_url, headers=cart_headers, data=cart_payload, timeout=10)
            response4.raise_for_status()
            print(f"✓ Product added to cart (Status: {response4.status_code})")
        except requests.exceptions.RequestException as e:
            print(f"✗ Failed to add product to cart: {e}")
            return None, None
        
        # Step 6: Proceed to checkout
        print("\n[Step 6] Proceeding to checkout...")
        checkout_url = "https://mimik-ai-3.myshopify.com/cart"
        checkout_payload = 'updates%5B%5D=1&checkout='
        
        checkout_headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-US,en;q=0.9',
            'cache-control': 'max-age=0',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://mimik-ai-3.myshopify.com',
            'priority': 'u=0, i',
            'referer': 'https://mimik-ai-3.myshopify.com/products/the-collection-snowboard-liquid',
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
            response5 = session.post(checkout_url, headers=checkout_headers, data=checkout_payload, timeout=10, allow_redirects=True)
            response5.raise_for_status()
            print(f"✓ Proceeded to checkout (Status: {response5.status_code})")
            print(f"✓ Redirected to checkout URL")
        except requests.exceptions.RequestException as e:
            print(f"✗ Failed to proceed to checkout: {e}")
            return None, None
        
        # Step 7: Display intermediate results
        print("\n" + "="*60)
        print("INTERMEDIATE RESULTS")
        print("="*60)
        print(f"\n✓ Authenticated: Yes")
        print(f"✓ Product Added to Cart: Yes")
        print(f"✓ Proceeded to Checkout: Yes")
        
        print("\n" + "-"*60)
        print("CHECKOUT URL:")
        print("-"*60)
        print(f"{response5.url}")
        print("-"*60)
        
        # Note: In a real scenario, you would need to:
        # 1. Parse the checkout URL to extract session tokens
        # 2. Extract queue tokens from the page HTML/JavaScript
        # 3. Dynamically build the GraphQL query with extracted values
        # For demonstration, this uses hardcoded values from a sample request
        
        print("\n[Step 7] Submitting checkout proposal (GraphQL)...")
        print("Note: This step requires dynamic token extraction from the checkout page")
        print("The following is a demonstration with example values...")
        
        # GraphQL endpoint
        graphql_url = "https://mimik-ai-3.myshopify.com/checkouts/unstable/graphql?operationName=Proposal"
        
        # This is an example payload - in production, sessionToken and queueToken 
        # would be extracted from the checkout page
        graphql_payload = json.dumps({
            "query": "query Proposal($sessionInput:SessionTokenInput!,$queueToken:String){session(sessionInput:$sessionInput){negotiate(input:{queueToken:$queueToken}){__typename result{...on NegotiationResultAvailable{checkpointData queueToken __typename}__typename}}__typename}}",
            "variables": {
                "sessionInput": {
                    "sessionToken": "EXAMPLE_SESSION_TOKEN_FROM_CHECKOUT_PAGE"
                },
                "queueToken": "EXAMPLE_QUEUE_TOKEN"
            },
            "operationName": "Proposal"
        })
        
        graphql_headers = {
            'accept': 'application/json',
            'accept-language': 'en-US',
            'content-type': 'application/json',
            'origin': 'https://mimik-ai-3.myshopify.com',
            'referer': response5.url,
            'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'shopify-checkout-client': 'checkout-web/1.0',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36'
        }
        
        print("⚠️  Skipping GraphQL request - requires dynamic token extraction")
        print("   In a real implementation:")
        print("   1. Parse checkout URL HTML to extract session tokens")
        print("   2. Extract queue tokens from page JavaScript")
        print("   3. Build GraphQL mutation with shipping/billing info")
        print("   4. Submit proposal and handle response")
        
        # Step 8: Final results
        print("\n" + "="*60)
        print("FINAL RESULTS")
        print("="*60)
        
        print("\nSession Cookies (Ready for Browser-Use):")
        if session.cookies:
            for cookie in session.cookies:
                print(f"  - {cookie.name}: {cookie.value[:50]}{'...' if len(cookie.value) > 50 else ''}")
        else:
            print("  (No cookies set)")
        
        print("\n" + "="*60)
        print("SUCCESS: Checkout URL generated!")
        print("These cookies can now be transferred to Browser-Use")
        print("to complete the checkout form with AI")
        print("="*60)
        
        return session, response5.url
        
    except KeyboardInterrupt:
        print("\n\n✗ Operation cancelled by user")
        return None, None
    except Exception as e:
        print(f"\n✗ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None


if __name__ == "__main__":
    main()

