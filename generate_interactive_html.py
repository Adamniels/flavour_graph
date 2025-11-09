"""
Generate HTML-based interactive product selection visualization.
Creates a professional, business-ready visualization similar to embeddings HTML files.
"""
import networkx as nx
import json
import copy
from main import setup_graph, create_priority_list_from_sales
from models import IndexedPriorityList
from subcategory_colors import get_subcategory_color, create_subcategory_colormap


def generate_html_visualization(G: nx.DiGraph, priority_list: IndexedPriorityList, 
                                num_products: int = 15, output_file: str = 'interactive_selection.html'):
    """Generate an HTML file with interactive product selection visualization."""
    
    # Calculate max weight
    max_weight = 0.0
    for u, v, data in G.edges(data=True):
        weight = data.get('weight', 0.0)
        if weight > max_weight:
            max_weight = weight
    
    # Create subcategory colormap
    subcategory_colors = create_subcategory_colormap(G)
    product_names = {node: G.nodes[node].get('name', node) for node in G.nodes()}
    
    # Create layout
    print("Calculating layout...")
    for u, v in G.edges():
        w = G[u][v].get('weight', 1)
        G[u][v]['spring_weight'] = w
    
    pos = nx.spring_layout(G, k=0.8, iterations=150, weight='spring_weight', 
                          seed=42, scale=5, threshold=1e-5)
    print("✓ Layout calculated")
    
    # Prepare nodes data
    nodes = []
    for node_id in G.nodes():
        subcategory = G.nodes[node_id].get('subcategory', 'Unknown')
        color = get_subcategory_color(subcategory)
        name = product_names[node_id]
        prio = priority_list._items[0][1] if priority_list._items else 0
        for nid, val in priority_list._items:
            if nid == node_id:
                prio = val
                break
        
        nodes.append({
            'id': node_id,
            'label': name[:30] + '...' if len(name) > 30 else name,
            'title': f"{name}<br>ID: {node_id}<br>Category: {subcategory}<br>Priority: {prio:,}",
            'x': pos[node_id][0] * 100,  # Scale for vis-network
            'y': pos[node_id][1] * 100,
            'color': color,
            'size': 10 + (prio / 100) * 5,
            'subcategory': subcategory,
            'priority': prio
        })
    
    # Prepare edges data
    edges = []
    edge_id = 0
    for u, v, data in G.edges(data=True):
        weight = data.get('weight', 0.0)
        edges.append({
            'id': edge_id,
            'from': u,
            'to': v,
            'value': weight,
            'title': f"Weight: {weight:.2f}",
            'width': max(0.5, weight / max_weight * 3),
            'color': {'color': '#94A3B8', 'opacity': 0.3}
        })
        edge_id += 1
    
    # Convert priority list to dict for JavaScript
    priority_dict = {nid: val for nid, val in priority_list._items}
    
    # Convert to JSON strings for JavaScript
    nodes_json = json.dumps(nodes, indent=8)
    edges_json = json.dumps(edges, indent=8)
    priority_dict_json = json.dumps(priority_dict, indent=8)
    subcategory_colors_json = json.dumps(subcategory_colors, indent=8)
    
    # Generate HTML
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <title>Interactive Product Selection</title>
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #F8F9FA;
            color: #1F2937;
        }}
        .container {{
            display: flex;
            gap: 20px;
            max-width: 1800px;
            margin: 0 auto;
        }}
        .graph-panel {{
            flex: 1;
            background: white;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            padding: 20px;
        }}
        .stats-panel {{
            width: 350px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            padding: 20px;
            overflow-y: auto;
            max-height: calc(100vh - 40px);
        }}
        #network {{
            width: 100%;
            height: 800px;
            border: 1px solid #E5E7EB;
            border-radius: 4px;
        }}
        h1 {{
            margin: 0 0 20px 0;
            font-size: 24px;
            font-weight: 600;
            color: #111827;
        }}
        h2 {{
            margin: 0 0 15px 0;
            font-size: 18px;
            font-weight: 600;
            color: #374151;
        }}
        .controls {{
            margin-bottom: 20px;
            display: flex;
            gap: 10px;
        }}
        button {{
            padding: 10px 20px;
            font-size: 14px;
            font-weight: 600;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .btn-primary {{
            background-color: #2563EB;
            color: white;
        }}
        .btn-primary:hover {{
            background-color: #1D4ED8;
        }}
        .btn-secondary {{
            background-color: #64748B;
            color: white;
        }}
        .btn-secondary:hover {{
            background-color: #475569;
        }}
        .btn-primary:disabled {{
            background-color: #CBD5E1;
            cursor: not-allowed;
        }}
        .stat-card {{
            background: #F9FAFB;
            border: 1px solid #E5E7EB;
            border-radius: 6px;
            padding: 15px;
            margin-bottom: 15px;
        }}
        .stat-card.current {{
            background: #ECFDF5;
            border-color: #10B981;
            border-width: 2px;
        }}
        .stat-label {{
            font-size: 11px;
            font-weight: 600;
            color: #6B7280;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 5px;
        }}
        .stat-value {{
            font-size: 16px;
            font-weight: 600;
            color: #111827;
        }}
        .product-name {{
            font-size: 14px;
            font-weight: 600;
            color: #111827;
            margin: 5px 0;
        }}
        .product-category {{
            font-size: 12px;
            color: #6B7280;
            font-style: italic;
        }}
        .affected-list {{
            list-style: none;
            padding: 0;
            margin: 10px 0;
        }}
        .affected-item {{
            padding: 8px;
            margin: 5px 0;
            background: #FFF7ED;
            border-left: 3px solid #F59E0B;
            border-radius: 4px;
            font-size: 12px;
        }}
        .selected-list {{
            list-style: none;
            padding: 0;
            margin: 10px 0;
        }}
        .selected-item {{
            padding: 8px;
            margin: 5px 0;
            background: #F9FAFB;
            border-left: 3px solid #3B82F6;
            border-radius: 4px;
            font-size: 12px;
        }}
        .selected-item.current {{
            background: #ECFDF5;
            border-color: #10B981;
        }}
        .progress-bar {{
            width: 100%;
            height: 8px;
            background: #E5E7EB;
            border-radius: 4px;
            overflow: hidden;
            margin: 10px 0;
        }}
        .progress-fill {{
            height: 100%;
            background: #2563EB;
            transition: width 0.3s;
        }}
        .info-text {{
            font-size: 12px;
            color: #6B7280;
            margin-top: 10px;
            font-style: italic;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="graph-panel">
            <h1>Interactive Product Selection</h1>
            <div class="controls">
                <button class="btn-primary" id="nextBtn" onclick="nextSelection()">Next Selection</button>
                <button class="btn-secondary" id="resetBtn" onclick="reset()">Reset</button>
            </div>
            <div id="network"></div>
        </div>
        <div class="stats-panel">
            <h2>Selection Information</h2>
            <div class="stat-card">
                <div class="stat-label">Progress</div>
                <div class="stat-value" id="progress">0 / {num_products}</div>
                <div class="progress-bar">
                    <div class="progress-fill" id="progressBar" style="width: 0%"></div>
                </div>
            </div>
            <div id="currentSelection"></div>
            <div id="affectedNeighbors"></div>
            <div id="selectedProducts"></div>
            <div class="info-text">
                Click "Next Selection" to continue<br>
                Click "Reset" to start over
            </div>
        </div>
    </div>

    <script type="text/javascript">
        // Graph data
        const nodes = new vis.DataSet({nodes_json});
        const edges = new vis.DataSet({edges_json});
        
        // State
        let selected = [];
        let currentSelection = null;
        let affectedNeighbors = [];
        let iteration = 0;
        const maxIterations = {num_products};
        const maxWeight = {max_weight:.2f};
        
        // Priority list (as dict for fast lookup)
        let priorityList = {priority_dict_json};
        const originalPriorityList = JSON.parse(JSON.stringify(priorityList));
        
        // Subcategory colors
        const subcategoryColors = {subcategory_colors_json};
        
        // Network options
        const options = {{
            nodes: {{
                shape: 'dot',
                font: {{
                    size: 12,
                    face: 'Arial',
                    color: '#1F2937'
                }},
                borderWidth: 2,
                shadow: true
            }},
            edges: {{
                smooth: {{
                    type: 'continuous',
                    roundness: 0.5
                }},
                arrows: {{
                    to: {{
                        enabled: true,
                        scaleFactor: 0.8
                    }}
                }},
                shadow: true
            }},
            physics: {{
                enabled: false
            }},
            interaction: {{
                hover: true,
                tooltipDelay: 100
            }}
        }};
        
        // Initialize network
        const container = document.getElementById('network');
        const data = {{ nodes: nodes, edges: edges }};
        const network = new vis.Network(container, data, options);
        
        // Update visualization
        function updateVisualization() {{
            const updateNodes = [];
            const updateEdges = [];
            const allNodes = nodes.get();
            const allEdges = edges.get();
            
            // Update nodes
            allNodes.forEach(node => {{
                const nodeId = node.id;
                const prio = priorityList[nodeId] || 0;
                const subcategory = node.subcategory || 'Unknown';
                const color = subcategoryColors[subcategory] || '#808080';
                
                let nodeColor = color;
                let nodeSize = 10 + (prio / 100) * 5;
                let borderColor = color;
                let borderWidth = 2;
                
                if (nodeId === currentSelection) {{
                    nodeColor = '#10B981';
                    nodeSize = 25;
                    borderColor = '#059669';
                    borderWidth = 3;
                }} else if (selected.includes(nodeId)) {{
                    nodeSize = 18;
                    borderColor = '#374151';
                    borderWidth = 2.5;
                }} else if (affectedNeighbors.includes(nodeId)) {{
                    nodeSize = 20;
                    borderColor = '#F59E0B';
                    borderWidth = 3;
                }}
                
                updateNodes.push({{
                    id: nodeId,
                    color: {{
                        background: nodeColor,
                        border: borderColor
                    }},
                    size: nodeSize,
                    borderWidth: borderWidth
                }});
            }});
            
            // Update edges
            allEdges.forEach(edge => {{
                const isCurrentEdge = edge.from === currentSelection || edge.to === currentSelection;
                let edgeColor = '#94A3B8';
                let edgeWidth = 0.5;
                let edgeOpacity = 0.2;
                
                if (isCurrentEdge && currentSelection) {{
                    edgeColor = '#F59E0B';
                    edgeWidth = Math.max(2, (edge.value / maxWeight) * 4);
                    edgeOpacity = 0.7;
                }}
                
                updateEdges.push({{
                    id: edge.id,
                    color: {{
                        color: edgeColor,
                        opacity: edgeOpacity
                    }},
                    width: edgeWidth
                }});
            }});
            
            nodes.update(updateNodes);
            edges.update(updateEdges);
            
            // Update stats panel
            updateStatsPanel();
        }}
        
        // Update stats panel
        function updateStatsPanel() {{
            // Progress
            document.getElementById('progress').textContent = `${{iteration}} / ${{maxIterations}}`;
            const progressPercent = (iteration / maxIterations) * 100;
            document.getElementById('progressBar').style.width = `${{progressPercent}}%`;
            
            // Current selection
            const currentDiv = document.getElementById('currentSelection');
            if (currentSelection) {{
                const node = nodes.get(currentSelection);
                const subcategory = node.subcategory || 'Unknown';
                const color = subcategoryColors[subcategory] || '#808080';
                currentDiv.innerHTML = `
                    <div class="stat-card current">
                        <div class="stat-label">Now Selecting</div>
                        <div class="product-name">${{node.label}}</div>
                        <div class="product-category" style="color: ${{color}}">${{subcategory}}</div>
                    </div>
                `;
            }} else {{
                currentDiv.innerHTML = '';
            }}
            
            // Affected neighbors
            const affectedDiv = document.getElementById('affectedNeighbors');
            if (affectedNeighbors.length > 0) {{
                let html = '<div class="stat-card"><div class="stat-label">Affected Neighbors</div><ul class="affected-list">';
                affectedNeighbors.slice(0, 8).forEach(neighborId => {{
                    const node = nodes.get(neighborId);
                    const oldPrio = originalPriorityList[neighborId] || 0;
                    const newPrio = priorityList[neighborId] || 0;
                    const reduction = oldPrio > 0 ? ((oldPrio - newPrio) / oldPrio * 100).toFixed(0) : 0;
                    html += `<li class="affected-item">${{node.label}}<br><small>${{oldPrio.toLocaleString()}} → ${{newPrio.toLocaleString()}} (-${{reduction}}%)</small></li>`;
                }});
                if (affectedNeighbors.length > 8) {{
                    html += `<li style="font-size: 11px; color: #6B7280; font-style: italic;">... and ${{affectedNeighbors.length - 8}} more</li>`;
                }}
                html += '</ul></div>';
                affectedDiv.innerHTML = html;
            }} else {{
                affectedDiv.innerHTML = '';
            }}
            
            // Selected products
            const selectedDiv = document.getElementById('selectedProducts');
            if (selected.length > 0) {{
                let html = '<div class="stat-card"><div class="stat-label">Selected Products</div><ul class="selected-list">';
                selected.slice(-10).forEach((prodId, idx) => {{
                    const node = nodes.get(prodId);
                    const num = selected.length - 10 + idx + 1;
                    const isCurrent = prodId === currentSelection;
                    html += `<li class="selected-item ${{isCurrent ? 'current' : ''}}">${{num}}. ${{node.label}}</li>`;
                }});
                if (selected.length > 10) {{
                    html += `<li style="font-size: 11px; color: #6B7280; font-style: italic;">... ${{selected.length - 10}} more above</li>`;
                }}
                html += '</ul></div>';
                selectedDiv.innerHTML = html;
            }} else {{
                selectedDiv.innerHTML = '';
            }}
            
            // Update button state
            document.getElementById('nextBtn').disabled = iteration >= maxIterations || Object.keys(priorityList).length === 0;
        }}
        
        // Next selection
        function nextSelection() {{
            if (iteration >= maxIterations || Object.keys(priorityList).length === 0) {{
                return;
            }}
            
            // Get highest priority
            let highestId = null;
            let highestPrio = -1;
            for (const [nodeId, prio] of Object.entries(priorityList)) {{
                if (prio > highestPrio) {{
                    highestPrio = prio;
                    highestId = nodeId;
                }}
            }}
            
            if (!highestId) return;
            
            // Get neighbors
            const neighbors = [];
            const allEdges = edges.get();
            allEdges.forEach(edge => {{
                if (edge.from === highestId) neighbors.push(edge.to);
                if (edge.to === highestId) neighbors.push(edge.from);
            }});
            
            // Reduce neighbor priorities
            affectedNeighbors = [];
            neighbors.forEach(neighborId => {{
                if (priorityList[neighborId] !== undefined) {{
                    const oldPrio = priorityList[neighborId];
                    const edge = allEdges.find(e => 
                        (e.from === highestId && e.to === neighborId) ||
                        (e.to === highestId && e.from === neighborId)
                    );
                    const weight = edge ? edge.value : 0;
                    
                    // Reduce priority based on weight
                    const reductionFactor = Math.min(weight / maxWeight, 0.65);
                    const newPrio = Math.max(1, Math.floor(oldPrio * (1 - reductionFactor)));
                    
                    if (oldPrio !== newPrio) {{
                        priorityList[neighborId] = newPrio;
                        affectedNeighbors.push(neighborId);
                    }}
                }}
            }});
            
            // Add to selected
            selected.push(highestId);
            currentSelection = highestId;
            iteration++;
            
            // Remove from priority list
            delete priorityList[highestId];
            
            // Update visualization
            updateVisualization();
        }}
        
        // Reset
        function reset() {{
            selected = [];
            currentSelection = null;
            affectedNeighbors = [];
            iteration = 0;
            priorityList = JSON.parse(JSON.stringify(originalPriorityList));
            updateVisualization();
        }}
        
        // Initial update
        updateVisualization();
    </script>
</body>
</html>"""
    
    # Write HTML file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✓ HTML visualization saved to {output_file}")
    return output_file


if __name__ == "__main__":
    print("=" * 70)
    print("GENERATING HTML INTERACTIVE SELECTION VISUALIZATION")
    print("=" * 70)
    print("\nSetting up...")
    
    G = setup_graph(min_edge_weight=5.0)
    print(f"✓ Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    
    import sys
    from io import StringIO
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    priority_list = create_priority_list_from_sales(G)
    sys.stdout = old_stdout
    print(f"✓ Priority list ready")
    
    print("\nGenerating HTML visualization...")
    output_file = generate_html_visualization(G, priority_list, num_products=15)
    
    print("\n" + "=" * 70)
    print(f"✓ Complete! Open {output_file} in your browser")
    print("=" * 70)

