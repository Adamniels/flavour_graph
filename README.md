# Flavour Graph

Ett produktgraf-system för att representera, analysera och visualisera relationer mellan produkter.

## 📖 Vad är Flavour Graph?

Flavour Graph är ett verktyg som:

1. **Skapar en graf** av produkter där noder är produkter och kanter representerar likheter
2. **Beräknar relationer** baserat på:
   - 🧪 **Ingredienser** - Produkter med liknande innehåll kopplas samman
   - 🛒 **Köpmönster** - Produkter som köps tillsammans får starkare kopplingar
   - 🏷️ **Kategorier** - Produkter i samma kategori kopplas
3. **Visualiserar** relationerna på olika sätt:
   - Interaktiva HTML-grafer som du kan zooma och utforska
   - 2D/3D embeddings för att se produktkluster
   - Statiska grafer för rapporter
4. **Hittar liknande produkter** med hjälp av Node2Vec machine learning
5. **Väljer produkter smart** för t.ex. varuautomater baserat på mångfald och popularitet

### Användningsområden

- 🏪 **Varuautomater** - Välj produktsortiment som maximerar mångfald och försäljning
- � **Produktrekommendationer** - "Kunder som köpte X köpte även Y"
- 📊 **Marknadsanalys** - Förstå produktrelationer och kluster
- 🎨 **Kategorihantering** - Visualisera och organisera produktsortiment
- 🤖 **Machine Learning** - Träna modeller på produktdata och relationer

---

## 📁 Projektstruktur

```
flavour_graph/
├── src/                        # Källkod
│   ├── core/                   # Kärnfunktionalitet (graf, modeller, algoritmer)
│   ├── interactive/            # HTML-visualiseringar
│   ├── embeddings/             # Node2Vec embeddings & similarity
│   └── visualization/          # Matplotlib visualiseringar
│
├── scripts/                    # Utility scripts
├── data/                       # Data-filer (produkter, försäljning, relationer)
├── output/                     # Genererade filer (HTML, bilder, visualiseringar)
│
├── run_interactive.py          # → Generera interaktiv HTML
├── run_embeddings.py           # → Hitta liknande produkter
├── run_visualization.py        # → Rita grafen med matplotlib
└── requirements.txt            # Python-beroenden
```

För mer detaljerad information om strukturen, se **[STRUCTURE.md](STRUCTURE.md)**.

---

## 🚀 Installation & Setup

### 1. Klona eller ladda ner projektet
```bash
git clone https://github.com/Adamniels/flavour_graph.git
cd flavour_graph
```

### 2. Skapa virtuell miljö (rekommenderas)
```bash
# På macOS/Linux:
python3 -m venv venv
source venv/bin/activate

# På Windows:
python -m venv venv
venv\Scripts\activate
```

### 3. Installera dependencies
```bash
pip install -r requirements.txt
```

**Beroenden som installeras:**
- `networkx` - Grafoperationer och algoritmer
- `matplotlib` - Statiska visualiseringar
- `node2vec` - Graf embeddings
- `gensim` - Word2Vec för embeddings
- `scikit-learn` - Dimensionalitetsreduktion (t-SNE)
- `pandas` - Datahantering
- `pyarrow` - Parquet-filer
- `plotly` - Interaktiva 3D-visualiseringar
- `openpyxl` - Excel-filer

---

## ⚡ Snabbstart

Om du bara vill komma igång snabbt:

```bash
# 1. Installera dependencies
pip install -r requirements.txt

# 2. Generera interaktiv HTML-visualisering
python run_interactive.py

# 3. Öppna filen som skapades
open output/interactive/interactive_selection.html

# 4. Utforska liknande produkter
python run_embeddings.py --product-name "Coca Cola"
```

**Det är allt!** Programmet använder färdiga datafiler i `data/` mappen.

## 💻 Användning - Huvudkommandon

### 1. Interaktiv HTML-visualisering 🌐
**Vad den gör:** Skapar en interaktiv webbsida där du kan utforska produktgrafen, zooma, panorera och söka efter produkter.

```bash
python run_interactive.py
```

**Output:** `output/interactive/interactive_selection.html`

**Hur man använder:**
1. Kör kommandot ovan
2. Öppna filen `output/interactive/interactive_selection.html` i din webbläsare
3. **Interaktioner:**
   - **Zooma:** Använd mushjulet eller trackpad
   - **Panorera:** Dra med musen
   - **Sök:** Använd sökfältet för att hitta produkter
   - **Info:** Klicka på noder för att se produktinformation

