import os
import requests
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

EXA_API_KEY = os.getenv('EXA_API')


def is_shopify_store(product_url):
    """
    Verify if a URL is a Shopify store by checking the Powered-By header
    
    Args:
        product_url: Product URL to verify
    
    Returns:
        bool: True if it's a Shopify store, False otherwise
    """
    try:
        # Extract base/home URL from product URL
        parsed = urlparse(product_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        
        # Make a HEAD request to check headers (more efficient than GET)
        try:
            response = requests.head(base_url, timeout=5, allow_redirects=True)
        except Exception:
            # Fallback to GET if HEAD is not supported
            response = requests.get(base_url, timeout=5, allow_redirects=True)
        
        # Check for Powered-By header
        powered_by = response.headers.get('Powered-By', '')
        if powered_by == 'Shopify':
            return True
        
        # Also check X-Shopify-* headers as additional verification
        shopify_headers = [key for key in response.headers.keys() if key.lower().startswith('x-shopify-')]
        if shopify_headers:
            return True
        
        return False
        
    except Exception as e:
        # If we can't verify, return False to be safe
        print(f"⚠️  Could not verify Shopify store for {product_url}: {str(e)}")
        return False


def extract_base_url(product_url):
    """
    Extract the base/home URL from a product URL
    
    Args:
        product_url: Full product URL
    
    Returns:
        str: Base URL (e.g., https://example.com from https://example.com/products/item)
    """
    parsed = urlparse(product_url)
    return f"{parsed.scheme}://{parsed.netloc}"


def search_shopify_products(query, num_results=10):
    """
    Search for Shopify product links using Exa API
    
    Args:
        query: Search query (e.g., "black tshirt")
        num_results: Number of results to return (default: 10)
    
    Returns:
        List of Shopify product URLs
    """
    
    if not EXA_API_KEY:
        raise ValueError("EXA_API_KEY not found in environment variables. Please set EXA_API in .env file.")
    
    # Exa API endpoint
    url = "https://api.exa.ai/search"
    
    # Headers
    headers = {
        "x-api-key": EXA_API_KEY,
        "Content-Type": "application/json"
    }
    
    # Remove "shopify" from query and search broadly
    clean_query = query.replace('shopify', '').replace('Shopify', '').strip()
    clean_query = ' '.join(clean_query.split())  # Remove extra spaces
    
    payload = {
        "query": clean_query,
        "num_results": 50,  # Get 50 results to filter
        "type": "neural",
        "use_autoprompt": True,
    }
    
    try:
        print(f"Searching Exa API for: {clean_query} (removed 'shopify' from query)")
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        results = data.get('results', [])
        print(f"✓ Received {len(results)} results from Exa")
        
        # Filter for product URLs and verify they're actually Shopify stores
        product_urls = []
        seen_urls = set()
        verified_stores = {}  # Cache verified stores to avoid duplicate checks
        
        for result in results:
            url = result.get('url', '')
            # Check if it's a product URL pattern
            if '/products/' in url.lower():
                # Normalize URL (remove query params, fragments)
                clean_url = url.split('?')[0].split('#')[0]
                
                if clean_url not in seen_urls:
                    seen_urls.add(clean_url)
                    base_url = extract_base_url(clean_url)
                    
                    # Check if we've already verified this store
                    if base_url not in verified_stores:
                        print(f"Verifying Shopify store: {base_url}...")
                        verified_stores[base_url] = is_shopify_store(clean_url)
                    
                    # Only add if it's a verified Shopify store
                    if verified_stores[base_url]:
                        product_urls.append(clean_url)
                        if len(product_urls) >= num_results:
                            break
        
        print(f"✓ Found {len(product_urls)} verified Shopify product URLs")
        return product_urls
        
    except requests.exceptions.RequestException as e:
        print(f"Error calling Exa API: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        raise
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise


# Example usage
if __name__ == "__main__":
    query = "mens white shirt purchase link"
    
    print("=" * 60)
    print("Testing Shopify Product Search with Exa API")
    print("=" * 60)
    
    try:
        urls = search_shopify_products(query, num_results=5)
        
        print(f"\nFound {len(urls)} Shopify product URLs:\n")
        for i, url in enumerate(urls, 1):
            print(f"{i}. {url}")
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
