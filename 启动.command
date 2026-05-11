#!/usr/bin/env bash
set -u

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR" || exit 1
export PYTHONPATH="$SCRIPT_DIR${PYTHONPATH:+:$PYTHONPATH}"
VENV_DIR="$SCRIPT_DIR/.venv"

trim_value() {
  local value="$1"
  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  if [[ "$value" == \"*\" && "$value" == *\" ]]; then
    value="${value:1:${#value}-2}"
  elif [[ "$value" == \'*\' && "$value" == *\' ]]; then
    value="${value:1:${#value}-2}"
  fi
  printf '%s' "$value"
}

read_env_var_from_file() {
  local var_name="$1"
  local file_path="$2"
  local line key value

  [[ -f "$file_path" ]] || return 1

  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line#"${line%%[![:space:]]*}"}"
    [[ -z "$line" || "$line" == \#* ]] && continue
    line="${line#export }"
    [[ "$line" == *"="* ]] || continue
    key="${line%%=*}"
    key="$(trim_value "$key")"
    [[ "$key" == "$var_name" ]] || continue
    value="${line#*=}"
    trim_value "$value"
    return 0
  done < "$file_path"

  return 1
}

load_saved_environment() {
  local files=(
    "$SCRIPT_DIR/.env"
    "$HOME/.zshenv"
    "$HOME/.zprofile"
    "$HOME/.zshrc"
    "$HOME/.bash_profile"
    "$HOME/.bashrc"
  )
  local vars=(MINIMAX_API_KEY MINIMAX_MCP_API_HOST MINIMAX_API_HOST)
  local var_name file_path value

  for var_name in "${vars[@]}"; do
    [[ -n "${!var_name-}" ]] && continue
    for file_path in "${files[@]}"; do
      if value="$(read_env_var_from_file "$var_name" "$file_path")"; then
        export "$var_name=$value"
        break
      fi
    done
  done
}

pause() {
  echo
  read -r -p "按回车继续..."
}

find_python() {
  if [[ -x "$VENV_DIR/bin/python" ]]; then
    printf '%s\n' "$VENV_DIR/bin/python"
    return 0
  fi
  if command -v python3 >/dev/null 2>&1; then
    command -v python3
    return 0
  fi
  if command -v python >/dev/null 2>&1; then
    command -v python
    return 0
  fi
  return 1
}

ensure_api_key() {
  if [[ -n "${MINIMAX_API_KEY:-}" ]]; then
    return 0
  fi

  clear
  cat <<'EOF'
╔════════════════════════════════════════════════════════════╗
║              未检测到环境变量 MINIMAX_API_KEY             ║
╚════════════════════════════════════════════════════════════╝

请输入你的 MiniMax API 密钥:
https://platform.minimaxi.com/user-center/basic-information/interface-key
EOF
  echo
  read -r -s -p "API Key: " API_KEY
  echo
  if [[ -z "$API_KEY" ]]; then
    echo "未输入密钥，退出。"
    pause
    exit 1
  fi

  export MINIMAX_API_KEY="$API_KEY"
  echo
  read -r -p "是否写入项目 .env，供以后双击启动器自动读取？[Y/n]: " SAVE_KEY
  if [[ ! "$SAVE_KEY" =~ ^[Nn]$ ]]; then
    {
      echo
      echo "# MiniMax tools"
      echo "export MINIMAX_API_KEY=\"$API_KEY\""
      echo "export MINIMAX_MCP_API_HOST=\"${MINIMAX_MCP_API_HOST}\""
    } >> "$SCRIPT_DIR/.env"
    echo "已写入项目 .env。下次双击启动器会自动读取。"
  else
    echo "已在当前启动器会话中临时设置 MINIMAX_API_KEY。"
  fi
  pause
}

ensure_python() {
  PYTHON_BIN="$(find_python || true)"
  if [[ -z "${PYTHON_BIN:-}" ]]; then
    echo
    echo "[错误] 未检测到 Python，请先安装 Python 3.10+"
    echo "下载地址: https://www.python.org/downloads/"
    pause
    exit 1
  fi

  if [[ "$PYTHON_BIN" == "$VENV_DIR/bin/python" ]]; then
    export VIRTUAL_ENV="$VENV_DIR"
    export PATH="$VENV_DIR/bin:$PATH"
  fi

  if ! "$PYTHON_BIN" - <<'PY' >/dev/null 2>&1
import sys
raise SystemExit(0 if sys.version_info >= (3, 10) else 1)
PY
  then
    echo
    echo "[错误] Python 版本过低，请安装 Python 3.10+"
    "$PYTHON_BIN" --version
    pause
    exit 1
  fi
}

ensure_deps() {
  if "$PYTHON_BIN" - <<'PY' >/dev/null 2>&1
import fastapi
import uvicorn
import httpx
import multipart
PY
  then
    [[ -f ".deps_installed" ]] || : > ".deps_installed"
    return 0
  fi

  echo
  echo "检测到依赖缺失，正在安装 requirements.txt..."
  echo
  if ! "$PYTHON_BIN" -m pip install -r requirements.txt; then
    echo
    echo "[错误] 依赖安装失败，请检查网络连接。"
    pause
    exit 1
  fi
  : > ".deps_installed"
  echo
  echo "依赖安装完成！"
  pause
}

open_url() {
  local url="$1"
  if command -v open >/dev/null 2>&1; then
    open "$url" >/dev/null 2>&1
  elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$url" >/dev/null 2>&1
  fi
}

end_action() {
  local code="$1"
  echo
  echo "---------------------------------------"
  if [[ "$code" == "0" ]]; then
    echo "[任务处理完成]"
  else
    echo "[任务执行异常] 退出码: $code"
  fi
  pause
}

run_python() {
  echo
  "$PYTHON_BIN" "$@"
  end_action "$?"
}

run_web_console() {
  echo
  echo "🌐 网页控制台启动后将自动打开 http://127.0.0.1:7860"
  echo "按 Ctrl+C 可停止服务。"
  echo
  (sleep 1.5; open_url "http://127.0.0.1:7860") &
  "$PYTHON_BIN" web_app.py
  end_action "$?"
}

show_header() {
  clear
  cat <<'EOF'
╔════════════════════════════════════════════════════════════╗
║ ❈ ✦ ❉ ✧ ❈ ✦ ❉ ✧ ❈ ✦ ❉ ✧ ❈ ✦ ❉ ✧ ❈ ✦ ❉ ✧ ❈ ✦ ❈ ✧ ❈ ✦ ❈ ✧ ❈  ║
║ ❈ ✦ ❉ ✧ ❈ ✦ ❉ ✧ ❈ ✦ ❉ ✧ ❈ ✦ ❉ ✧ ❈ ✦ ❉ ✧ ❈ ✦ ❈ ✧ ❈ ✦ ❈ ✧ ❈  ║
║                                                            ║
║        ██╗  ██╗  ████╗  █████╗    ████╗  ███████╗          ║
║        ██║ ██╔╝ ██╔═██╗ ██╔═██╗  ██╔═██╗ ██╔════╝          ║
║        █████╔╝  ██████║ █████╔╝  ██████║ ███████╗          ║
║        ██╔═██╗  ██╔═██║ ██╔═██╗  ██╔═██╗ ╚════██║          ║
║        ██║  ██╗ ██║ ██║ ██║  ██║ ██║ ██║ ███████║          ║
║        ╚═╝  ╚═╝ ╚═╝ ╚═╝ ╚═╝  ╚═╝ ╚═╝ ╚═╝ ╚══════╝          ║
║                                                            ║
║ ❈ ✦ ❉ ✧ ❈ ✦ ❉ ✧ ❈ ✦ ❉ ✧ ❈ ✦ ❉ ✧ ❈ ✦ ❉ ✧ ❈ ✦ ❉ ✧ ❈ ✦ ❈ ✧ ❈  ║
║ ❈ ✦ ❉ ✧ ❈ ✦ ❉ ✧ ❈ ✦ ❉ ✧ ❈ ✦ ❉ ✧ ❈ ✦ ❉ ✧ ❈ ✦ ❉ ✧ ❈ ✦ ❈ ✧ ❈  ║
╠════════════════════════════════════════════════════════════╣
║                ⚛️⚛️【MiniMax Agent】⚛️⚛️                   ║
╠════════════════════════════════════════════════════════════╣
║                   🐉 多模态控制台 V1.0 🐉                  ║
╚════════════════════════════════════════════════════════════╝
EOF
}

show_main_menu() {
  while true; do
    show_header
    cat <<'EOF'

╔══════════【 核心功能 】══════════╗
║                                  ║
║  [1] 🧠 文本对话     (AI Chat)   ║
║  [2] 🎙️ 小说转语音   (TTS)       ║
║  [3] 🎨 文生图       (T2I)       ║
║  [4] 🖼️ 图生图       (I2I)       ║
║                                  ║
╠══════════【 音乐与创作 】════════╣
║                                  ║
║  [5] 🎵 音乐生成     (Music)     ║
║  [6] 🎤 音乐翻唱     (Cover)     ║
║  [7] ✍️ 歌词生成     (Lyrics)    ║
║                                  ║
╠══════════【 工具与扩展 】════════╣
║                                  ║
║  [8] 🔎 网络搜索     (Search)    ║
║  [9] 👁️ 图片理解     (VLM)       ║
║  [10] 🧩 官方 MCP 扩展           ║
║  [11] 🧰 官方 Skills 技能包      ║
║  [12] 🌐 网页控制台              ║
║                                  ║
╠══════════【 系统控制 】══════════╣
║                                  ║
║  [0] 🚪 退出程序     (Exit)      ║
║                                  ║
╚══════════════════════════════════╝

EOF
    read -r -p "请输入编号并回车: " opt

    case "$opt" in
      1) run_python text_chat.py ;;
      2) run_python tts_novel.py ;;
      3) run_python image_gen.py t2i ;;
      4) run_python image_gen.py i2i ;;
      5) run_python music_gen.py gen ;;
      6) run_python music_gen.py cover ;;
      7) run_python lyrics_gen.py ;;
      8) run_python web_search.py ;;
      9) run_python vlm_image.py ;;
      10) run_python mcp_tools.py ;;
      11) show_skills_menu ;;
      12) run_web_console ;;
      0)
        echo
        echo "感谢使用 MiniMax 专用小工具！"
        exit 0
        ;;
      *)
        echo "⚠️ 输入错误，请重新选择 (0-12)"
        sleep 1
        ;;
    esac
  done
}

