import os
import requests
import json
import time
from dotenv import load_dotenv

load_dotenv()

SHOP_URL = f"https://{os.getenv('SHOPIFY_STORE_URL')}"
ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")
AUTODS_LOCATION_ID = 80020111495

headers = {
    "X-Shopify-Access-Token": ACCESS_TOKEN,
    "Content-Type": "application/json"
}

def get_product(product_id):
    url = f"{SHOP_URL}/admin/api/2024-01/products/{product_id}.json"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get("product")
    return None

def get_inventory_levels(inventory_item_id):
    url = f"{SHOP_URL}/admin/api/2024-01/inventory_levels.json?inventory_item_ids={inventory_item_id}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get("inventory_levels", [])
    return []

def disconnect_location(inventory_item_id, location_id):
    # First set to 0 just in case
    set_url = f"{SHOP_URL}/admin/api/2024-01/inventory_levels/set.json"
    payload = {
        "location_id": location_id,
        "inventory_item_id": inventory_item_id,
        "available": 0
    }
    requests.post(set_url, headers=headers, json=payload)
    
    # To disconnect, we delete the inventory level
    url = f"{SHOP_URL}/admin/api/2024-01/inventory_levels.json?inventory_item_id={inventory_item_id}&location_id={location_id}"
    response = requests.delete(url, headers=headers)
    if response.status_code == 204:
        print(f"   ✅ Disconnected from location {location_id}")
        return True
    else:
        print(f"   ❌ Failed to disconnect location {location_id}: Status {response.status_code} - {response.text}")
        return False

def connect_location(inventory_item_id, location_id):
    url = f"{SHOP_URL}/admin/api/2024-01/inventory_levels/connect.json"
    payload = {
        "location_id": location_id,
        "inventory_item_id": inventory_item_id
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code in [200, 201]:
        print(f"   ✅ Connected to AutoDS ({location_id})")
        return True
    elif "already connected" in response.text:
        print(f"   ✅ Already connected to AutoDS")
        return True
    else:
        print(f"   ❌ Failed to connect to AutoDS: {response.text}")
        return False

def set_inventory(inventory_item_id, location_id, qty):
    url = f"{SHOP_URL}/admin/api/2024-01/inventory_levels/set.json"
    payload = {
        "location_id": location_id,
        "inventory_item_id": inventory_item_id,
        "available": qty
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        print(f"   ✅ Set inventory to {qty} at AutoDS")
        return True
    else:
        print(f"   ❌ Failed to set inventory: {response.text}")
        return False

def process_product(product_id):
    product = get_product(product_id)
    if not product:
        print("Product not found")
        return

    print(f"Processing: {product['title']}")
    
    for variant in product['variants']:
        print(f"\n Variant: {variant['title']}")
        inv_item_id = variant['inventory_item_id']
        
        # 1. Get current levels
        levels = get_inventory_levels(inv_item_id)
        
        # 2. Disconnect from non-AutoDS locations
        for level in levels:
            loc_id = level['location_id']
            if loc_id != AUTODS_LOCATION_ID:
                print(f"   Running disconnect for location {loc_id}...")
                disconnect_location(inv_item_id, loc_id)
                time.sleep(0.5) # Rate limit safety
        
        # 3. Connect to AutoDS
        connect_location(inv_item_id, AUTODS_LOCATION_ID)
        time.sleep(0.5)
        
        # 4. Set Inventory
        set_inventory(inv_item_id, AUTODS_LOCATION_ID, 50)
        time.sleep(0.5)

# Test on "Honeydew Intimates 2pc Good Times Pajama Set"
process_product(8143639838855)
