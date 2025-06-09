(function () {
  "use strict";

  /* ─── helpers ─── */
  function parseEdgeList() {
    const uniq = new Set(), edges = [];
    document.getElementById("edge-list")
      .value.split(/\r?\n/)
      .map(l => l.trim())
      .filter(Boolean)
      .forEach(l => {
        const [a, b] = l.split(/\s+/).map(Number);
        if (!Number.isInteger(a) || !Number.isInteger(b) || a === b) return;
        const [u, v] = a < b ? [a, b] : [b, a];
        const str = `${u} ${v}`;
        if (!uniq.has(str)) { uniq.add(str); edges.push(str); }
      });
    return edges;
  }

  function drawGraph(edges, weights = []) {
    fetch("/plot", {
      method : "POST",
      headers: {"Content-Type": "application/json"},
      body   : JSON.stringify({edges, weights})
    })
    .then(r => r.json())
    .then(({img}) => {
      document.getElementById("graph-area").innerHTML =
        `<img src="${img}" alt="graph">`;
    });
  }

  /* random G(n,p) */
  function randomExample() {
    const n = Math.max(2, parseInt(document.getElementById("num-vertices").value, 10) || 6);
    const p = Math.min(1, Math.max(0, parseFloat(document.getElementById("edge-prob").value) || 0.3));

    const edges = [];
    for (let u = 0; u < n; u++) {
      for (let v = u + 1; v < n; v++) {
        if (Math.random() < p) edges.push([u, v]);
      }
    }
    if (edges.length === 0) {                     // ensure non-empty
      for (let v = 1; v < n; v++) edges.push([Math.floor(Math.random() * v), v]);
    }
    document.getElementById("edge-list").value = edges.map(e => e.join(" ")).join("\n");
    drawGraph(edges);
  }

  /* ─── DOM wiring ─── */
  document.addEventListener("DOMContentLoaded", () => {

    /* Preview */
    document.getElementById("btn-preview").onclick = () => {
      drawGraph(parseEdgeList());
    };

    /* Run */
    document.getElementById("btn-run").onclick = () => {
      const edges = parseEdgeList();
      fetch("/solve", {
        method : "POST",
        headers: {"Content-Type": "application/json"},
        body   : JSON.stringify({edges})
      })
      .then(r => r.json())
      .then(({weights, log}) => {
        drawGraph(edges, weights);
        document.getElementById("log-area").textContent = log || "(no output)";
      });
    };

    /* Random */
    document.getElementById("btn-random").onclick = randomExample;
  });
})();
