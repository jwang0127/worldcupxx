@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

rem 一键安装 Windows 任务计划程序
rem 默认根目录为 D:\WorldCupPredict
rem 如需自定义，可执行：install_scheduler.bat D:\你的目录

set "ROOT_DIR=%~1"
if "%ROOT_DIR%"=="" set "ROOT_DIR=D:\WorldCupPredict"

set "SCRIPTS_DIR=%ROOT_DIR%\scripts"
set "LOG_DIR=%ROOT_DIR%\logs"
set "OUTPUT_DIR=%ROOT_DIR%\output"
set "DATA_DIR=%ROOT_DIR%\data"

if not exist "%ROOT_DIR%" mkdir "%ROOT_DIR%"
if not exist "%SCRIPTS_DIR%" mkdir "%SCRIPTS_DIR%"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"
if not exist "%DATA_DIR%" mkdir "%DATA_DIR%"

set "PYTHON_EXE="
set "PYTHON_CMD="

where python >nul 2>nul
if %errorlevel%==0 (
    for /f "delims=" %%i in ('where python') do (
        set "PYTHON_EXE=%%i"
        set "PYTHON_CMD=\"%%i\""
        goto :python_found
    )
)

where py >nul 2>nul
if %errorlevel%==0 (
    set "PYTHON_EXE=py -3"
    set "PYTHON_CMD=py -3"
    goto :python_found
)

if exist "C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" (
    set "PYTHON_EXE=C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
    set "PYTHON_CMD=\"C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe\""
    goto :python_found
)

echo [错误] 未检测到 Python，请先安装 Python 3.9+ 并加入 PATH。
exit /b 1

:python_found
echo [信息] 使用 Python：%PYTHON_EXE%
echo [信息] 根目录：%ROOT_DIR%

set "TASK_FETCH=WorldCupPredict_FetchResults"
set "TASK_REVIEW=WorldCupPredict_ReviewYesterday"
set "TASK_ANALYZE=WorldCupPredict_AnalyzeToday"

set "CMD_FETCH=cmd.exe /c cd /d \"%SCRIPTS_DIR%\" ^&^& %PYTHON_CMD% fetch_results.py --root \"%ROOT_DIR%\" >> \"%LOG_DIR%\task_fetch.log\" 2^>^&1"
set "CMD_REVIEW=cmd.exe /c cd /d \"%SCRIPTS_DIR%\" ^&^& %PYTHON_CMD% review_yesterday.py --root \"%ROOT_DIR%\" >> \"%LOG_DIR%\task_review.log\" 2^>^&1"
set "CMD_ANALYZE=cmd.exe /c cd /d \"%SCRIPTS_DIR%\" ^&^& %PYTHON_CMD% analyze_today.py --root \"%ROOT_DIR%\" >> \"%LOG_DIR%\task_analyze.log\" 2^>^&1"

schtasks /create /f /tn "%TASK_FETCH%" /sc daily /st 14:00 /tr "%CMD_FETCH%" >nul
if errorlevel 1 (
    echo [错误] 创建任务 %TASK_FETCH% 失败。
    exit /b 1
)

schtasks /create /f /tn "%TASK_REVIEW%" /sc daily /st 14:05 /tr "%CMD_REVIEW%" >nul
if errorlevel 1 (
    echo [错误] 创建任务 %TASK_REVIEW% 失败。
    exit /b 1
)

schtasks /create /f /tn "%TASK_ANALYZE%" /sc daily /st 09:00 /tr "%CMD_ANALYZE%" >nul
if errorlevel 1 (
    echo [错误] 创建任务 %TASK_ANALYZE% 失败。
    exit /b 1
)

echo [成功] 任务计划已创建完成。
echo.
echo 任务 A：%TASK_FETCH%  -> 每天 14:00 抓取今日赛果
echo 任务 B：%TASK_REVIEW% -> 每天 14:05 生成昨日复盘
echo 任务 C：%TASK_ANALYZE% -> 每天 09:00 生成今日预测
echo.
echo 如需删除任务，可执行：
echo schtasks /delete /f /tn "%TASK_FETCH%"
echo schtasks /delete /f /tn "%TASK_REVIEW%"
echo schtasks /delete /f /tn "%TASK_ANALYZE%"

endlocal
