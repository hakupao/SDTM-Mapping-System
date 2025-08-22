@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

:: 确保脚本在正确的目录下运行
cd /d "%~dp0"

echo.
echo ===================================================================
echo                    VAPORCONE 数据处理平台启动脚本
echo ===================================================================
echo.

:: 设置颜色
set "green=[92m"
set "red=[91m"
set "yellow=[93m"
set "blue=[94m"
set "reset=[0m"

:: 记录开始时间
set start_time=%time%

echo %blue%脚本位置: %~dp0%reset%
echo %blue%当前工作目录: %cd%%reset%

:: 检查当前目录
if not exist "package.json" (
    echo %red%错误：请在 vaporcone-frontend 目录下运行此脚本！%reset%
    echo %red%当前目录: %cd%%reset%
    pause
    exit /b 1
)

echo %blue%[1/7] 检查环境依赖...%reset%

:: 检查Node.js
node --version >nul 2>&1
if !errorlevel! neq 0 (
    echo %red%❌ Node.js 未安装或未添加到PATH！%reset%
    echo    请访问 https://nodejs.org 下载并安装 Node.js 16.0 或更高版本
    pause
    exit /b 1
) else (
    for /f "tokens=*" %%i in ('node --version') do set node_version=%%i
    echo %green%✅ Node.js !node_version! 已安装%reset%
)

:: 检查Python
python --version >nul 2>&1
if !errorlevel! neq 0 (
    echo %red%❌ Python 未安装或未添加到PATH！%reset%
    echo    请访问 https://python.org 下载并安装 Python 3.8 或更高版本
    pause
    exit /b 1
) else (
    for /f "tokens=*" %%i in ('python --version') do set python_version=%%i
    echo %green%✅ !python_version! 已安装%reset%
)

echo %blue%[2/7] 检查端口占用...%reset%

:: 检查并清理端口3000
netstat -ano | findstr ":3000 " >nul 2>&1
if !errorlevel! equ 0 (
    echo %yellow%⚠️  端口 3000 已被占用，尝试终止占用进程...%reset%
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3000 "') do (
        taskkill /pid %%a /f >nul 2>&1
    )
)

:: 检查并清理端口5000
netstat -ano | findstr ":5000 " >nul 2>&1
if !errorlevel! equ 0 (
    echo %yellow%⚠️  端口 5000 已被占用，尝试终止占用进程...%reset%
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5000 "') do (
        taskkill /pid %%a /f >nul 2>&1
    )
)

echo %green%✅ 端口检查完成%reset%

echo %blue%[3/7] 安装前端依赖...%reset%

:: 检查和安装前端依赖（这可能是关键步骤）
if not exist "node_modules" (
    echo %yellow%📦 正在安装前端依赖包...%reset%
    call npm install
    if !errorlevel! neq 0 (
        echo %red%❌ 前端依赖安装失败！%reset%
        echo    请检查网络连接或尝试：npm cache clean --force
        pause
        exit /b 1
    )
    echo %green%✅ 前端依赖安装完成%reset%
) else (
    echo %green%✅ 前端依赖已存在%reset%
    :: 验证关键依赖
    if not exist "node_modules\react-scripts" (
        echo %yellow%⚠️  关键依赖缺失，重新安装...%reset%
        call npm install
    )
)

echo %blue%[4/7] 配置后端环境...%reset%

:: 检查后端目录
if not exist "backend" (
    echo %red%❌ backend 目录不存在！%reset%
    pause
    exit /b 1
)

cd backend

:: 检查虚拟环境并激活
if exist "..\..\.venv\Scripts\activate.bat" (
    echo %green%✅ 发现根目录虚拟环境%reset%
    call "..\..\.venv\Scripts\activate.bat" 2>nul
    if defined VIRTUAL_ENV (
        echo %green%✅ 虚拟环境激活成功: %VIRTUAL_ENV%%reset%
    ) else (
        echo %yellow%⚠️  虚拟环境激活可能失败%reset%
    )
) else (
    echo %yellow%⚠️  未找到根目录虚拟环境%reset%
)

