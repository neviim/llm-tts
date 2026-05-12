# Instalação

## Instalação automática (recomendada)

O script `install.sh` cuida de tudo: cria o ambiente virtual, instala todas as
dependências e configura o comando `lts` disponível globalmente no terminal.

```bash
# 1. Clonar o repositório
git clone <repositório> llm-tts
cd llm-tts

# 2. Executar o instalador
bash install.sh
```

Ao final, recarregue o terminal (ou execute `source ~/.bashrc`) e use:

```bash
lts "Olá, mundo!"
lts --help
```

---

## O que o instalador faz

| Etapa | Descrição |
|---|---|
| Verificação | Confirma Python 3.12+ no sistema |
| `.venv` | Cria ambiente virtual isolado com `uv` (ou `python -m venv` como fallback) |
| Dependências | Instala `requirements.txt` completo dentro do `.venv` |
| `output/` | Garante que o diretório de saída de áudio existe |
| Wrapper `lts` | Cria `~/.local/bin/lts` apontando para o Python do `.venv` |
| PATH | Adiciona `~/.local/bin` ao `~/.bashrc` (ou `~/.zshrc`) se necessário |
| Verificação | Confirma que os pacotes principais foram instalados corretamente |

O comando `lts` funciona de qualquer diretório sem precisar ativar o `.venv`.

---

## Opções do instalador

```
bash install.sh [--reinstalar]
```

| Flag | Descrição |
|---|---|
| *(sem flags)* | Mantém o `.venv` existente, reinstala dependências e recria o wrapper |
| `--reinstalar` | Remove e recria o `.venv` do zero |

---

## Requisitos do sistema

- **Python 3.12+** — versão mínima exigida
- **`uv`** (opcional, recomendado) — instalação significativamente mais rápida

Se `uv` não estiver disponível o instalador usa `pip`/`venv` automaticamente.

### Instalar uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Instalar Python 3.12 (Ubuntu/Debian)

```bash
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install python3.12 python3.12-venv
```

---

## Instalação manual (alternativa)

Se preferir controle total sobre cada etapa:

```bash
# 1. Criar ambiente virtual
uv venv .venv --python 3.12
# ou: python3.12 -m venv .venv

# 2. Instalar dependências
uv pip install --python .venv/bin/python -r requirements.txt
# ou: .venv/bin/pip install -r requirements.txt

# 3. Verificar
.venv/bin/python tts_ptbr.py --listar-vozes
```

Para ter o comando `lts` disponível globalmente, crie o wrapper manualmente:

```bash
mkdir -p ~/.local/bin
cat > ~/.local/bin/lts <<'EOF'
#!/usr/bin/env bash
exec "/caminho/para/llm-tts/.venv/bin/python" "/caminho/para/llm-tts/tts_ptbr.py" "$@"
EOF
chmod +x ~/.local/bin/lts

# Garantir que ~/.local/bin está no PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

---

## Token HuggingFace (engine pocket)

O engine `pocket` usa o modelo gated `kyutai/pocket-tts` no HuggingFace.
Um token válido é necessário para baixar o modelo no primeiro uso.
O engine `edge` (padrão) funciona sem nenhuma configuração.

### Configuração automática pelo instalador

O `install.sh` copia `.env.example → .env` automaticamente caso o arquivo
não exista, e exibe um aviso ao final com os passos necessários:

```
┌─ Engine pocket requer HuggingFace Token ──────────────────────┐
│  1. Obtenha seu token: https://huggingface.co/settings/tokens │
│  2. Aceite os termos:  https://huggingface.co/kyutai/pocket-tts│
│  3. Edite o arquivo:   .env                                   │
│     Substitua: HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx   │
└───────────────────────────────────────────────────────────────┘
```

### Configuração manual

Edite o `.env` na raiz do projeto:

```bash
# .env
HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Obtenha o token em <https://huggingface.co/settings/tokens> e aceite os
termos em <https://huggingface.co/kyutai/pocket-tts>.

---

## Download do modelo pocket (automático no primeiro uso)

O modelo é baixado automaticamente (~500 MB) para `~/.cache/huggingface/`
na primeira execução com `--engine pocket`:

```bash
lts --engine pocket "Olá"
```

As execuções seguintes usam o modelo em cache — sem download.

---

## Servidor REST

O servidor REST já está incluído em `requirements.txt` (FastAPI + uvicorn).
Para iniciá-lo após a instalação:

```bash
.venv/bin/uvicorn server.server:app --host 0.0.0.0 --port 8080
```

Documentação interativa disponível em `http://localhost:8080/docs`.
