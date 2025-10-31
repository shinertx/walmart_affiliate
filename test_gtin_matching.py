#!/usr/bin/env python3
"""
Test GTIN matching against Walmart API
Real GTINs from actual products
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))
from walmart_api import WalmartAPIClient

# Test GTINs
test_products = [
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

def test_gtin_matching():
    """Test matching these GTINs against Walmart"""
    
    api = WalmartAPIClient()
    POSTAL_CODE = '78210'
    
    print("\n" + "="*80)
    print("🔍 TESTING GTIN MATCHING AGAINST WALMART API")
    print("="*80)
    print(f"\nTesting {len(test_products)} GTINs...\n")
    
    matches = []  # all matches
    exact_matches = []  # only exact UPC matches
    partial_matches = []  # non-exact matches
    no_matches = []
    
    for gtin, product_name in test_products:
        print(f"🔎 Searching: {product_name[:40]:<40} (GTIN: {gtin})")
        
        # Try direct UPC/GTIN query first (if endpoint supports it)
        result = api.get_products(count=100, query=gtin)
        
        # If no results from direct query, fall back to brand-based search
        if not (result.get('success') and result['data'].get('items')):
            # Extract brand heuristically (handle common multi-word brands)
            lower_name = (product_name or '').lower()
            brand = None
            if "fox racing" in lower_name:
                brand = "Fox Racing"
            elif "dr martens" in lower_name:
                brand = "Dr. Martens"
            elif "arc'teryx" in lower_name or "arcteryx" in lower_name:
                brand = "Arc'teryx"
            elif "leupold" in lower_name:
                brand = "Leupold"
            elif "camco" in lower_name:
                brand = "Camco"
            elif "lifetime" in lower_name:
                brand = "Lifetime"
            elif "cannondale" in lower_name:
                brand = "Cannondale"
            elif "aetrex" in lower_name:
                brand = "Aetrex"
            elif "actionheat" in lower_name:
                brand = "ActionHeat"
            elif "accent paddles" in lower_name:
                brand = "Accent Paddles"
            elif "hot chillys" in lower_name:
                brand = "Hot Chillys"
            elif "acme" in lower_name:
                brand = "Acme"

            result = api.get_products(brand=brand, count=100) if brand else api.get_products(count=100)
        
        if result['success'] and result['data']['items']:
            walmart_products = result['data']['items']
            
            # Check if UPC matches exactly
            exact_match = None
            for wp in walmart_products:
                if wp.get('upc') == gtin:
                    exact_match = wp
                    break
            
            if exact_match:
                record = {
                    'gtin': gtin,
                    'original_name': product_name,
                    'walmart_name': exact_match.get('name'),
                    'walmart_price': exact_match.get('salePrice'),
                    'walmart_item_id': exact_match.get('itemId'),
                    'confidence': '✅ EXACT UPC MATCH',
                    'stock': exact_match.get('stock'),
                    'availableOnline': exact_match.get('availableOnline'),
                    'marketplace': exact_match.get('marketplace'),
                    'fulfilledByWalmart': exact_match.get('fulfilledByWalmart'),
                    'standardShipRate': exact_match.get('standardShipRate'),
                    'twoThreeDayShippingRate': exact_match.get('twoThreeDayShippingRate'),
                    'overnightShippingRate': exact_match.get('overnightShippingRate'),
                    'shipToStore': exact_match.get('shipToStore'),
                    'freeShipToStore': exact_match.get('freeShipToStore'),
                    'freeShippingOver35Dollars': exact_match.get('freeShippingOver35Dollars'),
                    'msrp': exact_match.get('msrp')
                }
                matches.append(record)
                exact_matches.append(record)
                print(f"  ✅ MATCH FOUND: {exact_match.get('name')[:50]}")
                print(f"     Price: ${exact_match.get('salePrice')} (MSRP: ${exact_match.get('msrp')})")
                print(f"     Walmart ID: {exact_match.get('itemId')}")
                print(f"     Availability: stock={exact_match.get('stock')}, availableOnline={exact_match.get('availableOnline')}")
                print(f"     Seller: marketplace={exact_match.get('marketplace')}, fulfilledByWalmart={exact_match.get('fulfilledByWalmart')}")
                print(f"     Shipping: standard={exact_match.get('standardShipRate')}, 2-3 day={exact_match.get('twoThreeDayShippingRate')}, overnight={exact_match.get('overnightShippingRate')}")
                print(f"     Pickup/Store: shipToStore={exact_match.get('shipToStore')}, freeShipToStore={exact_match.get('freeShipToStore')}, freeShipOver35={exact_match.get('freeShippingOver35Dollars')}\n")
            else:
                # Partial match
                top_result = walmart_products[0]
                record = {
                    'gtin': gtin,
                    'original_name': product_name,
                    'walmart_name': top_result.get('name'),
                    'walmart_price': top_result.get('salePrice'),
                    'walmart_item_id': top_result.get('itemId'),
                    'confidence': '⚠️  PARTIAL MATCH (search result)',
                    'stock': top_result.get('stock'),
                    'availableOnline': top_result.get('availableOnline'),
                    'marketplace': top_result.get('marketplace'),
                    'fulfilledByWalmart': top_result.get('fulfilledByWalmart'),
                    'standardShipRate': top_result.get('standardShipRate'),
                    'twoThreeDayShippingRate': top_result.get('twoThreeDayShippingRate'),
                    'overnightShippingRate': top_result.get('overnightShippingRate'),
                    'shipToStore': top_result.get('shipToStore'),
                    'freeShipToStore': top_result.get('freeShipToStore'),
                    'freeShippingOver35Dollars': top_result.get('freeShippingOver35Dollars'),
                    'msrp': top_result.get('msrp')
                }
                matches.append(record)
                partial_matches.append(record)
                print(f"  ⚠️  PARTIAL: {top_result.get('name')[:50]}")
                print(f"     Price: ${top_result.get('salePrice')} (MSRP: ${top_result.get('msrp')})")
                print(f"     Walmart ID: {top_result.get('itemId')}")
                print(f"     Availability: stock={top_result.get('stock')}, availableOnline={top_result.get('availableOnline')}")
                print(f"     Seller: marketplace={top_result.get('marketplace')}, fulfilledByWalmart={top_result.get('fulfilledByWalmart')}")
                print(f"     Shipping: standard={top_result.get('standardShipRate')}, 2-3 day={top_result.get('twoThreeDayShippingRate')}, overnight={top_result.get('overnightShippingRate')}")
                print(f"     Pickup/Store: shipToStore={top_result.get('shipToStore')}, freeShipToStore={top_result.get('freeShipToStore')}, freeShipOver35={top_result.get('freeShippingOver35Dollars')}\n")
        else:
            no_matches.append({
                'gtin': gtin,
                'original_name': product_name,
                'reason': 'No results found'
            })
            print(f"  ❌ NO MATCH\n")
    
    # Summary
    print("\n" + "="*80)
    print("📊 MATCHING RESULTS SUMMARY")
    print("="*80)
    print(f"\nTotal GTINs Tested: {len(test_products)}")
    print(f"Matches Found: {len(matches)}")
    print(f"No Matches: {len(no_matches)}")
    print(f"Match Rate: {len(matches)/len(test_products)*100:.1f}%")
    print(f"Exact UPC matches: {len(exact_matches)}")
    print(f"Partial matches: {len(partial_matches)}")
    
    if no_matches:
        print(f"\n❌ PRODUCTS WITH NO WALMART MATCH:")
        for product in no_matches:
            print(f"  • {product['original_name']} (GTIN: {product['gtin']})")
    
    return {
        'total_tested': len(test_products),
        'matches': matches,
        'no_matches': no_matches,
        'match_rate': len(matches) / len(test_products)
    }

if __name__ == '__main__':
    results = test_gtin_matching()

    # If we have matches, enrich with ZIP-aware details using item IDs
    if results['matches']:
        api = WalmartAPIClient()
        POSTAL_CODE = '78210'
        item_ids = [m.get('walmart_item_id') for m in results['matches'] if m.get('walmart_item_id')]
        # Deduplicate and ensure ints
        try:
            unique_ids = list({int(i) for i in item_ids})
        except Exception:
            unique_ids = list({i for i in item_ids if i is not None})

        print("\n" + "="*80)
        print(f"📍 ZIP-CODE ENRICHMENT: {POSTAL_CODE}")
        print("="*80)
        print(f"Enriching {len(unique_ids)} matched Walmart items with location-aware details...\n")

        # Chunk requests to avoid very long URLs
        def chunks(lst, n):
            for i in range(0, len(lst), n):
                yield lst[i:i+n]

        enriched: dict[int, dict] = {}
        for batch in chunks(unique_ids, 20):
            resp = api.get_items_by_ids(batch, postal_code=POSTAL_CODE)
            if resp.get('success') and resp['data'].get('items'):
                for it in resp['data']['items']:
                    wid = it.get('itemId')
                    if wid is not None:
                        enriched[wid] = it

        # Print per-match summary with ZIP-aware flags where available
        available_online_count = 0
        walmart_fulfilled_count = 0
        std_ship_free_count = 0
        processed = 0

        for m in results['matches']:
            wid = m.get('walmart_item_id')
            item = enriched.get(wid)
            if not item:
                continue
            processed += 1
            if item.get('availableOnline'):
                available_online_count += 1
            if item.get('fulfilledByWalmart'):
                walmart_fulfilled_count += 1
            if (item.get('standardShipRate') == 0) or (item.get('freeShippingOver35Dollars') is True):
                std_ship_free_count += 1
            print(f"🧭 {m['original_name'][:40]:<40} → Walmart ID {wid}")
            print(f"   Price: ${item.get('salePrice')} (MSRP: ${item.get('msrp')})")
            # Derive shipping speed classification from flags
            overnight = item.get('overnightShippingRate')
            two_three = item.get('twoThreeDayShippingRate')
            standard = item.get('standardShipRate')
            free_over_35 = item.get('freeShippingOver35Dollars')
            if overnight is not None:
                ship_speed = 'overnight available'
            elif two_three is not None:
                ship_speed = '2-3 day available'
            else:
                if standard == 0 or free_over_35 is True:
                    ship_speed = 'standard (likely free)'
                else:
                    ship_speed = 'standard'

            print(f"   Availability (ZIP {POSTAL_CODE}): stock={item.get('stock')}, availableOnline={item.get('availableOnline')} | ship speed: {ship_speed}")
            print(f"   Seller: marketplace={item.get('marketplace')}, fulfilledByWalmart={item.get('fulfilledByWalmart')}")
            print(f"   Shipping: standard={item.get('standardShipRate')}, 2-3 day={item.get('twoThreeDayShippingRate')}, overnight={item.get('overnightShippingRate')}")
            print(f"   Pickup/Store: shipToStore={item.get('shipToStore')}, freeShipToStore={item.get('freeShipToStore')}, freeShipOver35={item.get('freeShippingOver35Dollars')}\n")

        print("-"*80)
        print(f"ZIP {POSTAL_CODE} summary across enriched items:")
        print(f"  Items enriched: {processed}")
        print(f"  Available online: {available_online_count}")
        print(f"  Fulfilled by Walmart: {walmart_fulfilled_count}")
        print(f"  Free or threshold free shipping: {std_ship_free_count}")
