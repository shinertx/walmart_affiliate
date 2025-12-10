import os
import ssl
import certifi
from dotenv import load_dotenv
import shopify

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

if not SHOPIFY_STORE_URL or not SHOPIFY_ACCESS_TOKEN:
    print("Error: Shopify credentials missing.")
    exit(1)

# Initialize Shopify
session = shopify.Session(SHOPIFY_STORE_URL, API_VERSION, SHOPIFY_ACCESS_TOKEN)
shopify.ShopifyResource.activate_session(session)

try:
    count = shopify.Product.count()
    print(f"Total products in store: {count}")
except Exception as e:
    print(f"Error counting products: {e}")
