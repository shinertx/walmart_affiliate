"""
Shopify API Client for importing products from Walmart
"""
import requests
import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()


class ShopifyAPIClient:
    """
    Shopify API client for importing Walmart products
    """
    
    def __init__(self):
        self.shop_name = os.getenv('SHOPIFY_SHOP_NAME')
        self.access_token = os.getenv('SHOPIFY_ACCESS_TOKEN')
        self.api_version = os.getenv('SHOPIFY_API_VERSION', '2024-01')
        
        if not self.shop_name or not self.access_token:
            raise ValueError("SHOPIFY_SHOP_NAME and SHOPIFY_ACCESS_TOKEN must be set in environment variables")
        
        self.base_url = f"https://{self.shop_name}.myshopify.com/admin/api/{self.api_version}"
        self.headers = {
            'Content-Type': 'application/json',
            'X-Shopify-Access-Token': self.access_token
        }
        
        # Rate limiting
        self.rate_limit_delay = float(os.getenv('SHOPIFY_RATE_LIMIT_DELAY', '0.5'))
        self.max_retries = int(os.getenv('SHOPIFY_MAX_RETRIES', '3'))
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make a request to Shopify API with rate limiting and retries"""
        url = f"{self.base_url}/{endpoint}"
        
        for attempt in range(self.max_retries):
            try:
                if method.upper() == 'GET':
                    response = requests.get(url, headers=self.headers, timeout=30)
                elif method.upper() == 'POST':
                    response = requests.post(url, headers=self.headers, json=data, timeout=30)
                elif method.upper() == 'PUT':
                    response = requests.put(url, headers=self.headers, json=data, timeout=30)
                elif method.upper() == 'DELETE':
                    response = requests.delete(url, headers=self.headers, timeout=30)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                # Check for rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 2))
                    self.logger.warning(f"Rate limited. Waiting {retry_after}s...")
                    time.sleep(retry_after)
                    continue
                
                # Success
                if response.status_code in [200, 201]:
                    time.sleep(self.rate_limit_delay)  # Respect rate limits
                    return {
                        'success': True,
                        'data': response.json(),
                        'status_code': response.status_code
                    }
                
                # Client or server error
                self.logger.error(f"Shopify API error: {response.status_code} - {response.text[:200]}")
                if attempt == self.max_retries - 1:
                    return {
                        'success': False,
                        'error': f"HTTP {response.status_code}: {response.text}",
                        'status_code': response.status_code
                    }
                
                time.sleep(2 ** attempt)  # Exponential backoff
                
            except Exception as e:
                self.logger.error(f"Request failed: {str(e)}")
                if attempt == self.max_retries - 1:
                    return {
                        'success': False,
                        'error': str(e)
                    }
                time.sleep(2 ** attempt)
        
        return {
            'success': False,
            'error': f"Failed after {self.max_retries} attempts"
        }
    
    def create_product(self, product_data: Dict) -> Dict[str, Any]:
        """
        Create a product in Shopify
        
        Args:
            product_data: Product data in Shopify format
            
        Returns:
            Dict with success flag and product data or error
        """
        return self._make_request('POST', 'products.json', {'product': product_data})
    
    def get_product(self, product_id: int) -> Dict[str, Any]:
        """Get a product by ID"""
        return self._make_request('GET', f'products/{product_id}.json')
    
    def update_product(self, product_id: int, product_data: Dict) -> Dict[str, Any]:
        """Update a product"""
        return self._make_request('PUT', f'products/{product_id}.json', {'product': product_data})
    
    def delete_product(self, product_id: int) -> Dict[str, Any]:
        """Delete a product"""
        return self._make_request('DELETE', f'products/{product_id}.json')
    
    def get_products_count(self) -> int:
        """Get total number of products in the store"""
        result = self._make_request('GET', 'products/count.json')
        if result['success']:
            return result['data'].get('count', 0)
        return 0
    
    def search_product_by_sku(self, sku: str) -> Optional[Dict]:
        """
        Search for a product by SKU to avoid duplicates
        
        Note: This is a simple implementation. For production, consider:
        - Maintaining a local cache of SKUs
        - Using GraphQL for more efficient queries
        """
        # In a production system, we would maintain a cache of SKUs
        # For now, we'll just return None to skip duplicate checking
        # This can be improved by implementing proper SKU caching
        return None
    
    def test_connection(self) -> bool:
        """Test Shopify API connection"""
        try:
            result = self._make_request('GET', 'shop.json')
            if result['success']:
                shop_info = result['data'].get('shop', {})
                self.logger.info(f"Connected to Shopify store: {shop_info.get('name')}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Connection test failed: {str(e)}")
            return False
