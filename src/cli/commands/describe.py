import json
import difflib
from typing import Any

import typer
from rich import print
from rich.table import Table
from rich.pretty import Pretty

describe_app = typer.Typer(help="Ajuda interativa para os comandos/funcionalidades do toolkit forense.")

docs = {
    "map": {
        "name": "map / run_network_map",
        "description": "Retorna informações detalhadas de cada host da rede.",
        "example_return": [
            {
                "host": "192.168.1.1",
                "hostname": "router",
                "mac": "AA:BB:CC:DD:EE:FF",
                "vendor": "Cisco",
                "open_ports": [22, 80],
                "os_info": "Linux"
            }
        ],
    },
    "sweep": {
        "name": "sweep / ping_sweep",
        "description": "Faz um ping sweep na rede e retorna os hosts ativos.",
        "example_return": ["192.168.1.1", "192.168.1.3"],
    },
    "scan": {
        "name": "scan / port_scanner",
        "description": "Verifica quais portas estão abertas, fechadas e filtradas.",
        "example_return": [
            {
                "port": 53,
                "protocol": "UDP",
                "status": "open|filtered",
                "banner": "sem resposta",
                "alert": "DNS"
            }
        ],
    },
    "fingerprinting": {
        "name": "fingerprinting / detect_os",
        "description": "Detecta o sistema operacional, tipo de host, serviços e possíveis alertas de vulnerabilidade de um host.",
        "example_return": {
            "os": "Windows",
            "host_type": "Servidor",
            "services": ["SMB", "Web HTTP", "MySQL"],
            "alerts": ["SMB vulnerável (Samba 3.0)"]
        },
    },
    "traceroute": {
        "name": "traceroute / traceroute_host",
        "description": "Executa um traceroute até um host e retorna a rota (hops) percorrida.",
        "example_return": [
            {"hop": 1, "ip": "192.168.1.1", "rtt_ms": 1.2},
            {"hop": 2, "ip": "10.0.0.1", "rtt_ms": 10.5},
        ],
    },
    "arp_scan": {
        "name": "arp_scan / arp_scan",
        "description": "Faz uma varredura ARP na sub-rede para descobrir MACs/IPs ativos.",
        "example_return": [
            {"ip": "192.168.1.10", "mac": "AA:BB:CC:11:22:33", "vendor": "Intel"},
        ],
    },
    "parse_ports": {
        "name": "parse_ports",
        "description": "Função auxiliar que transforma a saída do scanner em um formato padronizado.",
        "example_return": [
            {"port": 22, "state": "open", "service": "ssh"},
            {"port": 80, "state": "open", "service": "http"},
        ],
    },
    "parse_network": {
        "name": "parse_network / ping_sweep.parse_network",
        "description": "Analisa e normaliza a representação da rede (ex: 192.168.0.0/24).",
        "example_return": {"network": "192.168.0.0/24", "hosts": 254},
    },
    "scan_host": {
        "name": "scan_host",
        "description": "Escaneia portas de um único host (wrapper do port_scanner).",
        "example_return": [
            {"port": 443, "protocol": "tcp", "status": "open", "service": "https"},
        ],
    },
    "ping_host": {
        "name": "ping_host",
        "description": "Faz ping em um host e retorna latência e status.",
        "example_return": {"host": "192.168.1.5", "alive": True, "rtt_ms": 2.3},
    },
}

def _find_key(key: str) -> str | None:
    key_lower = key.lower()
    keys = list(docs.keys())
    for k in keys:
        if k == key_lower or docs[k].get("name", "").lower().split()[0] == key_lower:
            return k

    matches = difflib.get_close_matches(key_lower, keys, n=3, cutoff=0.5)

    return matches[0] if matches else None

def _print_example(example: Any, full: bool):
    if full:
        print(Pretty(example))
    else:
        try:
            s = json.dumps(example, indent=2, ensure_ascii=False)
        except Exception:
            s = str(example)
        print(s)

@describe_app.command("func", help="Mostra a descrição e exemplo de retorno de uma função/command do toolkit.")
def describe(
    func: str = typer.Argument(..., help="Nome da função que você deseja entender (ex: map, scan, sweep)"),
    full: bool = typer.Option(False, "--full", "-f", help="Mostrar exemplo formatado (mais detalhado)."),
):
    key = _find_key(func)
    if not key:
        candidates = difflib.get_close_matches(func.lower(), list(docs.keys()), n=5, cutoff=0.4)
        if candidates:
            print(f"[yellow]Função '{func}' não encontrada. Você quis dizer:[/yellow]")
            for c in candidates:
                print(f"  • {c} — {docs[c]['description']}")
            raise typer.Exit(code=1)
        else:
            print(f"[red]Função '{func}' não encontrada e nenhuma sugestão foi localizada.[/red]")
            raise typer.Exit(code=1)

    info = docs[key]

    print(f"[bold blue]Nome da Função:[/bold blue] {info.get('name', key)}")
    print(f"[bold blue]Descrição:[/bold blue] {info.get('description')}")
    print("[bold blue]Exemplo de Retorno:[/bold blue]")
    _print_example(info.get("example_return"), full=full)

@describe_app.command("list", help="Lista todas as funções/commands documentados.")
def list_commands():
    table = Table(title="Comandos documentados", show_lines=False)
    table.add_column("chave", style="cyan", no_wrap=True)
    table.add_column("nome", style="magenta")
    table.add_column("descrição", style="white")
    for k, v in sorted(docs.items()):
        table.add_row(k, v.get("name", ""), v.get("description", ""))
    print(table)

if __name__ == "__main__":
    describe_app()
