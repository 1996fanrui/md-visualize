#!/usr/bin/env bash
# Check runtime dependencies for md-visualize skill.
# Usage: bash check_env.sh
# Exit 0 = ready, Exit 1 = missing dependencies (run setup_env.sh to fix).
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

missing=0

check() {
    local label="$1"
    local cmd="$2"
    local hint="$3"
    if eval "$cmd" >/dev/null 2>&1; then
        echo "[OK] $label"
    else
        echo "[MISSING] $label — $hint"
        missing=1
    fi
}

check "node"  "command -v node"  "install Node.js (brew install node | apt install nodejs)"
check "npm"   "command -v npm"   "ships with Node.js"
check "uv"    "command -v uv"    "curl -LsSf https://astral.sh/uv/install.sh | sh"
check "mmdc (mermaid-cli)" "command -v mmdc" "npm install -g @mermaid-js/mermaid-cli"

# chrome-headless-shell lives under puppeteer's cache.
chrome_found=0
for root in "$HOME/.cache/puppeteer/chrome-headless-shell" "$HOME/Library/Caches/Puppeteer/chrome-headless-shell"; do
    if [[ -d "$root" ]] && compgen -G "$root/*/chrome-headless-shell-*/chrome-headless-shell" >/dev/null; then
        chrome_found=1
        break
    fi
done
if [[ "$chrome_found" -eq 1 ]]; then
    echo "[OK] chrome-headless-shell"
else
    echo "[MISSING] chrome-headless-shell — npx puppeteer browsers install chrome-headless-shell"
    missing=1
fi

check "playwright chromium" \
    "uv run python -c 'from playwright.sync_api import sync_playwright'" \
    "uv run playwright install chromium"

if [[ -d "$SKILL_DIR/visual-components/node_modules" ]]; then
    echo "[OK] visual-components/node_modules"
else
    echo "[MISSING] visual-components/node_modules — run: (cd $SKILL_DIR/visual-components && npm install)"
    missing=1
fi

if [[ "$missing" -eq 0 ]]; then
    echo
    echo "[OK] All dependencies ready"
    exit 0
fi

echo
echo "Run scripts/setup_env.sh to install installable deps automatically."
exit 1
