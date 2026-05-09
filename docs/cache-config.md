# Cache, Clipboard e Configuração

## Cache de áudio

Áudios sintetizados são salvos em `.cache/tts_ptbr/` e reutilizados automaticamente quando o mesmo texto, engine e voz forem solicitados novamente.

### Comportamento padrão

```bash
# Primeira chamada — sintetiza e armazena em cache
.venv/bin/python tts_ptbr.py "Olá, mundo!"

# Segunda chamada — retorna instantaneamente do cache
.venv/bin/python tts_ptbr.py "Olá, mundo!"
# [cache] Áudio encontrado no cache.
```

### Forçar nova síntese (`--sem-cache`)

```bash
# Ignora o cache — sintetiza novamente e atualiza o cache
.venv/bin/python tts_ptbr.py --sem-cache "Olá, mundo!"

# Útil quando a voz do engine foi atualizada
.venv/bin/python tts_ptbr.py --sem-cache --engine edge --voz antonio "Boa tarde!"
```

### Limpar o cache (`--limpar-cache`)

```bash
# Remove todos os áudios em cache e exibe quantos foram removidos
.venv/bin/python tts_ptbr.py --limpar-cache
# [cache] 12 entrada(s) removida(s).
```

### Configurar tamanho máximo

O padrão é 50 entradas (LRU — as mais antigas são removidas quando o limite é atingido). Para alterar, edite o `config.yaml`:

```yaml
cache_max: 100
```

Ou salve via CLI:

```bash
.venv/bin/python tts_ptbr.py --engine edge --salvar-config
# depois edite config.yaml manualmente para adicionar cache_max
```

---

## Clipboard (`--clipboard`)

Lê o texto copiado (Ctrl+C) e usa como entrada. Combinável com qualquer outra flag.

### Uso básico

```bash
# Copie qualquer texto, depois execute:
.venv/bin/python tts_ptbr.py --clipboard
```

### Combinando com outras flags

```bash
# Clipboard com voz masculina
.venv/bin/python tts_ptbr.py --clipboard --voz antonio

# Clipboard em inglês com pocket
.venv/bin/python tts_ptbr.py --clipboard --engine pocket --idioma en --voz george

# Clipboard com pré-processamento e salvar
.venv/bin/python tts_ptbr.py --clipboard --preprocessar --salvar saida.wav

# Clipboard mais rápido
.venv/bin/python tts_ptbr.py --clipboard --velocidade 1.4

# Clipboard sem reproduzir (só salva)
.venv/bin/python tts_ptbr.py --clipboard --salvar clipboard.wav --sem-reproduzir
```

Se o clipboard estiver vazio, o script encerra com código de erro 1.

---

## Configuração padrão (`config.yaml`)

Persiste flags para não precisar repeti-las a cada uso.

### Salvar configuração atual (`--salvar-config`)

```bash
# Definir pocket + inglês + george como padrões
.venv/bin/python tts_ptbr.py \
  --engine pocket \
  --idioma en \
  --voz george \
  --velocidade 1.1 \
  --salvar-config
# Configuração salva em config.yaml.

# A partir de agora, basta:
.venv/bin/python tts_ptbr.py "Hello world"
# usa pocket, inglês, george, velocidade 1.1 automaticamente
```

### Exemplos de config.yaml

Configuração para uso PT-BR com edge:

```yaml
engine: edge
voz: antonio
velocidade: 1.0
preprocessar: false
```

Configuração para narração profissional:

```yaml
engine: edge
voz: francisca
velocidade: 0.9
formato: flac
sample_rate: 44100
preprocessar: true
cache_max: 100
```

Configuração para inglês com pocket:

```yaml
engine: pocket
idioma: en
voz: george
velocidade: 1.2
streaming: false
cache_max: 50
```

### Resetar para padrões

```bash
# Deletar o arquivo reseta tudo para os padrões do script
rm config.yaml
```

### Campos disponíveis

| Campo | Tipo | Padrão | Descrição |
|---|---|---|---|
| `engine` | string | `edge` | Engine padrão |
| `voz` | string | `francisca` | Voz padrão |
| `idioma` | string | `pt` | Idioma padrão (pocket) |
| `velocidade` | float | `1.0` | Velocidade de fala |
| `streaming` | bool | `false` | Streaming padrão (pocket) |
| `preprocessar` | bool | `false` | Pré-processamento padrão |
| `formato` | string | — | Formato padrão de saída |
| `sample_rate` | int | — | Sample rate padrão |
| `cache_max` | int | `50` | Máximo de entradas no cache |
