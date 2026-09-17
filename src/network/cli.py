"""
CLI da feature Network — expõe os comandos Typer para análise de rede.
Importa exclusivamente do pacote `network.*` (lógica vertical da feature).
"""

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from shared.config import get as cfg_get
from shared.binary_resolver import ForenseBinaryNotFoundError, ForenseSecurityBlockError
from shared.engine import ForenseCoreError, run_go_core
from shared.exporter import ExportFormat, export_data
from shared.logger import get_logger

network_app = typer.Typer(help="Conjunto de ferramentas para análise e exploração de redes")
console = Console()
logger = get_logger(__name__)

# --- Defaults lidos do forenselab.toml (avaliados uma única vez no import) ---
_DEFAULT_PORTS = cfg_get("network", "default_ports", default="21,22,53,80,443,445,3306,8080")
_DEFAULT_MAP_PORTS = cfg_get("network", "default_ports", default="21,22,80,443,445,8080")
_DEFAULT_EXPORT_DIR = Path(cfg_get("export", "default_dir", default="./artefatos"))


@network_app.command("map", help="Mapeia topologia visual interativa da rede via Go Core e gera grafo HTML")
def map(
    network: str = typer.Option(
        ..., "--network", "-n", help="Range de IPs ou CIDR da rede. Ex: 192.168.1.0/24 ou 192.168.1.1-254"
    ),
    output: Path = typer.Option(
        Path("artefatos/network/network_map.html"),
        "--output",
        "-o",
        help="Arquivo HTML de destino para o grafo interativo.",
        resolve_path=True,
    ),
    no_browser: bool = typer.Option(
        False, "--no-browser", help="Não abre o navegador automaticamente após gerar o mapa."
    ),
):
    try:
        from network.mapper import run_network_mapping

        result_path = run_network_mapping(
            network=network,
            output_html=output,
            open_browser=not no_browser,
        )
        console.print(f"[bold green][OK] Mapa visual gerado com sucesso em: {result_path}[/bold green]")
    except Exception as e:
        logger.exception("Erro ao gerar mapa da rede.")
        console.print(Panel(f"[bold red]Erro ao mapear topologia: {e}[/bold red]", title="Erro"))
        raise typer.Exit(code=1)


