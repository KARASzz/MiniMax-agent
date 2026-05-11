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
from fastapi import FastAPI, File, HTTPException, UploadFile, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel


PROJECT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = PROJECT_DIR / "output"
UPLOAD_DIR = PROJECT_DIR / "uploads"
ENV_FILE = PROJECT_DIR / ".env"
VOICE_ID_FILE = PROJECT_DIR / "Voice ID.md"

UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

app = FastAPI(title="MiniMax Web Console")
templates = Jinja2Templates(directory="templates")
templates.env.auto_reload = True
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
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


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





def main() -> None:
    host = os.environ.get("MINIMAX_WEB_HOST", "127.0.0.1")
    port = int(os.environ.get("MINIMAX_WEB_PORT", "7860"))
    print(f"MiniMax Web Console: http://{host}:{port}")
    uvicorn.run("web_app:app", host=host, port=port, reload=True)


if __name__ == "__main__":
    main()
