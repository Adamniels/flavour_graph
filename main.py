"""Flavour graph using NetworkX.

This module uses NetworkX to represent products as nodes with attributes:
 - prio: integer priority
 - tags: list of strings
 - ingredients: list of strings

Edges represent relationships with weight attributes:
 - ingredient_match: overlap in ingredients
 - user_match: historical co-purchase data
 - tag_match: overlap in tags
 - weight: combined score
"""
import json
import os
import networkx as nx
from typing import List, Tuple
from models import Weight
from models import IndexedPriorityList
import re
import pandas as pd


def _parse_ingredients(ingredient_statement: str) -> List[Tuple[str, float]]:
    """Parse ingredient statement into a list of tuples (name: str, quantity: float).
    
    Extracts ingredient names and quantities (including percentages) from the statement.
    If no quantity is found, defaults to 0.0.
    
    Args:
        ingredient_statement: Raw ingredient statement string
        
    Returns:
        List of tuples (ingredient_name, quantity) where quantity is a float
    """
    # Remove common prefixes like "Ingredienser:" or "Ingredients:"
    if ':' in ingredient_statement:
        ingredient_statement = ingredient_statement.split(':', 1)[1]
    
    # Split by commas, but be careful not to split on commas inside parentheses
    # We'll use a regex to split on commas that are not inside parentheses
    ingredients = []
    
    # Find all commas that are not inside parentheses
    # This is a simplified approach: split by comma, but check if we're inside parentheses
    parts = []
    current = ""
    paren_depth = 0
    
    for char in ingredient_statement:
        if char == '(':
            paren_depth += 1
            current += char
        elif char == ')':
            paren_depth -= 1
            current += char
        elif char == ',' and paren_depth == 0:
            # This comma is a separator, not inside parentheses
            parts.append(current.strip())
            current = ""
        else:
            current += char
    
    # Add the last part
    if current.strip():
        parts.append(current.strip())
    
    # Process each ingredient part
    for ing in parts:
        if not ing:
            continue
        
        # Try to extract quantity from parentheses
        # Pattern: ingredient (quantity) or ingredient (percentage%)
        # Examples: "kokosflingor (4,6%)", "taurin (0,4 %)", "russin (13%)"
        quantity = 0.0
        name = ing
        
        # Look for parentheses with numbers/percentages
        paren_match = re.search(r'\(([^)]+)\)', ing)
        if paren_match:
            content = paren_match.group(1).strip()
            
            # Check if it's a percentage or quantity
            # Pattern: number with optional comma as decimal separator, optional %
            # Examples: "4,6%", "0,4 %", "13%", "4.6%"
            # Match numbers with comma or dot as decimal separator
            qty_match = re.search(r'(\d+[,.]?\d*)\s*%?', content)
            if qty_match:
                qty_str = qty_match.group(1)
                # Replace comma with dot for float conversion
                qty_str = qty_str.replace(',', '.')
                try:
                    quantity = float(qty_str)
                except ValueError:
                    quantity = 0.0
                
                # Remove the parentheses content from the name
                name = re.sub(r'\s*\([^)]+\)', '', ing).strip()
            else:
                # Parentheses contain non-quantity info, keep it in the name
                name = ing
        else:
            # No parentheses, just the ingredient name
            name = ing
        
        # Clean up the name (remove extra whitespace)
        name = ' '.join(name.split())
        
        if name:  # Only add if we have a name
            ingredients.append((name, quantity))
    
    return ingredients


def setup_graph(min_edge_weight: float = 5.0) -> nx.DiGraph:
    """Top level setup: create and populate the graph.
    
    Args:
        min_edge_weight: Minimum weight threshold for creating edges (default: 5.0)
    """
    G = nx.DiGraph()
    read_in_products_information(G)
    fill_in_sales_information(G, min_weight_threshold=min_edge_weight)
    
    # Add fallback edges for isolated nodes based on category matching
    add_fallback_edges_by_category(G)
    
    return G


