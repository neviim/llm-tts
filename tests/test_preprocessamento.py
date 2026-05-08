"""Testes para preprocessar_texto e funções auxiliares de pré-processamento."""
import pytest
from tts_ptbr import preprocessar_texto


# ── Moeda ─────────────────────────────────────────────────────────────────────

class TestMoeda:
    def test_reais_e_centavos(self):
        assert preprocessar_texto("R$ 10,50") == "dez reais e cinquenta centavos"

    def test_apenas_reais(self):
        assert preprocessar_texto("R$ 5") == "cinco reais"

    def test_um_real(self):
        assert preprocessar_texto("R$ 1") == "um real"

    def test_um_centavo(self):
        assert preprocessar_texto("R$ 0,01") == "um centavo"

    def test_milhar_com_centavos(self):
        resultado = preprocessar_texto("R$ 1.000,50")
        assert "mil" in resultado
        assert "reais" in resultado
        assert "cinquenta centavos" in resultado

    def test_moeda_no_meio_da_frase(self):
        resultado = preprocessar_texto("custou R$ 20 hoje")
        assert "vinte reais" in resultado


# ── Porcentagem ───────────────────────────────────────────────────────────────

class TestPercentual:
    def test_inteiro(self):
        assert preprocessar_texto("50%") == "cinquenta por cento"

    def test_decimal(self):
        resultado = preprocessar_texto("98,5%")
        assert "noventa" in resultado
        assert "por cento" in resultado

    def test_cem_por_cento(self):
        assert preprocessar_texto("100%") == "cem por cento"


# ── Ordinais ──────────────────────────────────────────────────────────────────

class TestOrdinais:
    def test_masculino_terceiro(self):
        assert preprocessar_texto("3º lugar") == "terceiro lugar"

    def test_feminino_segunda(self):
        assert preprocessar_texto("2ª edição") == "segunda edição"

    def test_primeiro(self):
        assert preprocessar_texto("1º") == "primeiro"

    def test_primeira(self):
        assert preprocessar_texto("1ª") == "primeira"

    def test_decimo(self):
        assert preprocessar_texto("10º") == "décimo"


# ── Abreviações ───────────────────────────────────────────────────────────────

class TestAbreviacoes:
    @pytest.mark.parametrize("entrada,esperado", [
        ("Dr. Silva",      "Doutor Silva"),
        ("Dra. Ana",       "Doutora Ana"),
        ("Sr. José",       "Senhor José"),
        ("Sra. Lima",      "Senhora Lima"),
        ("Prof. Carlos",   "Professor Carlos"),
        ("Profa. Maria",   "Professora Maria"),
        ("Eng. Pereira",   "Engenheiro Pereira"),
        ("Av. Paulista",   "Avenida Paulista"),
        ("vs. time B",     "versus time B"),
        ("nº 100",         "número cem"),
    ])
    def test_abreviacao(self, entrada, esperado):
        assert preprocessar_texto(entrada) == esperado


# ── Siglas ────────────────────────────────────────────────────────────────────

class TestSiglas:
    def test_tts(self):
        assert preprocessar_texto("TTS") == "T T S"

    def test_ibm(self):
        assert preprocessar_texto("IBM") == "I B M"

    def test_duas_letras(self):
        assert preprocessar_texto("AI") == "A I"

    def test_letra_unica_nao_expande(self):
        # Uma única letra maiúscula não deve ser separada
        resultado = preprocessar_texto("A casa")
        assert resultado == "A casa"


# ── Números ───────────────────────────────────────────────────────────────────

class TestNumeros:
    def test_inteiro_simples(self):
        assert preprocessar_texto("5") == "cinco"

    def test_cem(self):
        assert preprocessar_texto("100") == "cem"

    def test_mil(self):
        assert preprocessar_texto("1000") == "mil"

    def test_milhar_pt_br(self):
        # 1.250 em notação PT-BR = 1250; num2words usa vírgula: "mil, duzentos e cinquenta"
        assert preprocessar_texto("1.250") == "mil, duzentos e cinquenta"

    def test_numero_decimal(self):
        resultado = preprocessar_texto("3,14")
        assert "três" in resultado


# ── Pipeline completo ─────────────────────────────────────────────────────────

class TestPipelineCompleto:
    def test_frase_mista(self):
        resultado = preprocessar_texto("R$ 1.250,50 — 3º lugar, Dr. Silva com 98,5%")
        assert "reais" in resultado
        assert "terceiro lugar" in resultado
        assert "Doutor Silva" in resultado
        assert "por cento" in resultado

    def test_espacos_normalizados(self):
        resultado = preprocessar_texto("  texto   com   espaços  ")
        assert "  " not in resultado
        assert resultado == resultado.strip()
