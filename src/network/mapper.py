"""
Módulo de Mapeamento Visual de Rede (Network Mapping).

Integra a descoberta de hosts em alta velocidade (Go Core Sweep) com a renderização
gráfica interativa de topologia de rede em HTML (PyVis / D3.js).
"""

from __future__ import annotations

import webbrowser
from pathlib import Path
from typing import Any, Optional

from rich.console import Console

from shared.engine import ForenseCoreError, run_go_core

console = Console()


def generate_interactive_map(
    network_cidr: str,
    active_hosts: list[dict[str, Any]],
    output_html: Path | str = "artefatos/network/network_map.html",
    open_browser: bool = True,
) -> Path:
    """
    Gera um grafo HTML interativo da rede conectando hosts ativos a um Gateway/Switch central.
    """
    try:
        from pyvis.network import Network
    except ImportError:
        raise ImportError(
            "A biblioteca 'pyvis' é necessária para renderizar o mapa interativo. "
            "Instale com: pip install pyvis"
        )

    output_path = Path(output_html).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Cria a rede interativa com tema escuro forense
    net = Network(height="750px", width="100%", bgcolor="#1a1b26", font_color="#c0caf5")
    net.force_atlas_2based()

    # Adiciona o nó central (Gateway/Sub-rede)
    central_id = f"Net: {network_cidr}"
    net.add_node(
        central_id,
        label=central_id,
        color="#f7768e",
        size=35,
        title=f"Sub-rede Analisada: {network_cidr}",
        shape="hexagon",
    )

    for host in active_hosts:
        ip = host.get("ip", "Unknown")
        method = host.get("method", "tcp-ack")
        port = host.get("port", "-")
        latency = host.get("latency_ms", 0)

        # Diferencia visualmente gateways (.1 ou .254) de endpoints comuns
        is_gw = ip.endswith(".1") or ip.endswith(".254")
        node_color = "#e0af68" if is_gw else "#7aa2f7"
        node_size = 25 if is_gw else 18
        shape = "diamond" if is_gw else "dot"

        hover_text = (
            f"<b>Host Ativo:</b> {ip}<br>"
            f"<b>Status:</b> ONLINE<br>"
            f"<b>Método de Resposta:</b> {method}<br>"
            f"<b>Porta Probe:</b> {port}<br>"
            f"<b>Latência:</b> {latency}ms"
        )

        net.add_node(
            ip,
            label=ip,
            color=node_color,
            size=node_size,
            title=hover_text,
            shape=shape,
        )

        # Conecta o host ao nó central da sub-rede
        edge_title = f"{latency}ms ({method})"
        net.add_edge(central_id, ip, title=edge_title, color="#414868", width=1.5)

    net.set_options(
        """
    var options = {
      "physics": {
        "forceAtlas2Based": {
          "gravitationalConstant": -50,
          "centralGravity": 0.01,
          "springLength": 100,
          "springConstant": 0.08
        },
        "maxVelocity": 30,
        "solver": "forceAtlas2Based",
        "timestep": 0.35
      }
    }
    """
    )

    net.save_graph(str(output_path))

    if open_browser:
        webbrowser.open(output_path.as_uri())

    return output_path


def run_network_mapping(
    network: str,
    output_html: Path | str = "artefatos/network/network_map.html",
    workers: int = 150,
    open_browser: bool = True,
) -> Path:
    """
    Dispara o sweep no Go Core e projeta os nós no grafo HTML.
    """
    console.print(f"[bold cyan][+] Mapeando topologia da rede {network} via Go Core...[/bold cyan]")

    response = run_go_core(
        "sweep",
        args=["--network", network, "--workers", str(workers)],
        task_name=f"Varredura de Topologia ({network})",
    )

    data = response.get("data", {})
    active_hosts = data.get("active_hosts", [])

    console.print(
        f"[bold green][OK] Varredura concluída. {len(active_hosts)} host(s) ativo(s) detectado(s).[/bold green]"
    )

    map_path = generate_interactive_map(
        network_cidr=network,
        active_hosts=active_hosts,
        output_html=output_html,
        open_browser=open_browser,
    )

    return map_path
