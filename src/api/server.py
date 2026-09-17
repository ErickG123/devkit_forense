"""
Servidor REST FastAPI e Streaming SSE para o Dashboard Web (forenselab-ui).

Fornece endpoints assíncronos não bloqueantes com Server-Sent Events (SSE)
para streaming em tempo real do progresso do Go Core (stderr NDJSON) e
resultados finais (stdout JSON), além de gerenciamento de cancelamento gracioso (Graceful Abort).
"""

from __future__ import annotations

import asyncio
import json
import os
import queue
import subprocess
import sys
import threading
import uuid
from typing import AsyncGenerator, Dict, Optional

from fastapi import APIRouter, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from shared.binary_resolver import (
    get_bundled_binary_path,
    get_core_workdir,
    is_dev_mode,
    resolve_core_command,
)
from shared.engine import (
    terminate_subprocess_gracefully,
    verify_binary_integrity,
)

# Registry em memória para rastreamento de processos ativos por Job ID
# Permite cancelamento atômico (Graceful Abort) de subprocessos Go
active_scan_jobs: Dict[str, subprocess.Popen] = {}
jobs_lock = threading.Lock()

router = APIRouter(prefix="/api/v1/network/scan", tags=["Network Streaming Scan"])


class AbortScanRequest(BaseModel):
    job_id: str = Field(..., description="Identificador único do Job gerado ao iniciar a varredura")


class AbortScanResponse(BaseModel):
    job_id: str
    status: str
    message: str


from shared.process_manager import launch_core_process


def _spawn_go_scan_process(
    target: str,
    ports: str = "21,22,53,80,443,445,3306,8080",
    workers: int = 500,
    timeout_ms: int = 1000,
) -> subprocess.Popen:
    """Inicia o subprocesso do Go Core via Shared Kernel padronizado (DRY)."""
    cmd_args = [
        "--target",
        target,
        "--ports",
        ports,
        "--workers",
        str(workers),
        "--timeout",
        str(timeout_ms),
    ]
    return launch_core_process(command="scan", args=cmd_args)


async def sse_scan_generator(
    job_id: str,
    target: str,
    ports: str,
    workers: int,
    timeout_ms: int,
) -> AsyncGenerator[str, None]:
    """
    Consome o stderr (progresso NDJSON) e o stdout (resultado JSON) do Go Core
    de forma não-bloqueante para o loop do asyncio, emitindo eventos SSE padronizados.
    """
    # Inicia o processo
    proc = _spawn_go_scan_process(target=target, ports=ports, workers=workers, timeout_ms=timeout_ms)

    with jobs_lock:
        active_scan_jobs[job_id] = proc

    # Emite evento de inicialização com o Job ID
    init_event = {
        "event": "started",
        "job_id": job_id,
        "target": target,
        "ports": ports,
    }
    yield f"event: started\ndata: {json.dumps(init_event)}\n\n"

    # Fila sincronizada para transportar linhas de stderr e stdout para o generator assíncrono
    event_queue: queue.Queue[tuple[str, str]] = queue.Queue()

    def read_stderr():
        if proc.stderr:
            for line in iter(proc.stderr.readline, ""):
                event_queue.put(("stderr", line))
            proc.stderr.close()

    def read_stdout():
        if proc.stdout:
            for line in iter(proc.stdout.readline, ""):
                event_queue.put(("stdout", line))
            proc.stdout.close()

    t_err = threading.Thread(target=read_stderr, daemon=True)
    t_out = threading.Thread(target=read_stdout, daemon=True)
    t_err.start()
    t_out.start()

    stdout_lines: list[str] = []

    try:
        while True:
            # Consome eventos da fila sem bloquear o event loop do asyncio
            items_processed = 0
            while not event_queue.empty():
                stream_type, content = event_queue.get_nowait()
                items_processed += 1

                if stream_type == "stderr":
                    clean = content.strip()
                    if clean:
                        try:
                            # Tenta validar se é o NDJSON padrão do ForenseLab
                            progress_data = json.loads(clean)
                            if isinstance(progress_data, dict):
                                progress_data["job_id"] = job_id
                                yield f"event: progress\ndata: {json.dumps(progress_data)}\n\n"
                        except json.JSONDecodeError:
                            # Log em formato texto livre
                            log_evt = {"job_id": job_id, "type": "log", "msg": clean}
                            yield f"event: progress\ndata: {json.dumps(log_evt)}\n\n"

                elif stream_type == "stdout":
                    stdout_lines.append(content)

            # Verifica se o processo encerrou
            return_code = proc.poll()
            if return_code is not None and event_queue.empty():
                break

            # Libera o event loop do asyncio para outras requisições
            await asyncio.sleep(0.05)

        # Processo encerrou normalmente ou por abort
        t_err.join(timeout=1.0)
        t_out.join(timeout=1.0)

        full_stdout = "".join(stdout_lines).strip()

        if return_code == 0:
            try:
                final_data = json.loads(full_stdout)
            except json.JSONDecodeError:
                final_data = {"status": "success", "raw": full_stdout}

            done_event = {
                "event": "done",
                "job_id": job_id,
                "status": "completed",
                "data": final_data,
            }
            yield f"event: done\ndata: {json.dumps(done_event)}\n\n"
        else:
            # Processo terminou com erro ou cancelamento
            error_event = {
                "event": "error",
                "job_id": job_id,
                "status": "aborted" if return_code in (-15, 1, 3221225786) else "failed",
                "exit_code": return_code,
                "message": full_stdout or "O processo foi encerrado ou cancelado.",
            }
            yield f"event: error\ndata: {json.dumps(error_event)}\n\n"

    except (asyncio.CancelledError, GeneratorExit):
        # Caso a conexão HTTP seja encerrada pelo cliente (navegador fechou a aba)
        terminate_subprocess_gracefully(proc)
        raise
    finally:
        with jobs_lock:
            active_scan_jobs.pop(job_id, None)
        if proc.poll() is None:
            terminate_subprocess_gracefully(proc)


