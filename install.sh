#!/usr/bin/env bash
set -e

# ==============================================================================
# search-cli Idempotent Setup & Global Linker Script
# ==============================================================================

echo "🚀 Setting up search-cli..."

# 1. Determine Python command (require Python 3.9+)
PYTHON_CMD=""
if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD="python"
else
    echo "❌ Error: Python 3.9+ is required but python3 was not found."
    exit 1
fi

PY_VER=$($PYTHON_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PY_MAJOR=$($PYTHON_CMD -c 'import sys; print(sys.version_info.major)')
PY_MINOR=$($PYTHON_CMD -c 'import sys; print(sys.version_info.minor)')

if [ "$PY_MAJOR" -lt 3 ] || ([ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 9 ]); then
    echo "❌ Error: Python 3.9+ is required. Found Python $PY_VER."
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 2. Virtual Environment (re-use if existing)
if [ ! -d ".venv" ] || [ ! -f ".venv/bin/pip" ]; then
    echo "📦 Creating virtual environment (.venv)..."
    $PYTHON_CMD -m venv .venv
else
    echo "📦 Found existing virtual environment (.venv)."
fi

# 3. Install/Update search-cli in editable mode
echo "⚡ Verifying dependencies and package..."
.venv/bin/pip install -e . --quiet

# 4. Global symlink to ~/.local/bin
TARGET_BIN_DIR="$HOME/.local/bin"
mkdir -p "$TARGET_BIN_DIR"
SOURCE_BIN="$SCRIPT_DIR/.venv/bin/search-cli"
DEST_BIN="$TARGET_BIN_DIR/search-cli"

if [ -L "$DEST_BIN" ] && [ "$(readlink "$DEST_BIN")" = "$SOURCE_BIN" ]; then
    echo "🔗 Symlink already active: $DEST_BIN -> $SOURCE_BIN"
else
    ln -sf "$SOURCE_BIN" "$DEST_BIN"
    echo "🔗 Linked $DEST_BIN -> $SOURCE_BIN"
fi

# 5. Shell PATH Configuration (strictly idempotent)
if [[ ":$PATH:" != *":$TARGET_BIN_DIR:"* ]]; then
    # Detect appropriate shell configuration file
    SHELL_RC=""
    if [[ "$SHELL" == *"zsh"* ]]; then
        SHELL_RC="$HOME/.zshrc"
    elif [[ "$SHELL" == *"bash"* ]]; then
        if [[ "$OSTYPE" == "darwin"* && -f "$HOME/.bash_profile" ]]; then
            SHELL_RC="$HOME/.bash_profile"
        else
            SHELL_RC="$HOME/.bashrc"
        fi
    elif [ -f "$HOME/.zshrc" ]; then
        SHELL_RC="$HOME/.zshrc"
    elif [ -f "$HOME/.bashrc" ]; then
        SHELL_RC="$HOME/.bashrc"
    else
        SHELL_RC="$HOME/.profile"
    fi

    # Check if ~/.local/bin is already exported in the RC file
    if [ -f "$SHELL_RC" ] && grep -E '\.local/bin' "$SHELL_RC" >/dev/null 2>&1; then
        echo "ℹ️  $TARGET_BIN_DIR is already configured in $SHELL_RC (open a new shell or run 'source $SHELL_RC')."
    else
        touch "$SHELL_RC"
        # Ensure file ends with a newline before appending
        [ -s "$SHELL_RC" ] && [ -n "$(tail -c1 "$SHELL_RC")" ] && echo "" >> "$SHELL_RC"
        echo "" >> "$SHELL_RC"
        echo '# Added by search-cli' >> "$SHELL_RC"
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$SHELL_RC"
        echo "✨ Added $TARGET_BIN_DIR to PATH in $SHELL_RC"
        echo "👉 Run 'source $SHELL_RC' or restart your terminal to activate."
    fi
else
    echo "ℹ️  $TARGET_BIN_DIR is already in your active PATH."
fi

echo ""
echo "✅ Setup verified!"
"$DEST_BIN" --version 2>/dev/null || .venv/bin/search-cli --version

echo ""
echo "🤖 Connect to AI Assistants (Model Context Protocol):"
echo "   Codex:  codex mcp add search-console -- search-cli mcp"
echo "   Claude: claude mcp add search-console --scope user -- search-cli mcp"

echo ""
echo "👉 Run 'search-cli --help' or 'search-cli auth login' to get started."

