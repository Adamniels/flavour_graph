"""Data models for the flavour graph.

Weight: Represents similarity/affinity between products
product_node: Represents a product with attributes (legacy - kept for compatibility)
"""
from typing import List, Tuple


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
