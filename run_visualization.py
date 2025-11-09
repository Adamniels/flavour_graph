#!/usr/bin/env python3
"""Run graph visualization."""
from src.visualization.visualize import draw_graph, print_graph_stats
from src.core.main import setup_graph, generate, create_priority_list_from_sales


def main():
    """Main entry point for visualization."""
    print("Creating flavour graph...")
    G = setup_graph()
    
    # Print stats
    print_graph_stats(G)
    
    # Create priority list from sales data
    print("\nCreating priority list from sales data...")
    priority_list = create_priority_list_from_sales(G)
    
    # Generate selection
    print("\nGenerating product selection...")
    selected = generate(40, G, priorityList=priority_list)
    print(f"Selected products ({len(selected)} total):")
    for i, node_id in enumerate(selected, 1):
        name = G.nodes[node_id].get('name', node_id)
        print(f"  {i:2d}. {name} (ID: {node_id})")
    
    # Draw full graph
    print("\nDrawing full graph...")
    draw_graph(G, 
              highlight_nodes=selected,
              min_edge_weight=0.0,
              layout='spring',
              figsize=(16, 12),
              show=True)


if __name__ == "__main__":
    main()
