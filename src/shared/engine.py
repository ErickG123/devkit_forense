"""
Motor de Execução e Orquestração IPC (Python <-> Go Core).

Implementa a invocação de subprocessos Go com streaming de progresso em tempo real via stderr (NDJSON)
e captura do resultado estruturado via stdout (JSON ou streaming NDJSON generator),
além de proteções críticas de produção:
  - Graceful shutdown capturando KeyboardInterrupt com sinal seguro (SIGTERM / CTRL_BREAK).
  - Anti-tampering com validação de hash SHA-256 do binário Go pré-execução.
  - Leitor gerador Memory Safe para streaming de milhões de registros em O(1) de RAM.
  - Repasse automático da flag --debug para geração de trilha de auditoria forense_debug.log.
"""

from __future__ import annotations

import collections.abc
import hashlib
import json
import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Generator, Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)

from shared.binary_resolver import (
    ForenseBinaryNotFoundError,
    ForenseSecurityBlockError,
    get_bundled_binary_path,
    get_core_workdir,
    is_dev_mode,
    resolve_core_command,
)

# Configura console com suporte seguro a terminais Windows (evita falhas de codepage cp1252 com braille)
console = Console(legacy_windows=False if sys.platform == "win32" else None)


class ForenseCoreError(Exception):
    """Classe base para erros originados no Go Core."""
    pass


class ForenseTimeoutError(ForenseCoreError):
    """Lançada quando a operação do Go Core excede o timeout estipulado."""
    pass


class ForenseProtocolError(ForenseCoreError):
    """Lançada quando a saída de stdout não está em conformidade com o contrato JSON."""
    pass


class ForenseExecutionError(ForenseCoreError):
    """Lançada quando o processo encerra com código diferente de zero."""
    def __init__(self, message: str, exit_code: int, error_data: Optional[dict] = None):
        super().__init__(message)
        self.exit_code = exit_code
        self.error_data = error_data or {}


class ForenseSecurityTamperingError(ForenseCoreError):
    """Lançada quando o hash SHA-256 do binário não corresponde à assinatura confiável."""
    pass


# Dicionário de hashes auditados injetados pelo pipeline de CI/CD (ou sobrescritos por env var)
EXPECTED_CORE_HASHES = {
    "windows-amd64": os.getenv("FORENSE_CORE_HASH_WINDOWS", ""),
    "linux-amd64": os.getenv("FORENSE_CORE_HASH_LINUX", ""),
    "darwin-arm64": os.getenv("FORENSE_CORE_HASH_DARWIN", ""),
}


def verify_binary_integrity(binary_path: Path) -> str:
    """
    Calcula e valida o hash SHA-256 do executável antes de qualquer chamada Popen.
    Lança ForenseSecurityTamperingError se houver discrepância detectada.
    """
    if not binary_path.is_file():
        raise ForenseBinaryNotFoundError(f"Binário não encontrado para checagem: {binary_path}")

    hasher = hashlib.sha256()
    with open(binary_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)

    calculated_hash = hasher.hexdigest().lower()

    # Checa env var explícita de integridade ou configuração CI/CD
    expected = os.getenv("FORENSE_EXPECTED_HASH", "").lower()
    if not expected:
        # Se houver hash configurado para a arquitetura atual, usa-o
        platform_key = "windows-amd64" if sys.platform == "win32" else "linux-amd64"
        expected = EXPECTED_CORE_HASHES.get(platform_key, "").lower()

    if expected and expected != "official_build_hash_here" and calculated_hash != expected:
        raise ForenseSecurityTamperingError(
            f"[CRITICAL SECURITY ALERT] Violação de integridade detectada (Anti-Tampering)!\n"
            f"O binário '{binary_path.name}' foi adulterado ou corrompido.\n"
            f"Hash Esperado: {expected}\n"
            f"Hash Calculado: {calculated_hash}"
        )

    return calculated_hash


