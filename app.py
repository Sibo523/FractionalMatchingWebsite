import base64
from typing import List, Tuple

from flask import Flask, render_template, request, jsonify
import matplotlib        
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import io, contextlib        

# ---- bring in the algorithm -------------------------------------------------
from algos import minimal_fraction_max_matching
# -----------------------------------------------------------------------------

app = Flask(__name__)
app.secret_key = "replace-me"


# ────────────────────────── helpers ──────────────────────────────────────────
def parse_edges(edge_strings: List[str]) -> Tuple[nx.Graph, int]:
    """
    Build a NetworkX graph from a list like ["0 1", "2 3"].
    Returns (graph, highest_vertex_index + 1)
    """
    g = nx.Graph()
    max_v = -1
    for s in edge_strings:
        u, v = map(int, s.split())
        if u == v:
            continue                   # ignore loops
        g.add_edge(u, v)
        max_v = max(max_v, u, v)
    g.add_nodes_from(range(max_v + 1))
    return g, max_v + 1


# ───────────────── render_png helper ─────────────────────────
def render_png(triplets):
    """
    triplets = [(u, v, w)] where w ∈ {0, 0.5, 1}
    Returns raw PNG bytes.
    """

    G         = nx.Graph()
    colours   = []
    edgelist  = []                          

    for u, v, w in triplets:
        G.add_edge(u, v)
        edgelist.append((u, v))             
        colours.append("red"   if w == 1
                       else "green" if w == 0.5
                       else "black")

    pos = nx.spring_layout(G, seed=42)
    fig, ax = plt.subplots(figsize=(5, 5))

    nx.draw(
        G, pos, ax=ax,
        edgelist=edgelist,                  
        edge_color=colours,
        node_color="#FAFAFA",
        with_labels=True,
        linewidths=2,
        font_size=10,
    )
    ax.set_axis_off()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()
# ─────────────────────────────────────────────────────────────


# ─────────────────────────── routes ──────────────────────────────────────────
@app.get("/")
def index():
    return render_template("index.html")


@app.post("/plot")
def plot_graph():
    """
    JSON →  { "edges": ["0 1", …], "weights": [1, 0.5, 0, …] (optional) }
    Returns → { "img": "data:image/png;base64,…" }
    """
    data    = request.get_json(force=True)
    edges   = data["edges"]
    weights = data.get("weights", [])

    # ── pad / default so len(weights) == len(edges) 
    if len(weights) < len(edges):
        weights = list(weights) + [0.0] * (len(edges) - len(weights))        

    triplets = [
        tuple(map(int, e.split())) + (float(weights[i]),)
        for i, e in enumerate(edges)
    ]
    img_b64 = base64.b64encode(render_png(triplets)).decode()
    return jsonify({"img": f"data:image/png;base64,{img_b64}"})



@app.post("/solve")
def solve():
    data  = request.get_json(force=True)
    edges = data["edges"]
    g, _  = parse_edges(edges)

    buf = io.StringIO()

    # ─── NEW: capture `logging` output as well ───────────────────
    import logging
    temp_handler = logging.StreamHandler(buf)
    temp_handler.setLevel(logging.DEBUG)      # or INFO if you prefer
    logging.getLogger().addHandler(temp_handler)

    try:
        # anything printed *or logged* by the algorithm ends in `buf`
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            match = minimal_fraction_max_matching(g)
    finally:
        logging.getLogger().removeHandler(temp_handler)  # clean-up

    log_txt = buf.getvalue()
    buf.close()

    def w(u, v):
        return match.get((u, v), match.get((v, u), 0.0))

    weights = [w(*map(int, e.split())) for e in edges]
    return jsonify({"weights": weights, "log": log_txt})

# ─────────────────────────────────────────────────────────────────────────────
@app.get("/about")
def about():
    """Simple `About` page."""
    return render_template("about.html")


if __name__ == "__main__":
    app.run(debug=True)
