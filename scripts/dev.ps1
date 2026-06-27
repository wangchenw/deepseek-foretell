# Foretell 本地开发（Windows）：安装依赖并启动后端 + 前端
# 用法: .\scripts\dev.ps1  或  scripts\dev.bat
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($PSScriptRoot)) {
    $PSScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
}
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root

$script:BackendProcess = $null
$script:FrontendProcess = $null
$script:ApiHost = "127.0.0.1"
$script:ApiPort = "8000"

function Write-Log([string]$Message) {
    Write-Host "[foretell] $Message" -ForegroundColor Cyan
}

function Write-Warn([string]$Message) {
    Write-Host "[foretell] $Message" -ForegroundColor Yellow
}

function Write-Err([string]$Message) {
    Write-Host "[foretell] $Message" -ForegroundColor Red
}

function Stop-DevProcess($Process, [string]$Label) {
    if ($null -eq $Process) { return }
    if (-not $Process.HasExited) {
        Write-Log ('停止{0} (pid {1})...' -f $Label, $Process.Id)
        Stop-Process -Id $Process.Id -Force -ErrorAction SilentlyContinue
    }
}

function Invoke-Cleanup {
    Stop-DevProcess $script:FrontendProcess "前端"
    Stop-DevProcess $script:BackendProcess "后端"
}

function Test-CommandExists([string]$Name) {
    return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

function Require-Command([string]$Name) {
    if (Test-CommandExists $Name) { return }
    Write-Err "未找到命令: $Name"
    switch ($Name) {
        "uv" { Write-Err "安装 uv: https://docs.astral.sh/uv/getting-started/installation/" }
        "node" { Write-Err "请先安装 Node.js 20+ (https://nodejs.org 或 nvm-windows)" }
        "pnpm" { Write-Err "安装 pnpm: corepack enable && corepack prepare pnpm@latest --activate" }
    }
    exit 1
}

function Ensure-Pnpm {
    if (Test-CommandExists "pnpm") { return }
    if (Test-CommandExists "corepack") {
        Write-Log "启用 corepack 以使用 pnpm..."
        & corepack enable 2>$null
        & corepack prepare pnpm@latest --activate 2>$null
    }
    Require-Command "pnpm"
}

function Import-DotEnv {
    param([string]$EnvFilePath)

    if ([string]::IsNullOrWhiteSpace($EnvFilePath)) { return }
    if (-not (Test-Path -LiteralPath $EnvFilePath)) { return }

    Get-Content -LiteralPath $EnvFilePath | ForEach-Object {
        $line = $_.Trim()
        if ($line -eq "" -or $line.StartsWith("#")) { return }
        if ($line -match '^\s*([^#=]+)=(.*)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim().Trim('"').Trim("'")
            Set-Item -LiteralPath "env:$name" -Value $value
        }
    }
}

function Get-ApiEndpoint {
    $script:ApiHost = "127.0.0.1"
    $script:ApiPort = "8000"
    Import-DotEnv -EnvFilePath (Join-Path $Root ".env")
    if ($env:API_HOST) { $script:ApiHost = $env:API_HOST }
    if ($env:API_PORT) { $script:ApiPort = $env:API_PORT }
}

function Test-BackendHealth {
    param([string]$Url)
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 2
        return ($response.StatusCode -ge 200 -and $response.StatusCode -lt 300)
    }
    catch {
        return $false
    }
}

function Wait-ForBackend {
    $url = "http://$($script:ApiHost):$($script:ApiPort)/health"
    Write-Log "等待后端就绪: $url"
    for ($i = 1; $i -le 60; $i++) {
        if (Test-BackendHealth -Url $url) {
            Write-Log "后端已就绪"
            return $true
        }
        if ($script:BackendProcess -and $script:BackendProcess.HasExited) {
            Write-Err "后端进程已退出，请检查上方日志"
            return $false
        }
        Start-Sleep -Seconds 1
    }
    Write-Err "后端启动超时（60s）"
    return $false
}

function Invoke-Pnpm {
    param(
        [Parameter(Mandatory = $true)][string]$WorkingDirectory,
        [Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments
    )
    & pnpm --dir $WorkingDirectory @Arguments
}

function Test-PnpmApproveBuilds {
    param([string]$WorkingDirectory)
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        & pnpm --dir $WorkingDirectory approve-builds --help 2>$null | Out-Null
        return ($LASTEXITCODE -eq 0)
    }
    finally {
        $ErrorActionPreference = $prev
    }
}

