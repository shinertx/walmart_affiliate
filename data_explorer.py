#!/usr/bin/env python3
"""
Walmart API Data Explorer

This script shows you all the fields and data structure returned by the Walmart API
"""

import sys
import json
from pathlib import Path
from pprint import pprint

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from walmart_api import WalmartAPIClient

def analyze_product_data():
    """Analyze and display the structure of product data returned by Walmart API"""
    print("🔍 WALMART API DATA EXPLORER")
    print("=" * 50)
    
    try:
        # Create API client
        client = WalmartAPIClient()
        
        print("📡 Fetching sample products to analyze data structure...")
        
        # Get a small sample to analyze
        result = client.get_products(count=3)
        
        if not result['success']:
            print(f"❌ API call failed: {result['error']}")
            return
        
        data = result['data']
        items = data.get('items', [])
        
        if not items:
            print("❌ No items returned")
            return
            
        print(f"✅ Successfully retrieved {len(items)} items")
        print("\n" + "=" * 60)
        print("📋 RESPONSE STRUCTURE")
        print("=" * 60)
        
        # Show top-level response structure
        print("\n🏗️  TOP-LEVEL RESPONSE FIELDS:")
        for key, value in data.items():
            if key != 'items':  # We'll analyze items separately
                value_type = type(value).__name__
                if isinstance(value, str):
                    display_value = f'"{value[:50]}..."' if len(value) > 50 else f'"{value}"'
                else:
                    display_value = str(value)
                print(f"   📄 {key}: ({value_type}) {display_value}")
        
        print(f"\n📦 ITEMS ARRAY: Contains {len(items)} product objects")
        
        # Analyze the first product in detail
        if items:
            first_item = items[0]
            print("\n" + "=" * 60)
            print("🛍️  PRODUCT OBJECT STRUCTURE (First Item)")
            print("=" * 60)
            
            # Categorize fields
            basic_fields = {}
            pricing_fields = {}
            image_fields = {}
            shipping_fields = {}
            attribute_fields = {}
            other_fields = {}
            
            for key, value in first_item.items():
                if key in ['itemId', 'parentItemId', 'name', 'shortDescription', 'longDescription', 'brandName', 'upc', 'modelNumber']:
                    basic_fields[key] = value
                elif key in ['msrp', 'salePrice', 'bestMarketplacePrice']:
                    pricing_fields[key] = value
                elif 'image' in key.lower() or key in ['thumbnailImage', 'mediumImage', 'largeImage']:
                    image_fields[key] = value
                elif 'ship' in key.lower() or key in ['standardShipRate', 'freeShipToStore', 'shipToStore', 'freeShippingOver35Dollars']:
                    shipping_fields[key] = value
                elif key in ['attributes', 'color', 'size']:
                    attribute_fields[key] = value
                else:
                    other_fields[key] = value
            
            # Display categorized fields
            def display_fields(title, fields, icon):
                if fields:
                    print(f"\n{icon} {title}:")
                    for key, value in fields.items():
                        value_type = type(value).__name__
                        if isinstance(value, str):
                            display_value = f'"{value[:60]}..."' if len(value) > 60 else f'"{value}"'
                        elif isinstance(value, dict):
                            display_value = f"{{...}} ({len(value)} keys)"
                        elif isinstance(value, list):
                            display_value = f"[...] ({len(value)} items)"
                        else:
                            display_value = str(value)
                        print(f"   • {key}: ({value_type}) {display_value}")
            
            display_fields("BASIC INFO", basic_fields, "🏷️")
            display_fields("PRICING", pricing_fields, "💰")
            display_fields("IMAGES", image_fields, "🖼️")
            display_fields("SHIPPING", shipping_fields, "📦")
            display_fields("ATTRIBUTES", attribute_fields, "🔧")
            display_fields("OTHER FIELDS", other_fields, "📋")
            
            # Show complete first item as JSON
            print("\n" + "=" * 60)
            print("📄 COMPLETE FIRST ITEM (JSON FORMAT)")
            print("=" * 60)
            print(json.dumps(first_item, indent=2)[:2000] + "..." if len(json.dumps(first_item, indent=2)) > 2000 else json.dumps(first_item, indent=2))
            
            # Field count summary
            all_fields = list(first_item.keys())
            print(f"\n📊 FIELD SUMMARY:")
            print(f"   Total Fields: {len(all_fields)}")
            print(f"   Basic Info: {len(basic_fields)}")
            print(f"   Pricing: {len(pricing_fields)}")
            print(f"   Images: {len(image_fields)}")
            print(f"   Shipping: {len(shipping_fields)}")
            print(f"   Attributes: {len(attribute_fields)}")
            print(f"   Other: {len(other_fields)}")
            
            print(f"\n🗂️  ALL AVAILABLE FIELDS:")
            for i, field in enumerate(sorted(all_fields), 1):
                print(f"   {i:2d}. {field}")
        
        # Show sample of different products to see variation
        if len(items) > 1:
            print("\n" + "=" * 60)
            print("🔄 FIELD VARIATION ACROSS PRODUCTS")
            print("=" * 60)
            
            all_unique_fields = set()
            for item in items:
                all_unique_fields.update(item.keys())
            
            print(f"📊 Across {len(items)} products:")
            print(f"   Total unique fields found: {len(all_unique_fields)}")
            
            # Check which fields are present in all vs some products
            field_presence = {}
            for field in all_unique_fields:
                count = sum(1 for item in items if field in item)
                field_presence[field] = count
            
            always_present = [f for f, c in field_presence.items() if c == len(items)]
            sometimes_present = [f for f, c in field_presence.items() if c < len(items)]
            
            print(f"\n✅ Fields present in ALL products ({len(always_present)}):")
            for field in sorted(always_present):
                print(f"   • {field}")
                
            if sometimes_present:
                print(f"\n⚠️  Fields present in SOME products ({len(sometimes_present)}):")
                for field in sorted(sometimes_present):
                    count = field_presence[field]
                    print(f"   • {field} ({count}/{len(items)} products)")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return

if __name__ == '__main__':
    analyze_product_data()