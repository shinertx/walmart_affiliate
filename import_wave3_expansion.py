import sys
import os
from pathlib import Path
import time
import json
import ssl
import certifi
from dotenv import load_dotenv
import shopify

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from walmart_api import WalmartAPIClient

load_dotenv()

# Fix SSL Context for Shopify API
ssl_context = ssl.create_default_context(cafile=certifi.where())
import urllib.request
original_urlopen = urllib.request.urlopen
def patched_urlopen(url, data=None, timeout=None, *, cafile=None, capath=None, cadefault=False, context=None):
    return original_urlopen(url, data, timeout, context=ssl_context)
urllib.request.urlopen = patched_urlopen

# Configuration
SHOPIFY_STORE_URL = os.getenv("SHOPIFY_STORE_URL")
SHOPIFY_ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")
API_VERSION = "2024-01"
AUTODS_LOCATION_ID = 80020111495  # AutoDS prod-wwbybglb

if not SHOPIFY_STORE_URL or not SHOPIFY_ACCESS_TOKEN:
    print("Error: Shopify credentials missing.")
    exit(1)

# Initialize Shopify
session = shopify.Session(SHOPIFY_STORE_URL, API_VERSION, SHOPIFY_ACCESS_TOKEN)
shopify.ShopifyResource.activate_session(session)

# Initialize Walmart
walmart_client = WalmartAPIClient()

def get_autods_fulfillment_service():
    try:
        services = shopify.FulfillmentService.find()
        for s in services:
            if s.location_id == AUTODS_LOCATION_ID:
                print(f"✅ Found AutoDS Fulfillment Service: {s.handle}")
                return s.handle
    except Exception as e:
        print(f"⚠️ Error finding fulfillment service: {e}")
    return None

AUTODS_HANDLE = get_autods_fulfillment_service()

# --- WAVE 3: EXPANSION KEYWORDS ---
# Focusing on Vacuums, Sporting Goods, and Household Items
EXPANSION_KEYWORDS = {
    "Vacuums": [
        "Robot Vacuum", "Cordless Vacuum", "Upright Vacuum", "Carpet Cleaner", "Handheld Vacuum", 
        "Shop Vac", "Stick Vacuum", "Canister Vacuum", "Steam Mop", "Vacuum Accessories",
        "Wet Dry Vac", "Pool Vacuum", "Leaf Vacuum", "Ash Vacuum", "Central Vacuum"
    ],
    "Sports": [
        "Camping Gear", "Exercise Bike", "Weights", "Kayak", "Paddle Board", 
        "Baseball", "Soccer", "Football", "Tennis", "Golf", "Hiking", 
        "Treadmill", "Elliptical", "Yoga", "Pilates", "Boxing", "Swimming",
        "Volleyball", "Badminton", "Table Tennis", "Skateboard", "Roller Skates", "Helmet", "Protective Gear", "Gym Bag"
    ],
    "Household": [
        "Air Purifier", "Dehumidifier", "Bed Sheets", "Comforter", "Cookware Set", 
        "Knife Set", "Dinnerware", "Storage Bins", "Trash Can", "Laundry Hamper",
        "Bath Towels", "Shower Curtain", "Kitchen Gadgets", "Food Storage", "Cleaning Supplies",
        "Mop", "Broom", "Dustpan", "Sponge", "Dish Soap", "Laundry Detergent", "Paper Towels", "Toilet Paper", "Tissues"
    ]
}

def calculate_price(cost):
    """
    Pricing Formula:
    ((Cost * 1.08 Tax * 1.10 Markup) + 0.30 Fee) / (1 - 0.029 Processing)
    Simplified: (Cost * 1.188 + 0.30) / 0.971
    """
    if not cost: return 0.0
    target = (cost * 1.188 + 0.30) / 0.971
    return round(target, 2)

def fetch_and_sort_items(query, category_name, max_items=500):
    """
    Fetches up to max_items, filters for quality, and sorts by review count.
    """
    print(f"\n🔍 Deep Search for '{query}' (Target: Top {max_items} items)...")
    
    all_candidates = []
    items_per_page = 25
    
    for page in range(0, 20): # 0 to 19
        start_index = (page * items_per_page) + 1
        if start_index > max_items:
            break
            
        try:
            response = walmart_client.search(query, numItems=items_per_page, start=start_index)
            
            if not response['success']:
                break
                
            items = response['data'].get('items', [])
            if not items:
                break
                
            all_candidates.extend(items)
            time.sleep(0.2)
            
        except Exception as e:
            print(f"   ⚠️ Error fetching page {page+1}: {e}")
            break
            
    print(f"   📊 Analyzed {len(all_candidates)} raw items.")
    
    # --- FILTERING ---
    valid_items = []
    for item in all_candidates:
        # 1. Filter: Sold by Walmart (First Party)
        marketplace = item.get('marketplace')
        seller_info = item.get('sellerInfo', '')
        is_walmart = (marketplace is False) or ("walmart" in seller_info.lower())
        
        if not is_walmart:
            continue
            
        # 2. Filter: In Stock
        if item.get('stock') != 'Available':
            continue
            
        # 3. Filter: Has Price
        if not item.get('salePrice'):
            continue
            
        valid_items.append(item)
        
    print(f"   ✅ Found {len(valid_items)} valid 'Sold by Walmart' items.")
    
    # --- SORTING ---
    for item in valid_items:
        if 'numReviews' not in item:
            item['numReviews'] = 0
        else:
            item['numReviews'] = int(item['numReviews'])
            
    sorted_items = sorted(valid_items, key=lambda x: x['numReviews'], reverse=True)
    return sorted_items

