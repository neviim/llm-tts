#!/usr/bin/env python3
"""
TTS Português BR — Servidor REST

Expõe todos os recursos do tts_ptbr.py via API HTTP.

Iniciar:
    .venv/bin/uvicorn server.server:app --host 0.0.0.0 --port 8080 --reload

Endpoints:
    GET  /              Documentação interativa (Swagger UI)
    GET  /health        Status do servidor
    GET  /vozes         Lista vozes do engine informado
    GET  /idiomas       Lista idiomas disponíveis (pocket)
    POST /tts           Sintetizar voz → retorna áudio (WAV/FLAC/OGG/MP3)
    POST /preprocessar  Aplica pré-processamento PT-BR ao texto
"""

import io
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field, field_validator

# Importa funções e constantes do script principal
sys.path.insert(0, str(Path(__file__).parent.parent))
from tts_ptbr import (
    FORMATOS_SUPORTADOS,
    IDIOMA_POCKET_PADRAO,
    IDIOMAS_POCKET,
    VOZ_EDGE_PADRAO,
    VOZ_POCKET_PADRAO,
    VOZES_EDGE,
    VOZES_POCKET,
    _aplicar_velocidade,
    _resample,
    _sintetizar,
    preprocessar_texto,
)

# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="TTS Português BR",
    description="API de síntese de voz com suporte a edge-tts e Pocket TTS.",
    version="1.0.0",
)

_MEDIA_TYPES = {
    "wav":  "audio/wav",
    "flac": "audio/flac",
    "ogg":  "audio/ogg",
    "mp3":  "audio/mpeg",
}


# ─────────────────────────────────────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────────────────────────────────────

class TTSRequest(BaseModel):
    texto: str = Field(..., min_length=1, description="Texto a sintetizar")
    engine: str = Field("edge", description="Engine TTS: 'edge' ou 'pocket'")
    idioma: str = Field(IDIOMA_POCKET_PADRAO, description="Idioma do modelo pocket (pt/en/fr/de/it/es)")
    voz: str | None = Field(None, description="Nome da voz embutida ou caminho .safetensors")
    preprocessar: bool = Field(False, description="Expandir abreviações, moeda, números etc. (PT-BR)")
    velocidade: float = Field(1.0, ge=0.1, le=4.0, description="Velocidade de fala (0.5–2.0, padrão 1.0)")
    formato: str = Field("wav", description="Formato de saída: wav, flac, ogg ou mp3")
    sample_rate: int | None = Field(None, description="Taxa de amostragem de saída em Hz (ex: 44100)")

    @field_validator("engine")
    @classmethod
    def validar_engine(cls, v):
        if v not in ("edge", "pocket"):
            raise ValueError("engine deve ser 'edge' ou 'pocket'")
        return v

    @field_validator("formato")
    @classmethod
    def validar_formato(cls, v):
        if v not in FORMATOS_SUPORTADOS:
            raise ValueError(f"formato deve ser um de: {', '.join(sorted(FORMATOS_SUPORTADOS))}")
        return v

    @field_validator("idioma")
    @classmethod
    def validar_idioma(cls, v):
        if v not in IDIOMAS_POCKET:
            raise ValueError(f"idioma deve ser um de: {', '.join(IDIOMAS_POCKET.keys())}")
        return v


class PreprocessarRequest(BaseModel):
    texto: str = Field(..., min_length=1, description="Texto a pré-processar")


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/health", summary="Status do servidor")
def health():
    return {"status": "ok"}


@app.get("/idiomas", summary="Lista idiomas disponíveis para o engine pocket")
def listar_idiomas():
    return {"idiomas": IDIOMAS_POCKET, "padrao": IDIOMA_POCKET_PADRAO}


@app.get("/vozes", summary="Lista vozes embutidas do engine")
def listar_vozes(engine: str = Query("edge", description="'edge' ou 'pocket'")):
    if engine == "pocket":
        return {
            "engine": "pocket",
            "vozes": list(VOZES_POCKET.keys()),
            "padrao": VOZ_POCKET_PADRAO,
            "nota": "Rafael tem embedding nativo para PT. Demais vozes funcionam melhor com idioma=en.",
        }
    return {
        "engine": "edge",
        "vozes": list(VOZES_EDGE.keys()),
        "padrao": VOZ_EDGE_PADRAO,
    }


@app.post("/preprocessar", summary="Pré-processa texto em PT-BR")
def endpoint_preprocessar(req: PreprocessarRequest):
    return {
        "original": req.texto,
        "processado": preprocessar_texto(req.texto),
    }


@app.post(
    "/tts",
    summary="Sintetizar voz",
    response_description="Arquivo de áudio no formato solicitado",
    responses={
        200: {"content": {"audio/wav": {}, "audio/flac": {}, "audio/ogg": {}, "audio/mpeg": {}}},
    },
)
def tts(req: TTSRequest):
    """
    Converte texto em áudio e retorna o arquivo binário.

    - **engine** `edge`: vozes Microsoft pt-BR (requer internet)
    - **engine** `pocket`: modelo neural local Kyutai (download único ~500MB)
    - **preprocessar**: expande `R$ 1.250,50` → *mil duzentos e cinquenta reais...*
    - **velocidade**: `1.5` fala 50% mais rápido (via resampling, afeta o pitch)
    - **formato**: `wav` (padrão), `flac`, `ogg`, `mp3`
    """
    texto = preprocessar_texto(req.texto) if req.preprocessar else req.texto

    if req.engine == "pocket":
        fonte_voz = req.voz or VOZ_POCKET_PADRAO
        idioma = req.idioma
    else:
        fonte_voz = req.voz if req.voz in VOZES_EDGE else VOZ_EDGE_PADRAO
        idioma = IDIOMA_POCKET_PADRAO

    try:
        data, sr = _sintetizar(texto, req.engine, fonte_voz, idioma)
    except (RuntimeError, FileNotFoundError, ValueError) as e:
        raise HTTPException(status_code=500, detail=str(e))

    sr_saida = req.sample_rate or sr
    if sr_saida != sr:
        data = _resample(data, sr, sr_saida)
    if req.velocidade != 1.0:
        data = _aplicar_velocidade(data, req.velocidade)

    buf = io.BytesIO()
    sf.write(buf, data, sr_saida, format=req.formato.upper())
    buf.seek(0)

    return Response(
        content=buf.read(),
        media_type=_MEDIA_TYPES.get(req.formato, "audio/wav"),
        headers={"Content-Disposition": f"attachment; filename=tts.{req.formato}"},
    )
