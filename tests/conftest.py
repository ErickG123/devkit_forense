import pytest
from typer.testing import CliRunner


@pytest.fixture(scope="session")
def runner():
    return CliRunner()
