"""Testes para funções utilitárias de áudio, arquivos e autenticação."""
import os
import pytest
import numpy as np
from unittest.mock import patch

import io
import sys
import tts_ptbr
from tts_ptbr import (
    _inferir_formato,
    _nome_numerado,
    _resample,
    _concatenar_audio,
    _ler_textos_arquivo,
    _ler_textos_stdin,
    _ler_token_env,
    _aplicar_velocidade,
    _normalizar,
    _processar_saida,
    _cache_key,
    _cache_buscar,
    _cache_salvar,
    _cache_limpar,
    _cache_stats,
    CACHE_DIR,
)


# ── _inferir_formato ──────────────────────────────────────────────────────────

class TestInferirFormato:
    @pytest.mark.parametrize("arquivo,esperado", [
        ("saida.wav",  "wav"),
        ("saida.flac", "flac"),
        ("saida.ogg",  "ogg"),
        ("saida.mp3",  "mp3"),
    ])
    def test_infere_pela_extensao(self, arquivo, esperado):
        assert _inferir_formato(arquivo, None) == esperado

    def test_formato_explicito_sobrepoe_extensao(self):
        assert _inferir_formato("saida.wav", "mp3") == "mp3"

    def test_sem_extensao_reconhecida_retorna_wav(self):
        assert _inferir_formato("saida", None) == "wav"
        assert _inferir_formato("saida.txt", None) == "wav"

    def test_formato_invalido_levanta_erro(self):
        with pytest.raises(ValueError, match="não suportado"):
            _inferir_formato("saida.wav", "aac")

    def test_formato_case_insensitive(self):
        assert _inferir_formato("saida.WAV", None) == "wav"
        assert _inferir_formato("saida.wav", "MP3") == "mp3"


# ── _nome_numerado ────────────────────────────────────────────────────────────

class TestNomeNumerado:
    def test_padding_minimo_tres_digitos(self):
        assert _nome_numerado("frase.wav", 1, 10) == "frase_001.wav"

    def test_dois_digitos_ainda_usa_tres(self):
        assert _nome_numerado("frase.wav", 10, 99) == "frase_010.wav"

    def test_mil_itens_usa_quatro_digitos(self):
        assert _nome_numerado("frase.wav", 1, 1000) == "frase_0001.wav"

    def test_preserva_extensao(self):
        assert _nome_numerado("audio.flac", 2, 5) == "audio_002.flac"

    def test_preserva_diretorio(self):
        assert _nome_numerado("output/frase.wav", 3, 5) == "output/frase_003.wav"


# ── _resample ─────────────────────────────────────────────────────────────────

class TestResample:
    def test_mesma_taxa_retorna_original(self):
        data = np.array([1.0, 2.0, 3.0, 4.0])
        result = _resample(data, 22050, 22050)
        np.testing.assert_array_equal(result, data)

    def test_dobra_taxa_dobra_amostras(self):
        data = np.ones(100)
        result = _resample(data, 22050, 44100)
        assert len(result) == 200

    def test_metade_taxa_metade_amostras(self):
        data = np.ones(100)
        result = _resample(data, 44100, 22050)
        assert len(result) == 50

    def test_preserva_dtype(self):
        data = np.ones(100, dtype=np.float32)
        result = _resample(data, 22050, 44100)
        assert result.dtype == np.float32


# ── _concatenar_audio ─────────────────────────────────────────────────────────

class TestConcatenarAudio:
    def test_mesma_taxa(self):
        a = (np.ones(100), 22050)
        b = (np.ones(200) * 2, 22050)
        data, sr = _concatenar_audio([a, b])
        assert sr == 22050
        assert len(data) == 300

    def test_usa_sr_do_primeiro_elemento(self):
        a = (np.ones(100), 22050)
        b = (np.ones(100), 44100)
        _, sr = _concatenar_audio([a, b])
        assert sr == 22050

    def test_reamostra_segundo_para_sr_do_primeiro(self):
        # b a 44100 Hz → reamostrado para 22050 → metade das amostras
        a = (np.ones(100), 22050)
        b = (np.ones(100), 44100)
        data, sr = _concatenar_audio([a, b])
        assert len(data) == 150  # 100 + 50


