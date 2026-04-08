#!/bin/bash
# publish-pypi.sh — WFH Wordlist PyPI publisher (Linux/macOS)
# Author: André Henrique (LinkedIn/X: @mrhenrike)
# Usage: PYPI_TOKEN=pypi-XXXX ./scripts/publish-pypi.sh
#        ./scripts/publish-pypi.sh --test  (TestPyPI)

set -e
cd "$(dirname "$0")/.."

TEST_MODE=false
[[ "$1" == "--test" ]] && TEST_MODE=true

echo "=== WFH Wordlist PyPI Publisher ==="

if [[ -z "$PYPI_TOKEN" ]]; then
    echo "ERROR: Set PYPI_TOKEN env var: export PYPI_TOKEN=pypi-XXXX"
    exit 1
fi

rm -rf dist build *.egg-info
python -m build

python -m twine check dist/*

export TWINE_USERNAME="__token__"
export TWINE_PASSWORD="$PYPI_TOKEN"

if $TEST_MODE; then
    python -m twine upload --repository-url https://test.pypi.org/legacy/ dist/* --non-interactive
    echo "Published to TestPyPI: pip install -i https://test.pypi.org/simple/ wfh-wordlist"
else
    python -m twine upload dist/* --non-interactive
    VER=$(python -c "import wfh; print(wfh.VERSION)")
    echo ""
    echo "=== Published wfh-wordlist v${VER} to PyPI ==="
    echo "Install: pip install wfh-wordlist==${VER}"
    echo "URL: https://pypi.org/project/wfh-wordlist/${VER}/"
fi
