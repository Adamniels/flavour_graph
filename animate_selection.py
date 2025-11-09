"""
Animation of the product selection process.
Shows each product being selected and how neighbor priorities decrease.
"""
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import FancyBboxPatch
import numpy as np
from typing import List, Tuple
import copy

from main import setup_graph, create_priority_list_from_sales
from models import IndexedPriorityList


def generate_with_animation(antal: int, G: nx.DiGraph, priorityList: IndexedPriorityList):
    """
    Modified generate function that yields state after each selection.
    Returns: generator yielding (selected_id, selected_list, priority_snapshot, affected_neighbors)
    """
    if priorityList is None:
        raise ValueError("priorityList cannot be None")
    
    # Calculate max weight for normalization
    max_weight = 0.0
    for u, v, data in G.edges(data=True):
        weight = data.get('weight', 0.0)
        if weight > max_weight:
            max_weight = weight
    
    selected = []
    
    for _ in range(antal):
        if len(priorityList._items) == 0:
            break
            
        # Get highest priority product
        highest_prio_id = priorityList.top(1)[0]
        
        # Get neighbors before selecting
        neighbors = list(G.neighbors(highest_prio_id))
        affected_neighbors = []
        
        # Create dict for fast lookup
        prio_dict = {nid: val for nid, val in priorityList._items}
        
        # Reduce priority of neighbors based on edge weight and track changes
        for neighbor in neighbors:
            old_prio = prio_dict.get(neighbor, 0)
            # Get edge weight
            edge_data = G.get_edge_data(highest_prio_id, neighbor)
            if edge_data:
                weight = edge_data.get('weight', 0.0)
                priorityList.reduce_prio_by_weight(neighbor, weight, max_weight)
            new_prio = next((val for nid, val in priorityList._items if nid == neighbor), 0)
            if old_prio != new_prio:
                affected_neighbors.append((neighbor, old_prio, new_prio))
        
        # Add to selected
        selected.append(highest_prio_id)
        
        # Remove from priority list
        priorityList.remove(highest_prio_id)
        
        # Take snapshot of current state (convert to dict for compatibility)
        priority_snapshot = {nid: val for nid, val in priorityList._items}
        
        # Yield current state
        yield (highest_prio_id, selected.copy(), priority_snapshot, affected_neighbors)


