#!/usr/bin/env bash
# tools/check-system.sh — validação pré-instalação do llm-tts
#
# Verifica se o sistema operacional possui todos os requisitos para que
# install.sh execute sem erros e o projeto funcione corretamente.
#
# Uso:
#   bash tools/check-system.sh            # relatório completo
#   bash tools/check-system.sh --silencioso  # só exibe falhas/avisos
#   bash tools/check-system.sh --json     # saída em JSON (para automação)
#
# Código de saída:
#   0 — sistema apto (pode haver avisos)
#   1 — uma ou mais falhas críticas encontradas
set -uo pipefail

# ── Cores ─────────────────────────────────────────────────────────────────────
_R='\033[0;31m'; _G='\033[0;32m'; _Y='\033[1;33m'; _C='\033[1;36m'
_B='\033[1m';    _D='\033[2m';    _W='\033[1;37m'; _X='\033[0m'

_c() { echo -e "$1"; }   # raw color
ok()   { _c "  ${_G}✓${_X}  $*"; }
fail() { _c "  ${_R}✗${_X}  $*"; }
warn() { _c "  ${_Y}!${_X}  $*"; }
info() { _c "  ${_D}·${_X}  $*"; }
sep()  { _c "\n  ${_C}$(printf '─%.0s' {1..50})${_X}"; }
hdr()  { _c "\n  ${_C}${_B}$*${_X}"; sep; echo; }

# ── Estado global ──────────────────────────────────────────────────────────────
ERROS=0
AVISOS=0
INFOS=0
declare -a _ERROS_LIST=()
declare -a _AVISOS_LIST=()
SILENCIOSO=false
FORMATO_JSON=false

for _arg in "$@"; do
    case "$_arg" in
        --silencioso|-s) SILENCIOSO=true ;;
        --json|-j)       FORMATO_JSON=true; SILENCIOSO=true ;;
        --help|-h)
            echo "Uso: bash tools/check-system.sh [--silencioso] [--json]"
            exit 0 ;;
    esac
done

# Funções de registro
_ok() {
    local msg="$1"
    (( INFOS++ )) || true
    $SILENCIOSO || ok "$msg"
}
_fail() {
    local msg="$1"
    (( ERROS++ )) || true
    _ERROS_LIST+=("$msg")
    fail "${_B}$msg${_X}"
}
_warn() {
    local msg="$1"
    (( AVISOS++ )) || true
    _AVISOS_LIST+=("$msg")
    warn "$msg"
}
_info() {
    $SILENCIOSO || info "$1"
    (( INFOS++ )) || true
}

# Helpers
_cmd()   { command -v "$1" &>/dev/null; }
_pkg_installed() {
    dpkg -l "$1" 2>/dev/null | grep -q '^ii' \
    || rpm -q "$1" &>/dev/null \
    || pacman -Q "$1" &>/dev/null 2>/dev/null
}
_ver_gte() {
    # _ver_gte "3.12" "3.10" → true (3.12 >= 3.10)
    printf '%s\n%s\n' "$2" "$1" | sort -V -C
}
_mb_livres() {
    # retorna MB livres em um caminho
    local path="$1"
    local target="$path"
    while [ ! -d "$target" ] && [ "$target" != "/" ]; do
        target="$(dirname "$target")"
    done
    df -BM "$target" 2>/dev/null | awk 'NR==2 {gsub("M",""); print $4}' || echo 0
}

# ── Cabeçalho ──────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

$SILENCIOSO || {
    echo
    _c "  ${_B}llm-tts${_X}  ${_D}·${_X}  Validação do sistema"
    _c "  ${_D}Verifica se o ambiente está apto para instalação${_X}"
}

# ══════════════════════════════════════════════════════════════════════════════
# 1. SISTEMA OPERACIONAL
# ══════════════════════════════════════════════════════════════════════════════
$SILENCIOSO || hdr "1 · Sistema Operacional"

OS="$(uname -s)"
ARCH="$(uname -m)"

# Plataforma suportada
case "$OS" in
    Linux)
        _ok "Plataforma: Linux ($ARCH)"
        ;;
    Darwin)
        _warn "Plataforma: macOS ($ARCH) — suportado, mas não é o ambiente primário do projeto"
        ;;
    MINGW*|CYGWIN*|MSYS*)
        _fail "Plataforma: Windows não é suportado — use WSL2 (Ubuntu 22.04+)"
        ;;
    *)
        _warn "Plataforma desconhecida: $OS — prossiga com cautela"
        ;;
