# Projektstruktur - Flavour Graph

## Översikt

Projektet är organiserat i logiska moduler för bättre underhåll och skalbarhet.

## Mappstruktur

```
flavour_graph/
├── src/                           # Källkod (organiserad i moduler)
│   ├── core/                      # Kärnfunktionalitet
│   ├── interactive/               # Interaktiv visualisering
│   ├── embeddings/                # Graph embeddings
│   └── visualization/             # Graf-visualiseringar
│
├── scripts/                       # Utility scripts
├── output/                        # Genererade filer (tre kategorier)
├── data/                          # Indata och tränade modeller
└── run_*.py                       # Enkla entry points för huvudfunktionerna
```

## Detaljerad Struktur

### `src/core/` - Kärnfunktionalitet
Innehåller grundläggande funktionalitet som används av alla andra moduler.

**Filer:**
- `main.py` - Graf-setup, edge creation, priority lists
- `models.py` - Datamodeller (Weight, product_node, IndexedPriorityList)
- `subcategory_colors.py` - Färgmappning för produktkategorier

**Ansvar:**
- Läsa och processa produktdata
- Skapa NetworkX-graf med edges baserat på relationer
- Hantera prioritetslistor från försäljningsdata
- Generera produkturval baserat på prioriteter

---

### `src/interactive/` - Interaktiv HTML-visualisering
Modern, snabb canvas-baserad visualisering för webbläsare.

**Filer:**
- `generate_html.py` - Genererar interaktiv HTML-fil

**Funktionalitet:**
- Canvas-baserad rendering (mycket snabbare än matplotlib)
- Interaktiv steg-för-steg produktval
- Zoom och panorering
- Visar grafkopplingar med vikter
- Real-time uppdatering av prioriteter

**Output:**
- `output/interactive/interactive_selection.html`

**Kör med:**
```bash
python run_interactive.py
```

---

### `src/embeddings/` - Graph Embeddings och Similarity Search
Node2Vec implementering för att hitta liknande produkter.

**Filer:**
- `embeddings.py` - ProductEmbeddings klass, träning och sökning
- `find_similar.py` - CLI för similarity search och visualiseringar

**Funktionalitet:**
- Node2Vec träning (random walks + Word2Vec)
- Similarity search mellan produkter
- 2D/3D visualiseringar av embeddings
- Weight-baserade visualiseringar

**Output:**
- `output/embeddings/embeddings_visualization_2d.png`
- `output/embeddings/embeddings_visualization_3d.html`
- `output/embeddings/embeddings_visualization_weights.html`
- `data/embeddings_model.pkl` (tränad modell)
- `data/embeddings_model_word2vec.model` (Word2Vec modell)

**Kör med:**
```bash
# Hitta liknande produkter
python run_embeddings.py --product-name "Coca Cola"

# Med visualiseringar
python run_embeddings.py --visualize --visualize-3d --visualize-weights

# Träna om modellen
python run_embeddings.py --retrain
```

---

### `src/visualization/` - Graf-visualiseringar
Matplotlib-baserade statiska och interaktiva visualiseringar.

**Filer:**
- `visualize.py` - draw_graph, draw_subgraph, print_graph_stats

**Funktionalitet:**
- Rita hela grafen med NetworkX layouts
- Visa subgrafer av valda produkter
- Weight-baserad färgning av edges
- Produktstatistik

**Output:**
- Matplotlib-fönster (visas direkt)
- Kan spara till `output/visualizations/` om save_path anges

**Kör med:**
```bash
python run_visualization.py
```

---

### `scripts/` - Utility Scripts
Hjälpscript för data-processing och testing.

**Filer:**
- `convert_sales_to_user_pattern.py` - Konvertera försäljningsdata till co-occurrence
- `test_connections.py` - Testa produktkopplingar

**Användning:**
```bash
python scripts/convert_sales_to_user_pattern.py
python scripts/test_connections.py
```

---

