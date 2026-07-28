"""
CLI da feature Email — expõe os comandos Typer para análise forense de e-mails.
Importa exclusivamente do pacote `email_feature.*` (lógica vertical da feature).

Nota: o pacote é nomeado `email_feature` para evitar conflito com o módulo
stdlib `email` do Python.
"""

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from mail.email_parser import parse_eml_folder
from mail.header_analysis import analyze_email_headers

email_app = typer.Typer(help="Ferramentas para análise e manipulação de dados de e-mail")
console = Console()


@email_app.command("parse", help="Analisa arquivos .eml e extrai metadados, anexos e hashes.")
def parse(
    folder: Path = typer.Argument(..., help="Caminho da pasta contendo os arquivos .eml"),
    output: Path = typer.Option(
        Path("artefatos/email"),
        "--output",
        "-o",
        help="Diretório de saída para salvar o JSON com os resultados.",
        resolve_path=True,
    ),
):
    try:
        output.mkdir(parents=True, exist_ok=True)

        with console.status("[bold green]Processando arquivos .eml...[/bold green]"):
            results = parse_eml_folder(str(folder))

        if not results:
            console.print(
                "[bold yellow]Nenhum arquivo .eml encontrado ou processado.[/bold yellow]"
            )
            return

        table = Table(title=f"E-mails Processados ({len(results)} encontrados)")
        table.add_column("De", style="cyan")
        table.add_column("Para", style="magenta")
        table.add_column("Assunto", style="white", overflow="fold")
        table.add_column("Data", style="yellow")
        table.add_column("Anexos", style="green", justify="right")

        for em in results:
            table.add_row(
                em.get("from") or "N/A",
                em.get("to") or "N/A",
                em.get("subject") or "N/A",
                em.get("date") or "N/A",
                str(len(em.get("attachments", []))),
            )

        console.print(table)

        saida = output / "email_parsed.json"
        with open(saida, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=4, ensure_ascii=False)

        console.print(f"[bold green]✅ Resultados salvos em: {saida}[/bold green]")

    except Exception as e:
        console.print(Panel(f"[bold red]Erro ao processar e-mails: {e}[/bold red]", title="Erro"))


@email_app.command(
    "headers", help="Analisa cabeçalhos de e-mail para detectar SPF, DKIM, DMARC e IPs de origem."
)
def headers(
    json_input: Path = typer.Argument(
        ..., help="Caminho do JSON gerado pelo comando 'parse'", exists=True
    ),
    output: Path = typer.Option(
        Path("artefatos/email"),
        "--output",
        "-o",
        help="Diretório de saída para salvar a análise.",
        resolve_path=True,
    ),
):
    try:
        output.mkdir(parents=True, exist_ok=True)

        with open(json_input, "r", encoding="utf-8") as f:
            emails = json.load(f)

        with console.status("[bold green]Analisando cabeçalhos...[/bold green]"):
            results = [analyze_email_headers(em) for em in emails]

        table = Table(title="Análise de Cabeçalhos")
        table.add_column("Assunto", style="cyan", overflow="fold")
        table.add_column("SPF", style="green")
        table.add_column("DKIM", style="yellow")
        table.add_column("DMARC", style="magenta")
        table.add_column("IPs de Origem", style="white")

        for r in results:
            spf_style = "green" if r.get("spf") == "pass" else "red"
            table.add_row(
                r.get("subject") or "N/A",
                f"[{spf_style}]{r.get('spf', 'N/A')}[/{spf_style}]",
                r.get("dkim", "N/A"),
                r.get("dmarc", "N/A"),
                ", ".join(r.get("origin_ips", [])) or "N/A",
            )

        console.print(table)

        saida = output / "email_headers.json"
        with open(saida, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=4, ensure_ascii=False)

        console.print(f"[bold green]✅ Análise salva em: {saida}[/bold green]")

    except Exception as e:
        console.print(Panel(f"[bold red]Erro ao analisar cabeçalhos: {e}[/bold red]", title="Erro"))
