"""Data loading utilities for the flavour graph.

Functions for reading product data, sales data, and subcategories from files.
"""
import json
import pandas as pd
import networkx as nx
from pathlib import Path
from typing import Dict
from .parsers import parse_ingredients, extract_product_name
from src.config import (
    PRODUCTS_FILE, 
    PRODUCTS_PARQUET, 
    SALES_FILE, 
    RELATIONS_FILE
)


def load_product_data(json_path: Path = None) -> list:
    """Load product data from JSON file.
    
    Args:
        json_path: Path to products JSON file (default: from config.PRODUCTS_FILE)
        
    Returns:
        List of product dictionaries
    """
    if json_path is None:
        json_path = PRODUCTS_FILE
    if json_path is None:
        json_path = PRODUCTS_FILE
    
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_subcategories(parquet_path: Path = None) -> Dict[str, str]:
    """Load EAN to subcategory mapping from parquet file.
    
    Args:
        parquet_path: Path to products parquet file (default: from config.PRODUCTS_PARQUET)
        
    Returns:
        Dictionary mapping EAN (14-digit string) to subcategory name
    """
    if parquet_path is None:
        parquet_path = PRODUCTS_PARQUET
    
    df_products = pd.read_parquet(parquet_path)
    
    # Create a mapping from EAN to subcategory
    # Normalize EANs: parquet has float, JSON has string with leading zeros
    ean_to_subcategory = {}
    for _, row in df_products.iterrows():
        if pd.notna(row['ean']):
            # Convert to int then to string with leading zeros (14 digits)
            ean_normalized = str(int(row['ean'])).zfill(14)
            ean_to_subcategory[ean_normalized] = row.get('subcategory', 'Unknown')
    
    print(f"Loaded {len(ean_to_subcategory)} subcategories from products.parquet")
    return ean_to_subcategory


def load_sales_data(sales_path: Path = None) -> pd.DataFrame:
    """Load sales data from parquet file.
    
    Args:
        sales_path: Path to sales parquet file (default: from config.SALES_FILE)
        
    Returns:
        DataFrame with sales data
    """
    if sales_path is None:
        sales_path = SALES_FILE
    
    print(f"Reading sales data from {sales_path}...")
    return pd.read_parquet(sales_path)

def add_product_nodes(G: nx.DiGraph):
    """Add product nodes with attributes to the graph.
    
    Reads product data from data/products.json for ingredients and names,
    and data/products.parquet for subcategories.
    
    Args:
        G: NetworkX graph to populate with nodes
    """
    # Load subcategories first
    ean_to_subcategory = load_subcategories()
    
    # Load product data
    products_data = load_product_data()
    
    # Process each product
    for product in products_data:
        # Extract product ID (using gtin or id as identifier)
        product_id = product.get('gtin', product.get('id', ''))
        if not product_id:
            continue
        
        # Extract gpcCategoryCode.name as a string
        gpc_category_name = ""
        if 'gpcCategoryCode' in product and product['gpcCategoryCode']:
            gpc_category_name = product['gpcCategoryCode'].get('name', '')
        
        # Extract fullIngredientStatement as a list of tuples (name, quantity)
        full_ingredient_statement = []
        if 'fullIngredientStatement' in product:
            if isinstance(product['fullIngredientStatement'], list):
                full_ingredient_statement = product['fullIngredientStatement']
            elif isinstance(product['fullIngredientStatement'], str):
                full_ingredient_statement = parse_ingredients(product['fullIngredientStatement'])
        elif 'ingredientStatement' in product and product['ingredientStatement']:
            full_ingredient_statement = parse_ingredients(product['ingredientStatement'])
        
        # Extract product name
        product_name = extract_product_name(product)
        
        # Get subcategory from parquet data
        subcategory = ean_to_subcategory.get(product_id, 'Unknown')
        
        # Build tags list - subcategory is NOT a tag, it's a separate attribute
        tags = []
        if gpc_category_name:
            tags.append(gpc_category_name)
        
        # Add node with attributes including subcategory
        attrs = {
            'prio': 5,
            'tags': tags,
            'ingredients': full_ingredient_statement,
            'gpcCategoryName': gpc_category_name,
            'fullIngredientStatement': full_ingredient_statement,
            'name': product_name,
            'subcategory': subcategory  # Separate attribute, not a tag
        }
        
        G.add_node(product_id, **attrs)


def load_copurchase_relations(json_path: str = None) -> Dict[str, dict]:
    """Load co-purchase relations from JSON file.
    
    This file contains information about which products are frequently
    bought together, generated from sales transaction data.
    
    Args:
        json_path: Path to product_relations.json (default: data/product_relations.json)
        
    Returns:
        Dictionary mapping EAN -> {related_products: [{product: EAN, co_purchase_count: int}]}
        
    Example:
        >>> relations = load_copurchase_relations()
        >>> relations['07310350118342']['related_products'][0]
        {'product': '07310240058449', 'co_purchase_count': 145}
    """
    if json_path is None:
        json_path = RELATIONS_FILE
    
    relations = {}
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            relations = json.load(f)
        print(f"✅ Loaded co-purchase data for {len(relations)} products from {json_path.name}")
    except FileNotFoundError:
        print(f"⚠️ Warning: {json_path} not found. Co-purchase weights will be 0.")
    
    return relations
