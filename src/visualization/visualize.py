"""Visualization functions for the flavour graph using NetworkX and Matplotlib."""
import networkx as nx
import matplotlib.pyplot as plt
from typing import Optional, List
from src.core.subcategory_colors import get_subcategory_color, create_subcategory_colormap


def draw_graph(G: nx.DiGraph, 
               highlight_nodes: Optional[List[str]] = None,
               min_edge_weight: float = 0.0,
               layout: str = 'spring',
               figsize: tuple = (12, 8),
               show: bool = True,
               save_path: Optional[str] = None):
    """Draw the flavour graph with customizable options.
    
    Args:
        G: NetworkX directed graph
        highlight_nodes: List of node IDs to highlight (e.g., selected products)
        min_edge_weight: Only draw edges with weight >= this threshold
        layout: Layout algorithm ('spring', 'circular', 'kamada_kawai', 'shell')
        figsize: Figure size (width, height) in inches
        show: Whether to display the plot
        save_path: If provided, save the figure to this path
    """
    plt.figure(figsize=figsize)
    
    # Create weight-based layout where high weights = shorter distances
    if layout == 'spring':
        print("Calculating weight-based layout...")
        
        # Set spring weights for layout (higher weight = shorter distance)
        for u, v in G.edges():
            w = G[u][v].get('weight', 1)
            G[u][v]['spring_weight'] = w
        
        pos = nx.spring_layout(
            G, 
            k=2.0,  # Larger k = more spread out (increased from 0.8)
            iterations=200,  # More iterations for better convergence
            weight='spring_weight',  # Use edge weights
            seed=42,
            scale=10,  # Larger scale to spread nodes much more (increased from 5)
            threshold=1e-6  # Lower threshold = better convergence
        )
        print("✓ Layout calculated with weight-based distances")
    elif layout == 'circular':
        pos = nx.circular_layout(G)
    elif layout == 'kamada_kawai':
        pos = nx.kamada_kawai_layout(G)
    elif layout == 'shell':
        pos = nx.shell_layout(G)
    else:
        pos = nx.spring_layout(G)
    
    # Filter edges by weight
    edges_to_draw = [
        (u, v) for u, v, d in G.edges(data=True)
        if d.get('weight', 0) >= min_edge_weight
    ]
    
    # Node colors: use subcategory colors, highlight selected nodes with border
    node_colors = []
    node_borders = []
    for node in G.nodes():
        subcategory = G.nodes[node].get('subcategory', 'Unknown')
        base_color = get_subcategory_color(subcategory)
        
        if highlight_nodes and node in highlight_nodes:
            node_colors.append(base_color)
            node_borders.append('#FF0000')  # Red border for highlighted
        else:
            node_colors.append(base_color)
            node_borders.append(base_color)  # Same color border
    
    # Node sizes based on priority (larger for better visibility)
    node_sizes = [G.nodes[node].get('prio', 5) * 150 for node in G.nodes()]
    
    # Draw nodes
    nx.draw_networkx_nodes(G, pos, 
                          node_color=node_colors,
                          node_size=node_sizes,
                          alpha=0.9,
                          edgecolors=node_borders,
                          linewidths=3)
    
    # Draw edges with varying thickness and color based on weight
    if edges_to_draw:
        print(f"Drawing {len(edges_to_draw)} edges...")
        edge_weights = [G[u][v].get('weight', 1) for u, v in edges_to_draw]
        max_weight = max(edge_weights) if edge_weights else 1
        
        print(f"Weight range: {min(edge_weights):.1f} - {max_weight:.1f}")
        print(f"Thresholds: Weak < {max_weight * 0.1:.1f}, Medium < {max_weight * 0.5:.1f}, Strong >= {max_weight * 0.5:.1f}")
        
        # Calculate percentage of max weight for each edge
        weight_percentages = [w / max_weight for w in edge_weights]
        
        # Group edges by strength category based on percentage of max weight
        # Weak: < 10% of max, Medium: 10-50% of max, Strong: >= 50% of max
        weak_edges = [(u, v, idx) for idx, (u, v) in enumerate(edges_to_draw) if weight_percentages[idx] < 0.10]
        medium_edges = [(u, v, idx) for idx, (u, v) in enumerate(edges_to_draw) if 0.10 <= weight_percentages[idx] < 0.50]
        strong_edges = [(u, v, idx) for idx, (u, v) in enumerate(edges_to_draw) if weight_percentages[idx] >= 0.50]
        
        # Draw weak edges (batched) - very thin and transparent
        if weak_edges:
            weak_edgelist = [(u, v) for u, v, _ in weak_edges]
            # Thin lines for weak connections (0.3-1.0)
            weak_widths = [0.3 + weight_percentages[idx] / 0.10 * 0.7 for _, _, idx in weak_edges]
            nx.draw_networkx_edges(G, pos,
                                  edgelist=weak_edgelist,
                                  width=weak_widths,
                                  alpha=0.15,
                                  edge_color='lightgray',
                                  arrows=True,
                                  arrowsize=8,
                                  arrowstyle='->')
        
        # Draw medium edges (batched) - medium thickness
        if medium_edges:
            medium_edgelist = [(u, v) for u, v, _ in medium_edges]
            # Medium lines (1.5-4.0)
            medium_widths = [1.5 + ((weight_percentages[idx] - 0.10) / 0.40) * 2.5 for _, _, idx in medium_edges]
            nx.draw_networkx_edges(G, pos,
                                  edgelist=medium_edgelist,
                                  width=medium_widths,
                                  alpha=0.5,
                                  edge_color='gray',
                                  arrows=True,
                                  arrowsize=15,
                                  arrowstyle='->')
        
        # Draw strong edges (batched) - thick and dark
        if strong_edges:
            strong_edgelist = [(u, v) for u, v, _ in strong_edges]
            # Thick lines for strong connections (5.0-8.0)
            strong_widths = [5.0 + ((weight_percentages[idx] - 0.50) / 0.50) * 3.0 for _, _, idx in strong_edges]
            nx.draw_networkx_edges(G, pos,
                                  edgelist=strong_edgelist,
                                  width=strong_widths,
                                  alpha=0.85,
                                  edge_color='black',
                                  arrows=True,
                                  arrowsize=25,
                                  arrowstyle='->')
        
        print(f"✓ Drew {len(weak_edges)} weak, {len(medium_edges)} medium, {len(strong_edges)} strong edges")
    
    # Create labels using product names instead of IDs
    labels = {}
    for node in G.nodes():
        name = G.nodes[node].get('name', node)
        # Truncate long names to keep graph readable
        if len(name) > 25:
            labels[node] = name[:22] + '...'
        else:
            labels[node] = name
    
    # Draw labels with semi-transparent background
    for node, label in labels.items():
        x, y = pos[node]
        plt.text(x, y, label,
                fontsize=7,
                fontweight='bold',
                color='black',
                ha='center',
                va='center',
                bbox=dict(boxstyle='round,pad=0.2',
                        facecolor='white',
                        edgecolor='none',
                        alpha=0.75))
    
    # Add legend showing ALL subcategories
    from collections import Counter
    subcats = [G.nodes[n].get('subcategory', 'Unknown') for n in G.nodes()]
    all_subcats = Counter(subcats).most_common()  # Show ALL, not just top 10
    
    legend_elements = []
    for subcat, count in all_subcats:
        color = get_subcategory_color(subcat)
        legend_elements.append(
            plt.Line2D([0], [0], marker='o', color='w', 
                      markerfacecolor=color, markersize=10, 
                      label=f'{subcat} ({count})',
                      markeredgecolor=color, markeredgewidth=2)
        )
    
    # Use 2 columns to fit all categories
    plt.legend(handles=legend_elements, loc='upper left', 
              fontsize=8, ncol=2, framealpha=0.95,
              columnspacing=0.5, handletextpad=0.3)
    
    # Add edge weight legend
    ax = plt.gca()
    
    # Create example lines showing weak, medium, and strong connections
    from matplotlib.lines import Line2D
    edge_legend_elements = [
        Line2D([0], [0], color='lightgray', linewidth=0.5, 
               label='Weak (< 10% of max)', alpha=0.4),
        Line2D([0], [0], color='gray', linewidth=2.5, 
               label='Medium (10-50% of max)', alpha=0.6),
        Line2D([0], [0], color='black', linewidth=6.5, 
               label='Strong (≥ 50% of max)', alpha=0.85)
    ]
    
    # Add second legend in upper right for edge weights
    edge_legend = plt.legend(handles=edge_legend_elements, 
                            loc='upper right', 
                            fontsize=8, 
                            framealpha=0.95,
                            title='Connection Strength',
                            title_fontsize=9)
    
    # Add the subcategory legend back (matplotlib removes the first when adding second)
    ax.add_artist(plt.legend(handles=legend_elements, loc='upper left', 
                             fontsize=8, ncol=2, framealpha=0.95,
                             columnspacing=0.5, handletextpad=0.3))
    
    plt.title('Flavour Graph - Product Relationships', fontsize=16, fontweight='bold')
    plt.axis('off')
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Saved graph to {save_path}")
    
    if show:
        plt.show()


