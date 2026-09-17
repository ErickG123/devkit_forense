#!/usr/bin/env bash
# ==============================================================================
# ForenseLab - Reset e Instalação Limpa do Ambiente Virtual (Bash / Linux / macOS)
# ==============================================================================

set -e

echo -e "\033[36m[*] Iniciando faxina e reset do ambiente ForenseLab v2.0...\033[0m"

# 1. Remove pastas legadas de ambiente e artefatos de build
rm -rf .venv venv build dist *.egg-info .pytest_cache .ruff_cache
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# 2. Localiza Python 3
PYTHON_BIN=$(command -v python3 || command -v python)
if [ -z "$PYTHON_BIN" ]; then
    echo -e "\033[31m[-] Python não encontrado no PATH.\033[0m"
    exit 1
fi

echo -e "\033[36m[+] Criando novo ambiente virtual .venv...\033[0m"
"$PYTHON_BIN" -m venv .venv

# 3. Ativa e instala
source .venv/bin/activate
echo -e "\033[36m[*] Instalando forensic-cli em modo editável com dependências limpas...\033[0m"
pip install --upgrade pip
pip install -e ".[dev]"

echo -e "\n\033[32m[✔] Ambiente ForenseLab v2.0 configurado com sucesso!\033[0m"
echo -e "    Execute para ativar:"
echo -e "    \033[33msource .venv/bin/activate\033[0m"
echo -e "    \033[33mforensic-cli --help\033[0m\n"