function Resolve-NativeCommand([string]$Name) {
    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    if (-not $cmd) { return $Name }
    if ($cmd.CommandType -eq "ExternalScript") {
        $cmdPath = [System.IO.Path]::ChangeExtension($cmd.Source, ".cmd")
        if (Test-Path -LiteralPath $cmdPath) { return $cmdPath }
    }
    return $cmd.Source
}

function Start-DevProcess([string]$FilePath, [string[]]$ArgumentList, [string]$WorkingDirectory) {
    $exe = Resolve-NativeCommand $FilePath
    return Start-Process -FilePath $exe -ArgumentList $ArgumentList -WorkingDirectory $WorkingDirectory -PassThru -NoNewWindow
}

try {
    Require-Command "uv"
    Require-Command "node"
    Ensure-Pnpm

    $nodeMajor = [int](& node -p "process.versions.node.split('.')[0]")
    if ($nodeMajor -lt 20) {
        Write-Warn "建议使用 Node.js 20+，当前: $(& node -v)"
    }

    Write-Log "安装 Python 3.14 并同步后端依赖..."
    & uv python install 3.14
    if ($LASTEXITCODE -ne 0) { throw "uv python install 失败" }
    & uv sync
    if ($LASTEXITCODE -ne 0) { throw "uv sync 失败" }

    $envFile = Join-Path $Root ".env"
    if (-not (Test-Path $envFile)) {
        Copy-Item (Join-Path $Root ".env.example") $envFile
        Write-Warn "已创建 .env，请填入 MINIMAX_API_KEY 与 MYSQL_* 等配置后重新运行"
    }

    $frontendEnv = Join-Path $Root "frontend\.env.local"
    if (-not (Test-Path $frontendEnv)) {
        Copy-Item (Join-Path $Root "frontend\.env.local.example") $frontendEnv
        Write-Log "已创建 frontend/.env.local"
    }

    Import-DotEnv -EnvFilePath $envFile
    if ($env:MINIMAX_API_KEY -eq "your-minimax-api-key" -or [string]::IsNullOrWhiteSpace($env:MINIMAX_API_KEY)) {
        Write-Warn "MINIMAX_API_KEY 未配置，对话功能可能不可用"
    }

    $frontendDir = Join-Path $Root "frontend"
    if (-not (Test-Path -LiteralPath $frontendDir)) {
        throw "未找到 frontend 目录: $frontendDir"
    }

    Write-Log "安装前端依赖..."
    Invoke-Pnpm -WorkingDirectory $frontendDir install --frozen-lockfile
    if ($LASTEXITCODE -ne 0) { throw "pnpm install 失败" }

    if (Test-PnpmApproveBuilds -WorkingDirectory $frontendDir) {
        $prev = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        try {
            & pnpm --dir $frontendDir approve-builds --all 2>$null | Out-Null
            Invoke-Pnpm -WorkingDirectory $frontendDir install --frozen-lockfile
            if ($LASTEXITCODE -ne 0) { throw "pnpm install 失败" }
        }
        finally {
            $ErrorActionPreference = $prev
        }
    }

    Get-ApiEndpoint

    Write-Log "启动后端: uvicorn api.main:app --reload --host $($script:ApiHost) --port $($script:ApiPort)"
    $script:BackendProcess = Start-DevProcess "uv" @(
        "run", "uvicorn", "api.main:app", "--reload",
        "--host", $script:ApiHost, "--port", $script:ApiPort
    ) $Root

    if (-not (Wait-ForBackend)) {
        exit 1
    }

    Write-Log '启动前端: pnpm dev (http://localhost:3000)'
    $script:FrontendProcess = Start-DevProcess "pnpm" @("--dir", $frontendDir, "dev") $Root

    Write-Host ""
    Write-Log "开发环境已就绪"
    Write-Log "  前端: http://localhost:3000"
    Write-Log "  后端: http://$($script:ApiHost):$($script:ApiPort)"
    Write-Log "  健康检查: http://$($script:ApiHost):$($script:ApiPort)/health"
    Write-Log "按 Ctrl+C 停止前后端"
    Write-Host ""

    while ($true) {
        $backendAlive = $script:BackendProcess -and -not $script:BackendProcess.HasExited
        $frontendAlive = $script:FrontendProcess -and -not $script:FrontendProcess.HasExited
        if (-not $backendAlive -and -not $frontendAlive) { break }
        Start-Sleep -Seconds 1
    }
}
catch {
    if ($_.Exception -isnot [System.Management.Automation.PipelineStoppedException]) {
        Write-Err $_.Exception.Message
        exit 1
    }
}
finally {
    Invoke-Cleanup
}
