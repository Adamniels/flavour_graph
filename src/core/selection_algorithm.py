"""Product selection algorithm.

Functions for selecting optimal products for a vending machine based on
priority scores and graph-based penalty propagation.
"""
import networkx as nx
from typing import List
from .models import IndexedPriorityList


def generate(antal: int, G: nx.DiGraph = None, priorityList: IndexedPriorityList = None) -> List[str]:
    """Select `antal` products to populate a vending machine.
    
    Uses a greedy algorithm with graph-based penalty propagation:
    1. Sort products by priority (sales-based)
    2. Pick highest priority product
    3. Penalize similar products (neighbors in graph) proportional to edge weight
    4. Repeat until `antal` products selected
    
    This ensures diversity in selection - if we pick a product, similar products
    get penalized so we don't over-select similar items.
    
    Args:
        antal: Number of products to select
        G: NetworkX graph with product relationships (if None, raises ValueError)
        priorityList: IndexedPriorityList with product priorities (required)
        
    Returns:
        List of product IDs selected
        
    Raises:
        ValueError: If priorityList is None or if G is None
        
    Example:
        >>> G = setup_graph()
        >>> priorities = create_priority_list_from_sales()
        >>> selected = generate(antal=20, G=G, priorityList=priorities)
        >>> print(f"Selected {len(selected)} products")
    """
    if G is None:
        raise ValueError("G (graph) cannot be None. Call setup_graph() first.")
    
    if priorityList is None:
        raise ValueError("priorityList cannot be None. Call create_priority_list_from_sales() first.")
    
    # Calculate max weight in the graph for normalization
    # This is used to scale penalties proportionally
    max_weight = 0.0
    for u, v, data in G.edges(data=True):
        weight = data.get('weight', 0.0)
        if weight > max_weight:
            max_weight = weight
    
    print(f"\nMax edge weight in graph: {max_weight:.1f}")
    print(f"Selecting {antal} products using greedy penalty propagation...\n")
    
    selected = []

    for i in range(antal):
        # Sort by priority (highest first)
        priorityList.sort(reverse=True)
        
        # Pick highest priority product
        highest_prio_id = priorityList.ids()[0]
        
        # Get product name for logging
        product_name = G.nodes[highest_prio_id].get('name', highest_prio_id)
        current_prio = priorityList.get_prio(highest_prio_id)
        print(f"{i+1}. Selected: {product_name} (priority: {current_prio:.2f})")
        
        # Get all neighbors (similar products) and penalize them
        neighbors = list(G.neighbors(highest_prio_id))
        penalties_applied = 0
        
        for neighbor in neighbors:
            # Get edge weight - higher weight = stronger similarity = bigger penalty
            edge_data = G.get_edge_data(highest_prio_id, neighbor)
            if edge_data:
                weight = edge_data.get('weight', 0.0)
                # Reduce neighbor's priority proportional to similarity
                priorityList.reduce_prio_by_weight(neighbor, weight, max_weight)
                penalties_applied += 1
        
        if penalties_applied > 0:
            print(f"   → Penalized {penalties_applied} similar products")
        
        # Add to selected list
        selected.append(highest_prio_id)
        
        # Remove selected product from priority list so it can't be selected again
        priorityList.remove(highest_prio_id)

    print(f"\n✓ Selected {len(selected)} products successfully")
    return selected
