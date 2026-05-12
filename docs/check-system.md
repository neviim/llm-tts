# Validação do Sistema (check-system.sh)

Script de diagnóstico que verifica se o sistema operacional possui todos os
requisitos antes de executar `install.sh`. Detecta problemas antecipadamente
e fornece instruções de correção para cada falha encontrada.

## Uso

```bash
# Relatório completo (recomendado antes da instalação)
bash tools/check-system.sh

# Mostrar apenas avisos e erros
bash tools/check-system.sh --silencioso

# Saída em JSON (para automação e scripts)
bash tools/check-system.sh --json
```

**Código de saída:**
- `0` — sistema apto (pode haver avisos não-bloqueantes)
- `1` — uma ou mais falhas críticas encontradas

---

## O que é verificado

### 1 · Sistema Operacional
| Verificação | Crítico |
|---|:---:|
| Plataforma (Linux / macOS / Windows) | Sim |
| Arquitetura (x86_64, arm64, armv7l) | — |
| Distribuição Linux detectada | — |
| Versão do Kernel >= 4.x | — |
| Executando como não-root | — |

### 2 · Python
| Verificação | Crítico |
|---|:---:|
| Python 3.12+ disponível no PATH | Sim |
| Módulo `venv` funcional | Sim |
| `ensurepip` disponível | — |
| Criação de venv temporário de teste | Sim |

### 3 · Ferramentas
| Verificação | Crítico |
|---|:---:|
| Bash >= 4.0 (necessário para install.sh) | Sim |
| `uv` (recomendado — instalação ~5× mais rápida) | — |
| `git` (para clonar o repositório) | — |
| `curl` ou `wget` | — |
| `gcc` / `g++` (compilar extensões se não houver wheel) | — |
| `python3.12-dev` (headers para extensões C) | — |
| `make` | — |

### 4 · Bibliotecas de Áudio
| Verificação | Crítico |
|---|:---:|
| `libportaudio2` (sounddevice) | — |
| `libsndfile1` (soundfile) | — |
| `libasound2` / `libasound2t64` (ALSA) | — |
| Daemon de áudio ativo (PulseAudio / PipeWire) | — |
| Dispositivo de saída de áudio detectado | — |

### 5 · Clipboard
| Verificação | Crítico |
|---|:---:|
| `xclip`, `xsel` ou `wl-clipboard` presente | — |

Necessário apenas para a flag `--clipboard`.

### 6 · Espaço em Disco e Memória
| Verificação | Mínimo | Crítico |
|---|---|:---:|
| Disco no projeto (venv + deps) | 800 MB | Sim |
| Disco em `~/.cache` (modelo pocket-tts) | 500 MB | — |
| Disco em `/tmp` (cache do pip) | 200 MB | — |
| RAM total (pocket-tts) | 2 GB (rec. 4 GB) | — |
| RAM disponível (instalação) | 1 GB | — |

### 7 · Conectividade de Rede
| Verificação | Crítico |
|---|:---:|
| PyPI acessível (`pypi.org`) | Sim |
| HuggingFace acessível (`huggingface.co`) | — |
| Microsoft TTS acessível (engine `edge`) | — |
| astral.sh acessível (instalador do `uv`) | — |

### 8 · Permissões de Escrita
| Verificação | Crítico |
|---|:---:|
| Escrita no diretório do projeto | Sim |
| Criação / escrita em `~/.local/bin` | Sim |
| Shell RC gravável (`~/.bashrc` ou `~/.zshrc`) | — |

### 9 · Configuração do Shell
| Verificação | Crítico |
|---|:---:|
| Shell padrão detectado | — |
| `~/.local/bin` no `$PATH` | — |
| `PYTHONPATH` não interferindo | — |
| Não executando dentro de um venv ativo | — |
| `PIP_REQUIRE_VIRTUALENV` não conflitante | — |

### 10 · HuggingFace Token (engine pocket)
| Verificação | Crítico |
|---|:---:|
| `HF_TOKEN` em variável de ambiente ou `.env` | — |
| Token não é o valor placeholder (`hf_xxx...`) | — |

O engine `edge` (padrão) funciona sem token. O engine `pocket` requer
token válido para baixar o modelo gated `kyutai/pocket-tts`.

Se ausente, o script exibe os 3 passos: obter token → aceitar termos → editar `.env`.

### 11 · Conflitos Potenciais
| Verificação | Crítico |
|---|:---:|
| Comando `lts` já existe no PATH | — |
| `.venv` existente e compatível | — |
| `requirements.txt` presente | Sim |
| `tts_ptbr.py` presente | Sim |
| `install.sh` presente e executável | — |

---

## Interpretando o resultado

```
  ✓ Verificações OK   : 42    ← tudo certo
  ! Avisos            : 2     ← não impedem, mas merecem atenção
  ✗ Erros críticos    : 0     ← sem erros → pode instalar

  ✓ Sistema apto para instalação
  Execute: bash install.sh
```

- **✓ verde** — requisito atendido
- **! amarelo** — aviso: funcionalidade pode ser limitada, mas instalação prossegue
- **✗ vermelho** — falha crítica: corrija antes de executar `install.sh`

---

## Correções comuns (Ubuntu / Debian / Mint)

```bash
# Python 3.12 + venv
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install python3.12 python3.12-venv python3.12-dev

# Bibliotecas de áudio
sudo apt install libportaudio2 libsndfile1 alsa-utils

# ALSA (Ubuntu 24.04+ / Mint 22+)
sudo apt install libasound2t64

# Clipboard
sudo apt install xclip          # X11
sudo apt install wl-clipboard   # Wayland

# Build tools (se precisar compilar extensões)
sudo apt install gcc g++ make

# uv (recomendado)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## Usando em CI/CD

```bash
# Falha o pipeline se o ambiente não estiver apto
bash tools/check-system.sh --silencioso || exit 1
bash install.sh
```

```bash
# Capturar resultado em JSON para processar
resultado=$(bash tools/check-system.sh --json)
apto=$(echo "$resultado" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['apto'])")
[ "$apto" = "True" ] && bash install.sh
```
