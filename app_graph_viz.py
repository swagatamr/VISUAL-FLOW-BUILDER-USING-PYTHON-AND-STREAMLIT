import json
import streamlit as st
from graphviz import Digraph

st.set_page_config(page_title="Flow / Graph Builder", layout="wide")

st.title("Flow / Graph Builder")

# ---------- SESSION STATE SETUP ----------
if "nodes" not in st.session_state:
    # each node: {"id": "A", "label": "Raw materials"}
    st.session_state.nodes = []

if "edges" not in st.session_state:
    # each edge: {"source": "A", "target": "B", "label": "step 1"}
    st.session_state.edges = []


# ---------- HELPER FUNCTIONS ----------
def get_node_ids():
    return [n["id"] for n in st.session_state.nodes]


def build_adjacency_list():
    adj = {n["id"]: [] for n in st.session_state.nodes}
    for e in st.session_state.edges:
        adj[e["source"]].append(e["target"])
    return adj


def build_graphviz():
    dot = Digraph(format="png")
    dot.attr(rankdir="TB", fontsize="10", nodesep="0.4", ranksep="0.6")

    # Add nodes
    for n in st.session_state.nodes:
        dot.node(n["id"], label=n["label"])

    # Add edges
    for e in st.session_state.edges:
        if e.get("label"):
            dot.edge(e["source"], e["target"], label=e["label"])
        else:
            dot.edge(e["source"], e["target"])

    return dot


# ---------- LAYOUT ----------
col_left, col_right = st.columns([1, 2])

with col_left:
    st.subheader("Node editor")

    st.markdown("#### Add / Update node")
    node_id = st.text_input("Node ID (unique, short)", placeholder="e.g. N1")
    node_label = st.text_input("Node label", placeholder="e.g. RAW MATERIALS")

    col_n1, col_n2 = st.columns(2)
    with col_n1:
        if st.button("Add / Update node"):
            if node_id.strip() == "":
                st.warning("Node ID cannot be empty.")
            else:
                # if node exists, update label; else add new
                existing = [n for n in st.session_state.nodes if n["id"] == node_id]
                if existing:
                    existing[0]["label"] = node_label or node_id
                else:
                    st.session_state.nodes.append(
                        {"id": node_id, "label": node_label or node_id}
                    )

    with col_n2:
        if st.button("Delete node"):
            if node_id.strip() == "":
                st.warning("Enter a node ID to delete.")
            else:
                st.session_state.nodes = [
                    n for n in st.session_state.nodes if n["id"] != node_id
                ]
                # also delete edges using this node
                st.session_state.edges = [
                    e
                    for e in st.session_state.edges
                    if e["source"] != node_id and e["target"] != node_id
                ]

    st.markdown("---")
    st.subheader("Edge editor")

    node_ids = get_node_ids()
    if len(node_ids) < 2:
        st.info("Add at least two nodes to create edges.")
    else:
        src = st.selectbox("Source", node_ids, key="src")
        dst = st.selectbox("Target", node_ids, key="dst")
        edge_label = st.text_input(
            "Edge label (optional)", placeholder="e.g. MIXING, TESTING..."
        )

        col_e1, col_e2 = st.columns(2)
        with col_e1:
            if st.button("Add edge"):
                st.session_state.edges.append(
                    {"source": src, "target": dst, "label": edge_label}
                )

        with col_e2:
            if st.button("Clear all edges"):
                st.session_state.edges = []

    st.markdown("---")
    st.subheader("Import / Export")

    # Download JSON
    graph_data = {
        "nodes": st.session_state.nodes,
        "edges": st.session_state.edges,
        "adjacency_list": build_adjacency_list(),
    }
    json_str = json.dumps(graph_data, indent=2)

    st.download_button(
        "⬇️ Download graph as JSON",
        data=json_str,
        file_name="graph_structure.json",
        mime="application/json",
    )

    # Upload JSON
    uploaded = st.file_uploader("⬆️ Load graph JSON", type=["json"])
    if uploaded is not None:
        try:
            data = json.load(uploaded)
            st.session_state.nodes = data.get("nodes", [])
            st.session_state.edges = data.get("edges", [])
            st.success("Graph loaded from JSON.")
        except Exception as e:
            st.error(f"Could not parse JSON: {e}")


with col_right:
    st.subheader("Graph preview")

    if st.session_state.nodes:
        dot = build_graphviz()
        st.graphviz_chart(dot)

        st.markdown("#### Adjacency list (Python dict)")
        st.code(build_adjacency_list(), language="python")

        st.markdown("#### Raw JSON")
        st.code(json_str, language="json")
    else:
        st.info("Add some nodes to see the graph.")