esac

# Arquitetura
case "$ARCH" in
    x86_64|amd64)   _ok  "Arquitetura: $ARCH (suporte completo a wheels)" ;;
    aarch64|arm64)  _ok  "Arquitetura: $ARCH (wheels disponíveis para principais pacotes)" ;;
    armv7l)         _warn "Arquitetura: $ARCH — alguns pacotes podem precisar compilar do fonte" ;;
    *)              _warn "Arquitetura: $ARCH — compatibilidade de wheels não garantida" ;;
esac

# Distro Linux
if [ "$OS" = "Linux" ]; then
    DISTRO_ID=""
    DISTRO_VER=""
    if [ -f /etc/os-release ]; then
        DISTRO_ID=$(. /etc/os-release && echo "${ID_LIKE:-$ID}" | awk '{print $1}')
        DISTRO_NAME=$(. /etc/os-release && echo "${PRETTY_NAME:-$NAME}")
        DISTRO_VER=$(. /etc/os-release && echo "${VERSION_ID:-}")
        _ok "Distribuição: $DISTRO_NAME"
    else
        _warn "Não foi possível detectar a distribuição Linux (/etc/os-release ausente)"
    fi

    # Kernel
    KERNEL="$(uname -r)"
    KERNEL_MAJOR=$(echo "$KERNEL" | cut -d. -f1)
    if [ "${KERNEL_MAJOR:-0}" -ge 4 ]; then
        _ok "Kernel: $KERNEL"
    else
        _warn "Kernel $KERNEL pode ser muito antigo — recomendado >= 4.x"
    fi
fi

# Executando como root?
if [ "$(id -u)" -eq 0 ]; then
    _warn "Executando como root — não recomendado; o alias 'lts' será criado para root"
else
    _ok "Usuário: $(whoami) (não-root)"
fi

# ══════════════════════════════════════════════════════════════════════════════
# 2. PYTHON
# ══════════════════════════════════════════════════════════════════════════════
$SILENCIOSO || hdr "2 · Python"

PY_MIN_MAJOR=3
PY_MIN_MINOR=12
PYTHON_OK=false
PYTHON_CMD=""

for _py in python3.12 python3 python; do
    if _cmd "$_py"; then
        _ver=$("$_py" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')" 2>/dev/null) || continue
        _maj=$(echo "$_ver" | cut -d. -f1)
        _min=$(echo "$_ver" | cut -d. -f2)
        if [ "${_maj:-0}" -ge "$PY_MIN_MAJOR" ] && [ "${_min:-0}" -ge "$PY_MIN_MINOR" ]; then
            PYTHON_OK=true
            PYTHON_CMD="$_py"
            _ok "Python $_ver encontrado: $(command -v "$_py")"
            break
        else
            _info "Python $_ver em $(command -v "$_py") — versão insuficiente (mínimo ${PY_MIN_MAJOR}.${PY_MIN_MINOR})"
        fi
    fi
done

if ! $PYTHON_OK; then
    _fail "Python ${PY_MIN_MAJOR}.${PY_MIN_MINOR}+ não encontrado"
    case "${DISTRO_ID:-}" in
        debian|ubuntu)
            _c "     ${_D}→ sudo add-apt-repository ppa:deadsnakes/ppa${_X}"
            _c "     ${_D}→ sudo apt install python3.12 python3.12-venv${_X}"
            ;;
        fedora|rhel|centos)
            _c "     ${_D}→ sudo dnf install python3.12${_X}"
            ;;
        arch)
            _c "     ${_D}→ sudo pacman -S python${_X}"
            ;;
    esac
fi

