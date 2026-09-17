# ==============================================================================
# Makefile - Automação e Developer Experience (DevEx) do ForenseLab
# ==============================================================================

.PHONY: help dev build-core build-all test lint clean format run-mock

SHELL := bash
PYTHON := python
GO := go
BIN_DIR := src/bin
CORE_DIR := core

help: ## Exibe os comandos disponíveis
	@echo "========================================================================"
	@echo "                ForenseLab - Comandos de Desenvolvimento                "
	@echo "========================================================================"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

dev: ## Configura ambiente de desenvolvimento JIT (FORENSE_DEV=1)
	@echo "[*] Instalando dependências e CLI em modo editável..."
	$(PYTHON) -m pip install -e ".[dev]"
	@echo "[+] Modo de desenvolvimento ativo!"
	@echo "    Para testar o Go JIT sem compilar a cada alteração, execute:"
	@echo "    export FORENSE_DEV=1  (Linux/macOS)  ou  \$$env:FORENSE_DEV=\"1\" (Windows)"

reset-env: ## [RESET] Remove virtualenv antigo, recria e reinstala pacote v2.0 limpo
	@echo "[*] Reiniciando virtual environment do zero..."
	@rm -rf .venv venv build dist *.egg-info
	$(PYTHON) -m venv .venv
	@echo "[+] Novo virtualenv criado em .venv/"
	@echo "    Ative o ambiente e execute: pip install -e .[dev]"
	@echo "    Linux/macOS: source .venv/bin/activate && pip install -e \".[dev]\""
	@echo "    Windows PS:  .\\.venv\\Scripts\\Activate.ps1; pip install -e \".[dev]\""

build-core: ## Compila o binário Go nativo para src/bin/ com stripping (-s -w)
	@echo "[*] Compilando Go Core nativo..."
	@mkdir -p $(BIN_DIR)
	@cd $(CORE_DIR) && CGO_ENABLED=0 $(GO) build -trimpath -ldflags="-s -w" -o ../$(BIN_DIR)/forense-core ./cmd/forense-core
	@if [ -f "$(BIN_DIR)/forense-core" ] && [ "$$(uname -o 2>/dev/null)" = "Msys" -o "$$(uname -s 2>/dev/null | grep -i mingw)" ]; then \
		mv $(BIN_DIR)/forense-core $(BIN_DIR)/forense-core.exe; \
	fi
	@echo "[+] Binário compilado com sucesso em $(BIN_DIR)/"

build-all: ## Cross-compila o Go Core para Windows, Linux e macOS
	@echo "[*] Compilando para Windows (amd64)..."
	@cd $(CORE_DIR) && CGO_ENABLED=0 GOOS=windows GOARCH=amd64 $(GO) build -trimpath -ldflags="-s -w" -o ../$(BIN_DIR)/forense-core.exe ./cmd/forense-core
	@echo "[*] Compilando para Linux (amd64)..."
	@cd $(CORE_DIR) && CGO_ENABLED=0 GOOS=linux GOARCH=amd64 $(GO) build -trimpath -ldflags="-s -w" -o ../$(BIN_DIR)/forense-core-linux-amd64 ./cmd/forense-core
	@echo "[*] Compilando para macOS (arm64 Apple Silicon)..."
	@cd $(CORE_DIR) && CGO_ENABLED=0 GOOS=darwin GOARCH=arm64 $(GO) build -trimpath -ldflags="-s -w" -o ../$(BIN_DIR)/forense-core-darwin-arm64 ./cmd/forense-core
	@echo "[+] Cross-compilação concluída em $(BIN_DIR)/"

test: test-all ## Executa a esteira completa (Go Unit -> Python Unit -> Integração IPC)

test-go: ## 1. Executa testes unitários no Go (portscan, DPAPI decrypt)
	@echo "[*] [1/3] Executando testes unitários Go..."
	@cd $(CORE_DIR) && $(GO) test -v ./...

test-python-unit: ## 2. Executa testes unitários em Python com Mocks
	@echo "[*] [2/3] Executando testes unitários Python..."
	FORENSE_MOCK=1 pytest tests/test_network.py tests/test_cli/test_network_scan_mocked.py -v

test-integration: build-core ## 3. Executa testes de integração reais Go-Python IPC
	@echo "[*] [3/3] Executando testes de integração IPC..."
	pytest tests/integration/ -v

test-all: test-go test-python-unit test-integration ## Executa todas as camadas na ordem sequencial recomendada
	@echo "[+] Todos os testes (Go, Python Unit e Integracao) passaram com sucesso!"

lint: ## Executa checagens estáticas de código (ruff e go vet)
	@echo "[*] Checando código Go..."
	@cd $(CORE_DIR) && $(GO) vet ./...
	@echo "[*] Checando código Python..."
	ruff check src/ tests/

format: ## Formata o código automaticamente (ruff e go fmt)
	@echo "[*] Formatando Go..."
	@cd $(CORE_DIR) && $(GO) fmt ./...
	@echo "[*] Formatando Python..."
	ruff format src/ tests/

run-mock: ## Executa a simulação IPC end-to-end (Python + Go)
	@echo "[*] Disparando tarefa Mock via CLI..."
	$(PYTHON) -c "import sys; sys.path.insert(0, 'src'); from shared.engine import run_go_core; print(run_go_core('mock', task_name='Simulacao Forense'))"

clean: ## Limpa artefatos temporários, caches e binários gerados
	@echo "[*] Removendo caches e arquivos de build..."
	@rm -rf build/ dist/ *.egg-info .pytest_cache/ .ruff_cache/
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find $(BIN_DIR) -type f ! -name ".gitkeep" -exec rm -f {} + 2>/dev/null || true
	@echo "[+] Limpeza concluída!"
