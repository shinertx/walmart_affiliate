#!/usr/bin/env python3
"""
Exact UPC/GTIN lookup test against Walmart Affiliate API
- Uses the items endpoint with 'upc' (fallback 'gtin')
- Summarizes found vs missing
- Optional ZIP enrichment via postalCode
"""
import sys
from pathlib import Path
from typing import List, Dict

sys.path.insert(0, str(Path(__file__).parent / 'src'))
from walmart_api import WalmartAPIClient

# Same GTIN list as our earlier test
TEST_PRODUCTS = [
    ("30317011833", "Leupold BackCountry Cross-Slot"),
    ("196261017816", "100% Racetrap Sunglasses"),
    ("014717391733", "Camco Hose Adapter"),
    ("196261003765", "100% Aircraft Bike Helmet"),
    ("195363230277", "Carve Designs Women's Swim Skirt"),
    ("190665173376", "Dr Martens 1460 WinterGrip Boots"),
    ("45468425545", "Aetrex Women's Wedge (size variant)"),
    ("191972541407", "Fox Racing Ranger Glove"),
    ("196261017069", "100% Speedcraft Sunglasses (variant)"),
    ("29402037773", "Cannon Uni-Troll 5"),
    ("30317011857", "Leupold BackCountry Cross-Slot 20-MOA"),
    ("854149008614", "Accent Paddles Hero Angler"),
    ("614996006436", "Hot Chillys Men's Clima-Tek Crew"),
    ("623555673156", "Arc'teryx Mantis 1 Waist Pack"),
    ("014717395137", "Camco 3\" Waste Valve"),
    ("191972604706", "Fox Racing Ranger Short with Liner"),
    ("081483823102", "Lifetime Fathom 10 Paddle Board"),
    ("623555677505", "Arc'teryx Beta AR Jacket (variant)"),
    ("196870083486", "Cannondale Quick CX 1"),
    ("196261033489", "100% Speedcraft HiPER Sunglasses"),
    ("048515048841", "Acme Tackle Lure"),
    ("675595807978", "ActionHeat Battery Heated Socks"),
]

POSTAL_CODE = '78210'  # Optional; set to None to skip localization


def chunked(lst: List[str], n: int) -> List[List[str]]:
    return [lst[i:i+n] for i in range(0, len(lst), n)]


def main():
    api = WalmartAPIClient()

    gtins = [gtin for gtin, _ in TEST_PRODUCTS]

    found: Dict[str, Dict] = {}
    missing: List[str] = []

    # Batch in groups (keep URLs reasonable)
    for batch in chunked(gtins, 20):
        print(f"🔎 Looking up UPCs (batch size {len(batch)}): {batch[0]}..{batch[-1]}")
        res = api.get_items_by_upc(batch, postal_code=POSTAL_CODE)
        if not res.get('success'):
            print(f"  ⚠️ Batch failed: {res.get('error')[:200]}")
            # Fallback: try individually
            for upc in batch:
                r1 = api.get_items_by_upc([upc], postal_code=POSTAL_CODE)
                if r1.get('success') and r1['data'].get('items'):
                    # pick exact UPC
                    items = [it for it in r1['data']['items'] if str(it.get('upc')) == upc]
                    if items:
                        found[upc] = items[0]
                    else:
                        missing.append(upc)
                else:
                    missing.append(upc)
            continue

        items = res['data'].get('items') or []
        # Index by UPC (multiple may return; choose first)
        for it in items:
            upc_val = str(it.get('upc')) if it.get('upc') is not None else None
            if upc_val and upc_val not in found:
                found[upc_val] = it

        # Mark those not present in this response
        for upc in batch:
            if upc not in found:
                missing.append(upc)

    # Print results in the same order as TEST_PRODUCTS
    print("\n" + "="*70)
    print("📊 Exact UPC/GTIN lookup results")
    print("="*70)
    found_count = 0
    for upc, name in TEST_PRODUCTS:
        rec = found.get(upc)
        if rec:
            found_count += 1
            print(f"✅ {name} (UPC {upc})")
            print(f"   Walmart ID: {rec.get('itemId')}")
            print(f"   Price: ${rec.get('salePrice')} (MSRP: ${rec.get('msrp')})")
            print(f"   Availability @ {POSTAL_CODE}: stock={rec.get('stock')}, availableOnline={rec.get('availableOnline')}")
            print(f"   Seller: marketplace={rec.get('marketplace')}, fulfilledByWalmart={rec.get('fulfilledByWalmart')}\n")
        else:
            print(f"❌ Not found: {name} (UPC {upc})")

    print("-"*70)
    print(f"Exact UPC matches: {found_count}/{len(TEST_PRODUCTS)}")


if __name__ == '__main__':
    main()
