#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

PYTHON_BIN="${PYTHON_BIN:-}"

if [[ -z "$PYTHON_BIN" ]]; then
  for candidate in \
    "/Library/Frameworks/Python.framework/Versions/3.11/bin/python3" \
    "python3.12" \
    "python3.11" \
    "python3"
  do
    if command -v "$candidate" >/dev/null 2>&1; then
      if "$candidate" - <<'PY'
import sys
raise SystemExit(0 if sys.version_info >= (3, 11) else 1)
PY
      then
        PYTHON_BIN="$candidate"
        break
      fi
    fi
  done
fi

if [[ -z "$PYTHON_BIN" ]]; then
  echo "No Python 3.11+ interpreter found." >&2
  echo "Your shell is probably using pyenv Python 3.7.12. Install/select Python 3.11+, or run:" >&2
  echo "  PYTHON_BIN=/Library/Frameworks/Python.framework/Versions/3.11/bin/python3 scripts/run_sqlite_dev.sh" >&2
  exit 1
fi

echo "Using Python: $("$PYTHON_BIN" -c 'import sys; print(sys.executable, sys.version.split()[0])')"

if [[ ! -x ".venv/bin/python" ]]; then
  "$PYTHON_BIN" -m venv .venv
fi

VENV_PY=".venv/bin/python"

if ! "$VENV_PY" - <<'PY'
import sys
raise SystemExit(0 if sys.version_info >= (3, 11) else 1)
PY
then
  echo "Existing .venv is not Python 3.11+. Recreating it." >&2
  rm -rf .venv
  "$PYTHON_BIN" -m venv .venv
fi

echo "Using venv: $("${VENV_PY}" -c 'import sys; print(sys.executable, sys.version.split()[0])')"

"$VENV_PY" -m pip install --upgrade pip setuptools wheel
"$VENV_PY" -m pip install -e ".[test]"
cp .env.sqlite.example .env
"$VENV_PY" -m alembic upgrade head
API_HOST="${API_HOST:-0.0.0.0}"
API_PORT="${API_PORT:-8000}"
echo "Starting API on http://${API_HOST}:${API_PORT}"
exec "$VENV_PY" -m uvicorn app.main:app --reload --host "$API_HOST" --port "$API_PORT"
