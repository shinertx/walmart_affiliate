import os
import requests
from dotenv import load_dotenv

load_dotenv()

SHOPIFY_STORE_URL = os.getenv('SHOPIFY_STORE_URL')
SHOPIFY_ACCESS_TOKEN = os.getenv('SHOPIFY_ACCESS_TOKEN')
API_VERSION = "2024-01"
BASE_URL = f"https://{SHOPIFY_STORE_URL}/admin/api/{API_VERSION}"
HEADERS = {
    "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN,
    "Content-Type": "application/json"
}

def main():
    url = f"{BASE_URL}/products.json?limit=250&fields=id,title,status,variants,tags"
    print("Searching for Downy...")
    
    while url:
        response = requests.get(url, headers=HEADERS)
        data = response.json()
        products = data.get('products', [])
        
        for product in products:
            if "Downy" in product['title']:
                print(f"Found Product: {product['title']} (ID: {product['id']})")
                print(f"Tags: {product['tags']}")
                print(f"Status: {product['status']}")
                for variant in product['variants']:
                    print(f"\nVariant ID: {variant['id']}")
                    print(f"  Fulfillment Service: {variant['fulfillment_service']}")
                    print(f"  Inventory Management: {variant['inventory_management']}")
                    print(f"  Inventory Policy: {variant['inventory_policy']}")
                    print(f"  Inventory Quantity: {variant['inventory_quantity']}")
                return # Found one, exit
        
        link = response.headers.get('Link')
        url = None
        if link:
            links = link.split(',')
            for l in links:
                if 'rel="next"' in l:
                    url = l.split(';')[0].strip('<> ')

if __name__ == "__main__":
    main()
