import shopify
import os
import ssl
import certifi
from dotenv import load_dotenv

load_dotenv()

# Fix SSL
ssl_context = ssl.create_default_context(cafile=certifi.where())
import urllib.request
original_urlopen = urllib.request.urlopen
def patched_urlopen(url, data=None, timeout=None, *, cafile=None, capath=None, cadefault=False, context=None):
    return original_urlopen(url, data, timeout, context=ssl_context)
urllib.request.urlopen = patched_urlopen

SHOPIFY_STORE_URL = os.getenv("SHOPIFY_STORE_URL")
SHOPIFY_ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")
API_VERSION = "2024-01"

session = shopify.Session(SHOPIFY_STORE_URL, API_VERSION, SHOPIFY_ACCESS_TOKEN)
shopify.ShopifyResource.activate_session(session)

location_id = 80020111495
try:
    location = shopify.Location.find(location_id)
    print(f"Location Name: {location.name}")
    print(f"Attributes: {location.attributes}")
except Exception as e:
    print(f"Error: {e}")

# Also list fulfillment services
print("\n--- Fulfillment Services ---")
services = shopify.FulfillmentService.find()
for s in services:
    print(f"Service: {s.name}, Handle: {s.handle}, Location ID: {s.location_id}")
print("----------------------------\n")
exit()
