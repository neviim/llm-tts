# Servidor REST

API HTTP com FastAPI que expõe todos os recursos do `tts_ptbr.py`.

## Iniciar o servidor

```bash
# Desenvolvimento (reload automático)
.venv/bin/uvicorn server.server:app --host 0.0.0.0 --port 8080 --reload

# Produção
.venv/bin/uvicorn server.server:app --host 0.0.0.0 --port 8080 --workers 2
```

Documentação interativa (Swagger): `http://localhost:8080/docs`

---

## GET /health

Verifica se o servidor está no ar.

```bash
curl http://localhost:8080/health
```

Resposta:

```json
{"status": "ok"}
```

---

## GET /vozes

Lista as vozes disponíveis para um engine.

```bash
# Vozes do engine edge (padrão)
curl http://localhost:8080/vozes
curl "http://localhost:8080/vozes?engine=edge"
```

Resposta:

```json
{
  "engine": "edge",
  "padrao": "francisca",
  "vozes": {
    "francisca": "pt-BR-FranciscaNeural",
    "antonio": "pt-BR-AntonioNeural",
    "thalita": "pt-BR-ThalitaNeural"
  }
}
```

```bash
# Vozes do engine pocket
curl "http://localhost:8080/vozes?engine=pocket"
```

Resposta:

```json
{
  "engine": "pocket",
  "padrao": "rafael",
  "vozes": {
    "rafael": "rafael",
    "cosette": "cosette",
    "george": "george",
    ...
  }
}
```

---

## GET /idiomas

Lista os idiomas disponíveis no engine pocket.

```bash
curl http://localhost:8080/idiomas
```

Resposta:

```json
{
  "padrao": "pt",
  "idiomas": ["pt", "en", "fr", "de", "it", "es"]
}
```

---

## POST /preprocessar

Aplica pré-processamento PT-BR ao texto sem sintetizar.

```bash
curl -s -X POST http://localhost:8080/preprocessar \
  -H "Content-Type: application/json" \
  -d '{"texto": "Dr. Silva ganhou R$ 1.250,00 em 1º lugar"}' \
  | python -m json.tool
```

Resposta:

```json
{
  "original": "Dr. Silva ganhou R$ 1.250,00 em 1º lugar",
  "processado": "Doutor Silva ganhou mil duzentos e cinquenta reais em primeiro lugar"
}
```

Mais exemplos:

```bash
# Porcentagem
curl -s -X POST http://localhost:8080/preprocessar \
  -H "Content-Type: application/json" \
  -d '{"texto": "Taxa de juros: 12,5%"}' | python -m json.tool

# Abreviações
curl -s -X POST http://localhost:8080/preprocessar \
  -H "Content-Type: application/json" \
  -d '{"texto": "Profa. Ana na Av. Paulista, nº 100"}' | python -m json.tool
```

---

## POST /tts

Sintetiza texto e retorna o áudio como binário.

### Parâmetros

```json
{
  "texto":        "Olá, mundo!",
  "engine":       "edge",
  "voz":          "francisca",
  "idioma":       "pt",
  "velocidade":   1.0,
  "preprocessar": false,
  "formato":      "wav",
  "sample_rate":  null
}
```

| Campo | Tipo | Padrão | Valores aceitos |
|---|---|---|---|
| `texto` | string | — | qualquer texto não vazio |
| `engine` | string | `"edge"` | `"edge"`, `"pocket"` |
| `voz` | string | `"francisca"` | nome de voz válido para o engine |
| `idioma` | string | `"pt"` | `"pt"`, `"en"`, `"fr"`, `"de"`, `"it"`, `"es"` |
| `velocidade` | float | `1.0` | `0.1` a `4.0` |
| `preprocessar` | bool | `false` | `true`, `false` |
| `formato` | string | `"wav"` | `"wav"`, `"flac"`, `"ogg"`, `"mp3"` |
| `sample_rate` | int | `null` | ex: `16000`, `44100`, `48000` |