### `output/` - Genererade Filer
Separata mappar för olika typer av output.

**Struktur:**
```
output/
├── interactive/        # HTML-visualiseringar
├── embeddings/        # Embeddings-visualiseringar
└── visualizations/    # Graf-visualiseringar
```

**Varför separata mappar?**
- Tydlig separation av concerns
- Lätt att hitta specifik typ av output
- Enklare att rensa (t.ex. bara embeddings-viz)
- Matchar källkods-strukturen

---

### `run_*.py` - Entry Points
Enkla scripts i root för att köra huvudfunktionerna.

**Filer:**
- `run_interactive.py` - Generera interaktiv HTML
- `run_embeddings.py` - Kör embeddings search och visualiseringar
- `run_visualization.py` - Rita grafen med matplotlib

**Varför i root?**
- Enkelt att hitta och köra
- Tydliga entry points för användare
- Ingen förvirring om var man ska starta

---

## Import-struktur

Alla imports använder nu absoluta paths från `src`:

```python
# I run_interactive.py
from src.interactive.generate_html import generate_html_visualization
from src.core.main import setup_graph, create_priority_list_from_sales

# I src/embeddings/find_similar.py
from src.core.main import setup_graph
from src.embeddings.embeddings import ProductEmbeddings

# I src/visualization/visualize.py
from src.core.subcategory_colors import get_subcategory_color
```

Detta ger:
- ✅ Tydlig modul-hierarki
- ✅ Ingen förvirring om relativa paths
- ✅ Enkelt att refaktorera
- ✅ IDE auto-complete fungerar bättre

---

## Path-hantering

Alla data-paths är nu relativa till project root, inte script directory.

**Exempel från `src/core/main.py`:**
```python
# Get project root (two levels up from this file)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
products_file = os.path.join(project_root, "data", "products.json")
```

Detta säkerställer att paths fungerar oavsett var scriptet körs ifrån.

---

## Fördelar med ny struktur

### 🎯 Separation of Concerns
Varje modul har ett tydligt ansvar:
- Core: Graf och data
- Interactive: HTML-visualisering
- Embeddings: Similarity search
- Visualization: Matplotlib-grafer

### 📦 Modulär Design
Enkelt att:
- Lägga till ny funktionalitet
- Testa individuella moduler
- Återanvända kod

### 🔧 Bättre Underhåll
- Lätt att hitta kod
- Tydlig fil-organisation
- Mindre risk för naming conflicts

### 🚀 Skalbarhet
- Kan enkelt lägga till fler moduler
- Output-strukturen skalas naturligt
- Entry points är enkla att utöka

---

## Migration från Gammal Struktur

**Tidigare:** Alla filer i root
```
main.py
models.py
embeddings.py
visualize.py
generate_interactive_html_fast.py
find_similar_products.py
...
```

**Nu:** Organiserat i moduler
```
src/
  core/main.py
  core/models.py
  embeddings/embeddings.py
  visualization/visualize.py
  interactive/generate_html.py
  embeddings/find_similar.py
run_interactive.py
run_embeddings.py
run_visualization.py
```

**Ändrade imports:**
- `from main import` → `from src.core.main import`
- `from embeddings import` → `from src.embeddings.embeddings import`
- etc.

**Nya output-paths:**
- `output/html/` → `output/interactive/`
- `output/visualizations/` → `output/embeddings/` (för embeddings)
- `output/visualizations/` → `output/visualizations/` (för grafer)

---

## Sammanfattning

Den nya strukturen ger ett **professionellt, skalbart och underhållbart** projekt med:
- ✅ Tydlig modul-organisation
- ✅ Separerade output-kategorier
- ✅ Enkla entry points
- ✅ Bättre path-hantering
- ✅ Redo för framtida expansion

**Tre huvudfunktioner, tre kommandon:**
1. `python run_interactive.py` - Interaktiv HTML
2. `python run_embeddings.py` - Embeddings & similarity
3. `python run_visualization.py` - Graf-visualisering
