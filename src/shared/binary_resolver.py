"""
Módulo de Resolução de Binários do ForenseLab.

Responsável por localizar o binário compilado em Go na pasta 'src/bin/'
ou fornecer o comando de execução direta ('go run') em ambiente de desenvolvimento (FORENSE_DEV=1).
"""

from __future__ import annotations

import os
import platform
import shutil
import sys
from pathlib import Path


class ForenseBinaryNotFoundError(FileNotFoundError):
    """Lançada quando o executável do Go core não é encontrado no sistema."""
    pass


class ForenseSecurityBlockError(PermissionError):
    """Lançada quando o antivírus ou SO bloqueia a execução do binário (ex: WinError 5)."""
    pass


def is_dev_mode() -> bool:
    """Verifica se a flag de desenvolvimento rápido está ativa via variável de ambiente."""
    return os.getenv("FORENSE_DEV", "0").lower() in ("1", "true", "yes")


def get_binary_name() -> str:
    """
    Retorna o nome do executável de acordo com o Sistema Operacional e Arquitetura.
    Prioriza binários com sufixo de arquitetura (gerados pelo empacotamento multiplataforma)
    e faz fallback para o nome genérico ('forense-core.exe' ou 'forense-core').
    """
    system = platform.system()
    machine = platform.machine().lower()

    if system == "Windows":
        return "forense-core.exe"
    elif system == "Darwin":
        if "arm" in machine or "aarch64" in machine:
            return "forense-core-darwin-arm64"
        return "forense-core-darwin-amd64"
    else:
        # Linux e outros sistemas POSIX
        if "arm" in machine or "aarch64" in machine:
            return "forense-core-linux-arm64"
        return "forense-core-linux-amd64"


def get_bundled_binary_path() -> Path:
    """
    Retorna o caminho absoluto esperado para o binário estático na pasta src/bin/.
    Verifica primeiro o binário específico por arquitetura; se não existir, usa o genérico.
    """
    base_src = Path(__file__).resolve().parent.parent
    bin_dir = base_src / "bin"

    # 1. Procura nome específico da plataforma e arquitetura
    arch_bin = bin_dir / get_binary_name()
    if arch_bin.is_file():
        return arch_bin

    # 2. Fallback para nomes padronizados sem sufixo
    default_name = "forense-core.exe" if platform.system() == "Windows" else "forense-core"
    return bin_dir / default_name


def get_core_workdir() -> Path | None:
    """Retorna o diretório de trabalho do Go core em modo de desenvolvimento."""
    if is_dev_mode():
        repo_root = Path(__file__).resolve().parents[2]
        core_dir = repo_root / "core"
        if core_dir.is_dir():
            return core_dir
    return None


def resolve_core_command() -> list[str]:
    """
    Resolve o comando para invocação do Go Core.

    Retorna:
        list[str]: Prefixo de comando pronto para subprocess.Popen
                   Ex: ['/path/to/src/bin/forense-core.exe']
                   ou: ['go', 'run', './cmd/forense-core']
    """
    if is_dev_mode():
        # Modo Dev: Executa via JIT com 'go run'
        go_bin = shutil.which("go")
        if not go_bin:
            raise ForenseBinaryNotFoundError(
                "FORENSE_DEV=1 está ativado, mas o executável 'go' não foi encontrado no PATH do sistema. "
                "Instale o Go ou desative o modo de desenvolvimento."
            )

        repo_root = Path(__file__).resolve().parents[2]
        core_dir = repo_root / "core"
        main_go = core_dir / "cmd" / "forense-core" / "main.go"
        if not main_go.is_file():
            raise ForenseBinaryNotFoundError(
                f"Código-fonte principal do Go não encontrado em: {main_go}"
            )
        return [go_bin, "run", "./cmd/forense-core"]

    # Modo Produção / Padrão: Usa o binário estático empacotado
    binary_path = get_bundled_binary_path()
    if not binary_path.is_file():
        raise ForenseBinaryNotFoundError(
            f"Binário forense não encontrado em: {binary_path}\n"
            "Causas comuns:\n"
            "  1. O binário ainda não foi compilado (execute: go build no módulo core).\n"
            "  2. A instalação do pacote está corrompida ou incompleta.\n"
            "  3. O executável foi removido/quarentenado pelo Windows Defender ou EDR.\n"
            "Dica: Para desenvolver sem compilar previamente, utilize FORENSE_DEV=1."
        )

    return [str(binary_path)]
