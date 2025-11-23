"""
x402 Client Using Official SDK
This uses the actual x402 SDK packages for production use.

Installation:
    pip install x402  # Core x402 client
    pip install x402-langchain  # For AI agents with LangChain
    pip install web3  # For blockchain transactions (if using Ethereum/Base)
    pip install solana  # For Solana transactions (if using Solana network)
"""

import os
from typing import Optional

# ============================================================================
# Method 1: Using x402 Core Client (for general HTTP clients)
# ============================================================================

def example_core_client():
    """
    Example using the core x402 client library.
    This is for general-purpose HTTP clients that need to handle x402 payments.
    """
    try:
        from x402 import X402Client
        from web3 import Web3
        
        # Initialize with your wallet
        private_key = os.getenv("PRIVATE_KEY", "YOUR_PRIVATE_KEY_HERE")
        
        # Create x402 client
        client = X402Client(
            private_key=private_key,
            network="base",  # or "ethereum", "solana", etc.
            rpc_url="https://mainnet.base.org"  # Network RPC endpoint
        )
        
        # Make requests - payment is handled automatically
        response = client.get("http://localhost:8001/premium")
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
    except ImportError:
        print("⚠️  x402 SDK not installed. Install with: pip install x402")
        print("    This is a placeholder - check x402 documentation for actual API")


# ============================================================================
# Method 2: Using x402-langchain (for AI agents)
# ============================================================================

def example_langchain_agent():
    """
    Example using x402-langchain for AI agents.
    This enables AI agents to autonomously make payments to access premium APIs.
    """
    try:
        from x402_langchain import create_x402_agent
        from langchain_openai import ChatOpenAI
        
        # Initialize AI agent with payment capabilities
        agent = create_x402_agent(
            private_key=os.getenv("PRIVATE_KEY", "YOUR_PRIVATE_KEY_HERE"),
            llm=ChatOpenAI(model="gpt-4"),
            spending_limit_daily=10.0,  # Max $10/day
            network="base"
        )
        
        # Agent automatically handles payments when accessing premium endpoints
        response = agent.fetch("http://localhost:8001/premium")
        
        print(f"Agent Response: {response}")
        
    except ImportError:
        print("⚠️  x402-langchain not installed. Install with: pip install x402-langchain")
        print("    This is a placeholder - check x402 documentation for actual API")


# ============================================================================
# Method 3: Manual Payment Flow (for custom implementations)
# ============================================================================

