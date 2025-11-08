"""
Interactive step-by-step product selection visualization.
Click "Next" button to see each selection.
"""
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import copy

from main import setup_graph, create_priority_list_from_sales
from models import IndexedPriorityList


class InteractiveSelection:
    def __init__(self, G: nx.DiGraph, priority_list: IndexedPriorityList, num_products: int = 10):
        self.G = G
        self.priority_list_original = copy.deepcopy(priority_list)
        self.priority_list = copy.deepcopy(priority_list)
        self.num_products = num_products
        
        self.selected = []
        self.current_selection = None
        self.affected_neighbors = []
        self.iteration = 0
        
        # Setup figure
        self.fig = plt.figure(figsize=(20, 10))
        gs = self.fig.add_gridspec(1, 2, width_ratios=[3, 1], wspace=0.3, bottom=0.1)
        self.ax_graph = self.fig.add_subplot(gs[0])
        self.ax_stats = self.fig.add_subplot(gs[1])
        
        # Create fixed layout
        self.pos = nx.spring_layout(G, k=2, iterations=50, seed=42, scale=2)
        
        # Product names
        self.product_names = {node: G.nodes[node].get('name', node) for node in G.nodes()}
        
        # Add buttons
        ax_next = plt.axes([0.7, 0.02, 0.1, 0.04])
        ax_reset = plt.axes([0.82, 0.02, 0.1, 0.04])
        
        self.btn_next = Button(ax_next, 'Next Selection', color='lightgreen', hovercolor='green')
        self.btn_next.on_clicked(self.next_selection)
        
        self.btn_reset = Button(ax_reset, 'Reset', color='lightcoral', hovercolor='red')
        self.btn_reset.on_clicked(self.reset)
        
        # Initial draw
        self.draw()
    
    def next_selection(self, event):
        """Select next product."""
        if self.iteration >= self.num_products:
            print(f"Already selected {self.num_products} products!")
            return
        
        if len(self.priority_list._items) == 0:
            print("No more products to select!")
            return
        
        # Get highest priority product
        highest_prio_id = self.priority_list.top(1)[0]
        
        # Get neighbors and their priorities before change
        neighbors = list(self.G.neighbors(highest_prio_id))
        self.affected_neighbors = []
        
        # Create dict for fast lookup
        prio_dict = {nid: val for nid, val in self.priority_list._items}
        
        for neighbor in neighbors:
            old_prio = prio_dict.get(neighbor, 0)
            self.priority_list.half_prio(neighbor)
            # Get new priority after change
            new_prio = next((val for nid, val in self.priority_list._items if nid == neighbor), 0)
            if old_prio != new_prio:
                self.affected_neighbors.append((neighbor, old_prio, new_prio))
        
        # Add to selected
        self.selected.append(highest_prio_id)
        self.current_selection = highest_prio_id
        self.iteration += 1
        
        # Remove from priority list
        self.priority_list.remove(highest_prio_id)
        
        # Update display
        self.draw()
        
        # Print to console
        name = self.product_names[highest_prio_id]
        print(f"\nIteration {self.iteration}: Selected '{name}'")
        print(f"  Affected {len(self.affected_neighbors)} neighbors")
    
    def reset(self, event):
        """Reset the selection process."""
        self.priority_list = copy.deepcopy(self.priority_list_original)
        self.selected = []
        self.current_selection = None
        self.affected_neighbors = []
        self.iteration = 0
        self.draw()
        print("\nReset! Ready to start again.")
    
    def draw(self):
        """Draw current state."""
        self.ax_graph.clear()
        self.ax_stats.clear()
        
        self.draw_graph()
        self.draw_stats()
        
        self.fig.canvas.draw()
    
    def draw_graph(self):
        """Draw the graph."""
        # Color and size nodes
        node_colors = []
        node_sizes = []
        node_borders = []
        affected_ids = [n[0] for n in self.affected_neighbors]
        
        # Create dict for fast priority lookup
        prio_dict = {nid: val for nid, val in self.priority_list._items}
        
        for node in self.G.nodes():
            size_base = 300
            
            if node == self.current_selection:
                node_colors.append('#00FF00')
                node_sizes.append(size_base * 3)
                node_borders.append('#FFD700')
            elif node in self.selected:
                node_colors.append('#FF6B00')
                node_sizes.append(size_base * 1.5)
                node_borders.append('#8B4513')
            elif node in affected_ids:
                node_colors.append('#FFFF00')
                node_sizes.append(size_base * 2)
                node_borders.append('#FFA500')
            else:
                prio = prio_dict.get(node, 5)
                intensity = min(prio / 100, 1.0)
                node_colors.append(plt.cm.Blues(0.3 + intensity * 0.5))
                node_sizes.append(size_base * (0.5 + intensity * 0.5))
                node_borders.append('#4682B4')
        
        # Draw nodes
        nx.draw_networkx_nodes(self.G, self.pos,
                              node_color=node_colors,
                              node_size=node_sizes,
                              alpha=0.9,
                              edgecolors=node_borders,
                              linewidths=3,
                              ax=self.ax_graph)
        
        # Draw edges
        if self.current_selection:
            current_edges = []
            other_edges = []
            
            for u, v in self.G.edges():
                if u == self.current_selection or v == self.current_selection:
                    current_edges.append((u, v))
                else:
                    other_edges.append((u, v))
            
            if other_edges:
                nx.draw_networkx_edges(self.G, self.pos,
                                      edgelist=other_edges,
                                      width=0.3,
                                      alpha=0.1,
                                      edge_color='gray',
                                      arrows=False,
                                      ax=self.ax_graph)
            
            if current_edges:
                edge_weights = [self.G[u][v].get('weight', 1) for u, v in current_edges]
                max_weight = max(edge_weights) if edge_weights else 1
                edge_widths = [w / max_weight * 4 for w in edge_weights]
                
                nx.draw_networkx_edges(self.G, self.pos,
                                      edgelist=current_edges,
                                      width=edge_widths,
                                      alpha=0.7,
                                      edge_color='#FF6B00',
                                      arrows=True,
                                      arrowsize=20,
                                      arrowstyle='->',
                                      ax=self.ax_graph)
        else:
            nx.draw_networkx_edges(self.G, self.pos,
                                  width=0.3,
                                  alpha=0.1,
                                  edge_color='gray',
                                  arrows=False,
                                  ax=self.ax_graph)
        
        # Draw labels for important nodes
        labels_to_draw = {}
        for node in self.G.nodes():
            if node == self.current_selection or node in self.selected or node in affected_ids:
                name = self.product_names[node]
                if len(name) > 20:
                    name = name[:17] + '...'
                labels_to_draw[node] = name
        
        nx.draw_networkx_labels(self.G, self.pos,
                               labels=labels_to_draw,
                               font_size=8,
                               font_weight='bold',
                               font_color='black',
                               ax=self.ax_graph)
        
        # Title
        self.ax_graph.set_title(f'Interactive Product Selection - Step {self.iteration}/{self.num_products}',
                               fontsize=18, fontweight='bold', pad=20)
        
        # Legend
        legend_elements = [
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#00FF00',
                      markersize=15, label='Just Selected', markeredgecolor='#FFD700', markeredgewidth=2),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#FF6B00',
                      markersize=12, label='Previously Selected', markeredgecolor='#8B4513', markeredgewidth=2),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#FFFF00',
                      markersize=12, label='Priority Just Decreased', markeredgecolor='#FFA500', markeredgewidth=2),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#6495ED',
                      markersize=10, label='Other Products (size = priority)', markeredgecolor='#4682B4', markeredgewidth=2),
        ]
        self.ax_graph.legend(handles=legend_elements, loc='upper left', fontsize=10)
        
        self.ax_graph.axis('off')
    
    def draw_stats(self):
        """Draw statistics panel."""
        ax = self.ax_stats
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        y_pos = 0.95
        line_height = 0.04
        
        # Title
        ax.text(0.5, y_pos, 'Selection Info', 
               ha='center', fontsize=16, fontweight='bold')
        y_pos -= line_height * 2
        
        # Progress
        ax.text(0.05, y_pos, f"Progress: {self.iteration}/{self.num_products}",
               fontsize=12, fontweight='bold')
        y_pos -= line_height * 1.5
        
        # Current selection
        if self.current_selection:
            current_name = self.product_names[self.current_selection]
            if len(current_name) > 25:
                current_name = current_name[:22] + '...'
            
            ax.add_patch(plt.Rectangle((0.02, y_pos - 0.03), 0.96, 0.06,
                                      edgecolor='#00FF00', facecolor='#E0FFE0', linewidth=2))
            
            ax.text(0.5, y_pos, f'JUST SELECTED:', ha='center',
                   fontsize=11, fontweight='bold', color='#006600')
            y_pos -= line_height
            ax.text(0.5, y_pos, current_name, ha='center',
                   fontsize=10, fontweight='bold', color='#003300')
            y_pos -= line_height * 2
        
        # Affected neighbors
        if self.affected_neighbors:
            ax.text(0.05, y_pos, f"Neighbors affected: {len(self.affected_neighbors)}",
                   fontsize=11, fontweight='bold', color='#FF6B00')
            y_pos -= line_height * 1.5
            
            for i, (neighbor_id, old_prio, new_prio) in enumerate(self.affected_neighbors[:8]):
                neighbor_name = self.product_names[neighbor_id]
                if len(neighbor_name) > 20:
                    neighbor_name = neighbor_name[:17] + '...'
                
                ax.text(0.05, y_pos, f"• {neighbor_name}",
                       fontsize=9)
                ax.text(0.95, y_pos, f"{old_prio:.0f} → {new_prio:.0f}",
                       fontsize=9, ha='right', color='#CC5500')
                y_pos -= line_height
            
            if len(self.affected_neighbors) > 8:
                ax.text(0.05, y_pos, f"  ... and {len(self.affected_neighbors) - 8} more",
                       fontsize=8, style='italic', color='gray')
                y_pos -= line_height
            
            y_pos -= line_height
        
        # Selected list
        ax.text(0.05, y_pos, 'Selected Products:', 
               fontsize=12, fontweight='bold')
        y_pos -= line_height * 1.5
        
        for i, prod_id in enumerate(self.selected[-10:], start=max(1, len(self.selected) - 9)):
            prod_name = self.product_names[prod_id]
            if len(prod_name) > 22:
                prod_name = prod_name[:19] + '...'
            
            color = '#00FF00' if prod_id == self.current_selection else '#FF6B00'
            ax.text(0.05, y_pos, f"{i}. {prod_name}",
                   fontsize=9, color=color)
            y_pos -= line_height
        
        if len(self.selected) > 10:
            ax.text(0.05, y_pos, f"  ... {len(self.selected) - 10} more above",
                   fontsize=8, style='italic', color='gray')
        
        # Instructions at bottom
        y_pos = 0.08
        ax.text(0.5, y_pos, 'Click "Next Selection" to continue',
               ha='center', fontsize=10, style='italic', color='blue')
        ax.text(0.5, y_pos - 0.04, 'Click "Reset" to start over',
               ha='center', fontsize=10, style='italic', color='red')


if __name__ == "__main__":
    print("=" * 70)
    print("INTERACTIVE PRODUCT SELECTION")
    print("=" * 70)
    print("\nSetting up...")
    
    G = setup_graph(min_edge_weight=5.0)
    print(f"✓ Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    
    import sys
    from io import StringIO
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    priority_list = create_priority_list_from_sales(G)
    sys.stdout = old_stdout
    print(f"✓ Priority list ready")
    
    print("\n" + "=" * 70)
    print("Opening interactive window...")
    print("=" * 70)
    print("\nInstructions:")
    print("  1. Click 'Next Selection' to select the next product")
    print("  2. Watch how neighbor priorities decrease (yellow nodes)")
    print("  3. Click 'Reset' to start over")
    print("  4. Close window to exit")
    print("\nEnjoy the visualization!\n")
    
    viewer = InteractiveSelection(G, priority_list, num_products=15)
    plt.show()
