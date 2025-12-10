import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

SHOP_URL = f"https://{os.getenv('SHOPIFY_STORE_URL')}"
ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")

headers = {
    "X-Shopify-Access-Token": ACCESS_TOKEN,
    "Content-Type": "application/json"
}

def get_product_by_title(title):
    url = f"{SHOP_URL}/admin/api/2024-01/products.json"
    params = {"title": title}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        products = response.json().get("products", [])
        if products:
            return products[0]
    return None

def inspect_variant(variant_id):
    url = f"{SHOP_URL}/admin/api/2024-01/variants/{variant_id}.json"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get("variant")
    return None

def get_locations():
    url = f"{SHOP_URL}/admin/api/2024-01/locations.json"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get("locations", [])
    return []

# Check one of the items that was failing
product = get_product_by_title("Honeydew Intimates 2pc Good Times Pajama Set")

if product:
    print(f"Found Product: {product['title']} (ID: {product['id']})")
    locations = get_locations()
    print("\n--- Available Locations ---")
    for loc in locations:
        print(f"ID: {loc['id']}, Name: {loc['name']}")
        if "AutoDS" in loc['name']:
            print(f"  FULL DATA: {json.dumps(loc, indent=2)}")

    print("\n--- Variant Details ---")
    for variant in product['variants']:
        print(f"\nVariant: {variant['title']} (ID: {variant['id']})")
        print(f"  Fulfillment Service: {variant['fulfillment_service']}")
        print(f"  Inventory Management: {variant['inventory_management']}")
        print(f"  Inventory Item ID: {variant['inventory_item_id']}")
        
        # Check inventory levels for this item
        inv_url = f"{SHOP_URL}/admin/api/2024-01/inventory_levels.json?inventory_item_ids={variant['inventory_item_id']}"
        inv_res = requests.get(inv_url, headers=headers)
        if inv_res.status_code == 200:
            levels = inv_res.json().get("inventory_levels", [])
            print("  Current Inventory Levels:")
            for level in levels:
                loc_name = next((l['name'] for l in locations if l['id'] == level['location_id']), "Unknown")
                print(f"    - {loc_name}: {level['available']}")
else:
    print("Product not found.")
