import sys
import os
from pathlib import Path
import json
import requests
from dotenv import load_dotenv

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from walmart_api import WalmartAPIClient

load_dotenv()

def main():
    client = WalmartAPIClient()
    
    item_id = "656"
    print(f"🔍 Checking details for Item ID: {item_id}")
    
    # Get full item details
    response = client.get_items_by_ids(ids=[item_id])
    
    if response['success']:
        items = response['data'].get('items', [])
        if items:
            item = items[0]
            print("\n--- Current Listing Details ---")
            print(f"Name: {item.get('name')}")
            print(f"Current Price: ${item.get('salePrice')}")
            print(f"MSRP: ${item.get('msrp')}")
            print(f"Seller: {item.get('sellerInfo') or 'Walmart'}")
            print(f"Stock: {item.get('stock')}")
            
            # Check for other sellers or price info if available in this endpoint
            # (Note: The standard affiliate API often just gives the Buy Box winner)
            
            print("\n--- Price Analysis ---")
            current_price = item.get('salePrice')
            target_price = 13.66
            
            if current_price:
                diff = current_price - target_price
                if diff > 0:
                    print(f"⚠️  The price is currently ${diff:.2f} HIGHER than the order price of ${target_price}.")
                    print("Possible reasons:")
                    print("1. The price has increased on Walmart since the order was placed.")
                    print("2. A cheaper third-party seller went out of stock, leaving a more expensive one.")
                    print("3. The order price included a discount or coupon not visible here.")
                elif diff < 0:
                    print(f"ℹ️  The price is currently ${abs(diff):.2f} LOWER than the order price.")
                else:
                    print("✅ The price matches exactly.")
            
        else:
            print("❌ Item not found.")
    else:
        print(f"❌ Error fetching details: {response.get('error')}")

if __name__ == "__main__":
    main()
