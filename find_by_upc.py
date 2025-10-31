#!/usr/bin/env python3
import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent / 'src'))
from walmart_api import WalmartAPIClient

def main():
    if len(sys.argv) < 2:
        print("Usage: find_by_upc.py <upc> [brand] [postal_code]")
        sys.exit(1)
    upc = sys.argv[1]
    brand = sys.argv[2] if len(sys.argv) > 2 else None
    postal = sys.argv[3] if len(sys.argv) > 3 else None

    api = WalmartAPIClient()

    # Try brand-restricted search first (up to 400 items)
    result = api.get_products(count=400, brand=brand) if brand else api.get_products(count=100)
    if not result.get('success'):
        print("API error:", result.get('error'))
        sys.exit(2)
    items = result['data'].get('items') or []
    match = next((it for it in items if it.get('upc') == upc), None)

    if not match:
        print("No exact UPC match found in returned items.")
        print(f"Checked {len(items)} items with brand={brand!r}.")
        sys.exit(3)

    # Optionally enrich by postal code
    if postal:
        enr = api.get_items_by_ids([match.get('itemId')], postal_code=postal)
        if enr.get('success') and enr['data'].get('items'):
            match = enr['data']['items'][0]

    print(json.dumps({
        'itemId': match.get('itemId'),
        'name': match.get('name'),
        'brandName': match.get('brandName'),
        'upc': match.get('upc'),
        'size': match.get('size'),
        'attributes': match.get('attributes'),
        'salePrice': match.get('salePrice'),
        'msrp': match.get('msrp'),
        'availableOnline': match.get('availableOnline'),
        'stock': match.get('stock')
    }, indent=2))

if __name__ == '__main__':
    main()