### Exemplos de uso

**WAV básico (edge):**

```bash
curl -s -X POST http://localhost:8080/tts \
  -H "Content-Type: application/json" \
  -d '{"texto": "Olá, mundo!"}' \
  --output output/saida.wav
```

**MP3 com voz masculina:**

```bash
curl -s -X POST http://localhost:8080/tts \
  -H "Content-Type: application/json" \
  -d '{"texto": "Bom dia, ouvintes!", "voz": "antonio", "formato": "mp3"}' \
  --output output/bom_dia.mp3
```

**Pocket TTS em inglês:**

```bash
curl -s -X POST http://localhost:8080/tts \
  -H "Content-Type: application/json" \
  -d '{
    "texto": "Hello, this is a test of the pocket TTS engine.",
    "engine": "pocket",
    "idioma": "en",
    "voz": "george"
  }' \
  --output output/hello.wav
```

**Com velocidade e pré-processamento:**

```bash
curl -s -X POST http://localhost:8080/tts \
  -H "Content-Type: application/json" \
  -d '{
    "texto": "Dr. Silva ganhou R$ 5.000,00 no 1º lugar.",
    "preprocessar": true,
    "velocidade": 0.9,
    "formato": "flac",
    "sample_rate": 44100
  }' \
  --output output/resultado.flac
```

**FLAC com alta qualidade:**

```bash
curl -s -X POST http://localhost:8080/tts \
  -H "Content-Type: application/json" \
  -d '{
    "texto": "Áudio de alta qualidade para edição profissional.",
    "voz": "francisca",
    "formato": "flac",
    "sample_rate": 48000
  }' \
  --output output/hq.flac
```

**Pocket em francês:**

```bash
curl -s -X POST http://localhost:8080/tts \
  -H "Content-Type: application/json" \
  -d '{
    "texto": "Bonjour! Comment allez-vous?",
    "engine": "pocket",
    "idioma": "fr",
    "voz": "cosette"
  }' \
  --output output/bonjour.wav
```

### Resposta de erro (422)

Parâmetros inválidos retornam HTTP 422:

```bash
# Engine inválido
curl -s -X POST http://localhost:8080/tts \
  -H "Content-Type: application/json" \
  -d '{"texto": "Teste", "engine": "google"}' | python -m json.tool
# {"detail": "engine deve ser 'edge' ou 'pocket'"}

# Velocidade fora do intervalo
curl -s -X POST http://localhost:8080/tts \
  -H "Content-Type: application/json" \
  -d '{"texto": "Teste", "velocidade": 5.0}' | python -m json.tool
# {"detail": "velocidade deve estar entre 0.1 e 4.0"}

# Texto vazio
curl -s -X POST http://localhost:8080/tts \
  -H "Content-Type: application/json" \
  -d '{"texto": ""}' | python -m json.tool
# {"detail": "texto não pode ser vazio"}
```

---

## Integração com Python

```python
import requests

# Sintetizar e salvar
resp = requests.post("http://localhost:8080/tts", json={
    "texto": "Olá, mundo!",
    "engine": "edge",
    "formato": "wav",
})
resp.raise_for_status()
with open("output/saida.wav", "wb") as f:
    f.write(resp.content)

# Pré-processar
resp = requests.post("http://localhost:8080/preprocessar", json={
    "texto": "R$ 1.250,00 — 3º lugar"
})
print(resp.json()["processado"])
# mil duzentos e cinquenta reais — terceiro lugar
```

## Integração com JavaScript/Node.js

```javascript
const fs = require("fs");

const resp = await fetch("http://localhost:8080/tts", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    texto: "Olá do Node.js!",
    engine: "edge",
    formato: "mp3",
  }),
});

const buffer = await resp.arrayBuffer();
fs.writeFileSync("output/saida.mp3", Buffer.from(buffer));
```
