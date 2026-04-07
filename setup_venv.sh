#!/usr/bin/env bash
# setup_venv.sh — Configura ambiente virtual para wfh.py
# Autor: André Henrique (@mrhenrike)
# Compatível com Linux e macOS

set -e

VENV_DIR=".venv"
PYTHON_MIN="3.8"

echo "=== wfh.py — Setup de ambiente virtual ==="

# Verificar Python
if ! command -v python3 &>/dev/null; then
    echo "ERRO: python3 não encontrado. Instale Python >= ${PYTHON_MIN}."
    exit 1
fi

PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Python detectado: $PY_VER"

# Criar venv
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
    echo "venv criado em $VENV_DIR"
else
    echo "venv já existe em $VENV_DIR"
fi

# Ativar e instalar
source "$VENV_DIR/bin/activate"
pip install --upgrade pip --quiet
pip install -r requirements.txt

echo ""
echo "=== Ambiente configurado! ==="
echo "Para ativar: source .venv/bin/activate"
echo "Para rodar:  python wfh.py --help"
