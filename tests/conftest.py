"""Fixtures globais para isolamento dos testes."""
import pytest
from unittest.mock import patch


@pytest.fixture(autouse=True)
def isolate_config():
    """Garante que nenhum teste leia config.yaml ou o cache de áudio em disco."""
    with patch("tts_ptbr._carregar_config", return_value={}), \
         patch("tts_ptbr._cache_buscar", return_value=None), \
         patch("tts_ptbr._cache_salvar"):
        yield
