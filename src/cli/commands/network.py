import typer
from rich import print

from core.network.network_map import run as run_network_map
from core.network.port_scanner import scan_host
from core.network.ping_sweep import parse_network, ping_host
from core.network.fingerprinting import detect_os

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
    result = detect_os(ip)
    print(result)