def draw_subgraph(G: nx.DiGraph,
                  node_ids: List[str],
                  full_graph: Optional[nx.DiGraph] = None,
                  figsize: tuple = (10, 6),
                  show: bool = True,
                  save_path: Optional[str] = None):
    """Draw a subgraph containing only specified nodes and their connections.
    
    Args:
        G: NetworkX directed graph (filtered by threshold)
        node_ids: List of node IDs to include in subgraph
        full_graph: Full unfiltered graph to check for weak connections
        figsize: Figure size (width, height) in inches
        show: Whether to display the plot
        save_path: If provided, save the figure to this path
    """
    # Create subgraph
    subgraph = G.subgraph(node_ids).copy()
    
    # If we have the full graph, add weak connections that might be below threshold
    if full_graph:
        for u in node_ids:
            for v in node_ids:
                if u != v and full_graph.has_edge(u, v):
                    # Add edge if it doesn't exist in filtered graph
                    if not subgraph.has_edge(u, v):
                        subgraph.add_edge(u, v, **full_graph[u][v])
    
    # Draw with edge labels showing weights
    plt.figure(figsize=figsize)
    
    # Weight-based layout for subgraph
    print("Calculating weight-based layout for subgraph...")
    for u, v in subgraph.edges():
        w = subgraph[u][v].get('weight', 1)
        subgraph[u][v]['spring_weight'] = w
    
    pos = nx.spring_layout(
        subgraph, 
        k=2.5,  # More space for readability 
        iterations=100, 
        weight='spring_weight',
        seed=42,
        scale=2
    )
    
    # Draw nodes with subcategory colors - all highlighted since they're all selected
    node_colors = []
    node_borders = []
    for node in subgraph.nodes():
        subcategory = subgraph.nodes[node].get('subcategory', 'Unknown')
        node_colors.append(get_subcategory_color(subcategory))
        node_borders.append('#FF0000')  # Red border for all selected
    
    node_sizes = [subgraph.nodes[node].get('prio', 5) * 300 for node in subgraph.nodes()]
    
    nx.draw_networkx_nodes(subgraph, pos,
                          node_color=node_colors,
                          node_size=node_sizes,
                          alpha=0.9,
                          edgecolors=node_borders,
                          linewidths=4)
    
    # Draw edges with varying thickness and color based on weight
    if subgraph.number_of_edges() > 0:
        edges_list = list(subgraph.edges())
        edge_weights = [subgraph[u][v].get('weight', 0) for u, v in edges_list]
        max_weight = max(edge_weights) if edge_weights else 1
        
        print(f"Subgraph weight range: {min(edge_weights):.1f} - {max_weight:.1f}")
        
        # Calculate percentage of max weight for each edge
        weight_percentages = [w / max_weight for w in edge_weights]
        
        # Group edges by strength (10% / 50% thresholds)
        weak_edges = [(u, v, idx) for idx, (u, v) in enumerate(edges_list) if weight_percentages[idx] < 0.10]
        medium_edges = [(u, v, idx) for idx, (u, v) in enumerate(edges_list) if 0.10 <= weight_percentages[idx] < 0.50]
        strong_edges = [(u, v, idx) for idx, (u, v) in enumerate(edges_list) if weight_percentages[idx] >= 0.50]
        
        # Draw weak edges
        if weak_edges:
            weak_edgelist = [(u, v) for u, v, _ in weak_edges]
            weak_widths = [0.5 + weight_percentages[idx] / 0.10 * 1.0 for _, _, idx in weak_edges]
            nx.draw_networkx_edges(subgraph, pos,
                                  edgelist=weak_edgelist,
                                  width=weak_widths,
                                  alpha=0.25,
                                  edge_color='lightgray',
                                  arrows=True,
                                  arrowsize=10,
                                  arrowstyle='->')
        
        # Draw medium edges
        if medium_edges:
            medium_edgelist = [(u, v) for u, v, _ in medium_edges]
            medium_widths = [2.0 + ((weight_percentages[idx] - 0.10) / 0.40) * 3.0 for _, _, idx in medium_edges]
            nx.draw_networkx_edges(subgraph, pos,
                                  edgelist=medium_edgelist,
                                  width=medium_widths,
                                  alpha=0.6,
                                  edge_color='gray',
                                  arrows=True,
                                  arrowsize=18,
                                  arrowstyle='->')
        
        # Draw strong edges
        if strong_edges:
            strong_edgelist = [(u, v) for u, v, _ in strong_edges]
            strong_widths = [6.0 + ((weight_percentages[idx] - 0.50) / 0.50) * 4.0 for _, _, idx in strong_edges]
            nx.draw_networkx_edges(subgraph, pos,
                                  edgelist=strong_edgelist,
                                  width=strong_widths,
                                  alpha=0.9,
                                  edge_color='black',
                                  arrows=True,
                                  arrowsize=30,
                                  arrowstyle='->')
        
        # Draw edge labels showing ALL weights (no filter)
        edge_labels = {(u, v): f"{d['weight']:.1f}" 
                      for u, v, d in subgraph.edges(data=True)}
        
        nx.draw_networkx_edge_labels(subgraph, pos,
                                     edge_labels=edge_labels,
                                     font_size=8,
                                     font_weight='bold',
                                     bbox=dict(boxstyle='round,pad=0.2', 
                                             facecolor='yellow', 
                                             alpha=0.7))
    
    # Create labels using product names
    labels = {}
    for node in subgraph.nodes():
        name = subgraph.nodes[node].get('name', node)
        # Keep full names in subgraph since there are fewer nodes
        if len(name) > 35:
            labels[node] = name[:32] + '...'
        else:
            labels[node] = name
    
    nx.draw_networkx_labels(subgraph, pos,
                           labels=labels,
                           font_size=10,
                           font_weight='bold',
                           font_family='sans-serif')
    
    plt.title('Selected Products - Connection Strengths', fontsize=14, fontweight='bold')
    plt.axis('off')
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Saved subgraph to {save_path}")
    
    if show:
        plt.show()


