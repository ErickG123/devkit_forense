import typer
from rich import print

from core.network.network_map import run as run_network_map
from core.network.port_scanner import scan_host
from core.network.ping_sweep import ping_sweep

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
    result = ping_sweep(network)
    print(result)
