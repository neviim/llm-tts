# Saída de áudio

## Salvar arquivo (`--salvar`)

Quando só o nome do arquivo é informado, salva automaticamente em `output/`.

```bash
# Salva em output/saida.wav
.venv/bin/python tts_ptbr.py --salvar saida.wav "Olá, mundo!"

# Salva em output/narração.flac
.venv/bin/python tts_ptbr.py --salvar narração.flac "Bem-vindos ao sistema."

# Caminho absoluto — salva exatamente onde indicado
.venv/bin/python tts_ptbr.py --salvar /tmp/teste.wav "Olá!"

# Subpasta relativa
.venv/bin/python tts_ptbr.py --salvar audios/capitulo1.wav "Era uma vez..."
```

## Formatos de saída (`--formato`)

Formatos suportados: `wav`, `flac`, `ogg`, `mp3`.

```bash
# Formato inferido pela extensão (recomendado)
.venv/bin/python tts_ptbr.py --salvar saida.mp3  "Olá!"
.venv/bin/python tts_ptbr.py --salvar saida.flac "Olá!"
.venv/bin/python tts_ptbr.py --salvar saida.ogg  "Olá!"

# Forçar formato independente da extensão
.venv/bin/python tts_ptbr.py --salvar saida --formato mp3  "Olá!"   # gera saida.mp3
.venv/bin/python tts_ptbr.py --salvar saida --formato flac "Olá!"   # gera saida.flac
```

## Salvar sem reproduzir (`--sem-reproduzir`)

Exige `--salvar`. Útil para geração em batch ou servidor sem placa de som.

```bash
.venv/bin/python tts_ptbr.py --salvar saida.wav --sem-reproduzir "Olá!"
.venv/bin/python tts_ptbr.py --salvar saida.mp3 --sem-reproduzir --engine pocket "Hello!"
```

## Taxa de amostragem (`--sample-rate`)

Reamostramento de saída. Edge gera 24 kHz; pocket gera 24 kHz. Use para padronizar.

```bash
# Upsampling para 44.1 kHz (CD quality)
.venv/bin/python tts_ptbr.py --salvar saida.wav --sample-rate 44100 "Olá!"

# Downsampling para 16 kHz (ASR / transcrição)
.venv/bin/python tts_ptbr.py --salvar saida.wav --sample-rate 16000 "Olá!"

# Combinado com formato
.venv/bin/python tts_ptbr.py --salvar saida.flac --sample-rate 48000 "Olá!"
```

## Processamento em lote (`--arquivo`)

Arquivo de texto com uma frase por linha. Linhas vazias são ignoradas.

**frases.txt:**
```
Bom dia, senhoras e senhores.
Hoje falaremos sobre inteligência artificial.
Obrigado pela atenção.
```

```bash
# Gera output/frase_001.wav, output/frase_002.wav, output/frase_003.wav
.venv/bin/python tts_ptbr.py --arquivo frases.txt --salvar frase.wav

# Juntar tudo em um único arquivo — output/podcast.wav
.venv/bin/python tts_ptbr.py --arquivo frases.txt --salvar podcast.wav --juntar

# Com pocket TTS + inglês
.venv/bin/python tts_ptbr.py \
  --engine pocket --idioma en --voz george \
  --arquivo frases_en.txt \
  --salvar episodio.wav \
  --juntar

# Com pré-processamento e formato mp3
.venv/bin/python tts_ptbr.py \
  --arquivo frases.txt \
  --preprocessar \
  --salvar narração.mp3 \
  --juntar \
  --sem-reproduzir
```

Arquivos numerados gerados seguem o padding mínimo de 3 dígitos:

| Total de frases | Exemplo de nome |
|-----------------|-----------------|
| 1–999           | `frase_001.wav` |
| 1000+           | `frase_0001.wav` |

## Stdin via pipe

Funciona como `--arquivo`, mas lê do pipe.

```bash
# Pipe simples
echo "Olá, mundo!" | .venv/bin/python tts_ptbr.py

# Múltiplas frases via heredoc
cat <<'EOF' | .venv/bin/python tts_ptbr.py --salvar narração.wav --juntar
Capítulo um.
Era uma vez um programador.
Ele escrevia código todos os dias.
EOF

# Arquivo via cat — equivalente a --arquivo
cat frases.txt | .venv/bin/python tts_ptbr.py --salvar saida.wav --juntar

# Filtrar linhas e converter
grep "NARRADOR:" roteiro.txt | sed 's/NARRADOR: //' | \
  .venv/bin/python tts_ptbr.py --salvar narrador.wav --juntar
```

## Ler arquivo inteiro (`--ler-arquivo`)

Diferente de `--arquivo` (que trata cada linha como uma frase separada em
batch), `--ler-arquivo` lê o **conteúdo todo do arquivo** como um único bloco
de texto. Quebras de linha viram espaço, e espaços/tabs múltiplos são
colapsados — bom para parágrafos, capítulos, posts e transcrições.

