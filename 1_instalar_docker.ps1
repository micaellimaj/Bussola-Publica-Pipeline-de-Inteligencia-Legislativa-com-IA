# =============================================================================
# Bussola Publica - Passo 1: instalar o Docker Desktop
# -----------------------------------------------------------------------------
# Como rodar:
#   1. Clique com o botao direito neste arquivo > "Executar com o PowerShell"
#      OU abra o PowerShell COMO ADMINISTRADOR e rode:
#         powershell -ExecutionPolicy Bypass -File .\1_instalar_docker.ps1
# -----------------------------------------------------------------------------
# O que faz: verifica se o Docker ja existe; se nao, instala via winget.
# Depois pede para voce iniciar o Docker Desktop e aceitar os termos (1 vez).
# =============================================================================

Write-Host "=== Bussola Publica - Instalacao do Docker Desktop ===" -ForegroundColor Cyan

# 1. Ja tem Docker?
$docker = Get-Command docker -ErrorAction SilentlyContinue
if ($docker) {
    Write-Host "[OK] Docker ja esta instalado: " -ForegroundColor Green -NoNewline
    docker --version
    Write-Host "Pode pular para o script 2_subir_n8n.ps1." -ForegroundColor Green
    Read-Host "Pressione ENTER para sair"
    exit 0
}

# 2. Tem winget?
$winget = Get-Command winget -ErrorAction SilentlyContinue
if (-not $winget) {
    Write-Host "[!] 'winget' nao encontrado nesta maquina." -ForegroundColor Yellow
    Write-Host "    Baixe e instale o Docker Desktop manualmente em:" -ForegroundColor Yellow
    Write-Host "    https://www.docker.com/products/docker-desktop/" -ForegroundColor White
    Read-Host "Pressione ENTER para sair"
    exit 1
}

# 3. Instala via winget
Write-Host "[..] Instalando o Docker Desktop via winget (pode demorar e pedir confirmacao)..." -ForegroundColor Cyan
winget install -e --id Docker.DockerDesktop --accept-source-agreements --accept-package-agreements

if ($LASTEXITCODE -ne 0) {
    Write-Host "[!] A instalacao automatica falhou ou foi cancelada." -ForegroundColor Yellow
    Write-Host "    Instale manualmente em: https://www.docker.com/products/docker-desktop/" -ForegroundColor White
    Read-Host "Pressione ENTER para sair"
    exit 1
}

Write-Host ""
Write-Host "[OK] Docker Desktop instalado." -ForegroundColor Green
Write-Host "-------------------------------------------------------------------" -ForegroundColor Cyan
Write-Host "PROXIMOS PASSOS (importantes):" -ForegroundColor Cyan
Write-Host "  1. REINICIE o Windows se for solicitado (o Docker usa o WSL2)." -ForegroundColor White
Write-Host "  2. Abra o 'Docker Desktop' pelo menu Iniciar e ACEITE os termos." -ForegroundColor White
Write-Host "     Espere o icone da baleia ficar verde / 'Running'." -ForegroundColor White
Write-Host "  3. Depois, rode o script: 2_subir_n8n.ps1" -ForegroundColor White
Write-Host "-------------------------------------------------------------------" -ForegroundColor Cyan
Read-Host "Pressione ENTER para sair"
