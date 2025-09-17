(function () {
    "use strict";

    function safeLog(...args) {
        if (window.DEBUG_NETWORK_JS) console.log("[network.js]", ...args);
    }

    function isVisAvailable() {
        return typeof vis !== "undefined" && vis && vis.Network && vis.DataSet;
    }

    function readInitData() {
        const script = document.getElementById("init-data");
        if (script && script.textContent && script.textContent.trim().length) {
            try {
                const parsed = JSON.parse(script.textContent);
                return {
                    nodes: parsed.nodes || [],
                    edges: parsed.edges || [],
                };
            } catch (err) {
                console.error("Erro ao parsear init-data JSON:", err);
            }
        }

        const nodes = Array.isArray(window.INIT_NODES) ? window.INIT_NODES : [];
        const edges = Array.isArray(window.INIT_EDGES) ? window.INIT_EDGES : [];
        return { nodes, edges };
    }

    function ensureElement(id) {
        const el = document.getElementById(id);
        if (!el) {
            console.error(`Elemento #${id} não encontrado no DOM.`);
        }

        return el;
    }

    try {
        const init = readInitData();
        safeLog("INIT_NODES length=", init.nodes.length, "INIT_EDGES length=", init.edges.length);
        if (init.nodes.length > 0) safeLog("Exemplo node:", init.nodes[0]);

        const container = ensureElement("mynetwork");
        if (!container) return;
        const rawEl = ensureElement("raw");
        const searchInput = ensureElement("search");
        const searchBtn = ensureElement("searchBtn");
        const btnForce = ensureElement("btnForce");
        const btnHier = ensureElement("btnHier");
        const btnStar = ensureElement("btnStar");
        const exportPNG = ensureElement("exportPNG");
        const exportJSON = ensureElement("exportJSON");

        const nodesPrepared = (init.nodes || []).map((n) => {
            const copy = Object.assign({}, n);
            copy.id = typeof copy.id === "string" ? copy.id : String(copy.id);
            if (copy.title === undefined || copy.title === null) copy.title = "";
            if (copy.raw === undefined) copy.raw = JSON.stringify(n, null, 2);

            return copy;
        });

        const edgesPrepared = (init.edges || []).map((e) => {
            const copy = Object.assign({}, e);
            if (copy.from === undefined || copy.to === undefined) return null;
            copy.from = typeof copy.from === "string" ? copy.from : String(copy.from);
            copy.to = typeof copy.to === "string" ? copy.to : String(copy.to);
            return copy;
        }).filter(Boolean);

        const data = {
            nodes: new vis.DataSet(nodesPrepared),
            edges: new vis.DataSet(edgesPrepared),
        };

        const options = {
            nodes: {
                shape: "dot",
                scaling: { label: { enabled: true } },
                font: { multi: "html" },
            },
            edges: {
                smooth: false,
                color: { inherit: true },
            },
            physics: {
                stabilization: true,
                barnesHut: { gravitationalConstant: -2000, springConstant: 0.001, springLength: 200 },
            },
            interaction: {
                hover: true,
                multiselect: false,
                tooltipDelay: 100,
            },
            layout: {
                improvedLayout: true,
            },
        };

        const network = new vis.Network(container, data, options);

        const nodeMap = {};
        data.nodes.get().forEach((n) => {
            nodeMap[n.id] = n;
        });

        const groups = {
            linux: { color: "#4DAF4A" },
            windows: { color: "#377EB8" },
            embedded: { color: "#FF7F00" },
            hop: { color: "#999999" },
            other: { color: "#8A2BE2" },
            unknown: { color: "#BBBBBB" },
        };

        Object.keys(groups).forEach((g) => {
            const upd = data.nodes
                .get()
                .filter((n) => n.group === g)
                .map((n) => ({ id: n.id, color: groups[g].color }));
            if (upd.length) data.nodes.update(upd);
        });

        network.on("selectNode", function (params) {
            const id = params.nodes && params.nodes[0];
            if (!id) return;
            const n = nodeMap[id] || data.nodes.get(id);
            if (!n) return;
            if (rawEl) rawEl.textContent = n.raw || JSON.stringify(n, null, 2);
        });

        network.on("deselectNode", function () {
            if (rawEl) rawEl.textContent = "Nenhum nó selecionado.";
        });

        if (searchBtn && searchInput) {
            searchBtn.addEventListener("click", function (e) {
                e.preventDefault();
                const q = searchInput.value.trim().toLowerCase();
                if (!q) return;
                const all = data.nodes.get();
                const found = all.find((n) => ("" + (n.label || "")).toLowerCase().includes(q) || ("" + (n.id || "")).toLowerCase().includes(q));
                if (found) {
                    network.selectNodes([found.id]);
                    network.focus(found.id, { scale: 1.2 });
                } else {
                    alert("Nenhum nó encontrado para: " + q);
                }
            });
        }

        if (btnForce) {
            btnForce.addEventListener("click", function (e) {
                e.preventDefault();
                network.setOptions({ physics: { enabled: true } });
            });
        }

        if (btnHier) {
            btnHier.addEventListener("click", function (e) {
                e.preventDefault();
                network.setOptions({
                    layout: { hierarchical: { enabled: true, direction: "LR", sortMethod: "hubsize" } },
                    physics: { enabled: false },
                });
            });
        }

        if (btnStar) {
            btnStar.addEventListener("click", function (e) {
                e.preventDefault();
                const allIds = data.nodes.get().map((n) => n.id);
                if (!allIds.length) return;
                const center = allIds[0];
                const positions = {};
                const R = 300;
                let i = 0;
                allIds.forEach((id) => {
                    if (id === center) positions[id] = { x: 0, y: 0 };
                    else {
                        positions[id] = { x: Math.cos((i / allIds.length) * 2 * Math.PI) * R, y: Math.sin((i / allIds.length) * 2 * Math.PI) * R };
                        i++;
                    }
                });
                network.setOptions({ physics: { enabled: false } });
                Object.keys(positions).forEach((id) => {
                    try {
                        network.moveNode(id, positions[id].x, positions[id].y);
                    } catch (err) {
                        console.err(err);
                    }
                });
            });
        }

        if (exportPNG) {
            exportPNG.addEventListener("click", function (e) {
                e.preventDefault();

                const canvas = container.querySelector("canvas");
                if (!canvas) return alert("Canvas não encontrado — aguarde a rede estabilizar.");

                const url = canvas.toDataURL();
                const a = document.createElement("a");

                a.href = url;
                a.download = "network_map.png";
                a.click();
            });
        }

        if (exportJSON) {
            exportJSON.addEventListener("click", function (e) {
                e.preventDefault();
                const payload = { nodes: data.nodes.get(), edges: data.edges.get() };
                const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(payload, null, 2));
                const a = document.createElement("a");
                a.setAttribute("href", dataStr);
                a.setAttribute("download", "network_map_data.json");
                a.click();
            });
        }

        safeLog("vis-network initialized successfully.");
    } catch (err) {
        console.error("Erro crítico em network.js:", err);
    }
})();
