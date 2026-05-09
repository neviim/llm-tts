"""Testes para validação de argumentos CLI e integração com mocks."""
import sys
import pytest
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

from tts_ptbr import main, falar, processar_batch, _carregar_config, _salvar_config, _FilaReproducao


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


# ── --clipboard ───────────────────────────────────────────────────────────────

class TestClipboard:
    def _mock_edge(self):
        return patch("tts_ptbr._sintetizar_edge", return_value=(AUDIO_FAKE, SR_FAKE))

    def test_clipboard_fala_conteudo(self):
        with patch("sys.argv", ["tts_ptbr.py", "--clipboard"]), \
             patch("pyperclip.paste", return_value="Texto do clipboard"), \
             self._mock_edge() as mock_edge, \
             patch("tts_ptbr.sd.play"), patch("tts_ptbr.sd.wait"):
            main()
            texto_enviado = mock_edge.call_args[0][0]
            assert "Texto do clipboard" in texto_enviado

    def test_clipboard_vazio_sai_com_erro(self):
        with patch("sys.argv", ["tts_ptbr.py", "--clipboard"]), \
             patch("pyperclip.paste", return_value=""), \
             pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 1

    def test_clipboard_sem_pyperclip_sai_com_erro(self):
        import sys as _sys
        with patch("sys.argv", ["tts_ptbr.py", "--clipboard"]), \
             patch.dict(_sys.modules, {"pyperclip": None}), \
             pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 1


# ── config.yaml ───────────────────────────────────────────────────────────────

class TestConfig:
    def test_carregar_config_arquivo_ausente(self, tmp_path):
        cfg = _carregar_config(tmp_path / "inexistente.yaml")
        assert cfg == {}

    def test_salvar_e_carregar_roundtrip(self, tmp_path):
        caminho = tmp_path / "cfg.yaml"
        _salvar_config({"engine": "pocket", "idioma": "en", "velocidade": 1.5}, caminho)
        assert caminho.exists()
        cfg = _carregar_config(caminho)
        assert cfg["engine"] == "pocket"
        assert cfg["idioma"] == "en"
        assert cfg["velocidade"] == 1.5

    def test_salvar_config_cli(self):
        with patch("sys.argv", ["tts_ptbr.py", "--engine", "pocket", "--idioma", "en", "--salvar-config"]), \
             patch("tts_ptbr._salvar_config") as mock_save:
            main()
        cfg_salvo = mock_save.call_args[0][0]
        assert cfg_salvo["engine"] == "pocket"
        assert cfg_salvo["idioma"] == "en"

    def test_config_aplicado_como_default(self):
        with patch("sys.argv", ["tts_ptbr.py", "Olá"]), \
             patch("tts_ptbr._carregar_config", return_value={"engine": "edge", "idioma": "pt"}), \
             patch("tts_ptbr._sintetizar_edge", return_value=(AUDIO_FAKE, SR_FAKE)) as mock_edge, \
             patch("tts_ptbr.sd.play"), patch("tts_ptbr.sd.wait"):
            main()
        assert mock_edge.called


# ── Fila de reprodução ────────────────────────────────────────────────────────

class TestFilaReproducao:
    def test_adicionar_retorna_tamanho(self):
        fila = _FilaReproducao()
        with patch("tts_ptbr.falar"):
            n = fila.adicionar("Texto 1", {"engine": "edge", "voz": "francisca"})
        assert n >= 1

    def test_limpar_esvazia_fila(self):
        import queue as _q
        fila = _FilaReproducao()
        fila._q.put(("Texto 1", {}))
        fila._q.put(("Texto 2", {}))
        n = fila.limpar()
        assert n == 2
        assert fila.tamanho() == 0

    def test_tamanho(self):
        fila = _FilaReproducao()
        fila._q.put(("t1", {}))
        fila._q.put(("t2", {}))
        assert fila.tamanho() == 2


# ── Barra de progresso (tqdm) ─────────────────────────────────────────────────

class TestBatchTqdm:
    def _mock_sintetizar(self):
        return patch("tts_ptbr._sintetizar", return_value=(AUDIO_FAKE, SR_FAKE))

    def test_batch_com_tqdm(self, tmp_path):
        textos = ["Frase um", "Frase dois"]
        with self._mock_sintetizar(), \
             patch("tts_ptbr.sd.play"), patch("tts_ptbr.sd.wait"):
            processar_batch(
                textos, "edge", "francisca",
                salvar=str(tmp_path / "f.wav"),
                reproduzir=False,
            )
        assert len(list(tmp_path.glob("f_*.wav"))) == 2

    def test_batch_sem_tqdm_fallback(self, tmp_path):
        import sys as _sys
        textos = ["Frase um", "Frase dois"]
        with self._mock_sintetizar(), \
             patch("tts_ptbr.sd.play"), patch("tts_ptbr.sd.wait"), \
             patch.dict(_sys.modules, {"tqdm": None}):
            processar_batch(
                textos, "edge", "francisca",
                salvar=str(tmp_path / "f.wav"),
                reproduzir=False,
            )
        assert len(list(tmp_path.glob("f_*.wav"))) == 2
