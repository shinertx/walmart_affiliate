import sys
import os
from pathlib import Path
import json

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from walmart_api import WalmartAPIClient

def main():
    client = WalmartAPIClient()
    
    # Item ID from the user's URL
    item_id = "17816601985"
    
    print(f"Checking stock for Item ID: {item_id}")
    response = client.get_items_by_ids(ids=[item_id])
    
    if response['success']:
        items = response['data'].get('items', [])
        if items:
            item = items[0]
            print("\n--- Item Details ---")
            print(f"Name: {item.get('name')}")
            print(f"Price: ${item.get('salePrice')}")
            print(f"Stock Status: {item.get('stock')}")
            print(f"Offer Type: {item.get('offerType')}")
            
            # Seller Info
            seller_info = item.get('sellerInfo')
            seller_name = item.get('seller', {}).get('sellerName')
            is_marketplace = item.get('marketplace')
            
            print(f"Seller: {seller_name} (Marketplace: {is_marketplace})")
            
            # Store/Pickup Info
            pickup_options = item.get('pickupOptions')
            print(f"Pickup Options: {pickup_options}")
            
            print("\n--- Full JSON for Debugging ---")
            print(json.dumps(item, indent=2))
            
            if is_marketplace:
                print("\n⚠️  WARNING: This item is currently being sold by a third-party seller.")
            else:
                print("\n✅ This item is sold directly by Walmart.")
                
        else:
            print("Item not found in API.")
    else:
        print(f"Error: {response.get('error')}")

if __name__ == "__main__":
    main()
