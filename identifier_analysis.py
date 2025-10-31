#!/usr/bin/env python3
"""
Explore UPC/GTIN and product identifier fields in Walmart API
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from walmart_api import WalmartAPIClient

def analyze_product_identifiers():
    """Analyze UPC, GTIN and other product identifiers"""
    print("🔍 WALMART API PRODUCT IDENTIFIERS ANALYSIS")
    print("=" * 60)
    
    client = WalmartAPIClient()
    
    # Get a larger sample to analyze identifier patterns
    result = client.get_products(count=25)
    
    if not result['success']:
        print(f"❌ Failed: {result['error']}")
        return
    
    items = result['data']['items']
    print(f"📊 Analyzing {len(items)} products for identifier fields...")
    
    # Track identifier fields
    upc_count = 0
    gtin_count = 0
    item_id_count = 0
    model_number_count = 0
    
    identifier_examples = {
        'upc': [],
        'gtin': [],
        'itemId': [],
        'modelNumber': []
    }
    
    print(f"\n🏷️  PRODUCT IDENTIFIER ANALYSIS")
    print("=" * 50)
    
    for i, item in enumerate(items, 1):
        print(f"\n📦 PRODUCT {i}:")
        print(f"   Name: {item.get('name', 'N/A')[:50]}...")
        
        # Check for UPC
        if 'upc' in item and item['upc']:
            upc = item['upc']
            upc_count += 1
            if len(identifier_examples['upc']) < 5:
                identifier_examples['upc'].append(upc)
            print(f"   📊 UPC: {upc} (Length: {len(upc)})")
        else:
            print(f"   📊 UPC: Not available")
        
        # Check for GTIN (might be separate field)
        if 'gtin' in item and item['gtin']:
            gtin = item['gtin']
            gtin_count += 1
            if len(identifier_examples['gtin']) < 5:
                identifier_examples['gtin'].append(gtin)
            print(f"   🏷️  GTIN: {gtin}")
        else:
            print(f"   🏷️  GTIN: Not found as separate field")
        
        # Item ID (always present)
        item_id = item.get('itemId', 'N/A')
        item_id_count += 1
        if len(identifier_examples['itemId']) < 5:
            identifier_examples['itemId'].append(str(item_id))
        print(f"   🆔 Item ID: {item_id}")
        
        # Model Number (sometimes present)
        if 'modelNumber' in item and item['modelNumber']:
            model_num = item['modelNumber']
            model_number_count += 1
            if len(identifier_examples['modelNumber']) < 5:
                identifier_examples['modelNumber'].append(model_num)
            print(f"   🔧 Model Number: {model_num}")
        else:
            print(f"   🔧 Model Number: Not available")
    
    # Summary statistics
    print(f"\n📈 IDENTIFIER AVAILABILITY SUMMARY")
    print("=" * 50)
    print(f"📊 UPC Field:")
    print(f"   Present in: {upc_count}/{len(items)} products ({upc_count/len(items)*100:.1f}%)")
    
    print(f"🏷️  GTIN Field:")
    print(f"   Present in: {gtin_count}/{len(items)} products ({gtin_count/len(items)*100:.1f}%)")
    
    print(f"🆔 Item ID Field:")
    print(f"   Present in: {item_id_count}/{len(items)} products (100%)")
    
    print(f"🔧 Model Number Field:")
    print(f"   Present in: {model_number_count}/{len(items)} products ({model_number_count/len(items)*100:.1f}%)")
    
    # Show examples
    print(f"\n📋 IDENTIFIER FORMAT EXAMPLES")
    print("=" * 50)
    
    if identifier_examples['upc']:
        print(f"📊 UPC Examples:")
        for upc in identifier_examples['upc']:
            upc_len = len(upc)
            upc_type = "UPC-A (12 digits)" if upc_len == 12 else f"Length: {upc_len} digits"
            print(f"   • {upc} ({upc_type})")
    
    if identifier_examples['gtin']:
        print(f"🏷️  GTIN Examples:")
        for gtin in identifier_examples['gtin']:
            print(f"   • {gtin}")
    
    if identifier_examples['itemId']:
        print(f"🆔 Item ID Examples:")
        for item_id in identifier_examples['itemId'][:3]:
            print(f"   • {item_id}")
    
    if identifier_examples['modelNumber']:
        print(f"🔧 Model Number Examples:")
        for model in identifier_examples['modelNumber']:
            print(f"   • {model}")
    
    # UPC/GTIN Analysis
    print(f"\n🔍 UPC/GTIN RELATIONSHIP ANALYSIS")
    print("=" * 50)
    print("📊 Key Findings:")
    if upc_count > 0:
        print(f"   ✅ UPC field is available in {upc_count/len(items)*100:.1f}% of products")
        print(f"   📏 UPC format: Standard barcode identifiers")
    else:
        print(f"   ❌ No UPC fields found in sample")
    
    if gtin_count > 0:
        print(f"   ✅ GTIN field is available as separate field")
    else:
        print(f"   ⚠️  No separate GTIN field found")
        print(f"   💡 UPC IS a type of GTIN (UPC-A = 12-digit GTIN)")
        print(f"   💡 The 'upc' field likely contains GTIN-compatible identifiers")
    
    print(f"\n📚 GTIN/UPC REFERENCE:")
    print(f"   • UPC-A (12 digits) = GTIN-12")
    print(f"   • UPC-E (8 digits) = GTIN-8") 
    print(f"   • EAN-13 (13 digits) = GTIN-13")
    print(f"   • EAN-14 (14 digits) = GTIN-14")
    print(f"   • Walmart's 'upc' field likely contains GTIN-12 (UPC-A) codes")

if __name__ == '__main__':
    analyze_product_identifiers()