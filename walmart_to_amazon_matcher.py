#!/usr/bin/env python3
"""
Walmart to Amazon Product Matching System
This demonstrates how to connect Walmart products to Amazon equivalents
"""

import sys
import time
import requests
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import urllib.parse
import hashlib

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from walmart_api import WalmartAPIClient

class WalmartToAmazonMatcher:
    """
    Match Walmart products to Amazon equivalents for shipping comparison
    """
    
    def __init__(self):
        self.walmart_client = WalmartAPIClient()
        # Note: You'd need Amazon Product Advertising API credentials for full implementation
        # For demo purposes, we'll simulate the matching process
    
    def get_walmart_products(self, count: int = 10) -> List[Dict]:
        """Get Walmart products for matching"""
        result = self.walmart_client.get_products(count=count)
        if result['success']:
            return result['data']['items']
        return []
    
    def extract_matching_data(self, walmart_product: Dict) -> Dict:
        """Extract key data points for matching"""
        return {
            'walmart_item_id': walmart_product.get('itemId'),
            'upc': walmart_product.get('upc'),
            'name': walmart_product.get('name', ''),
            'brand': walmart_product.get('brandName', ''),
            'model_number': walmart_product.get('modelNumber'),
            'price': walmart_product.get('salePrice'),
            'walmart_url': walmart_product.get('productTrackingUrl', ''),
            'category': walmart_product.get('categoryPath', ''),
            'description': walmart_product.get('shortDescription', '')
        }
    
    def simulate_amazon_lookup_by_upc(self, upc: str) -> Optional[Dict]:
        """
        Simulate Amazon UPC lookup
        In real implementation, you'd use Amazon Product Advertising API
        """
        if not upc or len(upc) != 12:
            return None
            
        # Simulate API call delay
        time.sleep(0.1)
        
        # Simulate different success rates based on UPC patterns
        # This is just for demonstration
        if upc.startswith('048238'):  # Generic/private label - lower match rate
            success_rate = 0.3
        elif upc.startswith('61895'):  # Another private label pattern
            success_rate = 0.2
        else:  # Brand name products - higher match rate
            success_rate = 0.85
            
        import random
        if random.random() < success_rate:
            # Simulate found Amazon product
            return {
                'amazon_asin': f'B0{hashlib.md5(upc.encode()).hexdigest()[:8].upper()}',
                'amazon_title': f'Amazon equivalent product for UPC {upc}',
                'amazon_price': round(random.uniform(5.0, 50.0), 2),
                'amazon_prime': random.choice([True, False]),
                'amazon_url': f'https://www.amazon.com/dp/B0{hashlib.md5(upc.encode()).hexdigest()[:8].upper()}',
                'match_method': 'UPC',
                'match_confidence': 0.95
            }
        return None
    
    def simulate_amazon_lookup_by_title_brand(self, title: str, brand: str) -> Optional[Dict]:
        """
        Simulate Amazon search by title and brand
        Real implementation would use Amazon's search API
        """
        if not title or len(title.strip()) < 5:
            return None
            
        # Simulate lower success rate for title matching
        import random
        if random.random() < 0.6:  # 60% success rate for title matching
            return {
                'amazon_asin': f'B0{hashlib.md5((title + brand).encode()).hexdigest()[:8].upper()}',
                'amazon_title': f'Similar: {title[:30]}...',
                'amazon_price': round(random.uniform(5.0, 50.0), 2),
                'amazon_prime': random.choice([True, False]),
                'amazon_url': f'https://www.amazon.com/s?k={urllib.parse.quote(title[:30])}',
                'match_method': 'Title+Brand',
                'match_confidence': 0.75
            }
        return None
    
    def match_product(self, walmart_product: Dict) -> Dict:
        """
        Attempt to match a Walmart product to Amazon
        Returns matching result with Amazon data if found
        """
        walmart_data = self.extract_matching_data(walmart_product)
        result = {
            'walmart': walmart_data,
            'amazon': None,
            'match_status': 'not_found',
            'match_method': None,
            'shipping_comparison': None
        }
        
        # Try UPC matching first (most reliable)
        if walmart_data['upc']:
            amazon_match = self.simulate_amazon_lookup_by_upc(walmart_data['upc'])
            if amazon_match:
                result['amazon'] = amazon_match
                result['match_status'] = 'found'
                result['match_method'] = 'UPC'
                result['shipping_comparison'] = self.compare_shipping(walmart_data, amazon_match)
                return result
        
        # Try title + brand matching
        amazon_match = self.simulate_amazon_lookup_by_title_brand(
            walmart_data['name'], 
            walmart_data['brand']
        )
        if amazon_match:
            result['amazon'] = amazon_match
            result['match_status'] = 'found'
            result['match_method'] = 'Title+Brand'
            result['shipping_comparison'] = self.compare_shipping(walmart_data, amazon_match)
            return result
        
        result['match_status'] = 'not_found'
        return result
    
    def compare_shipping(self, walmart_data: Dict, amazon_data: Dict) -> Dict:
        """Compare shipping options between Walmart and Amazon"""
        return {
            'walmart_price': walmart_data['price'],
            'amazon_price': amazon_data['amazon_price'],
            'price_difference': amazon_data['amazon_price'] - (walmart_data['price'] or 0),
            'amazon_prime_available': amazon_data['amazon_prime'],
            'recommendation': self.get_shipping_recommendation(walmart_data, amazon_data)
        }
    
    def get_shipping_recommendation(self, walmart_data: Dict, amazon_data: Dict) -> str:
        """Provide shipping recommendation"""
        walmart_price = walmart_data['price'] or 0
        amazon_price = amazon_data['amazon_price']
        
        if amazon_data['amazon_prime']:
            if amazon_price <= walmart_price * 1.1:  # Within 10%
                return "Amazon Prime recommended - fast shipping, similar price"
            else:
                return "Walmart cheaper - consider Walmart shipping"
        else:
            if walmart_price < amazon_price:
                return "Walmart recommended - better price"
            else:
                return "Amazon recommended - better value"
    
    def batch_match_products(self, count: int = 10) -> List[Dict]:
        """Match multiple Walmart products to Amazon"""
        print(f"🔍 Fetching {count} Walmart products...")
        walmart_products = self.get_walmart_products(count)
        
        if not walmart_products:
            print("❌ No Walmart products found")
            return []
        
        print(f"🔄 Matching {len(walmart_products)} products to Amazon...")
        matches = []
        
        for i, product in enumerate(walmart_products, 1):
            print(f"   Processing {i}/{len(walmart_products)}: {product.get('name', 'Unknown')[:40]}...")
            match_result = self.match_product(product)
            matches.append(match_result)
        
        return matches

