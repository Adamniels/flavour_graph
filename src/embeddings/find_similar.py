"""Find similar products using Node2Vec embeddings.

This script demonstrates how to use graph embeddings to find products
that are similar in terms of their graph structure, ingredients, and relationships.

Usage:
    python find_similar_products.py
    python find_similar_products.py --product-id "07310350118342"
    python find_similar_products.py --product-name "Coca Cola"
    python find_similar_products.py --retrain  # Force retraining
"""
import argparse
import os
from pathlib import Path
from src.core import setup_graph
from src.embeddings.embeddings import ProductEmbeddings
from src.config import EMBEDDINGS_MODEL, DEFAULT_EMBEDDING_DIMENSIONS


def find_similar_interactive(G, embeddings, product_id=None, product_name=None, topn=10):
    """Interactive similarity search.
    
    Args:
        G: NetworkX graph
        embeddings: ProductEmbeddings object
        product_id: Specific product ID to search (optional)
        product_name: Search by product name (optional)
        topn: Number of similar products to show
    """
    if product_id is None and product_name is None:
        # Show available products
        print("\n" + "=" * 80)
        print("AVAILABLE PRODUCTS (first 20)")
        print("=" * 80)
        
        for i, (node_id, data) in enumerate(list(G.nodes(data=True))[:20], 1):
            name = data.get('name', node_id)
            subcategory = data.get('subcategory', 'Unknown')
            print(f"{i:2d}. {name[:60]:60s} [{subcategory}]")
            print(f"    ID: {node_id}")
        
        print("\n💡 Tip: Use --product-id or --product-name to search for similar products")
        return
    
    # Find product by name
    if product_name:
        product_id = None
        for node_id, data in G.nodes(data=True):
            name = data.get('name', '').lower()
            if product_name.lower() in name:
                product_id = node_id
                print(f"✓ Found product: {data.get('name', node_id)}")
                break
        
        if product_id is None:
            print(f"❌ Product containing '{product_name}' not found")
            return
    
    # Check if product exists
    if product_id not in G.nodes():
        print(f"❌ Product ID '{product_id}' not found in graph")
        return
    
    # Get product info
    product_data = G.nodes[product_id]
    product_name_display = product_data.get('name', product_id)
    subcategory = product_data.get('subcategory', 'Unknown')
    ingredients = product_data.get('ingredients', [])
    tags = product_data.get('tags', [])
    
    print("\n" + "=" * 80)
    print("QUERY PRODUCT")
    print("=" * 80)
    print(f"Name:        {product_name_display}")
    print(f"ID:          {product_id}")
    print(f"Subcategory: {subcategory}")
    print(f"Tags:        {', '.join(tags) if tags else 'None'}")
    if ingredients:
        print(f"Ingredients: {len(ingredients)} items")
        # Show top 5 ingredients by quantity
        sorted_ing = sorted(ingredients, key=lambda x: x[1], reverse=True)[:5]
        for ing_name, qty in sorted_ing:
            if qty > 0:
                print(f"  - {ing_name}: {qty:.1f}%")
            else:
                print(f"  - {ing_name}")
    
    # Find similar products using embeddings
    print("\n" + "=" * 80)
    print(f"TOP {topn} SIMILAR PRODUCTS (by embedding similarity)")
    print("=" * 80)
    
    similar_products = embeddings.find_similar(product_id, topn=topn)
    
    if not similar_products:
        print("❌ No similar products found")
        return
    
    for i, (sim_id, similarity_score) in enumerate(similar_products, 1):
        sim_data = G.nodes[sim_id]
        sim_name = sim_data.get('name', sim_id)
        sim_subcategory = sim_data.get('subcategory', 'Unknown')
        sim_ingredients = sim_data.get('ingredients', [])
        
        print(f"\n{i}. {sim_name}")
        print(f"   Similarity Score: {similarity_score:.4f}")
        print(f"   ID: {sim_id}")
        print(f"   Subcategory: {sim_subcategory}")
        
        # Show shared ingredients if available
        if ingredients and sim_ingredients:
            ing_names_query = {ing[0] for ing in ingredients}
            ing_names_sim = {ing[0] for ing in sim_ingredients}
            shared = ing_names_query & ing_names_sim
            if shared:
                print(f"   Shared ingredients ({len(shared)}): {', '.join(list(shared)[:5])}")
        
        # Show graph connection if exists
        if G.has_edge(product_id, sim_id):
            edge_weight = G[product_id][sim_id].get('weight', 0)
            print(f"   Graph connection: {edge_weight:.2f}")


