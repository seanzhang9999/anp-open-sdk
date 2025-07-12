#!/bin/bash

# ANP SDK 本地 DNS 配置脚本
# 用于设置多域名本地测试环境

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 域名列表
DOMAINS=(
    "user.localhost"
    "service.localhost"
    "agent.localhost"
    "test.localhost"
    "api.localhost"
    "admin.localhost"
    "open.localhost"
)

# 检测操作系统
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        echo "windows"
    else
        echo "unknown"
    fi
}

# 获取 hosts 文件路径
get_hosts_file() {
    local os=$(detect_os)
    case $os in
        "macos"|"linux")
            echo "/etc/hosts"
            ;;
        "windows")
            echo "C:/Windows/System32/drivers/etc/hosts"
            ;;
        *)
            echo "unknown"
            ;;
    esac
}

# 检查是否有管理员权限
check_permissions() {
    local hosts_file=$(get_hosts_file)
    if [[ "$hosts_file" == "unknown" ]]; then
        echo -e "${RED}❌ 不支持的操作系统${NC}"
        exit 1
    fi
    
    if [[ ! -w "$hosts_file" ]]; then
        echo -e "${YELLOW}⚠️  需要管理员权限来修改 hosts 文件${NC}"
        echo -e "${BLUE}请使用以下命令重新运行:${NC}"
        
        local os=$(detect_os)
        case $os in
            "macos"|"linux")
                echo "sudo $0 $@"
                ;;
            "windows")
                echo "以管理员身份运行此脚本"
                ;;
        esac
        exit 1
    fi
}

# 添加域名到 hosts 文件
add_domains() {
    local hosts_file=$(get_hosts_file)
    local backup_file="${hosts_file}.anp_backup_$(date +%Y%m%d_%H%M%S)"
    
    echo -e "${BLUE}🔧 配置本地 DNS...${NC}"
    
    # 备份原始 hosts 文件
    echo -e "${YELLOW}📋 备份原始 hosts 文件到: $backup_file${NC}"
    cp "$hosts_file" "$backup_file"
    
    # 添加 ANP SDK 标记
    echo "" >> "$hosts_file"
    echo "# ANP SDK Local DNS Configuration - Start" >> "$hosts_file"
    echo "# Generated on $(date)" >> "$hosts_file"
    
    # 添加域名
    for domain in "${DOMAINS[@]}"; do
        # 检查域名是否已存在
        if grep -q "127.0.0.1[[:space:]]*$domain" "$hosts_file"; then
            echo -e "${YELLOW}⚠️  域名 $domain 已存在，跳过${NC}"
        else
            echo "127.0.0.1 $domain" >> "$hosts_file"
            echo -e "${GREEN}✅ 添加域名: $domain${NC}"
        fi
    done
    
    echo "# ANP SDK Local DNS Configuration - End" >> "$hosts_file"
    echo "" >> "$hosts_file"
    
    echo -e "${GREEN}🎉 本地 DNS 配置完成！${NC}"
}

# 移除域名从 hosts 文件
remove_domains() {
    local hosts_file=$(get_hosts_file)
    local temp_file=$(mktemp)
    
    echo -e "${BLUE}🧹 清理本地 DNS 配置...${NC}"
    
    # 移除 ANP SDK 相关的行
    sed '/# ANP SDK Local DNS Configuration - Start/,/# ANP SDK Local DNS Configuration - End/d' "$hosts_file" > "$temp_file"
    
    # 移除单独的域名行（如果存在）
    for domain in "${DOMAINS[@]}"; do
        sed -i.bak "/127\.0\.0\.1[[:space:]]*$domain/d" "$temp_file"
    done
    
    # 替换原文件
    mv "$temp_file" "$hosts_file"
    
    echo -e "${GREEN}✅ 本地 DNS 配置已清理${NC}"
}

# 验证配置
verify_configuration() {
    echo -e "${BLUE}🔍 验证 DNS 配置...${NC}"
    
    for domain in "${DOMAINS[@]}"; do
        if ping -c 1 -W 1000 "$domain" >/dev/null 2>&1; then
            echo -e "${GREEN}✅ $domain -> 127.0.0.1${NC}"
        else
            echo -e "${RED}❌ $domain 解析失败${NC}"
        fi
    done
}

# 显示帮助信息
show_help() {
    echo -e "${BLUE}ANP SDK 本地 DNS 配置脚本${NC}"
    echo ""
    echo "用法:"
    echo "  $0 setup    - 配置本地 DNS"
    echo "  $0 remove   - 移除本地 DNS 配置"
    echo "  $0 verify   - 验证 DNS 配置"
    echo "  $0 list     - 列出配置的域名"
    echo "  $0 help     - 显示帮助信息"
    echo ""
    echo "配置的域名:"
    for domain in "${DOMAINS[@]}"; do
        echo "  - $domain"
    done
}

# 列出域名
list_domains() {
    echo -e "${BLUE}📋 ANP SDK 配置的域名:${NC}"
    for domain in "${DOMAINS[@]}"; do
        echo -e "${GREEN}  ✓ $domain${NC}"
    done
    
    echo ""
    echo -e "${BLUE}🌐 测试 URL:${NC}"
    for domain in "${DOMAINS[@]}"; do
        echo -e "${YELLOW}  http://$domain:9527${NC}"
    done
}

# 主函数
main() {
    case "${1:-help}" in
        "setup")
            check_permissions "$@"
            add_domains
            echo ""
            echo -e "${BLUE}📋 后续步骤:${NC}"
            echo -e "${YELLOW}1. 启动 ANP SDK 服务: python -m anp_open_sdk_framework.server --host 0.0.0.0 --port 9527${NC}"
            echo -e "${YELLOW}2. 验证配置: $0 verify${NC}"
            echo -e "${YELLOW}3. 访问测试: curl http://user.localhost:9527/wba/user/test/did.json${NC}"
            ;;
        "remove")
            check_permissions "$@"
            remove_domains
            ;;
        "verify")
            verify_configuration
            ;;
        "list")
            list_domains
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# 执行主函数
main "$@"
