# Core Module Architecture

The `src/core` module has been refactored into focused, single-responsibility modules for better maintainability and clarity.

## Module Overview

### 📊 **graph_setup.py** - High-level orchestration
**Purpose:** Main entry points for creating the product graph and priority lists.

**Key Functions:**
- `setup_graph(min_edge_weight=5.0)` - Creates complete product graph with nodes and edges
- `create_priority_list_from_sales(G, sales_file=None)` - Creates priority list from sales data

**Usage:**
```python
from src.core import setup_graph, create_priority_list_from_sales

# Create graph
G = setup_graph(min_edge_weight=6.0)

# Create priority list from sales
priorities = create_priority_list_from_sales(G)
```

---

### 🎯 **selection_algorithm.py** - Product selection algorithm
**Purpose:** Greedy selection algorithm with graph-based penalty propagation.

**Key Functions:**
- `generate(antal, G, priorityList)` - Selects N products for vending machine

**Algorithm:**
1. Sort products by priority (sales-based)
2. Pick highest priority product
3. Penalize similar products (neighbors) proportional to edge weight
4. Repeat until N products selected

**Usage:**
```python
from src.core import setup_graph, create_priority_list_from_sales, generate

G = setup_graph()
priorities = create_priority_list_from_sales(G)
selected = generate(antal=20, G=G, priorityList=priorities)
```

---

### 📁 **data_loaders.py** - File I/O operations
**Purpose:** Loading products, sales, subcategories, and co-purchase data from files.

**Key Functions:**
- `get_project_root()` - Returns path to project root
- `load_product_data()` - Loads products.json
- `load_subcategories()` - Loads Subcategories.xlsx → EAN mapping
- `load_sales_data(sales_file)` - Loads sales parquet file
- `load_copurchase_relations()` - Loads co-purchase relations from product_relations.json
- `read_in_products_information(G)` - Populates graph with product nodes

**Example:**
```python
from src.core.data_loaders import load_copurchase_relations

# Load co-purchase data
relations = load_copurchase_relations()
# Returns: {'EAN': {'related_products': [{'product': 'EAN2', 'co_purchase_count': 145}]}}
```

---

### 🔤 **parsers.py** - Text parsing utilities
**Purpose:** Parsing and normalizing ingredient strings, EANs, product names.

**Key Functions:**
- `parse_ingredients(ing_str)` - Parses complex ingredient strings with quantities
- `normalize_ean(ean)` - Normalizes EAN to 14-digit string with leading zeros
- `extract_product_name(product_dict)` - Extracts best available product name

**Example:**
```python
from src.core.parsers import parse_ingredients

# Parse ingredient string
ing_str = "Water (95%), Sugar (4%), Lemon juice (1%)"
ingredients = parse_ingredients(ing_str)
# Result: [("Water", 95.0), ("Sugar", 4.0), ("Lemon juice", 1.0)]
```

---

### ⚖️ **edge_weights.py** - Similarity calculations
**Purpose:** Computing weights for edges between products.

**Key Functions:**
- `calculate_ingredient_similarity(ing1, ing2)` - Advanced Jaccard similarity with amount matching
- `calculate_tag_similarity(tags1, tags2)` - Tag overlap count
- `calculate_copurchase_weight(ean1, ean2, relations, normalize)` - Co-purchase similarity from transaction data
- `fill_in_sales_information(G, min_weight_threshold, copurchase_relations)` - Adds weighted edges to graph

**Similarity Components:**
1. **Ingredient Similarity** - Jaccard index + shared count + amount matching
2. **Tag Similarity** - Simple overlap count
3. **Co-purchase Similarity** - Transaction-based (log-scaled to prevent dominance)

**Example:**
```python
from src.core import load_copurchase_relations, calculate_copurchase_weight

relations = load_copurchase_relations()
weight = calculate_copurchase_weight('EAN1', 'EAN2', relations, normalize=True)
print(f"Co-purchase weight: {weight:.2f}")
```

---

### 🔗 **connections.py** - Graph connection functions
**Purpose:** Creating edges between products based on various relationships.

**Key Functions:**
- `add_subcategory_connections(G, edge_weight=0.5)` - Connects products in same subcategory
- `add_ingredient_connections(G, min_weight=8.0)` - Connects highly similar products

---

### 📦 **models.py** - Data models
**Purpose:** Core data structures used throughout the project.

**Key Classes:**
- `Weight` - Stores ingredient_match, user_match, tag_match and computes total score
- `IndexedPriorityList` - Priority queue with dynamic penalty propagation
- `UserGroupWeight` - Co-purchase pattern weights
- `product_node` - Product node representation (if used)

---

### 🎨 **subcategory_colors.py** - Color mapping
**Purpose:** Consistent color assignment for subcategories in visualizations.

**Key Functions:**
- `get_subcategory_color(subcategory)` - Gets color for a subcategory
- `create_subcategory_colormap(G)` - Creates color mapping for all subcategories in graph

---

## Import Structure

The `__init__.py` exports the most commonly used functions:

```python
from src.core import (
    # Main entry points
    setup_graph,
    create_priority_list_from_sales,
    generate,
    
    # Data models
    Weight,
    IndexedPriorityList,
    
    # Visualization
    get_subcategory_color,
    create_subcategory_colormap,
    
    # Data loading
    load_product_data,
    load_subcategories,
    load_sales_data,
)
```

## Dependency Graph

```
graph_setup.py (orchestration)
    ├── data_loaders.py (I/O)
    │   └── parsers.py (text utilities)
    ├── edge_weights.py (similarity)
    │   └── models.py (data structures)
    └── connections.py (graph edges)
        └── edge_weights.py

selection_algorithm.py
    └── models.py
```

## Design Principles

1. **Single Responsibility** - Each module has one clear purpose
2. **Clear Naming** - File names indicate what code lives where
3. **Explicit Dependencies** - Import hierarchy is straightforward
4. **Testability** - Isolated modules are easier to unit test
5. **Maintainability** - Changes are localized to specific areas

## Migration from Old main.py

The old `main.py` (619 lines) has been split as follows:

| Old Location | New Module | Lines |
|-------------|------------|-------|
| Ingredient parsing logic | `parsers.py` | 155 |
| File I/O operations | `data_loaders.py` | 128 |
| Weight calculations | `edge_weights.py` | 150 |
| Graph connections | `connections.py` | 130 |
| Selection algorithm | `selection_algorithm.py` | 95 |
| High-level setup | `graph_setup.py` | 160 |
| **Total** | **6 modules** | **818** |

Note: The total is larger due to added documentation, type hints, and clearer structure.


## Backward Compatibility

All imports from `src.core` continue to work:
```python
# Still works!
from src.core import setup_graph, generate, create_priority_list_from_sales
```

The old `main.py` has been backed up to `main.py.backup` for reference.
