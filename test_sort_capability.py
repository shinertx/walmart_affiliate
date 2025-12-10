import os
import json
import ssl
import certifi
from src.walmart_api import WalmartAPIClient

# Fix SSL issues on macOS
ssl_context = ssl.create_default_context(cafile=certifi.where())
ssl._create_default_https_context = ssl._create_unverified_context

def test_sort():
    client = WalmartAPIClient()
    
    print("🔍 Testing 'sort=best_seller' parameter...")
    
    # Try searching for "toys" with sort="best_seller"
    # Common sort values in APIs: best_seller, price_low, price_high, new, relevance, rating
    
    sort_options = ['best_seller', 'customer_rating', 'relevance']
    
    for sort_opt in sort_options:
        print(f"\n--- Testing sort='{sort_opt}' ---")
        result = client.search(query="toys", sort=sort_opt)
        
        if result['success']:
            items = result['data'].get('items', [])
            print(f"✅ Success! Got {len(items)} items.")
            if items:
                print("Top 3 items:")
                for i, item in enumerate(items[:3]):
                    print(f"  {i+1}. {item.get('name')} (Rank: {item.get('bestSellerRank') if 'bestSellerRank' in item else 'N/A'})")
        else:
            print(f"❌ Failed: {result.get('error')}")

if __name__ == "__main__":
    test_sort()
