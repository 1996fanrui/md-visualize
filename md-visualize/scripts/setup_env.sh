#!/usr/bin/env bash
# Install runtime dependencies for md-visualize skill.
# Usage: bash setup_env.sh
# Installs: mmdc, chrome-headless-shell, visual-components node_modules, playwright chromium.
# Does NOT install: node/npm/uv (please install via system package manager).
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

if ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
    echo "[ERROR] node/npm not found. Install Node.js first (brew install node | apt install nodejs)."
    exit 1
fi

if ! command -v mmdc >/dev/null 2>&1; then
    echo "[INSTALL] @mermaid-js/mermaid-cli (global)"
    npm install -g @mermaid-js/mermaid-cli
else
    echo "[SKIP] mmdc already installed"
fi

chrome_found=0
for root in "$HOME/.cache/puppeteer/chrome-headless-shell" "$HOME/Library/Caches/Puppeteer/chrome-headless-shell"; do
    if [[ -d "$root" ]] && compgen -G "$root/*/chrome-headless-shell-*/chrome-headless-shell" >/dev/null; then
        chrome_found=1
        break
    fi
done
if [[ "$chrome_found" -eq 0 ]]; then
    echo "[INSTALL] chrome-headless-shell (via puppeteer)"
    npx --yes puppeteer browsers install chrome-headless-shell
else
    echo "[SKIP] chrome-headless-shell already installed"
fi

if ! command -v uv >/dev/null 2>&1; then
    echo "[WARN] uv not installed. Install via: curl -LsSf https://astral.sh/uv/install.sh | sh"
fi

if [[ ! -d "$SKILL_DIR/visual-components/node_modules" ]]; then
    echo "[INSTALL] visual-components node_modules"
    (cd "$SKILL_DIR/visual-components" && npm install)
else
    echo "[SKIP] visual-components/node_modules already installed"
fi

if ! uv run python -c "from playwright.sync_api import sync_playwright" >/dev/null 2>&1; then
    echo "[INSTALL] playwright chromium"
    uv run playwright install chromium
else
    echo "[SKIP] playwright chromium already installed"
fi

echo
echo "[DONE] Re-run scripts/check_env.sh to verify."
