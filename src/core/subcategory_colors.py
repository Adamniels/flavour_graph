"""
Color mapping for product subcategories.
Reads colors dynamically from data/Subcategories.xlsx.
"""
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import pandas as pd
import os

# Cache for loaded colors
_SUBCATEGORY_COLORS_CACHE = None

def load_subcategory_colors(excel_path: str = None) -> dict:
    """Load subcategory colors from Excel file.
    
    Args:
        excel_path: Path to the Subcategories.xlsx file (optional, auto-detects)
        
    Returns:
        dict: mapping from subcategory_name to color hex code
    """
    global _SUBCATEGORY_COLORS_CACHE
    
    # Return cached colors if already loaded
    if _SUBCATEGORY_COLORS_CACHE is not None:
        return _SUBCATEGORY_COLORS_CACHE
    
    # Auto-detect path if not provided
    if excel_path is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(script_dir))
        excel_path = os.path.join(project_root, 'data', 'Subcategories.xlsx')
    
    try:
        df = pd.read_excel(excel_path)
        colors = {}
        
        # Load colors from Excel
        for _, row in df.iterrows():
            subcategory = row['subcategory_name']
            color = row['color']
            colors[subcategory] = color
        
        # Add fallback color
        colors['Unknown'] = '#808080'
        
        _SUBCATEGORY_COLORS_CACHE = colors
        print(f"Loaded {len(colors)-1} subcategory colors from {excel_path}")
        return colors
        
    except Exception as e:
        print(f"Warning: Could not load colors from {excel_path}: {e}")
        print("Using hash-based color generation as fallback")
        return {'Unknown': '#808080'}

def get_subcategory_color(subcategory: str, alpha: float = 1.0) -> str:
    """Get color for a subcategory.
    
    Args:
        subcategory: The subcategory name
        alpha: Opacity (0-1)
        
    Returns:
        Hex color string or RGBA tuple
    """
    # Load colors dynamically
    colors = load_subcategory_colors()
    
    if subcategory in colors:
        color = colors[subcategory]
    else:
        # Generate a color based on hash of subcategory name
        hash_val = hash(subcategory) % 360
        color = mcolors.hsv_to_rgb((hash_val / 360, 0.7, 0.9))
        color = mcolors.to_hex(color)
    
    if alpha < 1.0:
        # Convert to RGBA
        rgb = mcolors.to_rgb(color)
        return (*rgb, alpha)
    return color

def get_all_subcategories(G) -> list:
    """Get all unique subcategories from graph."""
    subcategories = set()
    for node, attrs in G.nodes(data=True):
        subcat = attrs.get('subcategory', 'Unknown')
        subcategories.add(subcat)
    return sorted(subcategories)

def create_subcategory_colormap(G):
    """Create a colormap for all subcategories in the graph.
    
    Returns:
        dict: mapping from subcategory to color
    """
    subcategories = get_all_subcategories(G)
    colormap = {}
    
    for subcat in subcategories:
        colormap[subcat] = get_subcategory_color(subcat)
    
    return colormap

def print_subcategory_stats(G):
    """Print statistics about subcategories."""
    from collections import Counter
    subcats = [G.nodes[n].get('subcategory', 'Unknown') for n in G.nodes()]
    counts = Counter(subcats)
    
    print("\n" + "="*60)
    print("SUBCATEGORY DISTRIBUTION")
    print("="*60)
    print(f"Total unique subcategories: {len(counts)}")
    print(f"\nTop 15 subcategories:")
    for subcat, count in counts.most_common(15):
        color = get_subcategory_color(subcat)
        print(f"  {subcat:20s} : {count:4d} products (color: {color})")
    print("="*60)
