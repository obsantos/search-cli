#!/usr/bin/env bash
set -e

# ==============================================================================
# search-cli Local Setup & Global Linker Script
# ==============================================================================

echo "🚀 Installing search-cli..."

# 1. Determine Python command
PYTHON_CMD=""
if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD="python"
else
    echo "❌ Error: Python 3.9+ is required but python3 was not found."
    exit 1
fi

# Check Python version (>= 3.9)
PY_VER=$($PYTHON_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PY_MAJOR=$($PYTHON_CMD -c 'import sys; print(sys.version_info.major)')
PY_MINOR=$($PYTHON_CMD -c 'import sys; print(sys.version_info.minor)')

if [ "$PY_MAJOR" -lt 3 ] || ([ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 9 ]); then
    echo "❌ Error: Python 3.9+ is required. Found Python $PY_VER."
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 2. Create Virtual Environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment (.venv)..."
    $PYTHON_CMD -m venv .venv
fi

# 3. Install in editable mode
echo "⚡ Installing dependencies and search-cli..."
.venv/bin/pip install --upgrade pip --quiet
.venv/bin/pip install -e . --quiet

# 4. Symlink binary to ~/.local/bin
TARGET_BIN_DIR="$HOME/.local/bin"
mkdir -p "$TARGET_BIN_DIR"
ln -sf "$SCRIPT_DIR/.venv/bin/search-cli" "$TARGET_BIN_DIR/search-cli"

echo "🔗 Symlinked $TARGET_BIN_DIR/search-cli -> $SCRIPT_DIR/.venv/bin/search-cli"

# 5. Check if ~/.local/bin is in PATH, and add to shell RC if missing
if [[ ":$PATH:" != *":$TARGET_BIN_DIR:"* ]]; then
    # Detect user shell config file
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
    fi

    if [ -n "$SHELL_RC" ]; then
        # Check if already present in the RC file
        if ! grep -q '\.local/bin' "$SHELL_RC" 2>/dev/null; then
            echo "" >> "$SHELL_RC"
            echo '# Added by search-cli' >> "$SHELL_RC"
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$SHELL_RC"
            echo "✨ Added $TARGET_BIN_DIR to PATH in $SHELL_RC"
            echo "👉 Run 'source $SHELL_RC' or restart your terminal to activate."
        fi
    else
        echo ""
        echo "⚠️  Note: $TARGET_BIN_DIR is not in your current PATH."
        echo "   Add it to your shell configuration:"
        echo "   export PATH=\"\$HOME/.local/bin:\$PATH\""
    fi
fi

echo ""
echo "✅ Installation complete!"
"$TARGET_BIN_DIR/search-cli" --version 2>/dev/null || .venv/bin/search-cli --version
echo ""
echo "👉 Run 'search-cli --help' or 'search-cli auth login' to get started."
