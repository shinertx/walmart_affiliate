#!/usr/bin/env python3
"""
Test the Shopify integration modules without making actual API calls
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from product_transformer import ProductTransformer


def test_product_transformer():
    """Test product transformation from Walmart to Shopify format"""
    transformer = ProductTransformer()
    
    # Sample Walmart product data
    walmart_product = {
        'itemId': 123456789,
        'name': 'Samsung Galaxy Buds Pro Wireless Earbuds',
        'shortDescription': 'Premium wireless earbuds with active noise cancellation',
        'longDescription': 'Experience premium sound quality with Samsung Galaxy Buds Pro featuring intelligent active noise cancellation',
        'salePrice': 149.99,
        'msrp': 199.99,
        'mediumImage': 'https://example.com/image.jpg',
        'categoryPath': 'Electronics/Audio/Headphones',
        'brandName': 'Samsung',
        'upc': '887276437378',
        'modelNumber': 'SM-R190',
        'availableOnline': True,
        'stock': 'Available',
        'features': [
            'Active noise cancellation',
            'IPX7 water resistance',
            'Up to 28 hours battery life with case'
        ],
        'productUrl': 'https://walmart.com/product/123456789',
        'freeShipping': True
    }
    
    print("🧪 Testing Product Transformer")
    print("=" * 60)
    
    # Test 1: Transform product
    print("\nTest 1: Transform Walmart product to Shopify format")
    try:
        shopify_product = transformer.transform_walmart_to_shopify(walmart_product)
        
        assert shopify_product['title'] == walmart_product['name']
        assert shopify_product['vendor'] == 'Samsung'
        assert shopify_product['product_type'] == 'Headphones'
        assert len(shopify_product['variants']) == 1
        assert shopify_product['variants'][0]['price'] == '149.99'
        assert shopify_product['variants'][0]['sku'] == '123456789'
        assert shopify_product['variants'][0]['barcode'] == '887276437378'
        assert len(shopify_product['images']) >= 1
        
        print("✅ Product transformation successful")
        print(f"   Title: {shopify_product['title']}")
        print(f"   Vendor: {shopify_product['vendor']}")
        print(f"   Product Type: {shopify_product['product_type']}")
        print(f"   Price: ${shopify_product['variants'][0]['price']}")
        print(f"   Tags: {shopify_product['tags']}")
    except Exception as e:
        print(f"❌ Product transformation failed: {str(e)}")
        return False
    
    # Test 2: Validate product
    print("\nTest 2: Product validation")
    try:
        is_valid = transformer.is_valid_product(walmart_product)
        assert is_valid == True
        print("✅ Product validation passed")
    except Exception as e:
        print(f"❌ Product validation failed: {str(e)}")
        return False
    
    # Test 3: Category filtering
    print("\nTest 3: Category filtering")
    try:
        matches_electronics = transformer.filter_by_category(walmart_product, ['Electronics'])
        matches_baby = transformer.filter_by_category(walmart_product, ['Baby'])
        
        assert matches_electronics == True
        assert matches_baby == False
        
        print("✅ Category filtering works correctly")
        print(f"   Matches 'Electronics': {matches_electronics}")
        print(f"   Matches 'Baby': {matches_baby}")
    except Exception as e:
        print(f"❌ Category filtering failed: {str(e)}")
        return False
    
    # Test 4: Walmart seller detection
    print("\nTest 4: Walmart seller detection")
    try:
        is_walmart = transformer.is_walmart_seller(walmart_product)
        assert is_walmart == True
        print("✅ Walmart seller detection works")
        
        # Test third-party product
        third_party_product = walmart_product.copy()
        third_party_product['marketplace'] = True
        is_walmart_third = transformer.is_walmart_seller(third_party_product)
        assert is_walmart_third == False
        print("✅ Third-party seller detection works")
    except Exception as e:
        print(f"❌ Seller detection failed: {str(e)}")
        return False
    
    # Test 5: Invalid product handling
    print("\nTest 5: Invalid product handling")
    try:
        invalid_product = {
            'itemId': 999,
            'name': 'Test Product',
            # Missing required fields like price, availableOnline
        }
        is_valid = transformer.is_valid_product(invalid_product)
        assert is_valid == False
        print("✅ Invalid product correctly rejected")
    except Exception as e:
        print(f"❌ Invalid product handling failed: {str(e)}")
        return False
    
    # Test 6: Long title truncation
    print("\nTest 6: Long title truncation")
    try:
        long_title_product = walmart_product.copy()
        long_title_product['name'] = 'A' * 300  # 300 character title
        
        shopify_product = transformer.transform_walmart_to_shopify(long_title_product)
        assert len(shopify_product['title']) <= 255
        print(f"✅ Long title truncated correctly ({len(shopify_product['title'])} chars)")
    except Exception as e:
        print(f"❌ Title truncation failed: {str(e)}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ All transformer tests passed!")
    return True


def test_title_handling():
    """Test title handling in product transformation"""
    transformer = ProductTransformer()
    
    print("\n🧪 Testing Title Handling")
    print("=" * 60)
    
    # Test with multiple spaces
    product1 = {
        'itemId': 1,
        'name': '  Multiple   Spaces  ',
        'salePrice': 10,
        'availableOnline': True
    }
    result1 = transformer.transform_walmart_to_shopify(product1)
    assert result1['title'] == 'Multiple Spaces'
    print(f"✅ Multiple spaces handled correctly")
    
    # Test with very long title
    product2 = {
        'itemId': 2,
        'name': 'A' * 300,
        'salePrice': 10,
        'availableOnline': True
    }
    result2 = transformer.transform_walmart_to_shopify(product2)
    assert len(result2['title']) <= 255
    print(f"✅ Long title truncated to {len(result2['title'])} chars")
    
    # Test with empty title
    product3 = {
        'itemId': 3,
        'name': '',
        'salePrice': 10,
        'availableOnline': True
    }
    result3 = transformer.transform_walmart_to_shopify(product3)
    assert result3['title'] == 'Untitled Product'
    print(f"✅ Empty title handled correctly")
    
    return True


def test_tag_generation():
    """Test tag generation through product transformation"""
    transformer = ProductTransformer()
    
    print("\n🧪 Testing Tag Generation")
    print("=" * 60)
    
    product = {
        'itemId': 123,
        'name': 'Test Product',
        'salePrice': 10,
        'availableOnline': True,
        'brandName': 'Samsung',
        'categoryPath': 'Electronics/Audio/Headphones',
        'freeShipping': True,
        'specialOffer': 'Clearance'
    }
    
    result = transformer.transform_walmart_to_shopify(product)
    tags = result['tags']
    tags_list = [t.strip() for t in tags.split(',')]
    
    assert 'Samsung' in tags_list
    assert 'Electronics' in tags_list
    assert 'Available Online' in tags_list
    assert 'Free Shipping' in tags_list
    assert 'Special Offer' in tags_list
    assert 'Walmart' in tags_list
    
    print(f"✅ Tags generated: {tags}")
    return True


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("🚀 SHOPIFY INTEGRATION UNIT TESTS")
    print("=" * 60)
    
    all_passed = True
    
    try:
        if not test_product_transformer():
            all_passed = False
        
        if not test_title_handling():
            all_passed = False
        
        if not test_tag_generation():
            all_passed = False
        
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("=" * 60)
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print("=" * 60)
        return 1


if __name__ == '__main__':
    sys.exit(main())
