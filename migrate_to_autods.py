import os
import requests
import time
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
    url = f"{BASE_URL}/products.json?limit=250&fields=id,title,tags,variants"
    
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

def update_variant_fulfillment_service(variant_id):
    url = f"{BASE_URL}/variants/{variant_id}.json"
    payload = {
        "variant": {
            "id": variant_id,
            "fulfillment_service": AUTODS_HANDLE,
            "inventory_management": "shopify"
        }
    }
    for attempt in range(3):
        try:
            response = requests.put(url, headers=HEADERS, json=payload, timeout=10)
            if response.status_code == 200:
                data = response.json()
                # Verify the update actually happened
                current_service = data.get('variant', {}).get('fulfillment_service')
                if current_service == AUTODS_HANDLE:
                    return True
                else:
                    print(f"   ⚠️ API returned 200, but fulfillment_service is still '{current_service}'")
                    return False
            else:
                print(f"   ❌ Failed to update variant {variant_id}: {response.text}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"   ⚠️ Network error ({e}), retrying in 5 seconds... (Attempt {attempt+1}/3)")
            time.sleep(5)
    return False

def set_inventory(inventory_item_id, location_id, quantity):
    """Set inventory level for a specific item at a specific location"""
    url = f"{BASE_URL}/inventory_levels/set.json"
    payload = {
        "location_id": location_id,
        "inventory_item_id": inventory_item_id,
        "available": quantity
    }
    
    for attempt in range(3):
        try:
            response = requests.post(url, headers=HEADERS, json=payload, timeout=10)
            if response.status_code == 200:
                data = response.json()
                # Verify inventory level
                current_qty = data.get('inventory_level', {}).get('available')
                if current_qty == quantity:
                    return True
                else:
                    print(f"   ⚠️ API returned 200, but inventory is {current_qty} (expected {quantity})")
                    return False
            else:
                print(f"   ⚠️ Failed to set inventory: {response.text}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"   ⚠️ Network error ({e}) during inventory set, retrying... (Attempt {attempt+1}/3)")
            time.sleep(5)
    return False

def main():
    print(f"🔌 Connecting to {SHOPIFY_STORE_URL}...")
    
    # 1. Get Products
    all_products = get_all_products()
    print(f"📦 Total products found: {len(all_products)}")
    
    updated_count = 0
    skipped_count = 0
    
    print("🚀 Starting Migration to AutoDS (This may take a while)...")
    
    for i, product in enumerate(all_products):
        tags = product.get('tags', '')
        
        # Process ALL products, including Walmart ones
        # if "Source:Walmart" in tags:
        #     skipped_count += 1
        #     continue
            
        print(f"[{i+1}/{len(all_products)}] 🔄 {product['title']}")
        
        for variant in product['variants']:
            variant_id = variant['id']
            inventory_item_id = variant['inventory_item_id']
            current_qty = variant.get('inventory_quantity', 0)
            
            # Check if already set to AutoDS
            if variant.get('fulfillment_service') == AUTODS_HANDLE:
                if current_qty > 10:
                    print(f"   ✅ Already AutoDS - Stock {current_qty} (>10), skipping update")
                    time.sleep(0.1)
                    continue
                
                # Just ensure stock is 50
                set_inventory(inventory_item_id, AUTODS_LOCATION_ID, 50)
                print(f"   ✅ Already AutoDS - Stock set to 50")
                time.sleep(0.6)
                continue

            # Update Fulfillment Service
            if update_variant_fulfillment_service(variant_id):
                print(f"   ✅ Moved to AutoDS")
                time.sleep(0.6) # Wait for Shopify to process the move
                
                # Set Inventory
                if set_inventory(inventory_item_id, AUTODS_LOCATION_ID, 50):
                    print(f"   ✅ Stock set to 50")
                else:
                    print(f"   ⚠️ Failed to set stock")
            
            time.sleep(0.6) # Rate limit prevention
        
        updated_count += 1
        
    print("\n📊 Summary:")
    print(f"   - Total Products Scanned: {len(all_products)}")
    print(f"   - Walmart Products Skipped: {skipped_count}")
    print(f"   - Non-Walmart Products Migrated: {updated_count}")

if __name__ == "__main__":
    main()
