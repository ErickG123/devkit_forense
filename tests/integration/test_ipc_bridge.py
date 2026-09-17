import json
import os
import platform
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def compiled_go_core():
    """
    Compila o binário Go real antes de iniciar os testes de integração.
    Garante que o executável em src/bin/ corresponda à última versão do core Go.
    """
    repo_root = Path(__file__).resolve().parents[2]
    core_dir = repo_root / "core"
    bin_dir = repo_root / "src" / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)

    bin_name = "forense-core.exe" if platform.system() == "Windows" else "forense-core"
    output_binary = bin_dir / bin_name

    cmd = [
        "go",
        "build",
        "-trimpath",
        "-ldflags=-s -w",
        "-o",
        str(output_binary),
        "./cmd/forense-core",
    ]

    compile_process = subprocess.run(
        cmd,
        cwd=core_dir,
        capture_output=True,
        text=True,
    )

    if compile_process.returncode != 0:
        pytest.fail(f"Falha na compilação do Go Core para testes de integração:\n{compile_process.stderr}")

    assert output_binary.is_file(), f"Binário compilado ausente em: {output_binary}"
    return output_binary


def test_real_ipc_protocol_execution(compiled_go_core):
    """
    Testa a comunicação IPC real entre subprocesso e contrato de schema:
    1. O stderr deve conter estritamente eventos de progresso em formato NDJSON.
    2. O stdout deve retornar exclusivamente o ResponseEnvelope JSON padrão (Schema 1.0).
    """
    binary_path = compiled_go_core

    proc = subprocess.Popen(
        [str(binary_path), "mock", "--target", "127.0.0.1"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )

    stdout_raw, stderr_raw = proc.communicate(timeout=15.0)

    # 1. Valida término com código zero
    assert proc.returncode == 0, f"Processo encerrou com erro {proc.returncode}. Stderr: {stderr_raw}"

    # 2. Valida o contrato do stderr (NDJSON)
    stderr_lines = [line.strip() for line in stderr_raw.strip().splitlines() if line.strip()]
    assert len(stderr_lines) >= 5, f"Esperava pelo menos 5 eventos de progresso, obteve {len(stderr_lines)}"

    for line in stderr_lines:
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            pytest.fail(f"Linha no stderr não é NDJSON válido: {line}")

        assert event.get("type") == "progress"
        assert "percent" in event
        assert "msg" in event
        assert 0.0 <= float(event["percent"]) <= 100.0

    # 3. Valida o contrato do stdout (ResponseEnvelope JSON)
    try:
        response = json.loads(stdout_raw.strip())
    except json.JSONDecodeError:
        pytest.fail(f"stdout não retornou JSON válido.\nRecebido: {stdout_raw}")

    assert response.get("schema_version") == "1.0"
    assert response.get("status") == "success"
    assert response.get("command") == "mock"
    assert "timestamp" in response
    assert "duration_ms" in response
    assert isinstance(response.get("data"), dict)
    assert response["data"].get("status") == "COMPLETED_OK"


def test_real_network_scan_e2e_cli(compiled_go_core):
    """
    Testa o fluxo ponta a ponta: CLI Typer invocando o binario Go real
    e exibindo a tabela Rich no console sem quebrar.
    """
    from typer.testing import CliRunner
    from network.cli import network_app

    runner = CliRunner()
    # Executa scan de portas no localhost com binario Go real compilado
    result = runner.invoke(network_app, ["scan", "--target", "127.0.0.1", "--ports", "80,443"])

    assert result.exit_code == 0
    # Verifica se a tabela ou mensagem foi renderizada
    assert "127.0.0.1" in result.output