```bash
# Ler um capítulo inteiro
.venv/bin/python tts_ptbr.py --ler-arquivo capitulo.txt

# Salvar como um único MP3, com pré-processamento PT-BR
.venv/bin/python tts_ptbr.py --ler-arquivo post.md --salvar post.mp3 -p

# Pocket TTS + streaming (reproduz enquanto gera)
.venv/bin/python tts_ptbr.py -e pocket --streaming --ler-arquivo artigo.txt
```

**Quando usar `--arquivo` vs `--ler-arquivo`:**

| Sua entrada | Use |
|-------------|-----|
| Uma frase por linha (legendas, falas) | `--arquivo` (batch) |
| Texto contínuo (parágrafo, capítulo, post) | `--ler-arquivo` |

Para stdin, o equivalente é `--stdin-inteiro`:

```bash
# Lê todo o stdin como um único texto (não batch)
cat artigo.txt | .venv/bin/python tts_ptbr.py --stdin-inteiro --salvar artigo.mp3
```

### Comandos prontos (usando `referencia/texto1.txt`)

Os exemplos abaixo assumem que você está em `/home/neviim/developer/llm-tts`
(ou outro diretório raiz do projeto). Existem três formas de invocar o Python:

```bash
# (a) Caminho do venv (sem precisar ativar)
.venv/bin/python tts_ptbr.py ...

# (b) Direto, se o venv já estiver ativo
python tts_ptbr.py ...

# (c) Caminhos absolutos — funciona de qualquer diretório
/home/neviim/developer/llm-tts/.venv/bin/python \
  /home/neviim/developer/llm-tts/tts_ptbr.py ...
```

Receitas práticas com o arquivo de referência:

```bash
# 1. Apenas falar (lê todo o arquivo como um texto contínuo)
.venv/bin/python tts_ptbr.py --ler-arquivo referencia/texto1.txt

# 2. Salvar em WAV no output/ (sem reproduzir)
.venv/bin/python tts_ptbr.py --ler-arquivo referencia/texto1.txt \
  --salvar texto1.wav --sem-reproduzir

# 3. Salvar em MP3 com pré-processamento PT-BR
#    (expande Dr., R$, %, números, ordinais, siglas...)
.venv/bin/python tts_ptbr.py --ler-arquivo referencia/texto1.txt \
  -p --salvar texto1.mp3 --sem-reproduzir

# 4. Trocar voz (edge): antonio em vez de francisca
.venv/bin/python tts_ptbr.py --ler-arquivo referencia/texto1.txt \
  --voz antonio --salvar texto1.mp3

# 5. Pocket TTS + streaming (reproduz em tempo real enquanto gera)
.venv/bin/python tts_ptbr.py -e pocket --streaming \
  --ler-arquivo referencia/texto1.txt

# 6. Acelerar a leitura em 25%
.venv/bin/python tts_ptbr.py --ler-arquivo referencia/texto1.txt \
  --velocidade 1.25 --salvar texto1.wav
```

> Sem path em `--salvar` (ex.: `texto1.mp3`), o arquivo vai automaticamente
> para `output/`.

## Velocidade de fala (`--velocidade`)

Intervalo: `0.1` a `4.0`. Padrão: `1.0`. Funciona com qualquer engine.

> A velocidade é aplicada por resampling — o pitch varia proporcionalmente.

```bash
# Mais devagar — útil para didático ou acessibilidade
.venv/bin/python tts_ptbr.py --velocidade 0.7 "Repita após mim: olá."
.venv/bin/python tts_ptbr.py --velocidade 0.5 "Ditado: a casa é azul."

# Mais rápido — resumos, notificações
.venv/bin/python tts_ptbr.py --velocidade 1.5 "Você tem 3 novas mensagens."
.venv/bin/python tts_ptbr.py --velocidade 2.0 "Aviso: bateria fraca."

# Combinando com salvar
.venv/bin/python tts_ptbr.py \
  --velocidade 0.8 \
  --salvar aula_devagar.wav \
  --sem-reproduzir \
  "Hoje estudaremos derivadas. A derivada de x ao quadrado é dois x."
```

## Streaming em tempo real (`--streaming`)

Reproduz enquanto gera — menor latência em textos longos. Exclusivo do engine `pocket`.

```bash
# Streaming básico
.venv/bin/python tts_ptbr.py --engine pocket --streaming \
  "Este é um texto longo que será reproduzido enquanto é gerado, reduzindo a latência."

# Streaming em inglês
.venv/bin/python tts_ptbr.py \
  --engine pocket \
  --streaming \
  --idioma en \
  --voz george \
  "Streaming audio generation allows for lower latency playback."

# Streaming com velocidade
.venv/bin/python tts_ptbr.py \
  --engine pocket \
  --streaming \
  --velocidade 1.2 \
  "Notícia urgente: confira os detalhes a seguir."
```

> `--streaming` não é compatível com `--salvar`.
