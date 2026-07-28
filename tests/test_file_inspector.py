import os
import tempfile

import pytest


@pytest.fixture
def sample_file():
    # Setup
    temp = tempfile.NamedTemporaryFile(delete=False)
    temp.write(b"Conteudo de teste para hash.")
    temp.close()

    yield temp.name

    # Teardown
    if os.path.exists(temp.name):
        os.unlink(temp.name)


def test_file_inspector_content(sample_file):
    assert os.path.exists(sample_file)
    with open(sample_file, "rb") as f:
        content = f.read()
    assert content == b"Conteudo de teste para hash."
