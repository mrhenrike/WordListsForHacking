# setup_venv.ps1 — Configura ambiente virtual para wfh.py (Windows)
# Autor: André Henrique (@mrhenrike)
# Compatível com PowerShell 5.1+ e Python 3.8+

$ErrorActionPreference = "Stop"

$VENV_DIR = ".venv"

Write-Host "=== wfh.py — Setup de ambiente virtual ===" -ForegroundColor Cyan

# Verificar Python
try {
    $pyVer = python --version 2>&1
    Write-Host "Python detectado: $pyVer"
} catch {
    Write-Host "ERRO: Python nao encontrado. Instale Python >= 3.8." -ForegroundColor Red
    exit 1
}

# Criar venv
if (-not (Test-Path $VENV_DIR)) {
    python -m venv $VENV_DIR
    Write-Host "venv criado em $VENV_DIR"
} else {
    Write-Host "venv ja existe em $VENV_DIR"
}

# Ativar e instalar
& "$VENV_DIR\Scripts\Activate.ps1"
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt

Write-Host ""
Write-Host "=== Ambiente configurado! ===" -ForegroundColor Green
Write-Host "Para ativar: .venv\Scripts\Activate.ps1"
Write-Host "Para rodar:  python wfh.py --help"
