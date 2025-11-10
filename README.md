# Flavour Graph

Ett produktgraf-system för att representera och analysera relationer mellan produkter.

## 📁 Projektstruktur

```
flavour_graph/
├── src/                        # Källkod
│   ├── core/                   # Kärnfunktionalitet (graf, modeller)
│   ├── interactive/            # HTML-visualiseringar
│   ├── embeddings/             # Node2Vec embeddings & similarity
│   └── visualization/          # Matplotlib visualiseringar
│
├── scripts/                    # Utility scripts
├── data/                       # Data-filer
├── output/                     # Genererade filer
│
├── run_interactive.py          # → Generera interaktiv HTML
├── run_embeddings.py           # → Hitta liknande produkter
├── run_visualization.py        # → Rita grafen
└── requirements.txt            # Dependencies
```

## 🚀 Installation & Setup

```bash
# 1. Klona repository
git clone https://github.com/Adamniels/flavour_graph.git
cd flavour_graph

# 2. Skapa virtual environment
python3 -m venv venv
source venv/bin/activate  # På macOS/Linux
# eller: venv\Scripts\activate  # På Windows

# 3. Installera dependencies
pip install -r requirements.txt
```

## 💻 Kommandon

### 1. Interaktiv HTML-visualisering
Genererar en interaktiv produktgraf i HTML med zoom/pan och sökning.

```bash
python run_interactive.py
```

**Output:** `output/interactive/interactive_selection.html`  
→ Öppna filen i din webbläsare för att utforska grafen interaktivt.

---

### 2. Embeddings & Similarity Search
Använder Node2Vec för att hitta liknande produkter baserat på grafstruktur.

```bash
# Hitta liknande produkter
python run_embeddings.py

# Med visualiseringar
python run_embeddings.py --visualize              # 2D plot
python run_embeddings.py --visualize-3d           # 3D interaktiv
python run_embeddings.py --visualize-weights      # Viktbaserad 3D

# Sök efter specifik produkt
python run_embeddings.py --product-name "Coca Cola"
python run_embeddings.py --product-id "07310350118342"

# Träna om modellen
python run_embeddings.py --retrain

# Alla visualiseringar samtidigt
python run_embeddings.py --visualize --visualize-3d --visualize-weights
```

**Output:**
- `output/embeddings/embeddings_visualization_2d.png` - 2D t-SNE plot
- `output/embeddings/embeddings_visualization_3d.html` - Interaktiv 3D
- `output/embeddings/embeddings_visualization_weights.html` - Viktbaserad 3D

---

### 3. Graf-visualisering (Matplotlib)
Skapar statiska visualiseringar av grafen.

```bash
python run_visualization.py
```

**Output:** Visar grafen i ett matplotlib-fönster

---

### 4. Utility Scripts

#### Konvertera Sales Data
Analyserar kundköpsmönster och skapar produktrelationer.

```bash
python scripts/convert_sales_to_user_pattern.py
```

#### Testa Connections
Kontrollerar kopplingar mellan valda produkter.

```bash
python scripts/test_connections.py
```

---

## 🔧 Använd som Python Module

```python
# Importera från core-modulen (refaktorerad struktur)
from src.core import (
    setup_graph,              # Skapa produktgraf
    create_priority_list_from_sales,  # Prioritetslistor från försäljning
    generate,                 # Produktvalalgoritm
    Weight,                   # Viktmodell för kanter
    IndexedPriorityList       # Prioritetskö
)

# Embeddings
from src.embeddings.embeddings import ProductEmbeddings

# HTML-visualisering
from src.interactive.generate_html import generate_html_visualization

# Matplotlib
from src.visualization.visualize import draw_graph, print_graph_stats

# === Exempel 1: Skapa och analysera graf ===
G = setup_graph(min_edge_weight=5.0)
print(f"Graf: {G.number_of_nodes()} noder, {G.number_of_edges()} kanter")

# === Exempel 2: Välj produkter för varuautomat ===
priority_list = create_priority_list_from_sales(G)
selected_products = generate(antal=20, G=G, priorityList=priority_list)
print(f"Valda {len(selected_products)} produkter")

# === Exempel 3: Hitta liknande produkter ===
embeddings = ProductEmbeddings(G, dimensions=64)
embeddings.train()
similar = embeddings.find_similar(product_id="07310350118342", topn=10)

# === Exempel 4: Generera visualiseringar ===
# Interaktiv HTML
generate_html_visualization(G, priority_list, output_file='output/interactive/my_graph.html')

# Matplotlib
draw_graph(G, layout='spring', show=True)
```