def main():
    parser = argparse.ArgumentParser(
        description="Find similar products using Node2Vec embeddings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python find_similar_products.py
  python find_similar_products.py --product-id "07310350118342"
  python find_similar_products.py --product-name "Coca Cola"
  python find_similar_products.py --product-name "Snickers" --topn 5
  python find_similar_products.py --retrain
  python find_similar_products.py --visualize
  python find_similar_products.py --visualize-3d
  python find_similar_products.py --visualize-weights
        """
    )
    
    parser.add_argument('--product-id', type=str, help='Product ID to find similar products for')
    parser.add_argument('--product-name', type=str, help='Product name to search for (partial match)')
    parser.add_argument('--topn', type=int, default=10, help='Number of similar products to show (default: 10)')
    parser.add_argument('--retrain', action='store_true', help='Force retraining of embeddings')
    parser.add_argument('--dimensions', type=int, default=64, help='Embedding dimensions (default: 64)')
    parser.add_argument('--visualize', action='store_true', help='Visualize embeddings in 2D (t-SNE)')
    parser.add_argument('--visualize-3d', action='store_true', help='Visualize embeddings in 3D (t-SNE, interactive)')
    parser.add_argument('--visualize-weights', action='store_true', help='Visualize products by graph weights (3D, interactive)')
    parser.add_argument('--vis-method', type=str, default='tsne', choices=['tsne', 'pca'], 
                       help='Dimensionality reduction method (default: tsne)')
    
    args = parser.parse_args()
    
    # Setup graph
    print("🔧 Setting up flavor graph...")
    G = setup_graph(min_edge_weight=5.0)
    print(f"✓ Graph loaded: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    
    # Check if embeddings exist
    embeddings = ProductEmbeddings(G, dimensions=args.dimensions)
    
    if EMBEDDINGS_MODEL.exists() and not args.retrain:
        print(f"\n📂 Loading existing embeddings from {EMBEDDINGS_MODEL}")
        try:
            embeddings.load()
            print("✓ Embeddings loaded successfully")
        except Exception as e:
            print(f"⚠️ Failed to load embeddings: {e}")
            print("🔧 Training new embeddings...")
            args.retrain = True
    else:
        args.retrain = True
    
    if args.retrain:
        print("\n🚀 Training Node2Vec embeddings...")
        print(f"   Dimensions: {args.dimensions}")
        print("   This may take a few minutes...")
        
        embeddings.train(
            walk_length=30,
            num_walks=200,
            p=1.0,  # Balanced exploration
            q=1.0,
            workers=4
        )
        
        # Save embeddings (uses config paths by default)
        embeddings.save()
        print(f"💾 Embeddings saved to {EMBEDDINGS_MODEL}")
    
    # Visualize embeddings if requested
    if args.visualize:
        print("\n📊 Creating 2D visualization of embeddings (colored by subcategory)...")
        # Use a subset of products for cleaner visualization
        sample_nodes = list(G.nodes())[:100] if G.number_of_nodes() > 100 else list(G.nodes())
        embeddings.visualize_embeddings_2d(
            product_ids=sample_nodes,
            method=args.vis_method,
            show_labels=True,
            color_by_subcategory=True,
            save_path='output/embeddings/embeddings_visualization_2d.png'
        )
    
    if args.visualize_3d:
        print("\n📊 Creating 3D visualization of embeddings (interactive)...")
        # Use more products for 3D (easier to navigate)
        sample_nodes = list(G.nodes())[:200] if G.number_of_nodes() > 200 else list(G.nodes())
        embeddings.visualize_embeddings_3d(
            product_ids=sample_nodes,
            method=args.vis_method,
            color_by_subcategory=True,
            save_path='output/embeddings/embeddings_visualization_3d.html'
        )
    
    if args.visualize_weights:
        print("\n📊 Creating weight-based 3D visualization (using your graph weights)...")
        print("   This shows products positioned by their average:")
        print("   - X-axis: ingredient_match")
        print("   - Y-axis: user_match (co-purchase)")
        print("   - Z-axis: tag_match")
        # Can use all products since this is interactive
        embeddings.visualize_by_weights(
            product_ids=None,  # All products
            color_by_subcategory=True,
            save_path='output/embeddings/embeddings_visualization_weights.html'
        )
    
    # Find similar products
    find_similar_interactive(
        G, 
        embeddings, 
        product_id=args.product_id,
        product_name=args.product_name,
        topn=args.topn
    )
    
    print("\n" + "=" * 80)
    print("✅ Done!")
    print("\n💡 Tips:")
    print("  - Use --product-name to search by product name")
    print("  - Use --topn to adjust number of results")
    print("  - Use --visualize to see embeddings in 2D (colored by category)")
    print("  - Use --visualize-3d for interactive 3D embeddings")
    print("  - Use --visualize-weights to see products by graph weights (ingredient/user/tag)")
    print("=" * 80)


if __name__ == "__main__":
    main()
