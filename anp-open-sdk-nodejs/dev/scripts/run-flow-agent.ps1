# PowerShell脚本：运行flow-anp-agent.ts示例
param (
    [switch]$wait = $false
)

# 显示启动信息
Write-Host "开始运行 flow-anp-agent.ts 示例..." -ForegroundColor Green

# 构建命令行参数
$cmdArgs = ""
if ($wait) {
    $cmdArgs = "--wait"
    Write-Host "等待用户输入模式已启用" -ForegroundColor Yellow
} else {
    Write-Host "自动模式已启用 (运行完成后自动退出)" -ForegroundColor Yellow
}

# 使用ts-node直接运行TypeScript文件
Write-Host "执行命令: npx ts-node -r tsconfig-paths/register examples/flow-anp-agent.ts $cmdArgs" -ForegroundColor Cyan
if ($cmdArgs -eq "") {
    npx ts-node -r tsconfig-paths/register examples/flow-anp-agent.ts
} else {
    npx ts-node -r tsconfig-paths/register examples/flow-anp-agent.ts $cmdArgs
}

Write-Host "程序执行完成!" -ForegroundColor Green