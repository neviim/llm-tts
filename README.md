# llm-tts — TTS Português BR

Sintetizador de voz por linha de comando com dois engines TTS, 26 vozes, 6 idiomas, cache, fila assíncrona e API REST.

| Engine   | Tipo   | Internet         | Offline |
|----------|--------|------------------|---------|
| `edge`   | Neural | Sempre           | Não     |
| `pocket` | Neural | Só no 1º download| Sim     |

---

## Instalação

```bash
uv venv .venv --python 3.12
uv pip install -r requirements.txt
```

Requisitos: Python 3.10+, [`uv`](https://docs.astral.sh/uv/getting-started/installation/).

---

## Início rápido

```bash
# Frase direta (edge, voz Francisca)
.venv/bin/python tts_ptbr.py "Olá, mundo!"

# Pocket TTS local
.venv/bin/python tts_ptbr.py --engine pocket "Olá!"

# Salvar como MP3 sem reproduzir
.venv/bin/python tts_ptbr.py --salvar saida.mp3 --sem-reproduzir "Olá!"

# Falar o que está no clipboard
.venv/bin/python tts_ptbr.py --clipboard

# Modo interativo
.venv/bin/python tts_ptbr.py
```

---

## Referência de argumentos

| Argumento              | Atalho | Descrição                                                              |
|------------------------|--------|------------------------------------------------------------------------|
| `texto`                |        | Texto a converter (posicional, opcional)                               |
| `--engine`             | `-e`   | Engine: `edge` (padrão) ou `pocket`                                    |
| `--voz`                | `-v`   | Voz: nome embutido, `.safetensors` ou `.wav` (pocket)                  |
| `--idioma LANG`        |        | [pocket] Idioma: `pt` (padrão), `en`, `fr`, `de`, `it`, `es`          |
| `--velocidade N`       |        | Velocidade de fala: 0.1–4.0, padrão 1.0                                |
| `--streaming`          |        | [pocket] Reproduz em tempo real enquanto gera                          |
| `--preprocessar`       | `-p`   | Expande abreviações, moeda, ordinais, siglas e números (PT-BR)         |
| `--salvar ARQUIVO`     |        | Salva o áudio gerado (`.wav`, `.flac`, `.ogg`, `.mp3`)                 |
| `--formato FMT`        |        | Formato explícito (padrão: inferido pela extensão)                     |
| `--sample-rate HZ`     |        | Taxa de amostragem do arquivo de saída em Hz                           |
| `--sem-reproduzir`     |        | Salva sem reproduzir — requer `--salvar`                               |
| `--arquivo TXT`        |        | Arquivo de texto com uma frase por linha                               |
| `--juntar`             |        | Concatena todas as frases num único arquivo — requer `--salvar`        |
| `--clipboard`          |        | Lê o texto do clipboard em vez de argumento ou stdin                   |
| `--sem-cache`          |        | Força nova síntese, ignorando o cache                                  |
| `--limpar-cache`       |        | Remove todos os áudios em cache e sai                                  |
| `--salvar-config`      |        | Persiste os parâmetros atuais em `config.yaml` e sai                   |
| `--clonar-voz ARQUIVO` |        | [pocket] Áudio de referência para clonagem de voz (requer login HF)   |
| `--exportar-voz DEST`  |        | [pocket] Exporta voice state para `.safetensors`                       |
| `--listar-vozes`       |        | Lista vozes embutidas do engine selecionado                            |

---

## Engines e vozes

### Edge TTS — Microsoft (`--engine edge`)

3 vozes neurais nativas PT-BR, online. Padrão do script.

| Nome        | Voz Microsoft         | Gênero            |
|-------------|-----------------------|-------------------|
| `francisca` | pt-BR-FranciscaNeural | Feminina (padrão) |
| `antonio`   | pt-BR-AntonioNeural   | Masculino         |
| `thalita`   | pt-BR-ThalitaNeural   | Feminina          |

```bash
.venv/bin/python tts_ptbr.py --voz antonio "Boa tarde!"
.venv/bin/python tts_ptbr.py --listar-vozes
```

### Pocket TTS — Kyutai (`--engine pocket`)

26 vozes neurais, modelo local (~500 MB, download único). `rafael` tem embedding nativo para PT; as demais funcionam melhor com `--idioma en`.

| Nome              | Gênero    | Login HF |
|-------------------|-----------|----------|
| `rafael` (padrão) | Masculino | Não      |
| `cosette`         | Feminino  | Sim      |
| `marius`          | Masculino | Sim      |
| `javert`          | Masculino | Sim      |
| `alba`            | Feminino  | Sim      |
| `jean`            | Masculino | Sim      |
| `anna`            | Feminino  | Sim      |
| `vera`            | Feminino  | Sim      |
| `fantine`         | Feminino  | Sim      |
| `charles`         | Masculino | Sim      |
| `paul`            | Masculino | Sim      |
| `eponine`         | Feminino  | Sim      |
| `azelma`          | Feminino  | Sim      |
| `george`          | Masculino | Sim      |
| `mary`            | Feminino  | Sim      |
| `jane`            | Feminino  | Sim      |
| `michael`         | Masculino | Sim      |
| `eve`             | Feminino  | Sim      |
| `bill_boerst`     | Masculino | Sim      |
| `peter_yearsley`  | Masculino | Sim      |
| `stuart_bell`     | Masculino | Sim      |
| `caro_davy`       | Feminino  | Sim      |
| `estelle`         | Feminino  | Sim (IT) |
| `giovanni`        | Masculino | Sim (IT) |
| `lola`            | Feminino  | Sim (ES) |
| `juergen`         | Masculino | Sim (DE) |

```bash
.venv/bin/python tts_ptbr.py --engine pocket --voz rafael "Olá!"
.venv/bin/python tts_ptbr.py --engine pocket --voz alba --idioma en "Hello world"
.venv/bin/python tts_ptbr.py --engine pocket --listar-vozes
```

---

## Idiomas — Pocket TTS (`--idioma`)

O modelo Kyutai suporta 6 idiomas. Cada idioma usa um modelo separado, baixado uma vez.

| Código | Idioma    | Vozes recomendadas                        |
|--------|-----------|-------------------------------------------|
| `pt`   | Português | `rafael`                                  |
| `en`   | Inglês    | `george`, `mary`, `anna`, `alba`, `eve`   |
| `fr`   | Francês   | `cosette`, `marius`, `fantine`, `jean`    |
| `de`   | Alemão    | `juergen`, `caro_davy`                    |
| `it`   | Italiano  | `giovanni`, `estelle`                     |
| `es`   | Espanhol  | `lola`                                    |

```bash
.venv/bin/python tts_ptbr.py --engine pocket --idioma en --voz george "Hello world"
.venv/bin/python tts_ptbr.py --engine pocket --idioma fr --voz fantine "Bonjour!"
.venv/bin/python tts_ptbr.py --engine pocket --idioma de --voz juergen "Guten Tag!"
```

---

## Pré-processamento de texto (`--preprocessar`)

Expande abreviações, moeda, porcentagem, ordinais, siglas e números para PT-BR antes de enviar ao engine.

```bash
.venv/bin/python tts_ptbr.py --preprocessar "R$ 1.250,50 — 3º lugar, Dr. Silva com 98,5%"
# → "mil, duzentos e cinquenta reais e cinquenta centavos — terceiro lugar,
#    Doutor Silva com noventa e oito vírgula cinco por cento"
```

| Entrada        | Saída                                  |
|----------------|----------------------------------------|
| `R$ 10,50`     | dez reais e cinquenta centavos         |
| `98,5%`        | noventa e oito vírgula cinco por cento |
| `3º lugar`     | terceiro lugar                         |
| `2ª edição`    | segunda edição                         |
| `TTS`, `IBM`   | T T S, I B M                          |
| `Dr. Ana`      | Doutora Ana                            |
| `Av. Paulista` | Avenida Paulista                       |
| `nº 100`       | número cem                             |

---

## Saída de áudio

### Formatos suportados

`wav` (padrão), `flac`, `ogg`, `mp3`.

```bash
# Salva em output/ quando só o nome do arquivo é informado
.venv/bin/python tts_ptbr.py --salvar saida.wav "Olá!"
.venv/bin/python tts_ptbr.py --salvar saida.flac "Olá!"
.venv/bin/python tts_ptbr.py --salvar saida.mp3 "Olá!"

# Forçar formato independente da extensão
.venv/bin/python tts_ptbr.py --salvar saida --formato mp3 "Olá!"

# Salvar sem reproduzir
.venv/bin/python tts_ptbr.py --salvar saida.wav --sem-reproduzir "Olá!"

# Taxa de amostragem personalizada
.venv/bin/python tts_ptbr.py --salvar saida.flac --sample-rate 44100 "Olá!"
```

### Processamento em lote (`--arquivo`)

Processa um arquivo com uma frase por linha. Com `tqdm` instalado, exibe barra de progresso automática.

```bash
# Gera frase_001.wav, frase_002.wav, ...
.venv/bin/python tts_ptbr.py --arquivo frases.txt --salvar frase.wav

# Junta tudo em um único arquivo
.venv/bin/python tts_ptbr.py --arquivo frases.txt --salvar completo.wav --juntar

# Com pré-processamento
.venv/bin/python tts_ptbr.py --arquivo frases.txt --preprocessar --salvar saida.wav --juntar
```

### Stdin via pipe

```bash
echo "Olá, mundo!" | .venv/bin/python tts_ptbr.py
cat frases.txt | .venv/bin/python tts_ptbr.py --salvar saida.wav --juntar
```

---

## Velocidade de fala (`--velocidade`)

Controla a velocidade por resampling (afeta pitch proporcionalmente). Funciona com qualquer engine.

```bash
.venv/bin/python tts_ptbr.py --velocidade 0.75 "Fala devagar"   # 25% mais lento
.venv/bin/python tts_ptbr.py --velocidade 1.5  "Fala rápido"    # 50% mais rápido
.venv/bin/python tts_ptbr.py --velocidade 2.0  "Bem rápido"
```

---

## Streaming em tempo real (`--streaming`)

Reproduz o áudio enquanto gera — menor latência em textos longos. Exclusivo do engine `pocket`.

```bash
.venv/bin/python tts_ptbr.py --engine pocket --streaming "Texto longo aqui..."
.venv/bin/python tts_ptbr.py --engine pocket --streaming --voz alba --idioma en "Long text"
```

> `--streaming` é incompatível com `--salvar` (reprodução em tempo real apenas).

---

## Clonagem de voz (pocket)

Requer aceitar os termos em <https://huggingface.co/kyutai/pocket-tts> e um token HuggingFace.

**Configurar token (recomendado via `.env`):**

```bash
cp .env.example .env
# Edite .env: HF_TOKEN=hf_xxxx
```

O token é lido automaticamente do `.env` ou de `HF_TOKEN` no ambiente. Se ausente, o script oferece login interativo via `uvx hf auth login`. Obtenha o token em <https://huggingface.co/settings/tokens>.

```bash
# Clonar e falar imediatamente
.venv/bin/python tts_ptbr.py --engine pocket --clonar-voz minha_voz.wav "Texto aqui"

# Clonar, falar e exportar para reuso futuro
.venv/bin/python tts_ptbr.py --engine pocket \
  --clonar-voz minha_voz.wav \
  --exportar-voz minha_voz.safetensors \
  "Texto aqui"

# Apenas exportar sem falar
.venv/bin/python tts_ptbr.py --engine pocket \
  --clonar-voz minha_voz.wav \
  --exportar-voz minha_voz.safetensors
```

**Usar voz exportada (sem login):**

```bash
.venv/bin/python tts_ptbr.py --engine pocket --voz minha_voz.safetensors "Texto aqui"
```

O `.safetensors` encapsula o voice state extraído e funciona em qualquer máquina sem autenticação.

```
minha_voz.wav  ──(login HF)──▶  falar com clonagem
      │
      └──exportar-voz──▶  minha_voz.safetensors  ──(sem login)──▶  qualquer máquina
```

---

## Cache de áudio

Áudios sintetizados são armazenados em `.cache/tts_ptbr/` e reutilizados automaticamente nas chamadas seguintes com o mesmo texto, engine e voz.

```bash
# Segunda chamada retorna instantaneamente
.venv/bin/python tts_ptbr.py "Olá, mundo!"
.venv/bin/python tts_ptbr.py "Olá, mundo!"   # → [cache] Áudio encontrado no cache.

# Forçar nova síntese (sem alterar o cache)
.venv/bin/python tts_ptbr.py --sem-cache "Olá, mundo!"

# Remover todos os áudios em cache
.venv/bin/python tts_ptbr.py --limpar-cache
```

**Configurar tamanho máximo** (padrão: 50 entradas) no `config.yaml`:

```yaml
cache_max: 100
```

---

## Clipboard (`--clipboard`)

Lê o texto copiado e usa como entrada. Combinável com qualquer outra flag.

```bash
.venv/bin/python tts_ptbr.py --clipboard
.venv/bin/python tts_ptbr.py --clipboard --engine pocket --voz george --idioma en
.venv/bin/python tts_ptbr.py --clipboard --velocidade 1.3 --salvar saida.wav
```

---

## Configuração padrão (`config.yaml`)

Persiste preferências para não repetir flags a cada uso.

```bash
# Definir pocket + inglês + voz george como padrões
.venv/bin/python tts_ptbr.py --engine pocket --idioma en --voz george --salvar-config

# A partir daí, basta:
.venv/bin/python tts_ptbr.py "Hello world"
```

O arquivo `config.yaml` é criado na pasta do projeto. Todos os campos são opcionais:

```yaml
engine: pocket
idioma: en
voz: george
velocidade: 1.2
streaming: false
preprocessar: false
formato: wav
sample_rate: 44100
cache_max: 50
```

---

## Modo interativo

Iniciado quando nenhum texto é fornecido. Mantém todas as configurações entre frases.

```bash
.venv/bin/python tts_ptbr.py
```

### Comandos

| Comando                           | Ação                                                    |
|-----------------------------------|---------------------------------------------------------|
| `engine <edge\|pocket>`           | Troca o engine em tempo real                            |
| `voz <nome\|arquivo>`             | Troca voz (nome embutido, `.safetensors` ou `.wav`)     |
| `idioma <pt\|en\|fr\|de\|it\|es>` | [pocket] Troca o idioma do modelo                       |
| `velocidade <N>`                  | Velocidade de fala (0.1–4.0, padrão 1.0)                |
| `streaming [on\|off]`             | [pocket] Ativa/desativa reprodução em streaming         |
| `preprocessar [on\|off]`          | Ativa/desativa pré-processamento (toggle)               |
| `salvar <arquivo>`                | Ativa salvamento automático                             |
| `salvar off`                      | Desativa o salvamento                                   |
| `formato <wav\|flac\|ogg\|mp3>`   | Define o formato do arquivo de saída                    |
| `formato off`                     | Volta a inferir formato pela extensão                   |
| `sample-rate <Hz>`                | Define taxa de amostragem (ex: 44100)                   |
| `sample-rate off`                 | Usa sample rate nativo do engine                        |
| `sem-reproduzir`                  | Alterna entre reproduzir / só salvar                    |
| `fila on`                         | Ativa fila assíncrona — não bloqueia entre frases       |
| `fila off`                        | Volta ao modo síncrono                                  |
| `fila ver`                        | Mostra quantas frases estão pendentes                   |
| `fila limpar`                     | Cancela as frases na fila                               |
| `clipboard`                       | Lê e fala o conteúdo do clipboard                       |
| `cache ver`                       | Estatísticas do cache (entradas e tamanho)              |
| `cache limpar`                    | Remove todos os áudios em cache                         |
| `cache on\|off`                   | Ativa/desativa o cache na sessão                        |
| `clonar <arquivo.wav>`            | [pocket] Define arquivo de referência para clonagem     |
| `exportar <destino.safetensors>`  | [pocket] Exporta voice state para reutilização          |
| `config salvar`                   | Persiste as configurações da sessão em `config.yaml`    |
| `config ver`                      | Exibe o conteúdo do `config.yaml` atual                 |
| `status`                          | Mostra configuração atual da sessão                     |
| `sair`                            | Encerra o programa                                      |

### Fila assíncrona

Com `fila on`, cada frase digitada é enfileirada imediatamente — a síntese e reprodução ocorrem em background, permitindo digitar a próxima sem esperar.

```
Texto: fila on
[fila] Ativada — frases serão enfileiradas sem bloquear.

Texto: Primeira frase para falar
[fila] Adicionado. (1 na fila)

Texto: Segunda frase em sequência
[fila] Adicionado. (2 na fila)

Texto: fila ver
[fila] 1 item(s) pendente(s).
```

---

## Servidor REST

API HTTP que expõe todos os recursos do `tts_ptbr.py`.

```bash
.venv/bin/uvicorn server.server:app --host 0.0.0.0 --port 8080 --reload
```

Documentação interativa: `http://localhost:8080/docs`

### Endpoints

| Método | Rota            | Descrição                                    |
|--------|-----------------|----------------------------------------------|
| GET    | `/health`       | Status do servidor                           |
| GET    | `/vozes`        | Lista vozes (`?engine=edge` ou `pocket`)     |
| GET    | `/idiomas`      | Lista idiomas disponíveis (pocket)           |
| POST   | `/preprocessar` | Aplica pré-processamento PT-BR ao texto      |
| POST   | `/tts`          | Sintetiza e retorna áudio (WAV/FLAC/OGG/MP3) |

### Parâmetros do POST /tts

```json
{
  "texto":       "Olá, mundo!",
  "engine":      "edge",
  "voz":         "francisca",
  "idioma":      "pt",
  "velocidade":  1.0,
  "preprocessar": false,
  "formato":     "wav",
  "sample_rate": null
}
```

### Exemplos

```bash
# Edge TTS → MP3
curl -s -X POST http://localhost:8080/tts \
  -H "Content-Type: application/json" \
  -d '{"texto": "Olá, mundo!", "engine": "edge", "formato": "mp3"}' \
  --output saida.mp3

# Pocket TTS em inglês, 1.2× velocidade
curl -s -X POST http://localhost:8080/tts \
  -H "Content-Type: application/json" \
  -d '{"texto": "Hello world", "engine": "pocket", "idioma": "en", "voz": "george", "velocidade": 1.2}' \
  --output saida.wav

# Pré-processar texto
curl -s -X POST http://localhost:8080/preprocessar \
  -H "Content-Type: application/json" \
  -d '{"texto": "R$ 1.250,00 — 3º lugar"}' | python -m json.tool
```

---

## Shell completion

Autocompletar argumentos no bash/zsh com `Tab`.

```bash
# Adicionar ao ~/.bashrc ou ~/.zshrc
eval "$(register-python-argcomplete .venv/bin/python tts_ptbr.py)"

# Ou ativar globalmente para todos os scripts com PYTHON_ARGCOMPLETE_OK
activate-global-python-argcomplete
```

---

## Estrutura do projeto

```
llm-tts/
├── .cache/tts_ptbr/         # cache de áudios (criado automaticamente)
├── .venv/                   # ambiente virtual Python
├── output/                  # áudios salvos (criado automaticamente)
├── vozes/                   # (opcional) .safetensors exportados
├── server/
│   ├── __init__.py
│   └── server.py            # API REST (FastAPI)
├── tests/
│   ├── conftest.py          # fixtures de isolamento
│   ├── test_cli.py          # testes CLI, clipboard, config, fila
│   ├── test_preprocessamento.py
│   ├── test_server.py       # testes da API REST
│   └── test_utils.py        # testes de utilitários e cache
├── .env                     # token HuggingFace — NÃO versionar
├── .env.example             # modelo de configuração
├── .gitignore
├── config.yaml              # configuração padrão (opcional)
├── tts_ptbr.py              # script principal
└── requirements.txt
```

---

## Dependências

| Pacote        | Função                                                |
|---------------|-------------------------------------------------------|
| `edge-tts`    | Engine online — vozes neurais Microsoft pt-BR         |
| `pocket-tts`  | Engine local — modelo neural Kyutai (~500 MB)         |
| `sounddevice` | Reprodução de áudio via hardware                      |
| `soundfile`   | Leitura e escrita de áudio WAV/FLAC/OGG/MP3           |
| `safetensors` | Importação/exportação de voice states                 |
| `scipy`       | Resampling (`--sample-rate`, `--velocidade`)          |
| `num2words`   | Conversão de números para PT-BR (`--preprocessar`)    |
| `pyyaml`      | Leitura e escrita do `config.yaml`                    |
| `pyperclip`   | Leitura do clipboard (`--clipboard`)                  |
| `tqdm`        | Barra de progresso no processamento batch             |
| `argcomplete` | Shell completion para bash/zsh                        |
| `fastapi`     | Servidor REST (opcional)                              |
| `uvicorn`     | Servidor ASGI para a API REST (opcional)              |

---

## Roadmap — o que pode ser implementado

### Engine pocket-tts

| Funcionalidade | Status | Descrição |
|---|---|---|
| Catálogo completo de vozes | ✅ Implementado | 26 vozes com login HF (`--listar-vozes`) |
| Outros idiomas | ✅ Implementado | `--idioma` com 6 línguas (pt, en, fr, de, es, it) |
| `--velocidade <0.5–2.0>` | ✅ Implementado | Controle de velocidade de fala |
| Streaming de áudio | ✅ Implementado | `--streaming` via `generate_audio_stream` |
| Modo servidor | ✅ Implementado | FastAPI REST em `server/server.py` |

### Produtividade

| Funcionalidade | Status | Descrição |
|---|---|---|
| Histórico de áudio | ✅ Implementado | Cache em `.cache/tts_ptbr/` com LRU e `--limpar-cache` |
| Leitura do clipboard | ✅ Implementado | `--clipboard` lê o conteúdo copiado |
| Fila de frases | ✅ Implementado | `fila on` no modo interativo enfileira em background |

### Interface

| Funcionalidade | Status | Descrição |
|---|---|---|
| Barra de progresso | ✅ Implementado | `tqdm` automático no batch com fallback sem dependência |
| Configuração via arquivo | ✅ Implementado | `config.yaml` com `--salvar-config` e defaults persistentes |
| Shell completion | ✅ Implementado | `argcomplete` para bash/zsh |

---

## Referências

- [edge-tts](https://github.com/rany2/edge-tts)
- [Pocket TTS — Kyutai Labs](https://github.com/kyutai-labs/pocket-tts)
- [Modelos de voz — kyutai/tts-voices](https://huggingface.co/kyutai/tts-voices)
