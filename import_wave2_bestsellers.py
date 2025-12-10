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

# --- WAVE 2: POWER KEYWORDS ---
# These are high-volume terms that cover the "Best Seller" categories
POWER_KEYWORDS = {
    "Electronics": [
        "TV", "Laptop", "Headphones", "Tablet", "Camera", "Speaker", "Monitor", "Printer", "Smart Watch", "Drone",
        "Gaming Console", "Soundbar", "Projector", "Hard Drive", "Keyboard", "Mouse", "Webcam", "Microphone", "Smart Home Hub", "Router"
    ],
    "Home": [
        "Vacuum", "Blender", "Coffee Maker", "Air Fryer", "Microwave", "Toaster", "Mixer", "Iron", "Fan", "Heater",
        "Bedding", "Towels", "Curtains", "Rug", "Lamp", "Mirror", "Clock", "Pillow", "Blanket", "Organizer",
        "Slow Cooker", "Pressure Cooker", "Air Purifier", "Dehumidifier", "Humidifier", "Food Processor", "Juicer", "Rice Cooker", "Waffle Maker", "Griddle"
    ],
    "Toys": [
        "Lego", "Lego Star Wars", "Lego Technic", "Lego City", "Lego Friends", "Lego Ninjago", "Lego Marvel", "Lego Harry Potter",
        "Doll", "Action Figure", "Board Game", "Puzzle", "Bike", "Scooter", "Drone", "Robot", "Car",
        "Nerf", "Barbie", "Hot Wheels", "Play Dough", "Stuffed Animal", "Building Blocks", "Art Set", "Science Kit", "Outdoor Play", "Trampoline", "Swing Set"
    ],
    "Sports": [
        "Treadmill", "Dumbbell", "Yoga Mat", "Tent", "Sleeping Bag", "Backpack", "Cooler", "Fishing Rod", "Golf Clubs", "Basketball",
        "Soccer Ball", "Football", "Baseball Bat", "Tennis Racket", "Helmet", "Kettlebell", "Resistance Bands", "Exercise Bike", "Elliptical", "Rowing Machine"
    ],
    "Automotive": [
        "Car Vacuum", "Dash Cam", "Car Seat Covers", "Floor Mats", 
        "Jump Starter", "Tire Inflator", "Car Wash Kit", "Oil", "Wiper Blades", "Battery Charger"
    ],
    "Office": [
        "Office Chair", "Computer Desk", "Printer", "Shredder", 
        "File Cabinet", "Desk Lamp", "Monitor Stand", "Keyboard", "Mouse", "Webcam"
    ],
    "Patio & Garden": [
        "Patio Set", "Grill", "Fire Pit", "Lawn Mower", 
        "Leaf Blower", "Garden Hose", "Planter", "Pressure Washer", "String Lights", "Hammock"
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
    # We'll try to fetch multiple pages. 
    # Note: The API might limit deep pagination. We'll try up to 20 pages (500 items).
    
    # The search API usually uses 'start' or 'offset'. 
    # Based on standard Walmart API, 'start' is the item index (1, 26, 51...).
    
    for page in range(0, 20): # 0 to 19
        start_index = (page * items_per_page) + 1
        if start_index > max_items:
            break
            
        # print(f"   Fetching page {page+1} (Start: {start_index})...")
        
        try:
            # Pass 'start' parameter to pagination
            response = walmart_client.search(query, numItems=items_per_page, start=start_index)
            
            if not response['success']:
                # print(f"   ⚠️ Page {page+1} failed or end of results.")
                break
                
            items = response['data'].get('items', [])
            if not items:
                break
                
            all_candidates.extend(items)
            
            # Rate limit slightly to be nice
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
    
    # --- SORTING (The "Best Seller" Logic) ---
    # Sort by number of reviews (descending)
    for item in valid_items:
        if 'numReviews' not in item:
            item['numReviews'] = 0
        else:
            item['numReviews'] = int(item['numReviews'])
            
    sorted_items = sorted(valid_items, key=lambda x: x['numReviews'], reverse=True)
    
    # Import all valid items found (removed top 10 cap)
    top_sellers = sorted_items
    
    return top_sellers

def import_wave2(target_category=None):
    print("🚀 Starting Wave 2: 'Best Sellers' Reconstruction...")
    
    total_imported = 0
    
    for category, keywords in POWER_KEYWORDS.items():
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
                    
                    # Apply markup formula to cover fees
                    target_price = calculate_price(cost)
                    # target_price = cost
                    
                    # Create in Shopify
                    product = shopify.Product()
                    product.title = title
                    # Description only, no visible affiliate link in body
                    product.body_html = description
                    product.vendor = "Walmart"
                    product.product_type = category
                    product.tags = f"Best-Seller, {category}, Sold-by-Walmart, {keyword}"
                    product.status = "active"
                    
                    # Images
                    if images:
                        product.images = [{"src": img.get('largeImage')} for img in images if img.get('largeImage')]
                    elif item.get('largeImage'):
                         product.images = [{"src": item.get('largeImage')}]

                    # Variant
                    variant = shopify.Variant()
                    variant.price = target_price
                    variant.sku = walmart_id
                    variant.inventory_management = "shopify"
                    
                    # If we found the AutoDS handle, use it directly
                    if AUTODS_HANDLE:
                        variant.fulfillment_service = AUTODS_HANDLE
                        variant.inventory_management = AUTODS_HANDLE
                    
                    variant.inventory_policy = "deny"
                    variant.inventory_quantity = 50 # Set to 50 for all warehouses/locations
                    # Store the affiliate URL in metafields for downstream use
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
                                product.reload()
                                variant = product.variants[0]
                                inventory_item_id = variant.inventory_item_id
                                
                                # Connect & Set AutoDS
                                shopify.InventoryLevel.connect(location_id=AUTODS_LOCATION_ID, inventory_item_id=inventory_item_id)
                                shopify.InventoryLevel.set(location_id=AUTODS_LOCATION_ID, inventory_item_id=inventory_item_id, available=50)
                                
                                # Disconnect others
                                levels = shopify.InventoryLevel.find(inventory_item_ids=inventory_item_id)
                                for level in levels:
                                    if level.location_id != AUTODS_LOCATION_ID:
                                        shopify.InventoryLevel.delete(inventory_item_id=inventory_item_id, location_id=level.location_id)
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
                    
    print(f"\n✨ Wave 2 Complete! Total Best Sellers Imported: {total_imported}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Import Walmart Best Sellers")
    parser.add_argument("--category", type=str, help="Specific category to import (e.g., 'Electronics')")
    args = parser.parse_args()
    
    import_wave2(target_category=args.category)