def read_in_products_information(G: nx.DiGraph):
    """Add product nodes with attributes to the graph.
    
    Reads product data from data/products.json for ingredients and names,
    and data/products.parquet for subcategories.
    """
    # Get the path to the data files
    script_dir = os.path.dirname(os.path.abspath(__file__))
    products_file = os.path.join(script_dir, "data", "products.json")
    products_parquet = os.path.join(script_dir, "data", "products.parquet")
    
    # Read the parquet file for subcategories
    import pandas as pd
    df_products = pd.read_parquet(products_parquet)
    
    # Create a mapping from EAN to subcategory
    # Normalize EANs: parquet has float, JSON has string with leading zeros
    ean_to_subcategory = {}
    for _, row in df_products.iterrows():
        if pd.notna(row['ean']):
            # Convert to int then to string with leading zeros (14 digits)
            ean_normalized = str(int(row['ean'])).zfill(14)
            ean_to_subcategory[ean_normalized] = row.get('subcategory', 'Unknown')
    
    print(f"Loaded {len(ean_to_subcategory)} subcategories from products.parquet")
    
    # Read the JSON file for detailed product info
    with open(products_file, 'r', encoding='utf-8') as f:
        products_data = json.load(f)
    
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
                full_ingredient_statement = _parse_ingredients(product['fullIngredientStatement'])
        elif 'ingredientStatement' in product and product['ingredientStatement']:
            full_ingredient_statement = _parse_ingredients(product['ingredientStatement'])
        
        # Extract product name
        brand_name = product.get('brandName', '')
        description_short = product.get('descriptionShort', '')
        trade_item_desc = product.get('tradeItemDescription', '')
        
        if brand_name and description_short:
            product_name = f"{brand_name} {description_short}"
        elif description_short:
            product_name = description_short
        elif brand_name:
            product_name = brand_name
        elif trade_item_desc:
            product_name = trade_item_desc
        else:
            product_name = product_id
        
        # Get subcategory from parquet data
        subcategory = ean_to_subcategory.get(product_id, 'Unknown')
        
        # Build tags list including both GPC category and subcategory
        tags = []
        if gpc_category_name:
            tags.append(gpc_category_name)
        if subcategory and subcategory != 'Unknown':
            tags.append(subcategory)  # Add subcategory to tags for matching
        
        # Add node with attributes including subcategory
        attrs = {
            'prio': 5,
            'tags': tags,
            'ingredients': full_ingredient_statement,
            'gpcCategoryName': gpc_category_name,
            'fullIngredientStatement': full_ingredient_statement,
            'name': product_name,
            'subcategory': subcategory  # Keep for coloring
        }
        
        G.add_node(product_id, **attrs)


def create_priority_list_from_sales(G: nx.DiGraph, sales_file: str = None) -> IndexedPriorityList:
    """Create an IndexedPriorityList from sales data.
    
    Reads sales data from parquet file and counts sales per product (by EAN/GTIN).
    Products with more sales get higher priority.
    
    Args:
        G: NetworkX graph containing product nodes
        sales_file: Path to sales parquet file (default: data/Sales_2025.parquet)
        
    Returns:
        IndexedPriorityList with products ranked by sales count
    """
    if sales_file is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        sales_file = os.path.join(script_dir, "data", "Sales_2025.parquet")
    
    print(f"Reading sales data from {sales_file}...")
    df = pd.read_parquet(sales_file)
    
    # Count sales per EAN
    sales_by_ean = df.groupby('ean').size().to_dict()
    print(f"Loaded {len(df)} sales records for {len(sales_by_ean)} unique products")
    
    # Create priority list
    # Match EAN from sales with GTIN in graph nodes
    priority_items = []
    matched_products = 0
    
    for node_id, node_data in G.nodes(data=True):
        # Extract GTIN from node_id (format: "GTIN-ProviderGLN")
        gtin = node_id.split('-')[0] if '-' in node_id else node_id
        
        # Convert GTIN to integer for matching (remove leading zeros)
        try:
            gtin_int = int(gtin)
            sales_count = sales_by_ean.get(gtin_int, 0)
            
            if sales_count > 0:
                matched_products += 1
            
            priority_items.append((node_id, sales_count))
        except ValueError:
            # If GTIN can't be converted to int, use default priority of 0
            priority_items.append((node_id, 0))
    
    print(f"Matched {matched_products} products with sales data out of {G.number_of_nodes()} products in graph")
    
    # Create IndexedPriorityList and sort by sales
    priority_list = IndexedPriorityList(priority_items)
    priority_list.sort(reverse=True)
    
    # Show top 10 products by sales
    print("\nTop 10 products by sales:")
    for i, node_id in enumerate(priority_list.top(10), 1):
        sales = dict(priority_items).get(node_id, 0)
        name = G.nodes[node_id].get('name', node_id)
        print(f"  {i}. {name[:50]:50s} - {sales:,} sales")
    
    return priority_list


