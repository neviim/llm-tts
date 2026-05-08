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

### Pré-processamento de texto (`--preprocessar`)

Expande abreviações, moeda, porcentagem, ordinais, siglas e números para PT-BR antes de enviar ao engine.

```bash
.venv/bin/python tts_ptbr.py --preprocessar "R$ 1.250,50 — 3º lugar, Dr. Silva com 98,5%"
# → "mil, duzentos e cinquenta reais e cinquenta centavos — terceiro lugar, Doutor Silva com noventa e oito vírgula cinco por cento"
```

| Entrada        | Saída                                      |
|----------------|--------------------------------------------|
| `R$ 10,50`     | dez reais e cinquenta centavos             |
| `98,5%`        | noventa e oito vírgula cinco por cento     |
| `3º lugar`     | terceiro lugar                             |
| `2ª edição`    | segunda edição                             |
| `TTS`, `IBM`   | T T S, I B M                              |
| `Dr. Ana`      | Doutora Ana                                |
| `Av. Paulista` | Avenida Paulista                           |
| `nº 100`       | número cem                                 |

### Ler de arquivo de texto (`--arquivo`)

Processa um arquivo com uma frase por linha. Com `--salvar`, gera arquivos numerados automaticamente.

```bash
# Gera frase_001.wav, frase_002.wav, ...
.venv/bin/python tts_ptbr.py --arquivo frases.txt --salvar frase.wav

# Junta tudo em um único arquivo
.venv/bin/python tts_ptbr.py --arquivo frases.txt --salvar completo.wav --juntar

# Combinado com pré-processamento
.venv/bin/python tts_ptbr.py --arquivo frases.txt --preprocessar --salvar saida.wav --juntar
```

### Ler do stdin via pipe

```bash
echo "Olá, mundo!" | .venv/bin/python tts_ptbr.py
cat frases.txt | .venv/bin/python tts_ptbr.py --salvar saida.wav --juntar
```

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
| `preprocessar [on\|off]`         | Ativa/desativa pré-processamento (toggle)         |
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
| `idioma <pt\|en\|fr\|de\|it\|es>` | [pocket] Troca o idioma do modelo em tempo real  |
| `velocidade <N>`                 | Velocidade de fala (0.1–4.0, padrão 1.0)          |
| `streaming [on\|off]`            | [pocket] Ativa/desativa reprodução em streaming   |
| `sem-reproduzir`                 | Alterna entre salvar-e-reproduzir / só salvar     |
| `status`                         | Mostra configuração atual                         |
| `sair`                           | Encerra o programa                                |

### Listar vozes embutidas

```bash
.venv/bin/python tts_ptbr.py --listar-vozes
.venv/bin/python tts_ptbr.py --engine pocket --listar-vozes
```

---

## Referência de argumentos

| Argumento              | Atalho | Descrição                                                       |
|------------------------|--------|-----------------------------------------------------------------|
| `texto`                |        | Texto a converter (posicional, opcional)                        |
| `--engine`             | `-e`   | Engine TTS: `edge` (padrão) ou `pocket`                         |
| `--voz`                | `-v`   | Voz: nome embutido, caminho `.safetensors` ou `.wav` (pocket)   |
| `--clonar-voz ARQUIVO` |        | [pocket] Áudio de referência para clonagem de voz               |
| `--exportar-voz DEST`  |        | [pocket] Exporta voice state para `.safetensors`                |
| `--salvar ARQUIVO`     |        | Salva o áudio gerado (`.wav`, `.flac`, `.ogg`, `.mp3`)          |
| `--formato FMT`        |        | Formato de saída explícito (padrão: inferido pela extensão)     |
| `--sample-rate HZ`     |        | Taxa de amostragem do arquivo de saída em Hz                    |
| `--sem-reproduzir`     |        | Salva sem reproduzir — requer `--salvar`                        |
| `--arquivo TXT`        |        | Arquivo de texto com uma frase por linha                        |
| `--idioma LANG`        |        | [pocket] Idioma do modelo: `pt` (padrão), `en`, `fr`, `de`, `it`, `es` |
| `--velocidade N`       |        | Velocidade de fala (0.1–4.0, padrão 1.0)                        |
| `--streaming`          |        | [pocket] Reproduz em tempo real enquanto gera                   |
| `--preprocessar`       | `-p`   | Expande abreviações, moeda, ordinais, siglas e números (PT-BR)  |
| `--juntar`             |        | Concatena todas as frases num único áudio — requer `--salvar`   |
| `--listar-vozes`       |        | Lista vozes embutidas do engine selecionado                     |

