import os
import sys
from src.walmart_api import WalmartAPIClient

def check_pagination():
    client = WalmartAPIClient()
    print("Fetching first page...")
    result = client.get_products(count=25, category='3944') # Electronics
    
    if result['success']:
        metadata = result['metadata']
        next_page = metadata.get('next_page')
        print(f"Next Page URL: {next_page}")
    else:
        print(f"Error: {result.get('error')}")

if __name__ == "__main__":
    check_pagination()
