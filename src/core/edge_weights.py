"""Edge weight calculation functions.

Functions for computing similarity weights between products based on
ingredients, tags, and user co-purchase patterns.
"""
import math
import networkx as nx
from typing import List, Tuple, Dict
from .models import Weight


def calculate_ingredient_similarity(ing1: List[Tuple[str, float]], ing2: List[Tuple[str, float]]) -> float:
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
        >>> ing1 = [("water", 100), ("sugar", 20), ("lemon", 5)]
        >>> ing2 = [("water", 90), ("sugar", 25), ("lime", 5)]
        >>> weight_ingredients(ing1, ing2)
        2.8  # Approximate value
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


def calculate_tag_similarity(tags1: List[str], tags2: List[str]) -> float:
    """Calculate tag similarity between two products.
    
    Args:
        tags1: List of tags for product 1
        tags2: List of tags for product 2
        
    Returns:
        Number of shared tags (float)
    """
    return float(len(set(tags1) & set(tags2)))


def calculate_copurchase_weight(ean_1: str, ean_2: str, relations: Dict[str, dict], normalize: bool = True) -> float:
    """Calculate co-purchase similarity weight between two products.
    
    Uses transaction data to determine how often two products are bought together.
    Higher weight = products are frequently purchased in the same transaction.
    
    Args:
        ean_1: First product EAN (e.g. '07310350118342')
        ean_2: Second product EAN
        relations: Co-purchase relations dictionary (from load_copurchase_relations)
        normalize: If True, apply log-scaling to reduce impact of very popular products
        
    Returns:
        Float weight representing co-purchase frequency
        - 0.0 if products are never bought together
        - Higher values for frequently co-purchased products
        - Log-scaled if normalize=True to prevent dominance
        
    Example:
        >>> relations = load_copurchase_relations()
        >>> weight = calculate_copurchase_weight('EAN1', 'EAN2', relations, normalize=True)
        >>> print(f"Co-purchase weight: {weight:.2f}")
    """
    if not relations or ean_1 not in relations:
        return 0.0
    
    # Find ean_2 in ean_1's related products
    for related in relations[ean_1].get('related_products', []):
        if related['product'] == ean_2:
            count = related['co_purchase_count']
            
            if normalize:
                # Log-scale to prevent very popular products dominating
                # +1 to avoid log(0)
                return math.log(count + 1)
            else:
                return float(count)
    
    return 0.0


def calculate_tag_similarity(tags1: List[str], tags2: List[str]) -> float:
    """Calculate tag similarity between two products.
    
    Args:
        tags1: List of tags for product 1
        tags2: List of tags for product 2
        
    Returns:
        Number of shared tags (float)
    """
    return float(len(set(tags1) & set(tags2)))


def add_weighted_edges(G: nx.DiGraph, min_weight_threshold: float = 4.0, copurchase_relations: Dict[str, dict] = None):
    """Compute and add weighted edges between all product pairs based on similarity.
    
    Creates edges between products based on:
    - Ingredient similarity (Jaccard + amount matching)
    - Tag overlap
    - User co-purchase patterns
    
    Only creates an edge if the total weight meets the threshold.
    
    Args:
        G: The graph to add edges to
        min_weight_threshold: Minimum total weight required to create an edge (default: 4.0)
                            Lower values = more edges, higher values = more selective
        copurchase_relations: Co-purchase data dictionary (optional, loaded if None)
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
            ing_weight = calculate_ingredient_similarity(ing1, ing2)
            
            # Calculate tag similarity
            tag_match = calculate_tag_similarity(
                node_data.get('tags', []),
                other_data.get('tags', [])
            )
            
            # User match using co-purchase data
            user_match = calculate_copurchase_weight(node_id, other_id, copurchase_relations, normalize=True)
            
            # Create Weight and add edge with attributes
            weight = Weight(
                ingredient_match=ing_weight,
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
