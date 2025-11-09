# Visualization Module - Graf-visualisering med Matplotlib

## Översikt

Denna modul skapar **statiska visualiseringar** av produktgrafen med Matplotlib. Den fokuserar på att visa grafstruktur, kluster och relationer mellan produkter för analys och rapportering.

## Vad gör denna modul?

Skapar **statiska bilder** som:
- ✅ Visar hela grafen med alla noder och kanter
- ✅ Visar subgrafer (del av grafen)
- ✅ Färgkodning efter kategori
- ✅ Kant-tjocklek baserad på styrka
- ✅ Statistik och grafegenskaper
- ✅ Hög kvalitet för rapporter/presentations

## Användningsområden

**När använda denna modul:**
- 📊 **Rapporter** - Statiska bilder för dokumentation
- 📈 **Presentationer** - High-quality visualiseringar
- 🔬 **Analys** - Översikt av grafstruktur
- 📸 **Snapshots** - Spara tillstånd vid specifik tidpunkt

**När INTE använda:**
- ❌ Interaktiv exploration → Använd `interactive/` istället
- ❌ Stora grafer (>1000 noder) → Använd `interactive/` istället
- ❌ Real-time updates → Använd `interactive/` istället

## Teknisk Implementation

### 1. Graph Layout Algoritmer

#### Fruchterman-Reingold (Spring Layout)

**Default layout för NetworkX:**

```python
pos = nx.spring_layout(G, k=1/sqrt(n), iterations=50)
```

**Hur det fungerar:**
- **Repulsive forces:** Alla noder stöter bort varandra
- **Attractive forces:** Länkade noder dras ihop
- **Simulering:** Iterativ optimering tills balans

**Parametrar:**
- `k` - Optimal avstånd mellan noder (default: `1/sqrt(n)`)
- `iterations` - Antal optimeringssteg (default: 50)
- `scale` - Total storlek på layout

**Fördelar:**
- ✅ Bra för att visa kluster
- ✅ Estetiskt tilltalande
- ✅ Avslöjar communities

**Nackdelar:**
- ❌ Långsam för stora grafer
- ❌ Non-deterministic (olika varje gång)
- ❌ Kan producera överlapp

#### Kamada-Kawai Layout

**Alternativ layout:**

```python
pos = nx.kamada_kawai_layout(G)
```

**Hur det fungerar:**
- Minimerar "energi" i grafen
- Försöker matcha graf-avstånd med euklidiskt avstånd
- Mer deterministisk än spring layout

**Fördelar:**
- ✅ Mer stabilt
- ✅ Bättre för hierarkiska grafer

**Nackdelar:**
- ❌ Mycket långsam
- ❌ Mindre tydliga kluster

#### Circular Layout

**För specifika användningsfall:**

```python
pos = nx.circular_layout(G)
```

**Placerar alla noder i en cirkel:**
- Bra för att visa symmetri
- Används sällan för produktgrafer

### 2. Matplotlib Drawing Pipeline

#### Node Drawing

```python
nx.draw_networkx_nodes(
    G, pos,
    node_color=[colors[node] for node in G.nodes()],
    node_size=300,
    alpha=0.8,
    edgecolors='black',
    linewidths=1.0
)
```

**Parametrar:**
- `node_color` - Lista med färger (från subcategory_colors)
- `node_size` - Storlek i points² (default: 300)
- `alpha` - Transparency (0.0-1.0)
- `edgecolors` - Kant runt noden
- `linewidths` - Tjocklek på nodkant

#### Edge Drawing

```python
nx.draw_networkx_edges(
    G, pos,
    width=[G[u][v]['weight'] / 10 for u, v in G.edges()],
    alpha=0.4,
    edge_color='gray'
)
```

**Parametrar:**
- `width` - Lista med kantbredder (baserat på weight)
- `alpha` - Transparency för kanter
- `edge_color` - Färg på kanter

#### Label Drawing

```python
nx.draw_networkx_labels(
    G, pos,
    labels={node: G.nodes[node]['name'] for node in G.nodes()},
    font_size=8,
    font_family='sans-serif'
)
```

**Parametrar:**
- `labels` - Dictionary med node → text
- `font_size` - Textstorlek
- `font_family` - Font att använda

### 3. Color Management

**Integration med subcategory_colors:**

```python
from src.core.subcategory_colors import get_subcategory_colors

# Ladda färger från Excel
color_map = get_subcategory_colors()

# Applicera på noder
node_colors = []
for node in G.nodes():
    subcategory = G.nodes[node].get('subcategory', 'Unknown')
    color = color_map.get(subcategory, '#CCCCCC')  # Gray default
    node_colors.append(color)
```

**Färgformat:**
- Hex strings: `#FF5733`
- RGB tuples: `(0.8, 0.2, 0.1)`
- Named colors: `'red'`, `'blue'`

### 4. Figure Configuration

#### Size & DPI

```python
plt.figure(figsize=(20, 20), dpi=150)
```

**Parametrar:**
- `figsize` - Tuple (width, height) i inches
- `dpi` - Dots per inch (resolution)

