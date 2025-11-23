#!/usr/bin/env python3
"""
Test script to demonstrate improved location accuracy in Uber API
"""

import asyncio
import sys
import os

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from uber.uber_api import generate_uber_url

async def test_locations():
    """Test various location scenarios to demonstrate accuracy improvements"""
    
    test_cases = [
        {
            "name": "Clear addresses (no ambiguity)",
            "from": "1600 Amphitheatre Parkway, Mountain View, CA",
            "to": "1 Apple Park Way, Cupertino, CA"
        },
        {
            "name": "Ambiguous city names",
            "from": "Paris, France",
            "to": "London, UK"
        },
        {
            "name": "Landmarks without full addresses",
            "from": "Eiffel Tower",
            "to": "Louvre Museum"
        },
        {
            "name": "Abbreviated addresses",
            "from": "Times Square, NYC",
            "to": "Central Park, Manhattan"
        },
        {
            "name": "International addresses",
            "from": "Tokyo Tower, Japan",
            "to": "Senso-ji Temple, Tokyo"
        }
    ]
    
    print("=" * 80)
    print("UBER LOCATION ACCURACY TEST")
    print("=" * 80)
    print()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'=' * 80}")
        print(f"TEST {i}: {test_case['name']}")
        print(f"{'=' * 80}")
        print(f"From: {test_case['from']}")
        print(f"To:   {test_case['to']}")
        print()
        
        try:
            url = await generate_uber_url(test_case['from'], test_case['to'])
            print(f"\n✅ Success! Generated URL:")
            print(f"{url}")
            print()
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        # Wait a bit between tests to avoid rate limiting
        if i < len(test_cases):
            print("\nWaiting 2 seconds before next test...")
            await asyncio.sleep(2)
    
    print("\n" + "=" * 80)
    print("TESTING COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_locations())

