"""Core functionality for flavour graph.

This package contains the core graph construction and product selection logic:

Modules:
- graph_setup: High-level graph creation and priority list setup
- selection: Product selection algorithm with penalty propagation
- data_loaders: File I/O for products, sales, subcategories
- parsers: Text parsing utilities for ingredients and EANs
- edge_weights: Similarity calculations for graph edges
- connections: Graph connection functions (subcategory, ingredient)
- models: Data classes (Weight, IndexedPriorityList, etc.)
- subcategory_colors: Color mapping for visualization
"""
# High-level orchestration
from .graph_setup import setup_graph, create_priority_list_from_sales

# Selection algorithm
from .selection_algorithm import generate

# Data models
from .models import Weight, IndexedPriorityList

# Visualization utilities
from .subcategory_colors import get_subcategory_color, create_subcategory_colormap

# Data loading (often needed for custom workflows)
from .data_loaders import load_product_data, load_subcategories, load_sales_data, load_copurchase_relations

# Weight calculations (for custom similarity metrics)
from .edge_weights import calculate_ingredient_similarity, calculate_tag_similarity, calculate_copurchase_weight

__all__ = [
    # Main entry points
    'setup_graph',
    'create_priority_list_from_sales',
    'generate',
    
    # Data models
    'Weight',
    'IndexedPriorityList',
    
    # Visualization
    'get_subcategory_color',
    'create_subcategory_colormap',
    
    # Data loading
    'load_product_data',
    'load_subcategories',
    'load_sales_data',
    'load_copurchase_relations',
    
    # Weight calculations
    'calculate_ingredient_similarity',
    'calculate_tag_similarity',
    'calculate_copurchase_weight',
]
