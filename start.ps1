# Academic Paper Assistant - 一键启动脚本
# 支持：启动/停止/重启/查看状态

param(
    [Parameter(Position = 0)]
    [ValidateSet("start", "stop", "restart", "status", "")]
    [string]$Action = ""
)

# 配置
$BackendPort = 8000
$FrontendPort = 5173
$BackendTitle = "APA-Backend"
$FrontendTitle = "APA-Frontend"

# 颜色输出
function Write-Color($Text, $Color = "White") {
    Write-Host $Text -ForegroundColor $Color
}

function Show-Header {
    Clear-Host
    Write-Color "==========================================" "Cyan"
    Write-Color "   Academic Paper Assistant - 控制台" "Green"
    Write-Color "==========================================" "Cyan"
    Write-Host ""
}

function Test-ServiceStatus {
    $backendRunning = Get-NetTCPConnection -LocalPort $BackendPort -ErrorAction SilentlyContinue
    $frontendRunning = Get-NetTCPConnection -LocalPort $FrontendPort -ErrorAction SilentlyContinue

    return @{
        Backend = [bool]$backendRunning
        Frontend = [bool]$frontendRunning
    }
}

function Start-Backend {
    Write-Color "[INFO] 正在启动后端服务..." "Yellow"

    # 检查端口是否被占用
    $existing = Get-NetTCPConnection -LocalPort $BackendPort -ErrorAction SilentlyContinue
    if ($existing) {
        Write-Color "[WARNING] 端口 $BackendPort 已被占用" "Yellow"
        return
    }

    # 启动后端
    $backendCmd = @"
cd /d "$PSScriptRoot"
call .venv\Scripts\activate.bat
echo [BACKEND] 正在启动...
python backend/api.py
pause
"@

    Start-Process cmd.exe -ArgumentList "/k", $backendCmd -WindowStyle Normal

    # 等待服务启动
    $retry = 0
    while ($retry -lt 10) {
        Start-Sleep -Seconds 1
        $test = Test-NetConnection -ComputerName localhost -Port $BackendPort -WarningAction SilentlyContinue
        if ($test.TcpTestSucceeded) {
            Write-Color "[OK] 后端服务已启动 (http://localhost:$BackendPort)" "Green"
            return
        }
        $retry++
    }
    Write-Color "[ERROR] 后端服务启动超时" "Red"
}

function Start-Frontend {
    Write-Color "[INFO] 正在启动前端服务..." "Yellow"

    # 检查端口是否被占用
    $existing = Get-NetTCPConnection -LocalPort $FrontendPort -ErrorAction SilentlyContinue
    if ($existing) {
        Write-Color "[WARNING] 端口 $FrontendPort 已被占用" "Yellow"
        return
    }

    # 启动前端
    $frontendCmd = @"
cd /d "$PSScriptRoot\frontend"
echo [FRONTEND] 正在启动...
npm run dev
pause
"@

    Start-Process cmd.exe -ArgumentList "/k", $frontendCmd -WindowStyle Normal

    Start-Sleep -Seconds 3
    Write-Color "[OK] 前端服务已启动 (http://localhost:$FrontendPort)" "Green"
}

function Stop-Services {
    Write-Color "[INFO] 正在关闭服务..." "Yellow"

    # 查找并关闭占用端口的进程
    Get-NetTCPConnection -LocalPort $BackendPort, $FrontendPort -ErrorAction SilentlyContinue |
        ForEach-Object {
            $proc = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue
            if ($proc) {
                Write-Color "[INFO] 关闭进程: $($proc.ProcessName) (PID: $($proc.Id))" "Gray"
                Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
            }
        }

    # 关闭相关窗口
    Get-Process | Where-Object {
        $_.MainWindowTitle -match "APA-Backend|APA-Frontend|后端服务|前端服务|backend|frontend"
    } | ForEach-Object {
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    }

    Write-Color "[OK] 服务已关闭" "Green"
}

