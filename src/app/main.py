# app.py
from flask import Flask, request, render_template, redirect, url_for, flash, current_app
import json
from .utils.converter import convert_hosts_to_graph

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = "troque_essa_chave_em_producao"
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", nodes_json="[]", edges_json="[]", filename=None)

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")
    if not file:
        flash("Nenhum arquivo enviado.", "error")
        return redirect(url_for("index"))

    try:
        data = json.load(file)
    except Exception as e:
        flash(f"Erro ao parsear JSON: {e}", "error")
        current_app.logger.exception("Erro ao parsear JSON no upload")
        return redirect(url_for("index"))

    hosts = []
    if isinstance(data, list):
        hosts = data
    elif isinstance(data, dict):
        candidates = [v for v in data.values() if isinstance(v, list)]
        if len(candidates) == 1:
            hosts = candidates[0]
        else:
            hosts = data.get("hosts") or data.get("results") or data.get("items") or data.get("network") or candidates[0] or []

    nodes, edges = convert_hosts_to_graph(hosts)
    node_count = len(nodes)
    edge_count = len(edges)

    current_app.logger.info(f"[UPLOAD] file={getattr(file, 'filename', None)} hosts_found={len(hosts)} nodes={node_count} edges={edge_count}")

    if node_count == 0:
        flash("Upload processado, porém nenhum nó foi gerado. Verifique o formato do JSON (veja logs do servidor).", "warning")
    else:
        flash(f"Upload OK — nodes: {node_count}, edges: {edge_count}", "success")

    return render_template(
        "index.html",
        nodes_json=nodes,
        edges_json=edges,
        filename=getattr(file, "filename", None),
        node_count=node_count,
        edge_count=edge_count
    )

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)
