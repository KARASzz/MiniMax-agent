from __future__ import annotations

import asyncio
import os
import re
import signal
import sys
import time
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from pydantic import BaseModel


PROJECT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = PROJECT_DIR / "output"
UPLOAD_DIR = PROJECT_DIR / "uploads"
ENV_FILE = PROJECT_DIR / ".env"
VOICE_ID_FILE = PROJECT_DIR / "Voice ID.md"

UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

app = FastAPI(title="MiniMax Web Console")
MCP_PROCESS: asyncio.subprocess.Process | None = None


def load_dotenv_file() -> None:
    if not ENV_FILE.exists():
        return
    for raw_line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def command_env() -> dict[str, str]:
    load_dotenv_file()
    env = os.environ.copy()
    env.setdefault("PYTHONPATH", str(PROJECT_DIR))
    env.setdefault("MINIMAX_MCP_API_HOST", "https://api.minimax.chat")
    return env


def clean_filename(name: str) -> str:
    base = Path(name).name or "upload.bin"
    return re.sub(r"[^A-Za-z0-9._-]+", "_", base)


def text_value(data: dict[str, Any], key: str, default: str = "") -> str:
    value = data.get(key, default)
    return str(value).strip() if value is not None else default


def int_value(data: dict[str, Any], key: str, default: int | None = None) -> int | None:
    value = data.get(key, default)
    if value in ("", None):
        return default
    return int(value)


def float_value(data: dict[str, Any], key: str, default: float = 1.0) -> float:
    value = data.get(key, default)
    if value in ("", None):
        return default
    return float(value)


def bool_value(data: dict[str, Any], key: str) -> bool:
    return data.get(key) in (True, "true", "1", "on", "yes")


def require_text(data: dict[str, Any], key: str, label: str) -> str:
    value = text_value(data, key)
    if not value:
        raise HTTPException(status_code=400, detail=f"缺少必填项: {label}")
    return value


def mandarin_voices(limit: int = 58) -> list[dict[str, str]]:
    if not VOICE_ID_FILE.exists():
        return []

    voices: list[dict[str, str]] = []
    pattern = re.compile(r"^\|\s*(\d+)\s*\|\s*中文 \(普通话\)\s*\|\s*`([^`]+)`\s*\|\s*([^|]+?)\s*\|")
    for line in VOICE_ID_FILE.read_text(encoding="utf-8", errors="replace").splitlines():
        match = pattern.match(line)
        if not match:
            continue
        index = int(match.group(1))
        if index > limit:
            continue
        voices.append({
            "index": str(index),
            "id": match.group(2).strip(),
            "name": match.group(3).strip(),
            "label": f"{index}. {match.group(3).strip()} — {match.group(2).strip()}",
        })
    return voices


def add_option(cmd: list[str], flag: str, value: str | int | float | None) -> None:
    if value not in ("", None):
        cmd.extend([flag, str(value)])


