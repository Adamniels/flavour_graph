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
import networkx as nx
from typing import List
from models import Weight
from models import IndexedPriorityList


def setup_graph() -> nx.DiGraph:
    """Top level setup: create and populate the graph."""
    G = nx.DiGraph()
    read_in_products_information(G)
    fill_in_sales_information(G)
    return G


def read_in_products_information(G: nx.DiGraph):
    """Add product nodes with attributes to the graph.
    
    In a real app this would read from a DB / CSV / API.
    """
    products = [
        ("cola", {"prio": 10, "tags": ["soda", "sweet"], "ingredients": ["water", "sugar", "cola_oil"]}),
        ("diet_cola", {"prio": 8, "tags": ["soda", "diet"], "ingredients": ["water", "aspartame"]}),
        ("orange_juice", {"prio": 7, "tags": ["juice", "citrus"], "ingredients": ["orange", "water"]}),
        ("lemonade", {"prio": 6, "tags": ["citrus", "sweet"], "ingredients": ["lemon", "sugar", "water"]}),
        ("sprite", {"prio": 9, "tags": ["soda", "citrus"], "ingredients": ["water", "sugar", "lemon", "lime"]}),
        ("water", {"prio": 5, "tags": ["plain", "healthy"], "ingredients": ["water"]}),
    ]
    
    for product_id, attrs in products:
        G.add_node(product_id, **attrs)


def fill_in_sales_information(G: nx.DiGraph):
    """Compute and add weighted edges between all product pairs based on similarity."""
    nodes = list(G.nodes(data=True))
    
    for i, (node_id, node_data) in enumerate(nodes):
        for j, (other_id, other_data) in enumerate(nodes):
            if i == j:
                continue
            
            # Calculate similarities
            ing_shared = len(set(node_data['ingredients']) & set(other_data['ingredients']))
            tag_shared = len(set(node_data['tags']) & set(other_data['tags']))
            user_match = float(tag_shared) * 0.2  # placeholder for co-purchase data
            
            # Create Weight and add edge with attributes
            weight = Weight(
                ingredient_match=float(ing_shared),
                user_match=user_match,
                tag_match=float(tag_shared)
            )
            
            # Add edge with all weight attributes
            G.add_edge(node_id, other_id, **weight.to_dict())


def generate(antal: int, G: nx.DiGraph = None, priorityList: IndexedPriorityList = None) -> List[str]:
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
    
    if priorityList is None:
        #throw error 
        return ValueError("priorityList cannot be None")
    
    selected = []

    for _ in antal:
        #sort 
        priorityList.sort(reverse=True)
        # pick top
        highest_prio_id = priorityList.ids()[0]
        # get all node_ids neighbouring highest prio_id
        neighbors = list(G.neighbors(highest_prio_id))
        for neighbor in neighbors:
            priorityList.half_prio(neighbor) # half prio of neighbors
        selected.append(highest_prio_id) # add to selected

    # Sort nodes by priority (descending)
    priorityList.sort(reverse=True)

    return selected # en lista med nycklar till grafnoderna



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
