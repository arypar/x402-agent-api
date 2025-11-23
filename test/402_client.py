"""
x402 Client Example - Programmatic Payment Handler
This demonstrates how an agent can programmatically handle x402 payments
without a frontend wallet UI.
"""

import requests
import json
from typing import Optional

class X402Client:
    """
    A simple client that handles x402 payment protocol automatically.
    
    Flow:
    1. Make initial request to endpoint
    2. If 402 received, parse payment instructions
    3. Sign and submit payment transaction
    4. Retry request with payment proof in X-PAYMENT header
    """
    
    def __init__(self, private_key: str, wallet_address: str):
        """
        Initialize the x402 client.
        
        Args:
            private_key: Your wallet's private key for signing transactions
            wallet_address: Your wallet address for payments
        """
        self.private_key = private_key
        self.wallet_address = wallet_address
        self.session = requests.Session()
    
    def request(self, url: str, method: str = "GET", **kwargs) -> requests.Response:
        """
        Make a request that automatically handles x402 payment requirements.
        
        Args:
            url: The endpoint URL
            method: HTTP method (GET, POST, etc.)
            **kwargs: Additional arguments to pass to requests
            
        Returns:
            Response from the server after payment (if required)
        """
        # Step 1: Make initial request
        response = self.session.request(method, url, **kwargs)
        
        # Step 2: Check if payment is required
        if response.status_code == 402:
            print(f"💳 Payment required for {url}")
            
            # Parse payment instructions from response
            payment_info = self._parse_payment_instructions(response)
            
            if payment_info:
                print(f"   Amount: {payment_info['amount']} {payment_info['currency']}")
                print(f"   Recipient: {payment_info['recipient']}")
                print(f"   Network: {payment_info['network']}")
                
                # Step 3: Generate payment proof
                payment_proof = self._generate_payment_proof(payment_info)
                
                # Step 4: Retry request with payment proof
                headers = kwargs.get('headers', {})
                headers['X-PAYMENT'] = payment_proof
                kwargs['headers'] = headers
                
                print("   ✓ Payment proof generated, retrying request...")
                response = self.session.request(method, url, **kwargs)
                
                if response.status_code == 200:
                    print("   ✓ Payment accepted, access granted!")
                else:
                    print(f"   ✗ Payment rejected: {response.status_code}")
        
        return response
    
    def _parse_payment_instructions(self, response: requests.Response) -> Optional[dict]:
        """
        Parse payment instructions from 402 response.
        
        The x402 protocol typically returns payment details in the response body
        or headers. Format may vary by implementation.
        """
        try:
            # Try to parse JSON response body
            data = response.json()
            
            # Common x402 response format
            if 'payment' in data:
                payment_data = data['payment']
                return {
                    'amount': payment_data.get('amount'),
                    'currency': payment_data.get('currency', 'USDC'),
                    'recipient': payment_data.get('recipient'),
                    'network': payment_data.get('network', 'base'),
                    'nonce': payment_data.get('nonce'),
                }
            
            # Alternative format: flat structure
            if 'amount' in data and 'recipient' in data:
                return {
                    'amount': data.get('amount'),
                    'currency': data.get('currency', 'USDC'),
                    'recipient': data.get('recipient'),
                    'network': data.get('network', 'base'),
                    'nonce': data.get('nonce'),
                }
                
        except Exception as e:
            print(f"   ✗ Failed to parse payment instructions: {e}")
        
        return None
    
    def _generate_payment_proof(self, payment_info: dict) -> str:
        """
        Generate a cryptographic proof of payment.
        
        This is a PLACEHOLDER implementation. In production, you would:
        1. Create a payment transaction on the specified blockchain
        2. Sign it with your private key
        3. Submit to the network
        4. Get the transaction hash/signature as proof
        
        For real implementation, you would use:
        - web3.py (for Ethereum/Base)
        - solana-py (for Solana)
        - ethers-py (alternative for EVM chains)
        """
        
        # PLACEHOLDER: Real implementation would create actual blockchain transaction
        # Example for Ethereum/Base (EVM):
        """
        from web3 import Web3
        from eth_account import Account
        
        # Connect to network RPC
        w3 = Web3(Web3.HTTPProvider('https://base-mainnet.infura.io/v3/YOUR_KEY'))
        
        # Create transaction
        tx = {
            'to': payment_info['recipient'],
            'value': w3.toWei(payment_info['amount'], 'ether'),
            'gas': 21000,
            'gasPrice': w3.eth.gas_price,
            'nonce': w3.eth.get_transaction_count(self.wallet_address),
            'chainId': 8453  # Base mainnet
        }
        
        # Sign transaction
        signed = w3.eth.account.sign_transaction(tx, self.private_key)
        
        # Send transaction
        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
        
        # Return transaction hash as proof
        return tx_hash.hex()
        """
        
        # For now, return a mock payment proof
        mock_proof = {
            'signature': f"0x_signed_payment_proof_for_{payment_info['amount']}_{payment_info['currency']}",
            'sender': self.wallet_address,
            'timestamp': int(__import__('time').time()),
            'nonce': payment_info.get('nonce', 0)
        }
        
        return json.dumps(mock_proof)
    
    def get(self, url: str, **kwargs) -> requests.Response:
        """Convenience method for GET requests"""
        return self.request(url, "GET", **kwargs)
    
    def post(self, url: str, **kwargs) -> requests.Response:
        """Convenience method for POST requests"""
        return self.request(url, "POST", **kwargs)


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Initialize client with your wallet credentials
    # ⚠️ IMPORTANT: Never hardcode real private keys! Use environment variables.
    client = X402Client(
        private_key="YOUR_PRIVATE_KEY_HERE",  # Use os.getenv('PRIVATE_KEY') in production
        wallet_address="0x71C7656EC7ab88b098defB751B7401B5f6d8976F"
    )
    
    base_url = "http://localhost:8001"
    
    print("=" * 60)
    print("X402 Client Test - Programmatic Payment Handler")
    print("=" * 60)
    
    # Test 1: Free endpoint (should work without payment)
    print("\n1. Testing FREE endpoint: /health")
    response = client.get(f"{base_url}/health")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    # Test 2: Premium endpoint (requires payment)
    print("\n2. Testing PREMIUM endpoint: /premium")
    response = client.get(f"{base_url}/premium")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print(f"   Response: {response.json()}")
    else:
        print(f"   Error: {response.text}")
    
    # Test 3: Expensive endpoint (requires payment)
    print("\n3. Testing EXPENSIVE endpoint: /expensive")
    response = client.get(f"{base_url}/expensive")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print(f"   Response: {response.json()}")
    else:
        print(f"   Error: {response.text}")
    
    print("\n" + "=" * 60)

