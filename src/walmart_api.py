import requests
import time
import json
import logging
from typing import Dict, Optional, List, Any
from datetime import datetime
import os
import base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from dotenv import load_dotenv

load_dotenv()

class WalmartAPIClient:
    """
    Walmart Affiliate API client for testing batch product retrieval
    Uses RSA signature-based authentication as required by Walmart API
    """
    
    def __init__(self):
        # Base endpoints
        self.base_url = os.getenv('BASE_URL', 'https://developer.api.walmart.com/api-proxy/service/affil/product/v2/paginated/items')
        self.items_by_ids_url = os.getenv('ITEMS_BY_IDS_URL', 'https://developer.api.walmart.com/api-proxy/service/affil/product/v2/items')
        self.consumer_id = os.getenv('WALMART_CONSUMER_ID')
        self.private_key_version = os.getenv('WALMART_PRIVATE_KEY_VERSION', '1')
        self.private_key_path = os.getenv('WALMART_PRIVATE_KEY_PATH')
        self.private_key_content = os.getenv('WALMART_PRIVATE_KEY')
        self.publisher_id = os.getenv('PUBLISHER_ID')
        self.campaign_id = os.getenv('CAMPAIGN_ID')
        self.ad_id = os.getenv('AD_ID')
        self.max_retries = int(os.getenv('MAX_RETRIES', 3))
        self.timeout = int(os.getenv('REQUEST_TIMEOUT', 30))
        self.delay = float(os.getenv('DELAY_BETWEEN_REQUESTS', 1))
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('walmart_api_test.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        if not self.consumer_id:
            raise ValueError("WALMART_CONSUMER_ID not found in environment variables")
        
        # Load private key
        self.private_key = self._load_private_key()
    
    def _load_private_key(self):
        """Load RSA private key from file or environment variable"""
        try:
            if self.private_key_content:
                # Load from environment variable (base64 encoded)
                key_bytes = base64.b64decode(self.private_key_content)
                return serialization.load_der_private_key(
                    key_bytes, 
                    password=None, 
                    backend=default_backend()
                )
            elif self.private_key_path and os.path.exists(self.private_key_path):
                # Load from file
                with open(self.private_key_path, 'rb') as key_file:
                    return serialization.load_pem_private_key(
                        key_file.read(),
                        password=None,
                        backend=default_backend()
                    )
            else:
                self.logger.warning("No private key found. Will create a demo key for testing.")
                return self._generate_demo_key()
        except Exception as e:
            self.logger.error(f"Failed to load private key: {str(e)}")
            self.logger.info("Generating demo key for testing...")
            return self._generate_demo_key()
    
    def _generate_demo_key(self):
        """Generate a temporary RSA key pair for testing purposes"""
        self.logger.info("🔑 Generating temporary RSA key pair for testing...")
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        # Save public key for reference
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        with open('walmart_public_key.pem', 'wb') as f:
            f.write(public_pem)
        
        self.logger.warning("⚠️  Generated temporary keys. You'll need to upload walmart_public_key.pem to Walmart Developer Portal")
        return private_key
    
    def _generate_signature(self, string_to_sign: str) -> str:
        """Generate RSA SHA256 signature for the given string"""
        try:
            signature = self.private_key.sign(
                string_to_sign.encode('utf-8'),
                padding.PKCS1v15(),
                hashes.SHA256()
            )
            return base64.b64encode(signature).decode('utf-8')
        except Exception as e:
            self.logger.error(f"Failed to generate signature: {str(e)}")
            raise
    
    def _get_headers(self) -> Dict[str, str]:
        """Get required headers for API requests with RSA signature authentication"""
        # Generate timestamp in milliseconds
        timestamp = str(int(time.time() * 1000))
        
        # Create signature data according to Walmart API spec
        signature_data = {
            'WM_CONSUMER.ID': self.consumer_id,
            'WM_CONSUMER.INTIMESTAMP': timestamp,
            'WM_SEC.KEY_VERSION': self.private_key_version
        }
        
        # Canonicalize the data (sort keys and create string)
        sorted_keys = sorted(signature_data.keys())
        canonical_string = '\n'.join(signature_data[key] for key in sorted_keys) + '\n'
        
        # Generate signature
        signature = self._generate_signature(canonical_string)
        
        # Build headers
        headers = {
            'WM_SVC.NAME': 'Walmart Open API',
            'WM_QOS.CORRELATION_ID': f'test_{timestamp}',
            'WM_CONSUMER.ID': self.consumer_id,
            'WM_CONSUMER.INTIMESTAMP': timestamp,
            'WM_SEC.KEY_VERSION': self.private_key_version,
            'WM_SEC.AUTH_SIGNATURE': signature,
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        return headers
    
    def _build_params(self, count: int = 25, **kwargs) -> Dict[str, Any]:
        """Build query parameters for API request"""
        params = {
            'count': count
        }
        
        # Add optional parameters
        if self.publisher_id:
            params['publisherId'] = self.publisher_id
        if self.campaign_id:
            params['campaignId'] = self.campaign_id  
        if self.ad_id:
            params['adId'] = self.ad_id
            
        # Add any additional filters
        for key, value in kwargs.items():
            if value is not None:
                params[key] = value
                
        return params

    def get_items_by_ids(self,
                         ids: List[int],
                         postal_code: Optional[str] = None,
                         extra_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Retrieve product details by Walmart item IDs. Optionally pass a postal/ZIP code
        to attempt location-aware availability/pricing when supported.

        Args:
            ids: List of Walmart item IDs
            postal_code: Optional postal/ZIP code (e.g., '78210')
            extra_params: Additional query params if needed

        Returns:
            Dict with success flag, data or error, response time metadata
        """
        if not ids:
            return {
                'success': False,
                'error': 'No item IDs provided'
            }

        headers = self._get_headers()

        params: Dict[str, Any] = {
            'ids': ','.join(str(i) for i in ids)
        }
        if postal_code:
            # Some endpoints may accept 'postalCode' to localize availability
            params['postalCode'] = postal_code
        if extra_params:
            params.update({k: v for k, v in extra_params.items() if v is not None})

        start_time = time.time()
        for attempt in range(self.max_retries):
            try:
                self.logger.info(f"Fetching {len(ids)} items by IDs (attempt {attempt + 1})")
                response = requests.get(self.items_by_ids_url, headers=headers, params=params, timeout=self.timeout)
                response_time = time.time() - start_time
                self.logger.info(f"Response status: {response.status_code}")
                self.logger.info(f"Response time: {response_time:.2f}s")
                self.logger.info(f"Response size: {len(response.content)} bytes")

                if response.status_code == 200:
                    data = response.json()
                    # Normalize to align with get_products structure when possible
                    # items endpoint usually returns {'items': [...]} or a list
                    if isinstance(data, dict):
                        items = data.get('items', data.get('data', data))
                    else:
                        items = data

                    return {
                        'success': True,
                        'data': {
                            'items': items
                        },
                        'response_time': response_time
                    }
                else:
                    error_text = response.text
                    self.logger.error(f"API error: {response.status_code} - {error_text[:300]}")
                    if response.status_code >= 500 and attempt < self.max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    return {
                        'success': False,
                        'error': f"Status {response.status_code}: {error_text}"
                    }
            except Exception as e:
                self.logger.error(f"Request failed: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return {
                    'success': False,
                    'error': str(e)
                }

    def get_items_by_upc(self,
                          upcs: List[str],
                          postal_code: Optional[str] = None,
                          extra_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Retrieve product details by UPC/GTIN codes using the items endpoint.
        Tries the 'upc' parameter; if unsupported, falls back to 'gtin'.

        Args:
            upcs: List of UPC/GTIN strings
            postal_code: Optional postal/ZIP code
            extra_params: Additional query params

        Returns:
            Dict with success flag and items array when successful.
        """
        if not upcs:
            return {'success': False, 'error': 'No UPCs provided'}

        headers = self._get_headers()

        def _request_with(param_name: str) -> Dict[str, Any]:
            params: Dict[str, Any] = {param_name: ','.join(upcs)}
            if postal_code:
                params['postalCode'] = postal_code
            if extra_params:
                params.update({k: v for k, v in extra_params.items() if v is not None})

            start_time = time.time()
            try:
                self.logger.info(f"Fetching {len(upcs)} items by {param_name} (batch)")
                resp = requests.get(self.items_by_ids_url, headers=headers, params=params, timeout=self.timeout)
                rt = time.time() - start_time
                self.logger.info(f"Response status: {resp.status_code}")
                self.logger.info(f"Response time: {rt:.2f}s")
                self.logger.info(f"Response size: {len(resp.content)} bytes")
                if resp.status_code == 200:
                    data = resp.json()
                    items = data.get('items', data if isinstance(data, list) else [])
                    return {'success': True, 'data': {'items': items}, 'response_time': rt}
                return {'success': False, 'error': f"Status {resp.status_code}: {resp.text}"}
            except Exception as e:
                return {'success': False, 'error': str(e)}

        # Try 'upc' param first
        res = _request_with('upc')
        if res.get('success'):
            return res
        # Fallback to 'gtin'
        self.logger.info("'upc' param failed; trying 'gtin' param")
        res2 = _request_with('gtin')
        if res2.get('success'):
            return res2
        return res2
    
    def get_products(self, 
                    count: int = 25,
                    category: Optional[str] = None,
                    brand: Optional[str] = None,
                    special_offer: Optional[str] = None,
                    **kwargs) -> Dict[str, Any]:
        """
        Retrieve products from Walmart API
        
        Args:
            count: Number of items to retrieve (testing parameter)
            category: Category ID filter
            brand: Brand name filter
            special_offer: Special offer filter (rollback, clearance, etc.)
            **kwargs: Additional filter parameters
            
        Returns:
            Dict containing API response data and metadata
        """
        headers = self._get_headers()
        params = self._build_params(
            count=count,
            category=category,
            brand=brand,
            specialOffer=special_offer,
            **kwargs
        )
        
        start_time = time.time()
        
        for attempt in range(self.max_retries):
            try:
                self.logger.info(f"Making API request (attempt {attempt + 1}) with count={count}")
                
                response = requests.get(
                    self.base_url,
                    headers=headers,
                    params=params,
                    timeout=self.timeout
                )
                
                end_time = time.time()
                response_time = end_time - start_time
                
                # Log request details
                self.logger.info(f"Response status: {response.status_code}")
                self.logger.info(f"Response time: {response_time:.2f}s")
                self.logger.info(f"Response size: {len(response.content)} bytes")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Add metadata to response
                    metadata = {
                        'request_time': datetime.now().isoformat(),
                        'response_time_seconds': response_time,
                        'response_size_bytes': len(response.content),
                        'requested_count': count,
                        'actual_items_returned': len(data.get('items', [])),
                        'total_pages': data.get('totalPages'),
                        'next_page': data.get('nextPage'),
                        'status_code': response.status_code,
                        'headers_sent': dict(headers),
                        'params_sent': dict(params)
                    }
                    
                    result = {
                        'data': data,
                        'metadata': metadata,
                        'success': True,
                        'error': None
                    }
                    
                    self.logger.info(f"Successfully retrieved {len(data.get('items', []))} items")
                    return result
                    
                else:
                    self.logger.warning(f"API returned status code: {response.status_code}")
                    self.logger.warning(f"Response content: {response.text[:500]}")
                    
                    if response.status_code == 429:  # Rate limited
                        wait_time = 2 ** attempt  # Exponential backoff
                        self.logger.info(f"Rate limited. Waiting {wait_time}s before retry...")
                        time.sleep(wait_time)
                        continue
                    
                    # For other HTTP errors, return the error immediately
                    return {
                        'data': None,
                        'metadata': {
                            'request_time': datetime.now().isoformat(),
                            'response_time_seconds': time.time() - start_time,
                            'requested_count': count,
                            'status_code': response.status_code,
                            'error_response': response.text
                        },
                        'success': False,
                        'error': f"HTTP {response.status_code}: {response.text}"
                    }
                    
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Request exception on attempt {attempt + 1}: {str(e)}")
                if attempt == self.max_retries - 1:  # Last attempt
                    return {
                        'data': None,
                        'metadata': {
                            'request_time': datetime.now().isoformat(),
                            'requested_count': count,
                            'error': str(e)
                        },
                        'success': False,
                        'error': f"Request failed after {self.max_retries} attempts: {str(e)}"
                    }
                time.sleep(2 ** attempt)  # Exponential backoff
            
            # Add delay between requests to be respectful
            time.sleep(self.delay)
        
        return {
            'data': None,
            'metadata': {
                'request_time': datetime.now().isoformat(),
                'requested_count': count
            },
            'success': False,
            'error': f"Failed after {self.max_retries} attempts"
        }
    
    def test_connection(self) -> bool:
        """Test basic API connectivity"""
        try:
            result = self.get_products(count=1)
            return result['success']
        except Exception as e:
            self.logger.error(f"Connection test failed: {str(e)}")
            return False