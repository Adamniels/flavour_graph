# Graph Embeddings Explained: Node2Vec + Visualisering

Denna guide förklarar hur vi använder **Node2Vec** för att skapa vektorrepresentationer av produkter och hur vi visualiserar dessa i 2D och 3D.

---

## 📚 Innehåll

1. [Översikt](#översikt)
2. [Steg 1: Grafen (rådata)](#steg-1-grafen-rådata)
3. [Steg 2: Node2Vec skapar embeddings](#steg-2-node2vec-skapar-embeddings)
4. [Steg 3: Visualisering med t-SNE](#steg-3-visualisering-med-t-sne)
5. [Vad är Component 1, 2, 3?](#vad-är-component-1-2-3)
6. [Alternativ: Weight-baserad visualisering](#alternativ-weight-baserad-visualisering)
7. [Användning](#användning)
8. [Fördelar och begränsningar](#fördelar-och-begränsningar)

---

## Översikt

### Problem
Vi har en graf med 1000+ produkter och 90,000+ kopplingar. Hur kan vi:
- Hitta liknande produkter snabbt?
- Visualisera produktrelationer?
- Kvantifiera produktlikhet?

### Lösning
**Node2Vec** → skapar 64-dimensionella vektorer för varje produkt
**Cosine similarity** → mäter likhet mellan produkter
**t-SNE/PCA** → reducerar till 2D/3D för visualisering

---

## Steg 1: Grafen (rådata)

Vår flavor graph innehåller:
- **1023 produkter** (noder)
- **90,104 kopplingar** (edges)

Varje koppling har en vikt baserad på:

```python
Weight = ingredient_match × 1.5 +  # Gemensamma ingredienser
         user_match × 0.6 +         # Co-purchase data
         tag_match × 1.0            # Gemensamma taggar/kategorier
```

### Exempel på graf-struktur:

```
[Coca-Cola Original] --12.5--> [Coca-Cola Zero]
[Coca-Cola Original] --11.1--> [Fanta]
[Coca-Cola Original] --8.3---> [Sprite]
[Snickers]           --9.1---> [Mars]
[Snickers]           --7.5---> [Twix]
```

Starkare kopplingar = mer liknande produkter.

---

## Steg 2: Node2Vec skapar embeddings

Node2Vec konverterar grafstrukturen till vektorer genom två steg:

### 2a. Random Walks på grafen

Node2Vec "promenerar" runt i grafen och skapar sekvenser av produkter:

```
Walk 1: Coca-Cola → Fanta → Sprite → 7UP → Pepsi
Walk 2: Coca-Cola → Sprite → Fanta → Coca-Cola Zero → Fanta
Walk 3: Snickers → Mars → Twix → Bounty → Kit Kat → Snickers
Walk 4: Vitamin Well Defence → Vitamin Well Awake → Vitamin Well Reload
...
```

**Parametrar:**
- `num_walks = 200` → 200 walks per produkt
- `walk_length = 30` → varje walk är 30 steg lång
- `p = 1.0` (return parameter) → styr sannolikhet att återvända till föregående nod
- `q = 1.0` (in-out parameter) → styr exploration vs exploitation
  - `q > 1`: håll nära startnod (BFS-liknande, lokal struktur)
  - `q < 1`: utforska långt (DFS-liknande, global struktur)

**Edge weights påverkar walks:**
- Kopplingar med högre weight → högre sannolikhet att väljas
- Detta betyder att produkter med starka relationer oftare "ses tillsammans"

### 2b. Word2Vec lär embeddings

Node2Vec behandar walks som "meningar" och produkter som "ord":

```python
# Walks blir "meningar":
sentences = [
    ["Coca-Cola", "Fanta", "Sprite", "7UP", "Pepsi"],
    ["Snickers", "Mars", "Twix", "Bounty", "Kit Kat"],
    ...
]

# Word2Vec (Skip-gram) lär:
# "Om Coca-Cola ofta förekommer nära Fanta i walks,
#  ska deras vektorer vara liknande"
```

**Word2Vec objective:**
Maximera sannolikheten att förutsäga kontext (grannar) från målprodukt:

```
maximize Σ log P(neighbor | product)
```

**Resultat:** Varje produkt får en **64-dimensionell vektor**:

```python
embeddings = {
    "Coca-Cola":    [0.23, -0.45, 0.12, ..., 0.67],  # 64 värden
    "Fanta":        [0.19, -0.42, 0.15, ..., 0.71],  # 64 värden
    "Snickers":     [-0.82, 0.31, -0.19, ..., 0.02], # 64 värden
    "Vitamin Well": [0.54, 0.22, -0.31, ..., 0.19],  # 64 värden
}
```

**Vad fångar embeddings?**
- Produkter som ofta "ses tillsammans" i walks → liknande vektorer
- Produkter i samma grannskap → liknande vektorer
- Grafstruktur och communities → kodade i vektorerna

---

## Steg 3: Visualisering med t-SNE

Nu har vi 64 dimensioner men kan bara visualisera 2D eller 3D. **t-SNE** (t-Distributed Stochastic Neighbor Embedding) komprimerar dimensionerna.

### Hur t-SNE fungerar:

#### 1. Beräkna "närhet" i 64D

För varje produktpar, beräkna euklidiskt avstånd:

```
Avstånd(Coca-Cola, Fanta)    = 0.15 (nära!)
Avstånd(Coca-Cola, Snickers) = 2.87 (långt!)
```

Konvertera avstånd till sannolikheter (närmare = högre sannolikhet):

```
P(Fanta | Coca-Cola)    = 0.85  (hög sannolikhet att vara granne)
P(Snickers | Coca-Cola) = 0.03  (låg sannolikhet)
```

#### 2. Skapa 3D-representation

t-SNE placerar punkter i 3D så att:
- Produkter **nära i 64D** förblir **nära i 3D**
- Produkter **långt ifrån i 64D** förblir **långt ifrån i 3D**

#### 3. Optimeringsprocess

t-SNE använder gradient descent för att minimera Kullback-Leibler divergence:

```
minimize KL(P_64D || P_3D)

där:
P_64D = sannolikhetsfördelning för närhet i 64 dimensioner
P_3D  = sannolikhetsfördelning för närhet i 3 dimensioner
```

Iterativ process:
```
Iteration 1:   Slumpmässiga positioner i 3D
Iteration 50:  Stora kluster börjar bildas
Iteration 200: Finjustering av positioner
Iteration 300: Konvergerat! ✓
```

#### 4. Resultat

Varje produkt får en 3D-koordinat:

```python
3D_positions = {
    "Coca-Cola":    [12.3, -5.7,  8.1],   # Component 1, 2, 3
    "Fanta":        [11.8, -6.2,  7.9],   # Nära Coca-Cola!
    "Snickers":     [-15.2, 3.4, -2.1],   # Långt från Coca-Cola!
    "Vitamin Well": [-8.4,  15.3, -3.2],  # Egen cluster
}
```

---

## Vad är Component 1, 2, 3?

Component 1, 2, 3 är **nya, konstgjorda axlar** som t-SNE skapar.

### Analogi

Tänk dig att du har:
- **64D-vektor** = en beskrivning av produkten med 64 egenskaper
  - Egenskap 1 = hur mycket citrussmak
  - Egenskap 2 = hur mycket kolsyra
  - Egenskap 3 = hur söt
  - ... (61 fler egenskaper)

t-SNE säger: 
> *"Istället för 64 egenskaper, kan jag skapa 3 nya 'super-egenskaper' som fångar det viktigaste"*

**Men**: Dessa super-egenskaper är **inte tolkbara**. De är matematiska kombinationer av alla 64 original-dimensioner.

### Varför inte tolkbara?

t-SNE är en **icke-linjär** transformation. Det betyder:

```
Component 1 ≠ "ingrediens similarity"
Component 1 ≠ "pris"
Component 1 ≠ "popularitet"
Component 1 = 🤷‍♂️ "en komplex, icke-linjär funktion av alla 64 dimensioner"
```

### Vad kan du säga om komponenterna?

Det enda du kan tolka är **relationer**:
- **Närhet i 3D** = liknande produkter (i grafstrukturen)
- **Kluster** = grupper av produkter som hänger ihop
- **Avstånd** = hur olika produkter är
- **Riktning** = betyder ingenting specifikt

### Exempel på vad du INTE kan säga:

❌ "Produkter med högt Component 1-värde är söta"
❌ "Component 2 representerar pris"
❌ "Component 3 är kolsyreinnehåll"

### Exempel på vad du KAN säga:

✅ "Dessa två produkter är nära varandra → de är strukturellt lika i grafen"
✅ "Detta kluster innehåller bara läskedrycker → embeddings fångar kategori"
✅ "Denna produkt är outlier → den har unika relationer"

---

## Alternativ: Weight-baserad visualisering

För **tolkbara axlar**, använd `--visualize-weights` istället!

### Tolkbara dimensioner

Istället för abstrakta komponenter, använder vi **faktiska graph weights**:

```python
# För varje produkt, beräkna genomsnittliga weights med alla grannar:

X-axel = Average ingredient_match
Y-axel = Average user_match (co-purchase)
Z-axel = Average tag_match
```

### Exempel:

```
Coca-Cola Original:
  - Avg ingredient_match: 3.2  (medelhög, delar ingredienser med flera)
  - Avg user_match:      4.8  (hög, köps ofta tillsammans med andra)
  - Avg tag_match:       2.1  (låg, unik i sin kategori)
  
Position: [3.2, 4.8, 2.1]
```

### Fördelar med weight-visualisering:

✅ **Direkt tolkbara axlar**
- Högt X-värde → många gemensamma ingredienser
- Högt Y-värde → ofta köps tillsammans med andra
- Högt Z-värde → central i sin kategori

✅ **Insikter om produktegenskaper**
- Produkt längst till höger → ingrediensmässigt populär
- Produkt längst upp → stark cross-selling potential
- Produkt i mitten → genomsnittlig på alla dimensioner

✅ **Användbart för strategi**
- Hitta produkter med hög co-purchase → bundle-rekommendationer
- Hitta produkter med hög ingredient similarity → substitut
- Hitta produkter med låg tag_match → nisch-produkter

### t-SNE vs Weight-visualisering

| Aspekt | t-SNE | Weight-baserad |
|--------|-------|----------------|
| **Axlar** | Abstrakta komponenter | ingredient/user/tag weights |
| **Tolkbarhet** | Nej | Ja |
| **Dimensioner** | Alla 64 komprimerade | Bara 3 av många möjliga |
| **Bra för** | Se kluster och struktur | Förstå varför produkter är lika |
| **Användning** | Explorativ analys | Strategiska beslut |

**Rekommendation:** Använd båda!
- **t-SNE** för att upptäcka mönster
- **Weight-visualisering** för att förstå varför mönstren existerar

---

## Användning

### Grundläggande produktsökning

```bash
# Visa tillgängliga produkter
python find_similar_products.py

# Sök efter liknande produkter
python find_similar_products.py --product-name "Coca-Cola" --topn 10

# Sök med produkt-ID
python find_similar_products.py --product-id "07310350118342" --topn 5
```

### Visualiseringar

```bash
# 2D t-SNE (färgkodad efter subcategory)
python find_similar_products.py --visualize

# 3D t-SNE (interaktiv, öppnas i webbläsare)
python find_similar_products.py --visualize-3d

# 3D weight-baserad (tolkbara axlar!)
python find_similar_products.py --visualize-weights

# Välj PCA istället för t-SNE
python find_similar_products.py --visualize --vis-method pca
```

### Träna om embeddings

```bash
# Träna om med nya parametrar
python find_similar_products.py --retrain --dimensions 128

# Träna och visualisera direkt
python find_similar_products.py --retrain --visualize-3d
```

### Kombinera funktioner

```bash
# Sök efter produkt och visualisera
python find_similar_products.py --product-name "Snickers" --visualize-weights
```

---

## Fördelar och begränsningar

### ✅ Fördelar med Node2Vec

1. **Snabb similarity search**
   - Cosine similarity i vektorrymd: O(n) istället för O(n²) graftraversering
   - Kan använda FAISS eller andra ANN-bibliotek för miljontals produkter

2. **Fångar grafstruktur**
   - Direkta kopplingar (grannar)
   - Indirekta kopplingar (grannar-av-grannar)
   - Community structure (kluster)

3. **Flexibel**
   - Kan användas för olika downstream tasks
   - Rekommendationer, clustering, anomaly detection

4. **Skalbar**
   - Träning kan paralleliseras
   - Embeddings kan cachas och återanvändas

### ⚠️ Begränsningar

1. **Träning tar tid**
   - För 1000 produkter: ~1-2 minuter
   - För 100,000 produkter: flera timmar

2. **Hyperparametrar**
   - `p`, `q`, `walk_length`, `num_walks` påverkar resultat
   - Kräver experimentering för optimala värden

3. **Statiska embeddings**
   - Om grafen uppdateras måste embeddings tränas om
   - Nya produkter kräver ny träning (eller approximation)

4. **Interpretability**
   - Svårt att förstå vad varje dimension betyder
   - "Black box" för icke-tekniska användare
   - → Lösning: Använd weight-visualisering istället!

---

## Tekniska detaljer

### Node2Vec-parametrar

```python
node2vec = Node2Vec(
    graph=G,
    dimensions=64,        # Vektor-storlek (32-256 är vanligt)
    walk_length=30,       # Längd på random walks
    num_walks=200,        # Antal walks per nod
    p=1.0,                # Return parameter (BFS vs DFS)
    q=1.0,                # In-out parameter
    workers=4,            # Parallellisering
    weight_key='weight'   # Använd edge weights
)

model = node2vec.fit(
    window=10,            # Context window för Word2Vec
    min_count=1,          # Minimum word frequency
    batch_words=4,        # Batch size för training
    epochs=10             # Antal training epochs
)
```

### t-SNE-parametrar

```python
tsne = TSNE(
    n_components=3,       # 2D eller 3D
    perplexity=30,        # Balans mellan lokal och global struktur
    random_state=42,      # För reproducerbarhet
    n_iter=1000,          # Antal iterationer
    learning_rate=200     # Gradient descent step size
)
```

### Similarity-beräkning

```python
# Cosine similarity mellan två produkter
similarity = np.dot(vector1, vector2) / (
    np.linalg.norm(vector1) * np.linalg.norm(vector2)
)

# Värden: 0 (ortogonala) till 1 (identiska)
```

---

## Vidare läsning

### Node2Vec
- [Original paper: node2vec - Scalable Feature Learning for Networks](https://arxiv.org/abs/1607.00653)
- [node2vec Python library](https://github.com/eliorc/node2vec)

### t-SNE
- [Original paper: Visualizing Data using t-SNE](https://www.jmlr.org/papers/volume9/vandermaaten08a/vandermaaten08a.pdf)
- [How to Use t-SNE Effectively](https://distill.pub/2016/misread-tsne/)

### Word2Vec
- [Original paper: Efficient Estimation of Word Representations](https://arxiv.org/abs/1301.3781)
- [Word2Vec Tutorial](http://mccormickml.com/2016/04/19/word2vec-tutorial-the-skip-gram-model/)

### Graph Embeddings
- [Graph Representation Learning Book](https://www.cs.mcgill.ca/~wlh/grl_book/)
- [Stanford CS224W: Machine Learning with Graphs](http://web.stanford.edu/class/cs224w/)

---

## Frågor och svar

### Q: Varför 64 dimensioner?
**A:** Balans mellan:
- Expressiveness (fler dimensioner = mer information)
- Computation (färre dimensioner = snabbare)
- Overfitting (för många dimensioner = memorerar grafen)

Typiska värden: 32, 64, 128, 256

### Q: Kan jag lita på similarity scores?
**A:** Ja, för relativa jämförelser:
- Score 0.95 vs 0.60 → första produkten är mycket mer lik
- Absoluta värden är mindre viktiga

### Q: Hur ofta ska jag träna om?
**A:** När grafen ändras signifikant:
- Nya produkter tillkommer
- Edge weights uppdateras med ny försäljningsdata
- Graph struktur förändras

### Q: Kan jag använda embeddings för andra uppgifter?
**A:** Ja! Embeddings kan användas för:
- Clustering (gruppera liknande produkter)
- Classification (förutsäga kategori)
- Link prediction (förutsäga framtida kopplingar)
- Anomaly detection (hitta ovanliga produkter)

### Q: Varför Node2Vec istället för andra metoder?
**A:** Alternativen:
- **DeepWalk**: Enklare, men använder inte edge weights
- **LINE**: Snabbare, men bara för första och andra ordningens proximitet
- **GraphSAGE/GCN**: Kraftfullare, men kräver mer data och beräkning
- **Node2Vec**: Bra balans mellan prestanda, flexibilitet och enkelhet

---

## Kontakt

För frågor eller feedback, kontakta projektutvecklarna eller öppna ett issue på GitHub.

**Lycka till med dina graph embeddings!** 🚀
