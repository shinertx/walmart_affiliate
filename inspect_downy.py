import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

SHOPIFY_STORE_URL = os.getenv('SHOPIFY_STORE_URL')
SHOPIFY_ACCESS_TOKEN = os.getenv('SHOPIFY_ACCESS_TOKEN')
API_VERSION = "2024-01"

BASE_URL = f"https://{SHOPIFY_STORE_URL}/admin/api/{API_VERSION}"
HEADERS = {
    "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN,
    "Content-Type": "application/json"
}

def find_product_by_title(title_fragment):
    url = f"{BASE_URL}/products.json?title={title_fragment}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        products = response.json().get('products', [])
        if products:
            return products[0]
    return None

def main():
    # Search for one of the items the user mentioned
    # Try a broader search
    url = f"{BASE_URL}/products.json?limit=50" 
    response = requests.get(url, headers=HEADERS)
    products = response.json().get('products', [])
    
    found = False
    for product in products:
        if "Downy" in product['title']:
            found = True
            print(f"Found Product: {product['title']} (ID: {product['id']})")
            print(f"Status: {product['status']}")
            for variant in product['variants']:
                print(f"\nVariant ID: {variant['id']}")
                print(f"  Fulfillment Service: {variant['fulfillment_service']}")
                print(f"  Inventory Management: {variant['inventory_management']}")
                print(f"  Inventory Policy: {variant['inventory_policy']}")
                print(f"  Inventory Quantity: {variant['inventory_quantity']}")
                print(f"  Inventory Item ID: {variant['inventory_item_id']}")
            break
    
    if not found:
        print("Downy product not found in first 50 items.")

if __name__ == "__main__":
    main()
