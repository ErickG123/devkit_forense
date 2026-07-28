"""
CLI da feature Browser — expõe os comandos Typer para análise de navegadores.
Importa exclusivamente do pacote `browser.*` (lógica vertical da feature).
"""

import json
import os
from pathlib import Path

import typer

from browser.browser_history import extract_firefox_history, extract_google_edge_history
from browser.common_words import extract_words
from browser.downloads_history import extract_downloads_history
from browser.fav_screen import carregar_json, extrair_urls_validas, processar_urls
from browser.logins import collect_chrome_logins, collect_edge_logins
from browser.unusual_patterns import processar_historico_da_pasta
from shared.exporter import ExportFormat, export_data

browser_app = typer.Typer(
    help="Conjunto de ferramentas para extrair e processar artefatos de navegadores "
    "(histórico, downloads, logins, favicons/screens e análises de padrões)."
)


@browser_app.command(
    "history",
    help="Extrai o histórico dos navegadores especificados (Chrome, Edge, Firefox ou todos).",
)
def history(
    chrome: bool = typer.Option(False, "--chrome", help="Extrair histórico do Chrome"),
    edge: bool = typer.Option(False, "--edge", help="Extrair histórico do Edge"),
    firefox: bool = typer.Option(False, "--firefox", help="Extrair histórico do Firefox"),
    all: bool = typer.Option(False, "--all", help="Extrair histórico de todos os navegadores"),
    output_dir: Path = typer.Option(
        Path("artefatos/historico"),
        "--output-dir",
        "-o",
        help="Diretório de saída para salvar os históricos.",
        resolve_path=True,
    ),
    export: ExportFormat | None = typer.Option(
        None,
        "--export",
        "-e",
        help="Exporta os dados extraídos. Valores: json, csv.",
    ),
):
    usuario = os.getlogin()
    home = str(Path.home())

    output_dir.mkdir(parents=True, exist_ok=True)

    def _salvar_e_notificar(dados, navegador):
        if export:
            # Delega ao exporter centralizado quando --export foi passado
            stem = f"historico_{navegador.lower()}_{usuario}"
            dest = export_data(dados, fmt=export, output_dir=output_dir, stem=stem)
            typer.secho(f"✅ Histórico do {navegador} exportado em: {dest}", fg=typer.colors.GREEN)
        else:
            # Comportamento padrão: JSON inline (mantém retrocompatibilidade)
            arquivo = output_dir / f"Historico_{navegador}_{usuario}.json"
            with open(arquivo, "w", encoding="utf-8") as f:
                json.dump(dados, f, indent=4, ensure_ascii=False)
            typer.secho(f"✅ Histórico do {navegador} salvo em: {arquivo}", fg=typer.colors.GREEN)

    if all or chrome:
        caminho_chrome = os.path.join(
            home, "AppData", "Local", "Google", "Chrome", "User Data", "Default", "History"
        )
        if os.path.exists(caminho_chrome):
            typer.echo("[*] Extraindo histórico do Chrome...")
            try:
                dados = extract_google_edge_history(caminho_chrome, "Chrome", usuario)
                _salvar_e_notificar(dados, "Chrome")
            except Exception as e:
                typer.secho(f"❌ Erro ao extrair histórico do Chrome: {e}", fg=typer.colors.RED)
        else:
            typer.secho("[!] Chrome não encontrado.", fg=typer.colors.YELLOW)

    if all or edge:
        caminho_edge = os.path.join(
            home, "AppData", "Local", "Microsoft", "Edge", "User Data", "Default", "History"
        )
        if os.path.exists(caminho_edge):
            typer.echo("[*] Extraindo histórico do Edge...")
            try:
                dados = extract_google_edge_history(caminho_edge, "Edge", usuario)
                _salvar_e_notificar(dados, "Edge")
            except Exception as e:
                typer.secho(f"❌ Erro ao extrair histórico do Edge: {e}", fg=typer.colors.RED)
        else:
            typer.secho("[!] Edge não encontrado.", fg=typer.colors.YELLOW)

    if all or firefox:
        caminho_firefox_perfis = os.path.join(
            home, "AppData", "Roaming", "Mozilla", "Firefox", "Profiles"
        )
        if os.path.exists(caminho_firefox_perfis):
            for perfil in os.listdir(caminho_firefox_perfis):
                caminho_sqlite = os.path.join(caminho_firefox_perfis, perfil, "places.sqlite")
                if os.path.exists(caminho_sqlite):
                    typer.echo(f"[*] Extraindo histórico do Firefox ({perfil})...")
                    try:
                        dados = extract_firefox_history(caminho_sqlite, usuario)
                        _salvar_e_notificar(dados, f"Firefox_{perfil}")
                    except Exception as e:
                        typer.secho(
                            f"❌ Erro ao extrair histórico do Firefox ({perfil}): {e}",
                            fg=typer.colors.RED,
                        )
                    break
            else:
                typer.secho("[!] places.sqlite do Firefox não encontrado.", fg=typer.colors.YELLOW)
        else:
            typer.secho("[!] Perfis do Firefox não encontrados.", fg=typer.colors.YELLOW)


