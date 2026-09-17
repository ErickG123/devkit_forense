"""
Testes unitários e de integração para o comando 'network scan' usando o sistema de Mocks.
Garante que a interface Typer e as tabelas Rich processem dados sem necessitar do binário Go compilado.
"""

import os
from typer.testing import CliRunner

from network.cli import network_app

runner = CliRunner()


def test_network_scan_with_mock(monkeypatch):
    """Verifica se o comando network scan executa com sucesso utilizando os dados do Mock."""
    monkeypatch.setenv("FORENSE_MOCK", "1")

    result = runner.invoke(
        network_app,
        ["scan", "--target", "192.168.1.50", "--ports", "80,443"],
    )

    assert result.exit_code == 0
    # Verifica elementos da tabela Rich renderizada
    assert "Resultados do Scan para 192.168.1.50" in result.output
    assert "80" in result.output
    assert "http" in result.output
    assert "443" in result.output
    assert "https" in result.output


def test_network_sweep_with_mock(monkeypatch):
    """Verifica se o comando network sweep processa os hosts ativos simulados via Mock."""
    monkeypatch.setenv("FORENSE_MOCK", "1")

    result = runner.invoke(
        network_app,
        ["sweep", "--network", "192.168.1.0/24"],
    )

    assert result.exit_code == 0
    assert "Hosts Ativos na Rede" in result.output
    assert "192.168.1.1" in result.output
    assert "192.168.1.15" in result.output
