"""
CLI da feature Browser — expõe os comandos Typer para análise de navegadores.
Importa exclusivamente do pacote `browser.*` (lógica vertical da feature).
"""

import json
import os
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from shared.engine import ForenseCoreError, run_go_core, stream_go_core
from shared.exporter import ExportFormat, export_data
from shared.reporter import generate_forensic_report

console = Console(legacy_windows=False if os.name == "nt" else None)

browser_app = typer.Typer(
    help="Conjunto de ferramentas para extrair e processar artefatos de navegadores "
    "(histórico, downloads, logins, favicons/screens e análises de padrões)."
)


@browser_app.command(
    "history",
    help="Extrai o histórico dos navegadores com Lock-Bypass em tempo real (Go Core NDJSON).",
)
def history(
    chrome: bool = typer.Option(False, "--chrome", help="Extrair histórico do Chrome"),
    edge: bool = typer.Option(False, "--edge", help="Extrair histórico do Edge"),
    all: bool = typer.Option(False, "--all", help="Extrair histórico de todos os navegadores"),
    limit: int = typer.Option(50, "--limit", "-l", help="Quantidade máxima de registros exibidos no terminal"),
    output_dir: Path = typer.Option(
        Path("artefatos/historico"),
        "--output-dir",
        "-o",
        help="Diretório de saída para salvar o histórico consolidado.",
        resolve_path=True,
    ),
    export: ExportFormat | None = typer.Option(
        None,
        "--export",
        "-e",
        help="Exporta os dados extraídos. Valores: json, csv.",
    ),
):
    output_dir.mkdir(parents=True, exist_ok=True)
    browser_target = "all"
    if chrome and not edge:
        browser_target = "chrome"
    elif edge and not chrome:
        browser_target = "edge"

    console.print(f"[bold cyan][*] Iniciando extração de histórico ({browser_target}) com Lock-Bypass...[/bold cyan]")

    all_records: list[dict] = []
    table = Table(title=f"Histórico Recente de Navegação ({browser_target.upper()})")
    table.add_column("Navegador", style="cyan")
    table.add_column("Perfil", style="magenta")
    table.add_column("Título / Página", style="white", overflow="fold")
    table.add_column("URL", style="yellow", overflow="fold")
    table.add_column("Visitas", justify="right", style="green")
    table.add_column("Última Visita (UTC)", style="blue")

    try:
        # Consome o gerador NDJSON em O(1) de memória
        for item in stream_go_core("browser-history", args=["--browser", browser_target]):
            all_records.append(item)
            if len(all_records) <= limit:
                table.add_row(
                    item.get("browser", "-"),
                    item.get("profile", "-"),
                    item.get("title", "") or "-",
                    item.get("url", "-"),
                    str(item.get("visit_count", 0)),
                    item.get("last_visit_utc", "-"),
                )

        console.print(table)
        console.print(f"[bold green][OK] Total de registros recuperados: {len(all_records)}[/bold green]")

        if export:
            dest = export_data(all_records, fmt=export, output_dir=output_dir, stem=f"historico_{browser_target}")
            console.print(f"[bold green]✅ Exportado para: {dest}[/bold green]")
        else:
            json_file = output_dir / f"historico_{browser_target}.json"
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(all_records, f, indent=2, ensure_ascii=False)
            console.print(f"[bold green]✅ Salvo em: {json_file}[/bold green]")

    except ForenseCoreError as e:
        console.print(Panel(f"[bold red]{e}[/bold red]", title="Erro no Go Core"))
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(Panel(f"[bold red]Erro na extração de histórico: {e}[/bold red]", title="Erro"))
        raise typer.Exit(code=1)


