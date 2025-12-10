import sys
import os
from pathlib import Path
import json
import csv
import re

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from walmart_api import WalmartAPIClient

def clean_html(raw_html):
    if not raw_html:
        return ""
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext

def generate_handle(title):
    # Create a URL-friendly handle
    handle = title.lower()
    handle = re.sub(r'[^a-z0-9\s-]', '', handle)
    handle = re.sub(r'\s+', '-', handle)
    return handle[:255]

def main():
    client = WalmartAPIClient()
    
    # Search queries to cover "all playstations"
    queries = [
        "PlayStation 5 Console",
        "PlayStation 5 Slim",
        "PlayStation 5 Bundle"
    ]
    
    all_items = {} # Use dict to deduplicate by itemId
    
    print("🔍 Searching for PlayStations...")
    
    for query in queries:
        print(f"   Searching for '{query}'...")
        # We'll fetch 2 pages for each query to get a good selection
        for page in range(2):
            start_index = page * 25 + 1
            try:
                # Using the search endpoint manually as in search_ps5.py
                search_url = "https://developer.api.walmart.com/api-proxy/service/affil/product/v2/search"
                headers = client._get_headers()
                params = {
                    'query': query,
                    'numItems': 25,
                    'start': start_index
                }
                
                import requests
                response = requests.get(search_url, headers=headers, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    items = data.get('items', [])
                    for item in items:
                        item_id = str(item.get('itemId'))
                        if item_id not in all_items:
                            all_items[item_id] = item
                else:
                    print(f"   ❌ Error searching page {page+1}: {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Exception: {e}")

    print(f"✅ Found {len(all_items)} unique PlayStation items.")
    
    # Fetch full details for these items to get better descriptions/images if needed
    # Although search results usually have enough for a basic listing.
    # Let's use the search result data directly to be faster, as it has price, image, name.
    
    csv_filename = "playstation_products_shopify.csv"
    
    # Shopify CSV Headers
    headers = [
        "Handle", "Title", "Body (HTML)", "Vendor", "Type", "Tags", "Published",
        "Option1 Name", "Option1 Value", "Option2 Name", "Option2 Value", "Option3 Name", "Option3 Value",
        "Variant SKU", "Variant Grams", "Variant Inventory Tracker", "Variant Inventory Qty",
        "Variant Inventory Policy", "Variant Fulfillment Service", "Variant Price",
        "Variant Compare At Price", "Variant Requires Shipping", "Variant Taxable",
        "Image Src", "Image Position", "Image Alt Text", "Gift Card",
        "SEO Title", "SEO Description"
    ]
    
    rows = []
    
    print("📝 Generating CSV...")
    
    for item_id, item in all_items.items():
        title = item.get('name', 'Unknown PlayStation Item')
        handle = generate_handle(title)
        description = item.get('shortDescription') or item.get('longDescription') or title
        # Clean description if it's HTML encoded or messy, but Shopify accepts HTML.
        # Usually Walmart API returns HTML in description.
        
        price = item.get('salePrice')
        msrp = item.get('msrp')
        
        # Skip if no price
        if not price:
            continue
            
        image_url = item.get('largeImage') or item.get('mediumImage') or item.get('thumbnailImage')
        
        row = {
            "Handle": handle,
            "Title": title,
            "Body (HTML)": description,
            "Vendor": "Sony", # Or "Walmart"
            "Type": "Gaming Console",
            "Tags": "PlayStation, PS5, Console, Gaming, Walmart",
            "Published": "TRUE",
            "Option1 Name": "Title",
            "Option1 Value": "Default Title",
            "Option2 Name": "", "Option2 Value": "",
            "Option3 Name": "", "Option3 Value": "",
            "Variant SKU": item_id, # Use Walmart ID as SKU
            "Variant Grams": "4500", # Approx weight for PS5
            "Variant Inventory Tracker": "shopify",
            "Variant Inventory Qty": "10", # Default stock
            "Variant Inventory Policy": "deny",
            "Variant Fulfillment Service": "manual", # User can change to AutoDS later
            "Variant Price": str(price),
            "Variant Compare At Price": str(msrp) if msrp else "",
            "Variant Requires Shipping": "TRUE",
            "Variant Taxable": "TRUE",
            "Image Src": image_url,
            "Image Position": "1",
            "Image Alt Text": title,
            "Gift Card": "FALSE",
            "SEO Title": title,
            "SEO Description": clean_html(description)[:320] if description else ""
        }
        rows.append(row)

    with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
        
    print(f"🎉 Successfully generated '{csv_filename}' with {len(rows)} products.")
    print("👉 You can now import this file into Shopify.")

if __name__ == "__main__":
    main()
