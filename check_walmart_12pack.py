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
    
    item_id = "25710670"
    print(f"Checking details for Walmart-sold Item ID: {item_id}")
    
    response = client.get_items_by_ids(ids=[item_id])
    
    if response['success']:
        items = response['data'].get('items', [])
        if items:
            item = items[0]
            print(f"Name: {item.get('name')}")
            print(f"Price: ${item.get('salePrice')}")
            print(f"Seller: {item.get('sellerInfo') or 'Walmart'}")
            print(f"Stock: {item.get('stock')}")
            print(f"Availability Online: {item.get('availableOnline')}")
            print(f"Offer Type: {item.get('offerType')}")
            print(f"URL: {item.get('productUrl')}")
            # print(json.dumps(item, indent=2)) # Uncomment for full debug if needed
        else:
            print("Item not found.")

if __name__ == "__main__":
    main()
