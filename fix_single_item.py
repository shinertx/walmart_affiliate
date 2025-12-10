import os
import requests
import json
import time
from dotenv import load_dotenv

load_dotenv()

SHOPIFY_STORE_URL = os.getenv('SHOPIFY_STORE_URL')
SHOPIFY_ACCESS_TOKEN = os.getenv('SHOPIFY_ACCESS_TOKEN')
VARIANT_ID = 42842827718791 # Sculpting Lace Bodysuit In Black
INVENTORY_ITEM_ID = 44944470081671
AUTODS_LOCATION_ID = 80020111495

HEADERS = {
    "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN,
    "Content-Type": "application/json"
}

def update_variant_tracking():
    url = f"https://{SHOPIFY_STORE_URL}/admin/api/2024-01/variants/{VARIANT_ID}.json"
    payload = {
        "variant": {
            "id": VARIANT_ID,
            "inventory_management": "shopify"
        }
    }
    print(f"Updating variant {VARIANT_ID} to track inventory...")
    response = requests.put(url, headers=HEADERS, json=payload)
    if response.status_code == 200:
        print("✅ Variant updated successfully.")
        return True
    else:
        print(f"❌ Failed to update variant: {response.text}")
        return False

def set_inventory():
    url = f"https://{SHOPIFY_STORE_URL}/admin/api/2024-01/inventory_levels/set.json"
    payload = {
        "location_id": AUTODS_LOCATION_ID,
        "inventory_item_id": INVENTORY_ITEM_ID,
        "available": 50
    }
    print(f"Setting inventory to 50 at AutoDS location...")
    response = requests.post(url, headers=HEADERS, json=payload)
    if response.status_code == 200:
        print("✅ Inventory set successfully.")
        print(response.json())
    else:
        print(f"❌ Failed to set inventory: {response.text}")

if __name__ == "__main__":
    if update_variant_tracking():
        time.sleep(1) # Wait a bit for propagation
        set_inventory()
