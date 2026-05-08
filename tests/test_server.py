"""Testes para a API REST (server/server.py) via TestClient."""
import io
import numpy as np
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from server.server import app

client = TestClient(app)

AUDIO_FAKE = np.zeros(22050, dtype=np.float32)
SR_FAKE = 22050


def mock_sintetizar(texto, engine, voz, idioma="pt"):
    return AUDIO_FAKE, SR_FAKE


# ── GET /health ───────────────────────────────────────────────────────────────

class TestHealth:
    def test_retorna_ok(self):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}


# ── GET /idiomas ──────────────────────────────────────────────────────────────

class TestIdiomas:
    def test_contem_idiomas_principais(self):
        r = client.get("/idiomas")
        assert r.status_code == 200
        data = r.json()
        for lang in ("pt", "en", "fr", "de", "it", "es"):
            assert lang in data["idiomas"]

    def test_padrao_e_pt(self):
        r = client.get("/idiomas")
        assert r.json()["padrao"] == "pt"


# ── GET /vozes ────────────────────────────────────────────────────────────────

class TestVozes:
    def test_edge_contem_francisca(self):
        r = client.get("/vozes?engine=edge")
        assert r.status_code == 200
        data = r.json()
        assert data["engine"] == "edge"
        assert "francisca" in data["vozes"]

    def test_pocket_contem_rafael(self):
        r = client.get("/vozes?engine=pocket")
        assert r.status_code == 200
        data = r.json()
        assert data["engine"] == "pocket"
        assert "rafael" in data["vozes"]

    def test_pocket_lista_mais_de_um_voz(self):
        r = client.get("/vozes?engine=pocket")
        assert len(r.json()["vozes"]) > 1

    def test_edge_padrao(self):
        r = client.get("/vozes")
        assert r.json()["engine"] == "edge"


# ── POST /preprocessar ────────────────────────────────────────────────────────

class TestPreprocessar:
    def test_retorna_original_e_processado(self):
        r = client.post("/preprocessar", json={"texto": "Dr. Silva"})
        assert r.status_code == 200
        data = r.json()
        assert data["original"] == "Dr. Silva"
        assert "Doutor" in data["processado"]

    def test_moeda(self):
        r = client.post("/preprocessar", json={"texto": "R$ 10,00"})
        assert "reais" in r.json()["processado"]

    def test_texto_vazio_422(self):
        r = client.post("/preprocessar", json={"texto": ""})
        assert r.status_code == 422


# ── POST /tts ─────────────────────────────────────────────────────────────────

class TestTTS:
    def _post(self, payload):
        with patch("server.server._sintetizar", side_effect=mock_sintetizar):
            return client.post("/tts", json=payload)

    def test_retorna_wav_por_padrao(self):
        r = self._post({"texto": "Olá"})
        assert r.status_code == 200
        assert r.headers["content-type"] == "audio/wav"

    def test_conteudo_nao_vazio(self):
        r = self._post({"texto": "Olá"})
        assert len(r.content) > 0

    def test_formato_mp3(self):
        r = self._post({"texto": "Olá", "formato": "mp3"})
        assert r.status_code == 200
        assert r.headers["content-type"] == "audio/mpeg"

    def test_formato_flac(self):
        r = self._post({"texto": "Olá", "formato": "flac"})
        assert r.status_code == 200
        assert r.headers["content-type"] == "audio/flac"

    def test_formato_ogg(self):
        r = self._post({"texto": "Olá", "formato": "ogg"})
        assert r.status_code == 200
        assert r.headers["content-type"] == "audio/ogg"

    def test_content_disposition(self):
        r = self._post({"texto": "Olá", "formato": "wav"})
        assert "tts.wav" in r.headers["content-disposition"]

    def test_preprocessar_expande_texto(self):
        chamadas = []

        def fake(texto, engine, voz, idioma="pt"):
            chamadas.append(texto)
            return AUDIO_FAKE, SR_FAKE

        with patch("server.server._sintetizar", side_effect=fake):
            client.post("/tts", json={"texto": "Dr. Silva", "preprocessar": True})

        assert "Doutor" in chamadas[0]

    def test_engine_invalido_422(self):
        r = self._post({"texto": "Olá", "engine": "invalido"})
        assert r.status_code == 422

    def test_formato_invalido_422(self):
        r = self._post({"texto": "Olá", "formato": "xyz"})
        assert r.status_code == 422

    def test_idioma_invalido_422(self):
        r = self._post({"texto": "Olá", "idioma": "klingon"})
        assert r.status_code == 422

    def test_velocidade_fora_do_limite_422(self):
        r = self._post({"texto": "Olá", "velocidade": 10.0})
        assert r.status_code == 422

    def test_velocidade_zero_422(self):
        r = self._post({"texto": "Olá", "velocidade": 0.0})
        assert r.status_code == 422

    def test_texto_vazio_422(self):
        r = self._post({"texto": ""})
        assert r.status_code == 422

    def test_engine_pocket(self):
        r = self._post({"texto": "Olá", "engine": "pocket"})
        assert r.status_code == 200

    def test_velocidade_aplicada(self):
        with patch("server.server._sintetizar", side_effect=mock_sintetizar), \
             patch("server.server._aplicar_velocidade", return_value=AUDIO_FAKE) as mock_vel:
            client.post("/tts", json={"texto": "Olá", "velocidade": 1.5})
            mock_vel.assert_called_once()

    def test_sample_rate_resample(self):
        with patch("server.server._sintetizar", side_effect=mock_sintetizar), \
             patch("server.server._resample", return_value=AUDIO_FAKE) as mock_rs:
            client.post("/tts", json={"texto": "Olá", "sample_rate": 44100})
            mock_rs.assert_called_once()
