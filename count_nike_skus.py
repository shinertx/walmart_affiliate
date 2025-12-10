import os
import requests
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

def get_all_products():
    """Fetch all products using pagination"""
    products = []
    url = f"{BASE_URL}/products.json?limit=250&fields=id,title,vendor,tags,variants"
    
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

def main():
    print(f"🔌 Connecting to {SHOPIFY_STORE_URL}...")
    
    all_products = get_all_products()
    print(f"📦 Total products found: {len(all_products)}")
    
    nike_products_count = 0
    nike_skus_count = 0
    
    print("\n🔍 Searching for 'Nike' products...")
    
    for product in all_products:
        title = product.get('title', '').lower()
        vendor = product.get('vendor', '').lower()
        tags = product.get('tags', '').lower()
        
        if 'nike' in title or 'nike' in vendor or 'nike' in tags:
            variant_count = len(product['variants'])
            nike_products_count += 1
            nike_skus_count += variant_count
            # print(f"   - Found: {product['title']} ({variant_count} SKUs)")
            
    print("\n📊 Nike Inventory Summary:")
    print(f"   - Total Nike Products: {nike_products_count}")
    print(f"   - Total Nike SKUs (Variants): {nike_skus_count}")

if __name__ == "__main__":
    main()
