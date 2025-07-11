# ANP SDK 本地 DNS 配置脚本 (Windows PowerShell)

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("setup", "remove", "verify", "list", "help")]
    [string]$Action = "help"
)

# 域名列表
$Domains = @(
    "user.localhost",
    "service.localhost", 
    "agent.localhost",
    "test.localhost",
    "api.localhost",
    "admin.localhost"
)

$HostsFile = "C:\Windows\System32\drivers\etc\hosts"

# 检查管理员权限
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# 添加域名到 hosts 文件
function Add-Domains {
    Write-Host "🔧 配置本地 DNS..." -ForegroundColor Blue
    
    # 备份原始文件
    $BackupFile = "$HostsFile.anp_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    Write-Host "📋 备份原始 hosts 文件到: $BackupFile" -ForegroundColor Yellow
    Copy-Item $HostsFile $BackupFile
    
    # 读取现有内容
    $HostsContent = Get-Content $HostsFile
    
    # 添加标记和域名
    $NewContent = @()
    $NewContent += $HostsContent
    $NewContent += ""
    $NewContent += "# ANP SDK Local DNS Configuration - Start"
    $NewContent += "# Generated on $(Get-Date)"
    
    foreach ($Domain in $Domains) {
        if ($HostsContent -match "127\.0\.0\.1\s+$Domain") {
            Write-Host "⚠️  域名 $Domain 已存在，跳过" -ForegroundColor Yellow
        } else {
            $NewContent += "127.0.0.1 $Domain"
            Write-Host "✅ 添加域名: $Domain" -ForegroundColor Green
        }
    }
    
    $NewContent += "# ANP SDK Local DNS Configuration - End"
    $NewContent += ""
    
    # 写入文件
    $NewContent | Out-File -FilePath $HostsFile -Encoding ASCII
    
    Write-Host "🎉 本地 DNS 配置完成！" -ForegroundColor Green
}

# 移除域名配置
function Remove-Domains {
    Write-Host "🧹 清理本地 DNS 配置..." -ForegroundColor Blue
    
    $HostsContent = Get-Content $HostsFile
    $NewContent = @()
    $SkipLines = $false
    
    foreach ($Line in $HostsContent) {
        if ($Line -match "# ANP SDK Local DNS Configuration - Start") {
            $SkipLines = $true
            continue
        }
        if ($Line -match "# ANP SDK Local DNS Configuration - End") {
            $SkipLines = $false
            continue
        }
        if (-not $SkipLines) {
            # 检查是否是单独的域名行
            $IsDomainLine = $false
            foreach ($Domain in $Domains) {
                if ($Line -match "127\.0\.0\.1\s+$Domain") {
                    $IsDomainLine = $true
                    break
                }
            }
            if (-not $IsDomainLine) {
                $NewContent += $Line
            }
        }
    }
    
    $NewContent | Out-File -FilePath $HostsFile -Encoding ASCII
    Write-Host "✅ 本地 DNS 配置已清理" -ForegroundColor Green
}

# 验证配置
function Test-Configuration {
    Write-Host "🔍 验证 DNS 配置..." -ForegroundColor Blue
    
    foreach ($Domain in $Domains) {
        try {
            $Result = Test-Connection -ComputerName $Domain -Count 1 -Quiet
            if ($Result) {
                Write-Host "✅ $Domain -> 127.0.0.1" -ForegroundColor Green
            } else {
                Write-Host "❌ $Domain 解析失败" -ForegroundColor Red
            }
        } catch {
            Write-Host "❌ $Domain 解析失败" -ForegroundColor Red
        }
    }
}

# 列出域名
function Show-Domains {
    Write-Host "📋 ANP SDK 配置的域名:" -ForegroundColor Blue
    foreach ($Domain in $Domains) {
        Write-Host "  ✓ $Domain" -ForegroundColor Green
    }
    
    Write-Host ""
    Write-Host "🌐 测试 URL:" -ForegroundColor Blue
    foreach ($Domain in $Domains) {
        Write-Host "  http://$Domain:9527" -ForegroundColor Yellow
    }
}

# 显示帮助
function Show-Help {
    Write-Host "ANP SDK 本地 DNS 配置脚本" -ForegroundColor Blue
    Write-Host ""
    Write-Host "用法:"
    Write-Host "  .\setup_local_dns.ps1 -Action setup    - 配置本地 DNS"
    Write-Host "  .\setup_local_dns.ps1 -Action remove   - 移除本地 DNS 配置"
    Write-Host "  .\setup_local_dns.ps1 -Action verify   - 验证 DNS 配置"
    Write-Host "  .\setup_local_dns.ps1 -Action list     - 列出配置的域名"
    Write-Host "  .\setup_local_dns.ps1 -Action help     - 显示帮助信息"
    Write-Host ""
    Write-Host "配置的域名:"
    foreach ($Domain in $Domains) {
        Write-Host "  - $Domain"
    }
}

# 主逻辑
switch ($Action) {
    "setup" {
        if (-not (Test-Administrator)) {
            Write-Host "❌ 需要管理员权限来修改 hosts 文件" -ForegroundColor Red
            Write-Host "请以管理员身份运行 PowerShell" -ForegroundColor Yellow
            exit 1
        }
        Add-Domains
        Write-Host ""
        Write-Host "📋 后续步骤:" -ForegroundColor Blue
        Write-Host "1. 启动 ANP SDK 服务: python -m anp_open_sdk_framework.server --host 0.0.0.0 --port 9527" -ForegroundColor Yellow
        Write-Host "2. 验证配置: .\setup_local_dns.ps1 -Action verify" -ForegroundColor Yellow
        Write-Host "3. 访问测试: curl http://user.localhost:9527/wba/user/test/did.json" -ForegroundColor Yellow
    }
    "remove" {
        if (-not (Test-Administrator)) {
            Write-Host "❌ 需要管理员权限来修改 hosts 文件" -ForegroundColor Red
            Write-Host "请以管理员身份运行 PowerShell" -ForegroundColor Yellow
            exit 1
        }
        Remove-Domains
    }
    "verify" {
        Test-Configuration
    }
    "list" {
        Show-Domains
    }
    default {
        Show-Help
    }
}
