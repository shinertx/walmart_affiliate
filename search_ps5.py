import sys
import os
from pathlib import Path
import json

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from walmart_api import WalmartAPIClient

def main():
    client = WalmartAPIClient()
    
    # Try searching with 'keyword' parameter which is common for affiliate APIs
    print("Searching for 'PlayStation 5 Disc Console Slim with NBA 2K26'...")
    
    # Note: The paginated/items endpoint might not support keyword search directly.
    # It usually supports category, brand, etc.
    # But let's try passing 'keyword' or 'query' just in case, or fetch a broad category and filter.
    # Actually, the best way might be to use the 'keyword' parameter if supported.
    
    # Let's try to find it.
    # If keyword search isn't supported on this endpoint, we might need to use a different approach
    # or just check if we can find it by browsing.
    
    # Attempt 1: Try 'keyword' param
    # response = client.get_products(count=25, keyword="PlayStation 5 Disc Console Slim with NBA 2K26")
    
    # if response['success']:
    #     items = response['data'].get('items', [])
    #     print(f"Found {len(items)} items.")
    #     for item in items:
    #         print(f"- {item.get('name')} (ID: {item.get('itemId')}) - Stock: {item.get('stockStatus')}")
            
    #         # Check for exact match or close match
    #         if "NBA 2K26" in item.get('name', '') and "PlayStation 5" in item.get('name', ''):
    #             print(f"  MATCH FOUND! Stock: {item.get('stockStatus')}")
    #             # Some APIs return 'stock' or 'availableOnline'
    #             print(json.dumps(item, indent=2))
    # else:
    #     print(f"Search failed: {response.get('error')}")
        
        # Attempt 3: Try the Search Endpoint explicitly
    print("\nTrying Search Endpoint...")
    search_url = "https://developer.api.walmart.com/api-proxy/service/affil/product/v2/search"
    
    # We need to manually construct the request using the client's helper methods for headers
    headers = client._get_headers()
    
    all_search_items = []
    total_pages_to_check = 2 # Check 50 items total
    items_per_page = 25
    
    import requests
    try:
        for page in range(total_pages_to_check):
            print(f"Searching page {page + 1}...")
            params = {
                'query': "PlayStation 5 NBA 2K26", # Broader query
                'numItems': items_per_page,
                'start': page * items_per_page + 1
            }
            
            response = requests.get(search_url, headers=headers, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                items = data.get('items', [])
                if not items:
                    print("No more items found.")
                    break
                all_search_items.extend(items)
            else:
                print(f"Error on page {page+1}: {response.status_code}")
                break

        print(f"Found {len(all_search_items)} total items in search results.")
        
        # Collect IDs to fetch full details
        item_ids = [str(item.get('itemId')) for item in all_search_items if item.get('itemId')]
        
        if item_ids:
            print(f"Fetching details for {len(item_ids)} items to check seller and stock...")
            
            # Batch requests in chunks of 20
            chunk_size = 20
            all_detailed_items = []
            
            for i in range(0, len(item_ids), chunk_size):
                chunk = item_ids[i:i + chunk_size]
                details_response = client.get_items_by_ids(ids=chunk)
                
                if details_response['success']:
                    all_detailed_items.extend(details_response['data'].get('items', []))
                else:
                    print(f"Failed to get details for batch {i}: {details_response.get('error')}")

            walmart_sold_count = 0
            
            print("\n--- Results (Sold by Walmart - Any Stock Status) ---")
            for item in all_detailed_items:
                is_marketplace = item.get('marketplace')
                stock_status = item.get('stock')
                name = item.get('name')
                item_id = item.get('itemId')
                offer_type = item.get('offerType')
                pickup_options = item.get('pickupOptions')
                
                # Check criteria: Not marketplace (Sold by Walmart)
                if is_marketplace is False:
                    print(f"✅ [WALMART DIRECT] {name} (ID: {item_id})")
                    print(f"   Price: ${item.get('salePrice')}")
                    print(f"   Stock: {stock_status}")
                    print(f"   Offer Type: {offer_type}")
                    print(f"   Pickup Options: {pickup_options}")
                    walmart_sold_count += 1
                    
                    # If we find a Walmart item, let's print the full JSON to see store details
                    if "NBA" in name and "PlayStation" in name:
                         print("   --> MATCHES QUERY! Full Details:")
                         print(json.dumps(item, indent=2))

            print(f"\nTotal items found sold by Walmart: {walmart_sold_count}")
            
            if walmart_sold_count == 0:
                print("\nNo items found sold directly by Walmart.")
                print("Checking for any items with 'STORE' in offerType...")
                for item in all_detailed_items:
                     offer_type = item.get('offerType', '')
                     if 'STORE' in str(offer_type):
                          print(f"Found STORE item: {item.get('name')} - {offer_type}")

            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    main()
