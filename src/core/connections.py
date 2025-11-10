"""Graph connection functions.

Functions for creating edges between products in the graph based on
various relationships (subcategories, ingredients, etc.).
"""
import networkx as nx
from .models import Weight

def add_subcategory_connections(G: nx.DiGraph, edge_weight: float = 0.5):
    """Connect all products within the same subcategory with a base weight.
    
    This creates a baseline connection between products in the same category,
    representing that they are substitutable or comparable products.
    
    Args:
        G: The graph to add edges to
        edge_weight: The weight to assign to subcategory connections (default: 0.5)
    """
    # Group nodes by subcategory
    subcategory_groups = {}
    for node_id, node_data in G.nodes(data=True):
        subcat = node_data.get('subcategory', 'Unknown')
        if subcat not in subcategory_groups:
            subcategory_groups[subcat] = []
        subcategory_groups[subcat].append((node_id, node_data))
    
    # Connect all products within each subcategory
    total_edges = 0
    for subcat, products in subcategory_groups.items():
        if len(products) < 2:
            continue
        
        # Connect each product to every other product in the same subcategory
        for i, (node_id, node_data) in enumerate(products):
            for j, (other_id, other_data) in enumerate(products):
                if i >= j:  # Avoid duplicates and self-edges
                    continue
                
                # Get or update existing edge
                if G.has_edge(node_id, other_id):
                    # Edge exists, increment the weight
                    edge_data = G[node_id][other_id]
                    weight = Weight(
                        ingredient_match=edge_data.get('ingredient_match', 0.0),
                        user_match=edge_data.get('user_match', 0.0),
                        tag_match=edge_data.get('tag_match', 0.0) + edge_weight
                    )
                    G.add_edge(node_id, other_id, **weight.to_dict())
                else:
                    # Create new edge
                    weight = Weight(
                        ingredient_match=0.0,
                        user_match=0.0,
                        tag_match=edge_weight
                    )
                    G.add_edge(node_id, other_id, **weight.to_dict())
                    total_edges += 1
                
                # Add reverse edge
                if G.has_edge(other_id, node_id):
                    edge_data = G[other_id][node_id]
                    weight = Weight(
                        ingredient_match=edge_data.get('ingredient_match', 0.0),
                        user_match=edge_data.get('user_match', 0.0),
                        tag_match=edge_data.get('tag_match', 0.0) + edge_weight
                    )
                    G.add_edge(other_id, node_id, **weight.to_dict())
                else:
                    weight = Weight(
                        ingredient_match=0.0,
                        user_match=0.0,
                        tag_match=edge_weight
                    )
                    G.add_edge(other_id, node_id, **weight.to_dict())
    
    print(f"Added {total_edges} subcategory connections (weight={edge_weight})")
