import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

SHOPIFY_STORE_URL = os.getenv('SHOPIFY_STORE_URL')
SHOPIFY_ACCESS_TOKEN = os.getenv('SHOPIFY_ACCESS_TOKEN')
API_VERSION = "2024-01"

HEADERS = {
    "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN,
    "Content-Type": "application/json"
}

def inspect_product(product_id):
    url = f"https://{SHOPIFY_STORE_URL}/admin/api/{API_VERSION}/products/{product_id}.json"
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code == 200:
        product = response.json().get('product')
        print(json.dumps(product, indent=2))
    else:
        print(f"Error: {response.status_code} - {response.text}")

if __name__ == "__main__":
    # ID from the CSV report that had "Invalid SKU Format"
    inspect_product("8143752364167")
