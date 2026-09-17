"""
CLI da feature Email — expõe os comandos Typer para análise forense de e-mails.
Importa exclusivamente do pacote `email_feature.*` (lógica vertical da feature).

Nota: o pacote é nomeado `email_feature` para evitar conflito com o módulo
stdlib `email` do Python.
"""

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from mail.header_analysis import analyze_email_headers

email_app = typer.Typer(help="Ferramentas para análise e manipulação de dados de e-mail")
console = Console()


@email_app.command(
    "parse",
    help="Analisa arquivo .eml ou pasta de evidências e extrai remetente, destinatário, IP de origem, cabeçalhos e anexos.",
)
def parse(
    file: Optional[Path] = typer.Option(
        None, "--file", "-f", help="Caminho de um arquivo .eml específico para análise."
    ),
    folder: Optional[Path] = typer.Option(
        None, "--folder", "-d", help="Caminho da pasta contendo múltiplos arquivos .eml."
    ),
    output: Path = typer.Option(
        Path("artefatos/email"),
        "--output",
        "-o",
        help="Diretório de saída para salvar o JSON com os resultados e anexos.",
        resolve_path=True,
    ),
):
    try:
        from mail.email_parser import parse_eml_file, parse_eml_folder

        output.mkdir(parents=True, exist_ok=True)
        results = []

        if file and file.is_file():
            with console.status(f"[bold green]Processando {file.name}...[/bold green]"):
                results.append(parse_eml_file(str(file)))
        elif folder and folder.is_dir():
            with console.status("[bold green]Processando pasta de e-mails...[/bold green]"):
                results = parse_eml_folder(str(folder))
        else:
            console.print(
                "[bold red]Erro: Informe ao menos um arquivo (--file evidencia.eml) ou diretório (--folder pasta/)[/bold red]"
            )
            raise typer.Exit(code=1)

        if not results:
            console.print("[bold yellow]Nenhum arquivo .eml válido encontrado ou processado.[/bold yellow]")
            return

        table = Table(title=f"Evidências de E-mail Analisadas ({len(results)} processado(s))")
        table.add_column("Arquivo / ID", style="cyan")
        table.add_column("De (Sender)", style="magenta")
        table.add_column("IP Origem", style="yellow")
        table.add_column("Assunto", style="white", overflow="fold")
        table.add_column("Data", style="blue")
        table.add_column("Anexos", style="green", justify="right")

        for em in results:
            table.add_row(
                em.get("file") or em.get("message_id") or "N/A",
                em.get("from") or "N/A",
                em.get("origin_ip") or "N/A",
                em.get("subject") or "N/A",
                em.get("date") or "N/A",
                str(len(em.get("attachments", []))),
            )

        console.print(table)

        saida = output / "email_parsed.json"
        with open(saida, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=4, ensure_ascii=False)

        console.print(f"[bold green][OK] Resultados e anexos salvos em: {saida}[/bold green]")

    except Exception as e:
        console.print(Panel(f"[bold red]Erro ao processar e-mails: {e}[/bold red]", title="Erro"))
        raise typer.Exit(code=1)


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
