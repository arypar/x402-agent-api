import 'dotenv/config';
import { privateKeyToAccount } from 'viem/accounts';
import { wrapFetchWithPayment, decodeXPaymentResponse } from 'x402-fetch';

/**
 * End-to-End Test for x402 Payment with Shopify Task Payload
 * 
 * Usage: 
 * 1. Ensure WALLET_PRIVATE_KEY is in your .env file
 * 2. Run: node example/test_shopify_x402.js
 */

async function testShopifyTask() {
    console.log('🧪 Starting x402 Shopify Task Test...');
    
    // 1. Get Private Key
     const privateKey = "61f448e5aa4121c40c0eb5de61f930c762b412db699317237d40a1e0ac048f15";
    if (!privateKey) {
        console.error('❌ Error: WALLET_PRIVATE_KEY not found in .env file');
        process.exit(1);
    }

    // 2. Setup Account
    // Ensure key format is correct (add 0x if missing)
    const formattedKey = privateKey.startsWith('0x') ? privateKey : `0x${privateKey}`;
    const account = privateKeyToAccount(formattedKey);
    console.log(`🔑 Using wallet: ${account.address}`);

    // 3. Wrap fetch with x402 payment handler
    const fetchWithPayment = wrapFetchWithPayment(fetch, account);

    // 4. Define Request Details
    const endpoint = 'https://undecorously-uncongestive-cindy.ngrok-free.dev/tasks/create';
    
    const payload = {
        task_type: "shopify_order",
        input_data: {
            product_url: "https://mimik-ai-3.myshopify.com/products/the-collection-snowboard-liquid",
            size: "ANY"
        }
    };

    console.log(`🚀 Sending request to: ${endpoint}`);
    console.log('📦 Payload:', JSON.stringify(payload, null, 2));

    try {
        // 5. Execute Request
        const res = await fetchWithPayment(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });

        // 6. Handle Response
        if (!res.ok) {
            throw new Error(`Request failed with status ${res.status}: ${res.statusText}`);
        }

        const body = await res.json();
        console.log('\n✅ API Response:', JSON.stringify(body, null, 2));

        // 7. Check Payment Details (Optional)
        const paymentRespHeader = res.headers.get('x-payment-response');
        if (paymentRespHeader) {
            const paymentDetails = decodeXPaymentResponse(paymentRespHeader);
            console.log('\n💰 Payment Details:', paymentDetails);
        } else {
            console.log('\nℹ️ No x-payment-response header found (maybe request was free or already paid?)');
        }

    } catch (error) {
        console.error('\n❌ Error:', error);
        if (error.response) {
            console.error('Status:', error.response.status);
            console.error('Data:', await error.response.text());
        }
    }
}

testShopifyTask().catch(console.error);