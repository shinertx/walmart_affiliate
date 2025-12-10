import os
import sys
import json
from src.walmart_api import WalmartAPIClient

def verify_pickup():
    client = WalmartAPIClient()
    
    # UPCs from the previous "Top 10" list (Wipes, Toothpaste, Batteries)
    upcs = [
        '681131105231', # Equate Wipes
        '310158084044', # Sensodyne
        '041333017990', # Duracell AA
        '017000024042', # Dial Soap
        '039800011329'  # Energizer AA
    ]
    
    zip_code = '72712' # Bentonville, AR (HQ)
    
    print(f"🔍 Verifying Pickup Eligibility for {len(upcs)} items in ZIP {zip_code}...")
    print("Using 'get_items_by_upc' endpoint instead of 'get_products'...")
    
    result = client.get_items_by_upc(upcs, postal_code=zip_code)
    
    if result['success']:
        items = result['data']['items']
        print(f"✅ Successfully retrieved {len(items)} items.")
        
        # DEBUG: Print ALL keys for the first item to find the hidden field
        if items:
            print("\n🕵️‍♀️ INSPECTING ALL FIELDS FOR FIRST ITEM:")
            first = items[0]
            for k, v in first.items():
                print(f"  {k}: {v}")
            print("-" * 40)
        
        eligible_count = 0
        for item in items:
            name = item.get('name')
            pickup = item.get('pickupTodayEligible')
            
            print(f"\nItem: {name}")
            print(f"  UPC: {item.get('upc')}")
            print(f"  Pickup Eligible: {pickup}")
            
            if pickup:
                eligible_count += 1
                print("  🎉 THIS ITEM IS SAME DAY ELIGIBLE!")
            else:
                print("  ❌ Not eligible for pickup in this ZIP.")
                
        print(f"\nSummary: {eligible_count}/{len(items)} items are eligible for Same Day Pickup.")
    else:
        print(f"Error: {result.get('error')}")

if __name__ == "__main__":
    verify_pickup()
