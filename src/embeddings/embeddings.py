"""Graph embeddings using Node2Vec for product similarity search.

This module creates X-dimensional vector representations of products from the flavor graph.
These embeddings capture the graph structure and allow us to find similar products
using vector similarity measures.

Node2Vec works by:
1. Performing biased random walks on the graph (exploring both breadth and depth)
2. Treating walks as "sentences" and nodes as "words"
3. Using Word2Vec (Skip-gram) to learn embeddings

The resulting vectors encode:
- Direct connections (which products are linked)
- Graph structure (clusters and communities)
- Edge weights (stronger connections = closer in vector space)
"""
import networkx as nx
import numpy as np
from node2vec import Node2Vec
from typing import List, Tuple, Optional, Dict
import pickle
import os
from pathlib import Path
from src.config import DEFAULT_EMBEDDING_DIMENSIONS, EMBEDDINGS_MODEL, EMBEDDINGS_WORD2VEC


class ProductEmbeddings:
    """Manages Node2Vec embeddings for the flavor graph."""
    
    def __init__(self, G: nx.DiGraph = None, dimensions: int = None):
        """Initialize embeddings.
        
        Args:
            G: NetworkX graph (optional, can be loaded later)
            dimensions: Dimensionality of the embedding vectors (default: from config.DEFAULT_EMBEDDING_DIMENSIONS)
        """
        self.G = G
        self.dimensions = dimensions if dimensions is not None else DEFAULT_EMBEDDING_DIMENSIONS
        self.model = None
        self.node2vec = None
        
    def train(self, 
              walk_length: int = 30,
              num_walks: int = 200,
              p: float = 1.0,
              q: float = 1.0,
              workers: int = 4,
              window: int = 10,
              min_count: int = 1,
              batch_words: int = 4) -> None:
        """Train Node2Vec embeddings on the graph.
        
        Args:
            walk_length: Length of each random walk (default: 30)
            num_walks: Number of walks per node (default: 200)
            p: Return parameter - controls likelihood of returning to previous node
               p > 1: less likely to sample already visited nodes (BFS-like)
               p < 1: more likely to return (local exploration)
            q: In-out parameter - controls exploration vs exploitation
               q > 1: stay close to starting node (BFS-like, local structure)
               q < 1: move outward (DFS-like, explore distant nodes)
            workers: Number of parallel workers
            window: Context window size for Word2Vec
            min_count: Minimum count for Word2Vec
            batch_words: Batch size for Word2Vec training
            
        Example parameter settings:
            - BFS (explore local neighborhood): p=1, q=2
            - DFS (explore distant nodes): p=1, q=0.5
            - Balanced (default): p=1, q=1
        """
        if self.G is None:
            raise ValueError("Graph not set. Call set_graph() first.")
        
        print(f"🔧 Training Node2Vec with {self.dimensions} dimensions...")
        print(f"   Parameters: walk_length={walk_length}, num_walks={num_walks}, p={p}, q={q}")
        print(f"   Graph: {self.G.number_of_nodes()} nodes, {self.G.number_of_edges()} edges")
        
        # Initialize Node2Vec
        # weight_key='weight' uses our edge weights during random walks
        self.node2vec = Node2Vec(
            self.G,
            dimensions=self.dimensions,
            walk_length=walk_length,
            num_walks=num_walks,
            p=p,
            q=q,
            workers=workers,
            weight_key='weight',  # Use edge weights from our graph
            quiet=False
        )
        
        # Train the Word2Vec model on the walks
        print("🚶 Generating random walks...")
        self.model = self.node2vec.fit(
            window=window,
            min_count=min_count,
            batch_words=batch_words,
            epochs=10  # Number of training epochs
        )
        
        print(f"✅ Training complete! Embeddings shape: ({len(self.model.wv)}, {self.dimensions})")
    
    def set_graph(self, G: nx.DiGraph) -> None:
        """Set the graph to use for embeddings."""
        self.G = G
        
    def get_embedding(self, product_id: str) -> Optional[np.ndarray]:
        """Get the embedding vector for a product.
        
        Args:
            product_id: Product identifier (node ID in graph)
            
        Returns:
            Numpy array of shape (dimensions,) or None if not found
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        try:
            return self.model.wv[product_id]
        except KeyError:
            return None
    
    def find_similar(self, 
                     product_id: str, 
                     topn: int = 10,
                     include_score: bool = True) -> List[Tuple[str, float]]:
        """Find the most similar products to a given product using embeddings.
        
        This uses cosine similarity in the embedding space. Products that are
        structurally similar in the graph will have similar embeddings.
        
        Args:
            product_id: Product identifier to find similar products for
            topn: Number of similar products to return
            include_score: If True, return (product_id, similarity_score) tuples
                          If False, return just product_id list
            
        Returns:
            List of (product_id, similarity_score) tuples, sorted by similarity
            Similarity scores range from 0 (unrelated) to 1 (identical)
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        try:
            similar = self.model.wv.most_similar(product_id, topn=topn)
            if include_score:
                return similar
            else:
                return [prod_id for prod_id, _ in similar]
        except KeyError:
            print(f"⚠️ Product {product_id} not found in embeddings")
            return []
    
    def find_similar_by_vector(self, 
                               vector: np.ndarray, 
                               topn: int = 10) -> List[Tuple[str, float]]:
        """Find products similar to a given embedding vector.
        
        Useful for finding products similar to a custom combination or average.
        
        Args:
            vector: Embedding vector (shape: dimensions,)
            topn: Number of results to return
            
        Returns:
            List of (product_id, similarity_score) tuples
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        return self.model.wv.similar_by_vector(vector, topn=topn)
    
    def get_average_embedding(self, product_ids: List[str]) -> Optional[np.ndarray]:
        """Get the average embedding of multiple products.
        
        Useful for finding products similar to a group/bundle.
        
        Args:
            product_ids: List of product identifiers
            
        Returns:
            Average embedding vector or None if no valid products
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        vectors = []
        for prod_id in product_ids:
            try:
                vectors.append(self.model.wv[prod_id])
            except KeyError:
                print(f"⚠️ Product {prod_id} not in embeddings, skipping")
        
        if not vectors:
            return None
        
        return np.mean(vectors, axis=0)
    
    def compute_similarity(self, product_id1: str, product_id2: str) -> Optional[float]:
        """Compute cosine similarity between two products.
        
        Args:
            product_id1: First product identifier
            product_id2: Second product identifier
            
        Returns:
            Similarity score between 0 and 1, or None if products not found
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        try:
            return self.model.wv.similarity(product_id1, product_id2)
        except KeyError:
            return None
    
    def save(self, filepath: Path = None) -> None:
        """Save the trained embeddings model to disk.
        
        Args:
            filepath: Path to save the model (default: from config.EMBEDDINGS_MODEL)
        """
        if filepath is None:
            filepath = EMBEDDINGS_MODEL
            model_path = EMBEDDINGS_WORD2VEC
        else:
            # Support custom paths with .pkl/.model pairs
            filepath = Path(filepath)
            model_path = filepath.with_suffix('.model')
            
        if self.model is None:
            raise ValueError("No model to save. Train first.")
        
        # Save the Word2Vec model
        self.model.save(str(model_path))
        
        # Save metadata
        metadata = {
            'dimensions': self.dimensions,
            'num_nodes': self.G.number_of_nodes() if self.G else 0,
            'num_edges': self.G.number_of_edges() if self.G else 0,
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(metadata, f)
        
        print(f"💾 Saved embeddings to {model_path} and metadata to {filepath}")
    
    def load(self, filepath: Path = None) -> None:
        """Load a trained embeddings model from disk.
        
        Args:
            filepath: Path to the saved model (default: from config.EMBEDDINGS_MODEL)
        """
        from gensim.models import Word2Vec
        
        if filepath is None:
            filepath = EMBEDDINGS_MODEL
            model_path = EMBEDDINGS_WORD2VEC
        else:
            # Support custom paths with .pkl/.model pairs
            filepath = Path(filepath)
            model_path = filepath.with_suffix('.model')
        
        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        self.model = Word2Vec.load(str(model_path))
        
        # Load metadata
        if filepath.exists():
            with open(filepath, 'rb') as f:
                metadata = pickle.load(f)
                self.dimensions = metadata.get('dimensions', DEFAULT_EMBEDDING_DIMENSIONS)
        
        print(f"📂 Loaded embeddings from {model_path}")
        print(f"   Dimensions: {self.dimensions}")
        print(f"   Vocabulary size: {len(self.model.wv)}")
    
    def visualize_embeddings_2d(self,
                                product_ids: List[str] = None,
                                method: str = 'tsne',
                                figsize: tuple = (12, 10),
                                show_labels: bool = False,
                                save_path: str = None,
                                color_by_subcategory: bool = True,
                                interactive: bool = True):
        """Visualize embeddings in 2D using dimensionality reduction.
        
        Args:
            product_ids: List of product IDs to visualize (None = all)
            method: 'tsne' or 'pca' for dimensionality reduction
            figsize: Figure size (width, height) - used for matplotlib only
            show_labels: If True, show product names as labels (matplotlib only)
            save_path: Path to save the figure (optional)
            color_by_subcategory: If True, color points by subcategory
            interactive: If True, create interactive plotly visualization with hover info
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        from sklearn.manifold import TSNE
        from sklearn.decomposition import PCA
        from src.core import get_subcategory_color
        
        # Get embeddings
        if product_ids is None:
            product_ids = list(self.model.wv.index_to_key)
        
        vectors = np.array([self.model.wv[pid] for pid in product_ids])
        
        # Reduce to 2D
        print(f"Reducing {len(product_ids)} embeddings to 2D using {method.upper()}...")
        if method == 'tsne':
            reducer = TSNE(n_components=2, random_state=42, perplexity=min(30, len(product_ids)-1))
        else:  # pca
            reducer = PCA(n_components=2, random_state=42)
        
        coords_2d = reducer.fit_transform(vectors)
        
        if interactive:
            # Create interactive plotly visualization
            try:
                import plotly.graph_objects as go
                from collections import defaultdict
                
                if color_by_subcategory and self.G:
                    subcategory_to_data = defaultdict(lambda: {'x': [], 'y': [], 'names': [], 'ids': [], 'info': []})
                    
                    for i, pid in enumerate(product_ids):
                        subcategory = self.G.nodes[pid].get('subcategory', 'Unknown')
                        name = self.G.nodes[pid].get('name', pid)
                        
                        # Build hover info with product details
                        tags = self.G.nodes[pid].get('tags', [])
                        ingredients = self.G.nodes[pid].get('ingredients', [])
                        
                        hover_text = f"<b>{name}</b><br>"
                        hover_text += f"ID: {pid}<br>"
                        hover_text += f"Category: {subcategory}<br>"
                        if tags:
                            hover_text += f"Tags: {', '.join(tags[:3])}"
                            if len(tags) > 3:
                                hover_text += f" (+{len(tags)-3} more)"
                            hover_text += "<br>"
                        if ingredients:
                            ing_list = [ing if isinstance(ing, str) else str(ing) for ing in ingredients[:3]]
                            hover_text += f"Ingredients: {', '.join(ing_list)}"
                            if len(ingredients) > 3:
                                hover_text += f" (+{len(ingredients)-3} more)"
                        
                        subcategory_to_data[subcategory]['x'].append(coords_2d[i, 0])
                        subcategory_to_data[subcategory]['y'].append(coords_2d[i, 1])
                        subcategory_to_data[subcategory]['names'].append(name)
                        subcategory_to_data[subcategory]['ids'].append(pid)
                        subcategory_to_data[subcategory]['info'].append(hover_text)
                    
                    # Create traces for each subcategory
                    traces = []
                    for subcategory, data in subcategory_to_data.items():
                        color = get_subcategory_color(subcategory)
                        
                        trace = go.Scatter(
                            x=data['x'],
                            y=data['y'],
                            mode='markers',
                            name=subcategory,
                            marker=dict(
                                size=8,
                                color=color,
                                line=dict(color='white', width=0.5),
                                opacity=0.8
                            ),
                            text=data['info'],
                            hovertemplate='%{text}<extra></extra>'
                        )
                        traces.append(trace)
                else:
                    # Simple plot without colors
                    names = [self.G.nodes[pid].get('name', pid) if self.G else pid for pid in product_ids]
                    hover_texts = []
                    for pid in product_ids:
                        name = self.G.nodes[pid].get('name', pid) if self.G else pid
                        hover_texts.append(f"<b>{name}</b><br>ID: {pid}")
                    
                    trace = go.Scatter(
                        x=coords_2d[:, 0],
                        y=coords_2d[:, 1],
                        mode='markers',
                        marker=dict(size=8, opacity=0.8),
                        text=hover_texts,
                        hovertemplate='%{text}<extra></extra>'
                    )
                    traces = [trace]
                
                # Create figure
                fig = go.Figure(data=traces)
                
                fig.update_layout(
                    title=f'Product Embeddings Visualization ({method.upper()})',
                    xaxis_title='Component 1',
                    yaxis_title='Component 2',
                    width=1400,
                    height=900,
                    hovermode='closest',
                    legend=dict(
                        yanchor="top",
                        y=0.99,
                        xanchor="left",
                        x=1.01
                    )
                )
                
                if save_path:
                    # Save as HTML for interactive visualization
                    html_path = str(save_path).replace('.png', '.html')
                    fig.write_html(html_path)
                    print(f"Saved interactive visualization to {html_path}")
                
                fig.show()
                return  # Exit after showing interactive visualization
                
            except ImportError:
                print("⚠️ plotly not installed. Falling back to matplotlib. Install with: pip install plotly")
                interactive = False
        
        if not interactive:
            # Fallback to matplotlib
            import matplotlib.pyplot as plt
            
            # Get colors by subcategory if requested
            if color_by_subcategory and self.G:
                from collections import defaultdict
                subcategory_to_products = defaultdict(list)
                
                for i, pid in enumerate(product_ids):
                    subcategory = self.G.nodes[pid].get('subcategory', 'Unknown')
                    subcategory_to_products[subcategory].append(i)
                
                # Plot
                fig, ax = plt.subplots(figsize=figsize)
                
                # Plot each subcategory with its own color
                for subcategory, indices in subcategory_to_products.items():
                    color = get_subcategory_color(subcategory)
                    subcat_coords = coords_2d[indices]
                    ax.scatter(subcat_coords[:, 0], subcat_coords[:, 1], 
                              c=[color], label=subcategory, alpha=0.7, s=80, edgecolors='white', linewidth=0.5)
                
                # Add legend
                ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9, framealpha=0.9)
            else:
                # Simple plot without colors
                fig, ax = plt.subplots(figsize=figsize)
                ax.scatter(coords_2d[:, 0], coords_2d[:, 1], alpha=0.6, s=50)
            
            # Add labels
            if show_labels and self.G:
                for i, pid in enumerate(product_ids):
                    name = self.G.nodes[pid].get('name', pid)
                    # Truncate long names
                    if len(name) > 25:
                        name = name[:22] + '...'
                    ax.annotate(name, (coords_2d[i, 0], coords_2d[i, 1]),
                               fontsize=6, alpha=0.6)
            
            ax.set_title(f'Product Embeddings Visualization ({method.upper()})', fontsize=16, fontweight='bold')
            ax.set_xlabel('Component 1', fontsize=12)
            ax.set_ylabel('Component 2', fontsize=12)
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                print(f"Saved visualization to {save_path}")
            
            plt.show()
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        import matplotlib.pyplot as plt
        from sklearn.manifold import TSNE
        from sklearn.decomposition import PCA
        from src.core import get_subcategory_color
        
        # Get embeddings
        if product_ids is None:
            product_ids = list(self.model.wv.index_to_key)
        
        vectors = np.array([self.model.wv[pid] for pid in product_ids])
        
        # Reduce to 2D
        print(f"Reducing {len(product_ids)} embeddings to 2D using {method.upper()}...")
        if method == 'tsne':
            reducer = TSNE(n_components=2, random_state=42, perplexity=min(30, len(product_ids)-1))
        else:  # pca
            reducer = PCA(n_components=2, random_state=42)
        
        coords_2d = reducer.fit_transform(vectors)
        
        # Get colors by subcategory if requested
        if color_by_subcategory and self.G:
            from collections import defaultdict
            subcategory_to_products = defaultdict(list)
            
            for i, pid in enumerate(product_ids):
                subcategory = self.G.nodes[pid].get('subcategory', 'Unknown')
                subcategory_to_products[subcategory].append(i)
            
            # Plot
            fig, ax = plt.subplots(figsize=figsize)
            
            # Plot each subcategory with its own color
            for subcategory, indices in subcategory_to_products.items():
                color = get_subcategory_color(subcategory)
                subcat_coords = coords_2d[indices]
                ax.scatter(subcat_coords[:, 0], subcat_coords[:, 1], 
                          c=[color], label=subcategory, alpha=0.7, s=80, edgecolors='white', linewidth=0.5)
            
            # Add legend
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9, framealpha=0.9)
        else:
            # Simple plot without colors
            fig, ax = plt.subplots(figsize=figsize)
            ax.scatter(coords_2d[:, 0], coords_2d[:, 1], alpha=0.6, s=50)
        
        # Add labels
        if show_labels and self.G:
            for i, pid in enumerate(product_ids):
                name = self.G.nodes[pid].get('name', pid)
                # Truncate long names
                if len(name) > 25:
                    name = name[:22] + '...'
                ax.annotate(name, (coords_2d[i, 0], coords_2d[i, 1]),
                           fontsize=6, alpha=0.6)
        
        ax.set_title(f'Product Embeddings Visualization ({method.upper()})', fontsize=16, fontweight='bold')
        ax.set_xlabel('Component 1', fontsize=12)
        ax.set_ylabel('Component 2', fontsize=12)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Saved visualization to {save_path}")
        
        plt.show()
    
    def visualize_embeddings_3d(self,
                                product_ids: List[str] = None,
                                method: str = 'tsne',
                                save_path: str = None,
                                color_by_subcategory: bool = True):
        """Visualize embeddings in 3D using dimensionality reduction (interactive with plotly).
        
        Args:
            product_ids: List of product IDs to visualize (None = all)
            method: 'tsne' or 'pca' for dimensionality reduction
            save_path: Path to save HTML file (optional)
            color_by_subcategory: If True, color points by subcategory
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        try:
            import plotly.graph_objects as go
            from sklearn.manifold import TSNE
            from sklearn.decomposition import PCA
            from src.core import get_subcategory_color
        except ImportError:
            print("⚠️ plotly not installed. Install with: pip install plotly")
            return
        
        # Get embeddings
        if product_ids is None:
            product_ids = list(self.model.wv.index_to_key)
        
        vectors = np.array([self.model.wv[pid] for pid in product_ids])
        
        # Reduce to 3D
        print(f"Reducing {len(product_ids)} embeddings to 3D using {method.upper()}...")
        if method == 'tsne':
            reducer = TSNE(n_components=3, random_state=42, perplexity=min(30, len(product_ids)-1))
        else:  # pca
            reducer = PCA(n_components=3, random_state=42)
        
        coords_3d = reducer.fit_transform(vectors)
        
        # Prepare data for plotly
        if color_by_subcategory and self.G:
            from collections import defaultdict
            subcategory_to_data = defaultdict(lambda: {'x': [], 'y': [], 'z': [], 'names': [], 'ids': [], 'info': []})
            
            for i, pid in enumerate(product_ids):
                subcategory = self.G.nodes[pid].get('subcategory', 'Unknown')
                name = self.G.nodes[pid].get('name', pid)
                
                # Build detailed hover info
                tags = self.G.nodes[pid].get('tags', [])
                ingredients = self.G.nodes[pid].get('ingredients', [])
                
                hover_text = f"<b>{name}</b><br>"
                hover_text += f"ID: {pid}<br>"
                hover_text += f"Category: {subcategory}<br>"
                if tags:
                    hover_text += f"Tags: {', '.join(tags[:3])}"
                    if len(tags) > 3:
                        hover_text += f" (+{len(tags)-3} more)"
                    hover_text += "<br>"
                if ingredients:
                    ing_list = [ing if isinstance(ing, str) else str(ing) for ing in ingredients[:3]]
                    hover_text += f"Ingredients: {', '.join(ing_list)}"
                    if len(ingredients) > 3:
                        hover_text += f" (+{len(ingredients)-3} more)"
                
                subcategory_to_data[subcategory]['x'].append(coords_3d[i, 0])
                subcategory_to_data[subcategory]['y'].append(coords_3d[i, 1])
                subcategory_to_data[subcategory]['z'].append(coords_3d[i, 2])
                subcategory_to_data[subcategory]['names'].append(name)
                subcategory_to_data[subcategory]['ids'].append(pid)
                subcategory_to_data[subcategory]['info'].append(hover_text)
            
            # Create traces for each subcategory
            traces = []
            for subcategory, data in subcategory_to_data.items():
                color = get_subcategory_color(subcategory)
                
                trace = go.Scatter3d(
                    x=data['x'],
                    y=data['y'],
                    z=data['z'],
                    mode='markers',
                    name=subcategory,
                    marker=dict(
                        size=6,
                        color=color,
                        line=dict(color='white', width=0.5),
                        opacity=0.8
                    ),
                    text=data['info'],
                    hovertemplate='%{text}<extra></extra>'
                )
                traces.append(trace)
        else:
            # Simple plot without colors
            hover_texts = []
            for pid in product_ids:
                name = self.G.nodes[pid].get('name', pid) if self.G else pid
                hover_text = f"<b>{name}</b><br>ID: {pid}"
                hover_texts.append(hover_text)
            
            trace = go.Scatter3d(
                x=coords_3d[:, 0],
                y=coords_3d[:, 1],
                z=coords_3d[:, 2],
                mode='markers',
                marker=dict(size=5, opacity=0.8),
                text=hover_texts,
                hovertemplate='%{text}<extra></extra>'
            )
            traces = [trace]
        
        # Create figure
        fig = go.Figure(data=traces)
        
        fig.update_layout(
            title=f'Product Embeddings 3D Visualization ({method.upper()})',
            scene=dict(
                xaxis_title='Component 1',
                yaxis_title='Component 2',
                zaxis_title='Component 3'
            ),
            width=1200,
            height=800,
            hovermode='closest'
        )
        
        if save_path:
            fig.write_html(save_path)
            print(f"Saved 3D visualization to {save_path}")
        
        fig.show()
    
    def visualize_by_weights(self,
                            product_ids: List[str] = None,
                            save_path: str = None,
                            color_by_subcategory: bool = True):
        """Visualize products in 3D using actual graph weights as dimensions.
        
        This creates a more interpretable visualization where axes represent:
        - X-axis: Average ingredient_match with neighbors
        - Y-axis: Average user_match (co-purchase) with neighbors
        - Z-axis: Average tag_match with neighbors
        
        Args:
            product_ids: List of product IDs to visualize (None = all)
            save_path: Path to save HTML file (optional)
            color_by_subcategory: If True, color points by subcategory
        """
        if self.G is None:
            raise ValueError("Graph not set. Cannot compute weights.")
        
        try:
            import plotly.graph_objects as go
            from src.core import get_subcategory_color
        except ImportError:
            print("⚠️ plotly not installed. Install with: pip install plotly")
            return
        
        if product_ids is None:
            product_ids = list(self.G.nodes())
        
        print(f"Computing weight-based coordinates for {len(product_ids)} products...")
        
        # Compute average weights for each product
        weight_coords = []
        valid_products = []
        
        for pid in product_ids:
            if pid not in self.G:
                continue
            
            neighbors = list(self.G.neighbors(pid))
            if not neighbors:
                continue
            
            # Calculate average weights with all neighbors
            total_ing = 0.0
            total_user = 0.0
            total_tag = 0.0
            
            for neighbor in neighbors:
                edge_data = self.G[pid][neighbor]
                total_ing += edge_data.get('ingredient_match', 0)
                total_user += edge_data.get('user_match', 0)
                total_tag += edge_data.get('tag_match', 0)
            
            n = len(neighbors)
            avg_ing = total_ing / n
            avg_user = total_user / n
            avg_tag = total_tag / n
            
            weight_coords.append([avg_ing, avg_user, avg_tag])
            valid_products.append(pid)
        
        weight_coords = np.array(weight_coords)
        
        print(f"✓ Computed coordinates for {len(valid_products)} products")
        print(f"  Ingredient range: {weight_coords[:, 0].min():.2f} - {weight_coords[:, 0].max():.2f}")
        print(f"  User match range: {weight_coords[:, 1].min():.2f} - {weight_coords[:, 1].max():.2f}")
        print(f"  Tag match range: {weight_coords[:, 2].min():.2f} - {weight_coords[:, 2].max():.2f}")
        
        # Prepare data for plotly
        if color_by_subcategory:
            from collections import defaultdict
            subcategory_to_data = defaultdict(lambda: {'x': [], 'y': [], 'z': [], 'names': [], 'ids': [], 'info': []})
            
            for i, pid in enumerate(valid_products):
                subcategory = self.G.nodes[pid].get('subcategory', 'Unknown')
                name = self.G.nodes[pid].get('name', pid)
                
                # Build detailed hover info
                tags = self.G.nodes[pid].get('tags', [])
                ingredients = self.G.nodes[pid].get('ingredients', [])
                
                hover_text = f"<b>{name}</b><br>"
                hover_text += f"ID: {pid}<br>"
                hover_text += f"Category: {subcategory}<br><br>"
                hover_text += f"<b>Average Weights:</b><br>"
                hover_text += f"Ingredient Match: {weight_coords[i, 0]:.2f}<br>"
                hover_text += f"User Co-purchase: {weight_coords[i, 1]:.2f}<br>"
                hover_text += f"Tag Match: {weight_coords[i, 2]:.2f}<br>"
                if tags:
                    hover_text += f"<br>Tags: {', '.join(tags[:3])}"
                    if len(tags) > 3:
                        hover_text += f" (+{len(tags)-3} more)"
                if ingredients:
                    ing_list = [ing if isinstance(ing, str) else str(ing) for ing in ingredients[:3]]
                    hover_text += f"<br>Ingredients: {', '.join(ing_list)}"
                    if len(ingredients) > 3:
                        hover_text += f" (+{len(ingredients)-3} more)"
                
                subcategory_to_data[subcategory]['x'].append(weight_coords[i, 0])
                subcategory_to_data[subcategory]['y'].append(weight_coords[i, 1])
                subcategory_to_data[subcategory]['z'].append(weight_coords[i, 2])
                subcategory_to_data[subcategory]['names'].append(name)
                subcategory_to_data[subcategory]['ids'].append(pid)
                subcategory_to_data[subcategory]['info'].append(hover_text)
            
            # Create traces for each subcategory
            traces = []
            for subcategory, data in subcategory_to_data.items():
                color = get_subcategory_color(subcategory)
                
                trace = go.Scatter3d(
                    x=data['x'],
                    y=data['y'],
                    z=data['z'],
                    mode='markers',
                    name=subcategory,
                    marker=dict(
                        size=6,
                        color=color,
                        line=dict(color='white', width=0.5),
                        opacity=0.8
                    ),
                    text=data['info'],
                    hovertemplate='%{text}<extra></extra>'
                )
                traces.append(trace)
        else:
            # Simple plot without colors
            hover_texts = []
            for i, pid in enumerate(valid_products):
                name = self.G.nodes[pid].get('name', pid)
                hover_text = f"<b>{name}</b><br>ID: {pid}<br><br>"
                hover_text += f"Avg Ingredient: {weight_coords[i, 0]:.2f}<br>"
                hover_text += f"Avg User: {weight_coords[i, 1]:.2f}<br>"
                hover_text += f"Avg Tag: {weight_coords[i, 2]:.2f}"
                hover_texts.append(hover_text)
            
            names = [self.G.nodes[pid].get('name', pid) for pid in valid_products]
            trace = go.Scatter3d(
                x=weight_coords[:, 0],
                y=weight_coords[:, 1],
                z=weight_coords[:, 2],
                mode='markers',
                marker=dict(size=5, opacity=0.8),
                text=hover_texts,
                hovertemplate='%{text}<extra></extra>'
            )
            traces = [trace]
        
        # Create figure
        fig = go.Figure(data=traces)
        
        fig.update_layout(
            title='Product Relationships by Graph Weights (3D)',
            scene=dict(
                xaxis_title='Avg Ingredient Match',
                yaxis_title='Avg User Match (Co-purchase)',
                zaxis_title='Avg Tag Match'
            ),
            width=1200,
            height=800,
            hovermode='closest'
        )
        
        if save_path:
            fig.write_html(save_path)
            print(f"Saved weight-based visualization to {save_path}")
        
        fig.show()
    
    def get_stats(self) -> Dict:
        """Get statistics about the embeddings.
        
        Returns:
            Dictionary with embedding statistics
        """
        if self.model is None:
            return {"status": "not_trained"}
        
        return {
            "status": "trained",
            "dimensions": self.dimensions,
            "vocabulary_size": len(self.model.wv),
            "vector_size": self.model.wv.vector_size,
        }


def create_embeddings_from_graph(G: nx.DiGraph, 
                                 dimensions: int = 64,
                                 save_path: str = None) -> ProductEmbeddings:
    """Convenience function to create and train embeddings from a graph.
    
    Args:
        G: NetworkX directed graph
        dimensions: Embedding dimensions
        save_path: Path to save the trained model (optional)
        
    Returns:
        Trained ProductEmbeddings object
    """
    embeddings = ProductEmbeddings(G, dimensions=dimensions)
    embeddings.train(
        walk_length=30,
        num_walks=200,
        p=1.0,  # Balanced exploration
        q=1.0,
        workers=4
    )
    
    if save_path:
        embeddings.save(save_path)
    
    return embeddings


if __name__ == "__main__":
    # Demo: Create embeddings from the flavor graph
    from src.core import setup_graph
    
    print("=" * 60)
    print("CREATING PRODUCT EMBEDDINGS WITH NODE2VEC")
    print("=" * 60)
    
    # Create graph
    print("\n1. Setting up flavor graph...")
    G = setup_graph(min_edge_weight=5.0)
    
    # Create and train embeddings
    print("\n2. Training Node2Vec embeddings...")
    embeddings = ProductEmbeddings(G, dimensions=64)
    embeddings.train(
        walk_length=30,
        num_walks=200,
        p=1.0,
        q=1.0
    )
    
    # Save embeddings
    print("\n3. Saving embeddings...")
    embeddings.save("data/embeddings_model.pkl")
    
    # Test similarity search
    print("\n4. Testing similarity search...")
    print("\nFinding 5 most similar products to first product in graph:")
    first_product = list(G.nodes())[0]
    first_product_name = G.nodes[first_product].get('name', first_product)
    print(f"Query product: {first_product_name} ({first_product})")
    
    similar = embeddings.find_similar(first_product, topn=5)
    print("\nMost similar products:")
    for i, (prod_id, score) in enumerate(similar, 1):
        prod_name = G.nodes[prod_id].get('name', prod_id)
        print(f"  {i}. {prod_name[:50]:50s} (similarity: {score:.3f})")
    
    # Test with a few more products
    print("\n" + "=" * 60)
    print("TESTING WITH MULTIPLE PRODUCTS")
    print("=" * 60)
    
    test_products = list(G.nodes())[:3]
    for prod_id in test_products:
        prod_name = G.nodes[prod_id].get('name', prod_id)
        print(f"\n📦 Product: {prod_name}")
        print(f"   ID: {prod_id}")
        
        similar = embeddings.find_similar(prod_id, topn=3)
        print("   Top 3 similar products:")
        for i, (sim_id, score) in enumerate(similar, 1):
            sim_name = G.nodes[sim_id].get('name', sim_id)
            print(f"     {i}. {sim_name[:45]:45s} ({score:.3f})")
    
    print("\n✅ Embeddings created successfully!")
    print("💡 Use find_similar_products.py to search for similar products")