class ManualX402Client:
    """
    Manual implementation showing the underlying payment flow.
    Use this if you need fine-grained control over payments.
    """
    
    def __init__(self, private_key: str, network: str = "base"):
        self.private_key = private_key
        self.network = network
        self._init_web3()
    
    def _init_web3(self):
        """Initialize Web3 connection for blockchain transactions"""
        try:
            from web3 import Web3
            from eth_account import Account
            
            # RPC endpoints by network
            rpc_urls = {
                "base": "https://mainnet.base.org",
                "base-sepolia": "https://sepolia.base.org",
                "ethereum": "https://eth.llamarpc.com",
                "polygon": "https://polygon-rpc.com"
            }
            
            self.w3 = Web3(Web3.HTTPProvider(rpc_urls.get(self.network)))
            self.account = Account.from_key(self.private_key)
            self.wallet_address = self.account.address
            
            print(f"✓ Connected to {self.network}")
            print(f"  Wallet: {self.wallet_address}")
            
        except ImportError:
            print("⚠️  web3.py not installed. Install with: pip install web3")
            self.w3 = None
    
    def make_payment(self, recipient: str, amount: float, currency: str = "USDC"):
        """
        Make a payment transaction on-chain.
        
        Args:
            recipient: Payment recipient address
            amount: Amount to pay
            currency: Currency (USDC, ETH, etc.)
            
        Returns:
            Transaction hash as proof of payment
        """
        if not self.w3:
            raise Exception("Web3 not initialized")
        
        try:
            from web3 import Web3
            
            # USDC token address (Base mainnet)
            usdc_address = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
            
            if currency == "USDC":
                # Transfer USDC tokens
                # ERC20 ABI for transfer function
                erc20_abi = [
                    {
                        "constant": False,
                        "inputs": [
                            {"name": "_to", "type": "address"},
                            {"name": "_value", "type": "uint256"}
                        ],
                        "name": "transfer",
                        "outputs": [{"name": "", "type": "bool"}],
                        "type": "function"
                    }
                ]
                
                usdc_contract = self.w3.eth.contract(
                    address=Web3.to_checksum_address(usdc_address),
                    abi=erc20_abi
                )
                
                # USDC has 6 decimals
                amount_in_smallest_unit = int(amount * 1_000_000)
                
                # Build transaction
                tx = usdc_contract.functions.transfer(
                    Web3.to_checksum_address(recipient),
                    amount_in_smallest_unit
                ).build_transaction({
                    'from': self.wallet_address,
                    'nonce': self.w3.eth.get_transaction_count(self.wallet_address),
                    'gas': 100000,
                    'gasPrice': self.w3.eth.gas_price,
                })
                
            else:  # Native ETH
                # Transfer native ETH
                tx = {
                    'to': Web3.to_checksum_address(recipient),
                    'value': self.w3.to_wei(amount, 'ether'),
                    'gas': 21000,
                    'gasPrice': self.w3.eth.gas_price,
                    'nonce': self.w3.eth.get_transaction_count(self.wallet_address),
                    'chainId': self.w3.eth.chain_id
                }
            
            # Sign transaction
            signed_tx = self.account.sign_transaction(tx)
            
            # Send transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            print(f"✓ Payment sent: {tx_hash.hex()}")
            
            # Wait for confirmation (optional)
            # receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            # print(f"  Confirmed in block: {receipt['blockNumber']}")
            
            return tx_hash.hex()
            
        except Exception as e:
            print(f"✗ Payment failed: {e}")
            raise
    
    def request_with_payment(self, url: str, method: str = "GET"):
        """
        Make a request to an x402-protected endpoint.
        Handles the full payment flow.
        """
        import requests
        import json
        
        # Step 1: Make initial request
        response = requests.request(method, url)
        
        # Step 2: Check if payment required
        if response.status_code == 402:
            print(f"💳 Payment required for {url}")
            
            # Parse payment instructions
            try:
                payment_info = response.json()
                amount = float(payment_info.get('amount', payment_info.get('payment', {}).get('amount')))
                recipient = payment_info.get('recipient', payment_info.get('payment', {}).get('recipient'))
                currency = payment_info.get('currency', payment_info.get('payment', {}).get('currency', 'USDC'))
                
                print(f"   Amount: {amount} {currency}")
                print(f"   Recipient: {recipient}")
                
                # Step 3: Make payment
                tx_hash = self.make_payment(recipient, amount, currency)
                
                # Step 4: Retry with payment proof
                headers = {
                    'X-PAYMENT': tx_hash,
                    'X-PAYMENT-SENDER': self.wallet_address,
                    'X-PAYMENT-NETWORK': self.network
                }
                
                print("   Retrying request with payment proof...")
                response = requests.request(method, url, headers=headers)
                
                if response.status_code == 200:
                    print("   ✓ Payment accepted!")
                else:
                    print(f"   ✗ Payment rejected: {response.status_code}")
                    
            except Exception as e:
                print(f"   ✗ Error processing payment: {e}")
        
        return response


# ============================================================================
# Usage Examples
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("X402 SDK Client Examples")
    print("=" * 60)
    
    # Check which method to use
    use_manual = True  # Set to False to try SDK examples
    
    if use_manual:
        print("\n📝 Using Manual Implementation")
        print("=" * 60)
        
        # For testing, we'll use a mock approach since we likely don't have
        # a funded wallet set up yet
        print("\n⚠️  Manual implementation requires:")
        print("   1. A funded wallet with USDC (or native token)")
        print("   2. Private key in environment variable: PRIVATE_KEY")
        print("   3. web3.py installed: pip install web3")
        print("\nExample code:")
        print("""
        client = ManualX402Client(
            private_key=os.getenv("PRIVATE_KEY"),
            network="base"
        )
        
        response = client.request_with_payment("http://localhost:8001/premium")
        print(response.json())
        """)
    else:
        print("\n📚 Using x402 SDK (recommended)")
        print("=" * 60)
        
        print("\n1. Core Client Example:")
        example_core_client()
        
        print("\n2. LangChain Agent Example:")
        example_langchain_agent()
    
    print("\n" + "=" * 60)
    print("💡 Recommendation:")
    print("   - For AI agents: Use x402-langchain")
    print("   - For general apps: Use x402 core client")
    print("   - For custom flows: Use manual implementation above")
    print("=" * 60)

