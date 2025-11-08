"""Data models for the flavour graph.

Weight: Represents similarity/affinity between products
product_node: Represents a product with attributes (legacy - kept for compatibility)
"""
from typing import List, Tuple
import json
from pathlib import Path


class Weight:
    """Weight object describing similarity/affinity between two products."""

    def __init__(self, ingredient_match: float = 0.0, user_match: float = 0.0, tag_match: float = 0.0):
        self.ingredient_match = float(ingredient_match)
        self.user_match = float(user_match)
        self.tag_match = float(tag_match)

    def score(self) -> float:
        """Combined score used for ranking/selection (simple sum)."""
        return self.ingredient_match + self.user_match + self.tag_match

    def __repr__(self) -> str:
        return f"Weight(ing={self.ingredient_match:.1f}, user={self.user_match:.1f}, tag={self.tag_match:.1f})"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for NetworkX edge attributes."""
        return {
            'ingredient_match': self.ingredient_match,
            'user_match': self.user_match,
            'tag_match': self.tag_match,
            'weight': self.score()  # total weight for algorithms
        }

class UserGroupWeight:
    """Reads co-purchase data and calculates user similarity between products."""
    
    def __init__(self, json_path: str = None):
        """Load product relations from JSON file.
        
        Args:
            json_path: Path to product_relations.json (default: ./product_relations.json in workspace)
        """
        if json_path is None:
            # Default to data folder in workspace root
            json_path = Path(__file__).parent / 'data' / 'product_relations.json'
        
        self.relations = {}
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                self.relations = json.load(f)
            print(f"✅ Loaded {len(self.relations)} products from {json_path}")
        except FileNotFoundError:
            print(f"⚠️ Warning: {json_path} not found. UserGroupWeight will return 0.")
    
    def get_weight(self, ean_1: str, ean_2: str, normalize: bool = True) -> float:
        """Calculate user similarity weight between two products.
        
        Args:
            ean_1: First product EAN (with leading 0, e.g. '07310350118342')
            ean_2: Second product EAN
            normalize: If True, apply log-scaling to reduce extreme values
            
        Returns:
            Float weight representing how often products are bought together
        """
        if ean_1 not in self.relations:
            return 0.0
        
        # Find ean_2 in ean_1's related products
        for related in self.relations[ean_1].get('related_products', []):
            if related['product'] == ean_2:
                count = related['co_purchase_count']
                
                if normalize:
                    # Log-scale to prevent very popular products dominating
                    import math
                    return math.log(count + 1)  # +1 to avoid log(0)
                else:
                    return float(count)
        
        return 0.0
    
    def get_top_related(self, ean: str, n: int = 5) -> List[Tuple[str, int]]:
        """Get top N related products for a given EAN.
        
        Returns:
            List of (ean, co_purchase_count) tuples
        """
        if ean not in self.relations:
            return []
        
        related = self.relations[ean].get('related_products', [])
        return [(p['product'], p['co_purchase_count']) for p in related[:n]]


class product_node:
    """Represents a single product node (legacy class - consider using NetworkX directly)."""

    def __init__(self, id: str, prio: int = 0, tags: List[str] = None, ingredients: List[str] = None):
        self.id = id
        self.prio = int(prio)
        self.tags = list(tags) if tags else []
        self.ingredients = list(ingredients) if ingredients else []
        self.links: List[Tuple['product_node', Weight]] = []

    def add_link(self, other: 'product_node', weight: Weight):
        self.links.append((other, weight))

    def to_dict(self) -> dict:
        """Convert to dictionary for NetworkX node attributes."""
        return {
            'prio': self.prio,
            'tags': self.tags,
            'ingredients': self.ingredients
        }

    def __repr__(self) -> str:
        return f"product_node(id={self.id!r}, prio={self.prio}, tags={self.tags}, ingredients={self.ingredients})"


#indexerbar hjälparklass för ID -> integer, sortering och indexering
class IndexedPriorityList:
    """Håller (id, value)-par, kan sorteras och indexeras.
    
    Exempel:
        idx = IndexedPriorityList.from_nodes(G.nodes(data=True), key='prio')
        idx.sort(reverse=True)
        top3_ids = idx.top(3)
        first_item = idx[0]  # (id, value)
    """
    def __init__(self, items):
        # items: list[tuple[id, int]]
        self._items = list(items)

    @classmethod
    def from_nodes(cls, nodes_iterable, key: str = 'prio'):
        items = [(node_id, int(data.get(key, 0))) for node_id, data in nodes_iterable]
        return cls(items)

    def sort(self, reverse: bool = True):
        self._items.sort(key=lambda x: x[1], reverse=reverse)

    # to get highest use case, use top(1)
    def top(self, n: int) -> List[str]:
        return [node_id for node_id, _ in self._items[:max(0, int(n))]]

    def ids(self) -> List[str]:
        return [node_id for node_id, _ in self._items]
    
    def half_prio(self, node_id: str):
        for i, (nid, val) in enumerate(self._items):
            if nid == node_id:
                self._items[i] = (nid, val // 2)
                break
    
    def __len__(self):
        return len(self._items)

    def remove(self, node_id: str):
        """Remove a product from the priority list."""
        self._items = [(nid, val) for nid, val in self._items if nid != node_id]

    # insert or update a product with its sales number as priority
    def insert_by_sales(self, product_id: str, sales_number: int):
        # Check if product already exists
        for i, (nid, val) in enumerate(self._items):
            if nid == product_id:
                self._items[i] = (nid, int(sales_number))
                self.sort(reverse=True)
                return
            
        # Product doesn't exist, insert new entry
        self._items.append((product_id, int(sales_number)))
        self.sort(reverse=True)

    def __getitem__(self, idx):
        return self._items[idx]
    

