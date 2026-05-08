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
| 8 | 网络搜索 | `web_search.py` | 基于 Token Plan 的网络搜索 |
| 9 | 图片理解 | `vlm_image.py` | VLM 视觉模型分析图片内容 |

## 环境要求

- Python 3.8+
- Windows 操作系统
- MiniMax API 密钥

## 安装

1. **设置环境变量**：

   ```powershell
   # API 密钥
   [Environment]::SetEnvironmentVariable("MINIMAX_API_KEY", "你的密钥", "User")
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
```

运行 `python cli.py --help` 或 `python cli.py <子命令> --help` 查看完整参数说明。

## 目录结构

```
+MiniMax小工具/
├── 启动.bat          # 交互式批处理入口
├── cli.py            # 非交互式 CLI 入口
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
├── Voice ID.md       # 音色 ID 参考
├── novel_input/      # 小说 .md 文件放置目录
└── output/           # 所有生成文件输出目录
    ├── images/
    ├── music/
    └── lyrics/
```

## OpenClaw 集成

本工具已集成为 OpenClaw skill（`mini-ant`），skill 定义位于：

```
~\.openclaw\workspace\skills\mini-ant\SKILL.md
```

OpenClaw agent 会自动发现该技能，根据用户意图调用对应的 `cli.py` 子命令。