def fill_in_sales_information(G: nx.DiGraph, min_weight_threshold: float = 5.0):
    """Compute and add weighted edges between all product pairs based on similarity.
    
    Args:
        G: The graph to add edges to
        min_weight_threshold: Minimum total weight required to create an edge (default: 5.0)
                            Lower values = more edges, higher values = more selective
    """
    nodes = list(G.nodes(data=True))
    edges_added = 0
    edges_skipped = 0
    
    for i, (node_id, node_data) in enumerate(nodes):
        for j, (other_id, other_data) in enumerate(nodes):
            if i == j:
                continue
            
            # Get ingredient lists (tuples of name, quantity)
            ing1 = node_data.get('ingredients', [])
            ing2 = other_data.get('ingredients', [])
            
            # Use the advanced Jaccard-based weight function
            ing_weight = weight_ingredients(ing1, ing2)
            
            # Calculate tag similarity
            tag_shared = len(set(node_data.get('tags', [])) & set(other_data.get('tags', [])))
            tag_match = float(tag_shared)
            
            # User match (placeholder for co-purchase data)
            user_match = float(tag_shared) * 0.2
            
            # Create Weight and add edge with attributes
            weight = Weight(
                ingredient_match=ing_weight,  # Now using advanced Jaccard similarity
                user_match=user_match,
                tag_match=tag_match
            )
            
            # Only add edge if total weight meets threshold
            total_weight = weight.score()
            if total_weight >= min_weight_threshold:
                G.add_edge(node_id, other_id, **weight.to_dict())
                edges_added += 1
            else:
                edges_skipped += 1
    
    print(f"Added {edges_added} edges (skipped {edges_skipped} weak connections with weight < {min_weight_threshold})")


def add_fallback_edges_by_category(G: nx.DiGraph, min_connections: int = 5):
    """Add edges for nodes with few connections by connecting them with products in the same category.
    
    This ensures products in the same subcategory (e.g., different chips) 
    get connected even if they don't share ingredients.
    Strategy:
    1. Find all nodes with fewer than min_connections outgoing edges
    2. For each such node, find other products with the same subcategory or tags
    3. Create connections to reach at least min_connections products in the same category
    
    Args:
        G: NetworkX directed graph
        min_connections: Minimum number of connections a node should have (default: 5)
    """
    nodes = list(G.nodes(data=True))
    edges_added = 0
    nodes_processed = 0
    
    print(f"\nAdding fallback edges for nodes with < {min_connections} connections based on category...")
    
    for node_id, node_data in nodes:
        # Only process nodes with fewer than min_connections outgoing edges
        current_connections = G.out_degree(node_id)
        if current_connections >= min_connections:
            continue
        
        nodes_processed += 1
        node_subcategory = node_data.get('subcategory', 'Unknown')
        node_tags = set(node_data.get('tags', []))
        
        # Calculate how many more connections we need
        connections_needed = min_connections - current_connections
        
        # Find potential connections in the same category
        category_matches = []
        
        for other_id, other_data in nodes:
            if node_id == other_id:
                continue
            
            # Skip if edge already exists
            if G.has_edge(node_id, other_id):
                continue
            
            other_subcategory = other_data.get('subcategory', 'Unknown')
            other_tags = set(other_data.get('tags', []))
            
            # Check if they share subcategory or tags
            same_subcategory = (node_subcategory != 'Unknown' and 
                              node_subcategory == other_subcategory)
            shared_tags = len(node_tags & other_tags)
            
            if same_subcategory or shared_tags > 0:
                # Calculate weights
                ing1 = node_data.get('ingredients', [])
                ing2 = other_data.get('ingredients', [])
                ing_weight = weight_ingredients(ing1, ing2)
                
                # Give extra weight for same subcategory
                tag_match = float(shared_tags)
                if same_subcategory:
                    tag_match += 2.0  # Bonus for same subcategory
                
                user_match = float(shared_tags) * 0.2
                
                weight = Weight(
                    ingredient_match=ing_weight,
                    user_match=user_match,
                    tag_match=tag_match
                )
                
                total_weight = weight.score()
                
                # Store with priority (same subcategory gets higher priority)
                priority = 2 if same_subcategory else 1
                category_matches.append((other_id, total_weight, priority, weight))
        
        # Sort by priority (same subcategory first) and then by weight
        category_matches.sort(key=lambda x: (x[2], x[1]), reverse=True)
        
        # Connect to enough products to reach min_connections
        connections_to_add = min(connections_needed, len(category_matches))
        for i in range(connections_to_add):
            other_id, total_weight, priority, weight = category_matches[i]
            G.add_edge(node_id, other_id, **weight.to_dict())
            edges_added += 1
    
    print(f"  Processed {nodes_processed} nodes with < {min_connections} connections")
    print(f"  Added {edges_added} fallback edges based on category matching")


