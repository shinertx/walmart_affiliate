#!/usr/bin/env python3
"""
Quick test example for Walmart API
This demonstrates basic usage without running full batch tests
"""

import sys
from pathlib import Path
import os
from dotenv import load_dotenv

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from walmart_api import WalmartAPIClient

def main():
    print("🧪 Quick Walmart API Test")
    print("=" * 30)
    
    load_dotenv()
    
    # Check for Consumer ID
    if not os.getenv('WALMART_CONSUMER_ID'):
        print("❌ WALMART_CONSUMER_ID not found in .env file")
        print("Please add your Consumer ID to the .env file")
        return 1
    
    try:
        # Create API client
        client = WalmartAPIClient()
        
        print("🔍 Testing API connection with 5 items...")
        
        # Test with a small batch
        result = client.get_products(count=5)
        
        if result['success']:
            data = result['data']
            metadata = result['metadata']
            
            print("✅ API test successful!")
            print(f"📊 Retrieved: {len(data.get('items', []))} items")
            print(f"⏱️  Response time: {metadata['response_time_seconds']:.2f}s")
            print(f"💾 Response size: {metadata['response_size_bytes']} bytes")
            print(f"📄 Total pages available: {data.get('totalPages', 'Unknown')}")
            
            # Show first product as example
            items = data.get('items', [])
            if items:
                first_item = items[0]
                print(f"\n🛍️ Example product:")
                print(f"   Name: {first_item.get('name', 'Unknown')[:60]}...")
                print(f"   Price: ${first_item.get('salePrice', 'N/A')}")
                print(f"   Brand: {first_item.get('brandName', 'N/A')}")
            
            print(f"\n🎯 Ready to run full batch testing!")
            
        else:
            print("❌ API test failed:")
            print(f"   Error: {result['error']}")
            return 1
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())