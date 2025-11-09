"""
Generate fast HTML-based interactive product selection visualization.
Uses pure canvas rendering (no heavy libraries) for maximum performance.
"""
import networkx as nx
import json
from src.core.main import setup_graph, create_priority_list_from_sales
from src.core.models import IndexedPriorityList
from src.core.subcategory_colors import get_subcategory_color, create_subcategory_colormap


def generate_html_visualization(G: nx.DiGraph, priority_list: IndexedPriorityList, 
                                num_products: int = 15, output_file: str = 'output/interactive/interactive_selection.html'):
    """Generate a fast HTML file with interactive product selection visualization."""
    
    # Calculate max weight
    max_weight = 0.0
    for u, v, data in G.edges(data=True):
        weight = data.get('weight', 0.0)
        if weight > max_weight:
            max_weight = weight
    
    # Create subcategory colormap
    subcategory_colors = create_subcategory_colormap(G)
    product_names = {node: G.nodes[node].get('name', node) for node in G.nodes()}
    
    # Create layout - faster with fewer iterations
    print("Calculating layout...")
    for u, v in G.edges():
        w = G[u][v].get('weight', 1)
        G[u][v]['spring_weight'] = w
    
    pos = nx.spring_layout(G, k=1.0, iterations=50, weight='spring_weight', 
                          seed=42, scale=3, threshold=1e-4)
    print("✓ Layout calculated")
    
    # Prepare compact nodes data
    nodes_data = []
    for node_id in G.nodes():
        subcategory = G.nodes[node_id].get('subcategory', 'Unknown')
        color = get_subcategory_color(subcategory)
        name = product_names[node_id]
        prio = 0
        for nid, val in priority_list._items:
            if nid == node_id:
                prio = val
                break
        
        nodes_data.append({
            'i': node_id,
            'n': name[:20] + '...' if len(name) > 20 else name,
            'f': name,  # full name
            's': subcategory,
            'c': color,
            'p': prio,
            'x': pos[node_id][0],
            'y': pos[node_id][1]
        })
    
    # Prepare compact edges data - only store essential info
    edges_data = []
    for u, v, data in G.edges(data=True):
        weight = data.get('weight', 0.0)
        edges_data.append([u, v, weight])  # Compact format
    
    # Convert priority list to dict
    priority_dict = {nid: val for nid, val in priority_list._items}
    
    # Convert to JSON strings (minified)
    nodes_json = json.dumps(nodes_data, separators=(',', ':'))
    edges_json = json.dumps(edges_data, separators=(',', ':'))
    priority_dict_json = json.dumps(priority_dict, separators=(',', ':'))
    subcategory_colors_json = json.dumps(subcategory_colors, separators=(',', ':'))
    
    # Generate optimized HTML with pure canvas
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <title>Interactive Product Selection</title>
    <style>
        *{{margin:0;padding:0;box-sizing:border-box}}
        body{{
            font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;
            background:#F8F9FA;
            color:#1F2937;
            overflow:hidden
        }}
        .container{{
            display:flex;
            height:100vh;
            gap:20px;
            padding:20px
        }}
        .graph-panel{{
            flex:1;
            background:white;
            border-radius:8px;
            box-shadow:0 1px 3px rgba(0,0,0,0.1);
            padding:20px;
            display:flex;
            flex-direction:column
        }}
        .stats-panel{{
            width:380px;
            background:white;
            border-radius:8px;
            box-shadow:0 1px 3px rgba(0,0,0,0.1);
            padding:20px;
            overflow-y:auto
        }}
        #graph-canvas{{
            flex:1;
            border:1px solid #E5E7EB;
            border-radius:4px;
            cursor:move
        }}
        h1{{
            margin:0 0 15px 0;
            font-size:22px;
            font-weight:600;
            color:#111827
        }}
        h2{{
            margin:0 0 15px 0;
            font-size:16px;
            font-weight:600;
            color:#374151
        }}
        .controls{{
            margin-bottom:15px;
            display:flex;
            gap:10px
        }}
        button{{
            padding:10px 20px;
            font-size:14px;
            font-weight:600;
            border:none;
            border-radius:6px;
            cursor:pointer;
            transition:all 0.2s
        }}
        .btn-primary{{
            background:#2563EB;
            color:white
        }}
        .btn-primary:hover:not(:disabled){{
            background:#1D4ED8
        }}
        .btn-secondary{{
            background:#64748B;
            color:white
        }}
        .btn-secondary:hover{{
            background:#475569
        }}
        .btn-primary:disabled{{
            background:#CBD5E1;
            cursor:not-allowed
        }}
        .stat-card{{
            background:#F9FAFB;
            border:1px solid #E5E7EB;
            border-radius:6px;
            padding:15px;
            margin-bottom:15px
        }}
        .stat-card.current{{
            background:#ECFDF5;
            border:2px solid #10B981
        }}
        .stat-label{{
            font-size:11px;
            font-weight:600;
            color:#6B7280;
            text-transform:uppercase;
            letter-spacing:0.5px;
            margin-bottom:8px
        }}
        .stat-value{{
            font-size:18px;
            font-weight:600;
            color:#111827
        }}
        .product-name{{
            font-size:14px;
            font-weight:600;
            color:#111827;
            margin:5px 0
        }}
        .product-category{{
            font-size:12px;
            color:#6B7280;
            font-style:italic
        }}
        .affected-list,.selected-list{{
            list-style:none;
            padding:0;
            margin:10px 0
        }}
        .affected-item,.selected-item{{
            padding:8px;
            margin:5px 0;
            background:#FFF7ED;
            border-left:3px solid #F59E0B;
            border-radius:4px;
            font-size:12px;
            word-wrap:break-word;
            overflow-wrap:break-word
        }}
        .selected-item{{
            background:#F9FAFB;
            border-color:#3B82F6
        }}
        .selected-item.current{{
            background:#ECFDF5;
            border-color:#10B981
        }}
        .progress-bar{{
            width:100%;
            height:8px;
            background:#E5E7EB;
            border-radius:4px;
            overflow:hidden;
            margin:10px 0
        }}
        .progress-fill{{
            height:100%;
            background:#2563EB;
            transition:width 0.3s
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
                    <div class="progress-fill" id="progressBar" style="width:0%"></div>
                </div>
            </div>
            <div id="currentSelection"></div>
            <div id="affectedNeighbors"></div>
            <div id="selectedProducts"></div>
        </div>
    </div>

    <script>
        // Data (compact format)
        const nodes={nodes_json};
        const edges={edges_json};
        const subcategoryColors={subcategory_colors_json};
        
        // State
        let selected=[];
        let currentSelection=null;
        let affectedNeighbors=[];
        let iteration=0;
        const maxIterations={num_products};
        const maxWeight={max_weight:.2f};
        
        // Priority list
        let priorityList={priority_dict_json};
        const originalPriorityList=JSON.parse(JSON.stringify(priorityList));
        
        // Calculate max priority for normalization (use original list)
        let maxPrio=0;
        for(const prio of Object.values(originalPriorityList)){{
            if(prio>maxPrio)maxPrio=prio;
        }}
        const minPrio=0;
        const prioRange=maxPrio-minPrio||1;
        
        // Node lookup map
        const nodeMap={{}};
        nodes.forEach(n=>{{nodeMap[n.i]=n}});
        
        // Canvas setup
        const canvas=document.getElementById('graph-canvas');
        const ctx=canvas.getContext('2d');
        let width=canvas.offsetWidth;
        let height=canvas.offsetHeight;
        canvas.width=width;
        canvas.height=height;
        
        // Calculate transform
        const margin=50;
        let minX=Infinity,maxX=-Infinity,minY=Infinity,maxY=-Infinity;
        nodes.forEach(n=>{{
            minX=Math.min(minX,n.x);
            maxX=Math.max(maxX,n.x);
            minY=Math.min(minY,n.y);
            maxY=Math.max(maxY,n.y);
        }});
        const rangeX=maxX-minX||1;
        const rangeY=maxY-minY||1;
        let baseScale=Math.min((width-2*margin)/rangeX,(height-2*margin)/rangeY);
        let zoomLevel=1;
        let panX=0;
        let panY=0;
        let scale=baseScale*zoomLevel;
        let translateX=(width-(maxX+minX)*scale)/2+panX;
        let translateY=(height-(maxY+minY)*scale)/2+panY;
        
        function transformX(x){{return x*scale+translateX}}
        function transformY(y){{return y*scale+translateY}}
        
        // Zoom and pan state
        let isDragging=false;
        let lastMouseX=0;
        let lastMouseY=0;
        
        // Draw graph (optimized)
        function drawGraph(){{
            ctx.clearRect(0,0,width,height);
            
            // Only draw edges connected to current selection (for performance)
            if(currentSelection){{
                edges.forEach(e=>{{
                    const [u,v,w]=e;
                    if(u===currentSelection||v===currentSelection){{
                        const n1=nodeMap[u];
                        const n2=nodeMap[v];
                        if(n1&&n2){{
                            const x1=transformX(n1.x);
                            const y1=transformY(n1.y);
                            const x2=transformX(n2.x);
                            const y2=transformY(n2.y);
                            
                            // Draw edge
                            ctx.strokeStyle='#F59E0B';
                            ctx.lineWidth=Math.max(1,(w/maxWeight)*3);
                            ctx.globalAlpha=0.6;
                            ctx.beginPath();
                            ctx.moveTo(x1,y1);
                            ctx.lineTo(x2,y2);
                            ctx.stroke();
                            
                            // Draw weight label on edge
                            const midX=(x1+x2)/2;
                            const midY=(y1+y2)/2;
                            ctx.fillStyle='#1F2937';
                            ctx.font='bold 11px sans-serif';
                            ctx.textAlign='center';
                            ctx.textBaseline='middle';
                            ctx.globalAlpha=0.9;
                            // Draw background for text
                            const text=w.toFixed(1);
                            const textWidth=ctx.measureText(text).width;
                            ctx.fillStyle='rgba(255,255,255,0.9)';
                            ctx.fillRect(midX-textWidth/2-3,midY-8,textWidth+6,16);
                            ctx.fillStyle='#1F2937';
                            ctx.fillText(text,midX,midY);
                        }}
                    }}
                }});
            }}
            
            // Draw nodes
            nodes.forEach(node=>{{
                const x=transformX(node.x);
                const y=transformY(node.y);
                const prio=priorityList[node.i]||0;
                
                let nodeColor=node.c;
                // Normalize node size: use logarithmic scaling to prevent huge nodes
                // Normal nodes: 3-7 pixels based on priority
                const normalizedPrio=Math.log10(prio+1)/Math.log10(maxPrio+1); // 0-1 range
                let nodeSize=3+normalizedPrio*4; // 3-7 pixels
                let borderColor=node.c;
                let borderWidth=1;
                
                if(node.i===currentSelection){{
                    nodeColor='#10B981';
                    nodeSize=12; // Fixed size for current selection
                    borderColor='#059669';
                    borderWidth=2;
                }}else if(selected.includes(node.i)){{
                    nodeSize=8; // Fixed size for selected
                    borderColor='#374151';
                    borderWidth=2;
                }}else if(affectedNeighbors.some(n=>n.id===node.i)){{
                    nodeSize=9; // Fixed size for affected
                    borderColor='#F59E0B';
                    borderWidth=2;
                }}
                
                ctx.fillStyle=nodeColor;
                ctx.strokeStyle=borderColor;
                ctx.lineWidth=borderWidth;
                ctx.globalAlpha=0.9;
                ctx.beginPath();
                ctx.arc(x,y,nodeSize,0,2*Math.PI);
                ctx.fill();
                ctx.stroke();
            }});
            
            // Draw labels for important nodes only
            const affectedIds=affectedNeighbors.map(n=>n.id);
            const important=[currentSelection,...selected.slice(-5),...affectedIds].filter(Boolean);
            important.forEach(nodeId=>{{
                const node=nodeMap[nodeId];
                if(node){{
                    const x=transformX(node.x);
                    const y=transformY(node.y);
                    ctx.fillStyle='#1F2937';
                    ctx.font='bold 10px sans-serif';
                    ctx.textAlign='center';
                    ctx.textBaseline='middle';
                    ctx.globalAlpha=0.9;
                    ctx.fillText(node.n,x,y-15);
                }}
            }});
        }}
        
        // Update stats panel
        function updateStatsPanel(){{
            document.getElementById('progress').textContent=`${{iteration}} / ${{maxIterations}}`;
            document.getElementById('progressBar').style.width=`${{(iteration/maxIterations)*100}}%`;
            
            const currentDiv=document.getElementById('currentSelection');
            if(currentSelection){{
                const node=nodeMap[currentSelection];
                const color=subcategoryColors[node.s]||'#808080';
                currentDiv.innerHTML=`<div class="stat-card current"><div class="stat-label">Now Selecting</div><div class="product-name">${{node.f}}</div><div class="product-category" style="color:${{color}}">${{node.s}}</div></div>`;
            }}else{{currentDiv.innerHTML=''}}
            
            // Show all affected neighbors
            const affectedDiv=document.getElementById('affectedNeighbors');
            if(affectedNeighbors.length>0){{
                let html='<div class="stat-card"><div class="stat-label">Affected Neighbors (${{affectedNeighbors.length}})</div><ul class="affected-list">';
                affectedNeighbors.forEach(neighbor=>{{
                    const node=nodeMap[neighbor.id];
                    if(node){{
                        const reduction=neighbor.oldPrio>0?((neighbor.oldPrio-neighbor.newPrio)/neighbor.oldPrio*100).toFixed(0):0;
                        html+=`<li class="affected-item">${{node.f}}<br><small>${{neighbor.oldPrio.toLocaleString()}} → ${{neighbor.newPrio.toLocaleString()}} (-${{reduction}}%)</small></li>`;
                    }}
                }});
                html+='</ul></div>';
                affectedDiv.innerHTML=html;
            }}else{{affectedDiv.innerHTML=''}}
            
            const selectedDiv=document.getElementById('selectedProducts');
            if(selected.length>0){{
                let html='<div class="stat-card"><div class="stat-label">Selected Products</div><ul class="selected-list">';
                selected.slice(-10).forEach((prodId,idx)=>{{
                    const node=nodeMap[prodId];
                    if(node){{
                        const startNum=Math.max(1,selected.length-9);
                        const num=startNum+idx;
                        const isCurrent=prodId===currentSelection;
                        html+=`<li class="selected-item ${{isCurrent?'current':''}}">${{num}}. ${{node.n}}</li>`;
                    }}
                }});
                if(selected.length>10)html+=`<li style="font-size:11px;color:#6B7280;font-style:italic">... ${{selected.length-10}} more above</li>`;
                html+='</ul></div>';
                selectedDiv.innerHTML=html;
            }}else{{selectedDiv.innerHTML=''}}
            
            document.getElementById('nextBtn').disabled=iteration>=maxIterations||Object.keys(priorityList).length===0;
        }}
        
        // Next selection
        function nextSelection(){{
            if(iteration>=maxIterations||Object.keys(priorityList).length===0)return;
            
            let highestId=null;
            let highestPrio=-1;
            for(const [nodeId,prio] of Object.entries(priorityList)){{
                if(prio>highestPrio){{highestPrio=prio;highestId=nodeId}}
            }}
            if(!highestId)return;
            
            const neighbors=[];
            edges.forEach(e=>{{
                if(e[0]===highestId)neighbors.push(e[1]);
                if(e[1]===highestId)neighbors.push(e[0]);
            }});
            
            affectedNeighbors=[];
            neighbors.forEach(neighborId=>{{
                if(priorityList[neighborId]!==undefined){{
                    const oldPrio=priorityList[neighborId];
                    const edge=edges.find(e=>(e[0]===highestId&&e[1]===neighborId)||(e[1]===highestId&&e[0]===neighborId));
                    const weight=edge?edge[2]:0;
                    const reductionFactor=Math.min(weight/maxWeight,0.65);
                    const newPrio=Math.max(1,Math.floor(oldPrio*(1-reductionFactor)));
                    if(oldPrio!==newPrio){{
                        priorityList[neighborId]=newPrio;
                        affectedNeighbors.push({{id:neighborId,oldPrio:oldPrio,newPrio:newPrio}});
                    }}
                }}
            }});
            
            selected.push(highestId);
            currentSelection=highestId;
            iteration++;
            delete priorityList[highestId];
            
            // Reset zoom and pan to default view
            zoomLevel=1;
            panX=0;
            panY=0;
            scale=baseScale*zoomLevel;
            translateX=(width-(maxX+minX)*scale)/2;
            translateY=(height-(maxY+minY)*scale)/2;
            
            drawGraph();
            updateStatsPanel();
        }}
        
        // Reset
        function reset(){{
            selected=[];
            currentSelection=null;
            affectedNeighbors=[];
            iteration=0;
            priorityList=JSON.parse(JSON.stringify(originalPriorityList));
            // Reset zoom and pan
            zoomLevel=1;
            panX=0;
            panY=0;
            scale=baseScale*zoomLevel;
            translateX=(width-(maxX+minX)*scale)/2+panX;
            translateY=(height-(maxY+minY)*scale)/2+panY;
            drawGraph();
            updateStatsPanel();
        }}
        
        // Zoom functionality
        function updateTransform(){{
            scale=baseScale*zoomLevel;
            translateX=(width-(maxX+minX)*scale)/2+panX;
            translateY=(height-(maxY+minY)*scale)/2+panY;
            drawGraph();
        }}
        
        // Mouse wheel zoom
        canvas.addEventListener('wheel',(e)=>{{
            e.preventDefault();
            const rect=canvas.getBoundingClientRect();
            const mouseX=e.clientX-rect.left;
            const mouseY=e.clientY-rect.top;
            
            // Calculate point in graph coordinates before zoom
            const graphX=(mouseX-translateX)/scale;
            const graphY=(mouseY-translateY)/scale;
            
            // Zoom
            const zoomFactor=e.deltaY>0?0.9:1.1;
            zoomLevel=Math.max(0.1,Math.min(50,zoomLevel*zoomFactor));
            
            // Calculate new transform
            scale=baseScale*zoomLevel;
            const newTranslateX=mouseX-graphX*scale;
            const newTranslateY=mouseY-graphY*scale;
            
            // Adjust pan to zoom towards mouse position
            panX=newTranslateX-(width-(maxX+minX)*scale)/2;
            panY=newTranslateY-(height-(maxY+minY)*scale)/2;
            
            updateTransform();
        }});
        
        // Mouse drag pan
        canvas.addEventListener('mousedown',(e)=>{{
            isDragging=true;
            lastMouseX=e.clientX;
            lastMouseY=e.clientY;
            canvas.style.cursor='grabbing';
        }});
        
        canvas.addEventListener('mousemove',(e)=>{{
            if(isDragging){{
                const deltaX=e.clientX-lastMouseX;
                const deltaY=e.clientY-lastMouseY;
                panX+=deltaX;
                panY+=deltaY;
                lastMouseX=e.clientX;
                lastMouseY=e.clientY;
                updateTransform();
            }}
        }});
        
        canvas.addEventListener('mouseup',()=>{{
            isDragging=false;
            canvas.style.cursor='move';
        }});
        
        canvas.addEventListener('mouseleave',()=>{{
            isDragging=false;
            canvas.style.cursor='move';
        }});
        
        // Handle resize
        window.addEventListener('resize',()=>{{
            width=canvas.offsetWidth;
            height=canvas.offsetHeight;
            canvas.width=width;
            canvas.height=height;
            const newBaseScale=Math.min((width-2*margin)/rangeX,(height-2*margin)/rangeY);
            // Adjust zoom level proportionally
            zoomLevel=(zoomLevel*baseScale)/newBaseScale;
            baseScale=newBaseScale;
            updateTransform();
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
    
    print(f"✓ Fast HTML visualization saved to {output_file}")
    return output_file


if __name__ == "__main__":
    print("=" * 70)
    print("GENERATING FAST HTML INTERACTIVE SELECTION VISUALIZATION")
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
    
    print("\nGenerating fast HTML visualization...")
    output_file = generate_html_visualization(G, priority_list, num_products=15)
    
    print("\n" + "=" * 70)
    print(f"✓ Complete! Open {output_file} in your browser")
    print("=" * 70)

