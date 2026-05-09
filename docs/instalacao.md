# Instalação

## Requisitos

- Python 3.10 ou superior
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/) — gerenciador de pacotes rápido

## Passo a passo

```bash
# 1. Clonar o repositório
git clone <repositório> llm-tts
cd llm-tts

# 2. Criar ambiente virtual com Python 3.12
uv venv .venv --python 3.12

# 3. Instalar dependências
uv pip install -r requirements.txt
```

## Verificar instalação

```bash
.venv/bin/python tts_ptbr.py --listar-vozes
```

Saída esperada:

```
Vozes disponíveis (engine: edge)
  francisca  pt-BR-FranciscaNeural  [padrão]
  antonio    pt-BR-AntonioNeural
  thalita    pt-BR-ThalitaNeural
```

## Token HuggingFace (pocket TTS — vozes extras)

Necessário apenas para as 25 vozes adicionais do engine `pocket`. A voz `rafael` funciona sem login.

```bash
# Copiar o modelo de configuração
cp .env.example .env
```

Edite o `.env` e insira o token:

```
HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Obtenha o token em <https://huggingface.co/settings/tokens> e aceite os termos em <https://huggingface.co/kyutai/pocket-tts>.

## Download do modelo pocket (automático no primeiro uso)

```bash
.venv/bin/python tts_ptbr.py --engine pocket "Olá"
# Baixa ~500 MB uma única vez para ~/.cache/huggingface/
```

## Servidor REST (opcional)

```bash
uv pip install fastapi uvicorn
.venv/bin/uvicorn server.server:app --port 8080
```
