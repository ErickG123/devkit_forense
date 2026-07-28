from main import _build_cli


def test_global_help(runner):
    app = _build_cli()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "ForenseLab" in result.stdout
    assert "network" in result.stdout


def test_network_help(runner):
    app = _build_cli()
    result = runner.invoke(app, ["network", "--help"])
    assert result.exit_code == 0
    assert "scan" in result.stdout
    assert "map" in result.stdout
