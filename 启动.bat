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
    echo  [错误] 未检测到 Python，请先安装 Python 3.10+
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
echo  ║   10. 官方 MCP 扩展 (Video / Voice / Server) ║
echo  ║   11. 官方 Skills 技能包                     ║
echo  ║   12. 网页控制台    (Web Console)            ║
echo  ║                                              ║
echo  ║   0. 退出                                    ║
echo  ║                                              ║
echo  ╚══════════════════════════════════════════════╝
echo.
set /p "CHOICE=请选择功能 [0-12]: "

if "%CHOICE%"=="1" goto CHAT
if "%CHOICE%"=="2" goto TTS
if "%CHOICE%"=="3" goto T2I
if "%CHOICE%"=="4" goto I2I
if "%CHOICE%"=="5" goto MUSIC
if "%CHOICE%"=="6" goto COVER
if "%CHOICE%"=="7" goto LYRICS
if "%CHOICE%"=="8" goto SEARCH
if "%CHOICE%"=="9" goto VLM
if "%CHOICE%"=="10" goto MCP
if "%CHOICE%"=="11" goto SKILLS
if "%CHOICE%"=="12" goto WEB
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

:MCP
echo.
python mcp_tools.py
echo.
pause
goto MENU

:SKILLS
cls
echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║         MiniMax 官方 Skills 技能包           ║
echo  ╠══════════════════════════════════════════════╣
echo  ║   1. frontend-dev                           ║
echo  ║   2. fullstack-dev                          ║
echo  ║   3. android-native-dev                     ║
echo  ║   4. ios-application-dev                    ║
echo  ║   5. flutter-dev                            ║
echo  ║   6. react-native-dev                       ║
echo  ║   7. shader-dev                             ║
echo  ║   8. gif-sticker-maker                      ║
echo  ║   9. minimax-pdf                            ║
echo  ║   10. pptx-generator                        ║
echo  ║   11. minimax-xlsx                          ║
echo  ║   12. minimax-docx                          ║
echo  ║   13. vision-analysis                       ║
echo  ║   14. minimax-multimodal-toolkit            ║
echo  ║   15. minimax-music-gen                     ║
echo  ║   16. buddy-sings                           ║
echo  ║   17. minimax-music-playlist                ║
echo  ║                                              ║
echo  ║   I. 接入说明                               ║
echo  ║   0. 返回主菜单                             ║
echo  ╚══════════════════════════════════════════════╝
echo.
set /p "SKILL_CHOICE=请选择技能 [0-17/I]: "

if /I "%SKILL_CHOICE%"=="I" goto SKILLS_INFO
if "%SKILL_CHOICE%"=="1" set "SKILL_NAME=frontend-dev" & goto SKILLS_SHOW
if "%SKILL_CHOICE%"=="2" set "SKILL_NAME=fullstack-dev" & goto SKILLS_SHOW
if "%SKILL_CHOICE%"=="3" set "SKILL_NAME=android-native-dev" & goto SKILLS_SHOW
if "%SKILL_CHOICE%"=="4" set "SKILL_NAME=ios-application-dev" & goto SKILLS_SHOW
if "%SKILL_CHOICE%"=="5" set "SKILL_NAME=flutter-dev" & goto SKILLS_SHOW
if "%SKILL_CHOICE%"=="6" set "SKILL_NAME=react-native-dev" & goto SKILLS_SHOW
if "%SKILL_CHOICE%"=="7" set "SKILL_NAME=shader-dev" & goto SKILLS_SHOW
if "%SKILL_CHOICE%"=="8" set "SKILL_NAME=gif-sticker-maker" & goto SKILLS_SHOW
if "%SKILL_CHOICE%"=="9" set "SKILL_NAME=minimax-pdf" & goto SKILLS_SHOW
if "%SKILL_CHOICE%"=="10" set "SKILL_NAME=pptx-generator" & goto SKILLS_SHOW
if "%SKILL_CHOICE%"=="11" set "SKILL_NAME=minimax-xlsx" & goto SKILLS_SHOW
if "%SKILL_CHOICE%"=="12" set "SKILL_NAME=minimax-docx" & goto SKILLS_SHOW
if "%SKILL_CHOICE%"=="13" set "SKILL_NAME=vision-analysis" & goto SKILLS_SHOW
if "%SKILL_CHOICE%"=="14" set "SKILL_NAME=minimax-multimodal-toolkit" & goto SKILLS_SHOW
if "%SKILL_CHOICE%"=="15" set "SKILL_NAME=minimax-music-gen" & goto SKILLS_SHOW
if "%SKILL_CHOICE%"=="16" set "SKILL_NAME=buddy-sings" & goto SKILLS_SHOW
if "%SKILL_CHOICE%"=="17" set "SKILL_NAME=minimax-music-playlist" & goto SKILLS_SHOW
if "%SKILL_CHOICE%"=="0" goto MENU

echo 无效选择，请重新输入。
timeout /t 2 >nul
goto SKILLS

:SKILLS_SHOW
echo.
python skills_cli.py "%SKILL_NAME%"
echo.
pause
goto SKILLS

:SKILLS_INFO
echo.
python skills_cli.py --install-info
echo.
pause
goto SKILLS

:WEB
echo.
echo 网页控制台启动后将自动打开 http://127.0.0.1:7860
echo 按 Ctrl+C 可停止服务。
echo.
start "" "http://127.0.0.1:7860"
python web_app.py
echo.
pause
goto MENU

:EXIT
echo.
echo 感谢使用 MiniMax 专用小工具！
echo.
exit /b 0
