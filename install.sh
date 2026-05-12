#!/usr/bin/env bash
# install.sh — instalador completo do llm-tts
# Uso: bash install.sh [--reinstalar]
set -euo pipefail

# ── Cores ─────────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[1;36m'; BOLD='\033[1m'; DIM='\033[2m'; RESET='\033[0m'

info()  { echo -e "  ${CYAN}·${RESET} $*"; }
ok()    { echo -e "  ${GREEN}✓${RESET} $*"; }
warn()  { echo -e "  ${YELLOW}!${RESET} $*"; }
die()   { echo -e "\n  ${RED}[erro]${RESET} $*\n" >&2; exit 1; }
sep()   { echo -e "\n  ${DIM}──────────────────────────────────────────${RESET}"; }

# ── Configurações ──────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_MIN_MAJOR=3
PYTHON_MIN_MINOR=12
VENV_DIR="$SCRIPT_DIR/.venv"
ALIAS_CMD="lts"
BIN_DIR="$HOME/.local/bin"
WRAPPER="$BIN_DIR/$ALIAS_CMD"
REINSTALAR=false

# ── Args ──────────────────────────────────────────────────────────────────────
for arg in "$@"; do
    case "$arg" in
        --reinstalar|-r) REINSTALAR=true ;;
        --help|-h)
            echo "Uso: bash install.sh [--reinstalar]"
            echo "  --reinstalar  Recria o ambiente virtual do zero"
            exit 0 ;;
        *) die "Argumento desconhecido: $arg. Use --help." ;;
    esac
done

# ── Cabeçalho ─────────────────────────────────────────────────────────────────
echo
echo -e "  ${BOLD}llm-tts${RESET}  ${DIM}·${RESET}  Instalador"
echo -e "  ${DIM}TTS Português BR — edge-tts + Pocket TTS${RESET}"
sep

# ── 1. Python 3.12+ ───────────────────────────────────────────────────────────
echo
info "Verificando Python ${PYTHON_MIN_MAJOR}.${PYTHON_MIN_MINOR}+..."