def main():
    """Demonstrate Walmart to Amazon matching"""
    print("🛒➡️🟧 WALMART TO AMAZON PRODUCT MATCHING")
    print("=" * 60)
    print("This tool finds Amazon equivalents for Walmart products")
    print("to help you compare shipping options and prices.\n")
    
    matcher = WalmartToAmazonMatcher()
    
    # Match a batch of products
    matches = matcher.batch_match_products(count=8)
    
    # Display results
    print(f"\n📊 MATCHING RESULTS")
    print("=" * 60)
    
    found_count = sum(1 for m in matches if m['match_status'] == 'found')
    print(f"✅ Successfully matched: {found_count}/{len(matches)} products ({found_count/len(matches)*100:.1f}%)")
    
    print(f"\n🔍 DETAILED MATCHES:")
    print("-" * 60)
    
    for i, match in enumerate(matches, 1):
        walmart = match['walmart']
        amazon = match['amazon']
        
        print(f"\n{i}. 📦 {walmart['name'][:50]}...")
        print(f"   🏪 Walmart: ${walmart['price']} | UPC: {walmart['upc']}")
        
        if match['match_status'] == 'found':
            print(f"   🟧 Amazon: ${amazon['amazon_price']} | ASIN: {amazon['amazon_asin']}")
            print(f"   🔗 Match Method: {match['match_method']} (Confidence: {amazon['match_confidence']:.0%})")
            
            shipping = match['shipping_comparison']
            print(f"   📦 Shipping Rec: {shipping['recommendation']}")
            
            if amazon['amazon_prime']:
                print(f"   ⚡ Prime Available: Yes")
        else:
            print(f"   ❌ Amazon: No match found")
    
    # Summary statistics
    upc_matches = sum(1 for m in matches if m.get('match_method') == 'UPC')
    title_matches = sum(1 for m in matches if m.get('match_method') == 'Title+Brand')
    
    print(f"\n📈 MATCH METHOD BREAKDOWN:")
    print(f"   🏷️  UPC Matches: {upc_matches} ({upc_matches/len(matches)*100:.1f}%)")
    print(f"   📝 Title Matches: {title_matches} ({title_matches/len(matches)*100:.1f}%)")
    print(f"   ❌ No Matches: {len(matches) - found_count} ({(len(matches) - found_count)/len(matches)*100:.1f}%)")
    
    print(f"\n💡 BUSINESS OPPORTUNITIES:")
    print(f"   • Price arbitrage detection")
    print(f"   • Shipping cost comparison") 
    print(f"   • Prime vs Walmart+ recommendation")
    print(f"   • Multi-platform inventory management")

if __name__ == '__main__':
    main()