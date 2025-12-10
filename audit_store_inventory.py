import sys
import os
from pathlib import Path
import json
import time
import csv
import requests
from dotenv import load_dotenv

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from walmart_api import WalmartAPIClient

load_dotenv()

# Shopify Configuration
SHOPIFY_STORE_URL = os.getenv('SHOPIFY_STORE_URL')
SHOPIFY_ACCESS_TOKEN = os.getenv('SHOPIFY_ACCESS_TOKEN')
API_VERSION = "2024-01"

if not SHOPIFY_STORE_URL or not SHOPIFY_ACCESS_TOKEN:
    print("❌ Error: Shopify credentials not found in .env file.")
    sys.exit(1)

BASE_URL = f"https://{SHOPIFY_STORE_URL}/admin/api/{API_VERSION}"
HEADERS = {
    "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN,
    "Content-Type": "application/json"
}

def get_all_shopify_products():
    print("📥 Fetching all products from Shopify...")
    products = []
    url = f"{BASE_URL}/products.json?limit=250"
    
    while url:
        try:
            response = requests.get(url, headers=HEADERS)
            if response.status_code == 200:
                data = response.json()
                batch = data.get('products', [])
                products.extend(batch)
                print(f"   Fetched {len(batch)} products... (Total: {len(products)})")
                
                # Pagination
                link_header = response.headers.get('Link')
                url = None
                if link_header:
                    links = link_header.split(', ')
                    for link in links:
                        if 'rel="next"' in link:
                            url = link[link.find('<')+1 : link.find('>')]
            else:
                print(f"❌ Error fetching Shopify products: {response.status_code} - {response.text}")
                break
        except Exception as e:
            print(f"❌ Exception: {e}")
            break
            
    return products

def calculate_target_price(walmart_price):
    # Formula: ((Cost * 1.08 [Tax] + Cost * 0.10 [Markup]) + 0.30 [Fixed Fee]) / (1 - 0.029 [Proc Fee])
    # Simplified: (Cost * 1.18 + 0.30) / 0.971
    
    if not walmart_price:
        return 0.0
        
    cost_with_tax_and_markup = walmart_price * 1.18
    target_price = (cost_with_tax_and_markup + 0.30) / 0.971
    return round(target_price, 2)

def audit_inventory():
    client = WalmartAPIClient()
    shopify_products = get_all_shopify_products()
    
    if not shopify_products:
        print("No products found in Shopify.")
        return

    print(f"\n🔍 Auditing {len(shopify_products)} products against Walmart API...")
    
    # Prepare CSV report
    report_file = 'inventory_audit_report.csv'
    fieldnames = ['Shopify_ID', 'Title', 'SKU', 'Walmart_Status', 'Seller', 'Stock', 'Cost', 'Current_Price', 'Target_Price', 'GTIN_Found', 'Action_Needed']
    
    audit_results = {
        'total': 0,
        'valid_walmart': 0,
        'third_party': 0,
        'out_of_stock': 0,
        'missing_gtin': 0,
        'invalid_sku': 0
    }

    with open(report_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        # Process in batches of 20 to respect Walmart API
        batch_size = 20
        for i in range(0, len(shopify_products), batch_size):
            batch = shopify_products[i:i+batch_size]
            
            # Map SKU to Shopify Product for easy lookup
            sku_map = {}
            ids_to_fetch = []
            
            for p in batch:
                variants = p.get('variants', [])
                if variants:
                    # Assuming first variant holds the main SKU
                    sku = variants[0].get('sku')
                    if sku and sku.isdigit(): # Basic validation that SKU looks like a Walmart ID
                        ids_to_fetch.append(sku)
                        sku_map[sku] = p
                    else:
                        # Log invalid SKU immediately
                        writer.writerow({
                            'Shopify_ID': p['id'],
                            'Title': p['title'],
                            'SKU': sku,
                            'Walmart_Status': 'Invalid SKU Format',
                            'Action_Needed': 'Check SKU'
                        })
                        audit_results['invalid_sku'] += 1

            if not ids_to_fetch:
                continue
                
            # Fetch from Walmart
            try:
                response = client.get_items_by_ids(ids=ids_to_fetch)
                walmart_items = {}
                if response['success']:
                    items_data = response['data'].get('items', [])
                    for item in items_data:
                        walmart_items[str(item['itemId'])] = item
                
                # Process each product in the batch
                for sku in ids_to_fetch:
                    product = sku_map[sku]
                    w_item = walmart_items.get(sku)
                    
                    row = {
                        'Shopify_ID': product['id'],
                        'Title': product['title'],
                        'SKU': sku,
                        'Current_Price': product['variants'][0]['price']
                    }
                    
                    if not w_item:
                        row['Walmart_Status'] = 'Not Found in Walmart API'
                        row['Action_Needed'] = 'Archive/Delete'
                        audit_results['invalid_sku'] += 1
                    else:
                        # Analyze Walmart Data
                        price = w_item.get('salePrice')
                        stock = w_item.get('stock')
                        seller = w_item.get('sellerInfo')
                        marketplace = w_item.get('marketplace')
                        gtin = w_item.get('upc') or w_item.get('gtin')
                        
                        row['Cost'] = price
                        row['Stock'] = stock
                        row['Seller'] = seller or ('Walmart' if not marketplace else 'Unknown')
                        row['GTIN_Found'] = 'Yes' if gtin else 'No'
                        
                        # Determine Status
                        is_walmart = (marketplace is False) or (seller and "walmart" in seller.lower())
                        
                        if not is_walmart:
                            row['Walmart_Status'] = 'Third Party'
                            row['Action_Needed'] = 'Archive (3rd Party)'
                            audit_results['third_party'] += 1
                        elif stock != 'Available':
                            row['Walmart_Status'] = 'Out of Stock'
                            row['Action_Needed'] = 'Pause (OOS)'
                            audit_results['out_of_stock'] += 1
                        elif not gtin:
                            row['Walmart_Status'] = 'Missing GTIN'
                            row['Action_Needed'] = 'Review (No GTIN)'
                            audit_results['missing_gtin'] += 1
                        else:
                            row['Walmart_Status'] = 'Valid'
                            row['Target_Price'] = calculate_target_price(price)
                            row['Action_Needed'] = 'Update Price & Sync'
                            audit_results['valid_walmart'] += 1
                            
                    writer.writerow(row)
                    audit_results['total'] += 1
                    
            except Exception as e:
                print(f"Error processing batch: {e}")
            
            # Rate limiting delay
            time.sleep(1)
            print(f"   Processed {min(i+batch_size, len(shopify_products))}/{len(shopify_products)} products...", end='\r')

    print("\n\n📊 Audit Complete!")
    print(f"Total Products Audited: {audit_results['total']}")
    print(f"✅ Valid Walmart Items: {audit_results['valid_walmart']}")
    print(f"❌ Third Party Sellers: {audit_results['third_party']}")
    print(f"❌ Out of Stock: {audit_results['out_of_stock']}")
    print(f"❌ Missing GTIN: {audit_results['missing_gtin']}")
    print(f"❌ Invalid/Not Found SKUs: {audit_results['invalid_sku']}")
    print(f"\nDetailed report saved to: {report_file}")

if __name__ == "__main__":
    audit_inventory()