# Módulo venv
if $PYTHON_OK; then
    if "$PYTHON_CMD" -m venv --help &>/dev/null; then
        _ok "Módulo venv disponível"
    else
        _fail "Módulo venv ausente para $PYTHON_CMD"
        _c "     ${_D}→ sudo apt install python3.12-venv${_X}"
    fi

    # ensurepip
    if "$PYTHON_CMD" -m ensurepip --version &>/dev/null; then
        _ok "ensurepip disponível"
    else
        _warn "ensurepip indisponível — pip pode não ser instalado no novo venv"
        _c "     ${_D}→ sudo apt install python3.12-distutils${_X}"
    fi

    # Teste real: criar venv temporário
    _tmp_venv="$(mktemp -d)/check_venv"
    if "$PYTHON_CMD" -m venv "$_tmp_venv" --without-pip &>/dev/null 2>&1; then
        _ok "Criação de venv funcional (teste real passou)"
        rm -rf "$(dirname "$_tmp_venv")"
    else
        _fail "Falha ao criar venv de teste — verifique permissões e módulos"
        rm -rf "$(dirname "$_tmp_venv")" 2>/dev/null || true
    fi
fi

# ══════════════════════════════════════════════════════════════════════════════
# 3. FERRAMENTAS
# ══════════════════════════════════════════════════════════════════════════════
$SILENCIOSO || hdr "3 · Ferramentas"

# uv
if _cmd uv; then
    _uv_ver=$(uv --version 2>/dev/null | awk '{print $2}')
    _ok "uv $_uv_ver encontrado — instalação rápida garantida"
else
    _warn "uv não encontrado — install.sh usará pip (mais lento, ~5× mais tempo)"
    _c "     ${_D}→ curl -LsSf https://astral.sh/uv/install.sh | sh${_X}"
fi

# bash >= 4
if _cmd bash; then
    _bash_ver=$(bash --version | head -1 | grep -oP '\d+\.\d+')
    _bash_maj=$(echo "$_bash_ver" | cut -d. -f1)
    if [ "${_bash_maj:-0}" -ge 4 ]; then
        _ok "Bash $_bash_ver"
    else
        _fail "Bash $_bash_ver — install.sh requer Bash >= 4.0"
    fi
else
    _fail "bash não encontrado"
fi

# git
if _cmd git; then
    _git_ver=$(git --version | awk '{print $3}')
    _ok "git $_git_ver"
else
    _warn "git não encontrado — necessário para clonar o repositório"
    _c "     ${_D}→ sudo apt install git${_X}"
fi

# curl
if _cmd curl; then
    _curl_ver=$(curl --version | head -1 | awk '{print $2}')
    _ok "curl $_curl_ver"
elif _cmd wget; then
    _ok "wget disponível (alternativa ao curl)"
else
    _warn "curl e wget ausentes — podem ser necessários para downloads auxiliares"
fi

# gcc / g++ (para compilar extensões se não houver wheel)
if _cmd gcc; then
    _gcc_ver=$(gcc --version | head -1 | grep -oP '\d+\.\d+\.\d+' | head -1)
    _ok "gcc $_gcc_ver (compilação de extensões C disponível)"
else
    _warn "gcc não encontrado — se não houver wheel pré-compilado, numpy/scipy falharão"
    _c "     ${_D}→ sudo apt install gcc g++${_X}"
fi

# python3-dev / python3.12-dev
_py_dev_ok=false
for _pkg in python3.12-dev python3-dev; do
    if _pkg_installed "$_pkg"; then
        _ok "Headers Python: $_pkg instalado"
        _py_dev_ok=true
        break
    fi
done
$_py_dev_ok || _warn "python3.12-dev não encontrado — necessário para compilar extensões C"

# make
_cmd make && _ok "make disponível" || _warn "make não encontrado — pode ser necessário para compilar pacotes"

# ══════════════════════════════════════════════════════════════════════════════
# 4. BIBLIOTECAS DO SISTEMA — ÁUDIO
# ══════════════════════════════════════════════════════════════════════════════
$SILENCIOSO || hdr "4 · Bibliotecas de Áudio"

# libportaudio2 (sounddevice)
if _pkg_installed libportaudio2; then
    _ok "libportaudio2 instalada (sounddevice)"
else
    # Wheel do sounddevice geralmente embute portaudio, mas checar é seguro
    _warn "libportaudio2 não encontrada — pode causar erro se sounddevice compilar do fonte"
    _c "     ${_D}→ sudo apt install libportaudio2${_X}"
fi

# libsndfile1 (soundfile)
if _pkg_installed libsndfile1; then
    _ok "libsndfile1 instalada (soundfile)"
else
    _warn "libsndfile1 não encontrada — pode causar erro se soundfile compilar do fonte"
    _c "     ${_D}→ sudo apt install libsndfile1${_X}"
fi

