"""
Entrypoint dual do ForenseLab.

Este módulo serve DOIS propósitos conforme o modo de execução:

  1. CLI (Typer) — quando invocado diretamente:
        python src/main.py
        forensic-cli network scan --target 192.168.1.1

  2. API REST (FastAPI + Uvicorn) — quando invocado com --api:
        python src/main.py --api
        uvicorn main:app --reload (a partir de src/)

A separação é feita por argumento de linha de comando, mantendo
ambas as interfaces no mesmo entrypoint sem acoplamento entre elas.
"""

import sys
import webbrowser

import uvicorn

# ─────────────────────────────────────────────────────────────────────────────
# FastAPI application — instanciada sempre (necessária para `uvicorn main:app`)
# ─────────────────────────────────────────────────────────────────────────────
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from browser.api import router as browser_router
from mail.api import router as mail_router
from network.api import router as network_router
from shared.config import get as cfg_get
from shared.logger import configure_verbose, get_logger
from shared.ui_installer import UI_DIR, download_and_install_ui, is_ui_installed

logger = get_logger(__name__)

app = FastAPI(
    title="ForenseLab API",
    description=(
        "API REST do DevKit Forense para análise de evidências digitais.\n\n"
        "Cada grupo de endpoints corresponde a uma feature vertical do projeto:\n"
        "- **/network** — Port scan, ping sweep, DNS recon, traceroute, IP info\n"
        "- **/browser** — Extração de artefatos de navegadores (em breve)\n"
        "- **/email**   — Análise forense de e-mails (em breve)\n"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — permite consumo pelo SPA (restringir `allow_origins` em produção)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registro dos roteadores por feature
app.include_router(network_router)
app.include_router(browser_router)
app.include_router(mail_router)

if is_ui_installed():
    app.mount("/", StaticFiles(directory=str(UI_DIR), html=True), name="ui")


@app.get("/api/health", tags=["Root"])
def root():
    return {
        "service": "ForenseLab API",
        "status": "online",
        "docs": "/docs",
        "redoc": "/redoc",
    }


# ─────────────────────────────────────────────────────────────────────────────
# CLI application (Typer) — instanciada apenas quando necessário
# ─────────────────────────────────────────────────────────────────────────────


def _build_cli():
    """Constrói e retorna o app Typer. Importações pesadas ficam lazy."""
    import typer

    from browser.cli import browser_app
    from mail.cli import email_app
    from network.cli import network_app
    from shared.describe import describe_app
    from shared.utils_cmd import utils_app

    cli = typer.Typer(
        name="forensic-cli",
        help=(
            "ForenseLab — DevKit Forense para análise de evidências digitais.\n\n"
            "Use [bold]--verbose[/bold] / [bold]-v[/bold] para habilitar o modo de "
            "rastreamento completo (DEBUG) no terminal.\n\n"
            "Use [bold]--api[/bold] para subir o servidor REST via Uvicorn."
        ),
        rich_markup_mode="rich",
    )

    @cli.callback()
    def global_options(
        verbose: bool = typer.Option(
            False,
            "--verbose",
            "-v",
            help=(
                "Habilita o modo verbose: exibe logs de DEBUG no terminal. "
                "Por padrão apenas WARNING/ERROR são gravados em [italic]forenselab.log[/italic]."
            ),
            is_eager=False,
        ),
    ) -> None:
        """Opções globais — executadas antes de qualquer sub-comando."""
        configure_verbose(verbose)

    cli.add_typer(network_app, name="network", help="Ferramentas para análise e operações em redes")
    cli.add_typer(
        browser_app,
        name="browser",
        help="Ferramentas para coleta e análise de dados de navegadores",
    )
    cli.add_typer(
        email_app,
        name="email",
        help="Ferramentas para análise e manipulação de dados de e-mail",
    )
    cli.add_typer(utils_app, name="utils", help="Funções utilitárias de apoio ao sistema")
    cli.add_typer(
        describe_app,
        name="describe",
        help="Explicações detalhadas sobre as funcionalidades disponíveis",
    )

    @cli.command(name="gui")
    def gui():
        """Inicializa a interface gráfica web e o servidor FastAPI embutido."""
        if not is_ui_installed():
            typer.echo("A interface gráfica requer o download de arquivos estáticos.")
            typer.confirm("Deseja baixar e instalar a interface gráfica agora?", abort=True)
            download_and_install_ui()
            app.mount("/", StaticFiles(directory=str(UI_DIR), html=True), name="ui")

        webbrowser.open("http://127.0.0.1:8000")
        uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")

    cli()


# ─────────────────────────────────────────────────────────────────────────────
# Entrypoint
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if "--api" in sys.argv:
        # Remove o argumento para que o Uvicorn não o receba
        sys.argv.remove("--api")
        import uvicorn

        host = cfg_get("api", "host", default="0.0.0.0")
        port = int(cfg_get("api", "port", default=8000))
        reload = "--reload" in sys.argv

        logger.info("Iniciando ForenseLab API em %s:%d (reload=%s)", host, port, reload)
        uvicorn.run("main:app", host=host, port=port, reload=reload)
    else:
        _build_cli()
