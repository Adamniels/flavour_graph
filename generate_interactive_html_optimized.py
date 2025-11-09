"""
Generate optimized HTML-based interactive product selection visualization.
Uses D3.js with canvas rendering for better performance on large graphs.
"""
import networkx as nx
import json
from main import setup_graph, create_priority_list_from_sales
from models import IndexedPriorityList
from subcategory_colors import get_subcategory_color, create_subcategory_colormap


def generate_html_visualization(G: nx.DiGraph, priority_list: IndexedPriorityList, 
                                num_products: int = 15, output_file: str = 'interactive_selection.html'):
    """Generate an optimized HTML file with interactive product selection visualization."""
    
    # Calculate max weight
    max_weight = 0.0
    for u, v, data in G.edges(data=True):
        weight = data.get('weight', 0.0)
        if weight > max_weight:
            max_weight = weight
    
    # Create subcategory colormap
    subcategory_colors = create_subcategory_colormap(G)
    product_names = {node: G.nodes[node].get('name', node) for node in G.nodes()}
    
    # Create layout - use a simpler, faster layout
    print("Calculating layout...")
    for u, v in G.edges():
        w = G[u][v].get('weight', 1)
        G[u][v]['spring_weight'] = w
    
    pos = nx.spring_layout(G, k=1.0, iterations=50, weight='spring_weight', 
                          seed=42, scale=3, threshold=1e-4)
    print("✓ Layout calculated")
    
    # Prepare nodes data - only include essential info
    nodes_data = []
    node_positions = {}
    for node_id in G.nodes():
        subcategory = G.nodes[node_id].get('subcategory', 'Unknown')
        color = get_subcategory_color(subcategory)
        name = product_names[node_id]
        prio = 0
        for nid, val in priority_list._items:
            if nid == node_id:
                prio = val
                break
        
        x, y = pos[node_id]
        node_positions[node_id] = {'x': x, 'y': y}
        
        nodes_data.append({
            'id': node_id,
            'name': name,
            'label': name[:25] + '...' if len(name) > 25 else name,
            'subcategory': subcategory,
            'color': color,
            'priority': prio,
            'x': x,
            'y': y
        })
    
    # Prepare edges data - only include essential info
    edges_data = []
    for u, v, data in G.edges(data=True):
        weight = data.get('weight', 0.0)
        edges_data.append({
            'source': u,
            'target': v,
            'weight': weight
        })
    
    # Convert priority list to dict
    priority_dict = {nid: val for nid, val in priority_list._items}
    
    # Convert to JSON strings
    nodes_json = json.dumps(nodes_data)
    edges_json = json.dumps(edges_data)
    priority_dict_json = json.dumps(priority_dict)
    subcategory_colors_json = json.dumps(subcategory_colors)
    node_positions_json = json.dumps(node_positions)
    
    # Generate optimized HTML with D3.js
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <title>Interactive Product Selection</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background-color: #F8F9FA;
            color: #1F2937;
            overflow: hidden;
        }}
        .container {{
            display: flex;
            height: 100vh;
            gap: 20px;
            padding: 20px;
        }}
        .graph-panel {{
            flex: 1;
            background: white;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            padding: 20px;
            display: flex;
            flex-direction: column;
        }}
        .stats-panel {{
            width: 380px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            padding: 20px;
            overflow-y: auto;
        }}
        #graph-canvas {{
            flex: 1;
            border: 1px solid #E5E7EB;
            border-radius: 4px;
            cursor: move;
        }}
        h1 {{
            margin: 0 0 15px 0;
            font-size: 22px;
            font-weight: 600;
            color: #111827;
        }}
        h2 {{
            margin: 0 0 15px 0;
            font-size: 16px;
            font-weight: 600;
            color: #374151;
        }}
        .controls {{
            margin-bottom: 15px;
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
        .btn-primary:hover:not(:disabled) {{
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
            margin-bottom: 8px;
        }}
        .stat-value {{
            font-size: 18px;
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
        .affected-list, .selected-list {{
            list-style: none;
            padding: 0;
            margin: 10px 0;
        }}
        .affected-item, .selected-item {{
            padding: 8px;
            margin: 5px 0;
            background: #FFF7ED;
            border-left: 3px solid #F59E0B;
            border-radius: 4px;
            font-size: 12px;
        }}
        .selected-item {{
            background: #F9FAFB;
            border-color: #3B82F6;
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
            <canvas id="graph-canvas"></canvas>
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
        </div>
    </div>

    <script type="text/javascript">
        // Data
        const nodesData = {nodes_json};
        const edgesData = {edges_json};
        const nodePositions = {node_positions_json};
        const subcategoryColors = {subcategory_colors_json};
        
        // State
        let selected = [];
        let currentSelection = null;
        let affectedNeighbors = [];
        let iteration = 0;
        const maxIterations = {num_products};
        const maxWeight = {max_weight:.2f};
        
        // Priority list
        let priorityList = {priority_dict_json};
        const originalPriorityList = JSON.parse(JSON.stringify(priorityList));
        
        // Canvas setup
        const canvas = document.getElementById('graph-canvas');
        const ctx = canvas.getContext('2d');
        let width = canvas.offsetWidth;
        let height = canvas.offsetHeight;
        canvas.width = width;
        canvas.height = height;
        
        // Scale and translate for layout
        const margin = 50;
        let scale = 1;
        let translateX = 0;
        let translateY = 0;
        
        // Calculate bounds
        let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
        nodesData.forEach(node => {{
            minX = Math.min(minX, node.x);
            maxX = Math.max(maxX, node.x);
            minY = Math.min(minY, node.y);
            maxY = Math.max(maxY, node.y);
        }});
        
        const rangeX = maxX - minX || 1;
        const rangeY = maxY - minY || 1;
        scale = Math.min((width - 2*margin) / rangeX, (height - 2*margin) / rangeY);
        translateX = (width - (maxX + minX) * scale) / 2;
        translateY = (height - (maxY + minY) * scale) / 2;
        
        // Transform coordinates
        function transformX(x) {{
            return x * scale + translateX;
        }}
        
        function transformY(y) {{
            return y * scale + translateY;
        }}
        
        // Draw graph
        function drawGraph() {{
            ctx.clearRect(0, 0, width, height);
            
            // Draw edges (only show edges connected to current selection for performance)
            if (currentSelection) {{
                edgesData.forEach(edge => {{
                    const isCurrentEdge = edge.source === currentSelection || edge.target === currentSelection;
                    if (isCurrentEdge) {{
                        const sourceNode = nodesData.find(n => n.id === edge.source);
                        const targetNode = nodesData.find(n => n.id === edge.target);
                        if (sourceNode && targetNode) {{
                            const x1 = transformX(sourceNode.x);
                            const y1 = transformY(sourceNode.y);
                            const x2 = transformX(targetNode.x);
                            const y2 = transformY(targetNode.y);
                            
                            ctx.strokeStyle = '#F59E0B';
                            ctx.lineWidth = Math.max(1, (edge.weight / maxWeight) * 3);
                            ctx.globalAlpha = 0.6;
                            ctx.beginPath();
                            ctx.moveTo(x1, y1);
                            ctx.lineTo(x2, y2);
                            ctx.stroke();
                        }}
                    }}
                }});
            }}
            
            // Draw nodes
            nodesData.forEach(node => {{
                const x = transformX(node.x);
                const y = transformY(node.y);
                const prio = priorityList[node.id] || 0;
                
                let nodeColor = node.color;
                let nodeSize = 4 + (prio / 100) * 3;
                let borderColor = node.color;
                let borderWidth = 1;
                
                if (node.id === currentSelection) {{
                    nodeColor = '#10B981';
                    nodeSize = 12;
                    borderColor = '#059669';
                    borderWidth = 2;
                }} else if (selected.includes(node.id)) {{
                    nodeSize = 8;
                    borderColor = '#374151';
                    borderWidth = 2;
                }} else if (affectedNeighbors.includes(node.id)) {{
                    nodeSize = 10;
                    borderColor = '#F59E0B';
                    borderWidth = 2;
                }}
                
                // Draw node
                ctx.fillStyle = nodeColor;
                ctx.strokeStyle = borderColor;
                ctx.lineWidth = borderWidth;
                ctx.globalAlpha = 0.9;
                ctx.beginPath();
                ctx.arc(x, y, nodeSize, 0, 2 * Math.PI);
                ctx.fill();
                ctx.stroke();
            }});
            
            // Draw labels for important nodes only
            const importantNodes = [currentSelection, ...selected.slice(-5), ...affectedNeighbors.slice(0, 5)].filter(Boolean);
            importantNodes.forEach(nodeId => {{
                const node = nodesData.find(n => n.id === nodeId);
                if (node) {{
                    const x = transformX(node.x);
                    const y = transformY(node.y);
                    
                    ctx.fillStyle = '#1F2937';
                    ctx.font = 'bold 10px sans-serif';
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    ctx.globalAlpha = 0.9;
                    ctx.fillText(node.label, x, y - 15);
                }}
            }});
        }}
        
        // Update stats panel
        function updateStatsPanel() {{
            document.getElementById('progress').textContent = `${{iteration}} / ${{maxIterations}}`;
            const progressPercent = (iteration / maxIterations) * 100;
            document.getElementById('progressBar').style.width = `${{progressPercent}}%`;
            
            const currentDiv = document.getElementById('currentSelection');
            if (currentSelection) {{
                const node = nodesData.find(n => n.id === currentSelection);
                const subcategory = node.subcategory || 'Unknown';
                const color = subcategoryColors[subcategory] || '#808080';
                currentDiv.innerHTML = `
                    <div class="stat-card current">
                        <div class="stat-label">Now Selecting</div>
                        <div class="product-name">${{node.name}}</div>
                        <div class="product-category" style="color: ${{color}}">${{subcategory}}</div>
                    </div>
                `;
            }} else {{
                currentDiv.innerHTML = '';
            }}
            
            const affectedDiv = document.getElementById('affectedNeighbors');
            if (affectedNeighbors.length > 0) {{
                let html = '<div class="stat-card"><div class="stat-label">Affected Neighbors</div><ul class="affected-list">';
                affectedNeighbors.slice(0, 8).forEach(neighborId => {{
                    const node = nodesData.find(n => n.id === neighborId);
                    if (node) {{
                        const oldPrio = originalPriorityList[neighborId] || 0;
                        const newPrio = priorityList[neighborId] || 0;
                        const reduction = oldPrio > 0 ? ((oldPrio - newPrio) / oldPrio * 100).toFixed(0) : 0;
                        html += `<li class="affected-item">${{node.label}}<br><small>${{oldPrio.toLocaleString()}} → ${{newPrio.toLocaleString()}} (-${{reduction}}%)</small></li>`;
                    }}
                }});
                if (affectedNeighbors.length > 8) {{
                    html += `<li style="font-size: 11px; color: #6B7280; font-style: italic;">... and ${{affectedNeighbors.length - 8}} more</li>`;
                }}
                html += '</ul></div>';
                affectedDiv.innerHTML = html;
            }} else {{
                affectedDiv.innerHTML = '';
            }}
            
            const selectedDiv = document.getElementById('selectedProducts');
            if (selected.length > 0) {{
                let html = '<div class="stat-card"><div class="stat-label">Selected Products</div><ul class="selected-list">';
                selected.slice(-10).forEach((prodId, idx) => {{
                    const node = nodesData.find(n => n.id === prodId);
                    if (node) {{
                        const num = selected.length - 10 + idx + 1;
                        const isCurrent = prodId === currentSelection;
                        html += `<li class="selected-item ${{isCurrent ? 'current' : ''}}">${{num}}. ${{node.label}}</li>`;
                    }}
                }});
                if (selected.length > 10) {{
                    html += `<li style="font-size: 11px; color: #6B7280; font-style: italic;">... ${{selected.length - 10}} more above</li>`;
                }}
                html += '</ul></div>';
                selectedDiv.innerHTML = html;
            }} else {{
                selectedDiv.innerHTML = '';
            }}
            
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
            edgesData.forEach(edge => {{
                if (edge.source === highestId) neighbors.push(edge.target);
                if (edge.target === highestId) neighbors.push(edge.source);
            }});
            
            // Reduce neighbor priorities
            affectedNeighbors = [];
            neighbors.forEach(neighborId => {{
                if (priorityList[neighborId] !== undefined) {{
                    const oldPrio = priorityList[neighborId];
                    const edge = edgesData.find(e => 
                        (e.source === highestId && e.target === neighborId) ||
                        (e.target === highestId && e.source === neighborId)
                    );
                    const weight = edge ? edge.weight : 0;
                    
                    const reductionFactor = Math.min(weight / maxWeight, 0.65);
                    const newPrio = Math.max(1, Math.floor(oldPrio * (1 - reductionFactor)));
                    
                    if (oldPrio !== newPrio) {{
                        priorityList[neighborId] = newPrio;
                        affectedNeighbors.push(neighborId);
                    }}
                }}
            }});
            
            selected.push(highestId);
            currentSelection = highestId;
            iteration++;
            delete priorityList[highestId];
            
            drawGraph();
            updateStatsPanel();
        }}
        
        // Reset
        function reset() {{
            selected = [];
            currentSelection = null;
            affectedNeighbors = [];
            iteration = 0;
            priorityList = JSON.parse(JSON.stringify(originalPriorityList));
            drawGraph();
            updateStatsPanel();
        }}
        
        // Handle window resize
        window.addEventListener('resize', () => {{
            width = canvas.offsetWidth;
            height = canvas.offsetHeight;
            canvas.width = width;
            canvas.height = height;
            scale = Math.min((width - 2*margin) / rangeX, (height - 2*margin) / rangeY);
            translateX = (width - (maxX + minX) * scale) / 2;
            translateY = (height - (maxY + minY) * scale) / 2;
            drawGraph();
        }});
        
        // Initial draw
        drawGraph();
        updateStatsPanel();
    </script>
</body>
</html>"""
    
    # Write HTML file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✓ Optimized HTML visualization saved to {output_file}")
    return output_file


if __name__ == "__main__":
    print("=" * 70)
    print("GENERATING OPTIMIZED HTML INTERACTIVE SELECTION VISUALIZATION")
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
    
    print("\nGenerating optimized HTML visualization...")
    output_file = generate_html_visualization(G, priority_list, num_products=15)
    
    print("\n" + "=" * 70)
    print(f"✓ Complete! Open {output_file} in your browser")
    print("=" * 70)

