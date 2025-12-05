# app_graph_visual_diagram_builder.py

import json
from typing import List, Dict

import streamlit as st
from graphviz import Digraph

st.set_page_config(page_title="Graph / Flow Visual Builder", layout="wide")
st.title("📈 Graph / Flow Visual Builder")

st.caption("Add rectangular nodes with labels, connect them with edges, export as JSON + adjacency list.")


# -------------------------------------------------------------------
# SESSION STATE
# -------------------------------------------------------------------
if "nodes" not in st.session_state:
    # nodes: [{"id": "N1", "label": "Start"}, ...]
    st.session_state.nodes: List[Dict] = []

if "edges" not in st.session_state:
    # edges: [{"source": "N1", "target": "N2", "direction": "directed", "label": ""}, ...]
    st.session_state.edges: List[Dict] = []


# -------------------------------------------------------------------
# HELPERS
# -------------------------------------------------------------------
def next_node_id() -> str:
    return f"N{len(st.session_state.nodes) + 1}"


def get_node_ids() -> List[str]:
    return [n["id"] for n in st.session_state.nodes]


def build_adjacency_list() -> Dict[str, List[str]]:
    adj: Dict[str, List[str]] = {n["id"]: [] for n in st.session_state.nodes}
    for e in st.session_state.edges:
        s, t, d = e["source"], e["target"], e["direction"]
        # directed: s -> t
        if d in ("directed", "bidirected", "undirected"):
            adj[s].append(t)
        # bidirected & undirected also have t -> s
        if d in ("bidirected", "undirected"):
            adj[t].append(s)
    return adj


def build_graphviz() -> Digraph:
    dot = Digraph(format="png")
    dot.attr(rankdir="TB", fontsize="10", nodesep="0.4", ranksep="0.6")
    dot.attr("node", shape="box")  # rectangular nodes

    # nodes
    for n in st.session_state.nodes:
        dot.node(n["id"], label=n["label"] or n["id"])

    # edges
    for e in st.session_state.edges:
        attrs = {}
        if e["direction"] == "bidirected":
            attrs["dir"] = "both"
        elif e["direction"] == "undirected":
            attrs["dir"] = "none"

        if e["label"]:
            dot.edge(e["source"], e["target"], label=e["label"], **attrs)
        else:
            dot.edge(e["source"], e["target"], **attrs)

    return dot


# -------------------------------------------------------------------
# LAYOUT
# -------------------------------------------------------------------
left_col, right_col = st.columns([1, 2])

# ===================== LEFT: NODES & EDGES FORMS ====================
with left_col:
    st.subheader("🧱 Nodes")

    # Add node button
    if st.button("➕ Add node", use_container_width=True):
        st.session_state.nodes.append({"id": next_node_id(), "label": ""})

    if not st.session_state.nodes:
        st.info("Click **Add node** to create your first rectangular node.")
    else:
        # Show each node as a text box (rectangle with label)
        new_labels = {}
        for node in st.session_state.nodes:
            key = f"node_label_{node['id']}"
            new_label = st.text_input(
                f"Node {node['id']}",
                value=node["label"],
                key=key,
                placeholder="Type node text here (this is inside the rectangle)",
            )
            new_labels[node["id"]] = new_label

        # Apply label updates
        for node in st.session_state.nodes:
            node["label"] = new_labels[node["id"]]

        # Node delete
        node_ids = get_node_ids()
        del_id = st.selectbox(
            "Delete node (optional)",
            options=["-- none --"] + node_ids,
            index=0,
        )
        if del_id != "-- none --" and st.button("🗑️ Delete selected node", use_container_width=True):
            st.session_state.nodes = [n for n in st.session_state.nodes if n["id"] != del_id]
            st.session_state.edges = [
                e
                for e in st.session_state.edges
                if e["source"] != del_id and e["target"] != del_id
            ]
            st.experimental_rerun()

    st.markdown("---")
    st.subheader("🔗 Edges")

    node_ids = get_node_ids()
    if len(node_ids) < 2:
        st.info("Create at least **2 nodes** to add edges.")
    else:
        src = st.selectbox("Source node", node_ids, key="edge_src")
        dst = st.selectbox("Target node", node_ids, key="edge_dst")
        direction = st.selectbox(
            "Edge type",
            ["directed", "bidirected", "undirected"],
            help="directed: A → B, bidirected: A ⇄ B, undirected: A — B",
        )
        edge_label = st.text_input("Edge label (optional)", key="edge_label")

        if st.button("➕ Add edge", use_container_width=True):
            if src == dst:
                st.warning("Source and target must be different.")
            else:
                st.session_state.edges.append(
                    {
                        "source": src,
                        "target": dst,
                        "direction": direction,
                        "label": edge_label,
                    }
                )

        if st.session_state.edges:
            if st.button("🧹 Clear all edges", use_container_width=True):
                st.session_state.edges = []

    st.markdown("---")
    st.subheader("📦 Export / Import")

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
        use_container_width=True,
    )

    uploaded = st.file_uploader("⬆️ Load graph JSON", type=["json"])
    if uploaded is not None:
        try:
            data = json.load(uploaded)
            st.session_state.nodes = data.get("nodes", [])
            st.session_state.edges = data.get("edges", [])
            st.success("Graph loaded from JSON.")
        except Exception as e:
            st.error(f"Could not parse JSON: {e}")


# ========================= RIGHT: GRAPH VIEW ========================
with right_col:
    st.subheader("📊 Graph preview")

    if st.session_state.nodes:
        dot = build_graphviz()
        st.graphviz_chart(dot)

        st.markdown("#### Adjacency list")
        st.code(build_adjacency_list(), language="python")

        st.markdown("#### Raw JSON")
        st.code(json_str, language="json")
    else:
        st.info("No nodes yet. Use the left panel to add nodes and edges.")
