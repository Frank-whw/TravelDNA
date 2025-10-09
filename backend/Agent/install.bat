@echo off
chcp 65001 >nul
echo ========================================
echo 智能旅游规划Agent - 安装脚本
echo ========================================
echo.

echo [1/4] 检查Python环境...
python --version
if errorlevel 1 (
    echo ❌ 未检测到Python，请先安装Python 3.8+
    pause
    exit /b 1
)
echo ✅ Python环境检测成功
echo.

echo [2/4] 安装依赖包...
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ 依赖安装失败
    pause
    exit /b 1
)
echo ✅ 依赖安装成功
echo.

echo [3/4] 检查配置文件...
if not exist .env (
    echo 📝 未检测到.env文件，正在复制示例文件...
    copy .env.example .env
    echo ⚠️  请编辑 .env 文件，填入你的API密钥
) else (
    echo ✅ .env文件已存在
)
echo.

echo [4/4] 测试Agent...
python -c "from enhanced_travel_agent import EnhancedTravelAgent; print('✅ Agent导入成功')"
if errorlevel 1 (
    echo ❌ Agent测试失败
    pause
    exit /b 1
)
echo.

echo ========================================
echo ✅ 安装完成！
echo ========================================
echo.
echo 使用方法：
echo   1. 编辑 .env 文件，填入API密钥
echo   2. 运行：python quick_start.py
echo   3. 或运行：python enhanced_travel_agent.py
echo.
echo 文档：
echo   - README.md - 完整使用说明
echo   - THOUGHT_CHAIN_SYSTEM.md - 系统架构文档
echo   - INPUTTIPS_API_README.md - 输入提示API说明
echo.
pause

