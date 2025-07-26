#!/bin/bash

# ANP Node.js SDK 测试演示脚本
# 展示改进后的测试报告功能

echo "🚀 ANP Node.js SDK 测试报告改进演示"
echo "═══════════════════════════════════════════════════════════════"

# 检查Python服务器状态
echo "🔍 检查Python服务器状态..."
if curl -s http://localhost:9527/ > /dev/null 2>&1; then
    echo "✅ Python服务器运行正常 (localhost:9527)"
    PYTHON_SERVER_RUNNING=true
else
    echo "⚠️  Python服务器未运行，跨语言测试将被跳过"
    echo "💡 启动命令: PYTHONPATH=\$PYTHONPATH:/path/to/anp-open-sdk-python python examples/flow_anp_agent/flow_anp_agent.py"
    PYTHON_SERVER_RUNNING=false
fi

echo ""
echo "📋 可用的测试命令:"
echo "  npm test                    # 运行所有测试（改进的报告格式）"
echo "  npm run test:verbose        # 详细模式"
echo "  npm run test:cross-lang     # 跨语言兼容性测试"
echo "  npm run test:foundation     # 基础功能测试"
echo "  npm run test:failed         # 只运行失败的测试"
echo "  npm run test:summary        # 简洁模式"

echo ""
echo "🎯 推荐的测试流程:"

if [ "$PYTHON_SERVER_RUNNING" = true ]; then
    echo "1️⃣  运行完整测试套件:"
    echo "   npm test"
    echo ""
    echo "2️⃣  如果有失败，查看详细信息:"
    echo "   npm run test:verbose"
    echo ""
    echo "3️⃣  针对性调试失败的测试:"
    echo "   npm run test:failed"
else
    echo "1️⃣  运行基础功能测试（无需Python服务器）:"
    echo "   npm run test:foundation"
    echo ""
    echo "2️⃣  启动Python服务器后运行完整测试:"
    echo "   npm test"
fi

echo ""
echo "🔧 调试特定测试:"
echo "   npm test -- --testNamePattern=\"测试名称\""
echo "   npm test tests/specific-file.test.ts"

echo ""
echo "📊 新的报告格式特性:"
echo "   ✅ 清晰的统计信息和成功率"
echo "   📋 按测试套件分组显示"
echo "   🔍 详细的错误信息和文件位置"
echo "   ⚡ 性能统计和慢速测试识别"
echo "   💡 智能修复建议"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "🎉 测试报告已优化！现在可以更清晰地查看测试结果了。"
echo ""

# 询问是否立即运行测试
read -p "是否现在运行测试演示？(y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 运行测试演示..."
    if [ "$PYTHON_SERVER_RUNNING" = true ]; then
        echo "运行跨语言兼容性测试..."
        npm run test:cross-lang
    else
        echo "运行基础功能测试..."
        npm run test:foundation
    fi
else
    echo "👋 稍后可以使用上述命令运行测试。"
fi