@browser_app.command(
    "downloads",
    help="Extrai registros de downloads dos navegadores com Lock-Bypass em tempo real (Go Core NDJSON).",
)
def downloads(
    chrome: bool = typer.Option(False, "--chrome", help="Extrair downloads do Chrome"),
    edge: bool = typer.Option(False, "--edge", help="Extrair downloads do Edge"),
    all: bool = typer.Option(False, "--all", help="Extrair downloads de todos os navegadores"),
    limit: int = typer.Option(50, "--limit", "-l", help="Quantidade máxima de registros exibidos no terminal"),
    output_dir: Path = typer.Option(
        Path("artefatos/downloads"),
        "--output-dir",
        "-o",
        help="Diretório de saída para salvar os artefatos dos downloads.",
        resolve_path=True,
    ),
    export: ExportFormat | None = typer.Option(
        None,
        "--export",
        "-e",
        help="Exporta os dados extraídos. Valores: json, csv.",
    ),
):
    output_dir.mkdir(parents=True, exist_ok=True)
    browser_target = "all"
    if chrome and not edge:
        browser_target = "chrome"
    elif edge and not chrome:
        browser_target = "edge"

    console.print(f"[bold cyan][*] Iniciando extração de downloads ({browser_target}) com Lock-Bypass...[/bold cyan]")

    all_downloads: list[dict] = []
    table = Table(title=f"Registros de Downloads ({browser_target.upper()})")
    table.add_column("Navegador", style="cyan")
    table.add_column("Perfil", style="magenta")
    table.add_column("Arquivo de Destino", style="white", overflow="fold")
    table.add_column("Bytes Recebidos", justify="right", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Data/Hora Início (UTC)", style="blue")

    try:
        for item in stream_go_core("browser-downloads", args=["--browser", browser_target]):
            all_downloads.append(item)
            if len(all_downloads) <= limit:
                table.add_row(
                    item.get("browser", "-"),
                    item.get("profile", "-"),
                    item.get("target_file", "") or "-",
                    str(item.get("received_bytes", 0)),
                    item.get("state", "UNKNOWN"),
                    item.get("start_time_utc", "-"),
                )

        console.print(table)
        console.print(f"[bold green][OK] Total de downloads recuperados: {len(all_downloads)}[/bold green]")

        if export:
            dest = export_data(all_downloads, fmt=export, output_dir=output_dir, stem=f"downloads_{browser_target}")
            console.print(f"[bold green]✅ Exportado para: {dest}[/bold green]")
        else:
            json_file = output_dir / f"downloads_{browser_target}.json"
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(all_downloads, f, indent=2, ensure_ascii=False)
            console.print(f"[bold green]✅ Salvo em: {json_file}[/bold green]")

    except ForenseCoreError as e:
        console.print(Panel(f"[bold red]{e}[/bold red]", title="Erro no Go Core"))
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(Panel(f"[bold red]Erro na extração de downloads: {e}[/bold red]", title="Erro"))
        raise typer.Exit(code=1)


@browser_app.command(
    "favscreen",
    help="Processa JSONs de histórico, extrai URLs válidas e captura favicons/screenshots.",
)
def favscreen(
    input_dir: Path = typer.Option(
        Path("artefatos/historico"),
        "--input-dir",
        "-i",
        help="Diretório contendo os JSONs de histórico para processar.",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    output_dir: Path = typer.Option(
        Path("artefatos/favscreen"),
        "--output-dir",
        "-o",
        help="Diretório de saída para salvar favicons e prints.",
        exists=False,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
):
    try:
        from browser.fav_screen import carregar_json, extrair_urls_validas, processar_urls
        arquivos_json = [
            input_dir / arquivo for arquivo in os.listdir(input_dir) if arquivo.endswith(".json")
        ]
        todas_urls = []

        for caminho in arquivos_json:
            dados = carregar_json(caminho)
            urls = extrair_urls_validas(dados)
            todas_urls.extend(urls)

        if todas_urls:
            todas_urls = list(set(todas_urls))
            processar_urls(todas_urls, output_dir)
            typer.echo("\n✅ Processamento finalizado.")
        else:
            typer.echo("\n⚠️ Nenhum arquivo JSON válido encontrado ou sem URLs úteis.")

    except Exception as erro:
        typer.echo(f"\n❌ Erro geral: {erro}")


@browser_app.command(
    "logins",
    help="Coleta credenciais/entradas de login dos navegadores suportados utilizando o motor Go (DPAPI Nativo).",
)
def logins(
    chrome: bool = typer.Option(False, "--chrome", help="Extrair logins do Chrome"),
    edge: bool = typer.Option(False, "--edge", help="Extrair logins do Edge"),
    all: bool = typer.Option(False, "--all", help="Extrair logins de todos os navegadores"),
    show_passwords: bool = typer.Option(
        False, "--show-passwords", "-s", help="Exibir senhas em texto plano no terminal"
    ),
    export_html: Optional[Path] = typer.Option(
        None, "--export-html", help="Caminho do arquivo para exportar Laudo Pericial em HTML"
    ),
    output_dir: Path = typer.Option(
        Path("artefatos/logins"),
        "--output-dir",
        "-o",
        help="Diretório para salvar os logins em JSON",
        resolve_path=True,
    ),
):
    output_dir.mkdir(parents=True, exist_ok=True)

    browser_target = "all"
    if chrome and not edge:
        browser_target = "chrome"
    elif edge and not chrome:
        browser_target = "edge"

    try:
        response = run_go_core(
            "browser-logins",
            args=["--browser", browser_target],
            task_name="Extraindo Credenciais Chromium (DPAPI)",
        )
        data = response.get("data", {})
        credentials = data.get("credentials") or []
        total = data.get("total_credentials", 0)

        table = Table(title=f"Credenciais Recuperadas ({total} encontradas)")
        table.add_column("Navegador", style="cyan")
        table.add_column("Perfil", style="magenta")
        table.add_column("URL / Origem", style="yellow", overflow="fold")
        table.add_column("Usuário", style="green")
        table.add_column("Senha", style="bold red" if show_passwords else "dim")

        for c in credentials:
            pwd_display = c.get("password", "") if show_passwords else "••••••••"
            table.add_row(
                c.get("browser", "Chromium"),
                c.get("profile", "Default"),
                c.get("origin_url", "-"),
                c.get("username", "-"),
                pwd_display,
            )

        console.print(table)

        # Salva o arquivo consolidado
        json_file = output_dir / f"{browser_target}_logins.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(credentials, f, indent=2, ensure_ascii=False)
        console.print(f"[bold green][OK] Credenciais salvas em: {json_file}[/bold green]")

        if export_html:
            report_path = generate_forensic_report(
                title=f"Laudo Pericial: Extração de Logins ({browser_target.upper()})",
                command=f"browser logins --{browser_target}",
                records=credentials,
                output_file=export_html,
                examiner=os.getenv("USERNAME", "Perito ForenseLab"),
            )
            console.print(f"[bold green][OK] Laudo Pericial HTML emitido em: {report_path}[/bold green]")

    except ForenseCoreError as e:
        console.print(Panel(f"[bold red]{e}[/bold red]", title="Erro na Extração de Logins"))
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(Panel(f"[bold red]Erro inesperado: {e}[/bold red]", title="Erro"))
        raise typer.Exit(code=1)


@browser_app.command(
    "patterns",
    help="Analisa históricos para identificar padrões incomuns e gera gráficos/relatórios na pasta de saída.",
)
def patterns(
    input_dir: Path = typer.Option(
        Path("artefatos/historico"),
        "--input-dir",
        "-i",
        help="Diretório contendo os JSONs de histórico para analisar padrões.",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    output_dir: Path = typer.Option(
        Path("artefatos/patterns_output"),
        "--output-dir",
        "-o",
        help="Diretório para salvar gráficos e relatórios.",
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
):
    try:
        from browser.unusual_patterns import processar_historico_da_pasta
        output_dir.mkdir(parents=True, exist_ok=True)

        typer.echo(f"[*] Processando arquivos em: {input_dir}")
        typer.echo(f"[*] Salvando resultados em: {output_dir}")

        processar_historico_da_pasta(str(input_dir), str(output_dir))

        typer.echo("\n✅ Processamento concluído.")

    except Exception as erro:
        typer.echo(f"\n❌ Erro ao executar patterns: {erro}")


@browser_app.command(
    "words",
    help="Extrai palavras/termos mais frequentes do histórico (ex.: pesquisas) e salva um JSON com os resultados.",
)
def words(
    chrome: bool = typer.Option(
        True, "--chrome", help="Extrair palavras mais pesquisadas do Chrome"
    ),
    output_dir: Path = typer.Option(
        Path("artefatos/words_output"),
        "--output-dir",
        "-o",
        help="Diretório para salvar o JSON com palavras mais pesquisadas",
        resolve_path=True,
    ),
):
    from browser.common_words import extract_words
    output_dir.mkdir(parents=True, exist_ok=True)
    extract_words(chrome=chrome, output_dir=output_dir)
