"""Test script to check connections between selected products."""
from main import setup_graph, generate, create_priority_list_from_sales

# Create graphs
print("Creating graphs...")
G = setup_graph(min_edge_weight=5.0)
G_full = setup_graph(min_edge_weight=0.0)

# Generate selection
priority_list = create_priority_list_from_sales(G)
selected = generate(4, G, priorityList=priority_list)

print("\n" + "="*70)
print("SELECTED PRODUCTS:")
print("="*70)
for i, node_id in enumerate(selected, 1):
    name = G.nodes[node_id].get('name', node_id)
    print(f"{i}. {name} (ID: {node_id})")

print("\n" + "="*70)
print("CONNECTIONS BETWEEN SELECTED PRODUCTS (in filtered graph):")
print("="*70)
found_in_filtered = False
for i, u in enumerate(selected):
    for j, v in enumerate(selected):
        if u != v and G.has_edge(u, v):
            found_in_filtered = True
            u_name = G.nodes[u].get('name', u)
            v_name = G.nodes[v].get('name', v)
            weight = G[u][v]['weight']
            print(f"{u_name} -> {v_name}: weight={weight:.2f}")

if not found_in_filtered:
    print("No connections found (all below threshold 5.0)")

print("\n" + "="*70)
print("CONNECTIONS IN FULL GRAPH (including weak connections):")
print("="*70)
connections = []
for i, u in enumerate(selected):
    for j, v in enumerate(selected):
        if u != v and G_full.has_edge(u, v):
            u_name = G_full.nodes[u].get('name', u)
            v_name = G_full.nodes[v].get('name', v)
            weight = G_full[u][v]['weight']
            connections.append((u_name, v_name, weight))

# Sort by weight descending
connections.sort(key=lambda x: x[2], reverse=True)

if connections:
    for u_name, v_name, weight in connections:
        print(f"{u_name} -> {v_name}: weight={weight:.2f}")
else:
    print("No connections found!")

print("\n" + "="*70)
print(f"Total connections in full graph: {len(connections)}")
print("="*70)