---

## Vozes disponíveis

### Engine `edge` (Microsoft Edge TTS)

| Nome        | Voz                   | Tipo              |
|-------------|-----------------------|-------------------|
| `francisca` | pt-BR-FranciscaNeural | Feminina (padrão) |
| `antonio`   | pt-BR-AntonioNeural   | Masculino         |
| `thalita`   | pt-BR-ThalitaNeural   | Feminina          |

### Engine `pocket` (Kyutai Pocket TTS)

26 vozes disponíveis. `rafael` tem embedding nativo para PT; as demais funcionam melhor com `--idioma en`.

| Nome          | Gênero   | Login HF |
|---------------|----------|----------|
| `rafael` (padrão) | Masculino | Não  |
| `cosette`     | Feminino  | Sim      |
| `marius`      | Masculino | Sim      |
| `alba`        | Feminino  | Sim      |
| `anna`        | Feminino  | Sim      |
| `george`      | Masculino | Sim      |
| `mary`        | Feminino  | Sim      |
| … +18 vozes   | —         | Sim      |

Voz exportada previamente: `minha_voz.safetensors` (sem login)  
Clonagem direta: `minha_voz.wav` (requer login HF)

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
├── server/
│   ├── __init__.py
│   └── server.py            # API REST (FastAPI)
├── tests/
│   ├── test_cli.py
│   ├── test_preprocessamento.py
│   ├── test_server.py
│   └── test_utils.py
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
| `soundfile`   | Leitura e escrita de áudio WAV/FLAC/OGG/MP3   |
| `safetensors` | Importação/exportação de voice states         |
| `scipy`       | Resampling de áudio (`--sample-rate`, `--velocidade`) |
| `num2words`   | Conversão de números para PT-BR (`--preprocessar`) |
| `fastapi`     | Servidor REST (opcional)                      |
| `uvicorn`     | Servidor ASGI para a API REST (opcional)      |

---

## Servidor REST

Inicia uma API HTTP que expõe todos os recursos do `tts_ptbr.py`:

```bash
.venv/bin/uvicorn server.server:app --host 0.0.0.0 --port 8080 --reload
```

Documentação interativa disponível em `http://localhost:8080/docs`.

### Endpoints

| Método | Rota           | Descrição                                  |
|--------|----------------|--------------------------------------------|
| GET    | `/health`      | Status do servidor                         |
| GET    | `/vozes`       | Lista vozes (`?engine=edge` ou `pocket`)   |
| GET    | `/idiomas`     | Lista idiomas disponíveis (pocket)         |
| POST   | `/preprocessar`| Aplica pré-processamento PT-BR ao texto    |
| POST   | `/tts`         | Sintetiza e retorna áudio (WAV/FLAC/OGG/MP3) |

### Exemplo

```bash
curl -s -X POST http://localhost:8080/tts \
  -H "Content-Type: application/json" \
  -d '{"texto": "Olá, mundo!", "engine": "edge", "formato": "mp3"}' \
  --output saida.mp3

# Pocket TTS com velocidade e idioma
curl -s -X POST http://localhost:8080/tts \
  -H "Content-Type: application/json" \
  -d '{"texto": "Hello world", "engine": "pocket", "idioma": "en", "voz": "george", "velocidade": 1.2}' \
  --output saida.wav
```

---

## Roadmap — o que pode ser implementado

### Produtividade

| Funcionalidade | Descrição |
|---|---|
| Histórico de áudio | Cache dos últimos N áudios gerados para não re-sintetizar textos repetidos |
| Leitura do clipboard | Falar o conteúdo copiado (`--clipboard`) |
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
