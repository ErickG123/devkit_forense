# Guia de Contribuição / Contributing to ForenseLab

Bem-vindo ao guia de contribuição do **ForenseLab**!  
A versão 2.0 adota uma **Arquitetura Híbrida** com padrões modernos de engenharia:
- **CLI & UX (Python / Typer / Rich):** Localizado em `src/`, responsável pelo parsing de comandos, orquestração IPC, formatação visual no terminal e geração de laudos periciais com Jinja2.
- **High-Performance Core (Go 1.22+ Puro / Zero CGO):** Localizado em `core/`, responsável por varreduras de rede concorrentes com Worker Pools, contorno de locks de arquivos em tempo de execução (`windows.CreateFile`) e descriptografia nativa DPAPI (`CryptUnprotectData`).
- **Front-end Web SPA (Opcional / Angular 17+):** Localizado em `forenselab-ui/`, consumindo a API REST do FastAPI.

---

## 🛠️ 1. Configurando o Ambiente Local de Desenvolvimento

### Pré-requisitos:
- **Python 3.11+**
- **Go 1.22+** (apenas para quem for alterar ou compilar código dentro de `core/`)
- **Git**

### Passo 1: Clone do Repositório
```bash
git clone https://github.com/ErickG123/devkit_forense.git
cd devkit_forense
```

### Passo 2: Inicialização Limpa do Virtualenv
Recomendamos o uso dos scripts de reset automatizados para garantir que nenhuma dependência obsoleta contamine o ambiente:

* **No Windows (PowerShell):**
  ```powershell
  .\reset_env.ps1
  ```
* **No Linux / macOS (Bash):**
  ```bash
  chmod +x reset_env.sh
  ./reset_env.sh
  ```
* **Ou via Makefile:**
  ```bash
  make reset-env
  ```

---

## ⚡ 2. Modo de Desenvolvimento JIT (Just-In-Time)

Para desenvolver e iterar no código Go sem ter que compilar o binário estático a cada alteração:

```bash
# Linux / macOS:
export FORENSE_DEV=1

# Windows (PowerShell):
$env:FORENSE_DEV="1"
```

Com `FORENSE_DEV=1` ativo, o módulo `src/shared/binary_resolver.py` delega a execução diretamente para:
```bash
go run ./cmd/forense-core <comando> [argumentos]
```

---

## 📐 3. Padrões de Código e Regras Arquiteturais

### A. Regras do Go Core (`core/`)
1. **Zero CGO:** É terminantemente proibido utilizar pacotes que dependam de toolchains C/C++ externas (como `go-sqlite3`). Para manipulação de SQLite, utilize estritamente `modernc.org/sqlite`.
2. **Contrato Estrito de IPC:**
   - O `os.Stdout` é **exclusivo** para dados estruturados JSON (`ResponseEnvelope` ou NDJSON para streaming). **Nunca use `fmt.Println` avulso no stdout.**
   - O `os.Stderr` é reservado para streaming de progresso em formato **NDJSON** via `ipc.EmitProgress()`.
3. **Visibilidade de Pacotes:** Funções e structs devem ser exportadas (primeira letra maiúscula) somente se forem consumidas fora do seu respectivo pacote.

### B. Regras do Python CLI (`src/`)
1. **Thin-Client UX:** Mantenha a camada Python focada em validação de argumentos do Typer e apresentação em tabelas Rich. Lógicas pesadas de rede ou cripto devem ser delegadas ao Go via `engine.run_go_core()` ou `engine.stream_go_core()`.
2. **Imports Otimizados:** Mantenha importações de bibliotecas pesadas de forma lazy dentro das funções dos comandos para manter o tempo de resposta do `--help` inferior a 200ms.

---

## 🧪 4. Executando a Bateria de Testes

Antes de submeter qualquer alteração, garanta que todos os testes passem:

```bash
# 1. Executa testes unitários isolados em Go (Table-Driven Tests)
make test-go

# 2. Executa testes unitários Python com Mocks (FORENSE_MOCK=1)
make test-python-unit

# 3. Executa testes de integração real IPC (compilação Go JIT + Typer E2E)
make test-integration

# Ou execute toda a esteira de uma vez:
make test
```

### Linters e Formatação:
```bash
# Python
ruff format src/ tests/
ruff check src/ tests/ --fix

# Go
cd core
go fmt ./...
go vet ./...
```

---

## 🚀 5. Submissão de Pull Requests (PR)

1. Crie uma branch descritiva a partir de `main` (ex.: `feat/novo-artefato-browser` ou `fix/tratamento-timeout`).
2. Siga o padrão de Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`).
3. Certifique-se de que a esteira de testes do GitHub Actions passe em todas as plataformas (Windows, Linux e macOS).
4. Abra o Pull Request descrevendo claramente:
   - O problema ou oportunidade de melhoria abordada.
   - O que foi alterado nas camadas Python e/ou Go.
   - Evidências ou prints dos testes locais executados com sucesso.
