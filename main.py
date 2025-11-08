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
import re


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


def setup_graph() -> nx.DiGraph:
    """Top level setup: create and populate the graph."""
    G = nx.DiGraph()
    read_in_products_information(G)
    fill_in_sales_information(G)
    return G


def read_in_products_information(G: nx.DiGraph):
    """Add product nodes with attributes to the graph.
    
    Reads product data from data/products.json and extracts:
    - gpcCategoryCode.name as a string
    - fullIngredientStatement as a list (parsed from ingredientStatement)
    """
    # Get the path to the products.json file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    products_file = os.path.join(script_dir, "data", "products.json")
    
    # Read the JSON file
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
        # First check if fullIngredientStatement exists, otherwise parse ingredientStatement
        full_ingredient_statement = []
        if 'fullIngredientStatement' in product:
            # If it's already a list of tuples, use it directly
            if isinstance(product['fullIngredientStatement'], list):
                full_ingredient_statement = product['fullIngredientStatement']
            # If it's a string, parse it
            elif isinstance(product['fullIngredientStatement'], str):
                full_ingredient_statement = _parse_ingredients(product['fullIngredientStatement'])
        elif 'ingredientStatement' in product and product['ingredientStatement']:
            # Parse ingredientStatement string into tuples
            full_ingredient_statement = _parse_ingredients(product['ingredientStatement'])
        
        # Add node with attributes
        # Using the existing structure: prio, tags, ingredients
        # We'll store gpcCategoryName and fullIngredientStatement as additional attributes
        attrs = {
            'prio': 5,  # Default priority, can be adjusted
            'tags': [gpc_category_name] if gpc_category_name else [],
            'ingredients': full_ingredient_statement,
            'gpcCategoryName': gpc_category_name,
            'fullIngredientStatement': full_ingredient_statement
        }
        
        G.add_node(product_id, **attrs)


def fill_in_sales_information(G: nx.DiGraph):
    """Compute and add weighted edges between all product pairs based on similarity."""
    nodes = list(G.nodes(data=True))
    
    for i, (node_id, node_data) in enumerate(nodes):
        for j, (other_id, other_data) in enumerate(nodes):
            if i == j:
                continue
            
            # Calculate similarities
            # Extract ingredient names from tuples (name, quantity) for comparison
            node_ing_names = {ing[0] for ing in node_data.get('ingredients', []) if isinstance(ing, tuple)}
            other_ing_names = {ing[0] for ing in other_data.get('ingredients', []) if isinstance(ing, tuple)}
            ing_shared = len(node_ing_names & other_ing_names)
            tag_shared = len(set(node_data.get('tags', [])) & set(other_data.get('tags', [])))
            user_match = float(tag_shared) * 0.2  # placeholder for co-purchase data
            
            # Create Weight and add edge with attributes
            weight = Weight(
                ingredient_match=float(ing_shared),
                user_match=user_match,
                tag_match=float(tag_shared)
            )
            
            # Add edge with all weight attributes
            G.add_edge(node_id, other_id, **weight.to_dict())


def generate(antal: int, G: nx.DiGraph = None) -> List[str]:
    """Select `antal` products to populate a vending machine.
    
    Current strategy: pick top-N by `prio` attribute.
    Can be extended to use graph algorithms (PageRank, centrality, etc.)
    
    Args:
        antal: Number of products to select
        G: NetworkX graph (if None, creates a new one)
        
    Returns:
        List of product IDs selected
    """
    if G is None:
        G = setup_graph()
    
    # Sort nodes by priority (descending)
    sorted_nodes = sorted(
        G.nodes(data=True),
        key=lambda x: x[1].get('prio', 0),
        reverse=True
    )
    
    # Select top antal
    selected = [node_id for node_id, _ in sorted_nodes[:max(0, int(antal))]]
    return selected


if __name__ == "__main__":
    # Demo: create graph and show structure
    G = setup_graph()
    
    print(f"Flavour Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges\n")
    
    print("Products (nodes):")
    for node_id, attrs in G.nodes(data=True):
        print(f"  {node_id:15s} prio={attrs['prio']:2d}  tags={attrs['tags']}")
    
    print("\nTop connections (edges with weight > 1.0):")
    for src, dst, attrs in G.edges(data=True):
        if attrs['weight'] > 1.0:
            print(f"  {src:15s} -> {dst:15s}  weight={attrs['weight']:.1f} "
                  f"(ing={attrs['ingredient_match']:.0f}, tag={attrs['tag_match']:.0f})")
    
    print("\nGenerated selection (top 4 by prio):")
    selected = generate(4, G)
    for product_id in selected:
        prio = G.nodes[product_id]['prio']
        print(f"  - {product_id} (prio={prio})")
