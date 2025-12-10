import os
import sys
import json
from src.walmart_api import WalmartAPIClient

def check_item():
    client = WalmartAPIClient()
    
    print("Fetching general products to find Same Day eligible items...")
    # Fetch a batch of products
    result = client.get_products(count=50)
    
    if result['success']:
        items = result['data']['items']
        print(f"Found {len(items)} items.")
        
        same_day_count = 0
        pickup_count = 0
        
        # Print all keys of the first item to inspect available fields
        if items:
            print("\n--- Keys available in API response ---")
            first_item = items[0]
            for k, v in first_item.items():
                print(f"{k}: {v}")
            print("----------------------------------------\n")

        for item in items:
            is_pickup = item.get('pickupTodayEligible', False)
            is_same_day = False # Check for other flags
            
            # Check all keys for "same day" or "delivery"
            delivery_keys = [k for k in item.keys() if 'day' in k.lower() or 'delivery' in k.lower()]
            
            if is_pickup:
                pickup_count += 1
                print(f"\n[PICKUP ELIGIBLE] {item.get('name')}")
                print(f"  UPC: {item.get('upc')}")
                print(f"  Pickup Today: {is_pickup}")
                for k in delivery_keys:
                    print(f"  {k}: {item.get(k)}")
            
        print(f"\nSummary: {pickup_count} items eligible for Pickup Today out of {len(items)}.")
            
    else:
        print(f"Error: {result.get('error')}")

if __name__ == "__main__":
    check_item()
