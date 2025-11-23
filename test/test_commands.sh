#!/bin/bash
# Test commands for x402-protected API

BASE_URL="http://localhost:8000"

echo "=========================================="
echo "Testing X402 Payment-Protected API"
echo "=========================================="

echo ""
echo "1. Test FREE endpoint (should work):"
echo "------------------------------------"
curl -s $BASE_URL/health | jq .

echo ""
echo ""
echo "2. Test PROTECTED endpoint - Uber Ride (should return 402):"
echo "------------------------------------------------------------"
curl -s -X POST $BASE_URL/tasks/create \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "uber_ride",
    "input_data": {
      "from_address": "123 Main St, San Francisco, CA",
      "to_address": "456 Market St, San Francisco, CA"
    }
  }' | jq .

echo ""
echo ""
echo "3. Test PROTECTED endpoint - Shopify Order (should return 402):"
echo "----------------------------------------------------------------"
curl -s -X POST $BASE_URL/tasks/create \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "shopify_order",
    "input_data": {
      "product_url": "https://kith.com/products/example-item",
      "size": "Medium"
    }
  }' | jq .

echo ""
echo ""
echo "4. Check other FREE endpoints:"
echo "------------------------------"
echo "GET /:"
curl -s $BASE_URL/ | jq .name .version .architecture

echo ""
echo "POST /shopify/search:"
curl -s -X POST $BASE_URL/shopify/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "black tshirt",
    "num_results": 3
  }' | jq .

echo ""
echo ""
echo "=========================================="
echo "Expected Results:"
echo "=========================================="
echo "✓ /health should return 200 OK"
echo "✓ /tasks/create should return 402 Payment Required"
echo "✓ Response should include payment details:"
echo "  - amount: 0.001"
echo "  - network: base"
echo "  - recipient: 0xda2964669a27ae905d4b114c52eb63ba2fab6d7f"
echo "=========================================="

