import sys
import os
from pathlib import Path
import json
from dotenv import load_dotenv

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from walmart_api import WalmartAPIClient

load_dotenv()

def main():
    client = WalmartAPIClient()
    
    query = "Hanes Over the Calf"
    print(f"🔍 Searching for: '{query}'...")
    
    # Try numItems instead of count for Search API
    response = client.search(query, numItems=25)
    
    if response['success']:
        items = response['data'].get('items', [])
        print(f"Found {len(items)} items in search.")
        
        walmart_candidate_ids = []
        
        for item in items:
            seller_name = item.get('sellerInfo') or "Walmart"
            if not seller_name or "walmart" in seller_name.lower():
                walmart_candidate_ids.append(str(item.get('itemId')))
        
        print(f"Found {len(walmart_candidate_ids)} potential Walmart items. Verifying stock...")
        
        if walmart_candidate_ids:
            details_response = client.get_items_by_ids(ids=walmart_candidate_ids)
            if details_response['success']:
                detailed_items = details_response['data'].get('items', [])
                
                available_walmart_items = []
                for item in detailed_items:
                    stock = item.get('stock')
                    available_online = item.get('availableOnline')
                    name = item.get('name')
                    price = item.get('salePrice')
                    item_id = item.get('itemId')
                    product_url = item.get('productUrl')
                    
                    print(f"ID: {item_id} | Stock: {stock} | Online: {available_online} | {name}")
                    
                    if available_online:
                        available_walmart_items.append(item)
                
                print("\n" + "="*50)
                print(f"Found {len(available_walmart_items)} items sold by Walmart AND In Stock Online:")
                for item in available_walmart_items:
                    print(f"- ID: {item.get('itemId')} | ${item.get('salePrice')} | {item.get('name')}")
                    print(f"  Link: {item.get('productUrl')}")
            else:
                print(f"❌ Failed to fetch details: {details_response.get('error')}")
        else:
            print("No Walmart items found in search results.")
            
    else:
        print(f"❌ Search failed: {response.get('error')}")

if __name__ == "__main__":
    main()