# ── _ler_textos_arquivo ───────────────────────────────────────────────────────

class TestLerTextos:
    def test_leitura_basica(self, tmp_path):
        arq = tmp_path / "frases.txt"
        arq.write_text("Linha 1\nLinha 2\nLinha 3\n", encoding="utf-8")
        assert _ler_textos_arquivo(str(arq)) == ["Linha 1", "Linha 2", "Linha 3"]

    def test_ignora_linhas_vazias(self, tmp_path):
        arq = tmp_path / "frases.txt"
        arq.write_text("Linha 1\n\n\nLinha 2\n", encoding="utf-8")
        assert _ler_textos_arquivo(str(arq)) == ["Linha 1", "Linha 2"]

    def test_remove_espacos_nas_bordas(self, tmp_path):
        arq = tmp_path / "frases.txt"
        arq.write_text("  Linha com espaço  \n", encoding="utf-8")
        assert _ler_textos_arquivo(str(arq)) == ["Linha com espaço"]

    def test_arquivo_so_com_linhas_vazias(self, tmp_path):
        arq = tmp_path / "frases.txt"
        arq.write_text("\n\n\n", encoding="utf-8")
        assert _ler_textos_arquivo(str(arq)) == []


# ── _ler_token_env ────────────────────────────────────────────────────────────