def print_graph_stats(G: nx.DiGraph):
    """Print statistics about the graph.
    
    Args:
        G: NetworkX directed graph
    """
    print("=" * 50)
    print("GRAPH STATISTICS")
    print("=" * 50)
    print(f"Nodes: {G.number_of_nodes()}")
    print(f"Edges: {G.number_of_edges()}")
    print(f"Density: {nx.density(G):.3f}")
    
    if G.number_of_nodes() > 0:
        # Average degree
        avg_degree = sum(dict(G.degree()).values()) / G.number_of_nodes()
        print(f"Average degree: {avg_degree:.2f}")
        
        # Top nodes by priority
        print("\nTop 5 nodes by priority:")
        sorted_nodes = sorted(G.nodes(data=True), 
                            key=lambda x: x[1].get('prio', 0), 
                            reverse=True)
        for i, (node_id, attrs) in enumerate(sorted_nodes[:5], 1):
            name = attrs.get('name', node_id)
            print(f"  {i}. {name}: prio={attrs['prio']}, "
                  f"in_degree={G.in_degree(node_id)}, "
                  f"out_degree={G.out_degree(node_id)}")
        
        # Strongest connections
        print("\nTop 5 strongest connections:")
        sorted_edges = sorted(G.edges(data=True),
                            key=lambda x: x[2].get('weight', 0),
                            reverse=True)
        for i, (src, dst, attrs) in enumerate(sorted_edges[:5], 1):
            src_name = G.nodes[src].get('name', src)
            dst_name = G.nodes[dst].get('name', dst)
            print(f"  {i}. {src_name} -> {dst_name}: weight={attrs['weight']:.2f}")
    
    print("=" * 50)


if __name__ == "__main__":
    # Demo: visualize the graph
    from src.core.main import setup_graph, generate, create_priority_list_from_sales
    
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
    
    # Draw full graph with ALL connections that exist in the graph
    print("\nDrawing full graph...")
    draw_graph(G, 
              highlight_nodes=selected,
              min_edge_weight=0.0,  # Draw ALL edges that exist in the graph
              layout='spring',
              figsize=(16, 12),
              show=True)
    
    # Draw subgraph of selected products with ALL their connections
    print("\nDrawing subgraph of selected products...")
    draw_subgraph(G, selected, full_graph=G, figsize=(10, 6), show=True)
