# Flavour Graph

Ett produktgraf-system för att representera och analysera relationer mellan produkter (t.ex. för vending machines).

## Struktur

- `models.py` - Datamodeller (Weight, product_node)
- `main.py` - Huvudlogik med NetworkX-graf
- `visualize.py` - Visualiseringsfunktioner
- `requirements.txt` - Python-beroenden

## Installation

```bash
pip install -r requirements.txt
```

## Användning

### Grundläggande exempel

```python
from main import setup_graph, generate

# Skapa grafen
G = setup_graph()

# Generera urval av produkter
selected = generate(4, G)
print(f"Valda produkter: {selected}")
```

### Visualisering

```python
from main import setup_graph, generate
from visualize import draw_graph, print_graph_stats

# Skapa och visa grafen
G = setup_graph()
print_graph_stats(G)

# Rita grafen med markerade produkter
selected = generate(4, G)
draw_graph(G, highlight_nodes=selected, min_edge_weight=1.0)
```

### Köra direkt

```bash
# Visa produkter och relationer
python main.py

# Visa graf-statistik och visualisering
python visualize.py
```

## Grafstruktur

**Noder** (produkter) har attribut:
- `prio` - prioritet (heltal)
- `tags` - lista med taggar
- `ingredients` - lista med ingredienser

**Edges** (relationer) har vikter:
- `ingredient_match` - antal gemensamma ingredienser
- `user_match` - historisk co-purchase data (placeholder)
- `tag_match` - antal gemensamma taggar
- `weight` - kombinerad viktning

## NetworkX Fördelar

- ✅ Enkel visualisering
- ✅ Inbyggda grafalgorimer (shortest path, centrality, etc.)
- ✅ Kan exportera till olika format (GraphML, JSON, etc.)
- ✅ Stöd för både riktade och oriktade grafer
