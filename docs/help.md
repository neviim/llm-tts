# Ajuda integrada (`--help` / `-h`)

O script possui um `--help` completo com layout colorido, seções organizadas, descrição de cada opção e exemplos reais de execução.

## Como exibir

```bash
python tts_ptbr.py --help
python tts_ptbr.py -h
```

---

## O que é exibido

### Cabeçalho e sintaxe

Mostra o nome, resumo e as três formas de invocar o script:

```
  llm-tts  ·  TTS Português BR
  26 vozes · 6 idiomas · cache · fila assíncrona · API REST

  ──────────────────────────────────────────────────────────────────────

  SINTAXE

  python tts_ptbr.py [opções] [texto]
  echo "texto" | python tts_ptbr.py [opções]
  python tts_ptbr.py  ← modo interativo (sem argumentos)
```

---

### Seção ENGINE E VOZ

```
── ENGINE E VOZ ──────────────────────────────────────────────────────

  -e, --engine  edge|pocket     Engine TTS  (padrão: edge)
                                edge   → online, vozes Microsoft neural PT-BR
                                pocket → local, modelo Kyutai (~500 MB, offline após 1º download)
  $ python tts_ptbr.py -e pocket "Olá!"
  $ python tts_ptbr.py --engine pocket --idioma en "Hello world"

  -v, --voz  NOME               Voz a utilizar
                                edge:   francisca* · antonio · thalita
                                pocket: rafael* · george · cosette · alba · eve · mary · ...
                                pocket: caminho para .safetensors ou .wav (voz clonada)
  $ python tts_ptbr.py --voz antonio "Boa tarde!"
  $ python tts_ptbr.py -e pocket --voz george --idioma en "Hello!"
  $ python tts_ptbr.py -e pocket --voz vozes/minha_voz.safetensors "Texto"

      --idioma  LANG            [pocket] Idioma do modelo  (padrão: pt)
                                pt · en · fr · de · it · es
  $ python tts_ptbr.py -e pocket --idioma fr --voz cosette "Bonjour!"
  $ python tts_ptbr.py -e pocket --idioma de --voz juergen "Guten Tag!"

      --listar-vozes            Lista vozes embutidas do engine selecionado
  $ python tts_ptbr.py --listar-vozes
  $ python tts_ptbr.py -e pocket --listar-vozes
```

---

### Seção SAÍDA DE ÁUDIO

```
── SAÍDA DE ÁUDIO ────────────────────────────────────────────────────

      --salvar  ARQUIVO         Salva o áudio gerado  (sem path → output/)
                                extensões: .wav  .flac  .ogg  .mp3
  $ python tts_ptbr.py --salvar saida.wav "Olá!"
  $ python tts_ptbr.py --salvar /tmp/audio.mp3 --sem-reproduzir "Texto"

      --formato  FMT            Formato explícito  (padrão: inferido pela extensão)
                                wav · flac · ogg · mp3
  $ python tts_ptbr.py --salvar saida --formato mp3 "Olá!"

      --sample-rate  HZ         Taxa de amostragem de saída em Hz
  $ python tts_ptbr.py --salvar hq.flac --sample-rate 44100 "Olá!"
  $ python tts_ptbr.py --salvar asr.wav  --sample-rate 16000 "Texto"

      --sem-reproduzir          Salva sem reproduzir  (requer --salvar)
  $ python tts_ptbr.py --salvar saida.wav --sem-reproduzir "Texto"
```

---

### Seção ENTRADA DE TEXTO

```
── ENTRADA DE TEXTO ──────────────────────────────────────────────────

      --arquivo  TXT            Arquivo com uma frase por linha (batch)
  $ python tts_ptbr.py --arquivo frases.txt --salvar frase.wav
  $ python tts_ptbr.py --arquivo frases.txt --salvar ep.wav --juntar

      --juntar                  Concatena frases em um único arquivo  (requer --salvar)
  $ cat frases.txt | python tts_ptbr.py --salvar completo.wav --juntar

      --clipboard               Lê o texto do clipboard em vez de argumento
  $ python tts_ptbr.py --clipboard
  $ python tts_ptbr.py --clipboard --engine pocket --voz george --idioma en
```

---

### Seção PROCESSAMENTO

