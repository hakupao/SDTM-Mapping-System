@echo off
chcp 65001 >nul
echo.
echo ====================================================
echo   VAPORCONE 重构版后端API服务器启动脚本 (增强版)
echo ====================================================
echo.

echo 📁 当前目录: %CD%
echo 📋 项目结构检查...

REM 检查项目结构
if not exist app.py (
    echo ❌ 错误: 未找到app_new.py主文件
    echo 💡 请确保在正确的backend目录下运行此脚本
    pause
    exit /b 1
)

if not exist api\ (
    echo ❌ 错误: 未找到api目录
    echo 💡 请确保重构架构文件完整
    pause
    exit /b 1
)

if not exist services\ (
    echo ❌ 错误: 未找到services目录
    echo 💡 请确保重构架构文件完整
    pause
    exit /b 1
)

echo ✅ 项目结构检查通过
echo.

REM 检查Python环境
echo 🐍 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到Python环境
    echo 💡 请确保Python已安装并添加到PATH环境变量
    pause
    exit /b 1
)

python --version
echo ✅ Python环境检查通过
echo.

REM 检查依赖文件路径
echo 📦 检查依赖文件...
if not exist ..\..\requirements.txt (
    echo ❌ 错误: 未找到requirements.txt文件
    echo 💡 预期路径: %CD%\..\..\requirements.txt
    echo 💡 请确保requirements.txt在项目根目录下
    echo.
    echo 📁 当前目录结构应为:
    echo    SDTM\
    echo    ├── requirements.txt          ^<-- 应该在这里
    echo    └── vaporcone-frontend\
    echo        └── backend\              ^<-- 您在这里
    echo            └── start_enhanced.bat
    pause
    exit /b 1
)

echo ✅ 找到依赖文件: ..\..\requirements.txt
echo.

REM 安装依赖
echo 📦 安装/更新依赖包...
echo 💡 正在执行: pip install -r ..\..\requirements.txt
pip install -r ..\..\requirements.txt
if errorlevel 1 (
    echo ❌ 依赖包安装失败
    echo 💡 请检查网络连接或使用国内镜像源
    echo 💡 例如: pip install -r ..\..\requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
    pause
    exit /b 1
)

echo ✅ 依赖包安装完成
echo.

REM 运行架构测试
echo 🧪 运行架构测试...
echo 💡 这将验证所有模块是否正常工作
python test_new_architecture.py
if errorlevel 1 (
    echo ❌ 架构测试失败
    echo 💡 请检查错误信息并修复相关问题
    pause
    exit /b 1
)

echo ✅ 架构测试通过
echo.

REM 启动服务器
echo 🚀 启动VAPORCONE重构版API服务器...
echo.
echo 📊 服务信息:
echo    - 主页面: http://localhost:5000/
echo    - API文档: http://localhost:5000/api/docs/
echo    - 健康检查: http://localhost:5000/health
echo    - 系统状态: http://localhost:5000/api/system/status
echo    - WebSocket: ws://localhost:5000
echo.
echo 💡 启动后请在浏览器中访问 http://localhost:5000/api/docs/ 查看API文档
echo 💡 按 Ctrl+C 停止服务器
echo.
echo ====================================================
echo   服务器启动中...
echo ====================================================

python app.py

echo.
echo 👋 服务器已停止
echo ====================================================
pause
