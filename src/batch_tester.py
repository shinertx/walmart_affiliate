import json
import csv
import time
from datetime import datetime
from typing import List, Dict, Any
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

from walmart_api import WalmartAPIClient

class BatchTester:
    """
    Test different batch sizes for Walmart API to find optimal throughput
    """
    
    def __init__(self, results_dir: str = "results"):
        self.api_client = WalmartAPIClient()
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        
        # Test configurations
        self.test_counts = [1, 5, 10, 25, 50, 100, 200, 400, 500, 1000]
        self.results = []
    
    def run_single_test(self, count: int, category: str = None) -> Dict[str, Any]:
        """Run a single test with specified count parameter"""
        print(f"\n🧪 Testing batch size: {count} items")
        
        start_time = time.time()
        result = self.api_client.get_products(
            count=count,
            category=category
        )
        
        if result['success']:
            metadata = result['metadata']
            items_returned = metadata['actual_items_returned']
            response_time = metadata['response_time_seconds']
            response_size = metadata['response_size_bytes']
            
            throughput = items_returned / response_time if response_time > 0 else 0
            
            test_result = {
                'timestamp': datetime.now().isoformat(),
                'requested_count': count,
                'actual_count': items_returned,
                'response_time': response_time,
                'response_size_bytes': response_size,
                'response_size_mb': response_size / (1024 * 1024),
                'throughput_items_per_second': throughput,
                'success': True,
                'error': None,
                'total_pages_available': metadata.get('total_pages'),
                'has_next_page': bool(metadata.get('next_page'))
            }
            
            print(f"✅ Success: {items_returned} items in {response_time:.2f}s")
            print(f"   Throughput: {throughput:.2f} items/second")
            print(f"   Response size: {response_size / 1024:.1f} KB")
            
        else:
            test_result = {
                'timestamp': datetime.now().isoformat(),
                'requested_count': count,
                'actual_count': 0,
                'response_time': 0,
                'response_size_bytes': 0,
                'response_size_mb': 0,
                'throughput_items_per_second': 0,
                'success': False,
                'error': result['error'],
                'total_pages_available': None,
                'has_next_page': False
            }
            
            print(f"❌ Failed: {result['error']}")
        
        return test_result
    
    def run_comprehensive_test(self, category: str = None, iterations: int = 1):
        """Run tests across different batch sizes"""
        print("🚀 Starting Walmart API Batch Size Testing")
        print(f"Testing batch sizes: {self.test_counts}")
        
        if category:
            print(f"Using category filter: {category}")
        
        print(f"Iterations per batch size: {iterations}")
        print("=" * 60)
        
        # Test API connectivity first
        print("🔍 Testing API connectivity...")
        if not self.api_client.test_connection():
            print("❌ API connection test failed. Please check your credentials.")
            return
        
        print("✅ API connection successful")
        
        all_results = []
        
        for count in self.test_counts:
            for iteration in range(iterations):
                if iterations > 1:
                    print(f"Iteration {iteration + 1}/{iterations} for count={count}")
                
                result = self.run_single_test(count, category)
                result['iteration'] = iteration + 1
                all_results.append(result)
                
                # Add delay between tests to be respectful to the API
                if count != self.test_counts[-1] or iteration != iterations - 1:
                    time.sleep(2)
        
        self.results = all_results
        self._save_results()
        self._analyze_results()
    
    def _save_results(self):
        """Save test results to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save as JSON
        json_file = self.results_dir / f"batch_test_results_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        # Save as CSV
        csv_file = self.results_dir / f"batch_test_results_{timestamp}.csv"
        df = pd.DataFrame(self.results)
        df.to_csv(csv_file, index=False)
        
        print(f"\n📊 Results saved to:")
        print(f"   JSON: {json_file}")
        print(f"   CSV: {csv_file}")
    
    def _analyze_results(self):
        """Analyze and visualize test results"""
        if not self.results:
            return
        
        df = pd.DataFrame(self.results)
        successful_results = df[df['success'] == True]
        
        if successful_results.empty:
            print("❌ No successful results to analyze")
            return
        
        print("\n📈 ANALYSIS RESULTS")
        print("=" * 50)
        
        # Basic statistics
        print("📊 Success Rate by Batch Size:")
        success_rate = df.groupby('requested_count')['success'].mean() * 100
        for count, rate in success_rate.items():
            print(f"   {count:4d} items: {rate:5.1f}%")
        
        if not successful_results.empty:
            # Performance metrics
            print("\n⚡ Performance Metrics (Successful Requests Only):")
            perf_stats = successful_results.groupby('requested_count').agg({
                'actual_count': ['mean', 'max'],
                'response_time': ['mean', 'min', 'max'],
                'throughput_items_per_second': ['mean', 'max'],
                'response_size_mb': ['mean', 'max']
            }).round(2)
            
            print(perf_stats)
            
            # Find optimal batch size
            optimal = successful_results.loc[successful_results['throughput_items_per_second'].idxmax()]
            print(f"\n🎯 Optimal Batch Size: {optimal['requested_count']} items")
            print(f"   Max Throughput: {optimal['throughput_items_per_second']:.2f} items/second")
            print(f"   Response Time: {optimal['response_time']:.2f}s")
            print(f"   Data Size: {optimal['response_size_mb']:.2f} MB")
            
            # Find maximum successful batch size
            max_successful = successful_results['requested_count'].max()
            max_items = successful_results['actual_count'].max()
            print(f"\n📏 Maximum Successful Batch:")
            print(f"   Requested: {max_successful} items")
            print(f"   Actually Retrieved: {max_items} items")
            
            # Create visualizations
            self._create_visualizations(df)
    
    def _create_visualizations(self, df: pd.DataFrame):
        """Create performance visualization charts"""
        successful_df = df[df['success'] == True]
        
        if successful_df.empty:
            return
        
        # Set up the plotting style
        plt.style.use('seaborn-v0_8')
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Walmart API Batch Size Performance Analysis', fontsize=16, fontweight='bold')
        
        # 1. Throughput vs Batch Size
        ax1 = axes[0, 0]
        successful_df.groupby('requested_count')['throughput_items_per_second'].mean().plot(
            kind='bar', ax=ax1, color='skyblue'
        )
        ax1.set_title('Average Throughput by Batch Size')
        ax1.set_xlabel('Requested Batch Size')
        ax1.set_ylabel('Items per Second')
        ax1.tick_params(axis='x', rotation=45)
        
        # 2. Response Time vs Batch Size
        ax2 = axes[0, 1]
        successful_df.groupby('requested_count')['response_time'].mean().plot(
            kind='line', ax=ax2, marker='o', color='orange'
        )
        ax2.set_title('Average Response Time by Batch Size')
        ax2.set_xlabel('Requested Batch Size')
        ax2.set_ylabel('Response Time (seconds)')
        
        # 3. Success Rate vs Batch Size
        ax3 = axes[1, 0]
        success_rate = df.groupby('requested_count')['success'].mean() * 100
        success_rate.plot(kind='bar', ax=ax3, color='lightgreen')
        ax3.set_title('Success Rate by Batch Size')
        ax3.set_xlabel('Requested Batch Size')
        ax3.set_ylabel('Success Rate (%)')
        ax3.tick_params(axis='x', rotation=45)
        
        # 4. Response Size vs Batch Size
        ax4 = axes[1, 1]
        successful_df.groupby('requested_count')['response_size_mb'].mean().plot(
            kind='bar', ax=ax4, color='lightcoral'
        )
        ax4.set_title('Average Response Size by Batch Size')
        ax4.set_xlabel('Requested Batch Size')
        ax4.set_ylabel('Response Size (MB)')
        ax4.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        # Save the plot
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        plot_file = self.results_dir / f"batch_test_analysis_{timestamp}.png"
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        print(f"📊 Analysis chart saved: {plot_file}")
        
        plt.show()
    
    def test_maximum_limits(self):
        """Test to find the absolute maximum batch size supported"""
        print("\n🔍 Testing Maximum Batch Size Limits")
        print("=" * 50)
        
        # Start with larger values to find upper limit quickly
        test_values = [1000, 2000, 5000, 10000, 20000]
        
        max_working_size = 0
        
        for count in test_values:
            print(f"\nTesting maximum batch size: {count}")
            result = self.run_single_test(count)
            
            if result['success']:
                max_working_size = count
                print(f"✅ {count} items: SUCCESS")
            else:
                print(f"❌ {count} items: FAILED - {result['error']}")
                break
        
        if max_working_size > 0:
            print(f"\n🎯 Maximum working batch size: {max_working_size} items")
        else:
            print(f"\n⚠️ Could not determine maximum batch size")
        
        return max_working_size