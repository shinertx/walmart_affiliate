import os
import requests
import json
import time
from dotenv import load_dotenv

load_dotenv()

SHOP_URL = f"https://{os.getenv('SHOPIFY_STORE_URL')}"
ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")

headers = {
    "X-Shopify-Access-Token": ACCESS_TOKEN,
    "Content-Type": "application/json"
}

def get_product_by_title(title):
    url = f"{SHOP_URL}/admin/api/2024-01/products.json"
    params = {"title": title}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        products = response.json().get("products", [])
        if products:
            return products[0]
    return None

def get_locations():
    url = f"{SHOP_URL}/admin/api/2024-01/locations.json"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return {loc['id']: loc['name'] for loc in response.json().get("locations", [])}
    return {}

def check_items():
    titles = [
        "Bounce Anna Sports Bra In White",
        "Ripley Pajama Set In Pink Plaid",
        "Turnt Crossover Bodysuit In Black",
        "Hooded Hacci Sleep Set With Jogger In Mesa Sunburst",
        "Womens Two Piece Cotton Pajamas Hearts Black",
        "Women's V-Neck Short Sleeve Jogger Set"
    ]

    locations_map = get_locations()

    print(f"{'PRODUCT TITLE':<50} | {'STATUS':<10} | {'VARIANT':<20} | {'SERVICE':<20} | {'STOCK'}")
    print("-" * 130)

    for title in titles:
        product = get_product_by_title(title)
        if not product:
            print(f"{title:<50} | NOT FOUND")
            continue

        status = product['status']
        
        for variant in product['variants']:
            v_title = variant['title']
            service = variant['fulfillment_service']
            inv_item_id = variant['inventory_item_id']
            
            # Get inventory levels
            inv_url = f"{SHOP_URL}/admin/api/2024-01/inventory_levels.json?inventory_item_ids={inv_item_id}"
            try:
                inv_res = requests.get(inv_url, headers=headers)
                stock_info = []
                if inv_res.status_code == 200:
                    levels = inv_res.json().get("inventory_levels", [])
                    for level in levels:
                        loc_name = locations_map.get(level['location_id'], level['location_id'])
                        qty = level['available']
                        stock_info.append(f"{loc_name}: {qty}")
            except:
                stock_info = ["Error fetching stock"]
            
            stock_str = ", ".join(stock_info)
            print(f"{title[:48]:<50} | {status:<10} | {v_title[:18]:<20} | {service:<20} | {stock_str}")
            time.sleep(0.5)

if __name__ == "__main__":
    check_items()