# ALSA — libasound2 (Ubuntu 23.10+: libasound2t64)
_alsa_ok=false
for _alsa_pkg in libasound2 libasound2t64 libasound2-data; do
    if _pkg_installed "$_alsa_pkg"; then
        _ok "ALSA: $_alsa_pkg instalada"
        _alsa_ok=true
        break
    fi
done
$_alsa_ok || _warn "libasound2 / libasound2t64 não encontrada — sounddevice pode falhar em runtime"

# Daemon de áudio em execução
_audio_daemon=""
if _cmd pactl && pactl info &>/dev/null 2>&1; then
    _audio_daemon="PulseAudio/PipeWire"
    _ok "Daemon de áudio ativo: PulseAudio/PipeWire"
elif _cmd pw-cli && pw-cli --version &>/dev/null 2>&1; then
    _audio_daemon="PipeWire"
    _ok "Daemon de áudio ativo: PipeWire"
elif _cmd pulseaudio && pulseaudio --check &>/dev/null 2>&1; then
    _audio_daemon="PulseAudio"
    _ok "Daemon de áudio ativo: PulseAudio"
else
    _warn "Nenhum daemon de áudio detectado (PulseAudio / PipeWire) — áudio não será reproduzido"
    _c "     ${_D}→ sudo apt install pulseaudio  ou  pipewire pipewire-pulse${_X}"
fi

# Dispositivo de saída de áudio
if _cmd aplay; then
    _num_dev=$(aplay -l 2>/dev/null | grep -c '^card' || echo 0)
    if [ "${_num_dev:-0}" -gt 0 ]; then
        _ok "Dispositivos de áudio detectados: $_num_dev saída(s)"
    else
        _warn "Nenhum dispositivo de áudio de saída encontrado"
    fi
else
    _warn "aplay (alsa-utils) não encontrado — não foi possível verificar dispositivos de áudio"
    _c "     ${_D}→ sudo apt install alsa-utils${_X}"
fi

# ══════════════════════════════════════════════════════════════════════════════
# 5. CLIPBOARD
# ══════════════════════════════════════════════════════════════════════════════
$SILENCIOSO || hdr "5 · Clipboard (flag --clipboard)"

_clip_ok=false
_clip_found=""

# Detectar se é Wayland ou X11
_session="${XDG_SESSION_TYPE:-}"
[ -z "$_session" ] && _cmd loginctl && \
    _session=$(loginctl show-session "$(loginctl | awk 'NR==2{print $1}')" -p Type --value 2>/dev/null || true)

for _tool in xclip xsel wl-clipboard; do
    if _cmd "$_tool" || _cmd "wl-copy" 2>/dev/null; then
        _clip_ok=true
        _clip_found="$_tool"
        break
    fi
done

if $_clip_ok; then
    _ok "Ferramenta de clipboard: $_clip_found"
else
    _warn "Nenhuma ferramenta de clipboard encontrada — flag --clipboard não funcionará"
    if [ "${_session:-}" = "wayland" ]; then
        _c "     ${_D}→ sudo apt install wl-clipboard${_X}"
    else
        _c "     ${_D}→ sudo apt install xclip${_X}"
    fi
fi

# ══════════════════════════════════════════════════════════════════════════════
# 6. ESPAÇO EM DISCO E MEMÓRIA
# ══════════════════════════════════════════════════════════════════════════════
$SILENCIOSO || hdr "6 · Espaço em Disco e Memória"

# Disco — diretório do projeto (venv + dependências ~700 MB)
_mb_proj=$(_mb_livres "$SCRIPT_DIR")
if [ "${_mb_proj:-0}" -ge 1500 ]; then
    _ok "Disco no projeto: ${_mb_proj} MB livres (mínimo: 1500 MB)"
elif [ "${_mb_proj:-0}" -ge 800 ]; then
    _warn "Disco no projeto: ${_mb_proj} MB livres — suficiente para o básico, mas justo para pocket-tts"
else
    _fail "Disco insuficiente no projeto: ${_mb_proj} MB livres (mínimo: 800 MB)"
fi

# Disco — ~/.cache (modelo pocket-tts ~500 MB)
_mb_cache=$(_mb_livres "$HOME/.cache")
if [ "${_mb_cache:-0}" -ge 700 ]; then
    _ok "Disco em ~/.cache: ${_mb_cache} MB livres (modelo pocket-tts ~500 MB)"
