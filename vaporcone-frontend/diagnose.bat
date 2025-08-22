@echo off
:: VAPORCONE 停止脚本诊断工具
echo ===================================================================
echo                VAPORCONE 停止脚本诊断工具
echo ===================================================================
echo.

echo [1/6] 测试基本命令权限...
tasklist >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ tasklist 命令失败 - 可能需要管理员权限
    set ADMIN_REQUIRED=1
) else (
    echo ✅ tasklist 命令正常
)

netstat -ano >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ netstat 命令失败
) else (
    echo ✅ netstat 命令正常
)

echo.
echo [2/6] 测试编码设置...
chcp 65001 >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ UTF-8 编码设置失败
) else (
    echo ✅ UTF-8 编码设置成功
)

echo.
echo [3/6] 测试延迟扩展...
setlocal EnableDelayedExpansion
if %errorlevel% neq 0 (
    echo ❌ 延迟扩展启用失败
) else (
    echo ✅ 延迟扩展启用成功
)

echo.
echo [4/6] 检查运行环境...
echo 操作系统: %OS%
echo 处理器架构: %PROCESSOR_ARCHITECTURE%
echo 当前目录: %CD%
echo 脚本位置: %~dp0

echo.
echo [5/6] 检查端口占用...
echo 检查端口 3000:
netstat -ano | findstr ":3000" | findstr "LISTENING"
if %errorlevel% neq 0 (
    echo   端口 3000 未被占用
) else (
    echo   端口 3000 被占用
)

echo 检查端口 5000:
netstat -ano | findstr ":5000" | findstr "LISTENING"
if %errorlevel% neq 0 (
    echo   端口 5000 未被占用
) else (
    echo   端口 5000 被占用
)

echo.
echo [6/6] 检查相关进程...
echo Node.js 进程:
tasklist /fi "imagename eq node.exe" 2>nul | findstr /v "PID" | findstr /v "信息"
if %errorlevel% neq 0 echo   未找到 Node.js 进程

echo Python 进程:
tasklist /fi "imagename eq python.exe" 2>nul | findstr /v "PID" | findstr /v "信息"
if %errorlevel% neq 0 echo   未找到 Python 进程

echo.
echo ===================================================================
echo                           诊断结果
echo ===================================================================

if defined ADMIN_REQUIRED (
    echo ⚠️  建议以管理员身份运行脚本
    echo    右键点击 stop.bat → "以管理员身份运行"
)

echo.
echo 💡 如果 stop.bat 仍然有问题，请：
echo    1. 以管理员身份运行
echo    2. 检查防病毒软件是否阻止批处理文件
echo    3. 尝试在命令提示符中手动运行脚本
echo    4. 确保脚本文件编码为 ANSI 或 UTF-8
echo.

echo ===================================================================
echo 按任意键退出...
pause >nul
