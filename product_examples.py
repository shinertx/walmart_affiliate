#!/usr/bin/env python3
"""
Show real product examples from different categories
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from walmart_api import WalmartAPIClient

def show_product_examples():
    """Show examples of different product types"""
    print("🛍️  WALMART PRODUCT EXAMPLES")
    print("=" * 50)
    
    client = WalmartAPIClient()
    
    # Get several products to show variety
    result = client.get_products(count=10)
    
    if not result['success']:
        print(f"❌ Failed: {result['error']}")
        return
    
    items = result['data']['items']
    
    for i, item in enumerate(items[:5], 1):
        print(f"\n📦 PRODUCT {i}")
        print("-" * 30)
        print(f"🏷️  Name: {item.get('name', 'N/A')}")
        print(f"🏪 Brand: {item.get('brandName', 'N/A')}")
        
        price_info = f"${item.get('salePrice', 'N/A')}"
        if 'msrp' in item:
            price_info += f" (MSRP: ${item['msrp']})"
        print(f"💰 Price: {price_info}")
        
        print(f"🔗 Category: {item.get('categoryPath', 'N/A')}")
        print(f"⭐ Rating: {item.get('customerRating', 'N/A')} ({item.get('numReviews', 0)} reviews)")
        print(f"📦 Stock: {item.get('stock', 'N/A')}")
        print(f"🚚 Free Shipping: {item.get('freeShippingOver35Dollars', False)}")
        print(f"🏬 Marketplace: {item.get('marketplace', False)}")
        description = item.get('shortDescription', 'No description')
        print(f"📋 Description: {description[:100]}...")
        
        if 'attributes' in item and item['attributes']:
            print(f"🔧 Attributes: {item['attributes']}")
        
        print(f"🔗 Product URL: {item['productTrackingUrl'][:80]}...")

if __name__ == '__main__':
    show_product_examples()