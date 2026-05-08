@echo off
if "%~1"=="utf8" goto main
chcp 65001 >nul
cmd /c "%~f0" utf8
exit /b

:main
setlocal EnableExtensions DisableDelayedExpansion
color 0B
title MiniMax 专用小工具 v1.0
cd /d "%~dp0"
set "PYTHONPATH=%~dp0"

:: ============================================================
:: 检查 MINIMAX_API_KEY
:: ============================================================
if "%MINIMAX_API_KEY%"=="" (
    echo.
    echo  ╔═══════════════════════════════════════════════════════╗
    echo  ║  未检测到环境变量 MINIMAX_API_KEY                    ║
    echo  ╚═══════════════════════════════════════════════════════╝
    echo.
    echo  请输入你的 MiniMax API 密钥（可在以下地址获取）：
    echo  https://platform.minimaxi.com/user-center/basic-information/interface-key
    echo.
    set /p "API_KEY=API Key: "
    if "%API_KEY%"=="" (
        echo 未输入密钥，退出。
        pause
        exit /b 1
    )
    echo.
    echo 正在设置环境变量...
    setx MINIMAX_API_KEY "%API_KEY%" >nul 2>&1
    set "MINIMAX_API_KEY=%API_KEY%"
    echo 已设置 MINIMAX_API_KEY 到用户环境变量。
    echo 注意：新开的终端窗口将自动生效。
    echo.
    pause
)

:: ============================================================
:: 检查 Python
:: ============================================================
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  [错误] 未检测到 Python，请先安装 Python 3.8+
    echo  下载地址: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

:: ============================================================
:: 首次运行安装依赖
:: ============================================================
if not exist ".deps_installed" (
    echo.
    echo  首次运行，正在安装依赖...
    echo.
    pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo  [错误] 依赖安装失败，请检查网络连接。
        pause
        exit /b 1
    )
    echo. > .deps_installed
    echo  依赖安装完成！
    echo.
)

:: ============================================================
:: 主菜单
:: ============================================================
:MENU
cls
echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║         MiniMax 专用小工具 v1.0              ║
echo  ╠══════════════════════════════════════════════╣
echo  ║                                              ║
echo  ║   1. 文本对话      (AI Chat)                 ║
echo  ║   2. 小说转语音    (Novel → Audio)           ║
echo  ║   3. 文生图        (Text → Image)            ║
echo  ║   4. 图生图        (Image → Image)           ║
echo  ║   5. 音乐生成      (Music Generation)        ║
echo  ║   6. 音乐翻唱      (Music Cover)             ║
echo  ║   7. 歌词生成      (Lyrics Generation)       ║
echo  ║   8. 网络搜索      (Web Search)              ║
echo  ║   9. 图片理解      (VLM)                     ║
echo  ║                                              ║
echo  ║   0. 退出                                    ║
echo  ║                                              ║
echo  ╚══════════════════════════════════════════════╝
echo.
set /p "CHOICE=请选择功能 [0-9]: "

if "%CHOICE%"=="1" goto CHAT
if "%CHOICE%"=="2" goto TTS
if "%CHOICE%"=="3" goto T2I
if "%CHOICE%"=="4" goto I2I
if "%CHOICE%"=="5" goto MUSIC
if "%CHOICE%"=="6" goto COVER
if "%CHOICE%"=="7" goto LYRICS
if "%CHOICE%"=="8" goto SEARCH
if "%CHOICE%"=="9" goto VLM
if "%CHOICE%"=="0" goto EXIT

echo 无效选择，请重新输入。
timeout /t 2 >nul
goto MENU

:: ============================================================
:: 功能调用
:: ============================================================

:CHAT
echo.
python text_chat.py
echo.
pause
goto MENU

:TTS
echo.
python tts_novel.py
echo.
pause
goto MENU

:T2I
echo.
python image_gen.py t2i
echo.
pause
goto MENU

:I2I
echo.
python image_gen.py i2i
echo.
pause
goto MENU

:MUSIC
echo.
python music_gen.py gen
echo.
pause
goto MENU

:COVER
echo.
python music_gen.py cover
echo.
pause
goto MENU

:LYRICS
echo.
python lyrics_gen.py
echo.
pause
goto MENU

:SEARCH
echo.
python web_search.py
echo.
pause
goto MENU

:VLM
echo.
python vlm_image.py
echo.
pause
goto MENU

:EXIT
echo.
echo 感谢使用 MiniMax 专用小工具！
echo.
exit /b 0
