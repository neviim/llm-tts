# Clonagem de voz (pocket)

Sintetiza com uma voz personalizada baseada em um áudio de referência. Requer engine `pocket`, token HuggingFace e aceite dos termos do modelo.

## Pré-requisitos

1. Aceitar os termos: <https://huggingface.co/kyutai/pocket-tts>
2. Token HF em `.env`:

```bash
cp .env.example .env
# Edite: HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## Gravar um áudio de referência

O áudio de referência deve ter:
- Duração: 5–30 segundos
- Silêncio no início e fim
- Fala clara, sem ruído de fundo
- Formato: `.wav` (mono ou estéreo, qualquer sample rate)

```bash
# Gravar via arecord (Linux)
arecord -d 10 -f cd minha_voz.wav

# Ou usar qualquer editor de áudio (Audacity, etc.)
```

## Clonar e falar imediatamente

```bash
.venv/bin/python tts_ptbr.py \
  --engine pocket \
  --clonar-voz minha_voz.wav \
  "Olá! Esta é minha voz clonada."
```

## Clonar e exportar para reuso

O `.safetensors` encapsula o voice state extraído. Funciona depois **sem login** e em qualquer máquina.

```bash
.venv/bin/python tts_ptbr.py \
  --engine pocket \
  --clonar-voz minha_voz.wav \
  --exportar-voz vozes/minha_voz.safetensors \
  "Testando a exportação da voz."
```

## Exportar sem falar

```bash
.venv/bin/python tts_ptbr.py \
  --engine pocket \
  --clonar-voz minha_voz.wav \
  --exportar-voz vozes/minha_voz.safetensors
```

## Usar voz exportada (sem login)

```bash
# Reutilizar o .safetensors sem precisar de HF_TOKEN
.venv/bin/python tts_ptbr.py \
  --engine pocket \
  --voz vozes/minha_voz.safetensors \
  "Olá! Usando voz exportada sem autenticação."

# Salvar em arquivo
.venv/bin/python tts_ptbr.py \
  --engine pocket \
  --voz vozes/minha_voz.safetensors \
  --salvar saida_clonada.wav \
  --sem-reproduzir \
  "Gerando áudio com voz personalizada."

# Com diferentes velocidades
.venv/bin/python tts_ptbr.py \
  --engine pocket \
  --voz vozes/minha_voz.safetensors \
  --velocidade 1.2 \
  "Fala um pouco mais rápida."
```

## Clonagem em inglês

```bash
# Gravar referência em inglês
.venv/bin/python tts_ptbr.py \
  --engine pocket \
  --idioma en \
  --clonar-voz reference_en.wav \
  --exportar-voz vozes/my_voice_en.safetensors \
  "This is my cloned English voice."

# Usar depois
.venv/bin/python tts_ptbr.py \
  --engine pocket \
  --idioma en \
  --voz vozes/my_voice_en.safetensors \
  "Hello! This is my exported voice."
```

## Fluxo completo

```
minha_voz.wav ──(HF_TOKEN)──▶ clonagem ──▶ falar imediatamente
                                   │
                                   └──▶ minha_voz.safetensors ──(sem login)──▶ qualquer máquina
```

## Armazenar vozes exportadas

Recomendado criar a pasta `vozes/` na raiz do projeto:

```bash
mkdir vozes
.venv/bin/python tts_ptbr.py \
  --engine pocket \
  --clonar-voz gravação.wav \
  --exportar-voz vozes/narrador_principal.safetensors
```

Usar depois:

```bash
.venv/bin/python tts_ptbr.py \
  --engine pocket \
  --voz vozes/narrador_principal.safetensors \
  "Bem-vindos ao episódio de hoje."
```
