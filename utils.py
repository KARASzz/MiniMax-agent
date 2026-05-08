import os
import sys
import time
import httpx
from config import BASE_URL, get_headers


def api_post(endpoint, payload):
    """发送 POST 请求到 MiniMax API，统一错误处理"""
    url = f"{BASE_URL}{endpoint}"
    resp = httpx.post(url, json=payload, headers=get_headers(), timeout=300)
    resp.raise_for_status()
    data = resp.json()
    base_resp = data.get("base_resp", {})
    if base_resp.get("status_code", 0) != 0:
        raise RuntimeError(f"API 错误 [{base_resp.get('status_code')}]: {base_resp.get('status_msg', '未知错误')}")
    return data


def api_get(endpoint, params=None):
    """发送 GET 请求到 MiniMax API，统一错误处理"""
    url = f"{BASE_URL}{endpoint}"
    resp = httpx.get(url, params=params, headers=get_headers(), timeout=120)
    resp.raise_for_status()
    data = resp.json()
    base_resp = data.get("base_resp", {})
    if base_resp.get("status_code", 0) != 0:
        raise RuntimeError(f"API 错误 [{base_resp.get('status_code')}]: {base_resp.get('status_msg', '未知错误')}")
    return data


def poll_task(task_id, interval=5, timeout=600):
    """
    轮询异步 TTS 任务状态，直到完成或超时。
    返回 (status, file_id)
    """
    endpoint = "/v1/query/t2a_async_query_v2"
    elapsed = 0
    while elapsed < timeout:
        data = api_get(endpoint, params={"task_id": task_id})
        status = data.get("status", "").lower()
        if status == "success":
            return "success", data.get("file_id")
        elif status == "failed":
            raise RuntimeError(f"TTS 任务失败 (task_id={task_id})")
        elif status == "expired":
            raise RuntimeError(f"TTS 任务已过期 (task_id={task_id})")
        # 仍在处理中
        print(f"  任务处理中... 已等待 {elapsed}s", end="\r")
        time.sleep(interval)
        elapsed += interval
    raise TimeoutError(f"TTS 任务超时 (task_id={task_id}, 已等待 {timeout}s)")


def get_file_download_url(file_id):
    """通过文件检索接口获取下载 URL"""
    data = api_get("/v1/files/retrieve", params={"file_id": file_id})
    file_info = data.get("file", {})
    download_url = file_info.get("download_url", "")
    if not download_url:
        raise RuntimeError(f"未获取到下载链接 (file_id={file_id})")
    return download_url


def download_file(url, save_path):
    """下载文件到本地，显示进度"""
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with httpx.stream("GET", url, timeout=300) as resp:
        resp.raise_for_status()
        total = int(resp.headers.get("content-length", 0))
        downloaded = 0
        with open(save_path, "wb") as f:
            for chunk in resp.iter_bytes(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)
                if total > 0:
                    pct = downloaded * 100 // total
                    bar = "█" * (pct // 2) + "░" * (50 - pct // 2)
                    print(f"\r  下载进度: [{bar}] {pct}%", end="")
        if total > 0:
            print()
    print(f"  已保存: {save_path}")


def save_hex_audio(hex_data, save_path):
    """将 hex 编码的音频数据保存为文件"""
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    audio_bytes = bytes.fromhex(hex_data)
    with open(save_path, "wb") as f:
        f.write(audio_bytes)
    print(f"  已保存: {save_path}")


def multi_line_input(prompt="", end_marker="", strip=True):
    """
    多行输入，直到用户输入 end_marker（默认空行）结束。
    返回所有行拼接后的字符串。
    """
    if prompt:
        print(prompt)
    print("  (输入空行结束多行输入，或输入 --END-- 单独成行结束)")
    lines = []
    while True:
        line = sys.stdin.readline()
        if not line:
            break
        line = line.rstrip("\n")
        if strip:
            line = line.strip()
        if line == "--END--":
            break
        if line == "" and not lines:
            # 第一个空行不结束，继续等待输入
            continue
        if line == "":
            # 遇到空行，结束输入
            break
        lines.append(line)
    return "\n".join(lines)


def print_separator(title=""):
    """打印分隔线"""
    if title:
        print(f"\n{'='*20} {title} {'='*20}")
    else:
        print("=" * 50)
