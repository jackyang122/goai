@echo off
REM ============================================
REM DeepTutor 启动脚本 (Windows)
REM ============================================

cd /d "%~dp0"

REM 设置默认端口
if "%DEEPTUTOR_PORT%"=="" set DEEPTUTOR_PORT=8003

REM 检查虚拟环境
if exist ".venv\Scripts\python.exe" (
    set PYTHON=.venv\Scripts\python.exe
) else if exist ".venv\bin\python" (
    set PYTHON=.venv\bin\python
) else (
    echo 错误: 未找到虚拟环境，请先创建虚拟环境
    exit /b 1
)

echo ==========================================
echo 启动 DeepTutor 服务
echo ==========================================
echo 端口: %DEEPTUTOR_PORT%
echo 工作目录: %CD%
echo Python: %PYTHON%
echo ==========================================

REM 加载环境变量
if exist ".env" (
    for /f "tokens=*" %%a in ('type .env ^| findstr /v "^#" ^| findstr /v "^$"') do set %%a
)

REM 启动服务
%PYTHON% -m deeptutor serve --host 0.0.0.0 --port %DEEPTUTOR_PORT% --reload