elif [ "${_mb_cache:-0}" -ge 500 ]; then
    _warn "Disco em ~/.cache: ${_mb_cache} MB livres — pode ser insuficiente para o modelo pocket-tts"
else
    _warn "Disco em ~/.cache: ${_mb_cache} MB livres — modelo pocket-tts não poderá ser baixado"
    _c "     ${_D}→ libere espaço ou redefina HF_HOME para outro volume${_X}"
fi

# Disco — /tmp (cache pip durante instalação ~200 MB)
_mb_tmp=$(_mb_livres /tmp)
if [ "${_mb_tmp:-0}" -ge 300 ]; then
    _ok "Disco em /tmp: ${_mb_tmp} MB livres (cache de instalação)"
else
    _warn "Disco em /tmp: ${_mb_tmp} MB livres — pip pode falhar por falta de espaço temporário"
fi

# RAM total
if _cmd free; then
    _ram_total_mb=$(free -m | awk 'NR==2{print $2}')
    _ram_livre_mb=$(free -m | awk 'NR==2{print $7}')
    if [ "${_ram_total_mb:-0}" -ge 4096 ]; then
        _ok "RAM total: ${_ram_total_mb} MB (adequado para pocket-tts)"
    elif [ "${_ram_total_mb:-0}" -ge 2048 ]; then
        _warn "RAM total: ${_ram_total_mb} MB — pocket-tts pode ser lento com menos de 4 GB"
    else
        _warn "RAM total: ${_ram_total_mb} MB — insuficiente para pocket-tts (mínimo recomendado: 4 GB)"
    fi
    if [ "${_ram_livre_mb:-0}" -ge 1024 ]; then
        _ok "RAM disponível: ${_ram_livre_mb} MB (suficiente para instalação)"
    else
        _warn "RAM disponível: ${_ram_livre_mb} MB — feche outros programas antes de instalar"
    fi
fi

# ══════════════════════════════════════════════════════════════════════════════
# 7. REDE
# ══════════════════════════════════════════════════════════════════════════════
$SILENCIOSO || hdr "7 · Conectividade de Rede"

_HAS_HTTP_CLIENT=false
_cmd curl && _HAS_HTTP_CLIENT=true
_cmd wget && _HAS_HTTP_CLIENT=true

if ! $_HAS_HTTP_CLIENT; then
    _fail "curl e wget ausentes — rede não pôde ser verificada e downloads auxiliares falharão"
    _c "     ${_D}→ sudo apt install curl${_X}"
fi

