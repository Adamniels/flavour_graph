# Embeddings Module - Graph Embeddings & Similarity Search

## Översikt

Denna modul använder **Node2Vec** för att skapa vektorrepresentationer av produkter baserat på grafstrukturen. Detta möjliggör semantisk sökning och similarity search mellan produkter.

## Vad gör denna modul?

1. **Tränar embeddings** - Skapar X-dimensionella vektorer för varje produkt
2. **Similarity search** - Hittar liknande produkter baserat på vektoravstånd
3. **Visualiseringar** - Visar produkter i 2D/3D för att förstå relationer

## Algoritmer & Tekniker

### Node2Vec

**Node2Vec** är en graph embedding-teknik som kombinerar:

#### 1. Random Walks (Slumpmässiga Vandringar)
- Börjar vid en nod och går slumpmässigt till grannar
- Utforskar både **bredd** (lokala grannar) och **djup** (avlägsna noder)
- Skapar "meningar" av nod-sekvenser

**Parametrar:**
- `walk_length=30` - Längd på varje vandring
- `num_walks=200` - Antal vandringar per nod
- `p=1.0` - Return parameter (sannolikhet att återvända)
- `q=1.0` - In-out parameter (utforska vs exploatera)

**Exempel:**
```
Product A → Product B → Product C → Product D → ...
```

#### 2. Word2Vec (Skip-gram)
Efter att random walks är skapade, behandlas de som "meningar":
- Varje produkt = ett "ord"
- Varje walk = en "mening"

**Skip-gram** lär modellen att förutsäga:
- Vilka produkter förekommer nära varandra i walks
- Detta fångar **context** - produkter med liknande grannar får liknande vektorer

**Parametrar:**
- `dimensions=64` - Vektorstorlek (hur många dimensioner)
- `window=10` - Context window (hur många ord åt varje håll)
- `epochs=10` - Antal träningsiterationer

### Resultat

**Vad fångar embeddingsen?**
- ✅ **Direkta kopplingar** - Produkter som är länkade i grafen
- ✅ **Grafstruktur** - Kluster och communities
- ✅ **Edge weights** - Starkare kopplingar = närmare vektorer
- ✅ **Transitiva relationer** - A→B och B→C innebär A≈C

### Similarity Search

**Cosine Similarity** används för att hitta liknande produkter:

```
similarity = (vector_A · vector_B) / (||vector_A|| × ||vector_B||)
```

- Värde mellan -1 och 1
- Närmare 1 = mer lika
- Tar inte hänsyn till magnitude, bara riktning

## Filer

### `embeddings.py`
**Huvud-implementering av ProductEmbeddings-klassen**

**Klasser:**
- `ProductEmbeddings` - Hanterar träning, spara/ladda, similarity search

**Metoder:**
```python
# Träna embeddings
embeddings.train(walk_length=30, num_walks=200, p=1.0, q=1.0)

# Hitta liknande produkter
similar = embeddings.find_similar(product_id, topn=10)

# Spara/ladda modell
embeddings.save("model.pkl")
embeddings.load("model.pkl")

# Visualiseringar
embeddings.visualize_embeddings_2d()  # t-SNE 2D
embeddings.visualize_embeddings_3d()  # Plotly 3D
embeddings.visualize_by_weights()     # Baserat på grafvikter
```

### `find_similar.py`
**CLI-verktyg för att hitta liknande produkter**

**Användning:**
```bash
# Hitta liknande produkter
python run_embeddings.py --product-name "Coca Cola"
python run_embeddings.py --product-id "07310350118342" --topn 5

# Träna om modellen
python run_embeddings.py --retrain

# Visualiseringar
python run_embeddings.py --visualize --visualize-3d --visualize-weights
```

## Visualiseringar

### 1. 2D t-SNE (PNG)
**Vad:** Reducerar 64D-vektorer till 2D för visualisering

**Algoritm:** t-SNE (t-Distributed Stochastic Neighbor Embedding)
- Bevarar lokala strukturer
- Produkter nära i 64D blir nära i 2D
- Färgade efter kategori

**Output:** `output/embeddings/embeddings_visualization_2d.png`

### 2. 3D t-SNE (Interaktiv HTML)
**Vad:** Samma som 2D men i 3D med interaktiv plotly

