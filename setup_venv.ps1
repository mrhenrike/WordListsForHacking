# setup_venv.ps1 — Setup virtual environment for wfh.py (Windows)
# Author: André Henrique (@mrhenrike)
# Compatible with Windows 10/11 PowerShell 5.1+

$ErrorActionPreference = "Stop"
$VenvDir = ".venv"
$PythonMin = "3.8"

Write-Host "=== wfh.py — Virtual Environment Setup (Windows) ===" -ForegroundColor Cyan
Write-Host ""

# Check Python
$pythonCmd = $null
foreach ($cmd in @("python", "python3", "py")) {
    try {
        $ver = & $cmd --version 2>&1
        if ($ver -match "Python (\d+\.\d+)") {
            $pythonCmd = $cmd
            Write-Host "Python found: $ver ($cmd)" -ForegroundColor Green
            break
        }
    } catch {}
}

if (-not $pythonCmd) {
    Write-Host "ERROR: Python not found." -ForegroundColor Red
    Write-Host ""
    Write-Host "Install Python from: https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "Or via winget:  winget install Python.Python.3.12" -ForegroundColor Yellow
    Write-Host "Or via scoop:   scoop install python" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Make sure to check 'Add Python to PATH' during installation." -ForegroundColor Yellow
    exit 1
}

# Create venv
if (-not (Test-Path $VenvDir)) {
    Write-Host "Creating virtual environment at $VenvDir..."
    & $pythonCmd -m venv $VenvDir
    Write-Host "venv created." -ForegroundColor Green
} else {
    Write-Host "venv already exists at $VenvDir" -ForegroundColor Yellow
}

# Activate
$activateScript = Join-Path $VenvDir "Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    & $activateScript
} else {
    Write-Host "ERROR: Could not find activation script at $activateScript" -ForegroundColor Red
    exit 1
}

# Upgrade pip
Write-Host ""
Write-Host "--- Upgrading pip ---" -ForegroundColor Cyan
& pip install --upgrade pip --quiet

# Install dependencies
Write-Host ""
Write-Host "--- Installing core dependencies ---" -ForegroundColor Cyan
& pip install -r requirements.txt

Write-Host ""
Write-Host "=== Environment ready! ===" -ForegroundColor Green
Write-Host ""
Write-Host "Activate: .\.venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "Run:      python wfh.py --help" -ForegroundColor White
Write-Host "Or:       wfh --help  (if installed via pip)" -ForegroundColor White
Write-Host ""
Write-Host "Optional extras:" -ForegroundColor Cyan
Write-Host "  pip install wfh-wordlist[docs]   # PDF/XLSX/DOCX parsing"
Write-Host "  pip install wfh-wordlist[ocr]    # OCR/image text extraction"
Write-Host "  pip install wfh-wordlist[full]   # All optional dependencies"
Write-Host ""
Write-Host "Windows prerequisites for OCR (optional):" -ForegroundColor Cyan
Write-Host "  winget install UB-Mannheim.TesseractOCR" -ForegroundColor White
