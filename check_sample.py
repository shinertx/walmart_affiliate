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
    print("🔍 Checking sample of 50 products...")
    
    url = f"{BASE_URL}/products.json?limit=50&fields=id,title,variants"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            print(f"❌ Error: {response.text}")
            return
            
        data = response.json()
        products = data.get('products', [])
        
        total = 0
        correct = 0
        
        for product in products:
            for variant in product['variants']:
                total += 1
                qty = variant.get('inventory_quantity', 0)
                tracking = variant.get('inventory_management')
                
                if qty >= 50 and tracking == 'shopify':
                    correct += 1
                else:
                    print(f"❌ {product['title']} - Qty: {qty}, Tracking: {tracking}")
        
        print(f"\n📊 Sample Results:")
        print(f"   Scanned: {total}")
        print(f"   Correct: {correct}")
        print(f"   Success Rate: {(correct/total)*100:.1f}%")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
