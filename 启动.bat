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

if "%MINIMAX_API_KEY%"=="" (
	for /f "usebackq delims=" %%A in (`powershell -NoProfile -Command "[Environment]::GetEnvironmentVariable('MINIMAX_API_KEY','User')"`) do set "MINIMAX_API_KEY=%%A"
)
if "%MINIMAX_API_KEY%"=="" (
	for /f "usebackq delims=" %%A in (`powershell -NoProfile -Command "[Environment]::GetEnvironmentVariable('MINIMAX_API_KEY','Machine')"`) do set "MINIMAX_API_KEY=%%A"
)
if "%MINIMAX_API_KEY%"=="" (
	echo.
	echo ╔════════════════════════════════════════════════════════════╗
	echo ║              未检测到环境变量 MINIMAX_API_KEY             ║
	echo ╚════════════════════════════════════════════════════════════╝
	echo.
	echo 请输入你的 MiniMax API 密钥:
	echo https://platform.minimaxi.com/user-center/basic-information/interface-key
	echo.
	set /p API_KEY="API Key: "
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

python --version >nul 2>&1
if errorlevel 1 (
	echo.
	echo [错误] 未检测到 Python，请先安装 Python 3.10+
	echo 下载地址: https://www.python.org/downloads/
	echo.
	pause
	exit /b 1
)

python -c "import fastapi, uvicorn, httpx, multipart" >nul 2>&1
if errorlevel 1 (
	echo.
	echo 检测到依赖缺失，正在安装 requirements.txt...
	echo.
	python -m pip install -r requirements.txt
	if errorlevel 1 (
		echo.
		echo [错误] 依赖安装失败，请检查网络连接。
		pause
		exit /b 1
	)
	echo. > .deps_installed
	echo 依赖安装完成！
	echo.
)

if not exist ".deps_installed" (
	echo. > .deps_installed
)

:header
cls
echo ╔════════════════════════════════════════════════════════════╗
echo ║ ❈ ✦ ❉ ✧ ❈ ✦ ❉ ✧ ❈ ✦ ❉ ✧ ❈ ✦ ❉ ✧ ❈ ✦ ❉ ✧ ❈ ✦ ❈ ✧ ❈ ✦ ❈ ✧ ❈  ║
echo ║ ❈ ✦ ❉ ✧ ❈ ✦ ❉ ✧ ❈ ✦ ❉ ✧ ❈ ✦ ❉ ✧ ❈ ✦ ❉ ✧ ❈ ✦ ❈ ✧ ❈ ✦ ❈ ✧ ❈  ║
echo ║                                                            ║
echo ║        ██╗  ██╗  ████╗  █████╗    ████╗  ███████╗          ║
echo ║        ██║ ██╔╝ ██╔═██╗ ██╔═██╗  ██╔═██╗ ██╔════╝          ║
echo ║        █████╔╝  ██████║ █████╔╝  ██████║ ███████╗          ║
echo ║        ██╔═██╗  ██╔═██║ ██╔═██╗  ██╔═██╗ ╚════██║          ║
echo ║        ██║  ██╗ ██║ ██║ ██║  ██║ ██║ ██║ ███████║          ║
echo ║        ╚═╝  ╚═╝ ╚═╝ ╚═╝ ╚═╝  ╚═╝ ╚═╝ ╚═╝ ╚══════╝          ║
echo ║                                                            ║
echo ║ ❈ ✦ ❉ ✧ ❈ ✦ ❉ ✧ ❈ ✦ ❉ ✧ ❈ ✦ ❉ ✧ ❈ ✦ ❉ ✧ ❈ ✦ ❉ ✧ ❈ ✦ ❈ ✧ ❈  ║
echo ║ ❈ ✦ ❉ ✧ ❈ ✦ ❉ ✧ ❈ ✦ ❉ ✧ ❈ ✦ ❉ ✧ ❈ ✦ ❉ ✧ ❈ ✦ ❉ ✧ ❈ ✦ ❈ ✧ ❈  ║
echo ╠════════════════════════════════════════════════════════════╣
echo ║                ⚛️⚛️【MiniMax Agent】⚛️⚛️                   ║
echo ╠════════════════════════════════════════════════════════════╣
echo ║                   🐉 多模态控制台 V1.0 🐉                  ║
echo ╚════════════════════════════════════════════════════════════╝

:menu
echo.
echo ╔══════════【 核心功能 】══════════╗
echo ║                                  ║
echo ║  [1] 🧠 文本对话     (AI Chat)   ║
echo ║  [2] 🎙️ 小说转语音   (TTS)       ║
echo ║  [3] 🎨 文生图       (T2I)       ║
echo ║  [4] 🖼️ 图生图       (I2I)       ║
echo ║                                  ║
echo ╠══════════【 音乐与创作 】════════╣
echo ║                                  ║
echo ║  [5] 🎵 音乐生成     (Music)     ║
echo ║  [6] 🎤 音乐翻唱     (Cover)     ║
echo ║  [7] ✍️ 歌词生成     (Lyrics)    ║
echo ║                                  ║
echo ╠══════════【 工具与扩展 】════════╣
echo ║                                  ║
echo ║  [8] 🔎 网络搜索     (Search)    ║
echo ║  [9] 👁️ 图片理解     (VLM)       ║
echo ║  [10] 🧩 官方 MCP 扩展           ║
echo ║  [11] 🧰 官方 Skills 技能包      ║
echo ║  [12] 🌐 网页控制台              ║
echo ║                                  ║
echo ╠══════════【 系统控制 】══════════╣
echo ║                                  ║
echo ║  [0] 🚪 退出程序     (Exit)      ║
echo ║                                  ║
echo ╚══════════════════════════════════╝
echo.
set /p opt="请输入编号并回车: "

if "%opt%"=="1" goto run_chat
if "%opt%"=="2" goto run_tts
if "%opt%"=="3" goto run_t2i
if "%opt%"=="4" goto run_i2i
if "%opt%"=="5" goto run_music
if "%opt%"=="6" goto run_cover
if "%opt%"=="7" goto run_lyrics
if "%opt%"=="8" goto run_search
if "%opt%"=="9" goto run_vlm
if "%opt%"=="10" goto run_mcp
if "%opt%"=="11" goto skills_menu
if "%opt%"=="12" goto run_web
if "%opt%"=="0" exit /b
echo ⚠️ 输入错误，请重新选择 (0-12)
timeout /t 2 >nul
goto header

:run_chat
echo.
python text_chat.py
set "LAST_ERROR=%ERRORLEVEL%"
goto end_action

:run_tts
echo.
python tts_novel.py
set "LAST_ERROR=%ERRORLEVEL%"
goto end_action

:run_t2i
echo.
python image_gen.py t2i
set "LAST_ERROR=%ERRORLEVEL%"
goto end_action

:run_i2i
echo.
python image_gen.py i2i
set "LAST_ERROR=%ERRORLEVEL%"
goto end_action

:run_music
echo.
python music_gen.py gen
set "LAST_ERROR=%ERRORLEVEL%"
goto end_action

:run_cover
echo.
python music_gen.py cover
set "LAST_ERROR=%ERRORLEVEL%"
goto end_action

:run_lyrics
echo.
python lyrics_gen.py
set "LAST_ERROR=%ERRORLEVEL%"
goto end_action

:run_search
echo.
python web_search.py
set "LAST_ERROR=%ERRORLEVEL%"
goto end_action

:run_vlm
echo.
python vlm_image.py
set "LAST_ERROR=%ERRORLEVEL%"
goto end_action

:run_mcp
echo.
python mcp_tools.py
set "LAST_ERROR=%ERRORLEVEL%"
goto end_action

:skills_menu
cls
echo ╔══════════【 MiniMax 官方 Skills 技能包 】══════════╗
echo ║                                                    ║
echo ║  [1]  frontend-dev                                ║
echo ║  [2]  fullstack-dev                               ║
echo ║  [3]  android-native-dev                          ║
echo ║  [4]  ios-application-dev                         ║
echo ║  [5]  flutter-dev                                 ║
echo ║  [6]  react-native-dev                            ║
echo ║  [7]  shader-dev                                  ║
echo ║  [8]  gif-sticker-maker                           ║
echo ║  [9]  minimax-pdf                                 ║
echo ║  [10] pptx-generator                              ║
echo ║  [11] minimax-xlsx                                ║
echo ║  [12] minimax-docx                                ║
echo ║  [13] vision-analysis                             ║
echo ║  [14] minimax-multimodal-toolkit                  ║
echo ║  [15] minimax-music-gen                           ║
echo ║  [16] buddy-sings                                 ║
echo ║  [17] minimax-music-playlist                      ║
echo ║                                                    ║
echo ║  [I]  接入说明                                    ║
echo ║  [0]  返回主菜单                                  ║
echo ║                                                    ║
echo ╚════════════════════════════════════════════════════╝
echo.
set /p skill_opt="请输入编号并回车: "

if /I "%skill_opt%"=="I" goto skills_info
if "%skill_opt%"=="1" set "SKILL_NAME=frontend-dev" & goto skills_show
if "%skill_opt%"=="2" set "SKILL_NAME=fullstack-dev" & goto skills_show
if "%skill_opt%"=="3" set "SKILL_NAME=android-native-dev" & goto skills_show
if "%skill_opt%"=="4" set "SKILL_NAME=ios-application-dev" & goto skills_show
if "%skill_opt%"=="5" set "SKILL_NAME=flutter-dev" & goto skills_show
if "%skill_opt%"=="6" set "SKILL_NAME=react-native-dev" & goto skills_show
if "%skill_opt%"=="7" set "SKILL_NAME=shader-dev" & goto skills_show
if "%skill_opt%"=="8" set "SKILL_NAME=gif-sticker-maker" & goto skills_show
if "%skill_opt%"=="9" set "SKILL_NAME=minimax-pdf" & goto skills_show
if "%skill_opt%"=="10" set "SKILL_NAME=pptx-generator" & goto skills_show
if "%skill_opt%"=="11" set "SKILL_NAME=minimax-xlsx" & goto skills_show
if "%skill_opt%"=="12" set "SKILL_NAME=minimax-docx" & goto skills_show
if "%skill_opt%"=="13" set "SKILL_NAME=vision-analysis" & goto skills_show
if "%skill_opt%"=="14" set "SKILL_NAME=minimax-multimodal-toolkit" & goto skills_show
if "%skill_opt%"=="15" set "SKILL_NAME=minimax-music-gen" & goto skills_show
if "%skill_opt%"=="16" set "SKILL_NAME=buddy-sings" & goto skills_show
if "%skill_opt%"=="17" set "SKILL_NAME=minimax-music-playlist" & goto skills_show
if "%skill_opt%"=="0" goto header
echo ⚠️ 输入错误，请重新选择 (0-17/I)
timeout /t 2 >nul
goto skills_menu

:skills_show
echo.
python skills_cli.py "%SKILL_NAME%"
set "LAST_ERROR=%ERRORLEVEL%"
goto end_skills_action

:skills_info
echo.
python skills_cli.py --install-info
set "LAST_ERROR=%ERRORLEVEL%"
goto end_skills_action

:run_web
echo.
echo 🌐 网页控制台启动后将自动打开 http://127.0.0.1:7860
echo 按 Ctrl+C 可停止服务。
echo.
start "" "http://127.0.0.1:7860"
python web_app.py
set "LAST_ERROR=%ERRORLEVEL%"
goto end_action

:end_skills_action
echo.
echo ---------------------------------------
if "%LAST_ERROR%"=="0" (
	echo [任务处理完成]
) else (
	echo [任务执行异常] 退出码: %LAST_ERROR%
)
set "LAST_ERROR="
echo 按任意键返回 Skills 菜单...
pause >nul
goto skills_menu

:end_action
echo.
echo ---------------------------------------
if "%LAST_ERROR%"=="0" (
	echo [任务处理完成]
) else (
	echo [任务执行异常] 退出码: %LAST_ERROR%
)
set "LAST_ERROR="
echo 按任意键返回主菜单...
pause >nul
goto header
