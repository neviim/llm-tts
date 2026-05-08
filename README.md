# llm-tts — TTS Português BR

Converte texto em voz em português brasileiro via linha de comando ou modo interativo.

Suporta dois engines TTS:

| Engine   | Tipo   | Requer internet  | Funciona offline |
|----------|--------|------------------|------------------|
| `edge`   | Neural | Sempre           | Não              |
| `pocket` | Neural | Só no 1º uso     | Sim              |

---

## Requisitos

- Python 3.10+
- `uv` ([instalação](https://docs.astral.sh/uv/getting-started/installation/))
- Conexão com internet para o engine `edge` e para o download inicial do modelo `pocket`

---

## Instalação

```bash
cd llm-tts

uv venv .venv --python 3.12
uv pip install -r requirements.txt
```

---

## Uso

### Frase direta (engine padrão: edge)

```bash
.venv/bin/python tts_ptbr.py "Olá, mundo!"
```

### Escolher engine

```bash
.venv/bin/python tts_ptbr.py --engine edge "Bom dia!"
.venv/bin/python tts_ptbr.py --engine pocket "Bom dia!"
```

### Salvar áudio em arquivo

Quando apenas um nome de arquivo é fornecido (sem diretório), o áudio é salvo automaticamente em `output/`. Caminhos absolutos ou relativos com diretório são usados como estão.

```bash
# Salva em output/saida.wav
.venv/bin/python tts_ptbr.py --salvar saida.wav "Olá, mundo!"

# Salva em output/saida.flac a 44100 Hz
.venv/bin/python tts_ptbr.py --salvar saida.flac --sample-rate 44100 "Olá!"

# Salva em output/saida.ogg sem reproduzir
.venv/bin/python tts_ptbr.py --salvar saida.ogg --sem-reproduzir "Olá!"

# Forçar formato independente da extensão
.venv/bin/python tts_ptbr.py --salvar saida --formato mp3 "Olá!"

# Caminho personalizado (absoluto ou com subpasta)
.venv/bin/python tts_ptbr.py --salvar /tmp/teste.wav "Olá!"

# Pocket TTS + salvar
.venv/bin/python tts_ptbr.py --engine pocket --salvar saida.flac "Olá!"
```

Formatos suportados: `wav`, `flac`, `ogg`, `mp3`

### Escolher voz embutida

```bash
.venv/bin/python tts_ptbr.py --voz antonio "Boa tarde!"
.venv/bin/python tts_ptbr.py --engine pocket --voz rafael "Olá!"
```

### Clonagem de voz (pocket)

Requer aceitar os termos em <https://huggingface.co/kyutai/pocket-tts>.

**Autenticação via `.env` (recomendado):**

```bash
cp .env.example .env
# edite .env e coloque seu token: HF_TOKEN=hf_xxxx
```

O token é lido automaticamente do `.env` ou da variável de ambiente `HF_TOKEN`. Se nenhum for encontrado, o script oferece o login interativo via `uvx hf auth login`.

Obtenha seu token em <https://huggingface.co/settings/tokens>.

```bash
# Clonar e falar na hora
.venv/bin/python tts_ptbr.py --engine pocket --clonar-voz minha_voz.wav "Texto aqui"

# Clonar, falar e exportar para reuso futuro
.venv/bin/python tts_ptbr.py --engine pocket \
  --clonar-voz minha_voz.wav \
  --exportar-voz minha_voz.safetensors \
  "Texto aqui"

# Apenas exportar sem falar (útil para preparar a voz)
.venv/bin/python tts_ptbr.py --engine pocket \
  --clonar-voz minha_voz.wav \
  --exportar-voz minha_voz.safetensors
```

### Usar voz exportada (sem login HF)

Após exportar uma vez, o arquivo `.safetensors` pode ser usado por qualquer pessoa sem autenticação:

```bash
.venv/bin/python tts_ptbr.py --engine pocket --voz minha_voz.safetensors "Texto aqui"
```

### Modo interativo

```bash
.venv/bin/python tts_ptbr.py
```

Comandos disponíveis:

| Comando                          | Ação                                              |
|----------------------------------|---------------------------------------------------|
| `voz <nome\|arquivo>`            | Troca voz (nome embutido, .safetensors ou .wav)   |
| `clonar <arquivo.wav>`           | Define arquivo para clonagem de voz (pocket)      |
| `exportar <destino.safetensors>` | Exporta voz atual para reuso (pocket)             |
| `engine <edge\|pocket>`          | Troca o engine em tempo real                      |
| `salvar <arquivo>`               | Ativa salvamento automático para o arquivo        |
| `salvar off`                     | Desativa o salvamento                             |
| `formato <wav\|flac\|ogg\|mp3>`  | Define o formato do arquivo de saída              |
| `formato off`                    | Volta a inferir formato pela extensão             |
| `sample-rate <Hz>`               | Define taxa de amostragem do arquivo (ex: 44100)  |
| `sample-rate off`                | Usa o sample rate nativo do engine               |
| `sem-reproduzir`                 | Alterna entre salvar-e-reproduzir / só salvar     |
| `status`                         | Mostra configuração atual                         |
| `sair`                           | Encerra o programa                                |

### Listar vozes embutidas

```bash
.venv/bin/python tts_ptbr.py --listar-vozes
.venv/bin/python tts_ptbr.py --engine pocket --listar-vozes
```

---

## Vozes disponíveis

### Engine `edge` (Microsoft Edge TTS)

| Nome        | Voz                   | Tipo              |
|-------------|-----------------------|-------------------|
| `francisca` | pt-BR-FranciscaNeural | Feminina (padrão) |
| `antonio`   | pt-BR-AntonioNeural   | Masculino         |
| `thalita`   | pt-BR-ThalitaNeural   | Feminina          |

### Engine `pocket` (Kyutai Pocket TTS)

| Fonte de voz              | Descrição                                | Login HF |
|---------------------------|------------------------------------------|----------|
| `rafael` (padrão)         | Voz masculina portuguesa embutida        | Não      |
| `minha_voz.safetensors`   | Voz exportada previamente                | Não      |
| `minha_voz.wav`           | Clonagem direta do arquivo de áudio      | Sim      |

---

## Fluxo de clonagem de voz

```
minha_voz.wav  ──(login HF necessário)──▶  falar com clonagem
      │
      │  --exportar-voz
      ▼
minha_voz.safetensors  ──(sem login)──▶  falar em qualquer máquina
```

O arquivo `.safetensors` encapsula o voice state extraído e pode ser distribuído ou reutilizado sem necessidade de autenticação no HuggingFace.

---

## Estrutura do projeto

```
llm-tts/
├── .venv/                   # ambiente virtual Python
├── output/                  # áudios gerados (criado automaticamente)
├── vozes/                   # (opcional) pasta para .safetensors exportados
├── .env                     # token HuggingFace — NÃO versionar
├── .env.example             # modelo de configuração
├── .gitignore
├── tts_ptbr.py              # script principal
└── requirements.txt         # dependências
```

---

## Dependências

| Pacote        | Função                                        |
|---------------|-----------------------------------------------|
| `edge-tts`    | Engine online — vozes neurais Microsoft pt-BR |
| `pocket-tts`  | Engine local — modelo neural Kyutai (~500MB)  |
| `sounddevice` | Reprodução de áudio via hardware              |
| `soundfile`   | Decodificação de áudio MP3/WAV                |
| `safetensors` | Importação/exportação de voice states         |
| `scipy`       | Resampling de áudio (`--sample-rate`)         |

---

## Roadmap — o que pode ser implementado

### Entrada de texto

| Funcionalidade | Descrição |
|---|---|
| Suporte a stdin | Ler texto de pipe: `echo "texto" \| python tts_ptbr.py` |
| `--arquivo <texto.txt>` | Processar arquivo de texto linha por linha |
| Pré-processamento | Expandir abreviações, números por extenso, siglas (ex: "R$ 10" → "dez reais") |

### Engine pocket-tts

| Funcionalidade | Descrição |
|---|---|
| Catálogo completo de vozes | Com login HF desbloqueiam-se ~25 vozes (`alba`, `anna`, `cosette`, etc.) |
| Outros idiomas | O modelo já suporta espanhol, francês, alemão, italiano — basta trocar `language=` |
| `--velocidade <0.5–2.0>` | Controle de velocidade de fala |
| Streaming de áudio | Reproduzir enquanto gera (latência menor) via `generate_audio_stream` |
| Modo servidor | Subir a API REST local do pocket-tts (`pocket-tts serve`) integrada ao script |

### Produtividade

| Funcionalidade | Descrição |
|---|---|
| Histórico de áudio | Cache dos últimos N áudios gerados para não re-sintetizar textos repetidos |
| Leitura do clipboard | Falar o conteúdo copiado (`--clipboard`) |
| Processamento em lote | Converter uma lista de frases em arquivos numerados automaticamente |
| Fila de frases | Enfileirar múltiplas entradas no modo interativo sem esperar cada reprodução |

### Interface

| Funcionalidade | Descrição |
|---|---|
| Barra de progresso | Indicar andamento no download do modelo e na geração de áudio longo |
| Configuração via arquivo | `config.yaml` com engine, voz e parâmetros padrão persistentes |
| Shell completion | Autocompletar argumentos no bash/zsh |

---

## Referências

- [edge-tts](https://github.com/rany2/edge-tts)
- [Pocket TTS — Kyutai Labs](https://github.com/kyutai-labs/pocket-tts)
- [Modelos de voz — kyutai/tts-voices](https://huggingface.co/kyutai/tts-voices)
