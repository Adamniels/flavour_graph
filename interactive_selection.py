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
from subcategory_colors import get_subcategory_color, create_subcategory_colormap


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
        
        # Calculate max weight for normalization
        self.max_weight = 0.0
        for u, v, data in G.edges(data=True):
            weight = data.get('weight', 0.0)
            if weight > self.max_weight:
                self.max_weight = weight
        print(f"\nMax weight in graph: {self.max_weight:.1f}")
        
        # Create subcategory colormap
        self.subcategory_colors = create_subcategory_colormap(G)
        print(f"\nCreated colormap for {len(self.subcategory_colors)} subcategories")
        
        # Setup larger figure for better visibility
        self.fig = plt.figure(figsize=(24, 14))
        gs = self.fig.add_gridspec(1, 2, width_ratios=[2.5, 1], wspace=0.25, bottom=0.08)
        self.ax_graph = self.fig.add_subplot(gs[0])
        self.ax_stats = self.fig.add_subplot(gs[1])
        
        # Create weight-based layout where high weights = shorter distances
        # Convert edge weights to spring constants (higher weight = stronger spring = shorter distance)
        print("\nCalculating weight-based layout...")
        
        # Create a dictionary of edge weights for the layout algorithm
        # In spring layout, 'weight' determines the strength of the spring
        # We want high edge weights to result in short distances
        max_weight = max([G[u][v].get('weight', 1) for u, v in G.edges()])
        
        # Normalize weights: higher weight = nodes should be closer
        # We'll use weight directly as the spring constant
        for u, v in G.edges():
            w = G[u][v].get('weight', 1)
            # Higher weight = stronger spring = shorter distance
            G[u][v]['spring_weight'] = w
        
        # Use spring layout with weights
        # k controls optimal distance, iterations for convergence
        self.pos = nx.spring_layout(
            G, 
            k=0.8,  # Smaller k = more spread out (reduced from 1.5)
            iterations=150,  # More iterations for better convergence
            weight='spring_weight',  # Use our calculated weights
            seed=42,
            scale=5,  # Larger scale to spread nodes more
            threshold=1e-5  # Lower threshold = better convergence
        )
        print("✓ Layout calculated with weight-based distances")
        
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
            # Get edge weight and use it for priority reduction
            edge_data = self.G.get_edge_data(highest_prio_id, neighbor)
            if edge_data:
                weight = edge_data.get('weight', 0.0)
                self.priority_list.reduce_prio_by_weight(neighbor, weight, self.max_weight)
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
        """Draw the graph with subcategory colors."""
        # Color and size nodes based on subcategory and state
        node_colors = []
        node_sizes = []
        node_borders = []
        affected_ids = [n[0] for n in self.affected_neighbors]
        
        # Create dict for fast priority lookup
        prio_dict = {nid: val for nid, val in self.priority_list._items}
        
        for node in self.G.nodes():
            size_base = 500  # Increased from 300 for better visibility
            subcategory = self.G.nodes[node].get('subcategory', 'Unknown')
            base_color = get_subcategory_color(subcategory)
            
            if node == self.current_selection:
                # Currently selected - bright with golden border
                node_colors.append('#00FF00')
                node_sizes.append(size_base * 3)
                node_borders.append('#FFD700')
            elif node in self.selected:
                # Previously selected - use subcategory color with black border
                node_colors.append(base_color)
                node_sizes.append(size_base * 1.8)  # Slightly larger
                node_borders.append('#000000')  # Black border
            elif node in affected_ids:
                # Affected by current selection - keep subcategory color, add orange ring
                node_colors.append(base_color)  # Keep subcategory color!
                node_sizes.append(size_base * 2.2)  # Larger for visibility
                node_borders.append('#FFA500')  # Orange/yellow outer ring
            else:
                # Normal nodes - subcategory color with intensity based on priority
                prio = prio_dict.get(node, 5)
                intensity = min(prio / 100, 1.0)
                # Use subcategory color with alpha based on priority
                node_colors.append(base_color)
                node_sizes.append(size_base * (0.5 + intensity * 0.5))
                node_borders.append(base_color)
        
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
                
                # Draw edge labels showing ALL weights (no threshold filter)
                edge_labels = {}
                for u, v in current_edges:
                    weight = self.G[u][v].get('weight', 0)
                    edge_labels[(u, v)] = f'{weight:.1f}'
                
                if edge_labels:
                    nx.draw_networkx_edge_labels(self.G, self.pos,
                                                 edge_labels=edge_labels,
                                                 font_size=8,
                                                 font_weight='bold',
                                                 font_color='black',
                                                 bbox=dict(boxstyle='round,pad=0.2',
                                                         facecolor='yellow',
                                                         edgecolor='#FF6B00',
                                                         alpha=0.85,
                                                         linewidth=1.5),
                                                 ax=self.ax_graph,
                                                 rotate=False)
        else:
            nx.draw_networkx_edges(self.G, self.pos,
                                  width=0.3,
                                  alpha=0.1,
                                  edge_color='gray',
                                  arrows=False,
                                  ax=self.ax_graph)
        
        # Draw labels for important nodes - centered on node for clarity
        # Only show labels for nodes not too far to the right (to avoid overlap with stats panel)
        labels_to_draw = {}
        affected_ids = [n[0] for n in self.affected_neighbors]
        
        # Get position bounds
        x_positions = [self.pos[node][0] for node in self.G.nodes()]
        x_max = max(x_positions)
        x_threshold = x_max * 0.85  # Only show labels for nodes in left 85% of graph
        
        for node in self.G.nodes():
            if node == self.current_selection or node in self.selected or node in affected_ids:
                # Check if node is not too far right (avoid stats panel overlap)
                if self.pos[node][0] < x_threshold:
                    name = self.product_names[node]
                    if len(name) > 18:
                        name = name[:15] + '...'
                    labels_to_draw[node] = name
        
        # Draw labels CENTERED on nodes with semi-transparent background
        for node, label in labels_to_draw.items():
            x, y = self.pos[node]
            
            # Center labels directly on nodes - NO offset
            self.ax_graph.text(x, y, label,
                             fontsize=6.5,
                             fontweight='bold',
                             color='black',
                             ha='center',
                             va='center',
                             bbox=dict(boxstyle='round,pad=0.15',
                                     facecolor='white',
                                     edgecolor='black',
                                     linewidth=0.5,
                                     alpha=0.9),
                             clip_on=True,
                             zorder=1000)
        
        # Title
        self.ax_graph.set_title(f'Interactive Product Selection - Step {self.iteration}/{self.num_products}',
                               fontsize=18, fontweight='bold', pad=20)
        
        # Legend - show ALL subcategories + state indicators (no emojis to avoid warnings)
        legend_elements = [
            # State indicators
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#00FF00',
                      markersize=15, label='Just Selected', markeredgecolor='#FFD700', markeredgewidth=2),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#FFFF00',
                      markersize=12, label='Priority Decreased', markeredgecolor='#FFA500', markeredgewidth=2),
        ]
        
        # Add ALL subcategories to legend, sorted by count
        from collections import Counter
        subcats = [self.G.nodes[n].get('subcategory', 'Unknown') for n in self.G.nodes()]
        all_subcats = Counter(subcats).most_common()  # Get all, not just top 5
        
        for subcat, count in all_subcats:
            color = get_subcategory_color(subcat)
            legend_elements.append(
                plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=color,
                          markersize=10, label=f'{subcat} ({count})', 
                          markeredgecolor=color, markeredgewidth=2)
            )
        
        # Use 2 columns to fit more categories
        self.ax_graph.legend(handles=legend_elements, loc='upper left', 
                            fontsize=8, ncol=2, framealpha=0.95, 
                            columnspacing=0.5, handletextpad=0.3)
        
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
        
        # Current selection - draw box FIRST, then text INSIDE
        if self.current_selection:
            current_name = self.product_names[self.current_selection]
            # Don't truncate - show full name in the box
            # Split into multiple lines if too long
            if len(current_name) > 30:
                # Try to split at space
                words = current_name.split()
                line1 = ""
                line2 = ""
                for word in words:
                    if len(line1) + len(word) < 25:
                        line1 += word + " "
                    else:
                        line2 += word + " "
                line1 = line1.strip()
                line2 = line2.strip()
                
                # Draw box FIRST for two lines - positioned to contain all text
                box_height = 0.11
                box_y = y_pos - 0.085
                ax.add_patch(plt.Rectangle((0.02, box_y), 0.96, box_height,
                                          edgecolor='#00FF00', facecolor='#E0FFE0', linewidth=2))
                
                # Now draw text INSIDE the box
                ax.text(0.5, y_pos - 0.01, 'JUST SELECTED:', ha='center',
                       fontsize=11, fontweight='bold', color='#006600')
                ax.text(0.5, y_pos - 0.035, line1, ha='center',
                       fontsize=10, fontweight='bold', color='#003300')
                ax.text(0.5, y_pos - 0.06, line2, ha='center',
                       fontsize=10, fontweight='bold', color='#003300')
                y_pos -= box_height + line_height * 0.3
            else:
                # Draw box FIRST for single line - positioned to contain text
                box_height = 0.08
                box_y = y_pos - 0.065
                ax.add_patch(plt.Rectangle((0.02, box_y), 0.96, box_height,
                                          edgecolor='#00FF00', facecolor='#E0FFE0', linewidth=2))
                
                # Now draw text INSIDE the box
                ax.text(0.5, y_pos - 0.01, 'JUST SELECTED:', ha='center',
                       fontsize=11, fontweight='bold', color='#006600')
                ax.text(0.5, y_pos - 0.038, current_name, ha='center',
                       fontsize=10, fontweight='bold', color='#003300')
                y_pos -= box_height + line_height * 0.3
                
                # Show subcategory (removed emoji to avoid font warnings)
                subcategory = self.G.nodes[self.current_selection].get('subcategory', 'Unknown')
                subcat_color = get_subcategory_color(subcategory)
                ax.text(0.5, y_pos, f'Category: {subcategory}', ha='center',
                       fontsize=9, style='italic', color=subcat_color, fontweight='bold')
                y_pos -= line_height * 1.5
        
        # Affected neighbors with edge weights
        if self.affected_neighbors:
            ax.text(0.05, y_pos, f"Neighbors affected: {len(self.affected_neighbors)}",
                   fontsize=11, fontweight='bold', color='#FF6B00')
            y_pos -= line_height * 1.5
            
            # Show top 8 affected neighbors with weight and % reduction
            for i, (neighbor_id, old_prio, new_prio) in enumerate(self.affected_neighbors[:8]):
                neighbor_name = self.product_names[neighbor_id]
                if len(neighbor_name) > 18:
                    neighbor_name = neighbor_name[:15] + '...'
                
                # Get edge weight
                edge_weight = 0.0
                if self.current_selection:
                    edge_data = self.G.get_edge_data(self.current_selection, neighbor_id)
                    if edge_data:
                        edge_weight = edge_data.get('weight', 0.0)
                
                # Calculate reduction percentage
                reduction_pct = ((old_prio - new_prio) / old_prio * 100) if old_prio > 0 else 0
                
                # Left side: product name
                ax.text(0.05, y_pos, f"• {neighbor_name}",
                       fontsize=8)
                
                # Right side: weight and priority change (compact format)
                info_text = f"w:{edge_weight:.1f} {old_prio:.0f}→{new_prio:.0f} (-{reduction_pct:.0f}%)"
                ax.text(0.98, y_pos, info_text,
                       fontsize=7.5, ha='right', color='#CC5500', family='monospace')
                y_pos -= line_height * 0.95
            
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
