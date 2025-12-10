import os
import requests
import csv
from dotenv import load_dotenv

load_dotenv()

SHOPIFY_STORE_URL = os.getenv('SHOPIFY_STORE_URL')
SHOPIFY_ACCESS_TOKEN = os.getenv('SHOPIFY_ACCESS_TOKEN')
API_VERSION = "2024-01"
AUTODS_HANDLE = "autods-prod-wwbybglb"

BASE_URL = f"https://{SHOPIFY_STORE_URL}/admin/api/{API_VERSION}"
HEADERS = {
    "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN,
    "Content-Type": "application/json"
}

import time

def get_all_products():
    products = []
    url = f"{BASE_URL}/products.json?limit=250&fields=handle,title,variants,tags"
    print("📥 Fetching products for CSV generation...")
    
    page = 1
    while url:
        print(f"   Fetching page {page}...")
        response = requests.get(url, headers=HEADERS)
        
        if response.status_code == 429:
            print("   ⚠️ Rate limit hit, sleeping 2s...")
            time.sleep(2)
            continue
            
        if response.status_code != 200:
            print(f"❌ Error: {response.text}")
            break
        
        data = response.json()
        products.extend(data.get('products', []))
        
        link = response.headers.get('Link')
        url = None
        if link:
            links = link.split(',')
            for l in links:
                if 'rel="next"' in l:
                    url = l.split(';')[0].strip('<> ')
            page += 1
    return products

def main():
    products = get_all_products()
    print(f"📦 Total products: {len(products)}")
    
    csv_filename = "autods_migration.csv"
    
    # CSV Headers for Shopify Import
    # We only need minimal columns to update variants
    headers = [
        "Handle", 
        "Title",
        "Option1 Name", "Option1 Value",
        "Option2 Name", "Option2 Value",
        "Option3 Name", "Option3 Value",
        "Variant SKU",
        "Variant Inventory Tracker", 
        "Variant Fulfillment Service", 
        "Variant Inventory Policy", 
        "Variant Inventory Qty"
    ]
    
    rows = []
    count = 0
    
    for product in products:
        # User wants ALL items migrated, including Walmart ones
        # tags = product.get('tags', '')
        # if "Source:Walmart" in tags:
        #     continue

        for variant in product['variants']:
            # We want to force update everything to 50, regardless of current state.
            # This ensures 123 Cedar items are moved and AutoDS items are topped up.
            
            # Prepare row
            row = {
                "Handle": product['handle'],
                "Title": product['title'], # Optional but good for reference
                "Option1 Name": "Title", # Default for single variant
                "Option1 Value": "Default Title",
                "Option2 Name": "", "Option2 Value": "",
                "Option3 Name": "", "Option3 Value": "",
                "Variant SKU": variant.get('sku', ''),
                "Variant Inventory Tracker": "shopify", # MUST be shopify
                "Variant Fulfillment Service": AUTODS_HANDLE,
                "Variant Inventory Policy": "deny",
                "Variant Inventory Qty": 50
            }
            
            # Handle Options correctly
            # Shopify API gives options in a list, but variants have 'option1', 'option2', 'option3'
            row["Option1 Name"] = "" # We don't strictly need Option Names for updates if we match by Handle/Option Values
            # Actually, for updates, Handle + Option Values identify the variant.
            
            row["Option1 Value"] = variant.get('option1')
            row["Option2 Value"] = variant.get('option2')
            row["Option3 Value"] = variant.get('option3')
            
            rows.append(row)
            count += 1

    print(f"📝 Generating CSV with {count} variants...")
    
    with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
        
    print(f"✅ Done! Saved to {csv_filename}")

if __name__ == "__main__":
    main()
