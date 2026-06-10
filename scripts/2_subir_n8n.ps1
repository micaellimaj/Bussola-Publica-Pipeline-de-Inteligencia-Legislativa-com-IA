# =============================================================================
# Bussola Publica - Passo 2: subir o n8n e preparar o pipeline
# -----------------------------------------------------------------------------
# Pre-requisito: Docker Desktop instalado e RODANDO (baleia verde).
# Como rodar: botao direito > "Executar com o PowerShell"
#   ou:  powershell -ExecutionPolicy Bypass -File .\2_subir_n8n.ps1
# -----------------------------------------------------------------------------
# O que faz, sem voce digitar quase nada:
#   1. Confere se o Docker esta rodando.
#   2. Cria o docker/.env (gera chave de criptografia automaticamente).
#   3. Descobre o caminho do seu repositorio (ou pergunta).
#   4. Sobe o n8n com 'docker compose up -d --build'.
#   5. Instala as dependencias do projeto (poetry install) no container.
#   6. Abre http://localhost:5678 no navegador.
# =============================================================================

$ErrorActionPreference = "Stop"
Write-Host "=== Bussola Publica - Subindo o n8n ===" -ForegroundColor Cyan

# Pasta docker/ (esta ao lado de scripts/)
$dockerDir = Resolve-Path (Join-Path $PSScriptRoot "..\docker")
Set-Location $dockerDir
Write-Host "[i] Pasta docker: $dockerDir" -ForegroundColor DarkGray

# 1. Docker rodando?
try {
    docker info *> $null
    if ($LASTEXITCODE -ne 0) { throw "Docker nao respondeu." }
    Write-Host "[OK] Docker esta rodando." -ForegroundColor Green
} catch {
    Write-Host "[X] O Docker Desktop nao esta rodando." -ForegroundColor Red
    Write-Host "    Abra o 'Docker Desktop', espere a baleia ficar verde e rode este script de novo." -ForegroundColor Yellow
    Read-Host "Pressione ENTER para sair"; exit 1
}

# 2. Descobrir o caminho do repositorio (pasta com main.py E pyproject.toml)
function Find-Repo {
    $roots = @(
        (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path,  # ex.: ...\Pos Tech
        (Join-Path $env:USERPROFILE "Desktop"),
        (Join-Path $env:USERPROFILE "OneDrive\Desktop"),
        $env:USERPROFILE
    ) | Select-Object -Unique
    foreach ($r in $roots) {
        if (-not (Test-Path $r)) { continue }
        $hit = Get-ChildItem -Path $r -Recurse -Depth 4 -Filter "pyproject.toml" -ErrorAction SilentlyContinue |
            Where-Object { Test-Path (Join-Path $_.DirectoryName "main.py") } |
            Select-Object -First 1
        if ($hit) { return $hit.DirectoryName }
    }
    return $null
}

Write-Host "[..] Procurando a pasta do seu repositorio (main.py + pyproject.toml)..." -ForegroundColor Cyan
$repo = Find-Repo
if ($repo) {
    Write-Host "[OK] Repositorio encontrado: $repo" -ForegroundColor Green
    $resp = Read-Host "Usar esta pasta? (S/n)"
    if ($resp -match '^[nN]') { $repo = $null }
}
if (-not $repo) {
    $repo = Read-Host "Cole o caminho da pasta do repositorio (a que tem main.py)"
}
if (-not (Test-Path (Join-Path $repo "main.py"))) {
    Write-Host "[X] Nao encontrei main.py em: $repo" -ForegroundColor Red
    Read-Host "Pressione ENTER para sair"; exit 1
}
$repoFwd = ($repo -replace '\\','/')   # docker prefere barras normais

# Aviso sobre o .env do projeto
if (-not (Test-Path (Join-Path $repo ".env"))) {
    Write-Host "[!] Atencao: nao ha .env na raiz do repo (DATABASE_URL/OPENAI_API_KEY)." -ForegroundColor Yellow
    Write-Host "    O pipeline precisa dele. Crie a partir do .env.example do projeto antes de executar." -ForegroundColor Yellow
}

# 3. Criar docker/.env se nao existir
$envPath = Join-Path $dockerDir ".env"
if (-not (Test-Path $envPath)) {
    Write-Host "[..] Criando docker/.env com chave de criptografia aleatoria..." -ForegroundColor Cyan
    $bytes = New-Object 'System.Byte[]' 24
    [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
    $key = -join ($bytes | ForEach-Object { $_.ToString('x2') })
    $user = Read-Host "Defina um usuario para o login do n8n (ENTER = admin)"
    if ([string]::IsNullOrWhiteSpace($user)) { $user = "admin" }
    $pass = Read-Host "Defina uma senha para o login do n8n (ENTER = bussola123)"
    if ([string]::IsNullOrWhiteSpace($pass)) { $pass = "bussola123" }
    @(
        "N8N_USER=$user",
        "N8N_PASSWORD=$pass",
        "N8N_ENCRYPTION_KEY=$key",
        "REPO_PATH=$repoFwd"
    ) | Set-Content -Path $envPath -Encoding UTF8
    Write-Host "[OK] docker/.env criado." -ForegroundColor Green
} else {
    Write-Host "[i] docker/.env ja existe. Atualizando apenas o REPO_PATH..." -ForegroundColor DarkGray
    $content = Get-Content $envPath | Where-Object { $_ -notmatch '^REPO_PATH=' }
    $content + "REPO_PATH=$repoFwd" | Set-Content -Path $envPath -Encoding UTF8
}

# 4. Subir o n8n
Write-Host "[..] Subindo o n8n (build na primeira vez demora alguns minutos)..." -ForegroundColor Cyan
docker compose up -d --build
if ($LASTEXITCODE -ne 0) { Write-Host "[X] Falha no docker compose up." -ForegroundColor Red; Read-Host "ENTER para sair"; exit 1 }

# 5. Esperar e instalar dependencias do projeto no container
Write-Host "[..] Aguardando o n8n iniciar..." -ForegroundColor Cyan
Start-Sleep -Seconds 12
Write-Host "[..] Instalando dependencias do projeto (poetry install) dentro do container..." -ForegroundColor Cyan
docker compose exec -T n8n sh -c "cd /opt/bussola-publica && poetry install --no-root"
if ($LASTEXITCODE -ne 0) {
    Write-Host "[!] poetry install retornou erro. Voce pode rodar manualmente depois:" -ForegroundColor Yellow
    Write-Host '    docker compose exec n8n sh -c "cd /opt/bussola-publica && poetry install --no-root"' -ForegroundColor White
}

# 6. Abrir o navegador
Write-Host ""
Write-Host "=====================================================================" -ForegroundColor Green
Write-Host " n8n no ar!  Abra:  http://localhost:5678" -ForegroundColor Green
Write-Host " Login: veja N8N_USER / N8N_PASSWORD no arquivo docker/.env" -ForegroundColor Green
Write-Host "---------------------------------------------------------------------" -ForegroundColor Green
Write-Host " Proximo: no n8n -> Import from File -> selecione" -ForegroundColor White
Write-Host "   ..\n8n\bussola_publica_ingestao_diaria.json" -ForegroundColor White
Write-Host " Configure as credenciais Postgres (Supabase) e SMTP e clique" -ForegroundColor White
Write-Host " em 'Execute Workflow' para ver os nos rodando." -ForegroundColor White
Write-Host "=====================================================================" -ForegroundColor Green
Start-Process "http://localhost:5678"
Read-Host "Pressione ENTER para sair"
