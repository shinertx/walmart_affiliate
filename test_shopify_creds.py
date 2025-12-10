import os
import requests
from dotenv import load_dotenv

def test_shopify_connection():
    load_dotenv()
    
    store_url = os.getenv('SHOPIFY_STORE_URL')
    token = os.getenv('SHOPIFY_ACCESS_TOKEN')
    
    print(f"Testing connection to: {store_url}")
    print(f"Using Token: {token[:10]}... (masked)")
    
    if not token or not store_url:
        print("❌ Missing credentials in .env file")
        return

    if not token.startswith('shpat_'):
        print("\n⚠️  WARNING: The token does not start with 'shpat_'.")
        print("   You likely copied the 'API Secret Key' instead of the 'Admin API Access Token'.")
        print("   The script requires the token that is revealed after clicking 'Install App'.")
    
    url = f"https://{store_url}/admin/api/2024-01/shop.json"
    headers = {
        "X-Shopify-Access-Token": token,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            shop = response.json().get('shop', {})
            print(f"\n✅ SUCCESS! Connected to shop: {shop.get('name')}")
            print(f"   Email: {shop.get('email')}")
            print(f"   Currency: {shop.get('currency')}")
        else:
            print(f"\n❌ FAILED. Status Code: {response.status_code}")
            print(f"   Response: {response.text}")
            print("\n   Please check that you copied the 'Admin API access token' (starts with shpat_)")
            
    except Exception as e:
        print(f"\n❌ Connection Error: {e}")

if __name__ == "__main__":
    test_shopify_connection()
