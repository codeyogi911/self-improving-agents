#!/usr/bin/env bash
# reflect installer — curl -fsSL https://raw.githubusercontent.com/codeyogi911/reflect/main/install.sh | bash
set -euo pipefail

REPO="codeyogi911/reflect"
INSTALL_DIR="${HOME}/.local/bin"

# ── Helpers ─────────────────────────────────────────────────────────
info()  { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
warn()  { printf '\033[1;33mWarning:\033[0m %s\n' "$*"; }
err()   { printf '\033[1;31mError:\033[0m %s\n' "$*" >&2; exit 1; }

command_exists() { command -v "$1" >/dev/null 2>&1; }

# ── Detect install method ──────────────────────────────────────────
install_via_pipx() {
    info "Installing via pipx..."
    pipx install reflect-cli
}

install_via_pip() {
    info "Installing via pip..."
    pip install --user reflect-cli
}

install_via_source() {
    info "Installing from source..."
    local clone_dir="${HOME}/.local/share/reflect"

    if [ -d "$clone_dir" ]; then
        info "Updating existing clone..."
        git -C "$clone_dir" pull --ff-only origin main
    else
        git clone "https://github.com/${REPO}.git" "$clone_dir"
    fi

    mkdir -p "$INSTALL_DIR"
    cd "$clone_dir"
    pip install --user -e . 2>/dev/null || {
        # Fallback: symlink for systems without pip
        ln -sf "$clone_dir/reflect" "$INSTALL_DIR/reflect"
        info "Installed via symlink (pip unavailable)"
    }
}

# ── Main ───────────────────────────────────────────────────────────
main() {
    info "Installing reflect..."

    if command_exists pipx; then
        install_via_pipx
    elif command_exists pip; then
        install_via_pip
    elif command_exists git; then
        install_via_source
    else
        err "No package manager found. Install pipx, pip, or git and try again."
    fi

    # Verify installation
    if command_exists reflect; then
        info "reflect installed successfully!"
        reflect --help | head -3
    else
        warn "reflect was installed but is not on your PATH."
        echo ""
        echo "Add this to your shell profile:"
        echo '  export PATH="$HOME/.local/bin:$PATH"'
        echo ""
        echo "Then restart your shell and run: reflect --help"
    fi
}

main "$@"
