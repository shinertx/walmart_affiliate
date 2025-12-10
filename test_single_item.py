import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

SHOPIFY_STORE_URL = os.getenv('SHOPIFY_STORE_URL')
SHOPIFY_ACCESS_TOKEN = os.getenv('SHOPIFY_ACCESS_TOKEN')
API_VERSION = "2024-01"
AUTODS_HANDLE = "autods-prod-wwbybglb"
AUTODS_LOCATION_ID = 80020111495

BASE_URL = f"https://{SHOPIFY_STORE_URL}/admin/api/{API_VERSION}"
HEADERS = {
    "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN,
    "Content-Type": "application/json"
}

def find_product(title):
    url = f"{BASE_URL}/products.json?title={title}"
    response = requests.get(url, headers=HEADERS)
    products = response.json().get('products', [])
    for p in products:
        if title.lower() in p['title'].lower():
            return p
    return None

def update_variant(variant_id):
    print(f"Attempting to update variant {variant_id}...")
    url = f"{BASE_URL}/variants/{variant_id}.json"
    payload = {
        "variant": {
            "id": variant_id,
            "fulfillment_service": AUTODS_HANDLE,
            "inventory_management": "shopify" 
        }
    }
    response = requests.put(url, headers=HEADERS, json=payload)
    if response.status_code == 200:
        print("✅ Fulfillment Service Update: Success")
        print(json.dumps(response.json()['variant'], indent=2))
        return True
    else:
        print(f"❌ Fulfillment Service Update Failed: {response.text}")
        return False

def set_inventory(inventory_item_id, location_id, quantity):
    print(f"Attempting to set inventory for item {inventory_item_id} at location {location_id}...")
    url = f"{BASE_URL}/inventory_levels/set.json"
    payload = {
        "location_id": location_id,
        "inventory_item_id": inventory_item_id,
        "available": quantity
    }
    response = requests.post(url, headers=HEADERS, json=payload)
    if response.status_code == 200:
        print("✅ Inventory Set: Success")
        print(json.dumps(response.json(), indent=2))
        return True
    else:
        print(f"❌ Inventory Set Failed: {response.text}")
        return False

def main():
    title = "Open Stitchcrochet Cover Up Tunic In White"
    print(f"Searching for: {title}")
    product = find_product(title)
    
    if not product:
        print("❌ Product not found")
        return

    print(f"Found Product: {product['title']} (ID: {product['id']})")
    
    for variant in product['variants']:
        print(f"\nProcessing Variant: {variant['id']}")
        print(f"Current Fulfillment Service: {variant['fulfillment_service']}")
        print(f"Current Inventory Management: {variant['inventory_management']}")
        
        if update_variant(variant['id']):
            set_inventory(variant['inventory_item_id'], AUTODS_LOCATION_ID, 50)

if __name__ == "__main__":
    main()
