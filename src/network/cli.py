"""
CLI da feature Network — expõe os comandos Typer para análise de rede.
Importa exclusivamente do pacote `network.*` (lógica vertical da feature).
"""

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from network.arp_scan import arp_scan
from network.dns_recon import dns_recon
from network.fingerprinting import detect_os
from network.ip_info import ip_info_lookup
from network.network_map import run as run_network_map
from network.ping_sweep import parse_network, ping_host
from network.port_scanner import parse_ports, scan_host
from network.smb_scan import smb_scan
from network.snmp_scan import snmp_scan
from network.traceroute import traceroute_host
from shared.config import get as cfg_get
from shared.exporter import ExportFormat, export_data
from shared.logger import get_logger

network_app = typer.Typer(help="Conjunto de ferramentas para análise e exploração de redes")
console = Console()
logger = get_logger(__name__)

# --- Defaults lidos do forenselab.toml (avaliados uma única vez no import) ---
_DEFAULT_PORTS = cfg_get("network", "default_ports", default="21,22,53,80,443,445,3306,8080")
_DEFAULT_MAP_PORTS = cfg_get("network", "default_ports", default="21,22,80,443,445,8080")
_DEFAULT_EXPORT_DIR = Path(cfg_get("export", "default_dir", default="./artefatos"))


@network_app.command("map", help="Mapeia dispositivos ativos na rede e salva os resultados")
def map(
    network: str = typer.Option(
        ..., "--network", "-n", help="Range de IPs da rede. Ex: 192.168.1.1-254"
    ),
    ports: str = typer.Option(
        _DEFAULT_MAP_PORTS, "--ports", "-p", help="Portas para escanear em cada host."
    ),
    output_dir: str = typer.Option(
        str(_DEFAULT_EXPORT_DIR / "network"),
        "--output",
        "-o",
        help="Diretório para salvar os resultados",
    ),
):
    console.print(
        f"[bold cyan][+] Iniciando mapeamento da rede {network} nas portas [{ports}]...[/bold cyan]"
    )
    try:
        with console.status("[bold green]Mapeando a rede...[/bold green]"):
            result = run_network_map(network, ports, output_dir)

        if result and result.get("json_file"):
            console.print(
                f"[bold green]✅ Resultados salvos em: {result.get('json_file')} e {result.get('csv_file')}[/bold green]"
            )
    except Exception as e:
        console.print(Panel(f"[bold red]Erro ao mapear rede: {e}[/bold red]", title="Erro"))


@network_app.command("scan", help="Realiza um scan de portas em um host específico")
def scan(
    target: str = typer.Option(..., "--target", "-t", help="Alvo do scan (IP ou hostname)"),
    ports: str = typer.Option(
        _DEFAULT_PORTS,
        "--ports",
        "-p",
        help="Portas para escanear. Ex: '22,80,100-200'",
    ),
    export: ExportFormat | None = typer.Option(
        None,
        "--export",
        "-e",
        help="Exporta os resultados para um arquivo. Valores: json, csv.",
    ),
    export_dir: Path = typer.Option(
        _DEFAULT_EXPORT_DIR / "network",
        "--export-dir",
        help="Diretório de destino da exportação.",
        resolve_path=True,
    ),
):
    logger.info("Comando 'scan' iniciado — alvo: %s | portas: %s", target, ports)
    try:
        ports_to_scan = parse_ports(ports)
        num_ports = len(ports_to_scan)
        logger.debug("Portas parseadas: %d porta(s) → %s", num_ports, ports_to_scan[:10])

        if num_ports == 0:
            logger.warning("Nenhuma porta válida fornecida para o scan em '%s'.", target)
            console.print("[bold yellow]Nenhuma porta especificada para o scan.[/bold yellow]")
            raise typer.Exit()

        console.print(
            f"[bold cyan][+] Iniciando scan em {num_ports} porta(s) de {target}...[/bold cyan]"
        )

        with console.status("[bold green]Escaneando portas...[/bold green]"):
            logger.debug("Disparando scan_host para '%s'...", target)
            results = scan_host(target=target, ports=ports)
            logger.debug("scan_host concluído — %d resultado(s) retornado(s).", len(results))

        table = Table(title=f"Resultados do Scan para {target}")
        table.add_column("Porta", style="cyan")
        table.add_column("Protocolo", style="magenta")
        table.add_column("Status", style="green")
        table.add_column("Serviço", style="yellow")
        table.add_column("Banner / Detalhes", style="white", overflow="fold")

        if not results:
            logger.info("Nenhuma porta aberta em '%s' no range '%s'.", target, ports)
            console.print(
                f"[bold yellow]Nenhuma porta aberta encontrada para '{target}' no range '{ports}'.[/bold yellow]"
            )
            return

        for res in results:
            logger.debug(
                "Porta aberta detectada: %s/%s — serviço: %s",
                res["port"],
                res["protocol"],
                res["service"],
            )
            table.add_row(
                str(res["port"]),
                res["protocol"],
                res["status"],
                res["service"],
                res.get("banner", ""),
            )
        console.print(table)
        logger.info(
            "Scan finalizado em '%s' — %d porta(s) abertas encontradas.", target, len(results)
        )

        if export:
            slug = target.replace(".", "_").replace(":", "-")
            dest = export_data(results, fmt=export, output_dir=export_dir, stem=f"scan_{slug}")
            console.print(f"[bold green]\u2705 Exportado para: {dest}[/bold green]")

    except ValueError as e:
        logger.error("Erro de validação nos parâmetros do scan: %s", e)
        console.print(Panel(f"[bold red]Erro de validação: {e}[/bold red]", title="Erro"))
    except Exception as e:
        logger.exception("Erro inesperado durante o scan em '%s'.", target)
        console.print(Panel(f"[bold red]Erro durante o scan: {e}[/bold red]", title="Erro"))


