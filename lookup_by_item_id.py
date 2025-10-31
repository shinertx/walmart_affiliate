#!/usr/bin/env python3
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))
from walmart_api import WalmartAPIClient

def main():
    if len(sys.argv) < 2:
        print("Usage: lookup_by_item_id.py <item_id> [postal_code]")
        sys.exit(1)
    try:
        item_id = int(sys.argv[1])
    except ValueError:
        print("item_id must be an integer")
        sys.exit(1)
    postal = sys.argv[2] if len(sys.argv) > 2 else None

    api = WalmartAPIClient()
    resp = api.get_items_by_ids([item_id], postal_code=postal)
    if not resp.get('success'):
        print("Error:", resp.get('error'))
        sys.exit(2)

    items = resp['data'].get('items') or []
    if not items:
        print("No items returned")
        sys.exit(3)

    item = items[0]
    out = {
        'itemId': item.get('itemId'),
        'name': item.get('name'),
        'upc': item.get('upc'),
        'brandName': item.get('brandName'),
        'modelNumber': item.get('modelNumber'),
        'salePrice': item.get('salePrice'),
        'msrp': item.get('msrp'),
        'availableOnline': item.get('availableOnline'),
        'stock': item.get('stock'),
        'size': item.get('size'),
        'attributes': item.get('attributes'),
        'variantInfo': {
            'color': item.get('color'),
            'size': item.get('size')
        }
    }
    print(json.dumps(out, indent=2))

if __name__ == '__main__':
    main()
