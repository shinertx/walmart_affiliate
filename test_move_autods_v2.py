import os
import requests
import json
import time
from dotenv import load_dotenv

load_dotenv()

SHOP_URL = f"https://{os.getenv('SHOPIFY_STORE_URL')}"
ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")
AUTODS_HANDLE = "autods-prod-wwbybglb"
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

def update_variant_fulfillment_service(variant_id):
    url = f"{SHOP_URL}/admin/api/2024-01/variants/{variant_id}.json"
    payload = {
        "variant": {
            "id": variant_id,
            "fulfillment_service": AUTODS_HANDLE,
            "inventory_management": "shopify" # Try keeping this as shopify first, or maybe it needs to be the handle too?
            # Usually if fulfillment_service is set, inventory_management might need to be the same if the service manages inventory.
            # But the service definition said inventory_management: false.
            # Let's try just setting fulfillment_service.
        }
    }
    response = requests.put(url, headers=headers, json=payload)
    if response.status_code == 200:
        print(f"   ✅ Updated variant {variant_id} fulfillment_service to {AUTODS_HANDLE}")
        return response.json().get("variant")
    else:
        print(f"   ❌ Failed to update variant {variant_id}: {response.text}")
        return None

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
        
        # 1. Update Fulfillment Service
        updated_variant = update_variant_fulfillment_service(variant['id'])
        
        if updated_variant:
            # 2. Set Inventory
            # We need to wait a moment?
            time.sleep(1)
            set_inventory(updated_variant['inventory_item_id'], AUTODS_LOCATION_ID, 50)

# Test on "Honeydew Intimates 2pc Good Times Pajama Set"
process_product(8143639838855)
