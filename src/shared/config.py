"""
Módulo de configuração do ForenseLab.

Carrega `forenselab.toml` da raiz do projeto usando `tomllib` (stdlib Python 3.11+).
Expõe uma interface pública simples:

    from shared.config import cfg, get

    # Acesso direto ao dicionário completo
    ports = cfg["network"]["default_ports"]

    # Acesso seguro com fallback (nunca levanta KeyError)
    timeout = get("network", "timeout", default=5.0)
    export_dir = get("export", "default_dir", default="./artefatos")

O arquivo é lido **uma única vez** ao importar este módulo (singleton).
Se `forenselab.toml` não existir ou for inválido, um aviso é emitido e
os valores-padrão definidos em `_DEFAULTS` são usados silenciosamente.
"""

from __future__ import annotations

import logging
import tomllib
from pathlib import Path
from typing import Any

logger = logging.getLogger("forenselab.shared.config")

# ---------------------------------------------------------------------------
# Localização do arquivo de configuração
# ---------------------------------------------------------------------------

# Sobe dois níveis a partir de src/shared/config.py → raiz do projeto
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_CONFIG_PATH = _PROJECT_ROOT / "forenselab.toml"

# ---------------------------------------------------------------------------
# Valores-padrão embutidos (espelham o conteúdo de forenselab.toml)
# Garantem que a CLI funcione mesmo sem o arquivo em disco.
# ---------------------------------------------------------------------------

_DEFAULTS: dict[str, dict[str, Any]] = {
    "network": {
        "default_ports": "21,22,53,80,443,445,3306,8080",
        "timeout": 5.0,
        "max_port_range": 1024,
    },
    "browser": {
        "default_output_dir": "./artefatos/historico",
    },
    "export": {
        "default_dir": "./artefatos",
        "default_format": "json",
    },
    "logging": {
        "file_level": "WARNING",
        "log_file": "forenselab.log",
    },
}


# ---------------------------------------------------------------------------
# Carregamento (executado uma única vez na importação)
# ---------------------------------------------------------------------------


def _load() -> dict[str, Any]:
    """
    Tenta ler `forenselab.toml`.

    - Se o arquivo existir e for TOML válido → merge com _DEFAULTS
      (valores do arquivo têm precedência sobre os defaults).
    - Se não existir → retorna _DEFAULTS e emite DEBUG.
    - Se for inválido → retorna _DEFAULTS e emite WARNING com o motivo.
    """
    if not _CONFIG_PATH.exists():
        logger.debug(
            "Arquivo '%s' não encontrado. Usando configurações padrão embutidas.",
            _CONFIG_PATH,
        )
        return _DEFAULTS.copy()

    try:
        with open(_CONFIG_PATH, "rb") as fh:
            file_cfg = tomllib.load(fh)

        # Merge profundo (um nível): defaults ← arquivo
        merged: dict[str, Any] = {}
        all_sections = set(_DEFAULTS) | set(file_cfg)
        for section in all_sections:
            merged[section] = {**_DEFAULTS.get(section, {}), **file_cfg.get(section, {})}

        logger.debug("Configuração carregada de '%s'.", _CONFIG_PATH)
        return merged

    except tomllib.TOMLDecodeError as exc:
        logger.warning(
            "Erro ao parsear '%s': %s. Usando configurações padrão embutidas.",
            _CONFIG_PATH,
            exc,
        )
        return _DEFAULTS.copy()


# Singleton — lido uma única vez em tempo de importação
cfg: dict[str, Any] = _load()


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------


def get(section: str, key: str, *, default: Any = None) -> Any:
    """
    Retorna o valor de `cfg[section][key]` de forma segura.

    Nunca levanta `KeyError` — retorna `default` caso a seção ou
    a chave não existam no arquivo carregado.

    Parameters
    ----------
    section:
        Nome da seção TOML (ex: ``"network"``, ``"export"``).
    key:
        Chave dentro da seção (ex: ``"default_ports"``).
    default:
        Valor de retorno caso a seção/chave não exista.

    Examples
    --------
    >>> from shared.config import get
    >>> get("network", "default_ports")
    '21,22,53,80,443,445,3306,8080'
    >>> get("network", "inexistente", default="fallback")
    'fallback'
    """
    return cfg.get(section, {}).get(key, default)
