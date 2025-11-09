# Guide: Generera alla Output-filer 📁

Denna guide visar hur du genererar alla visualiseringar och output-filer i projektet.

## Översikt av genererade filer

Alla genererade filer sparas i organiserade undermappar under `output/`:

```
output/
├── html/                                      (4.3 MB)
│   └── interactive_selection.html             (4.3 MB) - Interaktiv produktval
└── visualizations/                            (10 MB)
    ├── embeddings_visualization_2d.png        (719 KB) - 2D t-SNE plot
    ├── embeddings_visualization_3d.html       (4.7 MB) - 3D interaktiv plotly
    └── embeddings_visualization_weights.html  (4.9 MB) - 3D baserad på grafvikter
```

## Snabbstart: Generera allt

```bash
# 1. Aktivera virtual environment (om inte redan aktiverat)
source venv/bin/activate

# 2. Generera alla filer
python generate_interactive_html_fast.py
python find_similar_products.py --visualize --visualize-3d --visualize-weights
```

## Detaljerade kommandon

### 1. Interaktiv HTML-visualisering (output/html/)

**Kommando:**
```bash
python generate_interactive_html_fast.py
```

**Genererar:**
- `output/html/interactive_selection.html` (4.3 MB)

**Beskrivning:**
- Interaktiv canvas-baserad visualisering av produktgrafen
- Klicka "Next Selection" för att välja produkter stegvis
- Visar hur prioriteter minskar när produkter väljs
- Färgade noder baserat på produktkategori
- **Zoom:** Använd mushjulet för att zooma in/ut
- **Panorera:** Dra med musen för att flytta grafen
- Visar grafkopplingar med vikter när en produkt väljs

**Tid:** ~10-15 sekunder

**Funktioner:**
- Stegvis produktval med "Next Selection"-knapp
- Reset-knapp för att börja om
- Visar påverkade grannar med prioritetsändringar
- Lista över alla valda produkter
- Progress bar för antal valda produkter

---

### 2. Embeddings-visualiseringar (output/visualizations/)

**Kommando:**
```bash
python find_similar_products.py --visualize --visualize-3d --visualize-weights
```

**Genererar:**
- `output/visualizations/embeddings_visualization_2d.png` (719 KB)
- `output/visualizations/embeddings_visualization_3d.html` (4.7 MB)
- `output/visualizations/embeddings_visualization_weights.html` (4.9 MB)

**Beskrivning:**

#### 2D Visualisering (PNG)
- t-SNE reduktion av Node2Vec embeddings till 2D
- Färgad efter produktkategori
- Statisk bild (PNG)

#### 3D Interaktiv (HTML med plotly)
- t-SNE reduktion till 3D
- Interaktiv rotation och zoom
- Hover för produktinformation
- Färgad efter produktkategori

#### 3D Weight-baserad (HTML med plotly)
- Baserad på faktiska grafvikter
- X-axis: Genomsnittlig ingredient_match
- Y-axis: Genomsnittlig user_match (co-purchase)
- Z-axis: Genomsnittlig tag_match
- Mer tolkningsbar än t-SNE

**Tid:** ~20-30 sekunder totalt

**Kräver:** plotly, scikit-learn (redan installerade)

---

## Individuella visualiseringsflags

Du kan också generera visualiseringar individuellt:

```bash
# Endast 2D PNG
python find_similar_products.py --visualize

# Endast 3D interaktiv
python find_similar_products.py --visualize-3d

# Endast weight-baserad 3D
python find_similar_products.py --visualize-weights

# Kombinera som du vill
python find_similar_products.py --visualize --visualize-3d
```

## Rensa och regenerera

För att ta bort alla genererade filer och skapa nya:

```bash
# Ta bort alla genererade filer
rm -rf output/html/*.html
rm -rf output/visualizations/*.{png,html}

# Regenerera allt
python generate_interactive_html_fast.py
python find_similar_products.py --visualize --visualize-3d --visualize-weights
```

Eller helt enkelt:
```bash
# Ta bort hela output-mappen och regenerera
rm -rf output
mkdir -p output/{html,visualizations}

# Kör alla scripts
python generate_interactive_html_fast.py
python find_similar_products.py --visualize --visualize-3d --visualize-weights
```

## Andra användbara kommandon

### Träna om embeddings (tar ~2-3 minuter)
```bash
python find_similar_products.py --retrain
```

### Hitta liknande produkter
```bash
# Med produktnamn
python find_similar_products.py --product-name "Coca Cola"

# Med produkt-ID
python find_similar_products.py --product-id "07310350118342" --topn 10

# Med visualiseringar
python find_similar_products.py --product-name "Snickers" --visualize
```

### Visa produktgraf och statistik
```bash
python main.py
python visualize.py
```

### Öppna interaktiv HTML-visualisering
```bash
# Efter att ha genererat filen
open output/html/interactive_selection.html  # macOS
xdg-open output/html/interactive_selection.html  # Linux
start output/html/interactive_selection.html  # Windows
```

## Filstorlekar och krav

| Fil | Storlek | Kräver |
|-----|---------|--------|
| interactive_selection.html | 4.3 MB | networkx |
| embeddings_visualization_2d.png | 719 KB | node2vec, scikit-learn |
| embeddings_visualization_3d.html | 4.7 MB | plotly, scikit-learn |
| embeddings_visualization_weights.html | 4.9 MB | plotly |

**Totalt:** ~15 MB för alla genererade filer

## Felsökning

### Problem: "No module named 'networkx'"
**Lösning:**
```bash
pip install -r requirements.txt
```

### Problem: "embeddings_model.pkl not found"
**Lösning:**
```bash
python find_similar_products.py --retrain
```

### Problem: Webbläsaren öppnar inte HTML-filen
**Lösning:** Öppna manuellt:
```bash
# Navigera till filen i din filhanterare och dubbelklicka
# Eller använd kommandot för ditt OS:
open output/html/interactive_selection.html  # macOS
xdg-open output/html/interactive_selection.html  # Linux
```

## Git och version control

Mappen `output/` är i `.gitignore`, så genererade filer trackas inte av git.

För att checka in output-mappstrukturen utan filerna:
```bash
git add output/*/.gitkeep
git commit -m "Add output directory structure"
```

## Sammanfattning

För att generera **alla** visualiseringar och output:

```bash
# Aktivera environment (om inte redan aktiverat)
source venv/bin/activate

# Generera allt (totalt ~1 minut)
python generate_interactive_html_fast.py                                        # ~10 sekunder
python find_similar_products.py --visualize --visualize-3d --visualize-weights  # ~30 sekunder
```

Klart! Alla filer finns nu i `output/` mappen. 🎉

### Öppna resultatet

```bash
# Öppna interaktiv visualisering i webbläsaren
open output/html/interactive_selection.html
```