def build_command(tool: str, data: dict[str, Any]) -> list[str]:
    cmd = [sys.executable, "cli.py"]

    if tool == "chat":
        cmd += ["chat", require_text(data, "prompt", "问题")]
        add_option(cmd, "--model", text_value(data, "model", "MiniMax-M2.7"))
        add_option(cmd, "--system", text_value(data, "system"))
    elif tool == "search":
        cmd += ["search", require_text(data, "query", "搜索关键词")]
    elif tool == "vlm":
        cmd += ["vlm", require_text(data, "prompt", "分析提示"), require_text(data, "image", "图片路径或 URL")]
    elif tool == "image":
        cmd += ["image", require_text(data, "prompt", "图片描述")]
        add_option(cmd, "--ratio", text_value(data, "ratio", "1:1"))
        add_option(cmd, "--n", int_value(data, "n", 1))
        add_option(cmd, "--ref", text_value(data, "ref"))
        if bool_value(data, "optimize"):
            cmd.append("--optimize")
    elif tool == "music":
        cmd += ["music", require_text(data, "prompt", "音乐描述")]
        add_option(cmd, "--lyrics", text_value(data, "lyrics"))
        if bool_value(data, "instrumental"):
            cmd.append("--instrumental")
    elif tool == "cover":
        cmd += ["cover", require_text(data, "audio", "源音频"), require_text(data, "style", "翻唱风格")]
        add_option(cmd, "--lyrics", text_value(data, "lyrics"))
    elif tool == "lyrics":
        cmd += ["lyrics"]
        prompt = text_value(data, "prompt")
        if prompt:
            cmd.append(prompt)
        add_option(cmd, "--title", text_value(data, "title"))
        add_option(cmd, "--mode", text_value(data, "mode", "write_full_song"))
        add_option(cmd, "--existing", text_value(data, "existing"))
    elif tool == "tts":
        cmd += ["tts", require_text(data, "file", ".md 文件"), require_text(data, "voice_id", "Voice ID")]
        add_option(cmd, "--model", text_value(data, "model", "speech-2.8-hd"))
        add_option(cmd, "--speed", float_value(data, "speed", 1.0))
        add_option(cmd, "--vol", float_value(data, "vol", 5.0))
    elif tool == "speak":
        cmd += ["speak", require_text(data, "text", "朗读文本")]
        add_option(cmd, "--voice-id", text_value(data, "voice_id"))
        add_option(cmd, "--model", text_value(data, "model", "speech-2.8-hd"))
        add_option(cmd, "--speed", float_value(data, "speed", 1.0))
        add_option(cmd, "--vol", float_value(data, "vol", 5.0))
    elif tool == "voices":
        cmd += ["voices", "--type", text_value(data, "type", "all")]
    elif tool == "voice-design":
        cmd += ["voice-design", require_text(data, "prompt", "音色描述")]
        add_option(cmd, "--preview", text_value(data, "preview", "你好，这是一段由 MiniMax 生成的试听音频。"))
        add_option(cmd, "--voice-id", text_value(data, "voice_id"))
    elif tool == "voice-clone":
        source = require_text(data, "file", "克隆音频")
        cmd += ["voice-clone", require_text(data, "voice_id", "新 Voice ID"), source]
        add_option(cmd, "--text", text_value(data, "text", "你好，这是一段由 MiniMax 生成的试听音频。"))
        if source.startswith(("http://", "https://")):
            cmd.append("--url")
    elif tool == "video":
        cmd += ["video", require_text(data, "prompt", "视频描述")]
        add_option(cmd, "--model", text_value(data, "model"))
        add_option(cmd, "--first-frame", text_value(data, "first_frame"))
        add_option(cmd, "--duration", int_value(data, "duration"))
        add_option(cmd, "--resolution", text_value(data, "resolution"))
        if bool_value(data, "async_mode"):
            cmd.append("--async-mode")
    elif tool == "video-query":
        cmd += ["video-query", require_text(data, "task_id", "task_id")]
    elif tool == "play-audio":
        source = require_text(data, "input", "音频路径或 URL")
        cmd += ["play-audio", source]
        if source.startswith(("http://", "https://")):
            cmd.append("--url")
    elif tool == "skills":
        cmd += ["skills"]
        skill = text_value(data, "skill")
        if skill:
            cmd.append(skill)
        add_option(cmd, "--lines", int_value(data, "lines", 80))
    else:
        raise HTTPException(status_code=400, detail=f"未知功能: {tool}")

    return cmd


class RunRequest(BaseModel):
    tool: str
    data: dict[str, Any] = {}


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    return HTML


@app.post("/api/upload")
async def upload(file: UploadFile = File(...)) -> dict[str, str]:
    filename = f"{int(time.time())}_{clean_filename(file.filename or 'upload.bin')}"
    target = UPLOAD_DIR / filename
    content = await file.read()
    target.write_bytes(content)
    return {"path": str(target), "name": file.filename or filename}


