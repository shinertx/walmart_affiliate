import sys
import os
from pathlib import Path
import json
from dotenv import load_dotenv

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from walmart_api import WalmartAPIClient

load_dotenv()

def check_product_status(client, item_id, markup_percentage=20):
    print(f"\n🔍 Checking Item ID: {item_id}")
    response = client.get_items_by_ids(ids=[item_id])
    
    if not response['success']:
        print(f"❌ API Error: {response.get('error')}")
        return

    items = response['data'].get('items', [])
    if not items:
        print("❌ Item not found")
        return

    item = items[0]
    name = item.get('name')
    price = item.get('salePrice')
    stock_status = item.get('stock')
    
    # --- CRITICAL: SELLER CHECK ---
    # We need to identify if it's Walmart or 3rd Party
    seller_info = item.get('sellerInfo')
    marketplace = item.get('marketplace') # Boolean: True usually means 3rd party
    
    # Logic: It is "Walmart" if marketplace is False OR sellerInfo contains "Walmart"
    is_walmart_sold = False
    if marketplace is False:
        is_walmart_sold = True
    elif seller_info and "walmart" in seller_info.lower():
        is_walmart_sold = True
        
    print(f"Product: {name}")
    print(f"Current Cost: ${price}")
    print(f"Seller: {seller_info} (Marketplace Flag: {marketplace})")
    print(f"Stock Status: {stock_status}")

    # --- DECISION LOGIC ---
    if not is_walmart_sold:
        print("🔴 STATUS: DO NOT SELL (3rd Party Seller)")
        return

    if stock_status != "Available":
        print("🔴 STATUS: DO NOT SELL (Out of Stock)")
        return

    # --- PRICING LOGIC ---
    markup_amount = price * (markup_percentage / 100)
    final_price = price + markup_amount
    
    print(f"🟢 STATUS: READY TO SELL")
    print(f"   Cost: ${price}")
    print(f"   Markup ({markup_percentage}%): ${markup_amount:.2f}")
    print(f"   Your Price: ${final_price:.2f}")

def main():
    client = WalmartAPIClient()
    
    # 1. The Hanes Socks (Item 656) - Currently 3rd Party
    check_product_status(client, "656")
    
    # 2. A known Walmart item (Item 136427776) - Currently Walmart
    check_product_status(client, "136427776")
    
    # 3. Another potential Walmart item (Item 819052247)
    check_product_status(client, "819052247")
    
    # 4. The 12-pack (Item 25710670) - Walmart but OOS
    check_product_status(client, "25710670")

if __name__ == "__main__":
    main()
