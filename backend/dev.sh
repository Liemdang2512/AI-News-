#!/usr/bin/env bash
# Chạy API local: không watch .venv (tránh reload vòng lặp khi pip cài package)
set -e
cd "$(dirname "$0")"
if [[ ! -d .venv ]]; then
  python3 -m venv .venv
  .venv/bin/pip install -r requirements.txt
fi
exec .venv/bin/uvicorn main:app --reload --host 127.0.0.1 --port 8000 \
  --reload-exclude '.venv' --reload-exclude '**/.venv/**'
