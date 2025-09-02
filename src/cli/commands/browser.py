import os
import json
import typer
from pathlib import Path

from core.browser.browser_history import extract_google_edge_history, extract_firefox_history
from core.browser.downloads_history import extract_downloads_history
from core.browser.fav_screen import carregar_json, extrair_urls_validas, processar_urls
from core.browser.unusual_patterns import processar_historico_da_pasta
from core.browser.logins import collect_chrome_logins, collect_edge_logins
from core.browser.common_words import extract_words

browser_app = typer.Typer()

@browser_app.command("history")
def history(
    chrome: bool = typer.Option(False, "--chrome", help="Extrair histórico do Chrome"),
    edge: bool = typer.Option(False, "--edge", help="Extrair histórico do Edge"),
    firefox: bool = typer.Option(False, "--firefox", help="Extrair histórico do Firefox"),
    all: bool = typer.Option(False, "--all", help="Extrair histórico de todos navegadores")
):
    usuario = os.getlogin()
    home = str(Path.home())

    if all or chrome:
        caminho_chrome = os.path.join(home, "AppData", "Local", "Google", "Chrome", "User Data", "Default", "History")
        if os.path.exists(caminho_chrome):
            typer.echo("[*] Extraindo histórico do Chrome...")
            extract_google_edge_history(caminho_chrome, "Chrome", usuario)
        else:
            typer.echo("[!] Chrome não encontrado.")

    if all or edge:
        caminho_edge = os.path.join(home, "AppData", "Local", "Microsoft", "Edge", "User Data", "Default", "History")
        if os.path.exists(caminho_edge):
            typer.echo("[*] Extraindo histórico do Edge...")
            extract_google_edge_history(caminho_edge, "Edge", usuario)
        else:
            typer.echo("[!] Edge não encontrado.")

    if all or firefox:
        caminho_firefox_perfis = os.path.join(home, "AppData", "Roaming", "Mozilla", "Firefox", "Profiles")
        if os.path.exists(caminho_firefox_perfis):
            for perfil in os.listdir(caminho_firefox_perfis):
                caminho_sqlite = os.path.join(caminho_firefox_perfis, perfil, "places.sqlite")
                if os.path.exists(caminho_sqlite):
                    typer.echo(f"[*] Extraindo histórico do Firefox ({perfil})...")
                    extract_firefox_history(caminho_sqlite, usuario)
                    break
            else:
                typer.echo("[!] places.sqlite do Firefox não encontrado.")
        else:
            typer.echo("[!] Perfis do Firefox não encontrados.")

@browser_app.command("downloads")
def downloads(
    output_dir: Path = typer.Option(
        Path("artefatos/downloads"),
        "--output-dir",
        "-o",
        help="Diretório de saída para salvar os artefatos dos downloads.",
        resolve_path=True
    ),
    chrome: bool = typer.Option(False, "--chrome", help="Extrair downloads do Chrome"),
    edge: bool = typer.Option(False, "--edge", help="Extrair downloads do Edge"),
    firefox: bool = typer.Option(False, "--firefox", help="Extrair downloads do Firefox"),
    all: bool = typer.Option(False, "--all", help="Extrair downloads de todos os navegadores")
):
    output_dir.mkdir(parents=True, exist_ok=True)
    typer.echo(f"📂 Salvando artefatos em: {output_dir}")

    navegadores = {
        "chrome": chrome,
        "edge": edge,
        "firefox": firefox
    }

    if all or not any(navegadores.values()):
        navegadores = {k: True for k in navegadores}

    extract_downloads_history(
        output_dir=output_dir,
        chrome=navegadores["chrome"],
        edge=navegadores["edge"],
        firefox=navegadores["firefox"]
    )

    typer.echo("✅ Extração concluída!")

@browser_app.command("favscreen")
def favscreen(
    input_dir: Path = typer.Option(
        Path("artefatos/historico"),
        "--input-dir",
        "-i",
        help="Diretório contendo os JSONs de histórico para processar.",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True
    ),
    output_dir: Path = typer.Option(
        Path("artefatos/favscreen"),
        "--output-dir",
        "-o",
        help="Diretório de saída para salvar favicons e prints.",
        exists=False,
        file_okay=False,
        dir_okay=True,
        resolve_path=True
    )
):
    try:
        arquivos_json = [input_dir / arquivo for arquivo in os.listdir(input_dir) if arquivo.endswith(".json")]
        todas_urls = []

        for caminho in arquivos_json:
            print(f"[INFO] Carregando: {caminho}")
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

@browser_app.command("logins")
def logins(
    chrome: bool = typer.Option(False, "--chrome", help="Extrair logins do Chrome"),
    edge: bool = typer.Option(False, "--edge", help="Extrair logins do Edge"),
    all: bool = typer.Option(False, "--all", help="Extrair logins de todos os navegadores"),
    output_dir: Path = typer.Option(
        Path("artefatos/logins"),
        "--output-dir",
        "-o",
        help="Diretório para salvar os logins em JSON",
        resolve_path=True
    )
):
    output_dir.mkdir(parents=True, exist_ok=True)

    navegadores = {
        "chrome": chrome,
        "edge": edge
    }

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

@browser_app.command("patterns")
def patterns(
    input_dir: Path = typer.Option(
        Path("artefatos/historico"),
        "--input-dir",
        "-i",
        help="Diretório contendo os JSONs de histórico para analisar padrões.",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True
    ),
    output_dir: Path = typer.Option(
        Path("artefatos/patterns_output"),
        "--output-dir",
        "-o",
        help="Diretório para salvar gráficos e relatórios.",
        file_okay=False,
        dir_okay=True,
        resolve_path=True
    )
):
    try:
        output_dir.mkdir(parents=True, exist_ok=True)

        typer.echo(f"[*] Processando arquivos em: {input_dir}")
        typer.echo(f"[*] Salvando resultados em: {output_dir}")

        processar_historico_da_pasta(str(input_dir), str(output_dir))

        typer.echo("\n✅ Processamento concluído.")

    except Exception as erro:
        typer.echo(f"\n❌ Erro ao executar patterns: {erro}")

@browser_app.command("words")
def words(
    chrome: bool = typer.Option(True, "--chrome", help="Extrair palavras mais pesquisadas do Chrome"),
    output_dir: Path = typer.Option(
        Path("artefatos/words_output"),
        "--output-dir",
        "-o",
        help="Diretório para salvar o JSON com palavras mais pesquisadas",
        resolve_path=True
    )
):
    output_dir.mkdir(parents=True, exist_ok=True)

    extract_words(chrome=chrome, output_dir=output_dir)