```
── PROCESSAMENTO ─────────────────────────────────────────────────────

  -p, --preprocessar            Expande abreviações, moeda, ordinais e números (PT-BR)
                                R$ 1.250,50 → mil duzentos e cinquenta reais e cinquenta centavos
                                3º lugar   → terceiro lugar
                                Dr. Silva  → Doutor Silva
                                98,5%      → noventa e oito vírgula cinco por cento
  $ python tts_ptbr.py -p "R$ 1.250,00 — 3º lugar, Dr. Silva"

      --velocidade  N           Velocidade de fala 0.1–4.0  (padrão: 1.0)
                                < 1.0 → mais lento · > 1.0 → mais rápido  (afeta pitch)
  $ python tts_ptbr.py --velocidade 0.75 "Leitura didática"
  $ python tts_ptbr.py --velocidade 1.5  "Notificação rápida"

      --streaming               [pocket] Reproduz em tempo real enquanto gera
                                menor latência em textos longos · incompatível com --salvar
  $ python tts_ptbr.py -e pocket --streaming "Texto longo aqui..."
```

---

### Seção CLONAGEM DE VOZ

```
── CLONAGEM DE VOZ  [pocket] ─────────────────────────────────────────

      --clonar-voz  ARQUIVO     [pocket] Áudio de referência para clonagem  (requer HF_TOKEN)
  $ python tts_ptbr.py -e pocket --clonar-voz minha_voz.wav "Texto"

      --exportar-voz  DESTINO   [pocket] Exporta voice state para .safetensors
                                arquivo exportado funciona sem login em qualquer máquina
  $ python tts_ptbr.py -e pocket --clonar-voz ref.wav --exportar-voz vozes/voz.safetensors
  $ python tts_ptbr.py -e pocket --voz vozes/voz.safetensors "Reutilizando"
```

---

### Seção CACHE DE ÁUDIO

```
── CACHE DE ÁUDIO ────────────────────────────────────────────────────

      --sem-cache               Força nova síntese ignorando o cache
  $ python tts_ptbr.py --sem-cache "Texto"

      --limpar-cache            Remove todos os áudios em cache e sai
  $ python tts_ptbr.py --limpar-cache
```

---

### Seção CONFIGURAÇÃO

```
── CONFIGURAÇÃO ──────────────────────────────────────────────────────

      --salvar-config           Persiste os parâmetros atuais em config.yaml e sai
                                campos salvos: engine · voz · idioma · velocidade · formato
                                             streaming · preprocessar · sample_rate · cache_max
  $ python tts_ptbr.py --engine pocket --idioma en --voz george --salvar-config
```

---

### Seção EXEMPLOS COMPLETOS

Encerra o help com casos práticos prontos para copiar:

```
── EXEMPLOS COMPLETOS ────────────────────────────────────────────────

  · Falar e salvar em MP3
    $ python tts_ptbr.py --salvar podcast.mp3 --sem-reproduzir "Bom dia, ouvintes!"

  · Batch: converter arquivo → arquivos numerados
    $ python tts_ptbr.py --arquivo frases.txt --salvar frase.wav

  · Batch: juntar tudo em um único WAV
    $ python tts_ptbr.py --arquivo frases.txt --salvar episodio.wav --juntar

  · Pocket TTS em francês com velocidade
    $ python tts_ptbr.py -e pocket --idioma fr --voz cosette --velocidade 0.9 "Bonjour!"

  · Pré-processar + salvar em FLAC 44 kHz
    $ python tts_ptbr.py -p --salvar saida.flac --sample-rate 44100 "Dr. Ana, R$ 500,00"

  · Clipboard → falar com Antonio
    $ python tts_ptbr.py --clipboard --voz antonio

  · Definir pocket+inglês+george como padrões
    $ python tts_ptbr.py -e pocket --idioma en --voz george --salvar-config

  · Modo interativo
    $ python tts_ptbr.py

  · Servidor REST
    $ uvicorn server.server:app --host 0.0.0.0 --port 8080

  ──────────────────────────────────────────────────────────────────────
  Documentação completa:  docs/index.md
```

---

## Comportamento de cores

O help usa cores ANSI automaticamente quando a saída é um terminal:

| Elemento | Cor |
|---|---|
| Cabeçalho de seção | Ciano |
| Nome da flag (`--engine`) | Amarelo |
| Metavar (`edge\|pocket`) | Magenta |
| Bullets e notas | Cinza (dim) |
| Exemplos `$ comando` | Verde |

Quando a saída é redirecionada para arquivo ou pipe, as cores são desativadas automaticamente:

```bash
# Salvar help em arquivo — sem códigos ANSI
python tts_ptbr.py --help > ajuda.txt

# Paginar com less (preserva cores)
python tts_ptbr.py --help | less -R
```
