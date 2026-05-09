# Uso básico

## Frase direta

O argumento posicional `texto` é o mais simples:

```bash
.venv/bin/python tts_ptbr.py "Olá, mundo!"
.venv/bin/python tts_ptbr.py "Bom dia! Como você está?"
```

## Escolher engine (`--engine` / `-e`)

```bash
# Edge TTS — online, vozes Microsoft (padrão)
.venv/bin/python tts_ptbr.py --engine edge "Olá!"

# Pocket TTS — local, modelo Kyutai
.venv/bin/python tts_ptbr.py --engine pocket "Olá!"
.venv/bin/python tts_ptbr.py -e pocket "Olá!"
```

| Engine   | Internet | Offline | Vozes |
|----------|----------|---------|-------|
| `edge`   | Sempre   | Não     | 3 PT-BR |
| `pocket` | 1º uso   | Sim     | 26 multilíngues |

## Escolher voz (`--voz` / `-v`)

### Vozes Edge

```bash
.venv/bin/python tts_ptbr.py --voz francisca "Olá!"   # feminino (padrão)
.venv/bin/python tts_ptbr.py --voz antonio   "Olá!"   # masculino
.venv/bin/python tts_ptbr.py --voz thalita   "Olá!"   # feminino
```

### Vozes Pocket

```bash
.venv/bin/python tts_ptbr.py --engine pocket --voz rafael  "Olá!"   # masculino PT (padrão)
.venv/bin/python tts_ptbr.py --engine pocket --voz george  "Hello!" # masculino EN
.venv/bin/python tts_ptbr.py --engine pocket --voz mary    "Hello!" # feminino EN
.venv/bin/python tts_ptbr.py --engine pocket --voz cosette "Bonjour!" --idioma fr
```

## Listar vozes disponíveis (`--listar-vozes`)

```bash
# Vozes do engine edge
.venv/bin/python tts_ptbr.py --listar-vozes

# Vozes do engine pocket
.venv/bin/python tts_ptbr.py --engine pocket --listar-vozes
```

Saída para `--engine pocket --listar-vozes`:

```
Vozes disponíveis (engine: pocket)
  rafael          [padrão]
  cosette
  marius
  javert
  alba
  ...
```

## Escolher idioma (`--idioma`) — apenas pocket

```bash
# Português (padrão)
.venv/bin/python tts_ptbr.py --engine pocket --idioma pt --voz rafael "Olá!"

# Inglês
.venv/bin/python tts_ptbr.py --engine pocket --idioma en --voz george "Hello, world!"

# Francês
.venv/bin/python tts_ptbr.py --engine pocket --idioma fr --voz cosette "Bonjour!"

# Alemão
.venv/bin/python tts_ptbr.py --engine pocket --idioma de --voz juergen "Guten Tag!"

# Italiano
.venv/bin/python tts_ptbr.py --engine pocket --idioma it --voz giovanni "Ciao!"

# Espanhol
.venv/bin/python tts_ptbr.py --engine pocket --idioma es --voz lola "¡Hola!"
```

## Combinando engine + voz + idioma

```bash
# Notícia em inglês com voz feminina
.venv/bin/python tts_ptbr.py \
  --engine pocket \
  --idioma en \
  --voz mary \
  "Breaking news: scientists discover new exoplanet."

# PT-BR com Antonio (Edge)
.venv/bin/python tts_ptbr.py \
  --engine edge \
  --voz antonio \
  "Bom dia, ouvintes da Rádio Nacional!"
```