def create_animation(G: nx.DiGraph, priority_list: IndexedPriorityList, num_products: int = 10):
    """
    Create an animated visualization of the selection process.
    """
    # Setup figure with two subplots
    fig = plt.figure(figsize=(20, 10))
    gs = fig.add_gridspec(1, 2, width_ratios=[3, 1], wspace=0.3)
    ax_graph = fig.add_subplot(gs[0])
    ax_stats = fig.add_subplot(gs[1])
    
    # Create layout for graph (fixed positions)
    pos = nx.spring_layout(G, k=2, iterations=50, seed=42, scale=2)
    
    # Store animation state
    state = {
        'selected': [],
        'current': None,
        'affected': [],
        'iteration': 0,
        'priority_dict': {nid: val for nid, val in priority_list._items}
    }
    
    # Get all product names for display
    product_names = {node: G.nodes[node].get('name', node) for node in G.nodes()}
    
    # Create generator for selection process
    priority_list_copy = copy.deepcopy(priority_list)
    selection_gen = generate_with_animation(num_products, G, priority_list_copy)
    
    def init():
        """Initialize animation."""
        ax_graph.clear()
        ax_stats.clear()
        return []
    
    def update(frame):
        """Update function for each frame."""
        ax_graph.clear()
        ax_stats.clear()
        
        try:
            # Get next selection
            current_id, selected_list, priority_snapshot, affected_neighbors = next(selection_gen)
            state['selected'] = selected_list
            state['current'] = current_id
            state['affected'] = [n[0] for n in affected_neighbors]
            state['iteration'] = frame + 1
            state['priority_dict'] = priority_snapshot
            state['affected_changes'] = affected_neighbors
        except StopIteration:
            pass
        
        # Draw graph
        draw_graph_frame(ax_graph, G, pos, state, product_names)
        
        # Draw stats
        draw_stats_frame(ax_stats, G, state, product_names)
        
        return []
    
    def draw_graph_frame(ax, G, pos, state, names):
        """Draw the graph for current frame."""
        # Color nodes based on state
        node_colors = []
        node_sizes = []
        node_borders = []
        
        for node in G.nodes():
            size_base = 300
            
            if node == state['current']:
                # Currently selected - large and bright green
                node_colors.append('#00FF00')
                node_sizes.append(size_base * 3)
                node_borders.append('#FFD700')
            elif node in state['selected']:
                # Previously selected - orange
                node_colors.append('#FF6B00')
                node_sizes.append(size_base * 1.5)
                node_borders.append('#8B4513')
            elif node in state['affected']:
                # Affected by current selection - yellow
                node_colors.append('#FFFF00')
                node_sizes.append(size_base * 2)
                node_borders.append('#FFA500')
            else:
                # Normal nodes - light blue, size by priority
                prio = state['priority_dict'].get(node, 5)
                intensity = min(prio / 100, 1.0)
                node_colors.append(plt.cm.Blues(0.3 + intensity * 0.5))
                node_sizes.append(size_base * (0.5 + intensity * 0.5))
                node_borders.append('#4682B4')
        
        # Draw nodes
        nx.draw_networkx_nodes(G, pos,
                              node_color=node_colors,
                              node_size=node_sizes,
                              alpha=0.9,
                              edgecolors=node_borders,
                              linewidths=3,
                              ax=ax)
        
        # Draw edges - highlight connections to current selection
        if state['current']:
            # Get edges connected to current selection
            current_edges = []
            other_edges = []
            
            for u, v in G.edges():
                if u == state['current'] or v == state['current']:
                    current_edges.append((u, v))
                else:
                    other_edges.append((u, v))
            
            # Draw other edges (faint)
            if other_edges:
                nx.draw_networkx_edges(G, pos,
                                      edgelist=other_edges,
                                      width=0.3,
                                      alpha=0.1,
                                      edge_color='gray',
                                      arrows=False,
                                      ax=ax)
            
            # Draw current edges (highlighted)
            if current_edges:
                edge_weights = [G[u][v].get('weight', 1) for u, v in current_edges]
                max_weight = max(edge_weights) if edge_weights else 1
                edge_widths = [w / max_weight * 4 for w in edge_weights]
                
                nx.draw_networkx_edges(G, pos,
                                      edgelist=current_edges,
                                      width=edge_widths,
                                      alpha=0.7,
                                      edge_color='#FF6B00',
                                      arrows=True,
                                      arrowsize=20,
                                      arrowstyle='->',
                                      ax=ax)
                
                # Draw edge labels showing weights for current edges
                edge_labels = {(u, v): f"{G[u][v].get('weight', 0):.1f}" 
                              for u, v in current_edges}
                nx.draw_networkx_edge_labels(G, pos,
                                             edge_labels=edge_labels,
                                             font_size=9,
                                             font_weight='bold',
                                             bbox=dict(boxstyle='round,pad=0.3', 
                                                     facecolor='yellow', 
                                                     alpha=0.8,
                                                     edgecolor='#FF6B00'),
                                             ax=ax)
        else:
            # Draw all edges faintly
            nx.draw_networkx_edges(G, pos,
                                  width=0.3,
                                  alpha=0.1,
                                  edge_color='gray',
                                  arrows=False,
                                  ax=ax)
        
        # Draw labels for important nodes
        labels_to_draw = {}
        for node in G.nodes():
            if node == state['current'] or node in state['selected'] or node in state['affected']:
                name = names[node]
                if len(name) > 20:
                    name = name[:17] + '...'
                labels_to_draw[node] = name
        
        nx.draw_networkx_labels(G, pos,
                               labels=labels_to_draw,
                               font_size=8,
                               font_weight='bold',
                               font_color='black',
                               ax=ax)
        
        # Title
        ax.set_title(f'Product Selection Process - Iteration {state["iteration"]}/{num_products}',
                    fontsize=18, fontweight='bold', pad=20)
        
        # Legend
        legend_elements = [
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#00FF00', 
                      markersize=15, label='Currently Selected', markeredgecolor='#FFD700', markeredgewidth=2),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#FF6B00',
                      markersize=12, label='Previously Selected', markeredgecolor='#8B4513', markeredgewidth=2),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#FFFF00',
                      markersize=12, label='Priority Decreased', markeredgecolor='#FFA500', markeredgewidth=2),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#6495ED',
                      markersize=10, label='Other Products', markeredgecolor='#4682B4', markeredgewidth=2),
        ]
        ax.legend(handles=legend_elements, loc='upper left', fontsize=10)
        
        ax.axis('off')
    
    def draw_stats_frame(ax, G, state, names):
        """Draw statistics panel."""
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        y_pos = 0.95
        line_height = 0.04
        
        # Title
        ax.text(0.5, y_pos, 'Selection Statistics', 
               ha='center', fontsize=16, fontweight='bold')
        y_pos -= line_height * 2
        
        # Current iteration
        ax.text(0.05, y_pos, f"Iteration: {state['iteration']}/{num_products}",
               fontsize=12, fontweight='bold')
        y_pos -= line_height * 1.5
        
        # Current selection
        if state['current']:
            current_name = names[state['current']]
            if len(current_name) > 25:
                current_name = current_name[:22] + '...'
            
            # Add colored box
            box = FancyBboxPatch((0.02, y_pos - 0.03), 0.96, 0.06,
                                boxstyle="round,pad=0.01", 
                                edgecolor='#00FF00', facecolor='#E0FFE0',
                                linewidth=2)
            ax.add_patch(box)
            
            ax.text(0.5, y_pos, f'NOW SELECTING:', ha='center',
                   fontsize=11, fontweight='bold', color='#006600')
            y_pos -= line_height
            ax.text(0.5, y_pos, current_name, ha='center',
                   fontsize=10, fontweight='bold', color='#003300')
            y_pos -= line_height * 2
        
        # Affected neighbors
        if state.get('affected_changes'):
            ax.text(0.05, y_pos, f"Neighbors affected: {len(state['affected_changes'])}",
                   fontsize=11, fontweight='bold', color='#FF6B00')
            y_pos -= line_height * 1.5
            
            # Show top 5 affected with edge weights
            for i, (neighbor_id, old_prio, new_prio) in enumerate(state['affected_changes'][:5]):
                neighbor_name = names[neighbor_id]
                if len(neighbor_name) > 20:
                    neighbor_name = neighbor_name[:17] + '...'
                
                # Get edge weight
                edge_weight = 0.0
                if state['current']:
                    edge_data = G.get_edge_data(state['current'], neighbor_id)
                    if edge_data:
                        edge_weight = edge_data.get('weight', 0.0)
                
                ax.text(0.05, y_pos, f"• {neighbor_name}",
                       fontsize=9)
                
                # Show weight and priority change
                reduction_pct = ((old_prio - new_prio) / old_prio * 100) if old_prio > 0 else 0
                ax.text(0.95, y_pos, f"w:{edge_weight:.1f} | {old_prio:.0f}→{new_prio:.0f} (-{reduction_pct:.0f}%)",
                       fontsize=8, ha='right', color='#CC5500', family='monospace')
                y_pos -= line_height
            
            if len(state['affected_changes']) > 5:
                ax.text(0.05, y_pos, f"  ... and {len(state['affected_changes']) - 5} more",
                       fontsize=8, style='italic', color='gray')
                y_pos -= line_height
            
            y_pos -= line_height
        
        # Selected products list
        ax.text(0.05, y_pos, 'Selected Products:', 
               fontsize=12, fontweight='bold')
        y_pos -= line_height * 1.5
        
        for i, prod_id in enumerate(state['selected'][-8:], start=max(1, len(state['selected']) - 7)):
            prod_name = names[prod_id]
            if len(prod_name) > 22:
                prod_name = prod_name[:19] + '...'
            
            color = '#00FF00' if prod_id == state['current'] else '#FF6B00'
            ax.text(0.05, y_pos, f"{i}. {prod_name}",
                   fontsize=9, color=color)
            y_pos -= line_height
        
        if len(state['selected']) > 8:
            ax.text(0.05, y_pos, f"  ... {len(state['selected']) - 8} more above",
                   fontsize=8, style='italic', color='gray')
    
    # Create animation
    anim = animation.FuncAnimation(fig, update, init_func=init,
                                  frames=num_products, interval=2000,
                                  blit=False, repeat=True)
    
    return anim, fig


