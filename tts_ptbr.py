#!/usr/bin/env python3
"""
TTS Português BR
Converte texto em voz com dois engines:
  - edge   : Microsoft Edge TTS (online, alta qualidade, padrão)
  - pocket : Pocket TTS / Kyutai (local, neural, baixa latência)

Uso:
  python tts_ptbr.py "Texto"
  python tts_ptbr.py --engine pocket "Texto"
  python tts_ptbr.py --engine pocket --idioma en "Hello world"
  python tts_ptbr.py --velocidade 1.5 "Texto mais rápido"
  python tts_ptbr.py --engine pocket --streaming "Texto com streaming"
  python tts_ptbr.py --salvar saida.wav "Texto"
  python tts_ptbr.py --salvar saida.flac --sample-rate 44100 "Texto"
  python tts_ptbr.py --salvar saida.wav --sem-reproduzir "Texto"
  python tts_ptbr.py --engine pocket --clonar-voz minha_voz.wav "Texto"
  python tts_ptbr.py --engine pocket --voz minha_voz.safetensors "Texto"
  python tts_ptbr.py          # modo interativo
"""

import asyncio
import hashlib
import io
import json
import re
import sys
import argparse
import logging
from datetime import datetime
from pathlib import Path

import numpy as np
import edge_tts
import sounddevice as sd
import soundfile as sf
from scipy.signal import resample as scipy_resample
from num2words import num2words as _n2w

# ── Vozes do engine edge-tts ─────────────────────────────────────────────────
VOZES_EDGE = {
    "francisca": "pt-BR-FranciscaNeural",
    "antonio":   "pt-BR-AntonioNeural",
    "thalita":   "pt-BR-ThalitaNeural",
}
VOZ_EDGE_PADRAO = "francisca"

# ── Idiomas e vozes do engine pocket-tts ─────────────────────────────────────
IDIOMAS_POCKET = {
    "pt": "portuguese",
    "en": "english",
    "fr": "french_24l",
    "de": "german_24l",
    "it": "italian",
    "es": "spanish_24l",
}
IDIOMA_POCKET_PADRAO = "pt"

# Catálogo completo — kyutai/tts-voices + kyutai/pocket-tts
# Disponibilidade por idioma depende dos embeddings no repositório HF.
# Rafael é a única voz com embedding nativo para PT; demais funcionam melhor com EN.
VOZES_POCKET = {
    "rafael":         "rafael",           # PT (padrão)
    "cosette":        "cosette",
    "marius":         "marius",
    "javert":         "javert",
    "alba":           "alba",
    "jean":           "jean",
    "anna":           "anna",
    "vera":           "vera",
    "fantine":        "fantine",
    "charles":        "charles",
    "paul":           "paul",
    "eponine":        "eponine",
    "azelma":         "azelma",
    "george":         "george",
    "mary":           "mary",
    "jane":           "jane",
    "michael":        "michael",
    "eve":            "eve",
    "bill_boerst":    "bill_boerst",
    "peter_yearsley": "peter_yearsley",
    "stuart_bell":    "stuart_bell",
    "caro_davy":      "caro_davy",
    "estelle":        "estelle",          # FR
    "giovanni":       "giovanni",         # IT
    "lola":           "lola",             # ES
    "juergen":        "juergen",          # DE
}
VOZ_POCKET_PADRAO = "rafael"

FORMATOS_SUPORTADOS = {"wav", "flac", "ogg", "mp3"}
DIR_OUTPUT = Path(__file__).parent / "output"
CONFIG_PATH = Path(__file__).parent / "config.yaml"
CACHE_DIR = Path(__file__).parent / ".cache" / "tts_ptbr"
CACHE_INDEX = CACHE_DIR / "index.json"
CACHE_MAX_PADRAO = 50

_CAMPOS_CONFIG = frozenset({
    "engine", "idioma", "voz", "velocidade",
    "streaming", "preprocessar", "formato", "sample_rate", "cache_max",
})

# Estado do cache (configurável via CLI/config)
_usar_cache: bool = True
_cache_max: int = CACHE_MAX_PADRAO

logging.basicConfig(level=logging.WARNING)


# ─────────────────────────────────────────────────────────────────────────────
# Configuração persistente (config.yaml)
# ─────────────────────────────────────────────────────────────────────────────