### Core Module Structure (Ny refaktorerad arkitektur)

Sedan version 2.0 är `src/core` uppdelad i fokuserade moduler:

- **`graph_setup.py`** - High-level orchestration (`setup_graph`, `create_priority_list_from_sales`)
- **`selection_algorithm.py`** - Produktvalsalgoritm (`generate`)
- **`data_loaders.py`** - Fil-I/O operationer (JSON, Parquet)
- **`parsers.py`** - Text-parsing utilities (ingredienser, EAN)
- **`edge_weights.py`** - Likhetsberäkningar för grafkanter
- **`connections.py`** - Graf-kopplingar (underkategori, ingrediens)
- **`models.py`** - Dataklasser (`Weight`, `IndexedPriorityList`, etc.)
- **`subcategory_colors.py`** - Färgmapping för visualiseringar

Se **[src/core/README.md](src/core/README.md)** för fullständig dokumentation.

---

## 📊 Dokumentation

### Modul-specifik dokumentation
Varje modul har sin egen README med detaljerad information:

- **[src/core/README.md](src/core/README.md)** - **NY!** Refaktorerad core-modul arkitektur
  - Graph setup och orchestration
  - Produktvalsalgoritm med penalty propagation
  - Data loading och parsing
  - Edge weight calculations
  - Modellklasser (Weight, IndexedPriorityList)
- **[src/embeddings/README.md](src/embeddings/README.md)** - Node2Vec algoritm och similarity search
- **[src/interactive/README.md](src/interactive/README.md)** - Canvas rendering och interaktiv visualisering
- **[src/visualization/README.md](src/visualization/README.md)** - Matplotlib graf-visualiseringar

### Övergripande dokumentation
- **[STRUCTURE.md](STRUCTURE.md)** - Detaljerad projektstruktur och arkitektur
- **[EMBEDDINGS_EXPLAINED.md](EMBEDDINGS_EXPLAINED.md)** - Djupdykning i Node2Vec och embeddings
- **[GENERATE_FILES.md](GENERATE_FILES.md)** - Guide för att generera visualiseringar

---

## 🏗️ Teknisk Stack

- **NetworkX** - Graf-operationer och layout-algoritmer
- **Node2Vec** - Graf embeddings för similarity search
- **Gensim** - Word2Vec implementation för embeddings
- **Matplotlib** - Statiska graf-visualiseringar
- **Plotly** - Interaktiva 3D visualiseringar
- **Pandas** - Data manipulation och analys
- **scikit-learn** - Machine learning utilities (t-SNE, PCA)

---

## 📝 Features

### Graf-skapande
- ✅ Importera produktdata från JSON/Parquet
- ✅ Skapar kanter baserat på:
  - Ingrediens-likhet
  - Användarmönster (co-purchase)
  - Tag-matching
- ✅ Viktade kanter för att representera relationsstyrka

### Visualiseringar
- ✅ **Interaktiv HTML** - Canvas-baserad med zoom/pan
- ✅ **Embeddings 2D/3D** - t-SNE och viktbaserade plots
- ✅ **Matplotlib grafer** - Statiska high-quality bilder

### Similarity Search
- ✅ Node2Vec embeddings
- ✅ Cosine similarity
- ✅ Hitta liknande produkter baserat på grafstruktur

### Priority System
- ✅ Skapar prioritetslistor från sales data
- ✅ Dynamic selection-algoritm

---

## 🤝 Contributing

Projektet är organiserat med tydlig separation of concerns:
- `src/core/` - Kärnlogik som används av alla andra moduler
- `src/embeddings/` - Allt relaterat till embeddings
- `src/interactive/` - HTML-generering
- `src/visualization/` - Matplotlib-visualiseringar

Alla moduler har sina egna README-filer med detaljerad dokumentation.

---

## 👤 Author

Adam Nielsen

---

**Snabbhjälp:**
```bash
python run_interactive.py                    # Interaktiv HTML
python run_embeddings.py --help              # Visa alla options
python run_visualization.py                  # Matplotlib graf
```