**Filstorlek:**
- `figsize=(10, 10), dpi=100` → ~500 KB
- `figsize=(20, 20), dpi=150` → ~2 MB
- `figsize=(30, 30), dpi=300` → ~8 MB

#### Tight Layout

```python
plt.tight_layout()
```

**Effekt:**
- Tar bort onödig whitespace
- Anpassar margins automatiskt
- Ser till att labels inte klipps av

#### Axis Configuration

```python
plt.axis('off')  # Dölj axlar och grid
```

### 5. Edge Width Calculation

**Dynamisk kantbredd:**

```python
def calculate_edge_widths(G, scale_factor=0.1):
    """
    Beräkna kantbredder baserat på weight
    
    Args:
        G: NetworkX graf
        scale_factor: Multiplikator för weights
    
    Returns:
        List med bredder för varje kant
    """
    widths = []
    for u, v in G.edges():
        weight = G[u][v].get('weight', 1.0)
        width = weight * scale_factor
        widths.append(width)
    return widths
```

**Exempel:**
```python
# Weight 50 → width 5.0
# Weight 10 → width 1.0
# Weight 1 → width 0.1
widths = calculate_edge_widths(G, scale_factor=0.1)
```

## Filer

### `visualize.py`
**Huvudfil med visualiseringsfunktioner**

#### Funktioner:

##### `draw_graph(G, output_path, title)`
**Rita hela grafen**

```python
def draw_graph(G, output_path='graph.png', title='Product Graph'):
    """
    Rita och spara hela produktgrafen
    
    Args:
        G: NetworkX graf
        output_path: Var bilden ska sparas
        title: Titel på grafen
    """
    plt.figure(figsize=(20, 20), dpi=150)
    pos = nx.spring_layout(G, k=1/sqrt(len(G)), iterations=50)
    
    # Rita noder med färger
    node_colors = [get_node_color(node) for node in G.nodes()]
    nx.draw_networkx_nodes(G, pos, node_color=node_colors)
    
    # Rita kanter med vikter
    widths = [G[u][v]['weight'] * 0.1 for u, v in G.edges()]
    nx.draw_networkx_edges(G, pos, width=widths, alpha=0.4)
    
    plt.title(title, fontsize=20)
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
```

##### `draw_subgraph(G, node_ids, output_path, depth)`
**Rita en subgraf runt specifika noder**

```python
def draw_subgraph(
    G, 
    node_ids, 
    output_path='subgraph.png',
    depth=1
):
    """
    Rita subgraf runt valda noder
    
    Args:
        G: NetworkX graf
        node_ids: Lista med central noder
        output_path: Var bilden ska sparas
        depth: Hur många hopp från center (1-3)
    """
    # Hitta grannar inom depth
    subgraph_nodes = set(node_ids)
    for _ in range(depth):
        new_nodes = set()
        for node in subgraph_nodes:
            new_nodes.update(G.neighbors(node))
        subgraph_nodes.update(new_nodes)
    
    # Skapa subgraf
    subG = G.subgraph(subgraph_nodes)
    
    # Rita
    draw_graph(subG, output_path, title=f'Subgraph (depth={depth})')
```

**Depth exempel:**
- `depth=1` - Endast direkta grannar
- `depth=2` - Grannar + grannarnas grannar
- `depth=3` - 3 hopp ut

##### `print_graph_stats(G)`
**Skriv ut statistik om grafen**

```python
def print_graph_stats(G):
    """
    Print comprehensive graph statistics
    """
    print(f"Number of nodes: {G.number_of_nodes()}")
    print(f"Number of edges: {G.number_of_edges()}")
    print(f"Average degree: {sum(dict(G.degree()).values()) / G.number_of_nodes():.2f}")
    print(f"Density: {nx.density(G):.4f}")
    print(f"Is connected: {nx.is_connected(G)}")
    
    if nx.is_connected(G):
        print(f"Diameter: {nx.diameter(G)}")
        print(f"Average shortest path: {nx.average_shortest_path_length(G):.2f}")
    else:
        components = list(nx.connected_components(G))
        print(f"Number of components: {len(components)}")
        print(f"Largest component: {len(max(components, key=len))} nodes")
```

**Output exempel:**
```
Number of nodes: 856
Number of edges: 3421
Average degree: 7.99
Density: 0.0093
Is connected: True
Diameter: 12
Average shortest path: 4.23
```

## Grafegenskaper & Metrics

### Basic Metrics

**Number of nodes:**
```python
n = G.number_of_nodes()
```

**Number of edges:**
```python
m = G.number_of_edges()
```

**Degree (antal kopplingar per nod):**
```python
degrees = dict(G.degree())
avg_degree = sum(degrees.values()) / len(degrees)
```

### Density

**Graf-densitet:**
```python
density = nx.density(G)
# density = 2m / (n(n-1))  för unriktad graf
```

**Tolkning:**
- `density = 0.0` - Inga kanter
- `density = 1.0` - Komplett graf (alla noder kopplade)
- `density < 0.01` - Sparse graph (vanligt)
- `density > 0.5` - Dense graph (ovanligt)

