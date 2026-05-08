"""Testes para validação de argumentos CLI e integração com mocks."""
import sys
import pytest
import numpy as np
from unittest.mock import patch, MagicMock

from tts_ptbr import main, falar, processar_batch


# ── Validação de argumentos ───────────────────────────────────────────────────

class TestValidacaoArgs:
    def test_sem_reproduzir_sem_salvar_erro(self):
        with patch("sys.argv", ["tts_ptbr.py", "--sem-reproduzir", "Olá"]):
            with pytest.raises(SystemExit) as exc:
                main()
            assert exc.value.code == 2

    def test_juntar_sem_salvar_erro(self, tmp_path):
        arq = tmp_path / "f.txt"
        arq.write_text("linha\n")
        with patch("sys.argv", ["tts_ptbr.py", "--juntar", "--arquivo", str(arq)]):
            with pytest.raises(SystemExit) as exc:
                main()
            assert exc.value.code == 2


# ── --listar-vozes ────────────────────────────────────────────────────────────

class TestListarVozes:
    def test_listar_vozes_edge(self, capsys):
        with patch("sys.argv", ["tts_ptbr.py", "--listar-vozes"]):
            main()
        saida = capsys.readouterr().out
        assert "francisca" in saida
        assert "antonio" in saida
        assert "thalita" in saida

    def test_listar_vozes_pocket(self, capsys):
        with patch("sys.argv", ["tts_ptbr.py", "--engine", "pocket", "--listar-vozes"]):
            main()
        saida = capsys.readouterr().out
        assert "rafael" in saida

    def test_listar_vozes_indica_padrao(self, capsys):
        with patch("sys.argv", ["tts_ptbr.py", "--listar-vozes"]):
            main()
        saida = capsys.readouterr().out
        assert "padrão" in saida


# ── falar() com mock do engine ────────────────────────────────────────────────

AUDIO_FAKE = np.zeros(22050, dtype=np.float32)
SR_FAKE = 22050


class TestFalar:
    def _mock_edge(self):
        return patch("tts_ptbr._sintetizar_edge", return_value=(AUDIO_FAKE, SR_FAKE))

    def test_chama_engine_edge(self):
        with self._mock_edge() as mock_edge, \
             patch("tts_ptbr.sd.play"), patch("tts_ptbr.sd.wait"):
            falar("Olá", "edge", "francisca")
            mock_edge.assert_called_once_with("Olá", "francisca")

    def test_preprocessar_expande_antes_de_chamar_engine(self):
        with self._mock_edge() as mock_edge, \
             patch("tts_ptbr.sd.play"), patch("tts_ptbr.sd.wait"):
            falar("Dr. Silva", "edge", "francisca", preprocessar=True)
            texto_enviado = mock_edge.call_args[0][0]
            assert "Doutor" in texto_enviado
            assert "Dr." not in texto_enviado

    def test_salva_arquivo_wav(self, tmp_path):
        destino = str(tmp_path / "saida.wav")
        with self._mock_edge(), \
             patch("tts_ptbr.sd.play"), patch("tts_ptbr.sd.wait"):
            falar("Olá", "edge", "francisca", salvar=destino, reproduzir=False)
        assert (tmp_path / "saida.wav").exists()

    def test_sem_reproduzir_nao_chama_sd_play(self, tmp_path):
        destino = str(tmp_path / "saida.wav")
        with self._mock_edge(), \
             patch("tts_ptbr.sd.play") as mock_play, \
             patch("tts_ptbr.sd.wait"):
            falar("Olá", "edge", "francisca", salvar=destino, reproduzir=False)
            mock_play.assert_not_called()

    def test_reproduzir_chama_sd_play(self):
        with self._mock_edge(), \
             patch("tts_ptbr.sd.play") as mock_play, \
             patch("tts_ptbr.sd.wait"):
            falar("Olá", "edge", "francisca")
            mock_play.assert_called_once()


# ── processar_batch() ─────────────────────────────────────────────────────────

class TestProcessarBatch:
    def _mock_sintetizar(self):
        return patch("tts_ptbr._sintetizar", return_value=(AUDIO_FAKE, SR_FAKE))

    def test_gera_arquivos_numerados(self, tmp_path):
        textos = ["Frase um", "Frase dois", "Frase três"]
        with self._mock_sintetizar(), \
             patch("tts_ptbr.sd.play"), patch("tts_ptbr.sd.wait"):
            processar_batch(
                textos, "edge", "francisca",
                salvar=str(tmp_path / "frase.wav"),
                reproduzir=False,
            )
        arquivos = sorted(tmp_path.glob("frase_*.wav"))
        assert len(arquivos) == 3
        assert arquivos[0].name == "frase_001.wav"
        assert arquivos[2].name == "frase_003.wav"

    def test_juntar_gera_arquivo_unico(self, tmp_path):
        textos = ["Linha 1", "Linha 2"]
        destino = str(tmp_path / "completo.wav")
        with self._mock_sintetizar(), \
             patch("tts_ptbr.sd.play"), patch("tts_ptbr.sd.wait"):
            processar_batch(
                textos, "edge", "francisca",
                salvar=destino,
                reproduzir=False,
                juntar=True,
            )
        assert (tmp_path / "completo.wav").exists()
        assert not list(tmp_path.glob("completo_*.wav"))

    def test_preprocessar_em_batch(self):
        textos = ["Dr. Silva", "50%"]
        chamadas = []
        def fake_sintetizar(texto, engine, voz, idioma="pt"):
            chamadas.append(texto)
            return AUDIO_FAKE, SR_FAKE

        with patch("tts_ptbr._sintetizar", side_effect=fake_sintetizar), \
             patch("tts_ptbr.sd.play"), patch("tts_ptbr.sd.wait"):
            processar_batch(textos, "edge", "francisca", preprocessar=True, reproduzir=True)

        assert "Doutor" in chamadas[0]
        assert "por cento" in chamadas[1]