@router.get(
    "/stream",
    summary="Varredura de portas em tempo real via Server-Sent Events (SSE)",
    description="Dispara a varredura concorrente de portas TCP no Go Core e emite eventos SSE de progresso e resultado.",
)
async def scan_stream(
    target: str = Query(..., description="IP ou Hostname alvo da varredura"),
    ports: str = Query("21,22,53,80,443,445,3306,8080", description="Lista ou intervalo de portas (ex: 80,443 ou 1-1000)"),
    workers: int = Query(500, description="Número de workers concorrentes"),
    timeout_ms: int = Query(1000, description="Timeout por porta em ms"),
):
    job_id = f"job-{uuid.uuid4().hex[:12]}"

    return StreamingResponse(
        sse_scan_generator(
            job_id=job_id,
            target=target,
            ports=ports,
            workers=workers,
            timeout_ms=timeout_ms,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
        },
    )


@router.post(
    "/abort",
    summary="Cancela um job de varredura ativo (Graceful Abort)",
    response_model=AbortScanResponse,
)
def abort_scan(request: AbortScanRequest):
    with jobs_lock:
        proc = active_scan_jobs.get(request.job_id)

    if not proc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Nenhum processo ativo encontrado para o Job ID '{request.job_id}'. Pode já ter finalizado.",
        )

    terminate_subprocess_gracefully(proc)

    with jobs_lock:
        active_scan_jobs.pop(request.job_id, None)

    return AbortScanResponse(
        job_id=request.job_id,
        status="aborted",
        message=f"Processo do Job {request.job_id} cancelado com sucesso.",
    )


# Criação e configuração do aplicativo FastAPI principal
def create_app() -> FastAPI:
    app = FastAPI(
        title="ForenseLab Streaming API",
        description="Servidor de Streaming e Controle IPC para o Dashboard Angular (forenselab-ui)",
        version="2.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)

    # Rota compatível simplificada /api/scan para integrações rápidas
    @app.get("/api/scan")
    async def legacy_scan_stream(
        target: str = Query(..., description="Alvo do scan"),
        ports: str = Query("21,22,80,443,8080", description="Portas para escanear"),
    ):
        job_id = f"job-{uuid.uuid4().hex[:8]}"
        return StreamingResponse(
            sse_scan_generator(job_id=job_id, target=target, ports=ports, workers=300, timeout_ms=800),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )

    return app


app = create_app()
