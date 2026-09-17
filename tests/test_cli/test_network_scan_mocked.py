from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from network.cli import network_app
from shared.binary_resolver import ForenseSecurityBlockError


@pytest.fixture
def cli_runner():
    return CliRunner()


@patch("network.cli.run_go_core")
def test_network_scan_renders_rich_table(mock_run_go, cli_runner):
    """Garante que um JSON valido retornado pelo Go e desenhado em tabela Rich sem crashes."""
    mock_run_go.return_value = {
        "schema_version": "1.0",
        "status": "success",
        "command": "scan",
        "timestamp": "2026-09-17T12:00:00Z",
        "duration_ms": 142,
        "data": {
            "target": "192.168.1.100",
            "scanned_ports": 2,
            "total_open": 2,
            "open_ports": [
                {"port": 80, "protocol": "tcp", "state": "open", "service": "http", "latency_ms": 12},
                {"port": 443, "protocol": "tcp", "state": "open", "service": "https", "latency_ms": 15},
            ],
        },
    }

    result = cli_runner.invoke(network_app, ["scan", "--target", "192.168.1.100", "--ports", "80,443"])

    assert result.exit_code == 0
    assert "192.168.1.100" in result.output
    assert "80" in result.output
    assert "http" in result.output
    assert "443" in result.output
    assert "https" in result.output


@patch("network.cli.run_go_core")
def test_network_scan_handles_antivirus_block_gracefully(mock_run_go, cli_runner):
    """Garante que bloqueio por EDR/Windows Defender (WinError 5) nao gera traceback no terminal."""
    mock_run_go.side_effect = ForenseSecurityBlockError(
        "A execucao do processo foi bloqueada pelo Sistema Operacional ou Antivirus (WinError 5 / Permission Denied)."
    )

    result = cli_runner.invoke(network_app, ["scan", "--target", "127.0.0.1"])

    assert result.exit_code == 1
    assert "Traceback (most recent call last)" not in result.output
