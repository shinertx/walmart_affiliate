#!/usr/bin/env python3
"""
Walmart API Batch Testing Tool

This tool tests the Walmart Affiliate API to determine optimal batch sizes
for product retrieval and identify API limits.
"""

import sys
import argparse
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from batch_tester import BatchTester
from config import Config
import logging

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('walmart_api_test.log'),
            logging.StreamHandler()
        ]
    )

def print_banner():
    """Print welcome banner"""
    print("=" * 60)
    print("🛒 WALMART API BATCH TESTING TOOL")
    print("=" * 60)
    print("This tool tests different batch sizes to find optimal")
    print("throughput and API limits for Walmart's Affiliate API.")
    print("=" * 60)

def check_environment():
    """Check if environment is properly configured"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    required_vars = ['WALMART_CONSUMER_ID']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n📝 Please create a .env file with your API credentials.")
        print("   You can copy .env.example as a template.")
        return False
    
    return True

def main():
    """Main function"""
    setup_logging()
    print_banner()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Test Walmart API batch sizes')
    parser.add_argument('--mode', choices=['standard', 'limits', 'category'], 
                       default='standard', help='Testing mode')
    parser.add_argument('--category', type=str, help='Category ID to test with')
    parser.add_argument('--iterations', type=int, default=1, 
                       help='Number of iterations per batch size')
    parser.add_argument('--custom-sizes', type=str, 
                       help='Custom batch sizes (comma-separated)')
    parser.add_argument('--no-charts', action='store_true', 
                       help='Skip chart generation')
    
    args = parser.parse_args()
    
    # Check environment
    if not check_environment():
        return 1
    
    # Load configuration
    config = Config()
    
    # Create batch tester
    tester = BatchTester(results_dir=config.get('output.results_directory', 'results'))
    
    # Override batch sizes if custom ones provided
    if args.custom_sizes:
        try:
            custom_sizes = [int(x.strip()) for x in args.custom_sizes.split(',')]
            tester.test_counts = custom_sizes
            print(f"Using custom batch sizes: {custom_sizes}")
        except ValueError:
            print("❌ Invalid custom batch sizes format. Use: 1,5,10,25")
            return 1
    
    try:
        if args.mode == 'standard':
            print("🧪 Running standard batch size testing...")
            tester.run_comprehensive_test(
                category=args.category,
                iterations=args.iterations
            )
            
        elif args.mode == 'limits':
            print("🔍 Testing maximum API limits...")
            tester.test_maximum_limits()
            
        elif args.mode == 'category':
            categories = config.get_test_categories()
            if not categories:
                print("❌ No test categories configured")
                return 1
                
            print("🏷️ Testing different categories...")
            for cat_name, cat_id in categories.items():
                print(f"\n--- Testing category: {cat_name} (ID: {cat_id}) ---")
                tester.run_comprehensive_test(category=cat_id, iterations=1)
        
        print("\n✅ Testing completed successfully!")
        print("📊 Check the results/ directory for detailed output.")
        
    except KeyboardInterrupt:
        print("\n⏹️ Testing interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        logging.exception("Testing failed with exception")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())