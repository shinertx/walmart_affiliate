import os
import time
from pathlib import Path
import sys

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from dotenv import load_dotenv
from src.walmart_api import WalmartAPIClient

load_dotenv()

"""
Simple sample script:
- Searches Walmart for a given query
- Prints item name + affiliate link built from productUrl/itemId
Usage:
    python generate_affiliate_links_sample.py [query]
Defaults to query="ps5" if not provided.
"""

def main():
    query = sys.argv[1] if len(sys.argv) > 1 else "ps5"
    client = WalmartAPIClient()

    print(f"Searching Walmart for: {query}")
    res = client.search(query, numItems=25)
    if not res.get('success'):
        print("Search failed:", res.get('error'))
        return

    items = res['data'].get('items', [])
    if not items:
        print("No items found.")
        return

    print(f"Found {len(items)} items. Showing up to 25 with affiliate links:")
    for item in items[:25]:
        name = item.get('name')
        link = client.generate_affiliate_link(item)
        item_id = item.get('itemId')
        print(f"- {name} (itemId: {item_id})")
        print(f"  link: {link}")
        time.sleep(0.1)

if __name__ == "__main__":
    main()
