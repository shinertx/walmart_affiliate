"""
Product data transformer to convert Walmart products to Shopify format
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime


class ProductTransformer:
    """
    Transform Walmart product data to Shopify product format
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def transform_walmart_to_shopify(self, walmart_product: Dict) -> Dict[str, Any]:
        """
        Transform a Walmart product to Shopify format
        
        Args:
            walmart_product: Product data from Walmart API
            
        Returns:
            Product data in Shopify format
        """
        try:
            # Extract Walmart product fields
            item_id = walmart_product.get('itemId')
            name = walmart_product.get('name', 'Untitled Product')
            short_desc = walmart_product.get('shortDescription', '')
            long_desc = walmart_product.get('longDescription', '')
            price = walmart_product.get('salePrice', walmart_product.get('msrp', 0))
            image_url = walmart_product.get('mediumImage') or walmart_product.get('largeImage') or walmart_product.get('thumbnailImage')
            category = walmart_product.get('categoryPath', '')
            brand = walmart_product.get('brandName', '')
            upc = walmart_product.get('upc', '')
            model_number = walmart_product.get('modelNumber', '')
            availability = walmart_product.get('availableOnline', False)
            stock = walmart_product.get('stock', 'Available') if availability else 'Not Available'
            
            # Build product description
            description = self._build_description(long_desc, short_desc, walmart_product)
            
            # Create Shopify product structure
            shopify_product = {
                'title': self._clean_title(name),
                'body_html': description,
                'vendor': brand or 'Walmart',
                'product_type': self._extract_product_type(category),
                'tags': self._generate_tags(walmart_product),
                'published': True,
                'variants': [
                    {
                        'price': str(price),
                        'sku': str(item_id),
                        'inventory_management': 'shopify',
                        'inventory_policy': 'deny',
                        'fulfillment_service': 'manual',
                        'requires_shipping': True,
                        'taxable': True,
                        'barcode': upc if upc else None,
                        'weight': walmart_product.get('weight', 0),
                        'weight_unit': 'lb'
                    }
                ],
                'options': [
                    {
                        'name': 'Title',
                        'values': ['Default Title']
                    }
                ],
                'images': []
            }
            
            # Add product images
            if image_url:
                shopify_product['images'].append({
                    'src': image_url,
                    'alt': name
                })
            
            # Add additional images if available
            image_entities = walmart_product.get('imageEntities', [])
            for img in image_entities[:5]:  # Limit to 5 additional images
                if img.get('mediumImage'):
                    shopify_product['images'].append({
                        'src': img['mediumImage'],
                        'alt': name
                    })
            
            # Add metafields for Walmart-specific data
            shopify_product['metafields'] = [
                {
                    'namespace': 'walmart',
                    'key': 'item_id',
                    'value': str(item_id),
                    'type': 'single_line_text_field'
                },
                {
                    'namespace': 'walmart',
                    'key': 'product_url',
                    'value': walmart_product.get('productUrl', ''),
                    'type': 'url'
                }
            ]
            
            if upc:
                shopify_product['metafields'].append({
                    'namespace': 'walmart',
                    'key': 'upc',
                    'value': upc,
                    'type': 'single_line_text_field'
                })
            
            if model_number:
                shopify_product['metafields'].append({
                    'namespace': 'walmart',
                    'key': 'model_number',
                    'value': model_number,
                    'type': 'single_line_text_field'
                })
            
            return shopify_product
            
        except Exception as e:
            self.logger.error(f"Error transforming product: {str(e)}")
            raise
    
    def _clean_title(self, title: str) -> str:
        """Clean and truncate product title for Shopify (max 255 chars)"""
        if not title:
            return 'Untitled Product'
        
        # Remove excessive whitespace
        title = ' '.join(title.split())
        
        # Truncate to 255 characters
        if len(title) > 255:
            title = title[:252] + '...'
        
        return title
    
    def _build_description(self, long_desc: str, short_desc: str, product: Dict) -> str:
        """Build HTML product description"""
        parts = []
        
        # Add short description
        if short_desc:
            parts.append(f"<p>{short_desc}</p>")
        
        # Add long description
        if long_desc and long_desc != short_desc:
            parts.append(f"<div>{long_desc}</div>")
        
        # Add product features
        features = product.get('features', [])
        if features:
            parts.append("<h3>Features:</h3>")
            parts.append("<ul>")
            for feature in features[:10]:  # Limit to 10 features
                parts.append(f"<li>{feature}</li>")
            parts.append("</ul>")
        
        # Add specifications
        if not parts:
            parts.append(f"<p>High-quality product from Walmart.</p>")
        
        return '\n'.join(parts)
    
    def _extract_product_type(self, category_path: str) -> str:
        """Extract product type from category path"""
        if not category_path:
            return 'General'
        
        # Category path is usually like "Electronics/Computers/Laptops"
        # We want the most specific category (last one)
        categories = category_path.split('/')
        if categories:
            return categories[-1].strip()
        
        return 'General'
    
    def _generate_tags(self, product: Dict) -> str:
        """Generate product tags for better searchability"""
        tags = []
        
        # Add brand
        brand = product.get('brandName')
        if brand:
            tags.append(brand)
        
        # Add category tags
        category_path = product.get('categoryPath', '')
        if category_path:
            categories = [c.strip() for c in category_path.split('/') if c.strip()]
            tags.extend(categories)
        
        # Add special tags
        if product.get('availableOnline'):
            tags.append('Available Online')
        
        if product.get('freeShipping'):
            tags.append('Free Shipping')
        
        if product.get('specialOffer'):
            tags.append('Special Offer')
        
        # Add Walmart tag
        tags.append('Walmart')
        
        # Remove duplicates while preserving order
        # Using dict.fromkeys() instead of set() to maintain insertion order
        tags = list(dict.fromkeys(tags))  # Remove duplicates while preserving order
        return ', '.join(tags[:20])  # Limit to 20 tags
    
    def is_valid_product(self, walmart_product: Dict) -> bool:
        """
        Check if a Walmart product has required fields for Shopify import
        
        Args:
            walmart_product: Product data from Walmart API
            
        Returns:
            True if product is valid for import, False otherwise
        """
        # Must have essential fields
        if not walmart_product.get('itemId'):
            self.logger.debug("Missing itemId")
            return False
        
        if not walmart_product.get('name'):
            self.logger.debug("Missing name")
            return False
        
        # Must have a price
        price = walmart_product.get('salePrice') or walmart_product.get('msrp')
        if not price or price <= 0:
            self.logger.debug("Missing or invalid price")
            return False
        
        # Must be available online
        if not walmart_product.get('availableOnline', False):
            self.logger.debug("Not available online")
            return False
        
        return True
    
    def filter_by_category(self, walmart_product: Dict, categories: List[str]) -> bool:
        """
        Check if product belongs to specified categories
        
        Args:
            walmart_product: Product data from Walmart API
            categories: List of category keywords to filter by (e.g., ['Electronics', 'Baby'])
            
        Returns:
            True if product matches any of the categories
        """
        if not categories:
            return True
        
        category_path = walmart_product.get('categoryPath', '').lower()
        category_node = walmart_product.get('categoryNode', '').lower()
        
        for category in categories:
            if category.lower() in category_path or category.lower() in category_node:
                return True
        
        return False
    
    def is_walmart_seller(self, walmart_product: Dict) -> bool:
        """
        Check if product is sold by Walmart (not third-party seller)
        
        Args:
            walmart_product: Product data from Walmart API
            
        Returns:
            True if sold by Walmart, False if third-party seller
        """
        # Check if the seller name indicates Walmart
        seller_info = walmart_product.get('sellerInfo', '')
        if isinstance(seller_info, str):
            seller_info = seller_info.lower()
            if 'walmart' in seller_info:
                return True
            if seller_info and 'walmart' not in seller_info:
                return False
        
        # Check marketplace flag
        is_marketplace = walmart_product.get('marketplace', False)
        if is_marketplace:
            return False
        
        # Check shipping source
        shipping_source = walmart_product.get('fulfillmentSource', '').lower()
        if 'walmart' in shipping_source or 'store' in shipping_source:
            return True
        
        # If no clear indicator, assume it's Walmart (conservative default)
        return True