@browser_app.command(
    "downloads",
    help="Extrai registros de downloads dos navegadores e salva artefatos no diretório indicado.",
)
def downloads(
    output_dir: Path = typer.Option(
        Path("artefatos/downloads"),
        "--output-dir",
        "-o",
        help="Diretório de saída para salvar os artefatos dos downloads.",
        resolve_path=True,
    ),
    chrome: bool = typer.Option(False, "--chrome", help="Extrair downloads do Chrome"),
    edge: bool = typer.Option(False, "--edge", help="Extrair downloads do Edge"),
    firefox: bool = typer.Option(False, "--firefox", help="Extrair downloads do Firefox"),
    all: bool = typer.Option(False, "--all", help="Extrair downloads de todos os navegadores"),
):
    output_dir.mkdir(parents=True, exist_ok=True)
    typer.echo(f"📂 Salvando artefatos em: {output_dir}")

    navegadores = {"chrome": chrome, "edge": edge, "firefox": firefox}

    if all or not any(navegadores.values()):
        navegadores = {k: True for k in navegadores}

    extract_downloads_history(
        output_dir=output_dir,
        chrome=navegadores["chrome"],
        edge=navegadores["edge"],
        firefox=navegadores["firefox"],
    )

    typer.echo("✅ Extração concluída!")


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
    help="Coleta credenciais/entradas de login dos navegadores suportados e grava JSONs com os resultados.",
)
def logins(
    chrome: bool = typer.Option(False, "--chrome", help="Extrair logins do Chrome"),
    edge: bool = typer.Option(False, "--edge", help="Extrair logins do Edge"),
    all: bool = typer.Option(False, "--all", help="Extrair logins de todos os navegadores"),
    output_dir: Path = typer.Option(
        Path("artefatos/logins"),
        "--output-dir",
        "-o",
        help="Diretório para salvar os logins em JSON",
        resolve_path=True,
    ),
):
    output_dir.mkdir(parents=True, exist_ok=True)

    navegadores = {"chrome": chrome, "edge": edge}

    if all or not any(navegadores.values()):
        navegadores = {k: True for k in navegadores}

    if navegadores["chrome"]:
        typer.echo("[*] Extraindo logins do Chrome...")
        data_chrome = collect_chrome_logins()
        arquivo_chrome = output_dir / "chrome_logins.json"
        with open(arquivo_chrome, "w", encoding="utf-8") as f:
            json.dump(data_chrome, f, indent=2, ensure_ascii=False)
        typer.echo(f"✅ Logins do Chrome salvos em: {arquivo_chrome}")

    if navegadores["edge"]:
        typer.echo("[*] Extraindo logins do Edge...")
        data_edge = collect_edge_logins()
        arquivo_edge = output_dir / "edge_logins.json"
        with open(arquivo_edge, "w", encoding="utf-8") as f:
            json.dump(data_edge, f, indent=2, ensure_ascii=False)
        typer.echo(f"✅ Logins do Edge salvos em: {arquivo_edge}")


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
    output_dir.mkdir(parents=True, exist_ok=True)
    extract_words(chrome=chrome, output_dir=output_dir)