### Connectivity

**Connected components:**
```python
components = list(nx.connected_components(G))
num_components = len(components)
largest = max(components, key=len)
```

**Diameter (längsta kortaste vägen):**
```python
if nx.is_connected(G):
    diameter = nx.diameter(G)
```

**Average shortest path:**
```python
if nx.is_connected(G):
    avg_path = nx.average_shortest_path_length(G)
```

### Centrality Measures

**Degree Centrality:**
```python
degree_centrality = nx.degree_centrality(G)
# Mest kopplade noder
```

**Betweenness Centrality:**
```python
betweenness = nx.betweenness_centrality(G)
# Noder som ligger på många kortaste vägar
```

**PageRank:**
```python
pagerank = nx.pagerank(G)
# Viktighet baserat på länkstruktur
```

## Output

**Standard output:**
- `output/visualizations/graph.png`
- `output/visualizations/subgraph_*.png`

**Format:**
- PNG (raster graphics)
- Transparent background optional
- High DPI för print quality

## Användning

### Via entry point:
```bash
python run_visualization.py
```

### Direkt import:
```python
from src.core.main import setup_graph
from src.visualization.visualize import draw_graph, draw_subgraph, print_graph_stats

# Skapa graf
G = setup_graph(min_edge_weight=5.0)

# Rita hela grafen
draw_graph(G, 'output/visualizations/full_graph.png')

# Statistik
print_graph_stats(G)

# Rita subgraf runt Coca Cola
coca_cola_id = "07310350118342"
draw_subgraph(
    G, 
    [coca_cola_id], 
    'output/visualizations/coca_cola_neighborhood.png',
    depth=2
)
```

## Best Practices

### För stora grafer (>500 noder):

1. **Använd större figsize:**
```python
plt.figure(figsize=(30, 30), dpi=150)
```

2. **Minska label size:**
```python
nx.draw_networkx_labels(G, pos, font_size=6)
```

3. **Öka node spacing:**
```python
pos = nx.spring_layout(G, k=2/sqrt(n), iterations=100)
```

4. **Rita bara stora kanter:**
```python
large_edges = [(u, v) for u, v in G.edges() if G[u][v]['weight'] > 20]
subG = G.edge_subgraph(large_edges)
```

### För presentation:

1. **Hög DPI:**
```python
plt.savefig(output_path, dpi=300)
```

2. **Vit bakgrund:**
```python
plt.savefig(output_path, facecolor='white')
```

3. **Stor titel:**
```python
plt.title(title, fontsize=24, fontweight='bold')
```

## Performance

**Rendering time:**
- 100 noder: ~1 sekund
- 500 noder: ~5 sekunder
- 1000 noder: ~20 sekunder
- 2000+ noder: Använd `interactive/` istället

**Memory usage:**
- 100 noder: ~50 MB
- 1000 noder: ~500 MB
- 5000 noder: ~2 GB

## Troubleshooting

### Problem: Labels överlappar

**Lösning 1 - Större layout:**
```python
pos = nx.spring_layout(G, k=2/sqrt(n), scale=2)
```

**Lösning 2 - Adjust text:**
```python
from adjustText import adjust_text
# Optimerar label-placering
```

**Lösning 3 - Rita bara selected labels:**
```python
important_nodes = get_high_degree_nodes(G, top_n=50)
labels = {node: name for node, name in important_nodes}
nx.draw_networkx_labels(G, pos, labels=labels)
```

### Problem: Kanter täcker noder

**Lösning - Rita i rätt ordning:**
```python
# 1. Rita kanter först
nx.draw_networkx_edges(G, pos)
# 2. Rita noder ovanpå
nx.draw_networkx_nodes(G, pos)
# 3. Rita labels sist
nx.draw_networkx_labels(G, pos)
```

### Problem: Långsam rendering

**Lösning - Använd interactive istället:**
```python
from src.interactive.generate_html import generate_html_visualization
generate_html_visualization(G, 'output/interactive/graph.html')
```

## Framtida Förbättringar

- [ ] Plotly static exports (bättre kvalitet)
- [ ] SVG output för vector graphics
- [ ] Automatisk community detection & färgning
- [ ] Heatmaps för centrality
- [ ] Sankey diagrams för flow
- [ ] Chord diagrams för relationer
- [ ] Exportera till Gephi format

## Jämförelse med andra moduler

| Feature | Visualization | Interactive | Embeddings |
|---------|---------------|-------------|------------|
| **Output** | Static PNG | Interactive HTML | Plots + Analysis |
| **Användning** | Reports | Exploration | ML/Analysis |
| **Storlek** | <1000 nodes | 10000+ nodes | Any size |
| **Rendering** | Slow | Fast | Medium |
| **Interaktivitet** | None | Full | Limited |

## Läs mer

- **[NetworkX Drawing](https://networkx.org/documentation/stable/reference/drawing.html)** - Official docs
- **[Matplotlib](https://matplotlib.org/)** - Visualization library
- **[Graph Layout Algorithms](https://en.wikipedia.org/wiki/Graph_drawing)** - Wikipedia