PYTHON=""
for cmd in "python${PYTHON_MIN_MAJOR}.${PYTHON_MIN_MINOR}" python3 python; do
    if command -v "$cmd" &>/dev/null; then
        _ver=$("$cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || true)
        _maj=$(echo "$_ver" | cut -d. -f1)
        _min=$(echo "$_ver" | cut -d. -f2)
        if [ "${_maj:-0}" -ge "$PYTHON_MIN_MAJOR" ] && [ "${_min:-0}" -ge "$PYTHON_MIN_MINOR" ]; then
            PYTHON="$cmd"
            ok "Python $_ver encontrado em $(command -v "$cmd")"
            break
        fi
    fi
done

[ -n "$PYTHON" ] || die \
    "Python ${PYTHON_MIN_MAJOR}.${PYTHON_MIN_MINOR}+ não encontrado.\n" \
    "  Instale com:\n" \
    "    sudo add-apt-repository ppa:deadsnakes/ppa\n" \
    "    sudo apt install python3.12 python3.12-venv"

# ── 2. Ambiente virtual ───────────────────────────────────────────────────────
sep; echo

if [ -d "$VENV_DIR" ] && [ "$REINSTALAR" = false ]; then
    ok "Ambiente virtual já existe em .venv  ${DIM}(use --reinstalar para recriar)${RESET}"
else
    if [ -d "$VENV_DIR" ]; then
        info "Removendo ambiente anterior..."
        rm -rf "$VENV_DIR"
    fi

    if command -v uv &>/dev/null; then
        _uv_ver=$(uv --version 2>/dev/null | awk '{print $2}')
        info "Criando .venv com uv $_uv_ver (Python ${PYTHON_MIN_MAJOR}.${PYTHON_MIN_MINOR})..."
        uv venv --python "${PYTHON_MIN_MAJOR}.${PYTHON_MIN_MINOR}" "$VENV_DIR" --seed -q
    else
        info "Criando .venv com python -m venv..."
        "$PYTHON" -m venv "$VENV_DIR"
        "$VENV_DIR/bin/pip" install --upgrade pip --quiet
    fi
    ok "Ambiente criado: $VENV_DIR"
fi

# ── 3. Bibliotecas de sistema (áudio) ────────────────────────────────────────
# sounddevice no Linux não embute PortAudio — precisa de libportaudio2 instalada.
sep; echo
info "Verificando bibliotecas de sistema para áudio..."

_libs_audio="libportaudio2 libasound2t64"
_libs_faltando=""

if command -v dpkg &>/dev/null; then
    for _lib in $_libs_audio; do
        dpkg -l "$_lib" 2>/dev/null | grep -q '^ii' || _libs_faltando="$_libs_faltando $_lib"
    done
    _libs_faltando="${_libs_faltando# }"

    if [ -z "$_libs_faltando" ]; then
        ok "Bibliotecas de áudio presentes (libportaudio2, libasound2t64)."
    elif [ "$(id -u)" -eq 0 ]; then
        info "Instalando bibliotecas de áudio como root: $_libs_faltando"
        apt-get install -y $_libs_faltando -qq 2>/dev/null \
            && ok "Bibliotecas instaladas: $_libs_faltando" \
            || warn "Falha ao instalar $_libs_faltando — instale manualmente: sudo apt install $_libs_faltando"
    elif command -v sudo &>/dev/null; then
        warn "libportaudio2 ausente — sounddevice precisa dela para reproduzir áudio."
        echo -e "  ${DIM}Instale com: sudo apt install $_libs_faltando${RESET}"
        echo -e "  ${DIM}Pressione Enter para continuar sem ela, ou Ctrl+C para cancelar e instalar antes.${RESET}"
        read -r _
        info "Tentando instalar com sudo..."
        sudo apt-get install -y $_libs_faltando -qq 2>/dev/null \
            && ok "Bibliotecas instaladas." \
            || warn "Não foi possível instalar. Execute manualmente: sudo apt install $_libs_faltando"
    else
        warn "libportaudio2 ausente — sounddevice não conseguirá reproduzir áudio."
        warn "Execute após instalar: sudo apt install $_libs_faltando"
    fi
else
    # não é Debian/Ubuntu — avisa mas não bloqueia
    _ok_libs=false
    command -v ldconfig &>/dev/null && ldconfig -p 2>/dev/null | grep -q libportaudio && _ok_libs=true
    $_ok_libs && ok "libportaudio detectada via ldconfig." \
              || warn "Não foi possível verificar libportaudio2 (apt não disponível)."
fi

# ── 4. Dependências Python ────────────────────────────────────────────────────
sep; echo
info "Instalando dependências de requirements.txt..."

if command -v uv &>/dev/null; then
    uv pip install --python "$VENV_DIR/bin/python" -r "$SCRIPT_DIR/requirements.txt" -q
else
    "$VENV_DIR/bin/pip" install -r "$SCRIPT_DIR/requirements.txt" --quiet
fi

ok "Dependências instaladas."

# ── 5. Diretório de saída ─────────────────────────────────────────────────────
mkdir -p "$SCRIPT_DIR/output"
ok "Diretório output/ pronto."

# ── 6. Wrapper executável ─────────────────────────────────────────────────────
sep; echo
mkdir -p "$BIN_DIR"

cat > "$WRAPPER" <<WRAPPER
#!/usr/bin/env bash
exec "$VENV_DIR/bin/python" "$SCRIPT_DIR/tts_ptbr.py" "\$@"
WRAPPER

chmod +x "$WRAPPER"
ok "Comando '${BOLD}$ALIAS_CMD${RESET}' criado em $WRAPPER"

# ── 7. PATH no shell RC ───────────────────────────────────────────────────────
_path_line='export PATH="$HOME/.local/bin:$PATH"'
_shell_rc=""

case "${SHELL:-}" in
    */zsh)  _shell_rc="$HOME/.zshrc"  ;;
    */bash) _shell_rc="$HOME/.bashrc" ;;
    *)
        # fallback: tenta detectar qual RC existe
        [ -f "$HOME/.zshrc" ]  && _shell_rc="$HOME/.zshrc"  || true
        [ -f "$HOME/.bashrc" ] && _shell_rc="$HOME/.bashrc" || true
        ;;
esac

if [ -n "$_shell_rc" ]; then
    if grep -qE '(\.local/bin|local/bin)' "$_shell_rc" 2>/dev/null; then
        ok "~/.local/bin já está no PATH em $_shell_rc"
    else
        {
            echo ""
            echo "# llm-tts — adicionado por install.sh"
            echo "$_path_line"
        } >> "$_shell_rc"
        ok "PATH atualizado em $_shell_rc"
    fi
else
    warn "Shell RC não detectado. Adicione manualmente ao seu ~/.bashrc ou ~/.zshrc:"
    echo -e "       ${DIM}$_path_line${RESET}"
fi

