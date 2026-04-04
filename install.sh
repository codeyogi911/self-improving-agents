#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="${REFLECT_HOME:-$HOME/.reflect-cli}"
BIN_DIR="${HOME}/.local/bin"
REPO="codeyogi911/reflect"

# ── Resolve latest version ────────────���────────────────────────────
echo "Fetching latest version..."
VERSION=$(curl -fsSL -o /dev/null -w '%{redirect_url}' \
    "https://github.com/${REPO}/releases/latest" | grep -oE 'v[0-9]+\.[0-9]+\.[0-9]+')

if [ -z "$VERSION" ]; then
    echo "Error: could not resolve latest version." >&2
    echo "Check https://github.com/${REPO}/releases" >&2
    exit 1
fi

TARBALL_URL="https://github.com/${REPO}/releases/download/${VERSION}/reflect-cli-${VERSION}.tar.gz"

# ── Download and extract ────────────���──────────────────────────────
echo "Installing reflect ${VERSION}..."
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

curl -fsSL "$TARBALL_URL" -o "$TMP/reflect-cli.tar.gz"
tar -xzf "$TMP/reflect-cli.tar.gz" -C "$TMP"

# ── Install ──────────��─────────────────────────────────────────────
rm -rf "$INSTALL_DIR"
mv "$TMP/reflect-cli" "$INSTALL_DIR"
chmod +x "$INSTALL_DIR/reflect"

# ── Symlink CLI ───────��────────────────────────────────────────────
mkdir -p "$BIN_DIR"
ln -sf "$INSTALL_DIR/reflect" "$BIN_DIR/reflect"

# ── Check PATH ��─────────────────────────���──────────────────────────
if ! echo "$PATH" | tr ':' '\n' | grep -qx "$BIN_DIR"; then
    echo ""
    echo "Add to your shell profile:"
    echo "  export PATH=\"$BIN_DIR:\$PATH\""
    echo ""
fi

echo "Done — reflect ${VERSION}. Run 'reflect init' in any git repo."