def import_wave3(target_category=None):
    print("🚀 Starting Wave 3: 'Expansion' (Vacuums, Sports, Household)...")
    
    total_imported = 0
    
    for category, keywords in EXPANSION_KEYWORDS.items():
        if target_category and category != target_category:
            continue

        print(f"\n📂 Processing Category: {category}")
        print("=" * 50)
        
        for keyword in keywords:
            top_items = fetch_and_sort_items(keyword, category)
            
            if not top_items:
                print(f"   ⚠️ No valid items found for '{keyword}'")
                continue
                
            print(f"   🏆 Importing Top {len(top_items)} Best Sellers for '{keyword}'...")
            
            for item in top_items:
                try:
                    walmart_id = str(item['itemId'])
                    title = item.get('name')
                    description = item.get('longDescription') or item.get('shortDescription') or ""
                    cost = item.get('salePrice')
                    images = item.get('imageEntities', [])
                    reviews = item.get('numReviews')
                    affiliate_link = walmart_client.generate_affiliate_link(item)
                    
                    target_price = calculate_price(cost)
                    
                    # Create in Shopify
                    product = shopify.Product()
                    product.title = title
                    # Description only, no visible affiliate link in body
                    product.body_html = description
                    product.vendor = "Walmart"
                    product.product_type = category
                    product.tags = f"Best-Seller, {category}, Sold-by-Walmart, {keyword}, Wave3"
                    product.status = "active"
                    
                    if images:
                        product.images = [{"src": img.get('largeImage')} for img in images if img.get('largeImage')]
                    elif item.get('largeImage'):
                         product.images = [{"src": item.get('largeImage')}]

                    variant = shopify.Variant()
                    variant.price = target_price
                    variant.sku = walmart_id
                    variant.inventory_management = "shopify"
                    
                    # If we found the AutoDS handle, use it directly
                    if AUTODS_HANDLE:
                        variant.fulfillment_service = AUTODS_HANDLE
                        variant.inventory_management = AUTODS_HANDLE
                    
                    variant.inventory_policy = "deny"
                    variant.inventory_quantity = 50 
                    
                    if affiliate_link:
                        product.metafields = [
                            {
                                "namespace": "walmart",
                                "key": "affiliate_url",
                                "value": affiliate_link,
                                "type": "single_line_text_field"
                            }
                        ]
                    
                    product.variants = [variant]
                    
                    if product.save():
                        print(f"      ✅ Imported: {title[:40]}... (Reviews: {reviews})")
                        total_imported += 1
                        
                        # --- UPDATE INVENTORY (Fallback if not set by fulfillment service) ---
                        if not AUTODS_HANDLE:
                            try:
                                # Reload product to get variant ID and inventory_item_id
                                product.reload()
                                variant = product.variants[0]
                                inventory_item_id = variant.inventory_item_id
                                
                                # 1. Connect AutoDS Location
                                shopify.InventoryLevel.connect(
                                    location_id=AUTODS_LOCATION_ID,
                                    inventory_item_id=inventory_item_id
                                )
                                
                                # 2. Set AutoDS Inventory to 50
                                shopify.InventoryLevel.set(
                                    location_id=AUTODS_LOCATION_ID,
                                    inventory_item_id=inventory_item_id,
                                    available=50
                                )
                                
                                # 3. Disconnect Default Location
                                levels = shopify.InventoryLevel.find(inventory_item_ids=inventory_item_id)
                                for level in levels:
                                    if level.location_id != AUTODS_LOCATION_ID:
                                        shopify.InventoryLevel.delete(
                                            inventory_item_id=inventory_item_id,
                                            location_id=level.location_id
                                        )
                                
                            except Exception as inv_err:
                                print(f"         ⚠️ Failed to update AutoDS inventory: {inv_err}")
                            
                    else:
                        print(f"      ❌ Failed to save {title[:30]}...")
                        
                    # Rate limit Shopify (Increased to 10s to avoid 429 errors with parallel workers)
                    time.sleep(10)
                    
                except Exception as e:
                    if "429" in str(e):
                        print(f"      ⚠️ Rate limit hit. Sleeping for 30s...")
                        time.sleep(30)
                    else:
                        print(f"      ❌ Error importing item: {e}")
                    
    print(f"\n✨ Wave 3 Complete! Total Expansion Items Imported: {total_imported}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Import Walmart Wave 3 Expansion")
    parser.add_argument("--category", type=str, help="Specific category to import")
    args = parser.parse_args()
    
    import_wave3(target_category=args.category)