_check_url() {
    local url="$1" label="$2" critical="${3:-false}"
    local code
    if ! $_HAS_HTTP_CLIENT; then
        # já reportado acima como falha; silencia checagens individuais
        return
    fi
    if _cmd curl; then
        code=$(curl -s --max-time 8 -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
    else
        wget -q --timeout=8 --spider "$url" 2>/dev/null && code=200 || code=000
    fi
    if [ "${code:-000}" -ge 200 ] && [ "${code:-000}" -lt 400 ]; then
        _ok "Acessível: $label"
    else
        $critical && _fail "Inacessível: $label (HTTP $code) — pacotes não podem ser baixados" \
                  || _warn "Inacessível: $label — funcionalidade dependente pode não funcionar"
    fi
}

_check_url "https://pypi.org"                 "PyPI (pip install)"              true
_check_url "https://huggingface.co"           "HuggingFace (modelos pocket-tts)" false
_check_url "https://speech.platform.bing.com" "Microsoft TTS (engine edge)"      false
_check_url "https://astral.sh"                "astral.sh (instalador do uv)"     false

# ══════════════════════════════════════════════════════════════════════════════
# 8. PERMISSÕES
# ══════════════════════════════════════════════════════════════════════════════
$SILENCIOSO || hdr "8 · Permissões de Escrita"

# Diretório do projeto
if [ -w "$SCRIPT_DIR" ]; then
    _ok "Escrita no projeto: $SCRIPT_DIR"
else
    _fail "Sem permissão de escrita em $SCRIPT_DIR"
    _c "     ${_D}→ sudo chown -R $(whoami) \"$SCRIPT_DIR\"${_X}"
fi

# ~/.local/bin
_local_bin="$HOME/.local/bin"
if [ -d "$_local_bin" ] && [ -w "$_local_bin" ]; then
    _ok "Escrita em ~/.local/bin (já existe)"
elif [ ! -d "$_local_bin" ] && [ -w "$(dirname "$_local_bin")" ]; then
    _ok "~/.local/bin será criado pelo instalador (permissão ok)"
elif [ ! -d "$_local_bin" ] && [ -w "$HOME/.local" ]; then
    _ok "~/.local/bin será criado pelo instalador (permissão ok)"
elif [ ! -d "$HOME/.local" ] && [ -w "$HOME" ]; then
    _ok "~/.local/bin será criado pelo instalador (permissão ok)"
else
    _fail "Sem permissão para criar/escrever em ~/.local/bin — comando 'lts' não será instalado"
fi

# Shell RC
_rc_ok=false
for _rc in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.bash_profile"; do
    if [ -f "$_rc" ] && [ -w "$_rc" ]; then
        _ok "Shell RC gravável: $_rc"
        _rc_ok=true
        break
    elif [ ! -f "$_rc" ] && [ -w "$HOME" ]; then
        _ok "Shell RC será criado: $_rc (permissão ok)"
        _rc_ok=true
        break
    fi
done
$_rc_ok || _warn "Nenhum shell RC gravável encontrado (~/.bashrc, ~/.zshrc)"

# ══════════════════════════════════════════════════════════════════════════════
# 9. SHELL
# ══════════════════════════════════════════════════════════════════════════════
$SILENCIOSO || hdr "9 · Configuração do Shell"

# Shell padrão
_default_shell="${SHELL:-}"
if [ -n "$_default_shell" ]; then
    _ok "Shell padrão: $_default_shell"
else
    _warn "Variável \$SHELL não definida"
fi

# ~/.local/bin no PATH atual
if echo "$PATH" | grep -q "$HOME/.local/bin\|\.local/bin"; then
    _ok "~/.local/bin já está no \$PATH"
else
    _warn "~/.local/bin não está no \$PATH atual — será adicionado pelo install.sh ao shell RC"
    _c "     ${_D}→ após instalar, execute: source ~/.bashrc${_X}"
fi

# PYTHONPATH interferindo?
if [ -n "${PYTHONPATH:-}" ]; then
    _warn "PYTHONPATH definido: $PYTHONPATH — pode interferir com o venv isolado"
    _c "     ${_D}→ considere 'unset PYTHONPATH' antes de instalar${_X}"
else
    _ok "PYTHONPATH não definido (sem interferência no venv)"
fi

# Já dentro de um venv?
if [ -n "${VIRTUAL_ENV:-}" ]; then
    _warn "Já dentro de um venv: $VIRTUAL_ENV — desative com 'deactivate' antes de instalar"
else
    _ok "Nenhum venv ativo (\$VIRTUAL_ENV não definido)"
fi

# PIP_REQUIRE_VIRTUALENV
if [ "${PIP_REQUIRE_VIRTUALENV:-}" = "true" ]; then
    _warn "PIP_REQUIRE_VIRTUALENV=true — pode bloquear pip fora de venv; install.sh já usa venv"
else
    _ok "PIP_REQUIRE_VIRTUALENV não conflitante"
fi

# ══════════════════════════════════════════════════════════════════════════════
# 10. CONFLITOS
# ══════════════════════════════════════════════════════════════════════════════
$SILENCIOSO || hdr "10 · Conflitos Potenciais"

# Comando 'lts' já existe?
if _cmd lts; then
    _existing_lts=$(command -v lts)
    if echo "$_existing_lts" | grep -q ".local/bin/lts"; then
        _ok "Comando 'lts' já existe em ~/.local/bin — será sobrescrito pelo instalador"
    else
        _warn "Comando 'lts' encontrado em $_existing_lts — será sobrescrito (outro programa pode ser afetado)"
    fi
else
    _ok "Sem conflito: comando 'lts' não existe no PATH"
fi

# .venv existente no projeto
if [ -d "$SCRIPT_DIR/.venv" ]; then
    _venv_py="$SCRIPT_DIR/.venv/bin/python"
    if [ -x "$_venv_py" ]; then
        _venv_ver=$("$_venv_py" --version 2>/dev/null | awk '{print $2}')
        _venv_maj=$(echo "$_venv_ver" | cut -d. -f1)
        _venv_min=$(echo "$_venv_ver" | cut -d. -f2)
        if [ "${_venv_maj:-0}" -ge 3 ] && [ "${_venv_min:-0}" -ge 12 ]; then
            _ok ".venv existente com Python $_venv_ver — será reutilizado (use --reinstalar para recriar)"
        else
            _warn ".venv existente com Python $_venv_ver — versão abaixo de 3.12; use: bash install.sh --reinstalar"
        fi
    else
        _warn ".venv existente mas sem Python executável — pode estar corrompido; use --reinstalar"
    fi
else
    _ok "Sem .venv existente — será criado pelo instalador"
fi

# requirements.txt presente e legível
if [ -r "$SCRIPT_DIR/requirements.txt" ]; then
    _n_deps=$(grep -c '.' "$SCRIPT_DIR/requirements.txt" 2>/dev/null || echo 0)
    _ok "requirements.txt presente ($_n_deps dependências)"
else
    _fail "requirements.txt não encontrado em $SCRIPT_DIR"
fi

# tts_ptbr.py presente
if [ -r "$SCRIPT_DIR/tts_ptbr.py" ]; then
    _ok "tts_ptbr.py presente"
else
    _fail "tts_ptbr.py não encontrado em $SCRIPT_DIR — repositório incompleto?"
fi

# install.sh presente e executável
if [ -x "$SCRIPT_DIR/install.sh" ]; then
    _ok "install.sh presente e executável"
elif [ -r "$SCRIPT_DIR/install.sh" ]; then
    _warn "install.sh presente mas sem permissão de execução"
    _c "     ${_D}→ chmod +x install.sh${_X}"
else
    _warn "install.sh não encontrado — instale manualmente conforme docs/instalacao.md"
fi

# ══════════════════════════════════════════════════════════════════════════════
# RESUMO FINAL
# ══════════════════════════════════════════════════════════════════════════════
$SILENCIOSO || sep

echo
if [ "$FORMATO_JSON" = "true" ]; then
    # ── Saída JSON ─────────────────────────────────────────────────────────────
    printf '{\n'
    printf '  "apto": %s,\n' "$([ $ERROS -eq 0 ] && echo true || echo false)"
    printf '  "erros": %d,\n' "$ERROS"
    printf '  "avisos": %d,\n' "$AVISOS"
    printf '  "erros_lista": ['
    first=true
    for e in "${_ERROS_LIST[@]+"${_ERROS_LIST[@]}"}"; do
        $first && first=false || printf ','
        printf '"%s"' "$(echo "$e" | sed 's/"/\\"/g')"
    done
    printf '],\n  "avisos_lista": ['
    first=true
    for a in "${_AVISOS_LIST[@]+"${_AVISOS_LIST[@]}"}"; do
        $first && first=false || printf ','
        printf '"%s"' "$(echo "$a" | sed 's/"/\\"/g')"
    done
    printf ']\n}\n'
else
    # ── Resumo legível ─────────────────────────────────────────────────────────
    _c "\n  ${_B}Resumo${_X}"
    echo
    _c "  ${_G}✓ Verificações OK${_X}   : $INFOS"
    _c "  ${_Y}! Avisos${_X}           : $AVISOS"
    _c "  ${_R}✗ Erros críticos${_X}   : $ERROS"
    echo

    if [ "${#_ERROS_LIST[@]}" -gt 0 ]; then
        _c "  ${_R}${_B}Erros que impedem a instalação:${_X}"
        for e in "${_ERROS_LIST[@]}"; do
            _c "    ${_R}✗${_X} $e"
        done
        echo
    fi

    if [ "${#_AVISOS_LIST[@]}" -gt 0 ]; then
        _c "  ${_Y}${_B}Avisos (não bloqueiam a instalação):${_X}"
        for a in "${_AVISOS_LIST[@]}"; do
            _c "    ${_Y}!${_X} $a"
        done
        echo
    fi

    if [ $ERROS -eq 0 ]; then
        _c "  ${_G}${_B}✓ Sistema apto para instalação${_X}"
        _c "  ${_D}Execute: bash install.sh${_X}"
    else
        _c "  ${_R}${_B}✗ Corrija os erros acima antes de executar install.sh${_X}"
    fi
    echo
fi

exit $([ $ERROS -eq 0 ] && echo 0 || echo 1)