show_skills_menu() {
  while true; do
    clear
    cat <<'EOF'
╔══════════【 MiniMax 官方 Skills 技能包 】══════════╗
║                                                    ║
║  [1]  frontend-dev                                ║
║  [2]  fullstack-dev                               ║
║  [3]  android-native-dev                          ║
║  [4]  ios-application-dev                         ║
║  [5]  flutter-dev                                 ║
║  [6]  react-native-dev                            ║
║  [7]  shader-dev                                  ║
║  [8]  gif-sticker-maker                           ║
║  [9]  minimax-pdf                                 ║
║  [10] pptx-generator                              ║
║  [11] minimax-xlsx                                ║
║  [12] minimax-docx                                ║
║  [13] vision-analysis                             ║
║  [14] minimax-multimodal-toolkit                  ║
║  [15] minimax-music-gen                           ║
║  [16] buddy-sings                                 ║
║  [17] minimax-music-playlist                      ║
║                                                    ║
║  [I]  接入说明                                    ║
║  [0]  返回主菜单                                  ║
║                                                    ║
╚════════════════════════════════════════════════════╝

EOF
    read -r -p "请输入编号并回车: " skill_opt

    case "$skill_opt" in
      [Ii]) run_python skills_cli.py --install-info ;;
      1) run_python skills_cli.py frontend-dev ;;
      2) run_python skills_cli.py fullstack-dev ;;
      3) run_python skills_cli.py android-native-dev ;;
      4) run_python skills_cli.py ios-application-dev ;;
      5) run_python skills_cli.py flutter-dev ;;
      6) run_python skills_cli.py react-native-dev ;;
      7) run_python skills_cli.py shader-dev ;;
      8) run_python skills_cli.py gif-sticker-maker ;;
      9) run_python skills_cli.py minimax-pdf ;;
      10) run_python skills_cli.py pptx-generator ;;
      11) run_python skills_cli.py minimax-xlsx ;;
      12) run_python skills_cli.py minimax-docx ;;
      13) run_python skills_cli.py vision-analysis ;;
      14) run_python skills_cli.py minimax-multimodal-toolkit ;;
      15) run_python skills_cli.py minimax-music-gen ;;
      16) run_python skills_cli.py buddy-sings ;;
      17) run_python skills_cli.py minimax-music-playlist ;;
      0) return 0 ;;
      *)
        echo "⚠️ 输入错误，请重新选择 (0-17/I)"
        sleep 1
        ;;
    esac
  done
}

load_saved_environment

if [[ -z "${MINIMAX_MCP_API_HOST:-}" ]]; then
  export MINIMAX_MCP_API_HOST="https://api.minimax.chat"
fi

ensure_api_key
ensure_python
ensure_deps
show_main_menu