@app.post("/api/run")
async def run_tool(request: RunRequest) -> JSONResponse:
    cmd = build_command(request.tool, request.data)
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(PROJECT_DIR),
            env=command_env(),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_bytes, stderr_bytes = await asyncio.wait_for(proc.communicate(), timeout=3600)
    except asyncio.TimeoutError as exc:
        raise HTTPException(status_code=504, detail="任务超时") from exc

    stdout = stdout_bytes.decode("utf-8", errors="replace")
    stderr = stderr_bytes.decode("utf-8", errors="replace")
    return JSONResponse({
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "command": cmd[1:],
        "stdout": stdout,
        "stderr": stderr,
    })


@app.get("/api/skills")
async def skills() -> list[dict[str, str]]:
    from skills_cli import discover_skills

    return [skill.__dict__ for skill in discover_skills()]


@app.get("/api/voices/mandarin")
async def voices_mandarin() -> list[dict[str, str]]:
    return mandarin_voices()


@app.get("/api/outputs")
async def outputs() -> list[dict[str, Any]]:
    files = []
    for path in OUTPUT_DIR.rglob("*"):
        if path.is_file():
            stat = path.stat()
            files.append({
                "name": path.name,
                "path": str(path),
                "relative": str(path.relative_to(PROJECT_DIR)),
                "size": stat.st_size,
                "mtime": stat.st_mtime,
            })
    files.sort(key=lambda item: item["mtime"], reverse=True)
    return files[:80]


@app.get("/api/download")
async def download(path: str) -> FileResponse:
    target = Path(path).expanduser().resolve()
    allowed = False
    for root in (OUTPUT_DIR.resolve(), UPLOAD_DIR.resolve()):
        try:
            target.relative_to(root)
            allowed = True
            break
        except ValueError:
            continue
    if not allowed:
        raise HTTPException(status_code=403, detail="只允许下载 output 或 uploads 中的文件")
    if not target.is_file():
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(target)