**Användningsområden:**
- ✅ Utforska hela produktgrafen visuellt
- ✅ Se vilka produkter som är relaterade till varandra
- ✅ Förstå produktkluster och kategorier
- ✅ Identifiera starka vs svaga kopplingar

---

### 2. Hitta Liknande Produkter 🔍
**Vad den gör:** Använder Node2Vec för att hitta produkter som är likande baserat på grafstrukturen, ingredienser och köpmönster.

```bash
# Sök efter liknande produkter
python run_embeddings.py --product-name "Coca Cola"
python run_embeddings.py --product-id "07310350118342"

# Visa alla tillgängliga produkter
python run_embeddings.py

# Träna om modellen (om du ändrat data)
python run_embeddings.py --retrain

# Skapa visualiseringar av embeddings
python run_embeddings.py --visualize              # 2D t-SNE plot
python run_embeddings.py --visualize-3d           # 3D interaktiv
python run_embeddings.py --visualize-weights      # Viktbaserad 3D

# Kombinera flera alternativ
python run_embeddings.py --product-name "Fanta" --visualize --visualize-3d
```

**Output:**
- **Terminal:** Lista med de 10 mest liknande produkterna med similarity scores
- **Filer (vid --visualize):**
  - `output/embeddings/embeddings_visualization_2d.png` - 2D t-SNE plot
  - `output/embeddings/embeddings_visualization_3d.html` - Interaktiv 3D plot
  - `output/embeddings/embeddings_visualization_weights.html` - Viktbaserad 3D

**Hur similarity fungerar:**
1. Node2Vec skapar 64-dimensionella vektorer för varje produkt
2. Vektorer baseras på grafstruktur (vilka produkter är kopplade)
3. Cosine similarity används för att hitta närliggande vektorer
4. Produkter med liknande grannar får liknande vektorer

**Användningsområden:**
- ✅ Hitta alternativ till en produkt
- ✅ Rekommendera liknande produkter
- ✅ Förstå produktrelationer på djupare nivå
- ✅ Analysera produktkluster

---

### 3. Statisk Graf-visualisering 📊
**Vad den gör:** Skapar en statisk Matplotlib-visualisering av grafen med markerade produkter.

```bash
python run_visualization.py
```

**Output:** Ett Matplotlib-fönster visas med grafen

**Vad den visar:**
- Hela produktgrafen
- 40 utvalda produkter (markerade i annat färg)
- Produktnamn och statistik i terminalen
- Grafegenskaper (antal noder, kanter, etc.)

**Användningsområden:**
- ✅ Snabb översikt av grafstrukturen
- ✅ Spara bilder för rapporter/presentationer
- ✅ Analysera produktval-algoritmen
- ✅ Se grafstatistik

---

### 4. Utility Scripts 🛠️

#### Analysera Försäljningsdata
Analyserar kundköpsmönster från försäljningsdata och skapar produktrelationer.

```bash
python scripts/convert_sales_to_user_pattern.py
```

**Vad den gör:**
- Läser försäljningsdata från `data/Sales_2025.parquet`
- Identifierar produkter som köps tillsammans
- Skapar co-purchase relationer
- Sparar resultat till `data/product_relations.json`

**Användningsområden:**
- ✅ Uppdatera produktrelationer när du har ny försäljningsdata
- ✅ Analysera köpbeteenden

---

#### Testa Produktkopplingar
Kontrollerar kopplingar mellan specifika produkter i grafen.

```bash
python scripts/test_connections.py
```

**Vad den gör:**
- Laddar grafen
- Testar kopplingar mellan utvalda produkter
- Visar vikter och relationstyper

**Användningsområden:**
- ✅ Debugga grafkopplingar
- ✅ Verifiera att produkter är korrekt kopplade
- ✅ Förstå hur viktberäkningen fungerar

---

## 🔧 Använd som Python Module

Du kan också använda projektet som ett Python-bibliotek i dina egna script:

### Grundläggande Exempel

#### 1. Skapa och analysera graf
```python
from src.core import setup_graph, create_priority_list_from_sales

# Skapa produktgraf med minsta edge-vikt 5.0
G = setup_graph(min_edge_weight=5.0)

print(f"Graf: {G.number_of_nodes()} produkter, {G.number_of_edges()} kopplingar")

# Lista några produkter
for node_id, data in list(G.nodes(data=True))[:5]:
    print(f"- {data.get('name', node_id)}")
    print(f"  Underkategori: {data.get('subcategory', 'Unknown')}")
    print(f"  Ingredienser: {len(data.get('ingredients', []))}")
```

