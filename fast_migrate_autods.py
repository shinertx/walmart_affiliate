import os
import requests
import time
import concurrent.futures
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SHOPIFY_STORE_URL = os.getenv('SHOPIFY_STORE_URL')
SHOPIFY_ACCESS_TOKEN = os.getenv('SHOPIFY_ACCESS_TOKEN')
API_VERSION = "2024-01"
AUTODS_HANDLE = "autods-prod-wwbybglb"
AUTODS_LOCATION_ID = 80020111495

if not SHOPIFY_STORE_URL or not SHOPIFY_ACCESS_TOKEN:
    print("❌ Error: Missing Shopify credentials in .env file")
    exit(1)

BASE_URL = f"https://{SHOPIFY_STORE_URL}/admin/api/{API_VERSION}"
HEADERS = {
    "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN,
    "Content-Type": "application/json"
}

def get_all_products():
    """Fetch all products using pagination"""
    products = []
    url = f"{BASE_URL}/products.json?limit=250&fields=id,title,variants"
    
    print("📥 Fetching all products...")
    while url:
        response = requests.get(url, headers=HEADERS)
        if response.status_code != 200:
            print(f"❌ Error fetching products: {response.text}")
            break
            
        data = response.json()
        products.extend(data.get('products', []))
        
        # Handle pagination
        link = response.headers.get('Link')
        url = None
        if link:
            links = link.split(',')
            for l in links:
                if 'rel="next"' in l:
                    url = l.split(';')[0].strip('<> ')
    
    return products

def process_variant(variant):
    variant_id = variant['id']
    inventory_item_id = variant['inventory_item_id']
    
    # 1. Update Fulfillment Service
    url = f"{BASE_URL}/variants/{variant_id}.json"
    payload = {
        "variant": {
            "id": variant_id,
            "fulfillment_service": AUTODS_HANDLE,
            "inventory_management": "shopify"
        }
    }
    
    try:
        response = requests.put(url, headers=HEADERS, json=payload, timeout=10)
        if response.status_code != 200:
            return f"❌ Variant {variant_id} update failed: {response.status_code}"
    except Exception as e:
        return f"❌ Variant {variant_id} error: {str(e)}"

    # 2. Set Inventory
    url = f"{BASE_URL}/inventory_levels/set.json"
    payload = {
        "location_id": AUTODS_LOCATION_ID,
        "inventory_item_id": inventory_item_id,
        "available": 50
    }
    
    try:
        response = requests.post(url, headers=HEADERS, json=payload, timeout=10)
        if response.status_code != 200:
            return f"❌ Inventory {inventory_item_id} failed: {response.status_code}"
    except Exception as e:
        return f"❌ Inventory {inventory_item_id} error: {str(e)}"
        
    return None # Success

def main():
    print(f"🔌 Connecting to {SHOPIFY_STORE_URL}...")
    all_products = get_all_products()
    print(f"📦 Total products found: {len(all_products)}")
    
    all_variants = []
    for p in all_products:
        all_variants.extend(p['variants'])
        
    print(f"🚀 Starting Fast Migration for {len(all_variants)} variants...")
    print("   Using 10 concurrent threads...")
    
    count = 0
    errors = 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(process_variant, v): v for v in all_variants}
        
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            count += 1
            if result:
                print(result)
                errors += 1
            
            if count % 100 == 0:
                print(f"   Processed {count}/{len(all_variants)} (Errors: {errors})")

    print("\n✅ Migration Complete!")

if __name__ == "__main__":
    main()
