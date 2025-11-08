"""
Save the selection animation as a GIF file.
"""
from animate_selection import create_animation
from main import setup_graph, create_priority_list_from_sales
import matplotlib.animation as animation
import sys
from io import StringIO

print("=" * 70)
print("CREATING PRODUCT SELECTION ANIMATION")
print("=" * 70)

print("\n1. Setting up graph...")
G = setup_graph(min_edge_weight=5.0)
print(f"   ✓ Graph created: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

print("\n2. Creating priority list from sales data...")
# Suppress detailed output
old_stdout = sys.stdout
sys.stdout = StringIO()
priority_list = create_priority_list_from_sales(G)
sys.stdout = old_stdout
print(f"   ✓ Priority list ready")

print("\n3. Creating animation...")
num_products = 10
anim, fig = create_animation(G, priority_list, num_products=num_products)
print(f"   ✓ Animation created with {num_products} selections")

print("\n4. Saving as GIF...")
print("   This may take a minute...")
try:
    anim.save('product_selection_animation.gif', writer='pillow', fps=0.5, dpi=100)
    print("   ✓ Saved as: product_selection_animation.gif")
    print("\n" + "=" * 70)
    print("SUCCESS! Animation saved.")
    print("=" * 70)
    print("\nYou can now:")
    print("  - Open product_selection_animation.gif to view the animation")
    print("  - Share the GIF file")
    print("  - Use it in presentations")
except Exception as e:
    print(f"   ✗ Error saving GIF: {e}")
    print("   Try installing pillow: pip install pillow")