class TestLerTokenEnv:
    def test_lê_da_variavel_de_ambiente(self, monkeypatch):
        monkeypatch.setenv("HF_TOKEN", "hf_test123")
        assert _ler_token_env() == "hf_test123"

    def test_le_do_arquivo_env(self, tmp_path, monkeypatch):
        monkeypatch.delenv("HF_TOKEN", raising=False)
        env_file = tmp_path / ".env"
        env_file.write_text("HF_TOKEN=hf_from_file\n", encoding="utf-8")
        monkeypatch.setattr(tts_ptbr, "_ENV_PATH", env_file)
        assert _ler_token_env() == "hf_from_file"

    def test_token_com_aspas_no_arquivo(self, tmp_path, monkeypatch):
        monkeypatch.delenv("HF_TOKEN", raising=False)
        env_file = tmp_path / ".env"
        env_file.write_text('HF_TOKEN="hf_quoted"\n', encoding="utf-8")
        monkeypatch.setattr(tts_ptbr, "_ENV_PATH", env_file)
        assert _ler_token_env() == "hf_quoted"

    def test_retorna_none_se_ausente(self, tmp_path, monkeypatch):
        monkeypatch.delenv("HF_TOKEN", raising=False)
        monkeypatch.setattr(tts_ptbr, "_ENV_PATH", tmp_path / ".env_inexistente")
        assert _ler_token_env() is None

    def test_ignora_comentarios_no_arquivo(self, tmp_path, monkeypatch):
        monkeypatch.delenv("HF_TOKEN", raising=False)
        env_file = tmp_path / ".env"
        env_file.write_text("# comentário\nHF_TOKEN=hf_real\n", encoding="utf-8")
        monkeypatch.setattr(tts_ptbr, "_ENV_PATH", env_file)
        assert _ler_token_env() == "hf_real"

    def test_variavel_de_ambiente_tem_prioridade(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HF_TOKEN", "hf_env")
        env_file = tmp_path / ".env"
        env_file.write_text("HF_TOKEN=hf_file\n", encoding="utf-8")
        monkeypatch.setattr(tts_ptbr, "_ENV_PATH", env_file)
        assert _ler_token_env() == "hf_env"


# ── Cache de áudio ────────────────────────────────────────────────────────────

AUDIO_FAKE = np.zeros(22050, dtype=np.float32)
SR_FAKE = 22050


class TestCacheKey:
    def test_mesmos_args_mesma_chave(self):
        k1 = _cache_key("edge", "francisca", "pt", "Olá")
        k2 = _cache_key("edge", "francisca", "pt", "Olá")
        assert k1 == k2

    def test_texto_diferente_chave_diferente(self):
        k1 = _cache_key("edge", "francisca", "pt", "Olá")
        k2 = _cache_key("edge", "francisca", "pt", "Tchau")
        assert k1 != k2

    def test_engine_diferente_chave_diferente(self):
        k1 = _cache_key("edge", "francisca", "pt", "Olá")
        k2 = _cache_key("pocket", "francisca", "pt", "Olá")
        assert k1 != k2

    def test_voz_diferente_chave_diferente(self):
        k1 = _cache_key("edge", "francisca", "pt", "Olá")
        k2 = _cache_key("edge", "antonio", "pt", "Olá")
        assert k1 != k2

    def test_tamanho_fixo(self):
        assert len(_cache_key("edge", "francisca", "pt", "Olá")) == 16


class TestCacheSalvarBuscar:
    def test_salvar_e_buscar_roundtrip(self, tmp_path, monkeypatch):
        monkeypatch.setattr(tts_ptbr, "CACHE_DIR", tmp_path / "cache")
        monkeypatch.setattr(tts_ptbr, "CACHE_INDEX", tmp_path / "cache" / "index.json")
        _cache_salvar("edge", "francisca", "pt", "Olá", AUDIO_FAKE, SR_FAKE)
        resultado = _cache_buscar("edge", "francisca", "pt", "Olá")
        assert resultado is not None
        data, sr = resultado
        assert sr == SR_FAKE
        assert len(data) == len(AUDIO_FAKE)

    def test_miss_retorna_none(self, tmp_path, monkeypatch):
        monkeypatch.setattr(tts_ptbr, "CACHE_DIR", tmp_path / "cache")
        monkeypatch.setattr(tts_ptbr, "CACHE_INDEX", tmp_path / "cache" / "index.json")
        assert _cache_buscar("edge", "francisca", "pt", "Texto novo") is None

    def test_limite_remove_mais_antigo(self, tmp_path, monkeypatch):
        monkeypatch.setattr(tts_ptbr, "CACHE_DIR", tmp_path / "cache")
        monkeypatch.setattr(tts_ptbr, "CACHE_INDEX", tmp_path / "cache" / "index.json")
        monkeypatch.setattr(tts_ptbr, "_cache_max", 2)
        _cache_salvar("edge", "francisca", "pt", "Texto 1", AUDIO_FAKE, SR_FAKE)
        _cache_salvar("edge", "francisca", "pt", "Texto 2", AUDIO_FAKE, SR_FAKE)
        _cache_salvar("edge", "francisca", "pt", "Texto 3", AUDIO_FAKE, SR_FAKE)
        from tts_ptbr import _cache_ler_index
        index = _cache_ler_index()
        assert len(index) == 2
        # Texto 1 (o mais antigo) deve ter sido removido
        assert _cache_buscar("edge", "francisca", "pt", "Texto 1") is None


class TestCacheLimpar:
    def test_limpar_remove_arquivos(self, tmp_path, monkeypatch):
        monkeypatch.setattr(tts_ptbr, "CACHE_DIR", tmp_path / "cache")
        monkeypatch.setattr(tts_ptbr, "CACHE_INDEX", tmp_path / "cache" / "index.json")
        _cache_salvar("edge", "francisca", "pt", "Olá", AUDIO_FAKE, SR_FAKE)
        n = _cache_limpar()
        assert n == 1
        assert _cache_buscar("edge", "francisca", "pt", "Olá") is None

    def test_limpar_cache_vazio(self, tmp_path, monkeypatch):
        monkeypatch.setattr(tts_ptbr, "CACHE_DIR", tmp_path / "cache_vazio")
        assert _cache_limpar() == 0


# ── _ler_textos_stdin ─────────────────────────────────────────────────────────

class TestLerTextoStdin:
    def test_leitura_basica(self):
        with patch("tts_ptbr.sys.stdin", io.StringIO("Linha 1\nLinha 2\nLinha 3\n")):
            assert _ler_textos_stdin() == ["Linha 1", "Linha 2", "Linha 3"]

    def test_ignora_linhas_vazias(self):
        with patch("tts_ptbr.sys.stdin", io.StringIO("Linha 1\n\nLinha 2\n")):
            assert _ler_textos_stdin() == ["Linha 1", "Linha 2"]

    def test_remove_espacos_nas_bordas(self):
        with patch("tts_ptbr.sys.stdin", io.StringIO("  Texto  \n")):
            assert _ler_textos_stdin() == ["Texto"]

    def test_stdin_vazio(self):
        with patch("tts_ptbr.sys.stdin", io.StringIO("")):
            assert _ler_textos_stdin() == []


# ── _aplicar_velocidade ───────────────────────────────────────────────────────

class TestAplicarVelocidade:
    def test_velocidade_um_retorna_original(self):
        data = np.ones(100, dtype=np.float32)
        result = _aplicar_velocidade(data, 1.0)
        np.testing.assert_array_equal(result, data)

    def test_dobrar_velocidade_reduz_amostras_pela_metade(self):
        data = np.ones(100, dtype=np.float32)
        result = _aplicar_velocidade(data, 2.0)
        assert len(result) == 50

    def test_metade_velocidade_dobra_amostras(self):
        data = np.ones(100, dtype=np.float32)
        result = _aplicar_velocidade(data, 0.5)
        assert len(result) == 200

    def test_preserva_dtype(self):
        data = np.ones(100, dtype=np.float32)
        result = _aplicar_velocidade(data, 1.5)
        assert result.dtype == np.float32

    def test_velocidade_muito_alta_nao_retorna_vazio(self):
        data = np.ones(100, dtype=np.float32)
        result = _aplicar_velocidade(data, 200.0)
        assert len(result) >= 1


# ── _normalizar ───────────────────────────────────────────────────────────────

class TestNormalizar:
    def test_audio_baixo_e_amplificado(self):
        data = np.ones(100, dtype=np.float32) * 0.005
        result = _normalizar(data)
        assert np.abs(result).max() == pytest.approx(0.90, rel=1e-4)

    def test_audio_ja_alto_nao_e_alterado(self):
        data = np.ones(100, dtype=np.float32) * 0.95
        result = _normalizar(data)
        np.testing.assert_array_equal(result, data)

    def test_audio_no_limite_nao_e_alterado(self):
        data = np.ones(100, dtype=np.float32) * 0.90
        result = _normalizar(data)
        np.testing.assert_array_equal(result, data)

    def test_silencio_nao_levanta_erro(self):
        data = np.zeros(100, dtype=np.float32)
        result = _normalizar(data)
        np.testing.assert_array_equal(result, data)

    def test_preserva_dtype(self):
        data = np.ones(100, dtype=np.float32) * 0.01
        result = _normalizar(data)
        assert result.dtype == np.float32


# ── _processar_saida ──────────────────────────────────────────────────────────

AUDIO_FAKE_PS = np.zeros(22050, dtype=np.float32)
SR_FAKE_PS = 22050


class TestProcessarSaida:
    def test_salva_arquivo_wav(self, tmp_path):
        destino = str(tmp_path / "saida.wav")
        with patch("tts_ptbr.sd.play"), patch("tts_ptbr.sd.wait"):
            _processar_saida(AUDIO_FAKE_PS, SR_FAKE_PS, salvar=destino, reproduzir=False)
        assert (tmp_path / "saida.wav").exists()

    def test_velocidade_altera_tamanho(self, tmp_path):
        destino = str(tmp_path / "rapido.wav")
        with patch("tts_ptbr.sd.play"), patch("tts_ptbr.sd.wait"):
            _processar_saida(AUDIO_FAKE_PS, SR_FAKE_PS, salvar=destino, velocidade=2.0, reproduzir=False)
        import soundfile as sf
        data, _ = sf.read(destino)
        assert len(data) == pytest.approx(len(AUDIO_FAKE_PS) / 2, rel=0.05)

    def test_sample_rate_saida_reamostrado(self, tmp_path):
        destino = str(tmp_path / "44k.wav")
        with patch("tts_ptbr.sd.play"), patch("tts_ptbr.sd.wait"):
            _processar_saida(AUDIO_FAKE_PS, SR_FAKE_PS, salvar=destino, sample_rate_saida=44100, reproduzir=False)
        import soundfile as sf
        data, sr = sf.read(destino)
        assert sr == 44100
        assert len(data) == pytest.approx(len(AUDIO_FAKE_PS) * 2, rel=0.05)

    def test_reproduzir_chama_sd_play(self):
        with patch("tts_ptbr.sd.play") as mock_play, patch("tts_ptbr.sd.wait"):
            _processar_saida(AUDIO_FAKE_PS, SR_FAKE_PS, reproduzir=True)
        mock_play.assert_called_once()

    def test_sem_reproduzir_nao_chama_sd_play(self, tmp_path):
        destino = str(tmp_path / "s.wav")
        with patch("tts_ptbr.sd.play") as mock_play, patch("tts_ptbr.sd.wait"):
            _processar_saida(AUDIO_FAKE_PS, SR_FAKE_PS, salvar=destino, reproduzir=False)
        mock_play.assert_not_called()

    def test_so_nome_vai_para_pasta_output(self, tmp_path, monkeypatch):
        monkeypatch.setattr(tts_ptbr, "DIR_OUTPUT", tmp_path / "output")
        with patch("tts_ptbr.sd.play"), patch("tts_ptbr.sd.wait"):
            _processar_saida(AUDIO_FAKE_PS, SR_FAKE_PS, salvar="saida.wav", reproduzir=False)
        assert (tmp_path / "output" / "saida.wav").exists()

    def test_path_absoluta_nao_redireciona(self, tmp_path, monkeypatch):
        monkeypatch.setattr(tts_ptbr, "DIR_OUTPUT", tmp_path / "output")
        destino = str(tmp_path / "outro" / "saida.wav")
        with patch("tts_ptbr.sd.play"), patch("tts_ptbr.sd.wait"):
            _processar_saida(AUDIO_FAKE_PS, SR_FAKE_PS, salvar=destino, reproduzir=False)
        assert (tmp_path / "outro" / "saida.wav").exists()
        assert not (tmp_path / "output").exists()


# ── _cache_stats ──────────────────────────────────────────────────────────────

class TestCacheStats:
    def test_cache_vazio_retorna_mensagem(self, tmp_path, monkeypatch):
        monkeypatch.setattr(tts_ptbr, "CACHE_DIR", tmp_path / "cache_vazio")
        monkeypatch.setattr(tts_ptbr, "CACHE_INDEX", tmp_path / "cache_vazio" / "index.json")
        assert _cache_stats() == "Cache vazio."

    def test_cache_com_entrada_conta_corretamente(self, tmp_path, monkeypatch):
        monkeypatch.setattr(tts_ptbr, "CACHE_DIR", tmp_path / "cache")
        monkeypatch.setattr(tts_ptbr, "CACHE_INDEX", tmp_path / "cache" / "index.json")
        _cache_salvar("edge", "francisca", "pt", "Olá", AUDIO_FAKE, SR_FAKE)
        stats = _cache_stats()
        assert "1 entrada" in stats
        assert "MB" in stats


class TestCacheCLI:
    def _mock_edge(self):
        return patch("tts_ptbr._sintetizar_edge", return_value=(AUDIO_FAKE, SR_FAKE))

    def test_sem_cache_nao_busca(self):
        with patch("sys.argv", ["tts_ptbr.py", "--sem-cache", "Olá"]), \
             self._mock_edge(), \
             patch("tts_ptbr.sd.play"), patch("tts_ptbr.sd.wait"), \
             patch("tts_ptbr._cache_buscar") as mock_buscar:
            from tts_ptbr import main
            main()
        mock_buscar.assert_not_called()

    def test_limpar_cache_cli(self):
        with patch("sys.argv", ["tts_ptbr.py", "--limpar-cache"]), \
             patch("tts_ptbr._cache_limpar", return_value=3) as mock_limpar:
            from tts_ptbr import main
            main()
        mock_limpar.assert_called_once()
