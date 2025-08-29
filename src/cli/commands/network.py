import typer
from rich import print
from rich.text import Text

from core.network.network_map import run as run_network_map
from core.network.port_scanner import scan_host
from core.network.ping_sweep import parse_network, ping_host
from core.network.fingerprinting import detect_os
from core.network.traceroute import traceroute_host

network_app = typer.Typer()

@network_app.command("map")
def map(
    network: str = typer.Option(..., help="Range de IPs da rede, ex: 192.168.1.1-254"),
    output_dir: str = typer.Option("./output", help="Diretório para salvar os resultados"),
):
    result = run_network_map(network, output_dir)
    typer.echo(f"Resultados salvos em: {result['json_file']} e {result['csv_file']}")

@network_app.command("scan")
def scan(
    ip: str = typer.Option(..., help="IP da rede, ex: 192.168.0.0")
):
    result = scan_host(ip)
    print(result)

@network_app.command("sweep")
def sweep(
    network: str = typer.Option(..., help="Range de IPs da rede, ex: 192.168.1.1-254"),
):
    ips = parse_network(network)
    alive_hosts = []

    with typer.progressbar(ips, label="Scanning network") as progress:
        for ip in progress:
            if ping_host(ip):
                alive_hosts.append(ip)

    typer.echo(f"Hosts ativos: {alive_hosts}")

@network_app.command("fingerprinting")
def fingerprinting(
    ip: str = typer.Option(..., help="IP da red, ex: 192.168.0.0")
):
    typer.echo(f"[+] Verificando se {ip} está ativo...")
    if not ping_host(ip):
        typer.echo(f"[-] Host {ip} inatingível. Ping falhou.")
        return

    typer.echo(f"[+] Escaneando portas de {ip}...")
    ports = scan_host(ip)

    typer.echo(f"[+] Detectando OS, serviços e alertas...")
    result = detect_os(ip, ports=ports)

    print(result)

@network_app.command("traceroute")
def traceroute(
    ip: str = typer.Option(..., help="IP ou hostname do destino")
):
    typer.echo(f"[+] Iniciando traceroute para {ip}...")

    hops = traceroute_host(ip)

    with typer.progressbar(hops, label="Traceroute") as progress:
        for h in hops:
            rtt = h["rtt"]
            hop_text = Text(f"Hop {h['hop']}: {h['ip']} - RTT: ")

            if rtt is None:
                hop_text.append("inacessível", style="grey50")
            elif rtt < 10:
                hop_text.append(f"{rtt} ms", style="green")
            elif rtt < 50:
                hop_text.append(f"{rtt} ms", style="yellow")
            else:
                hop_text.append(f"{rtt} ms", style="red")

            print(hop_text)
            progress.update(1)