@network_app.command("sweep", help="Verifica hosts ativos em um range de IPs via ping")
def sweep(
    network: str = typer.Option(..., help="Range de IPs da rede. Exemplo: 192.168.1.1-254"),
):
    logger.info("Comando 'sweep' iniciado — range: %s", network)
    try:
        ips = parse_network(network)
        logger.debug("%d endereço(s) IP no range '%s'.", len(ips), network)
        alive_hosts = []

        with console.status("[bold green]Realizando ping sweep...[/bold green]"):
            for ip in ips:
                logger.debug("Pingando %s...", ip)
                if ping_host(ip):
                    logger.debug("Host ativo detectado: %s", ip)
                    alive_hosts.append(ip)

        logger.info("Sweep concluído — %d host(s) ativo(s) em '%s'.", len(alive_hosts), network)

        table = Table(title="Hosts Ativos")
        table.add_column("IP", style="cyan")
        table.add_column("Status", style="green")

        if alive_hosts:
            for host in alive_hosts:
                table.add_row(host, "ONLINE")
            console.print(table)
        else:
            logger.warning("Nenhum host respondeu ao ping no range '%s'.", network)
            console.print("[bold yellow]Nenhum host ativo encontrado.[/bold yellow]")
    except Exception as e:
        logger.exception("Erro inesperado durante o sweep no range '%s'.", network)
        console.print(Panel(f"[bold red]Erro durante o sweep: {e}[/bold red]", title="Erro"))


@network_app.command("fingerprinting", help="Detecta SO, serviços e portas abertas em um host")
def fingerprinting(ip: str = typer.Option(..., help="Endereço IP do host. Exemplo: 192.168.0.10")):
    console.print(f"[bold cyan][+] Verificando se {ip} está ativo...[/bold cyan]")
    try:
        if not ping_host(ip):
            console.print(f"[bold yellow][-] Host {ip} inatingível. Ping falhou.[/bold yellow]")
            return

        with console.status("[bold green]Escaneando portas e detectando SO...[/bold green]"):
            ports = scan_host(ip)
            result = detect_os(ip, ports=ports)

        table = Table(title=f"Fingerprinting de {ip}")
        table.add_column("Atributo", style="cyan")
        table.add_column("Valor", style="magenta")

        table.add_row("SO Detectado", result.get("os", "N/A"))
        table.add_row("Serviços", ", ".join(result.get("services", [])) or "Nenhum")
        table.add_row("Alertas", ", ".join(result.get("alerts", [])) or "Nenhum")

        console.print(table)
    except Exception as e:
        console.print(Panel(f"[bold red]Erro durante fingerprinting: {e}[/bold red]", title="Erro"))


@network_app.command("traceroute", help="Exibe o caminho (hops) até um domínio ou host")
def traceroute(
    domain: str = typer.Option(..., help="Informe um domínio ou hostname. Exemplo: google.com"),
):
    console.print(f"[bold cyan][+] Iniciando traceroute para {domain}...[/bold cyan]")
    try:
        with console.status("[bold green]Calculando rota...[/bold green]"):
            hops = traceroute_host(domain)

        table = Table(title=f"Traceroute para {domain}")
        table.add_column("Hop", style="cyan", justify="right")
        table.add_column("IP/Domínio", style="magenta")
        table.add_column("RTT (ms)", justify="right")

        for h in hops:
            rtt = h.get("rtt")
            target = h.get("domain", h.get("ip", "N/A"))
            if rtt is None:
                table.add_row(str(h["hop"]), target, "[grey50]Inacessível[/grey50]")
            elif rtt < 10:
                table.add_row(str(h["hop"]), target, f"[green]{rtt:.2f}[/green]")
            elif rtt < 50:
                table.add_row(str(h["hop"]), target, f"[yellow]{rtt:.2f}[/yellow]")
            else:
                table.add_row(str(h["hop"]), target, f"[red]{rtt:.2f}[/red]")

        console.print(table)
    except Exception as e:
        console.print(Panel(f"[bold red]Erro ao executar traceroute: {e}[/bold red]", title="Erro"))


