import os
import json
import requests
import time
import jwt
from dotenv import load_dotenv
from typing import Optional, Dict, Any
from urllib.parse import urlencode

# Load environment variables from .env file
load_dotenv()

# Load API credentials from .env
# COINBASE_API_KEY_ID: Your API key ID
# COINBASE_API_KEY_SECRET: Your API key secret (EC private key or Ed25519 key)
API_KEY_NAME = os.getenv("COINBASE_API_KEY_ID")
API_PRIVATE_KEY = os.getenv("COINBASE_API_KEY_SECRET")

if not API_KEY_NAME:
    raise ValueError("COINBASE_API_KEY_ID not found in .env file")

if not API_PRIVATE_KEY:
    raise ValueError("COINBASE_API_KEY_SECRET not found in .env file")

# API Configuration (matching onramp.js)
API_HOST = 'api.cdp.coinbase.com'
API_PATH = '/platform/v2/onramp/sessions'
ONRAMP_BASE_URL = 'https://www.coinbase.com/onramp'

# Onramp session configuration (matching onramp.js SESSION_CONFIG)
SESSION_CONFIG = {
    "purchaseCurrency": "USDC",
    "destinationNetwork": "base",
    "destinationAddress": "0x71C7656EC7ab88b098defB751B7401B5f6d8976F",
    "paymentAmount": "5.00",
    "paymentCurrency": "USD",
    "paymentMethod": "CARD",
    "country": "US",
    "subdivision": "NY",
    "redirectUrl": "https://yourapp.com/success",
    "clientIp": "181.10.161.120",
    "partnerUserRef": "user-1234"
}

def generate_jwt(request_method: str, request_path: str) -> str:
    """
    Build a short-lived JWT for a specific REST request.

    request_method: "GET", "POST", etc.
    request_path: the path part ONLY, e.g.:
        "/platform/v2/onramp/sessions"
        "/api/v3/brokerage/accounts"
    """
    # Build the URI claim for REST auth
    uri = f"{request_method} {API_HOST}{request_path}"
    
    # Current timestamp
    current_time = int(time.time())
    
    # JWT payload
    payload = {
        'iss': 'cdp',
        'nbf': current_time,
        'exp': current_time + 120,  # 2 minutes expiration
        'sub': API_KEY_NAME,
        'uri': uri
    }
    
    # JWT headers
    headers_dict = {
        'kid': API_KEY_NAME,
        'nonce': str(int(time.time() * 1000))  # milliseconds timestamp
    }
    
    # Determine algorithm based on key format
    if API_PRIVATE_KEY.startswith('-----BEGIN EC PRIVATE KEY-----'):
        # EC key (ES256)
        algorithm = 'ES256'
        private_key = API_PRIVATE_KEY
    else:
        # Ed25519 key (EdDSA) - base64 encoded
        algorithm = 'EdDSA'
        # For EdDSA, we need to decode the base64 key
        import base64
        from cryptography.hazmat.primitives.asymmetric import ed25519
        
        key_bytes = base64.b64decode(API_PRIVATE_KEY)
        private_key = ed25519.Ed25519PrivateKey.from_private_bytes(key_bytes[:32])
    
    # Generate JWT
    jwt_token = jwt.encode(payload, private_key, algorithm=algorithm, headers=headers_dict)
    
    return jwt_token


def create_onramp_session(jwt: str, session_config: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """
    Create an onramp session using the Coinbase API.
    
    Args:
        jwt: JWT bearer token for authentication
        session_config: Optional session configuration dict. If None, uses SESSION_CONFIG.
    
    Returns:
        Session data dictionary or None if creation fails
    """
    url = f"https://{API_HOST}{API_PATH}"
    
    headers = {
        'Authorization': f'Bearer {jwt}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    payload = session_config if session_config else SESSION_CONFIG
    
    print(f"\nMaking POST request to: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        
        if not response.ok:
            error_text = response.text
            raise Exception(f"HTTP {response.status_code}: {error_text}")
        
        session_data = response.json()
        print("\n✓ Created onramp session successfully!")
        print(f"Response: {json.dumps(session_data, indent=2)}")
        
        return session_data
        
    except Exception as error:
        raise Exception(f"Failed to create onramp session: {str(error)}")


def generate_onramp_url(session_token: str) -> str:
    """
    Generate an onramp URL with session token.
    
    Args:
        session_token: Session token from the onramp session
    
    Returns:
        Complete onramp URL
    """
    params = {'sessionToken': session_token}
    query_string = urlencode(params)
    return f"{ONRAMP_BASE_URL}?{query_string}"


def create_fresh_onramp_link(custom_config: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """
    Generate a fresh, single-use onramp link.
    
    ⚠️ CRITICAL: Each onramp URL is SINGLE-USE ONLY!
    - Once the URL is opened/used to launch Coinbase Onramp, it becomes invalid
    - You MUST call this function again to generate a new URL for each transaction
    - Do NOT cache, store, or reuse the generated URLs
    - Do NOT share URLs between users or sessions
    
    Args:
        custom_config: Optional custom session configuration. If None, uses SESSION_CONFIG.
    
    Returns:
        Fresh onramp URL (single-use only)
    """
    try:
        # Generate JWT
        jwt_token = generate_jwt("POST", API_PATH)
        
        # Create onramp session
        session_data = create_onramp_session(jwt_token, custom_config)
        
        # Extract and return onramp URL
        onramp_url = session_data.get('session', {}).get('onrampUrl')
        
        if not onramp_url:
            raise Exception("Onramp URL not found in response")
        
        return onramp_url
        
    except Exception as error:
        print(f"Error creating onramp link: {str(error)}")
        return None


def main():
    """
    Main function to generate JWT, create onramp session, and generate onramp URL.
    
    Note: Each onramp URL can only be used ONCE. Run this script again to generate a new link.
    """
    print("=" * 60)
    print("Coinbase Onramp Link Generator (Python)")
    print("=" * 60)
    print("\n⚠️  Note: Each onramp link can only be used ONCE!")
    print("   Run this script again to generate a fresh link.\n")
    
    try:
        # Step 1: Generate JWT
        print("[1/3] Generating JWT bearer token...")
        jwt_token = generate_jwt("POST", API_PATH)
        print(f"✓ Generated JWT token: {jwt_token[:50]}...")
        
        # Step 2: Create onramp session
        print("\n[2/3] Creating onramp session...")
        session_data = create_onramp_session(jwt_token)
        
        # Extract onramp URL from response
        # The API returns the complete URL in session.onrampUrl
        onramp_url = session_data.get('session', {}).get('onrampUrl')
        
        if not onramp_url:
            print("\n✗ Onramp URL not found in response")
            return None
        
        # Step 3: Display the onramp link
        print("\n[3/3] Onramp link ready!")
        print("\n✓ Onramp link generated successfully!")
        print(f"\n{'=' * 60}")
        print("🔗 Fresh Onramp URL (single-use only):")
        print(onramp_url)
        print(f"{'=' * 60}\n")
        
        return onramp_url
        
    except Exception as error:
        print(f"\n✗ Error: {str(error)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    main()
