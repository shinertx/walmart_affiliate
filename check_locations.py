import os
import shopify
import ssl
import certifi
from dotenv import load_dotenv

load_dotenv()

# Fix SSL Context
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

locations = shopify.Location.find()
print("Locations found:")
for loc in locations:
    print(f"ID: {loc.id}, Name: {loc.name}, Active: {loc.active}")
