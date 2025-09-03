@echo off
chcp 65001 >nul
echo ========================================
echo VAPORCONE 增强版启动脚本
echo ========================================
echo.

echo 🚀 启动后端API服务器...
cd backend
start "VAPORCONE Backend" python app.py
cd ..

echo.
echo ⏳ 等待后端服务启动...
timeout /t 5 /nobreak >nul

echo.
echo 🌐 启动前端界面...
start "VAPORCONE Frontend" npm start

echo.
echo ✅ 启动完成！
echo.
echo 📊 后端API: http://localhost:5000
echo 📊 API文档: http://localhost:5000/api/docs/
echo 🌐 前端界面: http://localhost:3000
echo.
echo 💡 提示：
echo    - 确保Python环境已配置
echo    - 确保已安装所需依赖: pip install -r requirements.txt
echo    - 确保前端依赖已安装: npm install
echo.
echo 🔍 监控日志文件: backend/logs/
echo.
pause