if __name__ == "__main__":
    print("Creating flavour graph...")
    G = setup_graph(min_edge_weight=5.0)
    
    print("Creating priority list from sales data...")
    priority_list = create_priority_list_from_sales(G)
    
    print("\nCreating animation...")
    print("This will show the selection process step by step.")
    print("Watch how each product selection affects its neighbors!\n")
    
    # Create animation with 10 products
    num_products = 10
    anim, fig = create_animation(G, priority_list, num_products=num_products)
    
    # Option to save as video or GIF
    print("\nAnimation created!")
    print("Options:")
    print("  - Press any key to start animation")
    print("  - Close window to exit")
    print("\nTo save as video: uncomment the save lines in code")
    
    # Uncomment to save animation
    # print("\nSaving animation as MP4...")
    # Writer = animation.writers['ffmpeg']
    # writer = Writer(fps=0.5, metadata=dict(artist='Me'), bitrate=1800)
    # anim.save('product_selection_animation.mp4', writer=writer)
    # print("Saved as product_selection_animation.mp4")
    
    # Uncomment to save as GIF
    # print("\nSaving animation as GIF...")
    # anim.save('product_selection_animation.gif', writer='pillow', fps=0.5)
    # print("Saved as product_selection_animation.gif")
    
    plt.show()
