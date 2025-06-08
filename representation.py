import networkx as nx
import matplotlib.pyplot as plt

# Define the DFA as a directed graph
G = nx.DiGraph()

# Add states as nodes
states = ["q0", "q1", "q2"]
for state in states:
    G.add_node(state)

# Define transitions: (from_state, to_state, symbol)
transitions = [
    ("q0", "q1", "a"),
    ("q0", "q0", "b"),
    ("q1", "q1", "a"),
    ("q1", "q2", "b"),
    ("q2", "q1", "a"),
    ("q2", "q0", "b"),
]

# Add edges with label attribute
for src, dst, sym in transitions:
    if G.has_edge(src, dst):
        # Append symbol if there's already an edge (combine labels)
        existing_label = G[src][dst]["label"]
        G[src][dst]["label"] = f"{existing_label}, {sym}"
    else:
        G.add_edge(src, dst, label=sym)

# Compute a layout for nodes
pos = nx.spring_layout(G)

# Draw nodes
nx.draw_networkx_nodes(G, pos, node_size=1200)

# Highlight the start state with a different marker style
nx.draw_networkx_nodes(G, pos, nodelist=["q0"], node_size=1200, node_color="lightgray")

# Highlight the accept state by a double ring (use larger node size with transparent interior)
nx.draw_networkx_nodes(G, pos, nodelist=["q2"], node_size=1400, node_color="none", edgecolors="black", linewidths=2)

# Draw node labels
nx.draw_networkx_labels(G, pos, font_size=12, font_family="sans-serif")

# Draw edges
nx.draw_networkx_edges(G, pos, arrowstyle="->", arrowsize=20)

# Draw edge labels (transition symbols)
edge_labels = nx.get_edge_attributes(G, "label")
nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=10)

# Remove axes for clarity
plt.axis("off")

# Display the plot
plt.show()
