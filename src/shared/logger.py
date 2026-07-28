"""
Módulo de logging estruturado do ForenseLab.

Expõe um único logger central (`get_logger`) configurado com dois handlers:
- FileHandler  → sempre ativo, nível WARNING, salva em `forenselab.log` na raiz.
- RichHandler  → ativo condicionalmente via `configure_verbose(True)`, nível DEBUG.

Uso nos módulos da feature:
    from shared.logger import get_logger
    logger = get_logger(__name__)
    logger.info("Iniciando varredura...")

Ativação do modo verbose (chamada pelo callback global do Typer em src/main.py):
    from shared.logger import configure_verbose
    configure_verbose(True)
"""

import logging
from pathlib import Path

from rich.logging import RichHandler

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

LOG_FILE = Path(__file__).resolve().parents[2] / "forenselab.log"
_LOGGER_NAME = "forenselab"
_FORMAT = "%(name)s | %(message)s"
_DATE_FORMAT = "[%H:%M:%S]"

# ---------------------------------------------------------------------------
# Construção interna do logger raiz
# ---------------------------------------------------------------------------


def _build_logger() -> logging.Logger:
    """Constrói e retorna o logger raiz do projeto (executado uma única vez)."""
    logger = logging.getLogger(_LOGGER_NAME)
    logger.setLevel(logging.DEBUG)  # handlers filtram por nível, não o logger raiz

    # ── File Handler ─────────────────────────────────────────────────────────
    # Silencioso: apenas WARNING+ vai para o disco, sempre ativo.
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.WARNING)
    file_handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    # ── Rich Console Handler ─────────────────────────────────────────────────
    # Por padrão exibe apenas WARNING+ no terminal.
    # `configure_verbose(True)` abaixa o nível para DEBUG.
    rich_handler = RichHandler(
        level=logging.WARNING,
        show_time=True,
        show_level=True,
        show_path=True,
        rich_tracebacks=True,
        tracebacks_show_locals=True,
        markup=True,
        log_time_format=_DATE_FORMAT,
    )
    rich_handler.setFormatter(logging.Formatter(fmt=_FORMAT, datefmt=_DATE_FORMAT))

    logger.addHandler(file_handler)
    logger.addHandler(rich_handler)

    return logger


# Logger raiz — singleton criado uma única vez na importação do módulo
_root_logger = _build_logger()


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------


def get_logger(name: str) -> logging.Logger:
    """
    Retorna um logger filho do logger raiz `forenselab`.

    Parameters
    ----------
    name:
        Convencionalmente `__name__` do módulo que está importando.

    Returns
    -------
    logging.Logger
        Logger filho já vinculado ao handler Rich e ao FileHandler.
    """
    return logging.getLogger(f"{_LOGGER_NAME}.{name}")


def configure_verbose(enabled: bool) -> None:
    """
    Ativa ou desativa o modo verbose na saída do terminal (RichHandler).

    Deve ser chamado pelo callback global do Typer **antes** de qualquer
    comando ser executado.

    Parameters
    ----------
    enabled:
        True  → DEBUG  (exibe todo o rastreamento no terminal).
        False → WARNING (apenas erros e avisos aparecem no terminal).
    """
    target_level = logging.DEBUG if enabled else logging.WARNING

    for handler in _root_logger.handlers:
        if isinstance(handler, RichHandler):
            handler.setLevel(target_level)
            if enabled:
                # Emite a própria mensagem de ativação usando o logger já configurado
                _root_logger.debug(
                    "[bold green]Modo verbose ativado[/bold green] — nível DEBUG habilitado no terminal."
                )
            break
