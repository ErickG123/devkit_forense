"""
Shared Kernel: Gerenciador Centralizado de Processos Forenses (DRY / DDD).

Centraliza a resolução de binários, verificação anti-tampering,
instanciação segura de subprocessos (com isolamento de grupos de processo no Windows),
e captura padronizada de bloqueios heurísticos de Antivírus/EDR.
"""

from __future__ import annotations

import os
import subprocess
import sys
from typing import Sequence

from rich.console import Console
from rich.panel import Panel

from shared.binary_resolver import (
    ForenseBinaryNotFoundError,
    ForenseSecurityBlockError,
    get_bundled_binary_path,
    get_core_workdir,
    is_dev_mode,
    resolve_core_command,
)
from shared.engine import verify_binary_integrity

console = Console(legacy_windows=False if sys.platform == "win32" else None)


def launch_core_process(
    command: str,
    args: Sequence[str] | None = None,
    debug: bool = False,
    benchmark: bool = False,
    ndjson: bool = False,
) -> subprocess.Popen:
    """
    Fábrica única e centralizada para iniciar o subprocesso do Go Core.

    Garante:
      1. Verificação de integridade anti-tampering (SHA-256) em binários de release.
      2. Configuração correta de pipes line-buffered (stdout=PIPE, stderr=PIPE).
      3. Isolamento de processo com CREATE_NEW_PROCESS_GROUP no Windows (para envio de CTRL_BREAK gracioso).
      4. Propagação consistente de flags globais (--debug, --benchmark, --ndjson).
      5. Tratamento amigável de bloqueios de EDR/Antivírus (WinError 5 / PermissionError).
    """
    base_cmd = resolve_core_command()

    if not is_dev_mode():
        bundled_bin = get_bundled_binary_path()
        if bundled_bin.is_file():
            verify_binary_integrity(bundled_bin)

    cmd_args = list(args or [])

    # Propagação de flags globais controlada e idempotente
    if (debug or os.getenv("FORENSE_DEBUG") == "1") and "--debug" not in cmd_args:
        cmd_args.append("--debug")

    if (benchmark or os.getenv("FORENSE_BENCHMARK") == "1") and "--benchmark" not in cmd_args:
        cmd_args.append("--benchmark")

    if ndjson and "--ndjson" not in cmd_args and "--jsonl" not in cmd_args:
        cmd_args.append("--ndjson")

    full_cmd = [*base_cmd, command, *cmd_args]

    creationflags = 0
    if sys.platform == "win32":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP

    try:
        return subprocess.Popen(
            full_cmd,
            cwd=get_core_workdir(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,  # Line-buffered
            creationflags=creationflags,
        )
    except PermissionError as e:
        console.print(
            Panel(
                "[bold yellow]AVISO DE SEGURANÇA: Executável Bloqueado pelo Antivírus / EDR[/bold yellow]\n\n"
                f"[white]O Windows Defender ou o sistema operacional bloqueou a execução do binário core:\n"
                f"  [cyan]{full_cmd[0]}[/cyan]\n\n"
                "Por se tratar de um toolkit forense que executa chamadas nativas de baixo nível (DPAPI/Sockets),\n"
                "soluções de antivírus heurísticas frequentemente geram [bold red]Falsos Positivos[/bold red].\n\n"
                "[bold green]Como resolver:[/bold green]\n"
                "  1. Abra a [bold]Segurança do Windows[/bold] -> [italic]Proteção contra vírus e ameaças[/italic].\n"
                "  2. Acesse [bold]Configurações de proteção[/bold] -> [italic]Exclusões[/italic].\n"
                "  3. Adicione a pasta do projeto ou o arquivo às exceções confiáveis.",
                title="[red]Bloqueio Detectado (WinError 5 / EDR)[/red]",
                border_style="red",
            )
        )
        raise ForenseSecurityBlockError(
            f"A execução do processo foi bloqueada pelo Sistema Operacional ou Antivírus (WinError 5 / Permission Denied).\n"
            f"Comando: {' '.join(full_cmd)}\n"
            f"Detalhe: {e}"
        ) from e
    except FileNotFoundError as e:
        console.print(
            Panel(
                "[bold yellow]EXECUTÁVEL NÃO ENCONTRADO OU REMOVIDO POR QUARENTENA[/bold yellow]\n\n"
                f"[white]O arquivo [cyan]{full_cmd[0]}[/cyan] não pôde ser localizado.\n"
                "Se o binário já havia sido compilado, é muito provável que o [bold red]Windows Defender tenha colocado o arquivo em quarentena silenciosa[/bold red].\n\n"
                "[bold green]Ações recomendadas:[/bold green]\n"
                "  1. Verifique o [italic]Histórico de Proteção[/italic] da Segurança do Windows.\n"
                "  2. Se foi colocado em quarentena, clique em 'Restaurar' e 'Permitir no dispositivo'.\n"
                "  3. Em ambiente de desenvolvimento, utilize [bold]FORENSE_DEV=1[/bold] para executar via JIT Go.",
                title="[yellow]Binário Ausente / Quarentenado[/yellow]",
                border_style="yellow",
            )
        )
        raise ForenseBinaryNotFoundError(
            f"Não foi possível iniciar o comando: {full_cmd[0]}. Verifique se o executável existe ou se foi movido para quarentena."
        ) from e
