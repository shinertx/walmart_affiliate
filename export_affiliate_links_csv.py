import os
import csv
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from dotenv import load_dotenv
from src.walmart_api import WalmartAPIClient

load_dotenv()

"""
Exports affiliate links for a search query to CSV.
Usage:
    python export_affiliate_links_csv.py [query] [outfile]
Defaults:
    query = "ps5"
    outfile = "affiliate_links.csv"
"""

def main():
    query = sys.argv[1] if len(sys.argv) > 1 else "ps5"
    outfile = sys.argv[2] if len(sys.argv) > 2 else "affiliate_links.csv"

    client = WalmartAPIClient()
    res = client.search(query, numItems=50)

    if not res.get('success'):
        print("Search failed:", res.get('error'))
        return 1

    items = res['data'].get('items', [])
    if not items:
        print("No items found.")
        return 0

    rows = []
    for item in items:
        name = item.get('name') or ''
        item_id = item.get('itemId')
        link = client.generate_affiliate_link(item) or ''
        rows.append({
            'name': name,
            'itemId': item_id,
            'affiliateLink': link
        })

    with open(outfile, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['name', 'itemId', 'affiliateLink'])
        w.writeheader()
        w.writerows(rows)

    print(f"Wrote {len(rows)} rows to {outfile}")
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
