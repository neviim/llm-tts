"""Fixtures globais para isolamento dos testes."""
import pytest
from unittest.mock import patch


@pytest.fixture(autouse=True)
def isolate_config():
    """Garante que nenhum teste leia ou escreva no config.yaml real em disco."""
    with patch("tts_ptbr._carregar_config", return_value={}):
        yield
