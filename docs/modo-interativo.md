# Modo interativo

Iniciado quando nenhum texto é fornecido. Mantém todas as configurações entre frases e aceita comandos de controle.

## Iniciar

```bash
.venv/bin/python tts_ptbr.py
```

Saída:

```
Modo interativo. Digite 'sair' para encerrar.
Engine: edge | Voz: francisca | Idioma: pt | Velocidade: 1.0
Texto:
```

## Falar textos

```
Texto: Bom dia, como você está?
Texto: O tempo hoje está excelente.
Texto: sair
```

---

## Trocar configurações em tempo real

### Engine

```
Texto: engine pocket
[config] Engine: pocket
Texto: Olá com voz local!
Texto: engine edge
[config] Engine: edge
```

### Voz

```
Texto: voz antonio
[config] Voz: antonio
Texto: Boa tarde, sou o Antonio.
Texto: voz francisca
[config] Voz: francisca
```

### Idioma (pocket)

```
Texto: engine pocket
Texto: idioma en
[config] Idioma: en
Texto: voz george
Texto: Hello, this is George speaking.
Texto: idioma fr
Texto: voz cosette
Texto: Bonjour! Je suis Cosette.
```

### Velocidade

```
Texto: velocidade 0.7
[config] Velocidade: 0.7
Texto: Fala mais devagar agora.
Texto: velocidade 1.5
[config] Velocidade: 1.5
Texto: Agora bem mais rápido!
Texto: velocidade 1.0
```

---

## Salvar áudio

```
Texto: salvar narração.wav
[config] Salvando em: narração.wav
Texto: Esta frase será salva em output/narração.wav.
Texto: salvar off
[config] Salvamento desativado.
```

### Formato e sample rate

```
Texto: formato mp3
[config] Formato: mp3
Texto: salvar podcast.mp3
Texto: Esta frase será salva em mp3.
Texto: sample-rate 44100
[config] Sample rate: 44100 Hz
Texto: sample-rate off
```

### Sem reproduzir (só salvar)

```
Texto: sem-reproduzir
[config] Reprodução: desativada
Texto: Esta frase só será salva, não reproduzida.
Texto: sem-reproduzir
[config] Reprodução: ativada
```

---

## Pré-processamento

```
Texto: preprocessar on
[config] Pré-processamento: ativado
Texto: Dr. Silva ganhou R$ 1.500,00 — 1º lugar.
# lê: "Doutor Silva ganhou mil e quinhentos reais — primeiro lugar."
Texto: preprocessar off
```

---

## Fila assíncrona

Com `fila on`, cada frase é enfileirada imediatamente. A síntese e reprodução ocorrem em background — você pode digitar a próxima frase sem esperar a atual terminar.

```
Texto: fila on
[fila] Ativada — frases serão enfileiradas sem bloquear.

Texto: Primeira frase do episódio.
[fila] Adicionado. (1 na fila)

Texto: Segunda frase logo em seguida.
[fila] Adicionado. (2 na fila)

Texto: Terceira frase sem esperar.
[fila] Adicionado. (3 na fila)

Texto: fila ver
[fila] 2 item(s) pendente(s).

Texto: fila limpar
[fila] 1 item(s) cancelado(s).

Texto: fila off
[fila] Modo síncrono restaurado.
```

---

## Cache no modo interativo

```
Texto: cache ver
[cache] 8 entrada(s) — 2.3 MB

Texto: cache off
[cache] Cache desativado para esta sessão.

Texto: cache on
[cache] Cache ativado.

Texto: cache limpar
[cache] 8 entrada(s) removida(s).
```

---

## Clipboard

```
Texto: clipboard
# Lê e fala o texto copiado (Ctrl+C) automaticamente
```

---

## Streaming (pocket)

```
Texto: engine pocket
Texto: streaming on
[config] Streaming: ativado
Texto: Este texto longo será reproduzido em tempo real enquanto é gerado.
Texto: streaming off
```

---

## Clonagem de voz (pocket)

```
Texto: engine pocket
Texto: clonar minha_voz.wav
[pocket] Voice state extraído de minha_voz.wav
Texto: Esta frase usa minha voz clonada.
Texto: exportar vozes/minha_voz.safetensors
[pocket] Voice state exportado: vozes/minha_voz.safetensors
```

---

## Configuração

```
Texto: config ver
engine: edge
voz: francisca
velocidade: 1.0

Texto: engine pocket
Texto: voz george
Texto: idioma en
Texto: config salvar
[config] Salvo em config.yaml.
```

---

## Status da sessão

```
Texto: status
Engine:         pocket
Voz:            george
Idioma:         en
Velocidade:     1.0
Streaming:      off
Pré-processamento: off
Reproduzir:     sim
Fila:           off
Cache:          on
```

---

## Referência de comandos

| Comando | Exemplo | Efeito |
|---|---|---|
| `engine <e>` | `engine pocket` | Troca o engine |
| `voz <v>` | `voz antonio` | Troca a voz |
| `idioma <l>` | `idioma en` | Troca idioma (pocket) |
| `velocidade <n>` | `velocidade 1.5` | Velocidade de fala |
| `streaming on\|off` | `streaming on` | Ativa streaming (pocket) |
| `preprocessar on\|off` | `preprocessar on` | Ativa pré-processamento |
| `salvar <arquivo>` | `salvar saida.wav` | Ativa salvamento |
| `salvar off` | | Desativa salvamento |
| `formato <fmt>` | `formato mp3` | Define formato |
| `formato off` | | Volta a inferir pelo nome |
| `sample-rate <hz>` | `sample-rate 44100` | Define sample rate |
| `sample-rate off` | | Usa sample rate nativo |
| `sem-reproduzir` | | Alterna reprodução |
| `fila on\|off` | `fila on` | Ativa fila assíncrona |
| `fila ver` | | Frases pendentes |
| `fila limpar` | | Cancela a fila |
| `clipboard` | | Lê e fala o clipboard |
| `ler-arquivo <caminho>` | `ler-arquivo capitulo.txt` | Lê o arquivo INTEIRO como um único texto (parágrafos, posts) |
| `cache ver` | | Estatísticas do cache |
| `cache on\|off` | `cache off` | Ativa/desativa cache |
| `cache limpar` | | Esvazia o cache |
| `clonar <arquivo>` | `clonar voz.wav` | Clona voz (pocket) |
| `exportar <dest>` | `exportar voz.safetensors` | Exporta voice state |
| `config ver` | | Exibe config.yaml |
| `config salvar` | | Salva sessão em config.yaml |
| `status` | | Configuração atual |
| `sair` | | Encerra o programa |
