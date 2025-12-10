import sys
import os
from pathlib import Path
import json
import requests
from dotenv import load_dotenv

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from walmart_api import WalmartAPIClient

load_dotenv()

def main():
    client = WalmartAPIClient()
    
    query = "Hanes Men's Over the Calf Tube Socks 6-Pack White Enforced Toe Fresh IQ sz 6-12"
    print(f"🔍 Searching Walmart for: '{query}'")
    
    search_url = "https://developer.api.walmart.com/api-proxy/service/affil/product/v2/search"
    headers = client._get_headers()
    params = {
        'query': query,
        'numItems': 10
    }
    
    try:
        response = requests.get(search_url, headers=headers, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('items', [])
            
            print(f"✅ Found {len(items)} items.")
            
            for item in items:
                print("\n--------------------------------------------------")
                print(f"Title: {item.get('name')}")
                print(f"Item ID: {item.get('itemId')}")
                print(f"Price: ${item.get('salePrice')}")
                print(f"Stock: {item.get('stock')}")
                print(f"URL: {item.get('productTrackingUrl')}")
                
                # Check if it matches closely
                if "Tube Socks" in item.get('name', '') and "6-Pack" in item.get('name', ''):
                     print("🌟 POTENTIAL MATCH")
                     
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    main()