# ── 8. Verificação rápida ─────────────────────────────────────────────────────
sep; echo
info "Verificando instalação..."

_python_ok=$("$VENV_DIR/bin/python" -c "
import importlib.util, sys
pkgs = ['numpy','scipy','sounddevice','soundfile','edge_tts','num2words','yaml','tqdm','fastapi']
missing = [p for p in pkgs if importlib.util.find_spec(p) is None]
print('missing:' + ','.join(missing) if missing else 'ok')
")

if [ "$_python_ok" = "ok" ]; then
    ok "Todos os pacotes verificados."
else
    _missing="${_python_ok#missing:}"
    warn "Pacotes não encontrados: $_missing"
    warn "Tente executar: uv pip install --python $VENV_DIR/bin/python $_missing"
fi

# ── 9. HuggingFace Token (engine pocket) ──────────────────────────────────────
sep; echo

_hf_configurado=false
_hf_token_val=""

# verifica .env existente
if [ -f "$SCRIPT_DIR/.env" ]; then
    _hf_token_val=$(grep -E '^HF_TOKEN=' "$SCRIPT_DIR/.env" 2>/dev/null | cut -d= -f2- | tr -d '"'"'" | tr -d ' ')
fi

if [ -n "${HF_TOKEN:-}" ] && echo "${HF_TOKEN}" | grep -qv '^hf_xxx'; then
    ok "HF_TOKEN detectado na variável de ambiente."
    _hf_configurado=true
elif [ -n "$_hf_token_val" ] && echo "$_hf_token_val" | grep -qv '^hf_xxx'; then
    ok "HF_TOKEN configurado em .env."
    _hf_configurado=true
else
    # .env não existe ou tem placeholder — criar a partir do .env.example
    if [ ! -f "$SCRIPT_DIR/.env" ] && [ -f "$SCRIPT_DIR/.env.example" ]; then
        cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
        info ".env criado a partir de .env.example."
    fi
    echo -e "  ${YELLOW}┌─ Engine pocket requer HuggingFace Token ─────────────────────────┐${RESET}"
    echo -e "  ${YELLOW}│${RESET}  O engine 'pocket' (TTS local/neural) usa um modelo gated no HF. ${YELLOW}│${RESET}"
    echo -e "  ${YELLOW}│${RESET}  O engine 'edge' (padrão) funciona agora sem nenhuma configuração.${YELLOW}│${RESET}"
    echo -e "  ${YELLOW}│${RESET}                                                                   ${YELLOW}│${RESET}"
    echo -e "  ${YELLOW}│${RESET}  Para ativar o engine pocket:                                     ${YELLOW}│${RESET}"
    echo -e "  ${YELLOW}│${RESET}  ${DIM}1. Obtenha seu token: https://huggingface.co/settings/tokens${RESET}   ${YELLOW}│${RESET}"
    echo -e "  ${YELLOW}│${RESET}  ${DIM}2. Aceite os termos:  https://huggingface.co/kyutai/pocket-tts${RESET} ${YELLOW}│${RESET}"
    echo -e "  ${YELLOW}│${RESET}  ${DIM}3. Edite o arquivo:   $SCRIPT_DIR/.env${RESET}"
    echo -e "  ${YELLOW}│${RESET}  ${DIM}   Substitua: HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx${RESET}    ${YELLOW}│${RESET}"
    echo -e "  ${YELLOW}└───────────────────────────────────────────────────────────────────┘${RESET}"
    echo
fi

# ── 10. Resumo ────────────────────────────────────────────────────────────────
sep
echo
echo -e "  ${GREEN}${BOLD}Instalação concluída!${RESET}"
echo
echo -e "  Recarregue o terminal ou execute:"
if [ -n "$_shell_rc" ]; then
    echo -e "    ${CYAN}source $_shell_rc${RESET}"
fi
echo
echo -e "  ${BOLD}Como usar:${RESET}"
echo -e "    ${BOLD}$ALIAS_CMD${RESET} \"Olá, mundo!\""
echo -e "    ${BOLD}$ALIAS_CMD${RESET} --engine pocket \"Texto local\""
echo -e "    ${BOLD}$ALIAS_CMD${RESET} --help"
echo
echo -e "  ${BOLD}Servidor REST:${RESET}"
echo -e "    ${CYAN}$VENV_DIR/bin/uvicorn server.server:app --port 8080${RESET}"
echo
echo -e "  ${DIM}Projeto em: $SCRIPT_DIR${RESET}"
echo
