import typer
from rich import print
from rich.text import Text
from rich.table import Table

from core.network.network_map import run as run_network_map
from core.network.port_scanner import scan_host, parse_ports
from core.network.ping_sweep import parse_network, ping_host
from core.network.fingerprinting import detect_os
from core.network.traceroute import traceroute_host
from core.network.arp_scan import arp_scan
from core.network.dns_recon import dns_recon
from core.network.ip_info import ip_info_lookup
from core.network.smb_scan import smb_scan
from core.network.snmp_scan import snmp_scan

network_app = typer.Typer(help="Conjunto de ferramentas para análise e exploração de redes")

@network_app.command("map", help="Mapeia dispositivos ativos na rede e salva os resultados")
def map(
    network: str = typer.Option(..., "--network", "-n", help="Range de IPs da rede. Ex: 192.168.1.1-254"),

    ports: str = typer.Option(
        "21,22,80,443,445,8080", 
        "--ports", 
        "-p", 
        help="Portas para escanear em cada host."
    ),

    output_dir: str = typer.Option(
        "./output", 
        "--output", 
        "-o", 
        help="Diretório para salvar os resultados"
    ),
):
    typer.echo(f"[+] Iniciando mapeamento da rede {network} nas portas [{ports}]...")

    result = run_network_map(network, ports, output_dir)

    if result and result.get('json_file'):
        typer.echo(f"Resultados salvos em: {result.get('json_file')} e {result.get('csv_file')}")

@network_app.command("scan", help="Realiza um scan de portas em um host específico")
def scan(
    target: str = typer.Option(..., "--target", "-t", help="Alvo do scan (IP ou hostname)"),
    ports: str = typer.Option("21,22,53,80,443,445,3306,8080", "--ports", "-p", help="Portas para escanear. Ex: '22,80,100-200'")
):
    try:
        ports_to_scan = parse_ports(ports)
        num_ports = len(ports_to_scan)

        if num_ports == 0:
            print("[yellow]Nenhuma porta especificada para o scan.[/yellow]")
            raise typer.Exit()

        typer.echo(f"[+] Iniciando scan em {num_ports} porta(s) de {target}...")

        results = []
        with typer.progressbar(length=num_ports, label="Scanning ports") as progress:
            def update_progress():
                progress.update(1)

            results = scan_host(
                target=target,
                ports=ports,
                callback=update_progress
            )

        table = Table(title=f"Resultados do Scan para {target}")
        table.add_column("Porta", style="cyan")
        table.add_column("Protocolo", style="magenta")
        table.add_column("Status", style="green")
        table.add_column("Serviço", style="yellow")
        table.add_column("Banner / Detalhes", style="white", overflow="fold")

        if not results:
            print(f"[yellow]Nenhuma porta aberta encontrada para '{target}' no range '{ports}'.[/yellow]")
            return

        for res in results:
            table.add_row(
                str(res["port"]),
                res["protocol"],
                res["status"],
                res["service"],
                res["banner"]
            )
        print(table)

    except ValueError as e:
        print(f"[bold red]Erro: {e}[/bold red]")

@network_app.command("sweep", help="Verifica hosts ativos em um range de IPs via ping")
def sweep(
    network: str = typer.Option(..., help="Range de IPs da rede. Exemplo: 192.168.1.1-254"),
):
    ips = parse_network(network)
    alive_hosts = []

    with typer.progressbar(ips, label="Scanning network") as progress:
        for ip in progress:
            if ping_host(ip):
                alive_hosts.append(ip)

    typer.echo(f"Hosts ativos: {alive_hosts}")

@network_app.command("fingerprinting", help="Detecta SO, serviços e portas abertas em um host")
def fingerprinting(
    ip: str = typer.Option(..., help="Endereço IP do host. Exemplo: 192.168.0.10")
):
    typer.echo(f"[+] Verificando se {ip} está ativo...")
    if not ping_host(ip):
        typer.echo(f"[-] Host {ip} inatingível. Ping falhou.")
        return

    typer.echo(f"[+] Escaneando portas de {ip}...")
    ports = scan_host(ip)

    typer.echo(f"[+] Detectando SO, serviços e alertas...")
    result = detect_os(ip, ports=ports)

    print(result)

@network_app.command("traceroute", help="Exibe o caminho (hops) até um domínio ou host")
def traceroute(
    domain: str = typer.Option(..., help="Informe um domínio ou hostname. Exemplo: google.com")
):
    typer.echo(f"[+] Iniciando traceroute para {domain}...")

    hops = traceroute_host(domain)

    with typer.progressbar(hops, label="Traceroute") as progress:
        for h in hops:
            rtt = h["rtt"]
            hop_text = Text(f" Hop {h['hop']}: {h.get('domain', h['ip'])} - RTT: ")

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

@network_app.command("arpscan", help="Realiza varredura ARP para identificar dispositivos na rede local")
def arp(
    network: str = typer.Option(..., help="Range de IPs da rede. Exemplo: 192.168.1.1-254"),
):
    result = arp_scan(network)
    print(result)

@network_app.command("dnscan", help="Realiza reconhecimento DNS em um domínio ou IP")
def dns(
    target: str = typer.Option(..., help="Informe o domínio ou IP alvo. Exemplo: exemplo.com ou 8.8.8.8"),
    output_dir: str = typer.Option(None, help="Diretório para salvar os resultados (JSON e CSV)"),
    with_subdomains: bool = typer.Option(False, help="Tentar descobrir subdomínios comuns do domínio informado"),
):
    result = dns_recon([target], output_dir=output_dir, with_subdomains=with_subdomains)

    typer.echo("[+] Resultados encontrados:")
    print(result)

@network_app.command("ipinfo", help="Obtém informações detalhadas sobre um IP ou hostname")
def ip_info(
    ip: str = typer.Option(..., help="IP ou hostname do destino. Exemplo: 8.8.8.8"),
):
    result = ip_info_lookup(ip)
    print(result)

@network_app.command("smbscan", help="Verifica serviços SMB ativos em um host")
def smb(
    ip: str = typer.Option(..., help="IP ou hostname do destino. Exemplo: 192.168.0.10"),
):
    result = smb_scan([ip])
    print(result)

@network_app.command("snmpscan", help="Executa varredura SNMP para identificar informações de dispositivos")
def snmp(
    ip: str = typer.Option(..., help="IP ou hostname do destino. Exemplo: 192.168.0.10"),
):
    result = snmp_scan(ip)
    print(result)