def _carregar_config(caminho: Path = CONFIG_PATH) -> dict:
    if not caminho.exists():
        return {}
    try:
        import yaml
        return yaml.safe_load(caminho.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


def _salvar_config(cfg: dict, caminho: Path = CONFIG_PATH) -> None:
    try:
        import yaml
        caminho.write_text(
            yaml.dump(cfg, allow_unicode=True, default_flow_style=False, sort_keys=True),
            encoding="utf-8",
        )
        print(f"[config] Salvo em {caminho}")
    except ImportError:
        print("[config] pyyaml não instalado. Execute: uv pip install pyyaml")
    except Exception as e:
        print(f"[config] Erro ao salvar: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# Cache de áudio
# ─────────────────────────────────────────────────────────────────────────────

def _cache_key(engine: str, voz: str, idioma: str, texto: str) -> str:
    payload = f"{engine}:{voz}:{idioma}:{texto}"
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def _cache_ler_index() -> dict:
    if not CACHE_INDEX.exists():
        return {}
    try:
        return json.loads(CACHE_INDEX.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _cache_escrever_index(index: dict) -> None:
    CACHE_INDEX.parent.mkdir(parents=True, exist_ok=True)
    CACHE_INDEX.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")


def _cache_buscar(engine: str, voz: str, idioma: str, texto: str) -> tuple[np.ndarray, int] | None:
    key = _cache_key(engine, voz, idioma, texto)
    index = _cache_ler_index()
    if key not in index:
        return None
    arquivo = CACHE_DIR / index[key]["arquivo"]
    if not arquivo.exists():
        return None
    try:
        data, sr = sf.read(str(arquivo))
        return data.astype(np.float32), int(sr)
    except Exception:
        return None


def _cache_salvar(engine: str, voz: str, idioma: str, texto: str, data: np.ndarray, sr: int) -> None:
    key = _cache_key(engine, voz, idioma, texto)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    arquivo_nome = f"{key}.wav"
    try:
        sf.write(str(CACHE_DIR / arquivo_nome), data, sr, format="WAV")
    except Exception:
        return
    index = _cache_ler_index()
    index[key] = {
        "engine": engine, "voz": voz, "idioma": idioma,
        "texto": texto[:120],
        "arquivo": arquivo_nome,
        "criado": datetime.now().isoformat(),
    }
    if len(index) > _cache_max:
        chaves = sorted(index, key=lambda k: index[k].get("criado", ""))
        for chave_antiga in chaves[:len(index) - _cache_max]:
            (CACHE_DIR / index[chave_antiga]["arquivo"]).unlink(missing_ok=True)
            del index[chave_antiga]
    _cache_escrever_index(index)


def _cache_limpar() -> int:
    if not CACHE_DIR.exists():
        return 0
    count = sum(1 for arq in CACHE_DIR.glob("*.wav") if arq.unlink() or True)
    if CACHE_INDEX.exists():
        CACHE_INDEX.unlink()
    return count


def _cache_stats() -> str:
    index = _cache_ler_index()
    if not index:
        return "Cache vazio."
    tamanho = sum(
        (CACHE_DIR / e["arquivo"]).stat().st_size
        for e in index.values()
        if (CACHE_DIR / e["arquivo"]).exists()
    )
    return f"{len(index)} entrada(s) — {tamanho / 1_000_000:.1f} MB"


# ─────────────────────────────────────────────────────────────────────────────
# Pré-processamento de texto (PT-BR)
# ─────────────────────────────────────────────────────────────────────────────

_ABREVIACOES = [
    (r'\bDr\.(?=\s|$)',    'Doutor'),
    (r'\bDra\.(?=\s|$)',   'Doutora'),
    (r'\bSr\.(?=\s|$)',    'Senhor'),
    (r'\bSra\.(?=\s|$)',   'Senhora'),
    (r'\bProf\.(?=\s|$)',  'Professor'),
    (r'\bProfa\.(?=\s|$)', 'Professora'),
    (r'\bEng\.(?=\s|$)',   'Engenheiro'),
    (r'\bAv\.(?=\s|$)',    'Avenida'),
    (r'\bvs\.(?=\s|$)',    'versus'),
    (r'\betc\.',           'etcétera'),
    (r'\bex\.(?=\s|$)',    'exemplo'),
    (r'\bobs\.(?=\s|$)',   'observação'),
    (r'\bpág\.(?=\s|$)',   'página'),
    (r'\bcap\.(?=\s|$)',   'capítulo'),
    (r'\bap\.(?=\s|$)',    'apartamento'),
    (r'\bn[º°]',           'número'),
]

_ORDINAIS_M = ['', 'primeiro', 'segundo', 'terceiro', 'quarto', 'quinto',
               'sexto', 'sétimo', 'oitavo', 'nono', 'décimo']
_ORDINAIS_F = ['', 'primeira', 'segunda', 'terceira', 'quarta', 'quinta',
               'sexta', 'sétima', 'oitava', 'nona', 'décima']


def _sub_moeda(m: re.Match) -> str:
    raw = m.group(1).replace('.', '').replace(',', '.')
    try:
        valor = float(raw)
        inteiro, frac = divmod(round(valor * 100), 100)
        partes = []
        if inteiro:
            partes.append(f"{_n2w(inteiro, lang='pt_BR')} {'real' if inteiro == 1 else 'reais'}")
        if frac:
            partes.append(f"{_n2w(frac, lang='pt_BR')} {'centavo' if frac == 1 else 'centavos'}")
        return ' e '.join(partes) or 'zero reais'
    except (ValueError, OverflowError):
        return m.group(0)


def _sub_percentual(m: re.Match) -> str:
    try:
        n = float(m.group(1).replace('.', '').replace(',', '.'))
        return f"{_n2w(n, lang='pt_BR')} por cento"
    except (ValueError, OverflowError):
        return m.group(0)


def _sub_ordinal(m: re.Match) -> str:
    n, genero = int(m.group(1)), m.group(2)
    tabela = _ORDINAIS_F if genero in ('ª', 'a') else _ORDINAIS_M
    return tabela[n] if 1 <= n < len(tabela) else m.group(0)


def _sub_numero(m: re.Match) -> str:
    raw = m.group(0)
    try:
        s = raw.replace('.', '').replace(',', '.')
        n = float(s) if '.' in s else int(s)
        return _n2w(n, lang='pt_BR')
    except (ValueError, OverflowError):
        return raw


def preprocessar_texto(texto: str) -> str:
    """Expande abreviações, moeda, porcentagem, ordinais, siglas e números."""
    texto = re.sub(r'R\$\s*([\d.,]+)', _sub_moeda, texto)
    texto = re.sub(r'([\d.,]+)\s*%', _sub_percentual, texto)
    texto = re.sub(r'\b(\d+)\s*([°ºª])', _sub_ordinal, texto)
    for padrao, sub in _ABREVIACOES:
        texto = re.sub(padrao, sub, texto)
    texto = re.sub(r'\b([A-Z]{2,})\b', lambda m: ' '.join(m.group(1)), texto)
    texto = re.sub(r'\b\d{1,3}(?:\.\d{3})*(?:,\d+)?\b|\b\d+(?:,\d+)?\b', _sub_numero, texto)
    return re.sub(r'\s+', ' ', texto).strip()


# ─────────────────────────────────────────────────────────────────────────────
# Engine: edge-tts
# ─────────────────────────────────────────────────────────────────────────────

async def _edge_sintetizar_bytes(texto: str, voz_id: str) -> bytes:
    communicate = edge_tts.Communicate(texto, voz_id)
    audio_bytes = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_bytes += chunk["data"]
    return audio_bytes


def _sintetizar_edge(texto: str, nome_voz: str = VOZ_EDGE_PADRAO) -> tuple[np.ndarray, int]:
    voz_id = VOZES_EDGE.get(nome_voz, VOZES_EDGE[VOZ_EDGE_PADRAO])
    audio_bytes = asyncio.run(_edge_sintetizar_bytes(texto, voz_id))
    data, samplerate = sf.read(io.BytesIO(audio_bytes))
    return data, samplerate


# ─────────────────────────────────────────────────────────────────────────────
# Engine: pocket-tts
# ─────────────────────────────────────────────────────────────────────────────

_pocket_models: dict[str, object] = {}
_ENV_PATH = Path(__file__).parent / ".env"


def _ler_token_env() -> str | None:
    """Lê HF_TOKEN de variável de ambiente ou do arquivo .env."""
    import os

    token = os.environ.get("HF_TOKEN")
    if token:
        return token

    if not _ENV_PATH.exists():
        return None

    for linha in _ENV_PATH.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if linha.startswith("#") or "=" not in linha:
            continue
        chave, _, valor = linha.partition("=")
        if chave.strip() == "HF_TOKEN":
            return valor.strip().strip('"').strip("'")

    return None


def _aplicar_token(token: str) -> bool:
    """
    Exporta o token para os.environ e para o cache do HuggingFace Hub.
    Setar HF_TOKEN no ambiente garante que hf_hub_download (usado
    internamente pelo pocket-tts) o encontre sem parâmetro explícito.
    """
    import os
    from huggingface_hub import login, errors as hf_errors

    os.environ["HF_TOKEN"] = token
    try:
        login(token=token, add_to_git_credential=False)
        return True
    except hf_errors.HfHubHTTPError:
        print("[pocket-tts] Token inválido ou expirado.")
        return False
    except Exception as e:
        print(f"[pocket-tts] Falha ao aplicar token: {e}")
        return False


def _carregar_pocket(idioma: str = IDIOMA_POCKET_PADRAO):
    global _pocket_models
    if idioma not in _pocket_models:
        lang_id = IDIOMAS_POCKET.get(idioma, idioma)
        token = _ler_token_env()
        if token:
            _aplicar_token(token)
        from pocket_tts import TTSModel
        print(f"[pocket-tts] Carregando modelo '{idioma}' ({lang_id}) — primeira execução faz download...")
        _pocket_models[idioma] = TTSModel.load_model(language=lang_id)
        print("[pocket-tts] Modelo pronto.")
    return _pocket_models[idioma]


_REPO_GATED = "kyutai/pocket-tts"
_REPO_GATED_URL = f"https://huggingface.co/{_REPO_GATED}"
_ARQUIVO_TESTE_VC = ("languages/portuguese/model.safetensors",
                     "39592ff23c9ef80098bb74895d104c26275fe2c9")


def _verificar_acesso_vc() -> tuple[bool, str]:
    from huggingface_hub import hf_hub_download
    from huggingface_hub.errors import GatedRepoError

    filename, revision = _ARQUIVO_TESTE_VC
    try:
        hf_hub_download(_REPO_GATED, filename=filename, revision=revision)
        return True, ""
    except GatedRepoError:
        return False, "gated"
    except Exception as e:
        return False, str(e)


def _autenticar_hf() -> bool:
    """
    Garante acesso ao repositório gated de voice cloning:
      1. Aplica HF_TOKEN do .env / variável de ambiente.
      2. Verifica acesso real ao arquivo de pesos.
      3. Se acesso negado (GatedRepoError), instrui o usuário a solicitar
         acesso na página do modelo e aguarda confirmação para retentar.
      4. Se token ausente, oferece login interativo via `uvx hf auth login`.
    Retorna True quando o acesso ao repositório estiver confirmado.
    """
    import subprocess

    print()
    print("[pocket-tts] Clonagem de voz requer acesso ao repositório gated.")

    token = _ler_token_env()
    if token:
        origem = str(_ENV_PATH) if _ENV_PATH.exists() else "variável de ambiente"
        print(f"[pocket-tts] Token encontrado em {origem}.")
        if not _aplicar_token(token):
            token = None

    if not token:
        print()
        print(f"  Dica: adicione HF_TOKEN=<seu_token> em {_ENV_PATH}")
        print()
        try:
            resp = input("Deseja fazer login com `uvx hf auth login`? (s/N): ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print()
            return False
        if resp not in ("s", "sim", "y", "yes"):
            return False
        if subprocess.run(["uvx", "hf", "auth", "login"]).returncode != 0:
            return False

    print("[pocket-tts] Verificando acesso ao repositório...")
    acesso, motivo = _verificar_acesso_vc()

    if acesso:
        print("[pocket-tts] Acesso confirmado.")
        return True

    if motivo == "gated":
        print()
        print("[pocket-tts] Token válido, mas acesso ao repositório ainda não aprovado.")
        print(f"  1. Abra: {_REPO_GATED_URL}")
        print("  2. Clique em 'Agree and access repository' e preencha o formulário.")
        print("  3. O acesso costuma ser aprovado imediatamente.")
        print()

        while True:
            try:
                resp = input("Já solicitou o acesso? Retentar verificação? (s/N): ").strip().lower()
            except (KeyboardInterrupt, EOFError):
                print()
                return False
            if resp not in ("s", "sim", "y", "yes"):
                return False

            print("[pocket-tts] Verificando acesso...")
            acesso, motivo = _verificar_acesso_vc()
            if acesso:
                print("[pocket-tts] Acesso concedido!")
                return True
            if motivo == "gated":
                print("[pocket-tts] Acesso ainda pendente. Tente novamente após aprovação.")
            else:
                print(f"[pocket-tts] Erro inesperado: {motivo}")
                return False
    else:
        print(f"[pocket-tts] Erro ao verificar acesso: {motivo}")
        return False


def _resolver_voice_state(model, fonte_voz: str, idioma: str = IDIOMA_POCKET_PADRAO) -> dict:
    p = Path(fonte_voz)

    if p.suffix == ".safetensors":
        if not p.exists():
            raise FileNotFoundError(f"Arquivo de voz não encontrado: {p}")
        return model.get_state_for_audio_prompt(p)

    if p.suffix in (".wav", ".mp3", ".flac", ".ogg", ".m4a"):
        if not p.exists():
            raise FileNotFoundError(f"Arquivo de áudio não encontrado: {p}")
        try:
            return model.get_state_for_audio_prompt(p, truncate=True)
        except ValueError as e:
            if "voice cloning" not in str(e).lower():
                raise
            if not _autenticar_hf():
                raise RuntimeError(
                    "Autenticação cancelada. Para clonar vozes:\n"
                    "  1. Aceite os termos em https://huggingface.co/kyutai/pocket-tts\n"
                    "  2. Execute: uvx hf auth login"
                ) from e
            global _pocket_models
            _pocket_models.pop(idioma, None)
            novo_model = _carregar_pocket(idioma)
            return novo_model.get_state_for_audio_prompt(p, truncate=True)

    voz_id = VOZES_POCKET.get(fonte_voz, VOZ_POCKET_PADRAO)
    try:
        return model.get_state_for_audio_prompt(voz_id)
    except ValueError as e:
        if "voice cloning" in str(e).lower():
            raise RuntimeError(
                f"A voz '{fonte_voz}' não tem embeddings para o modelo '{idioma}'.\n"
                "  Use 'rafael' para PT, ou mude de idioma com --idioma en."
            ) from e
        raise
    except Exception as e:
        msg = str(e).lower()
        if "not found" in msg or "404" in msg or "entrynotfound" in msg:
            raise RuntimeError(
                f"Voz '{fonte_voz}' não disponível para o idioma '{idioma}'.\n"
                f"  Tente --idioma en para acesso ao catálogo completo."
            ) from e
        raise


def _sintetizar_pocket(
    texto: str,
    fonte_voz: str = VOZ_POCKET_PADRAO,
    idioma: str = IDIOMA_POCKET_PADRAO,
) -> tuple[np.ndarray, int]:
    model = _carregar_pocket(idioma)
    voice_state = _resolver_voice_state(model, fonte_voz, idioma)
    audio_tensor = model.generate_audio(voice_state, texto)
    return audio_tensor.numpy(), model.sample_rate


def _sintetizar_pocket_stream(
    texto: str,
    fonte_voz: str = VOZ_POCKET_PADRAO,
    idioma: str = IDIOMA_POCKET_PADRAO,
) -> tuple[np.ndarray, int]:
    """Gera e reproduz áudio em tempo real via streaming. Retorna (array_completo, sr)."""
    model = _carregar_pocket(idioma)
    voice_state = _resolver_voice_state(model, fonte_voz, idioma)
    sr = model.sample_rate
    chunks: list[np.ndarray] = []

    with sd.OutputStream(samplerate=sr, channels=1, dtype="float32") as stream:
        for chunk in model.generate_audio_stream(voice_state, texto):
            data = chunk.numpy().astype(np.float32)
            stream.write(data.reshape(-1, 1))
            chunks.append(data)

    return (np.concatenate(chunks) if chunks else np.array([], dtype=np.float32)), sr


def exportar_voz_pocket(
    fonte_voz: str,
    destino: str,
    idioma: str = IDIOMA_POCKET_PADRAO,
) -> None:
    from pocket_tts.models.tts_model import export_model_state
    destino_path = Path(destino)
    if destino_path.suffix != ".safetensors":
        destino_path = destino_path.with_suffix(".safetensors")
    model = _carregar_pocket(idioma)
    print(f"[pocket-tts] Processando voz: {fonte_voz}")
    voice_state = _resolver_voice_state(model, fonte_voz, idioma)
    export_model_state(voice_state, destino_path)
    print(f"[pocket-tts] Voz exportada: {destino_path}")
    print(f"[pocket-tts] Use com: --voz {destino_path}")


# ─────────────────────────────────────────────────────────────────────────────
# Saída de áudio: reprodução e/ou salvamento
# ─────────────────────────────────────────────────────────────────────────────

def _resample(data: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
    if orig_sr == target_sr:
        return data
    n_samples = round(len(data) * target_sr / orig_sr)
    resampled = scipy_resample(data, n_samples)
    return resampled.astype(data.dtype)


def _aplicar_velocidade(data: np.ndarray, velocidade: float) -> np.ndarray:
    """Altera velocidade via resampling. Nota: modifica o pitch proporcionalmente."""
    if velocidade == 1.0:
        return data
    n_target = round(len(data) / velocidade)
    if n_target <= 0:
        return data
    return scipy_resample(data, n_target).astype(data.dtype)


def _inferir_formato(caminho: str, formato_explicito: str | None) -> str:
    if formato_explicito:
        fmt = formato_explicito.lower()
        if fmt not in FORMATOS_SUPORTADOS:
            raise ValueError(f"Formato '{fmt}' não suportado. Use: {', '.join(sorted(FORMATOS_SUPORTADOS))}")
        return fmt
    ext = Path(caminho).suffix.lstrip(".").lower()
    return ext if ext in FORMATOS_SUPORTADOS else "wav"


def _processar_saida(
    data: np.ndarray,
    samplerate: int,
    *,
    salvar: str | None = None,
    formato: str | None = None,
    sample_rate_saida: int | None = None,
    velocidade: float = 1.0,
    reproduzir: bool = True,
) -> None:
    sr_saida = sample_rate_saida or samplerate
    data_saida = _resample(data, samplerate, sr_saida) if sr_saida != samplerate else data

    if velocidade != 1.0:
        data_saida = _aplicar_velocidade(data_saida, velocidade)

    if salvar:
        fmt = _inferir_formato(salvar, formato)
        destino = Path(salvar)
        if not destino.parent.name or destino.parent == Path("."):
            destino = DIR_OUTPUT / destino.name
        if destino.suffix.lstrip(".").lower() != fmt:
            destino = destino.with_suffix(f".{fmt}")
        destino.parent.mkdir(parents=True, exist_ok=True)
        sf.write(str(destino), data_saida, sr_saida, format=fmt.upper())
        print(f"[salvo] {destino}  ({fmt.upper()}, {sr_saida} Hz)")

    if reproduzir:
        sd.play(data_saida, sr_saida)
        sd.wait()


# ─────────────────────────────────────────────────────────────────────────────
# Batch e utilitários de saída
# ─────────────────────────────────────────────────────────────────────────────

def _sintetizar(
    texto: str,
    engine: str,
    fonte_voz: str,
    idioma: str = IDIOMA_POCKET_PADRAO,
) -> tuple[np.ndarray, int]:
    if _usar_cache:
        hit = _cache_buscar(engine, fonte_voz, idioma, texto)
        if hit is not None:
            print("[cache] Áudio encontrado no cache.")
            return hit
    if engine == "pocket":
        data, sr = _sintetizar_pocket(texto, fonte_voz, idioma)
    else:
        data, sr = _sintetizar_edge(texto, fonte_voz)
    if _usar_cache:
        _cache_salvar(engine, fonte_voz, idioma, texto, data, sr)
    return data, sr


def _concatenar_audio(lista: list[tuple[np.ndarray, int]]) -> tuple[np.ndarray, int]:
    sr_ref = lista[0][1]
    arrays = [_resample(d, sr, sr_ref) if sr != sr_ref else d for d, sr in lista]
    return np.concatenate(arrays), sr_ref


def _nome_numerado(base: str, n: int, total: int) -> str:
    p = Path(base)
    digits = max(3, len(str(total)))
    return str(p.with_stem(f"{p.stem}_{str(n).zfill(digits)}"))


def _ler_textos_arquivo(caminho: str) -> list[str]:
    return [l.strip() for l in Path(caminho).read_text(encoding="utf-8").splitlines() if l.strip()]


def _ler_textos_stdin() -> list[str]:
    return [l.strip() for l in sys.stdin.read().splitlines() if l.strip()]


def processar_batch(
    textos: list[str],
    engine: str,
    fonte_voz: str,
    *,
    idioma: str = IDIOMA_POCKET_PADRAO,
    preprocessar: bool = False,
    salvar: str | None = None,
    formato: str | None = None,
    sample_rate_saida: int | None = None,
    velocidade: float = 1.0,
    reproduzir: bool = True,
    juntar: bool = False,
) -> None:
    if preprocessar:
        textos = [preprocessar_texto(t) for t in textos]

    saida_kw = dict(
        formato=formato,
        sample_rate_saida=sample_rate_saida,
        velocidade=velocidade,
        reproduzir=reproduzir,
    )

    if juntar:
        print(f"[batch] {len(textos)} linha(s) — gerando e juntando...")
        segmentos = []
        for i, texto in enumerate(textos, 1):
            print(f"  [{i}/{len(textos)}] {texto[:60]}{'...' if len(texto) > 60 else ''}")
            segmentos.append(_sintetizar(texto, engine, fonte_voz, idioma))
        data, sr = _concatenar_audio(segmentos)
        _processar_saida(data, sr, salvar=salvar, **saida_kw)
        return

    for i, texto in enumerate(textos, 1):
        prefixo = f"[{i}/{len(textos)}]" if len(textos) > 1 else f"[{engine}]"
        print(f"{prefixo} {texto[:70]}{'...' if len(texto) > 70 else ''}")
        destino = _nome_numerado(salvar, i, len(textos)) if salvar and len(textos) > 1 else salvar
        data, sr = _sintetizar(texto, engine, fonte_voz, idioma)
        _processar_saida(data, sr, salvar=destino, **saida_kw)


# ─────────────────────────────────────────────────────────────────────────────
# Ponto de entrada unificado
# ─────────────────────────────────────────────────────────────────────────────

def falar(
    texto: str,
    engine: str,
    fonte_voz: str,
    *,
    idioma: str = IDIOMA_POCKET_PADRAO,
    preprocessar: bool = False,
    salvar: str | None = None,
    formato: str | None = None,
    sample_rate_saida: int | None = None,
    velocidade: float = 1.0,
    reproduzir: bool = True,
    streaming: bool = False,
) -> None:
    if preprocessar:
        texto = preprocessar_texto(texto)

    saida_kw = dict(
        salvar=salvar,
        formato=formato,
        sample_rate_saida=sample_rate_saida,
        velocidade=velocidade,
    )

    if engine == "pocket" and streaming and reproduzir:
        # Streaming: reproduz em tempo real; salva o áudio completo ao final se pedido
        data, sr = _sintetizar_pocket_stream(texto, fonte_voz, idioma)
        if salvar or velocidade != 1.0 or sample_rate_saida:
            _processar_saida(data, sr, reproduzir=False, **saida_kw)
        return

    data, sr = _sintetizar(texto, engine, fonte_voz, idioma)
    _processar_saida(data, sr, reproduzir=reproduzir, **saida_kw)


def _vozes_para_engine(engine: str) -> dict:
    return VOZES_POCKET if engine == "pocket" else VOZES_EDGE


def _voz_padrao(engine: str) -> str:
    return VOZ_POCKET_PADRAO if engine == "pocket" else VOZ_EDGE_PADRAO


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    global _usar_cache, _cache_max
    cfg = _carregar_config()

    parser = argparse.ArgumentParser(
        description="TTS Português BR",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
exemplos:
  Falar e salvar em WAV:
    python tts_ptbr.py --salvar saida.wav "Olá, mundo!"

  Falar 1,5× mais rápido:
    python tts_ptbr.py --velocidade 1.5 "Texto mais rápido"

  Pocket TTS em inglês com voz alba:
    python tts_ptbr.py --engine pocket --idioma en --voz alba "Hello world"

  Pocket TTS com streaming em tempo real:
    python tts_ptbr.py --engine pocket --streaming "Texto aqui"

  Pré-processar texto antes de falar:
    python tts_ptbr.py --preprocessar "R$ 1.250,00 — 3º lugar, Dr. Silva"

  Ler de arquivo de texto (uma frase por linha):
    python tts_ptbr.py --arquivo frases.txt --salvar frase.wav

  Ler de arquivo e juntar em um único áudio:
    python tts_ptbr.py --arquivo frases.txt --salvar completo.wav --juntar

  Ler do stdin via pipe:
    echo "Olá mundo" | python tts_ptbr.py
    cat frases.txt | python tts_ptbr.py --salvar saida.wav --juntar

  Falar o texto do clipboard:
    python tts_ptbr.py --clipboard
    python tts_ptbr.py --clipboard --engine pocket --voz george --idioma en

  Forçar nova síntese (ignorar cache):
    python tts_ptbr.py --sem-cache "Texto"

  Limpar cache de áudio:
    python tts_ptbr.py --limpar-cache

  Salvar configuração padrão:
    python tts_ptbr.py --engine pocket --idioma en --salvar-config

  Exportar voice state para reuso:
    python tts_ptbr.py --engine pocket --clonar-voz minha_voz.wav --exportar-voz minha_voz.safetensors
        """,
    )
    parser.add_argument("texto", nargs="*", help="Texto para converter em voz")
    parser.add_argument(
        "--engine", "-e",
        choices=["edge", "pocket"],
        default="edge",
        help="Engine TTS: 'edge' (online, padrão) ou 'pocket' (local/neural)",
    )
    parser.add_argument(
        "--idioma",
        choices=list(IDIOMAS_POCKET.keys()),
        default=IDIOMA_POCKET_PADRAO,
        metavar="LANG",
        help=f"[pocket] Idioma do modelo: {', '.join(IDIOMAS_POCKET.keys())} (padrão: pt)",
    )
    parser.add_argument(
        "--voz", "-v",
        default=None,
        help="Voz: nome embutido, caminho .safetensors ou .wav (pocket)",
    )
    parser.add_argument(
        "--clonar-voz",
        metavar="ARQUIVO",
        default=None,
        help="[pocket] Arquivo de áudio para clonagem de voz (requer login HF)",
    )
    parser.add_argument(
        "--exportar-voz",
        metavar="DESTINO",
        default=None,
        help="[pocket] Exporta voice state para .safetensors",
    )
    parser.add_argument(
        "--salvar",
        metavar="ARQUIVO",
        default=None,
        help="Salva o áudio gerado em arquivo (.wav, .flac, .ogg, .mp3)",
    )
    parser.add_argument(
        "--formato",
        metavar="FMT",
        default=None,
        choices=sorted(FORMATOS_SUPORTADOS),
        help="Formato do arquivo de saída (padrão: inferido pela extensão)",
    )
    parser.add_argument(
        "--sample-rate",
        metavar="HZ",
        type=int,
        default=None,
        help="Taxa de amostragem do arquivo de saída em Hz (ex: 44100, 48000)",
    )
    parser.add_argument(
        "--velocidade",
        metavar="N",
        type=float,
        default=1.0,
        help="Velocidade de fala: 0.5 (lento) a 2.0 (rápido), padrão 1.0",
    )
    parser.add_argument(
        "--sem-reproduzir",
        action="store_true",
        help="Salva o áudio sem reproduzir (requer --salvar)",
    )
    parser.add_argument(
        "--streaming",
        action="store_true",
        help="[pocket] Reproduz áudio em tempo real enquanto gera (menor latência)",
    )
    parser.add_argument(
        "--arquivo",
        metavar="TXT",
        default=None,
        help="Arquivo de texto com uma frase por linha",
    )
    parser.add_argument(
        "--preprocessar", "-p",
        action="store_true",
        help="Expande abreviações, moeda, porcentagem, ordinais, siglas e números",
    )
    parser.add_argument(
        "--juntar",
        action="store_true",
        help="Junta todas as frases em um único arquivo de áudio (usar com --arquivo ou stdin)",
    )
    parser.add_argument(
        "--listar-vozes", action="store_true",
        help="Mostra as vozes embutidas disponíveis",
    )
    parser.add_argument(
        "--clipboard",
        action="store_true",
        help="Lê o texto do clipboard em vez de argumento ou stdin",
    )
    parser.add_argument(
        "--salvar-config",
        action="store_true",
        help="Salva os parâmetros atuais como configuração padrão em config.yaml e sai",
    )
    parser.add_argument(
        "--sem-cache",
        action="store_true",
        help="Desativa o cache de áudio para esta execução (força re-síntese)",
    )
    parser.add_argument(
        "--limpar-cache",
        action="store_true",
        help="Remove todos os áudios em cache e sai",
    )

    _cfg_defaults = {k: v for k, v in cfg.items() if k in _CAMPOS_CONFIG}
    if _cfg_defaults:
        parser.set_defaults(**_cfg_defaults)

    args = parser.parse_args()

    if args.sem_reproduzir and not args.salvar:
        parser.error("--sem-reproduzir requer --salvar")
    if args.juntar and not args.salvar:
        parser.error("--juntar requer --salvar")
    if args.velocidade <= 0:
        parser.error("--velocidade deve ser maior que 0")

    _usar_cache = not args.sem_cache
    _cache_max = int(cfg.get("cache_max", CACHE_MAX_PADRAO))

    # ── Limpar cache ──────────────────────────────────────────────────────────
    if args.limpar_cache:
        n = _cache_limpar()
        print(f"[cache] {n} entrada(s) removida(s).")
        return

    # ── Salvar configuração ───────────────────────────────────────────────────
    if args.salvar_config:
        cfg_salvar: dict = {"engine": args.engine, "idioma": args.idioma}
        if args.voz:
            cfg_salvar["voz"] = args.voz
        if args.velocidade != 1.0:
            cfg_salvar["velocidade"] = args.velocidade
        if args.streaming:
            cfg_salvar["streaming"] = True
        if args.preprocessar:
            cfg_salvar["preprocessar"] = True
        if args.formato:
            cfg_salvar["formato"] = args.formato
        if args.sample_rate:
            cfg_salvar["sample_rate"] = args.sample_rate
        _salvar_config(cfg_salvar)
        return

    # ── Listar vozes ─────────────────────────────────────────────────────────
    if args.listar_vozes:
        vozes = _vozes_para_engine(args.engine)
        voz_pad = _voz_padrao(args.engine)
        print(f"Vozes embutidas — engine: {args.engine}")
        for nome, voz_id in vozes.items():
            padrao = " (padrão)" if nome == voz_pad else ""
            print(f"  {nome:<16} → {voz_id}{padrao}")
        if args.engine == "pocket":
            print()
            print("  Nota: rafael tem embedding nativo para PT.")
            print("  Demais vozes funcionam melhor com --idioma en.")
            print("  Qualquer voz aceita arquivo.safetensors ou arquivo.wav com login HF.")
        return

    # ── Parâmetros de saída de áudio ─────────────────────────────────────────
    saida = dict(
        salvar=args.salvar,
        formato=args.formato,
        sample_rate_saida=args.sample_rate,
        velocidade=args.velocidade,
        reproduzir=not args.sem_reproduzir,
    )
    saida_batch = dict(
        **saida,
        idioma=args.idioma,
        preprocessar=args.preprocessar,
        juntar=args.juntar,
    )

    # ── Determinar fonte de voz ───────────────────────────────────────────────
    if args.engine == "pocket":
        fonte_voz = args.clonar_voz or args.voz or VOZ_POCKET_PADRAO
    else:
        vozes = _vozes_para_engine(args.engine)
        fonte_voz = args.voz if args.voz in vozes else _voz_padrao(args.engine)

    # ── Apenas exportar voz (sem texto) ──────────────────────────────────────
    if args.engine == "pocket" and args.exportar_voz and not args.texto and not args.arquivo:
        exportar_voz_pocket(fonte_voz, args.exportar_voz, args.idioma)
        return

    # ── Clipboard ────────────────────────────────────────────────────────────
    if args.clipboard:
        try:
            import pyperclip
            texto_clip = pyperclip.paste().strip()
        except ImportError:
            print("[erro] pyperclip não instalado. Execute: uv pip install pyperclip")
            sys.exit(1)
        if not texto_clip:
            print("[erro] Clipboard vazio.")
            sys.exit(1)
        args.texto = [texto_clip]

    # ── Coletar textos de arquivo ou stdin ────────────────────────────────────
    if args.arquivo:
        textos = _ler_textos_arquivo(args.arquivo)
        processar_batch(textos, args.engine, fonte_voz, **saida_batch)
        if args.engine == "pocket" and args.exportar_voz:
            exportar_voz_pocket(fonte_voz, args.exportar_voz, args.idioma)
        return

    if not args.texto and not sys.stdin.isatty():
        textos = _ler_textos_stdin()
        if textos:
            processar_batch(textos, args.engine, fonte_voz, **saida_batch)
            return

    # ── Frase direta ──────────────────────────────────────────────────────────
    if args.texto:
        texto = " ".join(args.texto)
        print(f"[{args.engine}] {texto}")
        falar(
            texto, args.engine, fonte_voz,
            idioma=args.idioma,
            preprocessar=args.preprocessar,
            streaming=args.streaming,
            **saida,
        )
        if args.engine == "pocket" and args.exportar_voz:
            exportar_voz_pocket(fonte_voz, args.exportar_voz, args.idioma)
        return

    # ── Modo interativo ───────────────────────────────────────────────────────
    engine_atual = args.engine
    idioma_atual = args.idioma
    voz_atual = fonte_voz
    salvar_atual: str | None = args.salvar
    formato_atual: str | None = args.formato
    sr_atual: int | None = args.sample_rate
    velocidade_atual: float = args.velocidade
    reproduzir_atual: bool = not args.sem_reproduzir
    preprocessar_atual: bool = args.preprocessar
    streaming_atual: bool = args.streaming

    def _status():
        partes = [f"engine: {engine_atual}"]
        if engine_atual == "pocket":
            partes.append(f"idioma: {idioma_atual}")
        partes.append(f"voz: {voz_atual}")
        if velocidade_atual != 1.0:
            partes.append(f"velocidade: {velocidade_atual}x")
        if preprocessar_atual:
            partes.append("preprocessar: on")
        if streaming_atual and engine_atual == "pocket":
            partes.append("streaming: on")
        if salvar_atual:
            partes.append(f"salvar: {salvar_atual}")
        if formato_atual:
            partes.append(f"formato: {formato_atual}")
        if sr_atual:
            partes.append(f"sample-rate: {sr_atual}")
        if not reproduzir_atual:
            partes.append("sem-reproduzir")
        return "  ".join(partes)

    print("TTS Português BR — modo interativo")
    print(_status())
    print("Comandos: engine, idioma, voz, velocidade, preprocessar, streaming, salvar,")
    print("          formato, sample-rate, sem-reproduzir, exportar, clonar,")
    print("          clipboard, cache ver, cache limpar, config salvar, config ver, status, sair")
    print()

    while True:
        try:
            entrada = input("Texto: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nEncerrando.")
            break

        if not entrada:
            continue

        low = entrada.lower()
        partes = entrada.split(maxsplit=1)
        cmd = partes[0].lower()
        arg = partes[1].strip() if len(partes) > 1 else ""

        if low in ("sair", "exit", "quit"):
            print("Até logo!")
            break

        if low == "status":
            print(_status())
            continue

        if cmd == "engine":
            if arg in ("edge", "pocket"):
                engine_atual = arg
                voz_atual = _voz_padrao(engine_atual)
                print(_status())
            else:
                print("Use: engine edge  ou  engine pocket")
            continue

        if cmd == "idioma":
            if arg in IDIOMAS_POCKET:
                idioma_atual = arg
                print(_status())
            else:
                print(f"Idiomas disponíveis: {', '.join(IDIOMAS_POCKET.keys())}")
            continue

        if cmd == "voz":
            if not arg:
                print(f"Voz atual: {voz_atual}")
                continue
            vozes = _vozes_para_engine(engine_atual)
            if engine_atual == "pocket":
                voz_atual = arg
            elif arg in vozes:
                voz_atual = arg
            else:
                print(f"Voz '{arg}' não encontrada. Disponíveis: {', '.join(vozes)}")
                continue
            print(_status())
            continue

        if cmd == "velocidade":
            if arg.lower() == "off" or arg == "1" or arg == "1.0":
                velocidade_atual = 1.0
            else:
                try:
                    v = float(arg)
                    if v <= 0:
                        raise ValueError
                    velocidade_atual = v
                except ValueError:
                    print("Use: velocidade 1.5  (0.5 = lento, 2.0 = rápido)  ou  velocidade off")
                    continue
            print(_status())
            continue

        if cmd == "streaming":
            if engine_atual != "pocket":
                print("Streaming só disponível com engine pocket.")
                continue
            streaming_atual = not streaming_atual
            estado = "ativado" if streaming_atual else "desativado"
            print(f"Streaming {estado}.")
            print(_status())
            continue

        if cmd == "clonar" and engine_atual == "pocket":
            voz_atual = arg
            print(f"Voz de clonagem: {voz_atual}")
            continue

        if cmd == "exportar" and engine_atual == "pocket":
            try:
                exportar_voz_pocket(voz_atual, arg, idioma_atual)
            except (RuntimeError, FileNotFoundError) as e:
                print(f"[erro] {e}")
            continue

        if cmd == "salvar":
            if arg.lower() == "off":
                salvar_atual = None
                reproduzir_atual = True
                print("Salvamento desativado.")
            else:
                salvar_atual = arg
            print(_status())
            continue

        if cmd == "formato":
            if arg.lower() in FORMATOS_SUPORTADOS:
                formato_atual = arg.lower()
            elif arg.lower() == "off":
                formato_atual = None
            else:
                print(f"Formatos disponíveis: {', '.join(sorted(FORMATOS_SUPORTADOS))}")
                continue
            print(_status())
            continue

        if cmd == "sample-rate":
            if arg.lower() == "off":
                sr_atual = None
            elif arg.isdigit():
                sr_atual = int(arg)
            else:
                print("Use: sample-rate 44100  ou  sample-rate off")
                continue
            print(_status())
            continue

        if cmd == "sem-reproduzir":
            if not salvar_atual:
                print("Defina um destino primeiro com: salvar <arquivo>")
                continue
            reproduzir_atual = not reproduzir_atual
            estado = "ativado" if not reproduzir_atual else "desativado"
            print(f"Modo sem-reproduzir {estado}.")
            print(_status())
            continue

        if cmd == "preprocessar":
            if arg.lower() in ("on", "1", "sim"):
                preprocessar_atual = True
            elif arg.lower() in ("off", "0", "não", "nao"):
                preprocessar_atual = False
            else:
                preprocessar_atual = not preprocessar_atual
            print(_status())
            continue

        if low == "clipboard":
            try:
                import pyperclip
                entrada = pyperclip.paste().strip()
            except ImportError:
                print("[clipboard] pyperclip não instalado. Execute: uv pip install pyperclip")
                continue
            if not entrada:
                print("[clipboard] Vazio.")
                continue
            print(f"[clipboard] {entrada[:80]}{'...' if len(entrada) > 80 else ''}")
            try:
                falar(
                    entrada, engine_atual, voz_atual,
                    idioma=idioma_atual,
                    preprocessar=preprocessar_atual,
                    salvar=salvar_atual,
                    formato=formato_atual,
                    sample_rate_saida=sr_atual,
                    velocidade=velocidade_atual,
                    reproduzir=reproduzir_atual,
                    streaming=streaming_atual,
                )
            except (RuntimeError, FileNotFoundError, ValueError) as e:
                print(f"[erro] {e}")
            continue

        if cmd == "cache":
            if arg == "ver":
                print(_cache_stats())
            elif arg == "limpar":
                n = _cache_limpar()
                print(f"[cache] {n} entrada(s) removida(s).")
            elif arg in ("on", ""):
                _usar_cache = True
                print("[cache] Ativado.")
            elif arg == "off":
                _usar_cache = False
                print("[cache] Desativado.")
            else:
                print("Use: cache ver  |  cache limpar  |  cache on  |  cache off")
            continue

        if cmd == "config":
            if arg == "ver":
                if CONFIG_PATH.exists():
                    print(CONFIG_PATH.read_text(encoding="utf-8"))
                else:
                    print(f"[config] Nenhum arquivo em {CONFIG_PATH}")
            elif arg == "salvar":
                cfg_salvar: dict = {
                    "engine": engine_atual,
                    "idioma": idioma_atual,
                    "voz": voz_atual,
                }
                if velocidade_atual != 1.0:
                    cfg_salvar["velocidade"] = velocidade_atual
                if streaming_atual:
                    cfg_salvar["streaming"] = True
                if preprocessar_atual:
                    cfg_salvar["preprocessar"] = True
                if formato_atual:
                    cfg_salvar["formato"] = formato_atual
                if sr_atual:
                    cfg_salvar["sample_rate"] = sr_atual
                _salvar_config(cfg_salvar)
            else:
                print("Use: config salvar  ou  config ver")
            continue

        try:
            print("[falando...]")
            falar(
                entrada, engine_atual, voz_atual,
                idioma=idioma_atual,
                preprocessar=preprocessar_atual,
                salvar=salvar_atual,
                formato=formato_atual,
                sample_rate_saida=sr_atual,
                velocidade=velocidade_atual,
                reproduzir=reproduzir_atual,
                streaming=streaming_atual,
            )
        except (RuntimeError, FileNotFoundError, ValueError) as e:
            print(f"[erro] {e}")


if __name__ == "__main__":
    main()
