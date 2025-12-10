import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

SHOPIFY_STORE_URL = os.getenv('SHOPIFY_STORE_URL')
SHOPIFY_ACCESS_TOKEN = os.getenv('SHOPIFY_ACCESS_TOKEN')

HEADERS = {
    "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN,
    "Content-Type": "application/json"
}

# Variant ID from previous context: 42946998009991
# Inventory Item ID: 45048533778567
VARIANT_ID = 42946998009991
INVENTORY_ITEM_ID = 45048533778567

LOCATIONS = {
    "123 Cedar Street": 75262066823,
    "AutoDS prod-wwbybglb": 80020111495
}

import time

def set_inventory(inventory_item_id, location_id, quantity):
    url = f"https://{SHOPIFY_STORE_URL}/admin/api/2024-01/inventory_levels/set.json"
    payload = {
        "location_id": location_id,
        "inventory_item_id": inventory_item_id,
        "available": quantity
    }
    while True:
        response = requests.post(url, headers=HEADERS, json=payload)
        if response.status_code == 429:
            print("Rate limit hit, sleeping 2s...")
            time.sleep(2)
            continue
        return response.json()

def get_inventory_levels(inventory_item_id):
    url = f"https://{SHOPIFY_STORE_URL}/admin/api/2024-01/inventory_levels.json?inventory_item_ids={inventory_item_id}"
    while True:
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 429:
            print("Rate limit hit, sleeping 2s...")
            time.sleep(2)
            continue
        return response.json()

print(f"Checking inventory for item {INVENTORY_ITEM_ID}...")
print(get_inventory_levels(INVENTORY_ITEM_ID))

print("\nSetting inventory to 50 at 123 Cedar Street...")
res1 = set_inventory(INVENTORY_ITEM_ID, LOCATIONS["123 Cedar Street"], 50)
print(res1)

print("\nSetting inventory to 50 at AutoDS prod-wwbybglb...")
res2 = set_inventory(INVENTORY_ITEM_ID, LOCATIONS["AutoDS prod-wwbybglb"], 50)
print(res2)

print("\nFinal check...")
print(get_inventory_levels(INVENTORY_ITEM_ID))
