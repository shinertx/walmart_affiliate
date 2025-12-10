import os
import sys
import json
from src.walmart_api import WalmartAPIClient

def check_grocery():
    client = WalmartAPIClient()
    
    print("🔍 Searching for 'Great Value' (Walmart Grocery) items...")
    
    # Search for "Great Value" brand items
    # We expect these to be sold by Walmart and potentially pickup eligible
    result = client.get_products(count=20, brand='Great Value', postalCode='72712')
    
    if result['success']:
        items = result['data']['items']
        print(f"✅ Found {len(items)} Great Value items.")
        
        pickup_count = 0
        for item in items:
            pickup = item.get('pickupTodayEligible', False)
            if pickup:
                pickup_count += 1
                print(f"  🎉 [PICKUP] {item.get('name')}")
            else:
                # Print one failure to see why
                if pickup_count == 0 and items.index(item) == 0:
                    print(f"  ❌ [NO PICKUP] {item.get('name')}")
                    print(f"     Seller: {item.get('sellerInfo', {}).get('sellerName')}")
                    print(f"     Offer Type: {item.get('offerType')}")
        
        print(f"\nSummary: {pickup_count}/{len(items)} Great Value items are eligible for Pickup.")
    else:
        print(f"Error: {result.get('error')}")

if __name__ == "__main__":
    check_grocery()
