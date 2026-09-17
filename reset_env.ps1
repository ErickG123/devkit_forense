# ==============================================================================
# ForenseLab - Reset e Instalação Limpa do Ambiente Virtual (PowerShell)
# ==============================================================================

Write-Host "[*] Iniciando faxina e reset do ambiente ForenseLab v2.0..." -ForegroundColor Cyan

# 1. Remove ambientes virtuais antigos e caches de build
$pathsToRemove = @(".venv", "venv", "build", "dist", "*.egg-info", ".pytest_cache", ".ruff_cache")
foreach ($path in $pathsToRemove) {
    if (Test-Path $path) {
        Write-Host "    [-] Removendo $path..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force $path -ErrorAction SilentlyContinue
    }
}

# 2. Localiza o interpretador Python
$pythonCmd = (Get-Command py, python -ErrorAction SilentlyContinue | Select-Object -First 1).Source
if (-not $pythonCmd) {
    Write-Error "[-] Python não encontrado no PATH. Instale o Python 3.11+."
    exit 1
}

Write-Host "[+] Criando novo ambiente virtual limpo em .venv com $pythonCmd..." -ForegroundColor Cyan
& $pythonCmd -m venv .venv

# 3. Ativa o novo ambiente
$activateScript = ".\.venv\Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    Write-Host "[+] Ativando ambiente virtual..." -ForegroundColor Green
    & $activateScript
}

# 4. Atualiza pip e instala o pacote no novo ambiente
Write-Host "[*] Atualizando pip e instalando ForenseLab em modo editável (v2.0 Limpa)..." -ForegroundColor Cyan
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -e ".[dev]"

Write-Host "`n[✔] Ambiente ForenseLab v2.0 configurado com sucesso!" -ForegroundColor Green
Write-Host "    Para ativar no seu terminal:" -ForegroundColor White
Write-Host "    .\.venv\Scripts\Activate.ps1" -ForegroundColor Yellow
Write-Host "    forensic-cli --help`n" -ForegroundColor Yellow
