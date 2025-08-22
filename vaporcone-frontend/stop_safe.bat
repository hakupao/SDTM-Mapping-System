@echo off
:: VAPORCONE 安全停止脚本 (防闪退版本)
setlocal EnableDelayedExpansion

echo ===================================================================
echo                    VAPORCONE 安全停止脚本
echo ===================================================================
echo.

echo [1/4] 检查服务状态...
echo.

:: 检查前端服务
echo 检查前端服务 (端口 3000)...
netstat -ano | findstr ":3000" | findstr "LISTENING" >nul 2>&1
if !errorlevel! equ 0 (
    echo   ✅ 发现前端服务正在运行
    set "frontend_found=true"
) else (
    echo   ℹ️  前端服务未运行
    set "frontend_found=false"
)

:: 检查后端服务
echo 检查后端服务 (端口 5000)...
netstat -ano | findstr ":5000" | findstr "LISTENING" >nul 2>&1
if !errorlevel! equ 0 (
    echo   ✅ 发现后端服务正在运行
    set "backend_found=true"
) else (
    echo   ℹ️  后端服务未运行
    set "backend_found=false"
)

echo.
echo [2/4] 选择停止方式...
echo.

if "!frontend_found!"=="false" if "!backend_found!"=="false" (
    echo 未发现运行中的服务，系统已处于停止状态
    goto end_script
)

echo 发现运行中的服务，请选择停止方式：
echo [1] 智能停止 - 仅停止VAPORCONE相关端口的进程 (推荐)
echo [2] 强制停止 - 停止所有Node.js和Python进程
echo [3] 快速停止 - 直接停止，无确认
echo [0] 取消
echo.
set /p choice=请输入选择 [1-3, 0]: 

if "%choice%"=="0" goto end_script
if "%choice%"=="2" goto force_stop
if "%choice%"=="3" goto quick_stop

echo.
echo [3/4] 安全停止服务...

:: 安全停止 - 根据端口找到具体进程
if "!frontend_found!"=="true" (
    echo 正在停止前端服务...
    for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":3000" ^| findstr "LISTENING"') do (
        echo   停止进程 %%p
        taskkill /pid %%p /f >nul 2>&1
    )
)

if "!backend_found!"=="true" (
    echo 正在停止后端服务...
    for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":5000" ^| findstr "LISTENING"') do (
        echo   停止进程 %%p
        taskkill /pid %%p /f >nul 2>&1
    )
)

goto verify_stop

:quick_stop
echo.
echo [3/4] 快速停止服务...
echo 正在快速停止所有相关进程...
taskkill /f /im node.exe >nul 2>&1
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im npm.exe >nul 2>&1
taskkill /f /im yarn.exe >nul 2>&1
echo ✅ 快速停止完成
goto verify_stop

:force_stop
echo.
echo [3/4] 强制停止所有相关进程...
echo 警告：这将停止所有Node.js和Python进程！
set /p confirm=确认继续? (y/N): 
if /i not "%confirm%"=="y" goto end_script

echo 强制停止Node.js进程...
taskkill /f /im node.exe >nul 2>&1
echo 强制停止Python进程...
taskkill /f /im python.exe >nul 2>&1
echo 强制停止其他相关进程...
taskkill /f /im npm.exe >nul 2>&1
taskkill /f /im yarn.exe >nul 2>&1

:verify_stop
echo.
echo [4/4] 验证停止结果...
timeout /t 2 /nobreak >nul

netstat -ano | findstr ":3000" | findstr "LISTENING" >nul 2>&1
if !errorlevel! equ 0 (
    echo ⚠️  端口 3000 仍被占用
    set "stop_success=false"
) else (
    echo ✅ 端口 3000 已释放
)

netstat -ano | findstr ":5000" | findstr "LISTENING" >nul 2>&1
if !errorlevel! equ 0 (
    echo ⚠️  端口 5000 仍被占用
    set "stop_success=false"
) else (
    echo ✅ 端口 5000 已释放
)

echo.
if "!stop_success!"=="false" (
    echo ⚠️  部分服务可能仍在运行，建议：
    echo    1. 检查任务管理器
    echo    2. 重启计算机
    echo    3. 使用强制停止选项
) else (
    echo 🎉 所有VAPORCONE服务已成功停止！
)

:end_script
echo.
echo ===================================================================
echo 按任意键退出...
pause >nul
exit /b 0