function Show-Status {
    $status = Test-ServiceStatus

    Write-Color "服务状态:" "Cyan"
    Write-Host "  后端 (Port $BackendPort): " -NoNewline
    if ($status.Backend) {
        Write-Color "运行中" "Green"
    } else {
        Write-Color "已停止" "Red"
    }

    Write-Host "  前端 (Port $FrontendPort): " -NoNewline
    if ($status.Frontend) {
        Write-Color "运行中" "Green"
    } else {
        Write-Color "已停止" "Red"
    }

    if ($status.Backend -and $status.Frontend) {
        Write-Host ""
        Write-Color "  访问地址:" "Cyan"
        Write-Color "    前端: http://localhost:$FrontendPort" "Yellow"
        Write-Color "    后端: http://localhost:$BackendPort" "Yellow"
    }
}

function Show-Menu {
    Show-Header
    Show-Status

    Write-Host ""
    Write-Color "操作选项:" "Cyan"
    Write-Color "  [1] 启动服务" "Green"
    Write-Color "  [2] 停止服务" "Red"
    Write-Color "  [3] 重启服务" "Yellow"
    Write-Color "  [4] 刷新状态" "Blue"
    Write-Color "  [0] 退出" "Gray"
    Write-Host ""
}

# 主逻辑
if ($Action -eq "stop") {
    Stop-Services
    exit
}

if ($Action -eq "restart") {
    Stop-Services
    Start-Sleep -Seconds 2
    Start-Backend
    Start-Frontend
    Show-Status
    exit
}

if ($Action -eq "status") {
    Show-Header
    Show-Status
    exit
}

if ($Action -eq "start" -or $Action -eq "") {
    Show-Header

    # 检查虚拟环境
    if (-not (Test-Path ".venv\Scripts\activate.bat")) {
        Write-Color "[ERROR] 虚拟环境不存在，请先运行 install.bat" "Red"
        pause
        exit 1
    }

    # 检查前端依赖
    if (-not (Test-Path "frontend\node_modules")) {
        Write-Color "[ERROR] 前端依赖不存在，请先运行 install.bat" "Red"
        pause
        exit 1
    }

    $status = Test-ServiceStatus

    if ($status.Backend -and $status.Frontend) {
        Write-Color "[INFO] 服务已经在运行中" "Green"
        Show-Status
    } else {
        Write-Color "正在启动 Academic Paper Assistant..." "Green"
        Write-Host ""

        if (-not $status.Backend) {
            Start-Backend
        }

        Start-Sleep -Seconds 2

        if (-not $status.Frontend) {
            Start-Frontend
        }

        Write-Host ""
        Write-Color "==========================================" "Cyan"
        Write-Color "   启动完成！" "Green"
        Write-Color "==========================================" "Cyan"
        Write-Host ""
        Write-Color "访问地址:" "Yellow"
        Write-Color "  前端界面: http://localhost:$FrontendPort" "White"
        Write-Color "  API 接口: http://localhost:$BackendPort" "White"
        Write-Host ""

        # 自动打开浏览器
        $openBrowser = Read-Host "是否自动打开浏览器? (Y/n)"
        if ($openBrowser -ne "n") {
            Start-Process "http://localhost:$FrontendPort"
        }
    }

    # 交互式菜单
    do {
        Write-Host ""
        $choice = Read-Host "输入命令 (1=启动 2=停止 3=重启 4=状态 0=退出)"

        switch ($choice) {
            "1" {
                $status = Test-ServiceStatus
                if (-not $status.Backend) { Start-Backend }
                if (-not $status.Frontend) { Start-Frontend }
            }
            "2" { Stop-Services }
            "3" {
                Stop-Services
                Start-Sleep -Seconds 2
                Start-Backend
                Start-Sleep -Seconds 1
                Start-Frontend
            }
            "4" { Show-Status }
            "0" {
                $confirm = Read-Host "是否同时关闭所有服务? (Y/n)"
                if ($confirm -ne "n") {
                    Stop-Services
                }
                exit
            }
        }
    } while ($true)
}
