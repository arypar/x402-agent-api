#!/usr/bin/env node

/**
 * Coinbase Onramp Link Generator
 * 
 * This script:
 * 1. Generates a JWT bearer token using the Coinbase CDP TypeScript SDK
 * 2. Creates an onramp session via API
 * 3. Generates the onramp URL
 */

const { generateJwt } = require('@coinbase/cdp-sdk/auth');

// ============================================================================
// CONFIGURATION - Add your API credentials here
// ============================================================================
const API_KEY_ID = '620b4c7c-b782-4036-aff4-be0ac592d9a4';
const API_KEY_SECRET = '7pRvC6oKM2RcAV0LldPxjkMVNIEljQTnwH3bn9F5HKnpWCR3CFSKZkjzELDb3dLudl7suVz4BHlgilP58SDD2Q==';
// ============================================================================

// API Configuration
const API_HOST = 'api.cdp.coinbase.com';
const API_PATH = '/platform/v2/onramp/sessions';
const ONRAMP_BASE_URL = 'https://www.coinbase.com/onramp';

// Onramp session parameters
const SESSION_CONFIG = {
  purchaseCurrency: "USDC",
  destinationNetwork: "base",
  destinationAddress: "0x71C7656EC7ab88b098defB751B7401B5f6d8976F",
  paymentAmount: "5.00",
  paymentCurrency: "USD",
  paymentMethod: "CARD",
  country: "US",
  subdivision: "NY",
  redirectUrl: "https://yourapp.com/success",
  clientIp: "181.10.161.120",
  partnerUserRef: "user-1234"
};

async function generateJwtToken() {
  if (!API_KEY_ID || API_KEY_ID === 'YOUR_API_KEY_ID_HERE') {
    throw new Error('API Key ID must be set in onramp.js. Please edit the file and set API_KEY_ID');
  }

  if (!API_KEY_SECRET || API_KEY_SECRET === 'YOUR_API_KEY_SECRET_HERE') {
    throw new Error('API Key Secret must be set in onramp.js. Please edit the file and set API_KEY_SECRET');
  }

  try {
    const jwt = await generateJwt({
      apiKeyId: API_KEY_ID,
      apiKeySecret: API_KEY_SECRET,
      requestMethod: 'POST',
      requestHost: API_HOST,
      requestPath: API_PATH,
      expiresIn: 120,
    });

    console.log('✓ Generated JWT token:', jwt.substring(0, 50) + '...');
    return jwt;
  } catch (error) {
    throw new Error(`Failed to generate JWT: ${error.message}`);
  }
}

async function createOnrampSession(jwt) {
  const url = `https://${API_HOST}${API_PATH}`;
  
  const headers = {
    'Authorization': `Bearer ${jwt}`,
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  };

  console.log('\nMaking POST request to:', url);
  console.log('Payload:', JSON.stringify(SESSION_CONFIG, null, 2));

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: headers,
      body: JSON.stringify(SESSION_CONFIG)
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`HTTP ${response.status}: ${errorText}`);
    }

    const sessionData = await response.json();
    console.log('\n✓ Created onramp session successfully!');
    console.log('Response:', JSON.stringify(sessionData, null, 2));
    
    return sessionData;
  } catch (error) {
    throw new Error(`Failed to create onramp session: ${error.message}`);
  }
}

function generateOnrampUrl(sessionToken) {
  const params = new URLSearchParams({
    sessionToken: sessionToken
  });
  
  return `${ONRAMP_BASE_URL}?${params.toString()}`;
}

async function main() {
  console.log('='.repeat(60));
  console.log('Coinbase Onramp Link Generator');
  console.log('='.repeat(60));
  console.log('\n⚠️  Note: Each onramp link can only be used ONCE!');
  console.log('   Run this script again to generate a fresh link.\n');

  try {
    // Step 1: Generate JWT
    console.log('[1/3] Generating JWT bearer token...');
    const jwt = await generateJwtToken();

    // Step 2: Create onramp session
    console.log('\n[2/3] Creating onramp session...');
    const sessionData = await createOnrampSession(jwt);

    // Extract onramp URL from response
    // The API returns the complete URL in session.onrampUrl
    const onrampUrl = sessionData.session?.onrampUrl;
    if (!onrampUrl) {
      throw new Error('Onramp URL not found in response');
    }

    // Step 3: Display the onramp link
    console.log('\n[3/3] Onramp link ready!');

    console.log('\n✓ Onramp link generated successfully!');
    console.log('\n' + '='.repeat(60));
    console.log('🔗 Fresh Onramp URL (single-use only):');
    console.log(onrampUrl);
    console.log('='.repeat(60) + '\n');

    return onrampUrl;
  } catch (error) {
    console.error('\n✗ Error:', error.message);
    process.exit(1);
  }
}

// Run the script
main();

