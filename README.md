# Flavour Graph

Ett produktgraf-system för att representera och analysera relationer mellan produkter (t.ex. för vending machines).

## Projektstruktur 📁

```
flavour_graph/
├── src/                        # Källkod
│   ├── core/                   # Kärnfunktionalitet
│   │   ├── main.py            # Graf-setup och huvudlogik
│   │   ├── models.py          # Datamodeller
│   │   └── subcategory_colors.py
│   │
│   ├── interactive/            # Interaktiv HTML-visualisering
│   │   └── generate_html.py  # Canvas-baserad visualisering
│   │
│   ├── embeddings/             # Node2Vec embeddings
│   │   ├── embeddings.py      # ProductEmbeddings klass
│   │   └── find_similar.py    # Similarity search
│   │
│   └── visualization/          # Graf-visualiseringar
│       └── visualize.py       # Matplotlib visualiseringar
│
├── scripts/                    # Utility scripts
│   ├── convert_sales_to_user_pattern.py
│   └── test_connections.py
│
├── output/                     # Genererade filer
│   ├── interactive/           # HTML visualiseringar
│   ├── embeddings/            # Embeddings visualiseringar
│   └── visualizations/        # Graf-visualiseringar
│
├── data/                       # Data och modeller
├── run_interactive.py          # 🚀 Kör interaktiv HTML
├── run_embeddings.py           # 🚀 Kör embeddings search
├── run_visualization.py        # 🚀 Kör graf-visualisering
├── requirements.txt
└── README.md
```

## Snabbstart 🚀

```bash
# Installera dependencies
pip install -r requirements.txt

# 1. Generera interaktiv HTML-visualisering
python run_interactive.py

# 2. Hitta liknande produkter med embeddings
python run_embeddings.py --visualize --visualize-3d --visualize-weights

# 3. Rita grafen med matplotlib
python run_visualization.py
```

## Genererade Filer 📁

Alla genererade filer sparas i separata undermappar under `output/`:

### Interaktiv HTML (`output/interactive/`)
- `interactive_selection.html` - **Interaktiv produktvalsvisualisation** 🎯
  - Genereras med: `python run_interactive.py`
  - Canvas-baserad snabb rendering
  - Klicka "Next Selection" för att välja produkter stegvis
  - Visar grafkopplingar och prioritetsändringar i realtid
  - Zoom och panorering med musen

### Embeddings (`output/embeddings/`)
- `embeddings_visualization_2d.png` - 2D-plot av produktembeddings (t-SNE/PCA)
- `embeddings_visualization_3d.html` - Interaktiv 3D plotly-visualisering
- `embeddings_visualization_weights.html` - 3D-visualisering baserad på grafvikter
  - Genereras med: `python run_embeddings.py --visualize --visualize-3d --visualize-weights`

### Graf-visualiseringar (`output/visualizations/`)
- Matplotlib-baserade grafer och visualiseringar
  - Genereras med: `python run_visualization.py`

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

# Generera interaktiv HTML-visualisering 🆕
python generate_interactive_html_fast.py

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
