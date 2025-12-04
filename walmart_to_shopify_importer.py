"""
Walmart to Shopify Product Importer

This script imports products from Walmart to Shopify, focusing on:
- Top 25,000 products
- Electronics and Baby categories
- Products available in stores (not third-party sellers)
"""
import sys
import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from walmart_api import WalmartAPIClient
from shopify_client import ShopifyAPIClient
from product_transformer import ProductTransformer


class WalmartShopifyImporter:
    """
    Import Walmart products to Shopify with filtering and transformation
    """
    
    def __init__(self, target_count: int = 25000, categories: Optional[List[str]] = None):
        """
        Initialize the importer
        
        Args:
            target_count: Number of products to import (default: 25,000)
            categories: List of category filters (e.g., ['Electronics', 'Baby'])
        """
        self.walmart_client = WalmartAPIClient()
        self.shopify_client = ShopifyAPIClient()
        self.transformer = ProductTransformer()
        
        self.target_count = target_count
        self.categories = categories or ['Electronics', 'Baby']
        
        # Statistics
        self.stats = {
            'total_fetched': 0,
            'filtered_out': 0,
            'validation_failed': 0,
            'third_party_filtered': 0,
            'category_filtered': 0,
            'imported': 0,
            'failed': 0,
            'skipped_duplicates': 0
        }
        
        # Setup logging
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging configuration"""
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f'import_{timestamp}.log'
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Starting import - Target: {self.target_count} products")
        self.logger.info(f"Categories: {', '.join(self.categories)}")
    
    def test_connections(self) -> bool:
        """Test connections to both Walmart and Shopify APIs"""
        self.logger.info("Testing API connections...")
        
        # Test Walmart API
        self.logger.info("Testing Walmart API connection...")
        if not self.walmart_client.test_connection():
            self.logger.error("Walmart API connection failed")
            return False
        self.logger.info("✅ Walmart API connection successful")
        
        # Test Shopify API
        self.logger.info("Testing Shopify API connection...")
        if not self.shopify_client.test_connection():
            self.logger.error("Shopify API connection failed")
            return False
        self.logger.info("✅ Shopify API connection successful")
        
        return True
    
    def fetch_walmart_products(self, batch_size: int = 100) -> List[Dict]:
        """
        Fetch products from Walmart API in batches
        
        Args:
            batch_size: Number of products to fetch per API call
            
        Returns:
            List of Walmart product dictionaries
        """
        all_products = []
        batches_needed = (self.target_count + batch_size - 1) // batch_size
        
        self.logger.info(f"Fetching {self.target_count} products in {batches_needed} batches")
        
        for batch_num in range(batches_needed):
            current_count = len(all_products)
            if current_count >= self.target_count:
                break
            
            remaining = self.target_count - current_count
            current_batch_size = min(batch_size, remaining)
            
            self.logger.info(f"Fetching batch {batch_num + 1}/{batches_needed} ({current_batch_size} items)...")
            
            try:
                # Fetch products from Walmart
                result = self.walmart_client.get_products(count=current_batch_size)
                
                if result['success']:
                    items = result['data'].get('items', [])
                    self.logger.info(f"Retrieved {len(items)} items from Walmart API")
                    all_products.extend(items)
                    self.stats['total_fetched'] += len(items)
                else:
                    self.logger.error(f"Failed to fetch batch: {result.get('error')}")
                
                # Add delay between requests
                if batch_num < batches_needed - 1:
                    time.sleep(2)
                    
            except Exception as e:
                self.logger.error(f"Error fetching batch: {str(e)}")
        
        self.logger.info(f"Total products fetched: {len(all_products)}")
        return all_products
    
    def filter_products(self, products: List[Dict]) -> List[Dict]:
        """
        Filter products based on criteria:
        - Must be in specified categories (Electronics, Baby)
        - Must be sold by Walmart (not third-party)
        - Must be valid for import
        
        Args:
            products: List of Walmart products
            
        Returns:
            List of filtered products
        """
        filtered = []
        
        for product in products:
            # Check if product is valid
            if not self.transformer.is_valid_product(product):
                self.stats['validation_failed'] += 1
                continue
            
            # Check category
            if not self.transformer.filter_by_category(product, self.categories):
                self.stats['category_filtered'] += 1
                continue
            
            # Check if sold by Walmart (not third-party)
            if not self.transformer.is_walmart_seller(product):
                self.stats['third_party_filtered'] += 1
                continue
            
            filtered.append(product)
        
        self.logger.info(f"Products after filtering: {len(filtered)}")
        self.logger.info(f"  - Validation failed: {self.stats['validation_failed']}")
        self.logger.info(f"  - Category filtered: {self.stats['category_filtered']}")
        self.logger.info(f"  - Third-party filtered: {self.stats['third_party_filtered']}")
        
        return filtered
    
    def import_to_shopify(self, products: List[Dict], batch_delay: float = 0.5) -> None:
        """
        Import products to Shopify
        
        Args:
            products: List of filtered Walmart products
            batch_delay: Delay between product imports (seconds)
        """
        total = len(products)
        self.logger.info(f"Starting import of {total} products to Shopify...")
        
        for idx, walmart_product in enumerate(products, 1):
            try:
                item_id = walmart_product.get('itemId')
                product_name = walmart_product.get('name', 'Unknown')
                
                self.logger.info(f"[{idx}/{total}] Importing: {product_name[:50]}...")
                
                # Transform product data
                shopify_product = self.transformer.transform_walmart_to_shopify(walmart_product)
                
                # Check if product already exists (by SKU)
                existing = self.shopify_client.search_product_by_sku(str(item_id))
                if existing:
                    self.logger.info(f"  Product already exists (SKU: {item_id}), skipping...")
                    self.stats['skipped_duplicates'] += 1
                    continue
                
                # Create product in Shopify
                result = self.shopify_client.create_product(shopify_product)
                
                if result['success']:
                    shopify_id = result['data']['product']['id']
                    self.logger.info(f"  ✅ Created product in Shopify (ID: {shopify_id})")
                    self.stats['imported'] += 1
                else:
                    self.logger.error(f"  ❌ Failed to create product: {result.get('error')}")
                    self.stats['failed'] += 1
                
                # Progress update every 100 products
                if idx % 100 == 0:
                    self.print_progress()
                
                # Rate limiting delay
                time.sleep(batch_delay)
                
            except Exception as e:
                self.logger.error(f"Error importing product: {str(e)}")
                self.stats['failed'] += 1
        
        self.logger.info("Import completed!")
        self.print_final_stats()
    
    def print_progress(self):
        """Print current progress"""
        self.logger.info("=" * 60)
        self.logger.info("PROGRESS UPDATE:")
        self.logger.info(f"  Imported: {self.stats['imported']}")
        self.logger.info(f"  Failed: {self.stats['failed']}")
        self.logger.info(f"  Skipped (duplicates): {self.stats['skipped_duplicates']}")
        self.logger.info("=" * 60)
    
    def print_final_stats(self):
        """Print final statistics"""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("IMPORT STATISTICS:")
        self.logger.info("=" * 60)
        self.logger.info(f"Total products fetched from Walmart: {self.stats['total_fetched']}")
        self.logger.info(f"Filtered out (validation): {self.stats['validation_failed']}")
        self.logger.info(f"Filtered out (category): {self.stats['category_filtered']}")
        self.logger.info(f"Filtered out (third-party): {self.stats['third_party_filtered']}")
        self.logger.info(f"Successfully imported: {self.stats['imported']}")
        self.logger.info(f"Failed imports: {self.stats['failed']}")
        self.logger.info(f"Skipped (duplicates): {self.stats['skipped_duplicates']}")
        self.logger.info("=" * 60)
        
        # Save statistics to file
        self.save_stats()
    
    def save_stats(self):
        """Save import statistics to JSON file"""
        stats_dir = Path('import_stats')
        stats_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stats_file = stats_dir / f'import_stats_{timestamp}.json'
        
        stats_data = {
            'timestamp': datetime.now().isoformat(),
            'target_count': self.target_count,
            'categories': self.categories,
            'statistics': self.stats
        }
        
        with open(stats_file, 'w') as f:
            json.dump(stats_data, f, indent=2)
        
        self.logger.info(f"Statistics saved to: {stats_file}")
    
    def run_import(self):
        """Run the complete import process"""
        self.logger.info("🛒 Starting Walmart to Shopify Import")
        self.logger.info("=" * 60)
        
        # Test connections
        if not self.test_connections():
            self.logger.error("Connection test failed. Aborting import.")
            return False
        
        # Fetch products from Walmart
        self.logger.info("\n📦 Step 1: Fetching products from Walmart...")
        products = self.fetch_walmart_products(batch_size=100)
        
        if not products:
            self.logger.error("No products fetched from Walmart. Aborting.")
            return False
        
        # Filter products
        self.logger.info("\n🔍 Step 2: Filtering products...")
        filtered_products = self.filter_products(products)
        
        if not filtered_products:
            self.logger.error("No products passed filtering. Aborting.")
            return False
        
        # Limit to target count
        if len(filtered_products) > self.target_count:
            filtered_products = filtered_products[:self.target_count]
            self.logger.info(f"Limited to target count: {self.target_count} products")
        
        # Import to Shopify
        self.logger.info(f"\n📤 Step 3: Importing {len(filtered_products)} products to Shopify...")
        self.import_to_shopify(filtered_products)
        
        return True


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Import Walmart products to Shopify'
    )
    parser.add_argument(
        '--count',
        type=int,
        default=25000,
        help='Number of products to import (default: 25000)'
    )
    parser.add_argument(
        '--categories',
        type=str,
        default='Electronics,Baby',
        help='Comma-separated list of categories (default: Electronics,Baby)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Batch size for Walmart API requests (default: 100)'
    )
    parser.add_argument(
        '--test-only',
        action='store_true',
        help='Only test connections, do not import'
    )
    
    args = parser.parse_args()
    
    # Parse categories
    categories = [c.strip() for c in args.categories.split(',')]
    
    # Create importer
    importer = WalmartShopifyImporter(
        target_count=args.count,
        categories=categories
    )
    
    # Test only mode
    if args.test_only:
        print("Running connection test only...")
        if importer.test_connections():
            print("✅ All connections successful!")
            return 0
        else:
            print("❌ Connection test failed")
            return 1
    
    # Run full import
    try:
        success = importer.run_import()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n⏹️ Import interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Import failed with error: {str(e)}")
        logging.exception("Import failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
