"""High-level graph setup and orchestration.

Functions for creating the complete product graph with nodes, edges,
and priority lists from data files.
"""
import networkx as nx
import pandas as pd
from pathlib import Path
from .models import IndexedPriorityList
from .data_loaders import load_product_data, load_subcategories, load_copurchase_relations
from .parsers import parse_ingredients, extract_product_name
from .edge_weights import add_weighted_edges
from .connections import add_subcategory_connections
from src.config import SALES_FILE, DEFAULT_MIN_EDGE_WEIGHT


def _add_product_nodes(G: nx.DiGraph):
    """Add product nodes with attributes to the graph.
    
    Reads product data from data/products.json for ingredients and names,
    and data/products.parquet for subcategories.
    
    Args:
        G: NetworkX graph to populate with nodes
        
    Note:
        This is a private helper function used internally by setup_graph().
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


def setup_graph(min_edge_weight: float = None) -> nx.DiGraph:
    """Create and populate the complete product relationship graph.
    
    This is the main entry point for graph creation. It:
    1. Creates an empty directed graph
    2. Adds product nodes with all attributes
    3. Computes and adds edges based on ingredient/tag/user similarity
    4. Adds subcategory-based connections
    
    Args:
        min_edge_weight: Minimum weight threshold for creating edges (default: from config.DEFAULT_MIN_EDGE_WEIGHT)
                        Higher values = fewer, stronger connections
                        Lower values = more, weaker connections
        
    Returns:
        nx.DiGraph with:
        - Nodes: products with attributes (name, ingredients, tags, subcategory, prio)
        - Edges: weighted connections between similar products
        
    Example:
        >>> G = setup_graph(min_edge_weight=6.0)
        >>> print(f"Graph has {G.number_of_nodes()} products and {G.number_of_edges()} connections")
    """
    print("=" * 60)
    print("SETTING UP PRODUCT GRAPH")
    print("=" * 60)
    
    # Use default from config if not specified
    if min_edge_weight is None:
        min_edge_weight = DEFAULT_MIN_EDGE_WEIGHT
    
    # 1. Create empty graph
    G = nx.DiGraph()
    
    # 2. Add product nodes with attributes from JSON and Parquet files
    print("\n[1/3] Loading product data...")
    _add_product_nodes(G)
    print(f"✓ Added {G.number_of_nodes()} products to graph")
    
    # 3. Compute and add similarity-based edges
    copurchase_relations = load_copurchase_relations()
    print(f"\n[2/3] Computing product similarities (min_weight={min_edge_weight})...")
    add_weighted_edges(G, min_weight_threshold=min_edge_weight, copurchase_relations=copurchase_relations)
    print(f"✓ Added {G.number_of_edges()} similarity-based edges")
    
    # 4. Add subcategory connections (baseline links for products in same category)
    print("\n[3/3] Adding subcategory connections...")
    add_subcategory_connections(G)
    print(f"✓ Final graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    
    print("\n" + "=" * 60)
    print("GRAPH SETUP COMPLETE")
    print("=" * 60 + "\n")
    
    return G


def create_priority_list_from_sales(G: nx.DiGraph, sales_file: Path = None) -> IndexedPriorityList:
    """Create an IndexedPriorityList from sales data.
    
    Reads sales data from parquet file and counts sales per product (by EAN/GTIN).
    Products with more sales get higher priority scores.
    
    This priority list is used by the selection algorithm to favor popular products
    while maintaining diversity through graph-based penalty propagation.
    
    Args:
        G: NetworkX graph containing product nodes
        sales_file: Path to sales parquet file (default: from config.SALES_FILE)
        
    Returns:
        IndexedPriorityList with products ranked by sales count
        - Higher sales count = higher priority
        - Products not in sales data get priority of 0
        
    Example:
        >>> G = setup_graph()
        >>> priorities = create_priority_list_from_sales(G)
        >>> top_products = priorities.top(10)
    """
    # Use config path if not specified
    if sales_file is None:
        sales_file = SALES_FILE
    
    print("=" * 60)
    print("CREATING PRIORITY LIST FROM SALES DATA")
    print("=" * 60)
    
    # Read sales data
    print(f"\nReading sales data from {sales_file.name}...")
    df = pd.read_parquet(sales_file)
    
    # Count sales per EAN (aggregate by product)
    sales_by_ean = df.groupby('ean').size().to_dict()
    print(f"✓ Loaded {len(df):,} sales records")
    print(f"✓ Found {len(sales_by_ean):,} unique products in sales data")
    
    # Match sales data with graph nodes
    priority_items = []
    matched_products = 0
    total_sales = 0
    
    for node_id, node_data in G.nodes(data=True):
        # Extract GTIN from node_id (format: "GTIN-ProviderGLN")
        gtin = node_id.split('-')[0] if '-' in node_id else node_id
        
        # Convert GTIN to integer for matching with EAN (removes leading zeros)
        try:
            gtin_int = int(gtin)
            sales_count = sales_by_ean.get(gtin_int, 0)
            
            if sales_count > 0:
                matched_products += 1
                total_sales += sales_count
            
            priority_items.append((node_id, sales_count))
        except ValueError:
            # If GTIN can't be converted to int, use default priority of 0
            priority_items.append((node_id, 0))
    
    print(f"✓ Matched {matched_products} products ({matched_products/G.number_of_nodes()*100:.1f}% of graph)")
    print(f"✓ Total sales: {total_sales:,}")
    
    # Create IndexedPriorityList and sort by sales (highest first)
    priority_list = IndexedPriorityList(priority_items)
    priority_list.sort(reverse=True)
    
    # Show top 10 products by sales
    print("\nTop 10 products by sales:")
    for i, node_id in enumerate(priority_list.top(10), 1):
        sales = dict(priority_items).get(node_id, 0)
        name = G.nodes[node_id].get('name', node_id)
        # Truncate name if too long
        display_name = name[:50] + "..." if len(name) > 50 else name
        print(f"  {i:2d}. {display_name:50s} - {sales:,} sales")
    
    print("\n" + "=" * 60)
    print("PRIORITY LIST COMPLETE")
    print("=" * 60 + "\n")
    
    return priority_list
