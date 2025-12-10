import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

SHOP_URL = f"https://{os.getenv('SHOPIFY_STORE_URL')}"
ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")

headers = {
    "X-Shopify-Access-Token": ACCESS_TOKEN,
    "Content-Type": "application/json"
}

def get_fulfillment_services():
    url = f"{SHOP_URL}/admin/api/2024-01/fulfillment_services.json?scope=all"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get("fulfillment_services", [])
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return []

services = get_fulfillment_services()
print(json.dumps(services, indent=2))