@network_app.command(
    "arpscan", help="Realiza varredura ARP para identificar dispositivos na rede local"
)
def arp(
    network: str = typer.Option(..., help="Range de IPs da rede. Exemplo: 192.168.1.1-254"),
):
    try:
        with console.status("[bold green]Executando ARP Scan...[/bold green]"):
            result = arp_scan(network)

        table = Table(title="Resultados do ARP Scan")
        table.add_column("IP", style="cyan")
        table.add_column("MAC Address", style="magenta")

        if isinstance(result, list) and result:
            for item in result:
                table.add_row(item.get("ip", "N/A"), item.get("mac", "N/A"))
            console.print(table)
        else:
            console.print(
                "[bold yellow]Nenhum dispositivo encontrado ou resultado inválido.[/bold yellow]"
            )
            console.print(result)
    except Exception as e:
        console.print(Panel(f"[bold red]Erro durante o ARP scan: {e}[/bold red]", title="Erro"))


@network_app.command("dnscan", help="Realiza reconhecimento DNS em um domínio ou IP")
def dns(
    target: str = typer.Option(
        ..., help="Informe o domínio ou IP alvo. Exemplo: exemplo.com ou 8.8.8.8"
    ),
    output_dir: str = typer.Option(None, help="Diretório para salvar os resultados (JSON e CSV)"),
    with_subdomains: bool = typer.Option(
        False, help="Tentar descobrir subdomínios comuns do domínio informado"
    ),
):
    try:
        with console.status("[bold green]Realizando reconhecimento DNS...[/bold green]"):
            result = dns_recon([target], output_dir=output_dir, with_subdomains=with_subdomains)

        table = Table(title=f"Resultados DNS para {target}")
        table.add_column("Domínio", style="cyan")
        table.add_column("Tipo", style="magenta")
        table.add_column("Valor", style="white", overflow="fold")

        if isinstance(result, list) and result:
            for item in result:
                table.add_row(
                    item.get("domain", "N/A"), item.get("type", "N/A"), item.get("value", "N/A")
                )
            console.print(table)
        else:
            console.print("[bold yellow]Nenhum registro encontrado.[/bold yellow]")
    except Exception as e:
        console.print(
            Panel(f"[bold red]Erro durante reconhecimento DNS: {e}[/bold red]", title="Erro")
        )


@network_app.command("ipinfo", help="Obtém informações detalhadas sobre um IP ou hostname")
def ip_info(
    ip: str = typer.Option(..., help="IP ou hostname do destino. Exemplo: 8.8.8.8"),
):
    try:
        with console.status("[bold green]Buscando informações do IP...[/bold green]"):
            result = ip_info_lookup(ip)

        table = Table(title=f"Informações do IP: {ip}")
        table.add_column("Campo", style="cyan")
        table.add_column("Valor", style="white")

        if isinstance(result, dict) and result:
            for key, value in result.items():
                table.add_row(str(key), str(value))
            console.print(table)
        else:
            console.print("[bold yellow]Nenhuma informação encontrada.[/bold yellow]")
    except Exception as e:
        console.print(Panel(f"[bold red]Erro ao buscar IP Info: {e}[/bold red]", title="Erro"))


@network_app.command("smbscan", help="Verifica serviços SMB ativos em um host")
def smb(
    ip: str = typer.Option(..., help="IP ou hostname do destino. Exemplo: 192.168.0.10"),
):
    try:
        with console.status("[bold green]Analisando serviços SMB...[/bold green]"):
            result = smb_scan([ip])

        console.print(f"[bold cyan]Resultados SMB para {ip}:[/bold cyan]")
        console.print(result)
    except Exception as e:
        console.print(Panel(f"[bold red]Erro durante SMB scan: {e}[/bold red]", title="Erro"))


@network_app.command(
    "snmpscan", help="Executa varredura SNMP para identificar informações de dispositivos"
)
def snmp(
    ip: str = typer.Option(..., help="IP ou hostname do destino. Exemplo: 192.168.0.10"),
):
    try:
        with console.status("[bold green]Executando varredura SNMP...[/bold green]"):
            result = snmp_scan(ip)

        console.print(f"[bold cyan]Resultados SNMP para {ip}:[/bold cyan]")
        console.print(result)
    except Exception as e:
        console.print(Panel(f"[bold red]Erro durante SNMP scan: {e}[/bold red]", title="Erro"))
