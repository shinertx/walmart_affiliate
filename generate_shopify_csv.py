import os
import sys
import csv
import time
import urllib.parse
from src.walmart_api import WalmartAPIClient

# Shopify CSV Headers
SHOPIFY_HEADERS = [
    'Handle', 'Title', 'Body (HTML)', 'Vendor', 'Product Category', 'Type', 'Tags', 'Published',
    'Option1 Name', 'Option1 Value', 'Option2 Name', 'Option2 Value', 'Option3 Name', 'Option3 Value',
    'Variant SKU', 'Variant Grams', 'Variant Inventory Tracker', 'Variant Inventory Qty',
    'Variant Price', 'Variant Compare At Price', 'Variant Requires Shipping', 'Variant Taxable',
    'Image Src', 'Image Position', 'Image Alt Text', 'Gift Card', 'SEO Title', 'SEO Description',
    'Google Shopping / Google Product Category', 'Google Shopping / Gender', 'Google Shopping / Age Group',
    'Google Shopping / MPN', 'Google Shopping / AdWords Grouping', 'Google Shopping / AdWords Labels',
    'Google Shopping / Condition', 'Google Shopping / Custom Product', 'Google Shopping / Custom Label 0',
    'Google Shopping / Custom Label 1', 'Google Shopping / Custom Label 2', 'Google Shopping / Custom Label 3',
    'Google Shopping / Custom Label 4', 'Variant Image', 'Variant Weight Unit', 'Cost per item'
]

def clean_text(text):
    if not text:
        return ""
    return text.replace('\n', ' ').replace('\r', '').strip()

def map_to_shopify(item):
    """Map a Walmart item to a Shopify CSV row"""
    
    # Basic Info
    title = clean_text(item.get('name', ''))
    handle = title.lower().replace(' ', '-').replace('/', '-').replace('&', '-').replace('--', '-')[:255] # Simple handle generation
    description = clean_text(item.get('longDescription', item.get('shortDescription', '')))
    vendor = clean_text(item.get('brandName', 'Walmart'))
    product_type = clean_text(item.get('categoryPath', '').split('/')[0] if item.get('categoryPath') else 'General')
    
    # Tags
    tags = ["Walmart", "Ship to Home"]
    if item.get('pickupTodayEligible'):
        tags.append("Same Day")
    if item.get('clearance'):
        tags.append("Clearance")
    if item.get('categoryPath'):
        tags.extend(item.get('categoryPath').split('/'))
    tags_str = ','.join(set(tags))
    
    # Pricing
    cost_price = item.get('salePrice', 0)
    # DROPSHIP MARKUP: Add 40% to the price
    markup_percentage = 0.40 
    price = round(cost_price * (1 + markup_percentage), 2)
    
    # Set Compare At Price (MSRP)
    # If the calculated price is still lower than MSRP, show MSRP. 
    # Otherwise, hide MSRP so it doesn't look like a fake sale.
    compare_at_price = item.get('msrp', 0)
    if compare_at_price and compare_at_price <= price:
        compare_at_price = "" 
        
    # Images
    image_src = item.get('largeImage', item.get('mediumImage', item.get('thumbnailImage', '')))
    
    # SKU / ID
    # AutoDS prefers the Walmart Item ID as the SKU for tracking
    sku = str(item.get('itemId', ''))
    
    # Add Source URL to tags for easy reference
    source_url = f"https://www.walmart.com/ip/{sku}"
    tags_list = tags_str.split(',')
    tags_list.append("Source:Walmart")
    tags_str = ','.join(tags_list)
    
    return {
        'Handle': handle,
        'Title': title,
        'Body (HTML)': description,
        'Vendor': vendor,
        'Product Category': '', # Optional, can map if needed
        'Type': product_type,
        'Tags': tags_str,
        'Published': 'TRUE',
        'Option1 Name': 'Title',
        'Option1 Value': 'Default Title',
        'Option2 Name': '',
        'Option2 Value': '',
        'Option3 Name': '',
        'Option3 Value': '',
        'Variant SKU': sku,
        'Variant Grams': '0', # Walmart doesn't always provide weight in grams easily
        'Variant Inventory Tracker': 'shopify',
        'Variant Inventory Qty': '10', # Default stock
        'Variant Price': price,
        'Variant Compare At Price': compare_at_price,
        'Variant Requires Shipping': 'TRUE',
        'Variant Taxable': 'TRUE',
        'Image Src': image_src,
        'Image Position': '1',
        'Image Alt Text': title,
        'Gift Card': 'FALSE',
        'SEO Title': title,
        'SEO Description': description[:320],
        'Google Shopping / Condition': 'New',
        'Variant Weight Unit': 'lb',
        'Cost per item': cost_price # Store the cost price for Shopify analytics
    }

def fetch_and_export(target_count=5000):
    client = WalmartAPIClient()
    all_items = []
    
    # Categories to cycle through to get variety
    # Electronics, Home, Toys, Clothing, Household Essentials
    categories = ['3944', '4044', '4171', '5438', '1115193']
    items_per_category = target_count // len(categories)
    
    print(f"🚀 Starting export of {target_count} items ({items_per_category} per category)...")
    
    with open('walmart_products_export.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=SHOPIFY_HEADERS)
        writer.writeheader()
        
        total_exported = 0
        
        for category in categories:
            print(f"\n📂 Processing Category ID: {category}")
            category_count = 0
            next_cursor = None
            
            while category_count < items_per_category:
                # Determine batch size
                batch_size = min(100, items_per_category - category_count)
                
                # Prepare params
                params = {'count': batch_size, 'category': category}
                if next_cursor:
                    params['lastDoc'] = next_cursor
                
                try:
                    print(f"   • Fetching batch (Target: {category_count}/{items_per_category})...")
                    # We use get_products but pass lastDoc if we have it
                    # Note: get_products signature is (count, category, brand, special_offer, **kwargs)
                    # So we pass lastDoc as a kwarg
                    
                    if next_cursor:
                        result = client.get_products(count=batch_size, category=category, lastDoc=next_cursor)
                    else:
                        result = client.get_products(count=batch_size, category=category)
                    
                    if not result['success']:
                        print(f"   ❌ Error: {result.get('error')}")
                        break
                        
                    items = result['data']['items']
                    if not items:
                        print("   ⚠️  No more items in this category.")
                        break
                        
                    # Process and write items
                    for item in items:
                        row = map_to_shopify(item)
                        writer.writerow(row)
                        
                    count_in_batch = len(items)
                    category_count += count_in_batch
                    total_exported += count_in_batch
                    
                    print(f"   ✅ Exported {count_in_batch} items. Total: {total_exported}")
                    
                    # Get next page cursor
                    next_page_url = result['metadata'].get('next_page')
                    if next_page_url:
                        # Extract lastDoc from URL
                        parsed = urllib.parse.urlparse(next_page_url)
                        qs = urllib.parse.parse_qs(parsed.query)
                        if 'lastDoc' in qs:
                            next_cursor = qs['lastDoc'][0]
                        else:
                            print("   ⚠️  No lastDoc found in next_page URL. Stopping category.")
                            break
                    else:
                        print("   ⚠️  No next_page returned. Stopping category.")
                        break
                        
                    # Be nice to the API
                    time.sleep(0.5)
                    
                except Exception as e:
                    print(f"   ❌ Exception: {e}")
                    break
                    
    print(f"\n🎉 Export Complete! {total_exported} items written to 'walmart_products_export.csv'")

if __name__ == "__main__":
    fetch_and_export(5000)