def weight_ingredients(ing1: List[tuple[str, float]], ing2: List[tuple[str, float]]) -> float:
    """Calculate advanced ingredient similarity weight between two products.
    
    This function considers both:
    1. Which ingredients are shared (Jaccard similarity)
    2. How similar the amounts are for shared ingredients
    
    Args:
        ing1: List of (ingredient, amount) tuples for product 1
        ing2: List of (ingredient, amount) tuples for product 2
        
    Returns:
        A float weight representing ingredient similarity (0.0 to ~10.0+)
        
    Example:
        ing1 = [("water", 100), ("sugar", 20), ("lemon", 5)]
        ing2 = [("water", 90), ("sugar", 25), ("lime", 5)]
        weight = weight_ingredients(ing1, ing2)  # Returns ~2.5-3.0
    """
    if not ing1 or not ing2:
        return 0.0
    
    # Convert to dictionaries for easier lookup
    dict1 = {ing: amt for ing, amt in ing1}
    dict2 = {ing: amt for ing, amt in ing2}
    
    # Get ingredient sets
    set1 = set(dict1.keys())
    set2 = set(dict2.keys())
    
    # 1. Jaccard similarity: shared / total unique
    shared = set1 & set2
    union = set1 | set2
    jaccard = len(shared) / len(union) if union else 0.0
    
    # 2. Amount similarity for shared ingredients
    # Compare how similar the amounts are using normalized differences
    amount_similarity = 0.0
    if shared:
        for ingredient in shared:
            amt1 = dict1[ingredient]
            amt2 = dict2[ingredient]
            # Normalized difference: 1.0 means identical, 0.0 means very different
            max_amt = max(amt1, amt2)
            min_amt = min(amt1, amt2)
            if max_amt > 0:
                similarity = min_amt / max_amt  # ratio between 0 and 1
                amount_similarity += similarity
        
        amount_similarity /= len(shared)  # average similarity
    
    # 3. Combine metrics
    # Weight: jaccard (0-1) * 5 + shared count (0-N) + amount similarity (0-1) * 3
    base_score = jaccard * 5.0  # Jaccard index weighted
    shared_bonus = len(shared)   # Raw count of shared ingredients
    amount_bonus = amount_similarity * 3.0  # Amount similarity weighted
    
    total_weight = base_score + shared_bonus + amount_bonus
    
    return total_weight

def generate(antal: int, G: nx.DiGraph = None, priorityList: IndexedPriorityList = None) -> List[str]:
    """Select `antal` products to populate a vending machine.
    
    Current strategy: pick top-N by `prio` attribute.
    Can be extended to use graph algorithms (PageRank, centrality, etc.)
    
    Args:
        antal: Number of products to select
        G: NetworkX graph (if None, creates a new one)
        priorityList: IndexedPriorityList (required)
        
    Returns:
        List of product IDs selected
    """
    if G is None:
        G = setup_graph()
    
    if priorityList is None:
        raise ValueError("priorityList cannot be None")
    
    selected = []

    for _ in range(antal):
        # sort 
        priorityList.sort(reverse=True)
        # pick top
        highest_prio_id = priorityList.ids()[0]
        # get all node_ids neighbouring highest prio_id
        neighbors = list(G.neighbors(highest_prio_id))
        for neighbor in neighbors:
            priorityList.half_prio(neighbor) # half prio of neighbors
        selected.append(highest_prio_id) # add to selected
        
        # Remove selected product from priority list so it can't be selected again
        priorityList.remove(highest_prio_id)

    return selected # en lista med nycklar till grafnoderna



