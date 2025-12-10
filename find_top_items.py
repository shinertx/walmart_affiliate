import os
import sys
import json
from src.walmart_api import WalmartAPIClient

def find_top_items():
    client = WalmartAPIClient()
    
    print("🔍 Searching for top-rated Same Day eligible items...")
    
    # We'll fetch a larger batch to find the "gems"
    # We can try to filter by category if needed, but let's start broad or use a popular category like Electronics (3944) or Home (4044)
    # Let's try a broad search first.
    
    # Note: The API might not support direct 'sort' by sales, so we'll use reviews as a proxy.
    
    all_items = []
    
    # Fetch a few pages or a large count
    try:
        # We MUST provide a postal code to get "pickupTodayEligible" status
        zip_code = '78210'
        print(f"  • Fetching Household Essentials in ZIP {zip_code}...")
        
        # Category 1115193 is Household Essentials, 976759 is Grocery
        # We'll try to find items that are commonly in store
        result = client.get_products(count=50, category='1115193', postalCode=zip_code) 
        if result['success']:
            all_items.extend(result['data']['items'])
            
        print(f"  • Fetching Personal Care in ZIP {zip_code}...")
        result = client.get_products(count=50, category='1005862', postalCode=zip_code)
        if result['success']:
            all_items.extend(result['data']['items'])
            
    except Exception as e:
        print(f"Error fetching items: {e}")
        return

    print(f"\n📊 Analyzed {len(all_items)} items.")
    
    # Filter for Same Day (Pickup Today)
    same_day_items = [item for item in all_items if item.get('pickupTodayEligible', False) is True]
    
    print(f"✅ Found {len(same_day_items)} items eligible for Same Day Pickup.")
    
    if not same_day_items:
        print("⚠️  No Same Day items found in this batch. Showing top items regardless of shipping method for reference.")
        candidates = all_items
    else:
        candidates = same_day_items

    # Sort by number of reviews (proxy for popularity)
    # Ensure numReviews is an int
    for item in candidates:
        if 'numReviews' not in item:
            item['numReviews'] = 0
        else:
            item['numReviews'] = int(item['numReviews'])
            
    sorted_items = sorted(candidates, key=lambda x: x['numReviews'], reverse=True)
    
    top_10 = sorted_items[:10]
    
    print("\n🏆 TOP 10 ITEMS (By Review Count):")
    print("=" * 60)
    for i, item in enumerate(top_10, 1):
        print(f"{i}. {item.get('name')}")
        print(f"   Price: ${item.get('salePrice')}")
        print(f"   Reviews: {item.get('numReviews')} ({item.get('customerRating')} stars)")
        print(f"   UPC: {item.get('upc')}")
        print(f"   Pickup: {item.get('pickupTodayEligible')}")
        print(f"   Image: {item.get('largeImage')}")
        print("-" * 60)

if __name__ == "__main__":
    find_top_items()
