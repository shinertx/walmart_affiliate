import requests
import json
import time
import os
from src.walmart_api import WalmartAPIClient

# ------------------------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------------------------
# Load from .env file
from dotenv import load_dotenv
load_dotenv()

SHOPIFY_STORE_URL = os.getenv('SHOPIFY_STORE_URL') # e.g. "your-store.myshopify.com"
SHOPIFY_ACCESS_TOKEN = os.getenv('SHOPIFY_ACCESS_TOKEN') # e.g. "shpat_xxxxxxxx..."
SHOPIFY_API_VERSION = "2024-01"

class ShopifySyncBot:
    def __init__(self):
        if not SHOPIFY_STORE_URL or not SHOPIFY_ACCESS_TOKEN:
            raise ValueError("❌ Missing Shopify credentials in .env file!")
            
        self.walmart = WalmartAPIClient()
        self.base_url = f"https://{SHOPIFY_STORE_URL}/admin/api/{SHOPIFY_API_VERSION}"
        self.headers = {
            "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN,
            "Content-Type": "application/json"
        }

    def get_all_shopify_products(self):
        """Fetch all products from Shopify that are tagged 'Source:Walmart'"""
        print("📥 Fetching products from Shopify...")
        products = []
        url = f"{self.base_url}/products.json?limit=250&fields=id,title,variants,tags"
        
        while url:
            response = requests.get(url, headers=self.headers)
            if response.status_code != 200:
                print(f"Error fetching Shopify products: {response.text}")
                break
                
            data = response.json()
            batch = data.get('products', [])
            
            # Filter for Walmart products
            for p in batch:
                if "Source:Walmart" in p.get('tags', ''):
                    products.append(p)
            
            # Pagination
            link = response.headers.get('Link')
            url = None
            if link:
                # Parse the 'next' link from headers
                links = link.split(',')
                for l in links:
                    if 'rel="next"' in l:
                        url = l.split(';')[0].strip('<> ')
        
        print(f"✅ Found {len(products)} Walmart-sourced products in Shopify.")
        return products

    def update_inventory(self):
        """Main loop to sync inventory"""
        products = self.get_all_shopify_products()
        
        print("🔄 Starting Inventory Sync...")
        
        # Extract Walmart IDs from variants (we stored them in SKU)
        for product in products:
            for variant in product['variants']:
                walmart_id = variant['sku'] # We stored Item ID in SKU
                variant_id = variant['id']
                
                # 1. Check Walmart Real-Time Data
                # We use a lightweight call or batch call here
                # For demo, we check one by one (batching is better for production)
                result = self.walmart.get_items_by_ids([walmart_id])
                
                if result['success'] and result['data']['items']:
                    item_data = result['data']['items'][0]
                    
                    # 2. Determine Status
                    is_in_stock = item_data.get('stock') == 'Available'
                    new_price = item_data.get('salePrice')
                    
                    # Apply Markup (e.g. 40%)
                    my_price = round(new_price * 1.40, 2)
                    
                    # 3. Update Shopify
                    self.update_shopify_variant(variant_id, my_price, is_in_stock)
                    
                    print(f"   Updated {product['title'][:30]}... -> ${my_price} | Stock: {is_in_stock}")
                else:
                    print(f"   ⚠️ Could not find Walmart ID {walmart_id}")
                    
                # Rate limit protection
                time.sleep(0.5)

    def update_shopify_variant(self, variant_id, price, is_in_stock):
        """Push updates to Shopify"""
        url = f"{self.base_url}/variants/{variant_id}.json"
        
        # If in stock, set qty to 10, else 0
        qty = 10 if is_in_stock else 0
        
        payload = {
            "variant": {
                "id": variant_id,
                "price": str(price),
                "inventory_quantity": qty,
                # If using inventory tracking, you might need to adjust inventory_item_id instead
                # But for simple dropshipping, this often works or we toggle 'inventory_management'
            }
        }
        
        requests.put(url, headers=self.headers, json=payload)

if __name__ == "__main__":
    try:
        bot = ShopifySyncBot()
        bot.update_inventory()
    except ValueError as e:
        print(e)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