if __name__ == "__main__":
    # Test the advanced ingredient weight function
    print("=" * 60)
    print("TESTING ADVANCED INGREDIENT WEIGHT FUNCTION")
    print("=" * 60)
    
    # Test cases
    test_cases = [
        (
            [("water", 100), ("sugar", 20), ("lemon", 5)],
            [("water", 100), ("sugar", 20), ("lemon", 5)],
            "Identical products"
        ),
        (
            [("water", 100), ("sugar", 20), ("lemon", 5)],
            [("water", 90), ("sugar", 25), ("lime", 5)],
            "Similar but different amounts and ingredients"
        ),
        (
            [("water", 100), ("sugar", 20)],
            [("water", 50)],
            "Partial overlap, different amounts"
        ),
        (
            [("cola_oil", 1), ("vanilla", 2)],
            [("orange", 100), ("pulp", 50)],
            "No overlap at all"
        ),
        (
            [("water", 100), ("sugar", 30), ("cola_oil", 2)],
            [("water", 95), ("aspartame", 1)],
            "Cola vs Diet Cola (one shared ingredient)"
        ),
    ]
    
    for ing1, ing2, description in test_cases:
        weight = weight_ingredients(ing1, ing2)
        print(f"\n{description}:")
        print(f"  Product 1: {ing1}")
        print(f"  Product 2: {ing2}")
        print(f"  Weight: {weight:.3f}")
    
    print("\n" + "=" * 60)
    print("GRAPH DEMO")
    print("=" * 60)
    
    # Test with different thresholds to see the effect
    print("\n--- Testing with threshold = 5.0 (more connections) ---")
    G = setup_graph(min_edge_weight=5.0)
    
    print(f"\nFlavour Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges\n")
    
    print("Products (first 10 nodes):")
    for i, (node_id, attrs) in enumerate(G.nodes(data=True)):
        if i >= 10:
            print(f"  ... and {G.number_of_nodes() - 10} more products")
            break
        name = attrs.get('name', node_id)[:50]  # Truncate long names
        print(f"  {name:50s} prio={attrs['prio']:2d}  tags={attrs['tags']}")
    
    print("\nTop connections (edges with weight > 5.0, showing products with names, first 20):")
    count = 0
    for src, dst, attrs in sorted(G.edges(data=True), key=lambda x: x[2]['weight'], reverse=True):
        src_name = G.nodes[src].get('name', src)
        dst_name = G.nodes[dst].get('name', dst)
        
        # Skip if both are just GTINs (no real names)
        if src_name.isdigit() and dst_name.isdigit():
            continue
            
        if attrs['weight'] > 5.0 and count < 20:
            src_display = src_name[:40] if len(src_name) > 40 else src_name
            dst_display = dst_name[:40] if len(dst_name) > 40 else dst_name
            print(f"  {src_display:40s} -> {dst_display:40s}")
            print(f"    weight={attrs['weight']:.1f} (ingredient={attrs['ingredient_match']:.1f}, tag={attrs['tag_match']:.0f}, user={attrs['user_match']:.1f})")
            count += 1
    
    # Create priority list from sales data
    print("\n" + "=" * 60)
    print("CREATING PRIORITY LIST FROM SALES DATA")
    print("=" * 60)
    priority_list = create_priority_list_from_sales(G)
    
    print(f"\n" + "=" * 60)
    print("TESTING GENERATE FUNCTION WITH SALES-BASED PRIORITY")
    print("=" * 60)
    print(f"\nGenerating selection of top 40 products by sales:")
    
    # Save sales data before generate() modifies the priority_list
    sales_dict = {node_id: sales for node_id, sales in priority_list._items}
    
    selected = generate(40, G, priorityList=priority_list)
    
    for i, product_id in enumerate(selected, 1):
        name = G.nodes[product_id].get('name', product_id)
        sales = sales_dict.get(product_id, 0)
        print(f"  {i:2d}. {name[:60]:60s} - {sales:,} sales")
