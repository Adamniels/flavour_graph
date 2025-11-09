# Flavour Graph

Ett produktgraf-system för att representera och analysera relationer mellan produkter (t.ex. för vending machines).

## Struktur

- `models.py` - Datamodeller (Weight, product_node, IndexedPriorityList)
- `main.py` - Huvudlogik med NetworkX-graf
- `visualize.py` - Visualiseringsfunktioner
- `embeddings.py` - **Node2Vec graph embeddings för produktsökning** 🆕
- `find_similar_products.py` - **Hitta liknande produkter med embeddings** 🆕
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

# Hitta liknande produkter (Node2Vec embeddings) 🆕
python find_similar_products.py
python find_similar_products.py --product-name "Coca Cola"
python find_similar_products.py --product-id "07310350118342" --topn 5
```

## Graph Embeddings (Node2Vec) 🆕

Systemet använder **Node2Vec** för att skapa X-dimensionella vektorrepresentationer av produkter. Detta möjliggör:
- 🔍 Snabb sökning efter liknande produkter
- 📊 Kvantifiering av produktlikhet (cosine similarity)
- 🎯 Rekommendationer baserade på grafstruktur

**📖 [Läs detaljerad förklaring: EMBEDDINGS_EXPLAINED.md](EMBEDDINGS_EXPLAINED.md)**

Denna guide förklarar:
- Hur Node2Vec fungerar (random walks + Word2Vec)
- Vad är Component 1, 2, 3 i visualiseringar?
- Skillnad mellan t-SNE och weight-baserad visualisering
- Praktiska exempel och användningsfall

### Hur det fungerar

Node2Vec skapar embeddings genom:
1. **Random walks** på grafen (utforskar både bredd och djup)
2. **Word2Vec** (Skip-gram) för att lära embeddings från walks
3. Produkter med liknande grafpositioner → liknande vektorer

Embeddings fångar:
- Direkta kopplingar (vilka produkter är länkade)
- Grafstruktur (kluster och communities)
- Edge weights (starkare kopplingar = närmare i vektorrymd)

### Användning av embeddings

```python
from main import setup_graph
from embeddings import ProductEmbeddings

# Skapa och träna embeddings
G = setup_graph()
embeddings = ProductEmbeddings(G, dimensions=64)
embeddings.train(walk_length=30, num_walks=200)

# Hitta liknande produkter
similar = embeddings.find_similar("07310350118342", topn=10)
for product_id, similarity_score in similar:
    print(f"{product_id}: {similarity_score:.3f}")

# Spara för senare användning
embeddings.save("data/embeddings_model.pkl")
```

### Command-line verktyg

```bash
# Visa tillgängliga produkter
python find_similar_products.py

# Hitta liknande produkter med namn
python find_similar_products.py --product-name "Snickers"

# Hitta liknande produkter med ID
python find_similar_products.py --product-id "07310350118342" --topn 5

# Träna om embeddings (ta några minuter)
python find_similar_products.py --retrain

# Visualisera embeddings i 2D (t-SNE)
python find_similar_products.py --visualize
```

### Parametrar för Node2Vec

- `dimensions`: Vektorstorlek (default: 64)
- `walk_length`: Längd på random walks (default: 30)
- `num_walks`: Antal walks per nod (default: 200)
- `p`: Return parameter - styr sannolikhet att återvända till föregående nod
- `q`: In-out parameter - styr exploration vs exploitation
  - `q > 1`: håll nära startnod (BFS-liknande)
  - `q < 1`: rör utåt (DFS-liknande)

### API-funktioner

```python
# Hitta liknande produkter
embeddings.find_similar(product_id, topn=10)

# Beräkna similarity mellan två produkter
similarity = embeddings.compute_similarity(prod1, prod2)

# Hitta produkter liknande en grupp (genomsnitt av embeddings)
avg_vector = embeddings.get_average_embedding([prod1, prod2, prod3])
similar = embeddings.find_similar_by_vector(avg_vector, topn=10)

# Visualisera embeddings i 2D
embeddings.visualize_embeddings_2d(method='tsne')
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
