# llm-tts — Índice da documentação

Guia de leitura recomendado: do básico ao avançado.

---

## 1. Começando

### [1.1 Instalação](instalacao.md)
Configure o ambiente antes de qualquer coisa.

- Criar ambiente virtual com `uv`
- Instalar dependências (`requirements.txt`)
- Verificar a instalação com `--listar-vozes`
- Configurar token HuggingFace para vozes extras (pocket)
- Instalar dependências opcionais do servidor REST

---

## 2. Uso básico

### [2.1 Engines, vozes e idiomas](uso-basico.md)
Os três parâmetros principais que controlam como o áudio é gerado.

- Frase direta via argumento posicional
- `--engine edge` vs `--engine pocket` — diferenças e casos de uso
- `--voz` — vozes Edge (francisca, antonio, thalita) e pocket (26 vozes)
- `--listar-vozes` — exibir vozes disponíveis por engine
- `--idioma` — português, inglês, francês, alemão, italiano, espanhol

---

## 3. Saída de áudio

### [3.1 Formatos, batch e velocidade](saida-audio.md)
Tudo relacionado a como e onde o áudio é entregue.

- `--salvar` — salvar em arquivo; sem path vai para `output/` automaticamente
- `--formato` — wav, flac, ogg, mp3
- `--sample-rate` — taxa de amostragem de saída (16 kHz, 44.1 kHz, etc.)
- `--sem-reproduzir` — gerar sem tocar o áudio
- `--arquivo` — batch a partir de arquivo `.txt` (uma frase por linha)
- `--juntar` — concatenar todas as frases em um único arquivo
- Stdin via pipe (`echo` / `cat`)
- `--velocidade` — de 0.1× a 4.0× com exemplos práticos
- `--streaming` — reprodução em tempo real com latência reduzida (pocket)

---

## 4. Processamento de texto

### [4.1 Pré-processamento PT-BR](preprocessamento.md)
Como expandir abreviações, valores e números para leitura natural.

- `--preprocessar` / `-p` — ativar o pipeline de expansão
- Moeda: `R$ 1.250,50` → "mil duzentos e cinquenta reais e cinquenta centavos"
- Porcentagem: `12,5%` → "doze vírgula cinco por cento"
- Ordinais: `3º`, `2ª` → "terceiro", "segunda"
- Abreviações: `Dr.`, `Sra.`, `Av.`, `nº` → formas completas
- Siglas: `TTS`, `USB` → leitura letra por letra
- Números cardinais e decimais
- Frases mistas com múltiplos tipos combinados

---

## 5. Personalização de voz

### [5.1 Clonagem de voz](clonagem-voz.md)
Sintetizar com uma voz personalizada usando áudio de referência.

- Pré-requisitos: token HF e aceite dos termos do modelo
- Dicas para gravar um bom áudio de referência
- `--clonar-voz` — clonar e falar imediatamente
- `--exportar-voz` — exportar para `.safetensors` (reutilizável sem login)
- `--voz <arquivo.safetensors>` — usar voz exportada em qualquer máquina
- Clonagem em outros idiomas (inglês, francês, etc.)
- Organização de vozes exportadas na pasta `vozes/`

---

## 6. Produtividade

### [6.1 Cache, clipboard e configuração](cache-config.md)
Recursos para tornar o uso diário mais rápido e configurável.

- **Cache automático** — reutiliza áudios já sintetizados de `.cache/tts_ptbr/`
- `--sem-cache` — forçar nova síntese ignorando o cache
- `--limpar-cache` — remover todas as entradas do cache
- `--clipboard` — ler e falar o texto copiado (Ctrl+C)
- `--salvar-config` — persistir flags atuais em `config.yaml`
- `config.yaml` — todos os campos disponíveis com exemplos completos

---

## 7. Uso avançado

### [7.1 Modo interativo](modo-interativo.md)
Sessão contínua com controle total em tempo real — sem reiniciar o script.

- Iniciar o modo interativo (sem argumentos)
- Trocar engine, voz, idioma e velocidade durante a sessão
- Salvar e controlar o formato de saída em tempo real
- `fila on` — enfileirar frases sem bloquear a digitação
- Gerenciar o cache dentro da sessão
- Ler o clipboard diretamente do prompt
- Streaming e clonagem de voz no modo interativo
- Salvar a configuração da sessão em `config.yaml`
- Tabela de referência com todos os 28 comandos disponíveis

### [7.2 Servidor REST](servidor-rest.md)
API HTTP com FastAPI para integração com outras aplicações.

- Iniciar o servidor (desenvolvimento e produção)
- `GET /health` — verificar status
- `GET /vozes` — listar vozes por engine
- `GET /idiomas` — listar idiomas disponíveis
- `POST /preprocessar` — aplicar pré-processamento PT-BR
- `POST /tts` — sintetizar e receber áudio binário
- Todos os parâmetros do `/tts` com tipos e valores aceitos
- Exemplos com `curl`, Python (`requests`) e JavaScript (`fetch`)

---

## Referência rápida de flags

| Flag | Atalho | Documento |
|---|---|---|
| `--engine` | `-e` | [uso-basico.md](uso-basico.md) |
| `--voz` | `-v` | [uso-basico.md](uso-basico.md) |
| `--idioma` | | [uso-basico.md](uso-basico.md) |
| `--listar-vozes` | | [uso-basico.md](uso-basico.md) |
| `--salvar` | | [saida-audio.md](saida-audio.md) |
| `--formato` | | [saida-audio.md](saida-audio.md) |
| `--sample-rate` | | [saida-audio.md](saida-audio.md) |
| `--sem-reproduzir` | | [saida-audio.md](saida-audio.md) |
| `--arquivo` | | [saida-audio.md](saida-audio.md) |
| `--juntar` | | [saida-audio.md](saida-audio.md) |
| `--velocidade` | | [saida-audio.md](saida-audio.md) |
| `--streaming` | | [saida-audio.md](saida-audio.md) |
| `--preprocessar` | `-p` | [preprocessamento.md](preprocessamento.md) |
| `--clonar-voz` | | [clonagem-voz.md](clonagem-voz.md) |
| `--exportar-voz` | | [clonagem-voz.md](clonagem-voz.md) |
| `--sem-cache` | | [cache-config.md](cache-config.md) |
| `--limpar-cache` | | [cache-config.md](cache-config.md) |
| `--clipboard` | | [cache-config.md](cache-config.md) |
| `--salvar-config` | | [cache-config.md](cache-config.md) |
