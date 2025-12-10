import os
import requests
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SHOPIFY_STORE_URL = os.getenv('SHOPIFY_STORE_URL')
SHOPIFY_ACCESS_TOKEN = os.getenv('SHOPIFY_ACCESS_TOKEN')
API_VERSION = "2024-01"

if not SHOPIFY_STORE_URL or not SHOPIFY_ACCESS_TOKEN:
    print("❌ Error: Missing Shopify credentials in .env file")
    exit(1)

BASE_URL = f"https://{SHOPIFY_STORE_URL}/admin/api/{API_VERSION}"
HEADERS = {
    "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN,
    "Content-Type": "application/json"
}

def get_locations():
    """Fetch all active locations (warehouses)"""
    url = f"{BASE_URL}/locations.json"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json().get('locations', [])
    else:
        print(f"❌ Error fetching locations: {response.text}")
        return []

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

def enable_inventory_tracking(variant_id):
    """Enable Shopify inventory tracking for a variant"""
    url = f"{BASE_URL}/variants/{variant_id}.json"
    payload = {
        "variant": {
            "id": variant_id,
            "inventory_management": "shopify"
        }
    }
    response = requests.put(url, headers=HEADERS, json=payload)
    if response.status_code == 200:
        return True
    else:
        print(f"   ⚠️ Failed to enable tracking: {response.text}")
        return False

def connect_inventory_to_location(inventory_item_id, location_id):
    """Connect an inventory item to a location"""
    url = f"{BASE_URL}/inventory_levels/connect.json"
    payload = {
        "location_id": location_id,
        "inventory_item_id": inventory_item_id
    }
    response = requests.post(url, headers=HEADERS, json=payload)
    if response.status_code == 201 or response.status_code == 200:
        return True
    else:
        # It might already be connected, which is fine
        if "already connected" in response.text:
            return True
        if "fulfillment service location" in response.text:
            return False
        print(f"   ⚠️ Failed to connect to location: {response.text}")
        return False

def set_inventory(inventory_item_id, location_id, quantity):
    """Set inventory level for a specific item at a specific location"""
    url = f"{BASE_URL}/inventory_levels/set.json"
    payload = {
        "location_id": location_id,
        "inventory_item_id": inventory_item_id,
        "available": quantity
    }
    
    response = requests.post(url, headers=HEADERS, json=payload)
    if response.status_code == 200:
        return True
    else:
        # Ignore the specific error about multiple locations
        if "fulfillment service location" in response.text:
            return False
        print(f"   ⚠️ Failed to set inventory: {response.text}")
        return False

def main():
    print(f"🔌 Connecting to {SHOPIFY_STORE_URL}...")
    
    # 1. Get Locations
    all_locations = get_locations()
    if not all_locations:
        print("No locations found. Exiting.")
        return

    # Filter locations
    allowed_keywords = ["AutoDS", "JENNI", "123 Cedar"]
    locations = []
    for loc in all_locations:
        name = loc['name']
        if any(keyword.lower() in name.lower() for keyword in allowed_keywords):
            locations.append(loc)
            
    print(f"📍 Found {len(all_locations)} total locations.")
    print(f"✅ Targeting {len(locations)} locations: {[loc['name'] for loc in locations]}")
    
    # 2. Get Products
    all_products = get_all_products()
    print(f"📦 Total products found: {len(all_products)}")
    
    # 3. Filter and Update
    updated_count = 0
    skipped_count = 0
    
    print("🚀 Starting Bulk Update (This may take a while)...")
    
    for i, product in enumerate(all_products):
        tags = product.get('tags', '')
        
        # SKIP if it is a Walmart product
        if "Source:Walmart" in tags:
            skipped_count += 1
            continue
            
        print(f"[{i+1}/{len(all_products)}] 🔄 {product['title']}")
        
        for variant in product['variants']:
            variant_id = variant['id']
            inventory_item_id = variant['inventory_item_id']
            current_qty = variant.get('inventory_quantity', 0)

            # SKIP if inventory is already greater than 0
            if current_qty > 0:
                print(f"   ⏭️  Skipping {variant['title']} (Current Qty: {current_qty})")
                continue
            
            # STEP 1: Ensure Inventory Tracking is ON
            if variant.get('inventory_management') != 'shopify':
                enable_inventory_tracking(variant_id)
                time.sleep(0.6) # Rate limit prevention
            
            # STEP 2: Update for EACH location
            for loc in locations:
                # Try to set inventory
                success = set_inventory(inventory_item_id, loc['id'], 50)
                
                if not success:
                    # If failed, try connecting first, then set again
                    print(f"   🔄 Attempting to connect item to {loc['name']}...")
                    if connect_inventory_to_location(inventory_item_id, loc['id']):
                        success = set_inventory(inventory_item_id, loc['id'], 50)
                
                if success:
                    print(f"   ✅ Set 50 at {loc['name']}")
                else:
                    # Check for the specific conflict error
                    print(f"   ⚠️ Could not set at {loc['name']} (likely due to conflict with other locations)")
                
                time.sleep(0.6) # Rate limit prevention
        
        updated_count += 1
        
    print("\n📊 Summary:")
    print(f"   - Total Products Scanned: {len(all_products)}")
    print(f"   - Walmart Products Skipped: {skipped_count}")
    print(f"   - Non-Walmart Products Updated: {updated_count}")

if __name__ == "__main__":
    main()