@network_app.command("scan", help="Realiza um scan de portas em um host específico utilizando o motor Go de alta performance")
def scan(
    target: str = typer.Option(..., "--target", "-t", help="Alvo do scan (IP ou hostname)"),
    ports: str = typer.Option(
        _DEFAULT_PORTS,
        "--ports",
        "-p",
        help="Portas para escanear. Ex: '22,80,100-200'",
    ),
    workers: int = typer.Option(
        500,
        "--workers",
        "-w",
        help="Quantidade de workers paralelos no motor Go.",
    ),
    timeout: int = typer.Option(
        1000,
        "--timeout",
        help="Timeout por porta em milissegundos.",
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
    logger.info("Comando 'scan' iniciado (Go Core) — alvo: %s | portas: %s", target, ports)
    try:
        args = [
            "--target",
            target,
            "--ports",
            ports,
            "--workers",
            str(workers),
            "--timeout",
            str(timeout),
        ]
        response = run_go_core("scan", args=args, task_name=f"Escaneando {target}")
        data = response.get("data", {})
        results = data.get("open_ports", [])
        duration_ms = response.get("duration_ms", 0)

        table = Table(title=f"Resultados do Scan para {target} (Duração: {duration_ms}ms)")
        table.add_column("Porta", style="cyan", justify="right")
        table.add_column("Protocolo", style="magenta")
        table.add_column("Status", style="green")
        table.add_column("Serviço", style="yellow")
        table.add_column("Latência (ms)", justify="right", style="blue")
        table.add_column("Banner / Detalhes", style="white", overflow="fold")

        if not results:
            logger.info("Nenhuma porta aberta em '%s' no range '%s'.", target, ports)
            console.print(
                f"[bold yellow]Nenhuma porta aberta encontrada para '{target}' no range '{ports}'.[/bold yellow]"
            )
            return

        for res in results:
            table.add_row(
                str(res["port"]),
                res.get("protocol", "tcp"),
                res.get("state", "open").upper(),
                res.get("service", "unknown"),
                str(res.get("latency_ms", 0)),
                res.get("banner", "") or "-",
            )
        console.print(table)
        logger.info(
            "Scan finalizado em '%s' — %d porta(s) abertas encontradas.", target, len(results)
        )

        if export:
            slug = target.replace(".", "_").replace(":", "-")
            dest = export_data(results, fmt=export, output_dir=export_dir, stem=f"scan_{slug}")
            console.print(f"[bold green]✅ Exportado para: {dest}[/bold green]")

    except (ForenseSecurityBlockError, ForenseBinaryNotFoundError) as e:
        logger.error("Falha de segurança ou executável bloqueado durante scan em '%s': %s", target, e)
        raise typer.Exit(code=1)
    except ForenseCoreError as e:
        logger.error("Erro no motor Go durante scan em '%s': %s", target, e)
        console.print(Panel(f"[bold red]{e}[/bold red]", title="Erro no Núcleo Go"))
        raise typer.Exit(code=1)
    except Exception as e:
        logger.exception("Erro inesperado durante o scan em '%s'.", target)
        console.print(Panel(f"[bold red]Erro durante o scan: {e}[/bold red]", title="Erro"))
        raise typer.Exit(code=1)


@network_app.command("sweep", help="Verifica hosts ativos em um range de IPs via probe unprivileged")
def sweep(
    network: str = typer.Option(
        ...,
        help="Range de IPs da rede. Exemplo: 192.168.1.1-254 ou 192.168.1.0/24",
    ),
    workers: int = typer.Option(100, "--workers", "-w", help="Quantidade de workers paralelos."),
    timeout: int = typer.Option(400, "--timeout", help="Timeout de probe por host em ms."),
):
    logger.info("Comando 'sweep' iniciado (Go Core) — range: %s", network)
    try:
        args = [
            "--network",
            network,
            "--workers",
            str(workers),
            "--timeout",
            str(timeout),
        ]
        response = run_go_core("sweep", args=args, task_name=f"Ping Sweep ({network})")
        data = response.get("data", {})
        alive_hosts = data.get("active_hosts", [])
        duration_ms = response.get("duration_ms", 0)

        logger.info(
            "Sweep concluído — %d host(s) ativo(s) em '%s' (%dms).",
            len(alive_hosts),
            network,
            duration_ms,
        )

        table = Table(title=f"Hosts Ativos na Rede ({network}) - {duration_ms}ms")
        table.add_column("IP", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Método", style="magenta")
        table.add_column("Porta Probe", justify="right", style="yellow")
        table.add_column("Latência (ms)", justify="right", style="blue")

        if alive_hosts:
            for host in alive_hosts:
                table.add_row(
                    host["ip"],
                    host.get("status", "ONLINE"),
                    host.get("method", "tcp-ack"),
                    str(host.get("port", "-")),
                    str(host.get("latency_ms", 0)),
                )
            console.print(table)
        else:
            logger.warning("Nenhum host respondeu no range '%s'.", network)
            console.print("[bold yellow]Nenhum host ativo encontrado.[/bold yellow]")

    except ForenseCoreError as e:
        logger.error("Erro no motor Go durante sweep: %s", e)
        console.print(Panel(f"[bold red]{e}[/bold red]", title="Erro no Núcleo Go"))
        raise typer.Exit(code=1)
    except Exception as e:
        logger.exception("Erro inesperado durante o sweep no range '%s'.", network)
        console.print(Panel(f"[bold red]Erro durante o sweep: {e}[/bold red]", title="Erro"))
        raise typer.Exit(code=1)


@network_app.command("fingerprinting", help="Detecta SO, serviços e banners em um host utilizando o motor Go")
def fingerprinting(
    ip: str = typer.Option(..., "--ip", "-i", help="Endereço IP do host alvo. Exemplo: 192.168.0.10"),
    ports: str = typer.Option(
        "21,22,23,25,53,80,110,135,139,143,443,445,3306,3389,5432,5900,8080",
        "--ports",
        "-p",
        help="Portas para escanear via Go Core",
    ),
):
    try:
        from network.fingerprinting import analyze_fingerprint

        # 1. Executa o Port Scan ultrarrápido via Go Core
        response = run_go_core(
            "scan",
            args=["--target", ip, "--ports", ports, "--workers", "200", "--timeout", "800"],
            task_name=f"Varredura Go para Fingerprint ({ip})",
        )
        data = response.get("data", {})
        open_ports = data.get("open_ports", [])

        # 2. Executa análise contextual e banner grabbing direcionado
        with console.status("[bold green]Analisando banners e inferindo sistema operacional...[/bold green]"):
            result = analyze_fingerprint(ip, open_ports)

        # 3. Renderiza tabela com dados ricos
        table = Table(title=f"Fingerprinting de {ip} ({result.get('os')})")
        table.add_column("Atributo", style="cyan", width=25)
        table.add_column("Valor / Diagnóstico", style="white", overflow="fold")

        table.add_row("SO Estimado", f"[bold green]{result.get('os')}[/bold green]")
        table.add_row("Perfil do Host", result.get("host_type", "Desconhecido"))
        table.add_row("Portas Abertas", f"{result.get('total_open')} porta(s)")

        if result.get("ports"):
            services_detail = "\n".join(
                f"• Porta {p['port']} ({p['service']}): {p['banner']}" for p in result["ports"]
            )
            table.add_row("Serviços & Banners", services_detail)

        if result.get("alerts"):
            alerts_text = "\n".join(f"[bold red]⚠️ {a}[/bold red]" for a in result["alerts"])
            table.add_row("Alertas Forenses", alerts_text)

        console.print(table)

    except (ForenseSecurityBlockError, ForenseBinaryNotFoundError) as e:
        logger.error("Bloqueio de segurança durante fingerprinting em '%s': %s", ip, e)
        raise typer.Exit(code=1)
    except ForenseCoreError as e:
        console.print(Panel(f"[bold red]{e}[/bold red]", title="Erro no Go Core"))
        raise typer.Exit(code=1)
    except Exception as e:
        logger.exception("Erro inesperado durante o fingerprinting em '%s'.", ip)
        console.print(Panel(f"[bold red]Erro durante o fingerprinting: {e}[/bold red]", title="Erro"))
        raise typer.Exit(code=1)


@network_app.command(
    "arpscan",
    help="[DEPRECIADO] Redireciona automaticamente para o comando 'network sweep' nativo em Go",
)
def arp(
    network: str = typer.Option(..., help="Range de IPs da rede. Exemplo: 192.168.1.1-254 ou 192.168.1.0/24"),
    workers: int = typer.Option(100, "--workers", "-w", help="Quantidade de workers paralelos."),
    timeout: int = typer.Option(400, "--timeout", help="Timeout de probe por host em ms."),
):
    console.print(
        "[bold yellow][AVISO DE DEPRECIAÇÃO][/bold yellow] "
        "[dim]O comando 'arpscan' (baseado em scapy/Npcap) foi depreciado em favor do motor unprivileged em Go.[/dim]\n"
        f"[bold cyan][*] Redirecionando automaticamente para: [white]network sweep --network {network}[/white]...[/bold cyan]\n"
    )
    # Invoca internamente a implementação de sweep baseada no motor Go
    sweep(network=network, workers=workers, timeout=timeout)


@network_app.command("traceroute", help="Exibe o caminho (hops) até um domínio ou host")
def traceroute(
    domain: str = typer.Option(..., help="Informe um domínio ou hostname. Exemplo: google.com"),
):
    console.print(f"[bold cyan][+] Iniciando traceroute para {domain}...[/bold cyan]")
    try:
        from network.traceroute import traceroute_host
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
        from network.arp_scan import arp_scan
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
        from network.dns_recon import dns_recon
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
        from network.ip_info import ip_info_lookup
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
        from network.smb_scan import smb_scan
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
        from network.snmp_scan import snmp_scan
        with console.status("[bold green]Executando varredura SNMP...[/bold green]"):
            result = snmp_scan(ip)

        console.print(f"[bold cyan]Resultados SNMP para {ip}:[/bold cyan]")
        console.print(result)
    except Exception as e:
        console.print(Panel(f"[bold red]Erro durante SNMP scan: {e}[/bold red]", title="Erro"))