def terminate_subprocess_gracefully(proc: subprocess.Popen, grace_seconds: float = 3.0) -> None:
    """
    Envia sinal de término limpo (SIGTERM ou CTRL_BREAK_EVENT) e concede
    um período de graça para o Go Core desalocar recursos e fechar locks SQLite.
    Se o processo não responder, finaliza forçadamente com kill().
    """
    if proc.poll() is not None:
        return

    try:
        if sys.platform == "win32":
            # No Windows com processo iniciado em novo grupo, enviamos CTRL_BREAK_EVENT
            proc.send_signal(signal.CTRL_BREAK_EVENT)
        else:
            proc.send_signal(signal.SIGTERM)
    except OSError:
        pass

    start_grace = time.time()
    while time.time() - start_grace < grace_seconds:
        if proc.poll() is not None:
            return
        time.sleep(0.1)

    # Força término se ainda estiver zumbi após o período de graça
    try:
        proc.kill()
    except OSError:
        pass


def _handle_mock_execution(
    command: str,
    args: Optional[list[str]],
    task_name: str,
    show_progress: bool,
) -> dict[str, Any]:
    """Simula a execução do Go Core através de arquivos JSON em tests/mocks/."""
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[2]
    mock_file = repo_root / "tests" / "mocks" / f"mock_network_{command}.json"

    if not mock_file.is_file():
        mock_file = repo_root / "tests" / "mocks" / f"mock_{command}.json"

    if show_progress:
        with Progress(
            SpinnerColumn("line"),
            TextColumn("[bold cyan]{task.fields[task_name]}[/]"),
            BarColumn(bar_width=None),
            TaskProgressColumn(),
            TextColumn("[dim yellow]{task.description}[/]"),
            TimeElapsedColumn(),
            console=console,
            transient=False,
        ) as progress_bar:
            t = progress_bar.add_task("Simulando execução (Mock)...", total=100.0, task_name=task_name)
            progress_bar.update(t, completed=50.0, description="Processando mock data...")
            time.sleep(0.05)
            progress_bar.update(t, completed=100.0, description="Finalizado (Mock).")

    if mock_file.is_file():
        return json.loads(mock_file.read_text(encoding="utf-8"))

    return {
        "schema_version": "1.0",
        "status": "success",
        "command": command,
        "timestamp": "2026-09-17T12:00:00Z",
        "duration_ms": 10,
        "data": {
            "mock": True,
            "command": command,
            "target": "127.0.0.1",
            "open_ports": [
                {"port": 80, "protocol": "tcp", "state": "open", "service": "http", "latency_ms": 1}
            ],
            "active_hosts": [
                {"ip": "127.0.0.1", "status": "ONLINE", "method": "tcp-ack", "port": 80, "latency_ms": 1}
            ],
        },
    }