@app.post("/api/mcp/start")
async def start_mcp() -> dict[str, Any]:
    global MCP_PROCESS
    if MCP_PROCESS and MCP_PROCESS.returncode is None:
        return {"running": True, "pid": MCP_PROCESS.pid}
    MCP_PROCESS = await asyncio.create_subprocess_exec(
        sys.executable,
        "cli.py",
        "mcp-server",
        cwd=str(PROJECT_DIR),
        env=command_env(),
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    return {"running": True, "pid": MCP_PROCESS.pid}


@app.post("/api/mcp/stop")
async def stop_mcp() -> dict[str, Any]:
    global MCP_PROCESS
    if not MCP_PROCESS or MCP_PROCESS.returncode is not None:
        return {"running": False}
    MCP_PROCESS.send_signal(signal.SIGTERM)
    try:
        await asyncio.wait_for(MCP_PROCESS.wait(), timeout=5)
    except asyncio.TimeoutError:
        MCP_PROCESS.kill()
        await MCP_PROCESS.wait()
    return {"running": False}


@app.get("/api/mcp/status")
async def mcp_status() -> dict[str, Any]:
    if MCP_PROCESS and MCP_PROCESS.returncode is None:
        return {"running": True, "pid": MCP_PROCESS.pid}
    return {"running": False}


HTML = r"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>MiniMax 控制台</title>
  <style>
    :root {
      --bg: #f6f7f9;
      --panel: #ffffff;
      --text: #16202a;
      --muted: #697586;
      --line: #d9dee7;
      --accent: #0f766e;
      --accent-2: #b45309;
      --danger: #b42318;
      --blue: #1d4ed8;
      --radius: 8px;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font: 14px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    .app {
      min-height: 100vh;
      display: grid;
      grid-template-columns: 260px minmax(0, 1fr);
    }
    aside {
      border-right: 1px solid var(--line);
      background: #fbfcfd;
      padding: 18px 12px;
      overflow-y: auto;
      max-height: 100vh;
      position: sticky;
      top: 0;
    }
    main {
      padding: 20px;
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(320px, 420px);
      gap: 16px;
      align-items: start;
    }
    h1 {
      font-size: 20px;
      line-height: 1.2;
      margin: 0 0 4px;
      letter-spacing: 0;
    }
    h2 {
      font-size: 16px;
      margin: 0;
      letter-spacing: 0;
    }
    .muted { color: var(--muted); }
    .brand { padding: 0 8px 14px; }
    .nav-group { margin: 14px 0 6px; padding: 0 8px; color: var(--muted); font-size: 12px; }
    .tool-btn {
      width: 100%;
      min-height: 34px;
      display: flex;
      align-items: center;
      gap: 8px;
      border: 1px solid transparent;
      background: transparent;
      color: var(--text);
      border-radius: 6px;
      padding: 7px 8px;
      cursor: pointer;
      text-align: left;
      font: inherit;
    }
    .tool-btn:hover { background: #eef2f6; }
    .tool-btn.active { background: #e3f4f1; border-color: #a7d8d1; color: #0b5d56; }
    .ico { width: 22px; text-align: center; color: var(--muted); }
    .card {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      padding: 16px;
    }
    .topbar {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: center;
      margin-bottom: 14px;
    }
    .status {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 5px 10px;
      color: var(--muted);
      background: #fff;
      white-space: nowrap;
    }
    .dot { width: 8px; height: 8px; border-radius: 999px; background: #98a2b3; }
    .dot.ok { background: var(--accent); }
    form {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
    }
    label { display: grid; gap: 5px; font-weight: 600; }
    label.full { grid-column: 1 / -1; }
    input, textarea, select {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 9px 10px;
      font: inherit;
      color: var(--text);
      background: #fff;
    }
    textarea { min-height: 110px; resize: vertical; }
    input[type="checkbox"] { width: 18px; height: 18px; }
    .check-row { display: flex; align-items: center; gap: 8px; padding-top: 25px; }
    .actions {
      grid-column: 1 / -1;
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      align-items: center;
      margin-top: 2px;
    }
    button.primary, button.secondary, button.danger {
      border: 1px solid transparent;
      border-radius: 6px;
      min-height: 36px;
      padding: 8px 12px;
      font: inherit;
      cursor: pointer;
    }
    button.primary { background: var(--accent); color: white; }
    button.secondary { background: #eef2f6; color: var(--text); border-color: var(--line); }
    button.danger { background: #fff1f0; color: var(--danger); border-color: #f6c7c2; }
    button:disabled { opacity: .55; cursor: wait; }
    .result {
      min-height: 220px;
      max-height: 58vh;
      overflow: auto;
      white-space: pre-wrap;
      background: #111827;
      color: #e5e7eb;
      border-radius: 6px;
      padding: 12px;
      font: 13px/1.5 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    }
    .side-stack { display: grid; gap: 16px; }
    .file-list { display: grid; gap: 8px; max-height: 280px; overflow: auto; }
    .file-item {
      display: grid;
      gap: 2px;
      padding: 9px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fff;
    }
    a { color: var(--blue); text-decoration: none; }
    a:hover { text-decoration: underline; }
    .pill {
      display: inline-block;
      font-size: 12px;
      padding: 2px 7px;
      border-radius: 999px;
      background: #fff7ed;
      color: var(--accent-2);
      border: 1px solid #fed7aa;
    }
    @media (max-width: 980px) {
      .app { grid-template-columns: 1fr; }
      aside { position: static; max-height: none; border-right: 0; border-bottom: 1px solid var(--line); }
      main { grid-template-columns: 1fr; padding: 14px; }
      form { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class="app">
    <aside>
      <div class="brand">
        <h1>MiniMax 控制台</h1>
        <div class="muted">本地单页前端</div>
      </div>
      <div id="nav"></div>
    </aside>

    <main>
      <section class="card">
        <div class="topbar">
          <div>
            <h2 id="toolTitle"></h2>
            <div id="toolDesc" class="muted"></div>
          </div>
          <span class="status"><span id="statusDot" class="dot"></span><span id="statusText">空闲</span></span>
        </div>
        <form id="toolForm"></form>
      </section>

      <section class="side-stack">
        <div class="card">
          <div class="topbar">
            <h2>输出</h2>
            <button id="clearOutput" class="secondary" type="button">清空</button>
          </div>
          <div id="result" class="result">请选择左侧功能。</div>
        </div>
        <div class="card">
          <div class="topbar">
            <h2>最近文件</h2>
            <button id="refreshFiles" class="secondary" type="button">刷新</button>
          </div>
          <div id="files" class="file-list"></div>
        </div>
      </section>
    </main>
  </div>

  <script>
    const groups = [
      ["基础", [
        ["chat", "对话", "MiniMax 文本对话"],
        ["search", "搜索", "网络搜索"],
        ["vlm", "看图", "图片理解"],
      ]],
      ["生成", [
        ["image", "图片", "文生图 / 图生图"],
        ["music", "音乐", "音乐生成"],
        ["cover", "翻唱", "音乐翻唱"],
        ["lyrics", "歌词", "歌词生成"],
        ["tts", "小说", "小说转语音"],
      ]],
      ["官方 MCP", [
        ["speak", "朗读", "文本转语音"],
        ["voices", "音色", "查询音色"],
        ["voice-design", "设计", "音色设计"],
        ["voice-clone", "克隆", "音色克隆"],
        ["video", "视频", "视频生成"],
        ["video-query", "任务", "查询视频任务"],
        ["play-audio", "播放", "播放音频"],
        ["mcp-server", "MCP", "启动 / 停止 MCP Server"],
      ]],
      ["技能", [
        ["skills", "Skills", "官方 Skills 列表"],
      ]],
    ];

    const schemas = {
      chat: { title: "文本对话", desc: "调用 cli.py chat", fields: [
        text("prompt", "问题", true, "textarea"),
        text("model", "模型", false, "text", "MiniMax-M2.7"),
        text("system", "系统提示", false, "textarea"),
      ]},
      search: { title: "网络搜索", desc: "调用 cli.py search", fields: [text("query", "关键词", true)] },
      vlm: { title: "图片理解", desc: "支持图片 URL 或上传本地图片", fields: [
        text("prompt", "分析提示", true, "textarea", "描述这张图片"),
        text("image", "图片路径或 URL", true),
        file("image_file", "上传图片", "image"),
      ]},
      image: { title: "图片生成", desc: "生成结果保存到 output/images", fields: [
        text("prompt", "图片描述", true, "textarea"),
        select("ratio", "比例", ["1:1","16:9","9:16","4:3","3:4","3:2","2:3","21:9"], "1:1"),
        number("n", "数量", 1, 1, 9),
        text("ref", "参考图 URL"),
        check("optimize", "Prompt 优化"),
      ]},
      music: { title: "音乐生成", desc: "生成结果保存到 output/music", fields: [
        text("prompt", "音乐描述", true, "textarea"),
        text("lyrics", "歌词", false, "textarea"),
        check("instrumental", "纯音乐"),
      ]},
      cover: { title: "音乐翻唱", desc: "源音频可上传或填写 URL", fields: [
        text("audio", "源音频路径或 URL", true),
        file("audio_file", "上传音频", "audio"),
        text("style", "翻唱风格", true, "textarea"),
        text("lyrics", "歌词", false, "textarea"),
      ]},
      lyrics: { title: "歌词生成", desc: "生成结果保存到 output/lyrics", fields: [
        text("prompt", "主题 / 风格", false, "textarea"),
        text("title", "歌曲标题"),
        select("mode", "模式", ["write_full_song","edit"], "write_full_song"),
        text("existing", "已有歌词", false, "textarea"),
      ]},
      tts: { title: "小说转语音", desc: "读取 .md 文件并批量合成", fields: [
        text("file", ".md 文件路径", true),
        file("md_file", "上传 .md 文件", ".md"),
        voiceSelect("voice_id", "Voice ID", "male-qn-qingse", true),
        text("model", "模型", false, "text", "speech-2.8-hd"),
        number("speed", "语速", 1, 0.5, 2, 0.1),
        volumeSelect("vol", "音量", "5.0"),
      ]},
      speak: { title: "文本转语音", desc: "官方 MCP TTS 封装", fields: [
        text("text", "朗读文本", true, "textarea"),
        voiceSelect("voice_id", "Voice ID", "female-shaonv", false, true),
        text("model", "模型", false, "text", "speech-2.8-hd"),
        number("speed", "语速", 1, 0.5, 2, 0.1),
        volumeSelect("vol", "音量", "5.0"),
      ]},
      voices: { title: "查询音色", desc: "官方 MCP list_voices", fields: [select("type", "类型", ["all","system","voice_cloning"], "all")] },
      "voice-design": { title: "音色设计", desc: "根据描述生成音色", fields: [
        text("prompt", "音色描述", true, "textarea"),
        text("preview", "试听文本", false, "textarea", "你好，这是一段由 MiniMax 生成的试听音频。"),
        voiceSelect("voice_id", "指定 Voice ID", "", false, true),
      ]},
      "voice-clone": { title: "音色克隆", desc: "使用本地音频或 URL 克隆音色", fields: [
        text("voice_id", "新 Voice ID", true),
        text("file", "音频路径或 URL", true),
        file("clone_file", "上传音频", "audio"),
        text("text", "试听文本", false, "textarea", "你好，这是一段由 MiniMax 生成的试听音频。"),
      ]},
      video: { title: "视频生成", desc: "建议长任务使用异步模式", fields: [
        text("prompt", "视频描述", true, "textarea"),
        text("model", "模型"),
        text("first_frame", "首帧图片路径或 URL"),
        file("first_frame_file", "上传首帧", "image"),
        number("duration", "时长"),
        select("resolution", "分辨率", ["","768P","1080P"], ""),
        check("async_mode", "异步提交"),
      ]},
      "video-query": { title: "查询视频任务", desc: "查询 async 返回的 task_id", fields: [text("task_id", "task_id", true)] },
      "play-audio": { title: "播放音频", desc: "需要本机 ffplay", fields: [text("input", "音频路径或 URL", true)] },
      "mcp-server": { title: "MCP Server", desc: "后台启动或停止内置官方 MCP Server", fields: [] },
      skills: { title: "官方 Skills", desc: "查看已安装的 Skills 说明", fields: [
        select("skill", "技能", [""], ""),
        number("lines", "显示行数", 80, 20, 500),
      ]},
    };

    function text(name, label, required=false, kind="text", value="") { return {type:"text", name, label, required, kind, value}; }
    function number(name, label, value="", min="", max="", step="") { return {type:"number", name, label, value, min, max, step}; }
    function check(name, label) { return {type:"check", name, label}; }
    function select(name, label, options, value) { return {type:"select", name, label, options, value}; }
    function volumeSelect(name, label, value="5.0") { return {type:"volume", name, label, value}; }
    function voiceSelect(name, label, value="", required=false, allowEmpty=false) { return {type:"voice", name, label, value, required, allowEmpty}; }
    function file(name, label, accept) { return {type:"file", name, label, accept}; }

    const nav = document.getElementById("nav");
    const form = document.getElementById("toolForm");
    const result = document.getElementById("result");
    const statusText = document.getElementById("statusText");
    const statusDot = document.getElementById("statusDot");
    let activeTool = "chat";
    let running = false;
    let mandarinVoices = [];

    function renderNav() {
      nav.innerHTML = "";
      for (const [group, tools] of groups) {
        const label = document.createElement("div");
        label.className = "nav-group";
        label.textContent = group;
        nav.appendChild(label);
        for (const [id, name, desc] of tools) {
          const btn = document.createElement("button");
          btn.className = "tool-btn" + (id === activeTool ? " active" : "");
          btn.type = "button";
          btn.title = desc;
          btn.innerHTML = `<span class="ico">${name.slice(0, 2)}</span><span>${name}</span>`;
          btn.onclick = () => { activeTool = id; renderNav(); renderTool(); };
          nav.appendChild(btn);
        }
      }
    }

    async function loadSkills() {
      const res = await fetch("/api/skills");
      const skills = await res.json();
      const names = [""].concat(skills.map(s => s.name));
      schemas.skills.fields[0].options = names;
    }

    async function loadMandarinVoices() {
      const res = await fetch("/api/voices/mandarin");
      mandarinVoices = await res.json();
    }

    function renderTool() {
      const schema = schemas[activeTool];
      document.getElementById("toolTitle").textContent = schema.title;
      document.getElementById("toolDesc").textContent = schema.desc;
      form.innerHTML = "";

      if (activeTool === "mcp-server") {
        const actions = document.createElement("div");
        actions.className = "actions";
        actions.innerHTML = `
          <button class="primary" type="button" id="startMcp">启动</button>
          <button class="danger" type="button" id="stopMcp">停止</button>
          <button class="secondary" type="button" id="statusMcp">状态</button>
        `;
        form.appendChild(actions);
        document.getElementById("startMcp").onclick = () => mcpAction("start");
        document.getElementById("stopMcp").onclick = () => mcpAction("stop");
        document.getElementById("statusMcp").onclick = () => mcpAction("status");
        return;
      }

      for (const field of schema.fields) {
        const wrap = document.createElement("label");
        wrap.className = field.kind === "textarea" || field.type === "file" ? "full" : "";
        if (field.type === "check") {
          wrap.className = "check-row";
          wrap.innerHTML = `<input name="${field.name}" type="checkbox"><span>${field.label}</span>`;
        } else if (field.type === "select") {
          wrap.innerHTML = `<span>${field.label}</span><select name="${field.name}">${field.options.map(o => `<option value="${escapeAttr(o)}"${o === field.value ? " selected" : ""}>${o || "默认"}</option>`).join("")}</select>`;
        } else if (field.type === "voice") {
          const options = [];
          if (field.allowEmpty) options.push(`<option value="">官方默认 / 不指定</option>`);
          for (const voice of mandarinVoices) {
            const selected = voice.id === field.value ? " selected" : "";
            options.push(`<option value="${escapeAttr(voice.id)}"${selected}>${escapeHtml(voice.label)}</option>`);
          }
          wrap.innerHTML = `<span>${field.label}${field.required ? " *" : ""}</span><select name="${field.name}">${options.join("")}</select>`;
        } else if (field.type === "volume") {
          const options = [];
          for (let i = 0; i <= 10; i += 1) {
            const value = i.toFixed(1);
            const selected = value === String(field.value) ? " selected" : "";
            options.push(`<option value="${value}"${selected}>${value}</option>`);
          }
          wrap.innerHTML = `<span>${field.label}</span><select name="${field.name}">${options.join("")}</select>`;
        } else if (field.type === "number") {
          wrap.innerHTML = `<span>${field.label}</span><input name="${field.name}" type="number" value="${field.value ?? ""}" min="${field.min ?? ""}" max="${field.max ?? ""}" step="${field.step ?? ""}">`;
        } else if (field.type === "file") {
          wrap.innerHTML = `<span>${field.label}</span><input name="${field.name}" type="file" accept="${field.accept || ""}">`;
        } else if (field.kind === "textarea") {
          wrap.innerHTML = `<span>${field.label}${field.required ? " *" : ""}</span><textarea name="${field.name}">${field.value || ""}</textarea>`;
        } else {
          wrap.innerHTML = `<span>${field.label}${field.required ? " *" : ""}</span><input name="${field.name}" value="${field.value || ""}">`;
        }
        form.appendChild(wrap);
      }
      const actions = document.createElement("div");
      actions.className = "actions";
      actions.innerHTML = `<button class="primary" type="submit">执行</button><span class="pill">会调用本地 cli.py</span>`;
      form.appendChild(actions);
    }

    function escapeAttr(value) {
      return String(value).replaceAll("&", "&amp;").replaceAll('"', "&quot;").replaceAll("<", "&lt;");
    }

    async function uploadFile(input) {
      if (!input.files || !input.files[0]) return "";
      const body = new FormData();
      body.append("file", input.files[0]);
      const res = await fetch("/api/upload", { method: "POST", body });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      return data.path;
    }

    async function collectData() {
      const data = {};
      for (const el of form.elements) {
        if (!el.name) continue;
        if (el.type === "file") continue;
        if (el.type === "checkbox") data[el.name] = el.checked;
        else data[el.name] = el.value;
      }
      const fileMap = {
        image_file: "image",
        audio_file: "audio",
        md_file: "file",
        clone_file: "file",
        first_frame_file: "first_frame",
      };
      for (const el of form.querySelectorAll("input[type=file]")) {
        if (el.files && el.files[0]) {
          data[fileMap[el.name]] = await uploadFile(el);
        }
      }
      return data;
    }

    form.onsubmit = async (event) => {
      event.preventDefault();
      if (running) return;
      running = true;
      setStatus("执行中", true);
      result.textContent = "任务执行中...";
      form.querySelectorAll("button").forEach(btn => btn.disabled = true);
      try {
        const data = await collectData();
        const res = await fetch("/api/run", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({ tool: activeTool, data }),
        });
        const payload = await res.json();
        renderResult(payload, res.ok);
        await loadOutputs();
      } catch (err) {
        result.textContent = String(err);
      } finally {
        running = false;
        setStatus("空闲", false);
        form.querySelectorAll("button").forEach(btn => btn.disabled = false);
      }
    };

    function renderResult(payload, httpOk) {
      if (!httpOk || payload.detail) {
        result.textContent = payload.detail || JSON.stringify(payload, null, 2);
        return;
      }
      let body = "";
      body += `命令: python ${payload.command.join(" ")}\n`;
      body += `状态: ${payload.ok ? "成功" : "失败"} (${payload.returncode})\n\n`;
      body += pretty(payload.stdout);
      if (payload.stderr) body += `\n\n[stderr]\n${payload.stderr}`;
      result.textContent = body.trim() || "无输出";
    }

    function pretty(text) {
      const trimmed = (text || "").trim();
      if (!trimmed) return "";
      try { return JSON.stringify(JSON.parse(trimmed), null, 2); }
      catch { return trimmed; }
    }

    async function mcpAction(action) {
      setStatus("处理中", true);
      const url = action === "status" ? "/api/mcp/status" : `/api/mcp/${action}`;
      const res = await fetch(url, { method: action === "status" ? "GET" : "POST" });
      const payload = await res.json();
      result.textContent = JSON.stringify(payload, null, 2);
      setStatus(payload.running ? `MCP ${payload.pid}` : "空闲", !!payload.running);
    }

    function setStatus(text, active) {
      statusText.textContent = text;
      statusDot.classList.toggle("ok", active);
    }

    async function loadOutputs() {
      const res = await fetch("/api/outputs");
      const files = await res.json();
      const box = document.getElementById("files");
      if (!files.length) {
        box.innerHTML = `<div class="muted">暂无文件</div>`;
        return;
      }
      box.innerHTML = files.map(file => {
        const href = `/api/download?path=${encodeURIComponent(file.path)}`;
        const size = formatSize(file.size);
        return `<div class="file-item"><a href="${href}">${escapeHtml(file.relative)}</a><span class="muted">${size}</span></div>`;
      }).join("");
    }

    function formatSize(size) {
      if (size > 1024 * 1024) return `${(size / 1024 / 1024).toFixed(1)} MB`;
      if (size > 1024) return `${(size / 1024).toFixed(1)} KB`;
      return `${size} B`;
    }

    function escapeHtml(value) {
      return String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
    }

    document.getElementById("clearOutput").onclick = () => result.textContent = "";
    document.getElementById("refreshFiles").onclick = loadOutputs;

    (async function init() {
      await Promise.all([loadSkills(), loadMandarinVoices()]);
      renderNav();
      renderTool();
      loadOutputs();
    })();
  </script>
</body>
</html>
"""


def main() -> None:
    host = os.environ.get("MINIMAX_WEB_HOST", "127.0.0.1")
    port = int(os.environ.get("MINIMAX_WEB_PORT", "7860"))
    print(f"MiniMax Web Console: http://{host}:{port}")
    uvicorn.run("web_app:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