**Fördelar:**
- Mer information bevaras (3D vs 2D)
- Kan rotera och zooma
- Hover för produktinfo

**Output:** `output/embeddings/embeddings_visualization_3d.html`

### 3. Weight-based 3D (Interaktiv HTML)
**Vad:** Visar produkter baserat på faktiska grafvikter (inte t-SNE)

**Axlar:**
- X: Genomsnittlig `ingredient_match`
- Y: Genomsnittlig `user_match` (co-purchase)
- Z: Genomsnittlig `tag_match`

**Fördelar:**
- Mer tolkningsbar än t-SNE
- Visar faktiska relationstyper
- Direkt koppling till grafen

**Output:** `output/embeddings/embeddings_visualization_weights.html`

## Dimensionality Reduction

### t-SNE vs PCA

**t-SNE (t-Distributed Stochastic Neighbor Embedding):**
- ✅ Bevarar lokala strukturer bättre
- ✅ Avslöjar kluster och patterns
- ❌ Långsammare
- ❌ Icke-linjär (svårare att tolka)
- **Används:** För visualiseringar

**PCA (Principal Component Analysis):**
- ✅ Mycket snabbare
- ✅ Linjär (lättare att tolka)
- ❌ Bevarar globala strukturer (inte lokala)
- **Används:** För snabba översikter

## Datakällor

**Input:**
- NetworkX-graf från `src.core` (graph_setup)
- Produktrelationer från `data/product_relations.json`

**Output - Tränade modeller:**
- `data/embeddings_model.pkl` - Metadata och mappningar
- `data/embeddings_model_word2vec.model` - Word2Vec modell

**Output - Visualiseringar:**
- `output/embeddings/embeddings_visualization_2d.png`
- `output/embeddings/embeddings_visualization_3d.html`
- `output/embeddings/embeddings_visualization_weights.html`

## Prestanda

**Träningstid:**
- ~40 sekunder för 1000 noder
- Beror på: antal noder, num_walks, walk_length

**Memory:**
- ~100 MB för tränad modell (1000 noder, 64 dim)

**Similarity search:**
- Mycket snabb (<1ms per query)
- Använder numpy vectorization

## Exempel: Hitta Liknande Produkter

```python
from src.core import setup_graph
from src.embeddings.embeddings import ProductEmbeddings

# Skapa graf
G = setup_graph(min_edge_weight=5.0)

# Träna embeddings
embeddings = ProductEmbeddings(G, dimensions=64)
embeddings.train(walk_length=30, num_walks=200)

# Hitta liknande
similar = embeddings.find_similar("07310350118342", topn=10)

for product_id, similarity_score in similar:
    name = G.nodes[product_id]['name']
    print(f"{name}: {similarity_score:.3f}")
```

## Parameterjustering

### För bättre lokala strukturer (BFS-liknande):
```python
embeddings.train(p=1.0, q=2.0)  # q > 1 håller nära startnod
```

### För att utforska långt (DFS-liknande):
```python
embeddings.train(p=1.0, q=0.5)  # q < 1 rör sig utåt
```

### För balanserad exploration:
```python
embeddings.train(p=1.0, q=1.0)  # Standardvärden
```

## Läs mer

För djupare förklaring av algoritmer och koncept, se:
- **[EMBEDDINGS_EXPLAINED.md](EMBEDDINGS_EXPLAINED.md)** - Detaljerad förklaring av Node2Vec (i samma mapp)
- **[Original Node2Vec Paper](https://arxiv.org/abs/1607.00653)** - Akademisk referens

## Användningsfall

1. **Produktrekommendationer** - "Kunder som köpte X köpte också..."
2. **Inventory management** - Gruppera liknande produkter
3. **Kategori-analys** - Upptäck naturliga produktgrupper
4. **Anomaly detection** - Hitta produkter som inte passar in
5. **A/B testing** - Jämför produktgrupper

## Framtida Förbättringar

- [ ] Ensemble methods (kombinera flera embeddings)
- [ ] Deep Learning embeddings (GraphSAGE, GAT)
- [ ] Temporal embeddings (fånga tidsaspekter)
- [ ] Multi-modal embeddings (text + graf)
