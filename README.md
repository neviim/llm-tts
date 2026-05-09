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

### Cache de áudio (`--sem-cache`, `--limpar-cache`)

Áudios sintetizados são armazenados em `.cache/tts_ptbr/` e reutilizados automaticamente quando o mesmo texto, engine e voz forem solicitados novamente.

```bash
# Segunda chamada retorna instantaneamente do cache
.venv/bin/python tts_ptbr.py "Olá, mundo!"
.venv/bin/python tts_ptbr.py "Olá, mundo!"   # → [cache] Áudio encontrado no cache.

# Forçar nova síntese
.venv/bin/python tts_ptbr.py --sem-cache "Olá, mundo!"

# Limpar todos os áudios em cache
.venv/bin/python tts_ptbr.py --limpar-cache
```

O tamanho máximo do cache (padrão: 50 entradas) pode ser configurado no `config.yaml`:

```yaml
cache_max: 100
```

No modo interativo: `cache ver` (estatísticas), `cache limpar`, `cache on/off`.

### Falar o texto do clipboard (`--clipboard`)

```bash
# Fala o que está copiado com as configurações atuais
.venv/bin/python tts_ptbr.py --clipboard

# Combinado com qualquer flag
.venv/bin/python tts_ptbr.py --clipboard --engine pocket --voz george --idioma en
.venv/bin/python tts_ptbr.py --clipboard --velocidade 1.3 --salvar saida.wav
```

No modo interativo, o comando `clipboard` lê e fala o conteúdo copiado com as configurações da sessão.

### Configuração padrão (`config.yaml`)

Salva as preferências atuais para não precisar repetir flags a cada execução:

```bash
# Define pocket + inglês + voz george como padrões
.venv/bin/python tts_ptbr.py --engine pocket --idioma en --voz george --salvar-config

# A partir daí, basta:
.venv/bin/python tts_ptbr.py "Hello world"
```

O arquivo `config.yaml` é criado na pasta do projeto. Campos suportados:

```yaml
engine: pocket
idioma: en
voz: george
velocidade: 1.2
streaming: false
preprocessar: false
formato: wav
sample_rate: 44100
```

No modo interativo, use `config salvar` para persistir as configurações da sessão e `config ver` para inspecionar o arquivo atual.

### Escolher voz embutida

```bash
# edge — 3 vozes nativas PT-BR
.venv/bin/python tts_ptbr.py --voz antonio "Boa tarde!"
.venv/bin/python tts_ptbr.py --voz thalita "Olá!"

# pocket — 26 vozes (rafael tem embedding PT nativo; demais funcionam melhor com --idioma en)
.venv/bin/python tts_ptbr.py --engine pocket --voz rafael "Olá!"
.venv/bin/python tts_ptbr.py --engine pocket --voz alba --idioma en "Hello world"
.venv/bin/python tts_ptbr.py --engine pocket --listar-vozes
```

### Idiomas — pocket TTS (`--idioma`)

O modelo Kyutai suporta 6 idiomas. Troca o modelo carregado (cada idioma é baixado uma vez).

```bash
.venv/bin/python tts_ptbr.py --engine pocket --idioma pt "Olá, mundo!"         # Português (padrão)
.venv/bin/python tts_ptbr.py --engine pocket --idioma en --voz george "Hello!"  # Inglês
.venv/bin/python tts_ptbr.py --engine pocket --idioma fr --voz fantine "Bonjour!"  # Francês
.venv/bin/python tts_ptbr.py --engine pocket --idioma de --voz juergen "Guten Tag!"  # Alemão
.venv/bin/python tts_ptbr.py --engine pocket --idioma it --voz giovanni "Ciao!"  # Italiano
.venv/bin/python tts_ptbr.py --engine pocket --idioma es --voz lola "¡Hola!"    # Espanhol
```

| Código | Idioma    | Vozes recomendadas                      |
|--------|-----------|-----------------------------------------|
| `pt`   | Português | `rafael`                                |
| `en`   | Inglês    | `george`, `mary`, `anna`, `alba`, `eve` |
| `fr`   | Francês   | `cosette`, `marius`, `fantine`, `jean`  |
| `de`   | Alemão    | `juergen`, `caro_davy`                  |
| `it`   | Italiano  | `giovanni`, `estelle`                   |
| `es`   | Espanhol  | `lola`                                  |

### Velocidade de fala (`--velocidade`)

Controla a velocidade por resampling (afeta pitch proporcionalmente). Funciona com qualquer engine.

```bash
.venv/bin/python tts_ptbr.py --velocidade 0.75 "Fala devagar"   # 25% mais lento
.venv/bin/python tts_ptbr.py --velocidade 1.5  "Fala rápido"    # 50% mais rápido
.venv/bin/python tts_ptbr.py --velocidade 2.0  "Bem rápido"     # 2× velocidade
.venv/bin/python tts_ptbr.py --engine pocket --velocidade 1.2 --salvar saida.wav "Texto"
```

### Streaming em tempo real (`--streaming`)

Reproduz o áudio enquanto gera — menor latência em textos longos. Exclusivo do engine `pocket`.

```bash
.venv/bin/python tts_ptbr.py --engine pocket --streaming "Texto longo aqui..."
.venv/bin/python tts_ptbr.py --engine pocket --streaming --voz alba --idioma en "Long text here"
```

> Não compatível com `--salvar` (o streaming é reprodução apenas).

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
| `clipboard`                      | Lê e fala o conteúdo do clipboard                 |
| `cache ver`                      | Mostra estatísticas do cache (entradas e tamanho) |
| `cache limpar`                   | Remove todos os áudios em cache                   |
| `cache on\|off`                  | Ativa/desativa o cache para a sessão              |
| `config salvar`                  | Persiste as configurações da sessão em config.yaml |
| `config ver`                     | Exibe o conteúdo atual do config.yaml             |
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
| `--clipboard`          |        | Lê o texto do clipboard em vez de argumento ou stdin            |
| `--sem-cache`          |        | Desativa o cache de áudio para esta execução                    |
| `--limpar-cache`       |        | Remove todos os áudios em cache e sai                           |
| `--salvar-config`      |        | Persiste os parâmetros atuais em `config.yaml` e sai            |
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
| `pyyaml`      | Leitura e escrita do `config.yaml`            |
| `pyperclip`   | Leitura do clipboard (`--clipboard`)          |
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
