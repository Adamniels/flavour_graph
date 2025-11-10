#!/usr/bin/env python3
"""Generate interactive HTML visualization."""
from src.interactive.generate_html import generate_html_visualization
from src.core import setup_graph, create_priority_list_from_sales
import sys
from io import StringIO


def main():
    """Main entry point for interactive visualization."""
    print("=" * 70)
    print("GENERATING INTERACTIVE HTML VISUALIZATION")
    print("=" * 70)
    print("\nSetting up...")
    
    G = setup_graph(min_edge_weight=5.0)
    print(f"✓ Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    priority_list = create_priority_list_from_sales(G)
    sys.stdout = old_stdout
    print(f"✓ Priority list ready")
    
    print("\nGenerating HTML visualization...")
    output_file = generate_html_visualization(G, priority_list, num_products=15)
    
    print("\n" + "=" * 70)
    print(f"✓ Complete! Open {output_file} in your browser")
    print("=" * 70)


if __name__ == "__main__":
    main()
