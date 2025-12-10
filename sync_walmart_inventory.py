import csv
import requests
import os
import time
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Shopify Configuration
SHOPIFY_STORE_URL = os.getenv("SHOPIFY_STORE_URL")
SHOPIFY_ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")
API_VERSION = "2024-01"

if not SHOPIFY_STORE_URL or not SHOPIFY_ACCESS_TOKEN:
    print("Error: SHOPIFY_STORE_URL and SHOPIFY_ACCESS_TOKEN must be set in .env")
    exit(1)

BASE_URL = f"https://{SHOPIFY_STORE_URL}/admin/api/{API_VERSION}"
HEADERS = {
    "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN,
    "Content-Type": "application/json"
}

def update_shopify_product(product_id, data):
    """Updates a product in Shopify via the Admin API."""
    url = f"{BASE_URL}/products/{product_id}.json"
    try:
        response = requests.put(url, headers=HEADERS, json={"product": data})
        if response.status_code == 200:
            return True
        else:
            print(f"   ❌ API Error {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False

def sync_inventory_from_report(report_file='inventory_audit_report.csv'):
    print(f"Starting inventory sync from {report_file}...")
    
    if not os.path.exists(report_file):
        print(f"Error: Report file {report_file} not found. Run audit_store_inventory.py first.")
        return

    success_count = 0
    error_count = 0
    
    with open(report_file, mode='r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        
        for row in reader:
            shopify_id = row['Shopify_ID']
            action = row['Action_Needed']
            target_price = row['Target_Price']
            title = row['Title']
            
            print(f"Processing {title} (ID: {shopify_id})...")
            
            update_data = {}
            
            if action == 'Update Price & Sync':
                # Update Price and set to Active
                update_data = {
                    "id": shopify_id,
                    "status": "active",
                    "tags": "Walmart-Synced, Valid",
                    "variants": [
                        {
                            "price": target_price,
                            "inventory_management": "shopify" 
                        }
                    ]
                }
                # Note: Updating variants like this might be tricky if there are multiple. 
                # But for this use case, we assume 1 variant per product as per the audit script logic.
                
            elif action in ['Archive (3rd Party)', 'Archive/Delete', 'Check SKU']:
                # Archive the product
                update_data = {
                    "id": shopify_id,
                    "status": "archived",
                    "tags": f"Archived: {row['Walmart_Status']}"
                }

            elif action == 'Pause (OOS)':
                # Archive or Draft for OOS
                update_data = {
                    "id": shopify_id,
                    "status": "archived",
                    "tags": "Walmart-OOS"
                }
            
            if update_data:
                if update_shopify_product(shopify_id, update_data):
                    print(f"   ✅ Success: {action}")
                    success_count += 1
                else:
                    print(f"   ❌ Failed: {action}")
                    error_count += 1
            else:
                print(f"   ⚠️  No action defined for {action}")

            # Rate limiting pause
            time.sleep(0.5)

    print(f"\nSync Complete!")
    print(f"Success: {success_count}")
    print(f"Errors: {error_count}")

if __name__ == "__main__":
    sync_inventory_from_report()
