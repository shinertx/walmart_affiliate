import os
import requests
from dotenv import load_dotenv

load_dotenv()

SHOPIFY_STORE_URL = os.getenv('SHOPIFY_STORE_URL')
SHOPIFY_ACCESS_TOKEN = os.getenv('SHOPIFY_ACCESS_TOKEN')
API_VERSION = "2024-01"
BASE_URL = f"https://{SHOPIFY_STORE_URL}/admin/api/{API_VERSION}"
HEADERS = {
    "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN,
    "Content-Type": "application/json"
}

import time

def main():
    print("🔍 Auditing Inventory Levels...")
    
    url = f"{BASE_URL}/products.json?limit=250&fields=id,title,variants"
    total_variants = 0
    correct_inventory = 0
    low_inventory = 0
    
    page = 1
    while url:
        print(f"   Scanning page {page}...", end='\r', flush=True)
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
        except requests.exceptions.RequestException as e:
            print(f"\n❌ Network Error: {e}")
            time.sleep(5)
            continue

        if response.status_code == 429:
            print("\n   ⚠️ Rate limit hit, sleeping 2s...")
            time.sleep(2)
            continue
            
        if response.status_code != 200:
            print(f"❌ Error: {response.text}")
            break
            
        data = response.json()
        products = data.get('products', [])
        
        if not products:
            break
            
        for product in products:
            for variant in product['variants']:
                total_variants += 1
                qty = variant.get('inventory_quantity', 0)
                tracking = variant.get('inventory_management')
                
                # Check if stock is >= 50 AND tracking is enabled (shopify)
                if qty >= 50 and tracking == 'shopify':
                    correct_inventory += 1
                else:
                    low_inventory += 1
                    # Print first 3 failures to give user an idea
                    if low_inventory <= 3:
                        reason = []
                        if qty < 50: reason.append(f"Qty: {qty}")
                        if tracking != 'shopify': reason.append(f"Tracking: {tracking}")
                        print(f"\n   ⚠️ Issue ({', '.join(reason)}): {product['title']}")
        
        # Pagination
        link = response.headers.get('Link')
        url = None
        if link:
            links = link.split(',')
            for l in links:
                if 'rel="next"' in l:
                    url = l.split(';')[0].strip('<> ')
            page += 1
            time.sleep(0.5) # Be nice to API
    
    print("\n\n📊 Audit Results:")
    print(f"   Total Variants Scanned: {total_variants}")
    print(f"   ✅ Variants with 50+ Stock: {correct_inventory}")
    print(f"   ❌ Variants with < 50 Stock: {low_inventory}")
    
    if total_variants > 0:
        print(f"   Success Rate: {(correct_inventory/total_variants)*100:.1f}%")

if __name__ == "__main__":
    main()
