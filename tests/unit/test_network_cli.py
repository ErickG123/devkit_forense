from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from network.cli import network_app
from shared.binary_resolver import ForenseBinaryNotFoundError, ForenseSecurityBlockError


@pytest.fixture
def runner():
    return CliRunner()


@patch("network.cli.run_go_core")
def test_network_scan_success(mock_run_go, runner):
    """Valida se o comando scan monta a tabela Rich corretamente ao receber JSON do Go Core."""
    mock_run_go.return_value = {
        "schema_version": "1.0",
        "status": "success",
        "command": "scan",
        "timestamp": "2026-09-17T12:00:00Z",
        "duration_ms": 150,
        "data": {
            "target": "127.0.0.1",
            "scanned_ports": 2,
            "total_open": 2,
            "open_ports": [
                {"port": 80, "protocol": "tcp", "state": "open", "service": "http", "latency_ms": 5},
                {"port": 443, "protocol": "tcp", "state": "open", "service": "https", "latency_ms": 7},
            ],
        },
    }

    result = runner.invoke(network_app, ["scan", "--target", "127.0.0.1", "--ports", "80,443"])
    assert result.exit_code == 0
    assert "127.0.0.1" in result.output
    assert "80" in result.output
    assert "http" in result.output
    assert "443" in result.output
    assert "https" in result.output


@patch("network.cli.run_go_core")
def test_network_sweep_success(mock_run_go, runner):
    """Valida se o comando sweep desenha a tabela Rich de hosts ativos."""
    mock_run_go.return_value = {
        "schema_version": "1.0",
        "status": "success",
        "command": "sweep",
        "timestamp": "2026-09-17T12:00:00Z",
        "duration_ms": 300,
        "data": {
            "network": "192.168.1.0/24",
            "total_scanned": 254,
            "total_active": 1,
            "active_hosts": [
                {"ip": "192.168.1.1", "status": "ONLINE", "method": "tcp-ack", "port": 80, "latency_ms": 3}
            ],
        },
    }

    result = runner.invoke(network_app, ["sweep", "--network", "192.168.1.0/24"])
    assert result.exit_code == 0
    assert "192.168.1.1" in result.output
    assert "ONLINE" in result.output
    assert "tcp-ack" in result.output


@patch("network.cli.run_go_core")
def test_network_scan_antivirus_security_block(mock_run_go, runner):
    """Valida que erro de antivírus/permissão (WinError 5) não quebra o terminal com traceback."""
    mock_run_go.side_effect = ForenseSecurityBlockError("WinError 5: Acesso negado pelo antivírus.")

    result = runner.invoke(network_app, ["scan", "--target", "127.0.0.1"])
    assert result.exit_code == 1
    assert "Traceback (most recent call last)" not in result.output


@patch("network.cli.run_go_core")
def test_network_scan_binary_not_found(mock_run_go, runner):
    """Valida que binário ausente ou quarentenado é tratado sem traceback descontrolado."""
    mock_run_go.side_effect = ForenseBinaryNotFoundError("Binário forense-core ausente.")

    result = runner.invoke(network_app, ["scan", "--target", "127.0.0.1"])
    assert result.exit_code == 1
    assert "Traceback (most recent call last)" not in result.output