:: 安装后端依赖
if exist "..\..\requirements.txt" (
    echo %yellow%📦 检查Python依赖...%reset%
    pip install -r ..\..\requirements.txt >nul 2>&1
) else (
    echo %yellow%⚠️  未找到requirements.txt%reset%
)

echo %green%✅ 后端环境配置完成%reset%
cd ..

echo %blue%[5/7] 检查VAPORCONE核心模块...%reset%

if exist "..\VC_BC01_constant.py" (
    echo %green%✅ VAPORCONE核心模块已找到%reset%
) else (
    echo %red%❌ VAPORCONE核心模块未找到%reset%
    echo %yellow%⚠️  系统可能无法正常工作，但将继续启动...%reset%
)

echo %blue%[6/7] 启动后端API服务器...%reset%

:: 启动后端
cd backend
echo %blue%正在启动后端API服务器...%reset%
start "VAPORCONE 后端API" cmd /k "title VAPORCONE后端API && echo 启动后端服务器... && python app.py"

:: 等待后端启动
echo %yellow%⏳ 等待后端服务器启动...%reset%
timeout /t 5 /nobreak >nul

:: 验证后端启动
echo %blue%检查后端状态...%reset%
cd ..

echo %blue%[7/7] 启动前端开发服务器...%reset%

:: 启动前端（内嵌逻辑）
echo %blue%正在启动React开发服务器...%reset%

:: 创建临时前端启动脚本
echo @echo off > temp_start_frontend.bat
echo chcp 65001 ^>nul >> temp_start_frontend.bat
echo title VAPORCONE前端服务器 >> temp_start_frontend.bat
echo cd /d "%cd%" >> temp_start_frontend.bat
echo echo 启动React开发服务器... >> temp_start_frontend.bat
echo echo 当前目录: %%cd%% >> temp_start_frontend.bat
echo npm start >> temp_start_frontend.bat
echo pause >> temp_start_frontend.bat

:: 启动前端服务器
start "VAPORCONE 前端" cmd /k temp_start_frontend.bat

:: 清理临时文件（延迟删除）
timeout /t 2 /nobreak >nul
del temp_start_frontend.bat >nul 2>&1

:: 等待前端启动
echo %yellow%⏳ 等待前端服务器启动...%reset%
timeout /t 5 /nobreak >nul

:: 计算启动时间
set end_time=%time%

echo.
echo ===================================================================
echo                          🎉 启动完成！
echo ===================================================================
echo.
echo %green%✅ 后端API服务器：%reset% http://localhost:5000
echo %green%✅ 前端Web界面：%reset%  http://localhost:3000
echo.
echo %yellow%📋 下一步操作：%reset%
echo    1. 浏览器将自动打开 http://localhost:3000
echo    2. 在系统中选择要处理的研究 (CIRCULATE、GOZILA等)
echo    3. 检查系统状态和数据库连接
echo    4. 开始使用VAPORCONE数据处理功能
echo.
echo %yellow%🛑 停止服务：%reset%
echo    运行 stop.bat 或 stop_enhanced.bat 来停止所有服务
echo.
echo %blue%📝 注意事项：%reset%
echo    - 🗄️ 确保MySQL数据库服务正在运行
echo    - 🔧 检查数据库连接配置 (VC_BC01_constant.py)
echo    - 📊 确保研究配置文件 (*.xlsx) 存在于正确位置
echo    - 🛠️ 确保所有VAPORCONE核心模块完整可用
echo    - ⚠️  系统仅支持真实数据模式，所有组件缺一不可
echo.
echo ===================================================================

:: 自动打开浏览器
timeout /t 3 /nobreak >nul
start http://localhost:3000

echo %green%启动脚本执行完成！服务正在后台运行...%reset%
echo 按任意键关闭此窗口（不会停止服务）
pause >nul