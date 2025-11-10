"""Convert sales data to product co-occurrence patterns.

Analyzes customer purchase data and creates a JSON file showing which products
are frequently bought together.
"""
import pandas as pd
import json
from collections import defaultdict
from itertools import combinations

def analyze_product_cooccurrence(parquet_path: str, output_path: str = 'product_relations.json'):
    """Analyze product co-occurrence from sales data.
    
    Args:
        parquet_path: Path to the sales parquet file
        output_path: Path to save the JSON output
    """
    print(f"📂 Reading sales data from: {parquet_path}")
    
    # Read parquet file
    df = pd.read_parquet(parquet_path)
    
    print(f"📊 Total rows: {len(df)}")
    print(f"🔑 Columns: {list(df.columns)}")
    
    # Detect column names (handle variations)
    customer_col = None
    ean_col = None
    
    for col in df.columns:
        col_lower = col.lower()
        if 'customer' in col_lower or 'cust' in col_lower:
            customer_col = col
        if 'ean' in col_lower:
            ean_col = col
    
    if not customer_col or not ean_col:
        print(f"❌ Could not find customer/ean columns. Available: {list(df.columns)}")
        return
    
    # Filter out rows with missing EAN codes
    rows_before = len(df)
    df = df[df[ean_col].notna()]
    rows_after = len(df)
    print(f"🔍 Filtered out {rows_before - rows_after} rows with missing EAN codes")
    
    # Add leading zero to EAN codes and convert to string
    df['ean_formatted'] = '0' + df[ean_col].astype(int).astype(str)
    product_col = 'ean_formatted'
    
    print(f"✅ Using columns: Customer={customer_col}, Product=EAN (formatted with leading 0)")
    
    # Group products by customer
    customer_products = df.groupby(customer_col)[product_col].apply(list).to_dict()
    print(f"👥 Unique customers: {len(customer_products)}")
    
    # Count co-occurrences
    product_cooccurrence = defaultdict(lambda: defaultdict(int))
    
    for customer_id, products in customer_products.items():
        # Get unique products per customer
        unique_products = list(set(products))
        
        # For each pair of products bought together
        for prod1, prod2 in combinations(unique_products, 2):
            product_cooccurrence[prod1][prod2] += 1
            product_cooccurrence[prod2][prod1] += 1
    
    print(f"🛍️  Unique products: {len(product_cooccurrence)}")
    
    # Create JSON structure
    product_relations = {}
    
    for product, related_products in product_cooccurrence.items():
        # Sort by co-purchase count (highest first)
        sorted_relations = sorted(
            related_products.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        product_relations[product] = {
            "related_products": [
                {
                    "product": rel_prod,
                    "co_purchase_count": count
                }
                for rel_prod, count in sorted_relations
            ]
        }
    
    # Save to JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(product_relations, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ File '{output_path}' created successfully!")
    print(f"📊 Products analyzed: {len(product_relations)}")
    
    # Show examples
    print("\n🔍 Example product relationships (top 3 products):")
    for i, (product, data) in enumerate(list(product_relations.items())[:3]):
        print(f"\n{product}:")
        top_related = data['related_products'][:5]
        for rel in top_related:
            print(f"  → {rel['product']}: {rel['co_purchase_count']} customers bought both")
        if i >= 2:
            break
    
    return product_relations


if __name__ == "__main__":
    # Path to sales data
    sales_file = '/Users/viktorliljenberg/Downloads/data/Sales_2025.parquet'
    output_file = '/Users/viktorliljenberg/Desktop/dev/flavour_graph/data/product_relations.json'
    
    analyze_product_cooccurrence(sales_file, output_file)
