#!/usr/bin/env bash
# === AI-Shifu Course Creator — Bootstrap Script ===
# Run after unpacking:  bash setup.sh
set -euo pipefail
SKILL_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "==> Bootstrapping ai-shifu-course-creator skill"
echo "    Skill directory: $SKILL_DIR"

# ─── Python dependencies ─────────────────────────────────
echo "[1/4] Installing Python dependencies..."
if [ -f "$SKILL_DIR/requirements.txt" ]; then
  pip3 install -r "$SKILL_DIR/requirements.txt" --quiet
  echo "    OK: requests installed"
else
  echo "    SKIP: no requirements.txt"
fi

# ─── Environment file ────────────────────────────────────
echo "[2/4] Setting up environment..."
if [ -f "$SKILL_DIR/.env" ]; then
  echo "    SKIP: .env already exists"
elif [ -f "$SKILL_DIR/.env.template" ]; then
  cp "$SKILL_DIR/.env.template" "$SKILL_DIR/.env"
  echo "    OK: .env created from template (edit SHIFU_TOKEN + SHIFU_BASE_URL)"
else
  echo "    WARN: no .env template found — create .env manually"
fi

# ─── CLI executable ──────────────────────────────────────
echo "[3/4] Making scripts executable..."
chmod +x "$SKILL_DIR/scripts/shifu-cli.py"
chmod +x "$SKILL_DIR/scripts/mdf-proxy.py"
echo "    OK"

# ─── Quick connectivity check ────────────────────────────
echo "[4/4] Checking connectivity..."
SHIFU_BASE_URL="$(grep -E '^SHIFU_BASE_URL=' "$SKILL_DIR/.env" 2>/dev/null | cut -d= -f2- | tr -d '\"' || echo 'http://localhost:8080')"
if curl -s -o /dev/null -w '%{http_code}' "$SHIFU_BASE_URL/api/config" 2>/dev/null | grep -qE '2[0-9]{2}'; then
  echo "    OK: API reachable at $SHIFU_BASE_URL"
else
  echo "    WARN: Could not reach API at $SHIFU_BASE_URL (may need SHIFU_BASE_URL override)"
fi

echo ""
echo "  Setup complete. Next steps:"
echo "    1. Edit $SKILL_DIR/.env → set SHIFU_TOKEN + SHIFU_BASE_URL"
echo "    2. Test: python3 $SKILL_DIR/scripts/shifu-cli.py list"
echo "    3. (Optional) Start MDF proxy: python3 $SKILL_DIR/scripts/mdf-proxy.py"
