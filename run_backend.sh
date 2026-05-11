#!/usr/bin/env bash
# run_backend.sh – start the AI PII Redactor FastAPI server
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND="$SCRIPT_DIR/backend"

echo ""
echo "  ██████╗ ██╗██╗     ██████╗ ██╗   ██╗ █████╗ ██████╗ ██████╗"
echo "  ██╔══██╗██║██║    ██╔════╝ ██║   ██║██╔══██╗██╔══██╗██╔══██╗"
echo "  ██████╔╝██║██║    ██║  ███╗██║   ██║███████║██████╔╝██║  ██║"
echo "  ██╔═══╝ ██║██║    ██║   ██║██║   ██║██╔══██║██╔══██╗██║  ██║"
echo "  ██║     ██║██║    ╚██████╔╝╚██████╔╝██║  ██║██║  ██║██████╔╝"
echo "  ╚═╝     ╚═╝╚═╝     ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝"
echo "                     AI PII Redactor v1.0"
echo ""

# Validate Python
if ! command -v python3 &>/dev/null && ! command -v python &>/dev/null; then
  echo "❌  Python not found. Install Python 3.10+ and retry."
  exit 1
fi
PY=$(command -v python3 || command -v python)

# Warn if Tesseract missing
if ! command -v tesseract &>/dev/null; then
  echo "⚠   Tesseract not in PATH — image/PDF redaction will fail."
  echo "    → https://github.com/UB-Mannheim/tesseract/wiki"
  echo ""
fi

# Activate virtualenv if present
for VENV in .venv venv; do
  [ -f "$SCRIPT_DIR/$VENV/bin/activate" ] && source "$SCRIPT_DIR/$VENV/bin/activate" && break
  [ -f "$SCRIPT_DIR/$VENV/Scripts/activate" ] && source "$SCRIPT_DIR/$VENV/Scripts/activate" && break
done

cd "$BACKEND"

echo "🚀  Starting server on http://127.0.0.1:8000 ..."
echo "    Open the URL in your browser to use the UI."
echo "    Press Ctrl+C to stop."
echo ""

uvicorn main:app --reload --host 127.0.0.1 --port 8000