#### 2. Välj produkter för varuautomat
```python
from src.core import setup_graph, create_priority_list_from_sales, generate

# Skapa graf och prioritetslista
G = setup_graph()
priority_list = create_priority_list_from_sales(G)

# Välj 20 produkter med algoritmen
# (algoritmen använder graph-baserad penalty propagation för mångfald)
selected_products = generate(antal=20, G=G, priorityList=priority_list)

print(f"\nValda {len(selected_products)} produkter för varumaten:")
for i, product_id in enumerate(selected_products, 1):
    name = G.nodes[product_id].get('name', product_id)
    subcat = G.nodes[product_id].get('subcategory', 'Unknown')
    print(f"{i:2d}. {name} ({subcat})")
```

#### 3. Hitta liknande produkter med embeddings
```python
from src.core import setup_graph
from src.embeddings.embeddings import ProductEmbeddings

# Skapa graf
G = setup_graph()

# Skapa och träna embeddings
embeddings = ProductEmbeddings(G, dimensions=64)

# Ladda befintlig modell (eller träna om med embeddings.train())
embeddings.load()

# Hitta liknande produkter
product_id = "07310350118342"  # Coca Cola
similar = embeddings.find_similar(product_id, topn=10)

print(f"\nProdukter liknande {G.nodes[product_id].get('name')}:")
for sim_id, score in similar:
    name = G.nodes[sim_id].get('name', sim_id)
    print(f"- {name}: {score:.3f}")
```

#### 4. Generera interaktiv HTML
```python
from src.core import setup_graph, create_priority_list_from_sales
from src.interactive.generate_html import generate_html_visualization

# Skapa graf och prioritetslista
G = setup_graph()
priority_list = create_priority_list_from_sales(G)

# Generera HTML-fil
output_file = generate_html_visualization(
    G, 
    priority_list, 
    num_products=15,
    output_file='output/interactive/my_custom_graph.html'
)

print(f"HTML sparad till: {output_file}")
```

#### 5. Skapa Matplotlib-visualiseringar
```python
from src.core import setup_graph
from src.visualization.visualize import draw_graph, print_graph_stats

G = setup_graph()

# Skriv ut grafstatistik
print_graph_stats(G)

# Rita grafen
draw_graph(
    G, 
    layout='spring',      # spring, circular, kamada_kawai
    figsize=(16, 12),
    show=True,            # Visa direkt
    save_path=None        # eller ange sökväg för att spara
)
```

### Avancerade Exempel

#### Anpassad viktberäkning
```python
from src.core import (
    setup_graph,
    calculate_ingredient_similarity,
    calculate_tag_similarity,
    calculate_copurchase_weight,
    load_copurchase_relations
)

G = setup_graph()

# Beräkna likhet mellan två produkter
product1 = list(G.nodes())[0]
product2 = list(G.nodes())[1]

# Hämta produktdata
data1 = G.nodes[product1]
data2 = G.nodes[product2]

# Beräkna olika typer av likhet
ing_sim = calculate_ingredient_similarity(
    data1.get('ingredients', []), 
    data2.get('ingredients', [])
)
tag_sim = calculate_tag_similarity(
    data1.get('tags', []), 
    data2.get('tags', [])
)

relations = load_copurchase_relations()
copurchase_sim = calculate_copurchase_weight(
    product1.split('-')[0],  # EAN
    product2.split('-')[0],  # EAN
    relations,
    normalize=True
)

print(f"Ingredienslikhet: {ing_sim:.2f}")
print(f"Tagglikhet: {tag_sim:.2f}")
print(f"Co-purchase: {copurchase_sim:.2f}")
```

#### Anpassa färger för kategorier
```python
from src.core import setup_graph, get_subcategory_color, create_subcategory_colormap

G = setup_graph()

# Skapa färgmapping för alla underkategorier
colormap = create_subcategory_colormap(G)

# Hämta färg för specifik kategori
color = get_subcategory_color("Läsk")
print(f"Färg för Läsk: {color}")

# Visa alla kategorier och deras färger
for subcat, color in colormap.items():
    print(f"{subcat}: {color}")
```

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
- **[src/embeddings/EMBEDDINGS_EXPLAINED.md](src/embeddings/EMBEDDINGS_EXPLAINED.md)** - Djupdykning i Node2Vec och embeddings

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
