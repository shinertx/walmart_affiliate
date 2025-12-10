import csv
from collections import Counter

def analyze_export():
    vendors = []
    prices = []
    titles = []
    
    with open('walmart_products_export.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            vendors.append(row['Vendor'])
            try:
                prices.append(float(row['Variant Price']))
            except:
                pass
            titles.append(row['Title'])

    print(f"Total Items: {len(titles)}")
    print(f"Average Price: ${sum(prices)/len(prices):.2f}")
    
    print("\nTop 10 Brands:")
    print(Counter(vendors).most_common(10))
    
    print("\nSample Titles:")
    for t in titles[:5]:
        print(f"- {t}")

if __name__ == "__main__":
    analyze_export()
