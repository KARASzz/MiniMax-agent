# MiniMax 多模态 AI 小工具 🐜

基于 [MiniMax API](https://www.minimaxi.com/) 的多模态工具集，集成文本对话、网络搜索、图片理解/生成、音乐生成/翻唱、歌词生成、小说转语音等功能。

## 功能列表

| # | 功能 | 模块 | 说明 |
|---|------|------|------|
| 1 | 文本对话 | `text_chat.py` | 多轮对话，支持 MiniMax-M2.7 / M2.5 系列模型 |
| 2 | 小说转语音 | `tts_novel.py` | 读取 `.md` 小说，自动章节拆分，批量 TTS |
| 3 | 文生图 | `image_gen.py` | 文字描述生成图片，支持多种宽高比 |
| 4 | 图生图 | `image_gen.py` | 基于参考图生成新图片 |
| 5 | 音乐生成 | `music_gen.py` | 根据描述生成音乐，支持纯音乐/带歌词 |
| 6 | 音乐翻唱 | `music_gen.py` | 将已有音频翻唱为指定风格 |
| 7 | 歌词生成 | `lyrics_gen.py` | AI 创作歌词，支持全新创作和编辑模式 |
| 8 | 网络搜索 | `web_search.py` | 基于 Token Plan. 的网络搜索 |
| 9 | 图片理解 | `vlm_image.py` | VLM 视觉模型分析图片内容 |
| 10 | 官方 MCP Server | `mcp_server.py` / `MiniMax-MCP/` | 保留并复用官方 MCP 服务器目录 |
| 11 | 视频生成 | `mcp_tools.py` | 调用官方 MCP `generate_video` |
| 12 | 音色查询/设计/克隆 | `mcp_tools.py` | 调用官方 MCP `list_voices` / `voice_design` / `voice_clone` |
| 13 | 官方 Skills 技能包 | `skills_cli.py` / `skills/` | 查看并接入 MiniMax 官方 AI 编程技能 |

## 环境要求

- Python 3.10+（官方 `MiniMax-MCP` 依赖要求）
- Windows 操作系统
- MiniMax API 密钥

## 安装

1. **设置环境变量**：

   ```powershell
   # API 密钥
   [Environment]::SetEnvironmentVariable("MINIMAX_API_KEY", "你的密钥", "User")
   # 可选：官方 MCP 通道 Host，不设置时 MCP 默认使用 https://api.minimax.chat
   [Environment]::SetEnvironmentVariable("MINIMAX_MCP_API_HOST", "https://api.minimax.chat", "User")
   # 工具目录（项目放在哪就填哪，OpenClaw 集成需要）
   [Environment]::SetEnvironmentVariable("MINIMAX_TOOLS_DIR", "D:\你的路径\+MiniMax小工具", "User")
   ```

   或通过 Windows 系统设置 → 高级 → 环境变量 → 新建用户变量。设置后重启终端生效。

2. **安装依赖**：

   ```bash
   pip install -r requirements.txt
   ```

## 使用方式

### 交互模式（批处理菜单）

双击 `启动.bat`，按编号选择功能，跟随提示操作。

macOS 可双击 `启动.command`，或在终端运行：

```bash
./启动.command
```

macOS 启动器会依次读取项目 `.env`、`~/.zshenv`、`~/.zprofile`、`~/.zshrc`、`~/.bash_profile`、`~/.bashrc` 中的 `MINIMAX_API_KEY`。
`启动.command` 固定使用项目虚拟环境 `.venv/bin/python`；如不存在，请先运行 `python3 -m venv .venv` 并安装依赖。

也可以启动单页网页控制台：

```bash
.venv/bin/python web_app.py
```

默认地址为 `http://127.0.0.1:7860`。

### 命令行模式（CLI）

`cli.py` 提供非交互式入口，适合脚本调用或 OpenClaw agent 集成：

```bash
# 文本对话
python cli.py chat "什么是量子计算？"
python cli.py chat "翻译这段话" --model MiniMax-M2.7-highspeed --system "你是专业翻译"

# 网络搜索
python cli.py search "最新AI新闻"

# 图片理解
python cli.py vlm "描述图片内容" "C:\path\to\image.jpg"

# 图片生成
python cli.py image "一只可爱的猫咪在花园里" --ratio 16:9 --n 2

# 音乐生成
python cli.py music "欢快的电子舞曲" --instrumental
python cli.py music "流行情歌" --lyrics "[Verse]\n月光洒落..."

# 音乐翻唱
python cli.py cover "song.mp3" "爵士风格女声翻唱"

# 歌词生成
python cli.py lyrics "关于夏天的甜蜜爱情"

# 小说转语音
python cli.py tts "novel_input\小说.md" "male-qn-qingse" --model speech-2.8-hd

# 官方 MCP 扩展：查询音色 / 音色设计 / 音色克隆
python cli.py voices --type all
python cli.py speak "这是一段试听文本" --voice-id female-shaonv
python cli.py voice-design "温柔、清晰、适合小说旁白的女性声音" --preview "欢迎收听。"
python cli.py voice-clone my_custom_voice "C:\path\to\demo.mp3" --text "这是我的声音。"

# 官方 MCP 扩展：视频生成
python cli.py video "电影感城市夜景，雨后霓虹，镜头缓慢推进" --async-mode
python cli.py video-query "上一条命令返回的 task_id"

# 启动内置官方 MCP Server（给 Claude Desktop / Cursor / OpenClaw 等 MCP 客户端使用）
python cli.py mcp-server

# 查看内置官方 Skills 技能包
python cli.py skills
python cli.py skills minimax-multimodal-toolkit
python cli.py skills --install-info

# 本地单页网页控制台
python web_app.py
```

运行 `python cli.py --help` 或 `python cli.py <子命令> --help` 查看完整参数说明。

## 目录结构

```
+MiniMax小工具/
├── 启动.bat          # 交互式批处理入口
├── cli.py            # 非交互式 CLI 入口
├── mcp_server.py     # 内置官方 MiniMax MCP Server 启动入口
├── mcp_tools.py      # 官方 MCP 能力的 CLI/交互式封装
├── minimax_mcp_bridge.py # 共享 API Key/Host/输出目录的桥接层
├── skills_cli.py     # 官方 Skills 技能包索引和查看入口
├── web_app.py        # 本地单页网页控制台
├── config.py         # API 配置（密钥、BASE_URL）
├── utils.py          # 通用工具函数（HTTP、轮询、下载）
├── text_chat.py      # 文本对话
├── tts_novel.py      # 小说转语音
├── image_gen.py      # 图片生成
├── music_gen.py      # 音乐生成 / 翻唱
├── lyrics_gen.py     # 歌词生成
├── web_search.py     # 网络搜索
├── vlm_image.py      # 图片理解 (VLM)
├── requirements.txt  # Python 依赖
├── MiniMax-MCP/      # 官方 MiniMax MCP Server（保留原目录）
├── skills/           # 官方 MiniMax Skills 技能包（保留原目录）
├── Voice ID.md       # 音色 ID 参考
├── novel_input/      # 小说 .md 文件放置目录
└── output/           # 所有生成文件输出目录
    ├── images/
    ├── music/
    └── lyrics/
```

## 官方 MiniMax MCP 接入

本项目保留 `MiniMax-MCP/` 官方服务器目录，通过 `minimax_mcp_bridge.py` 接入，仍然共用同一个 `MINIMAX_API_KEY`。官方 MCP 桥接默认使用 `https://api.minimax.chat`；如需切换，可设置 `MINIMAX_MCP_API_HOST` 或 `MINIMAX_API_HOST`。

安装依赖后可以直接启动：

```bash
python cli.py mcp-server
```

MCP 客户端配置示例：

```json
{
  "mcpServers": {
    "MiniMax": {
      "command": "python",
      "args": ["D:\\你的路径\\MiniMax-agent\\mcp_server.py"],
      "env": {
        "MINIMAX_API_HOST": "https://api.minimax.chat",
        "MINIMAX_MCP_BASE_PATH": "D:\\你的路径\\MiniMax-agent\\output",
        "MINIMAX_API_RESOURCE_MODE": "local"
      }
    }
  }
}
```

如果你的 MCP 客户端不能继承系统环境变量，把同一个 `MINIMAX_API_KEY` 也加到上面的 `env` 里即可。

## 官方 Skills 技能包

`skills/` 目录保留官方技能包原样内容，项目侧通过 `skills_cli.py` 读取 `skills/README_zh.md` 和各技能的 `SKILL.md`。双击 `启动.bat` 后选择“官方 Skills 技能包”即可查看完整列表。

```bash
python cli.py skills
python cli.py skills frontend-dev
python cli.py skills --install-info
```

## OpenClaw 集成

本工具已集成为 OpenClaw skill（`mini-ant`），skill 定义位于：

```
~\.openclaw\workspace\skills\mini-ant\SKILL.md
```

OpenClaw agent 会自动发现该技能，根据用户意图调用对应的 `cli.py` 子命令。