def run_go_core(
    command: str,
    args: Optional[list[str]] = None,
    task_name: str = "Executando tarefa forense",
    timeout: float = 60.0,
    show_progress: bool = True,
    debug: bool = False,
    benchmark: bool = False,
) -> dict[str, Any]:
    """
    Executa um comando no Go Core gerenciando a comunicação entre processos (IPC).

    Parâmetros:
        command: Subcomando a ser executado pelo binário (ex: 'mock', 'scan').
        args: Argumentos adicionais repassados ao comando.
        task_name: Rótulo exibido na barra de progresso do Rich.
        timeout: Tempo limite máximo em segundos antes do encerramento forçado.
        show_progress: Se True, renderiza a barra de progresso no terminal.
        debug: Se True, repassa a flag --debug ao Go Core para auditoria em forense_debug.log.
        benchmark: Se True, monitora tempo (clock/CPU) e RAM (psutil), salvando em benchmark_results.json.

    Retorna:
        dict: O envelope JSON completo retornado pelo binário no stdout.
    """
    # 0. Interceptação de Mock para Testes (CI/CD sem binário Go compilado)
    if os.getenv("FORENSE_MOCK", "0").lower() in ("1", "true", "yes"):
        return _handle_mock_execution(command, args, task_name, show_progress)

    # 1. Inicia o subprocesso utilizando a fábrica centralizada (DRY / Shared Kernel)
    from shared.process_manager import launch_core_process

    proc = launch_core_process(
        command=command,
        args=args,
        debug=debug,
        benchmark=benchmark,
    )

    # 3. Threads de leitura para evitar deadlocks de buffer em pipes do SO
    stdout_chunks: list[str] = []
    stderr_raw_lines: list[str] = []

    def read_stdout():
        if proc.stdout:
            for line in iter(proc.stdout.readline, ""):
                stdout_chunks.append(line)
            proc.stdout.close()

    stdout_thread = threading.Thread(target=read_stdout, daemon=True)
    stdout_thread.start()

    # Monitoramento de Benchmark (CPU / RAM Peak via psutil)
    peak_ram_bytes = 0
    stop_sampler = threading.Event()

    def sample_memory():
        nonlocal peak_ram_bytes
        try:
            import psutil
            p = psutil.Process(proc.pid)
            while not stop_sampler.is_set():
                try:
                    mem = p.memory_info().rss
                    if mem > peak_ram_bytes:
                        peak_ram_bytes = mem
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    break
                time.sleep(0.02)
        except Exception:
            pass

    sampler_thread = None
    is_benchmark_active = benchmark or os.getenv("FORENSE_BENCHMARK") == "1"
    perf_start = time.perf_counter()
    start_time = time.time()

    if is_benchmark_active:
        sampler_thread = threading.Thread(target=sample_memory, daemon=True)
        sampler_thread.start()

    if show_progress:
        progress_bar = Progress(
            SpinnerColumn("line"),
            TextColumn("[bold cyan]{task.fields[task_name]}[/]"),
            BarColumn(bar_width=None),
            TaskProgressColumn(),
            TextColumn("[dim yellow]{task.description}[/]"),
            TimeElapsedColumn(),
            console=console,
            transient=False,
        )
    else:
        progress_bar = None

    try:
        if progress_bar:
            with progress_bar:
                task_id = progress_bar.add_task(
                    description="Aguardando inicialização...",
                    total=100.0,
                    completed=0.0,
                    task_name=task_name,
                )

                if proc.stderr:
                    for line in iter(proc.stderr.readline, ""):
                        stderr_raw_lines.append(line)
                        cleaned_line = line.strip()
                        if not cleaned_line:
                            continue

                        try:
                            event = json.loads(cleaned_line)
                            if isinstance(event, dict) and event.get("type") == "progress":
                                percent = float(event.get("percent_done", event.get("percent", 0.0)))
                                msg = event.get("msg", "")
                                progress_bar.update(
                                    task_id,
                                    completed=percent,
                                    description=msg,
                                )
                        except (json.JSONDecodeError, ValueError):
                            pass

                        if (time.time() - start_time) > timeout:
                            terminate_subprocess_gracefully(proc)
                            raise ForenseTimeoutError(
                                f"A operação '{task_name}' excedeu o limite de {timeout}s."
                            )

                    proc.stderr.close()
        else:
            if proc.stderr:
                for line in iter(proc.stderr.readline, ""):
                    stderr_raw_lines.append(line)
                    if (time.time() - start_time) > timeout:
                        terminate_subprocess_gracefully(proc)
                        raise ForenseTimeoutError(
                            f"A operação '{task_name}' excedeu o limite de {timeout}s."
                        )
                proc.stderr.close()

    except (KeyboardInterrupt, BaseException):
        # Graceful Shutdown em caso de Ctrl+C ou interrupção no Python
        terminate_subprocess_gracefully(proc)
        raise
    finally:
        stop_sampler.set()
        if sampler_thread and sampler_thread.is_alive():
            sampler_thread.join(timeout=1.0)

    perf_total_sec = time.perf_counter() - perf_start
    stdout_thread.join(timeout=5.0)
    return_code = proc.wait(timeout=5.0)

    raw_stdout = "".join(stdout_chunks).strip()
    raw_stderr = "".join(stderr_raw_lines).strip()

    parsed_json: Optional[dict[str, Any]] = None
    if raw_stdout:
        try:
            parsed_json = json.loads(raw_stdout)
        except json.JSONDecodeError as err:
            raise ForenseProtocolError(
                f"Contrato violado: O núcleo Go não retornou um JSON válido no stdout.\n"
                f"Saída recebida:\n{raw_stdout}\n"
                f"Stderr recebido:\n{raw_stderr}"
            ) from err

    if return_code != 0:
        error_info = {}
        error_msg = f"O processo encerrou com código de erro {return_code}."
        if parsed_json and isinstance(parsed_json, dict) and "error" in parsed_json:
            error_info = parsed_json.get("error", {})
            error_msg = error_info.get("message", error_msg)
        elif raw_stderr:
            error_msg = f"{error_msg} Detalhes: {raw_stderr}"

        raise ForenseExecutionError(
            message=error_msg,
            exit_code=return_code,
            error_data=error_info,
        )

    if not parsed_json:
        raise ForenseProtocolError(
            f"O processo encerrou com sucesso (exit 0), mas o stdout estava vazio.\n"
            f"Stderr: {raw_stderr}"
        )

    # Se benchmark ativo, consolida métricas comparativas em benchmark_results.json
    if is_benchmark_active:
        go_metrics = parsed_json.get("metrics") or {}
        benchmark_entry = {
            "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "command": command,
            "task_name": task_name,
            "python_duration_sec": round(perf_total_sec, 4),
            "python_peak_ram_mb": round(peak_ram_bytes / (1024 * 1024), 2),
            "go_duration_ms": parsed_json.get("duration_ms", 0),
            "go_alloc_mb": round(go_metrics.get("alloc_bytes", 0) / (1024 * 1024), 2),
            "go_sys_mb": round(go_metrics.get("sys_bytes", 0) / (1024 * 1024), 2),
            "go_num_gc": go_metrics.get("num_gc", 0),
        }

        bench_file = Path("benchmark_results.json")
        history = []
        if bench_file.is_file():
            try:
                history = json.loads(bench_file.read_text(encoding="utf-8"))
                if not isinstance(history, list):
                    history = []
            except Exception:
                history = []
        history.append(benchmark_entry)
        bench_file.write_text(json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8")

        console.print(
            f"[bold cyan][BENCHMARK][/bold cyan] [green]Comando:[/] {command} | "
            f"[green]Tempo Total:[/] {benchmark_entry['python_duration_sec']}s (Go: {benchmark_entry['go_duration_ms']}ms) | "
            f"[green]Pico RAM Processo:[/] {benchmark_entry['python_peak_ram_mb']} MB | "
            f"[green]Go Heap Alloc:[/] {benchmark_entry['go_alloc_mb']} MB"
        )

    return parsed_json


def stream_go_core(
    command: str,
    args: Optional[list[str]] = None,
    timeout: Optional[float] = None,
    debug: bool = False,
) -> Generator[dict[str, Any], None, None]:
    """
    Consome o stdout do Go Core em tempo real via streaming NDJSON.
    Utiliza o padrão gerador (yield), garantindo consumo de memória O(1) mesmo
    com milhões de registros.
    """
    from shared.process_manager import launch_core_process

    proc = launch_core_process(
        command=command,
        args=args,
        debug=debug,
        ndjson=True,
    )

    try:
        if proc.stdout:
            for line in iter(proc.stdout.readline, ""):
                clean_line = line.strip()
                if not clean_line:
                    continue
                try:
                    record = json.loads(clean_line)
                    yield record
                except json.JSONDecodeError:
                    continue
    except (KeyboardInterrupt, GeneratorExit):
        terminate_subprocess_gracefully(proc)
        raise
    finally:
        if proc.poll() is None:
            terminate_subprocess_gracefully(proc)
