"""
MiniMax Token Plan - 图片理解 (VLM)
使用 coding-plan-vlm 额度进行图片分析
"""

import os
import base64
import httpx
from config import BASE_URL, get_headers
from utils import print_separator


SUPPORTED_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB


def process_image_source(image_source):
    """
    处理图片来源，返回 API 所需的 image_url 格式。
    - HTTP/HTTPS URL → 直接传递
    - 本地文件路径 → 读取并转为 base64 data URL
    """
    if image_source.startswith(("http://", "https://")):
        return image_source

    # 本地文件
    if not os.path.exists(image_source):
        raise FileNotFoundError(f"文件不存在: {image_source}")

    ext = os.path.splitext(image_source)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"不支持的格式 {ext}，仅支持: {', '.join(SUPPORTED_EXTENSIONS)}")

    file_size = os.path.getsize(image_source)
    if file_size > MAX_FILE_SIZE:
        raise ValueError(f"文件过大 ({file_size / 1024 / 1024:.1f}MB)，最大支持 20MB")

    fmt_map = {".jpg": "jpeg", ".jpeg": "jpeg", ".png": "png", ".webp": "webp"}
    image_format = fmt_map.get(ext, "jpeg")

    with open(image_source, "rb") as f:
        data = f.read()

    b64 = base64.b64encode(data).decode("utf-8")
    return f"data:image/{image_format};base64,{b64}"


def analyze_image(prompt, image_url):
    """调用 VLM 图片理解 API"""
    url = f"{BASE_URL}/v1/coding_plan/vlm"
    payload = {"prompt": prompt, "image_url": image_url}
    resp = httpx.post(url, json=payload, headers=get_headers(), timeout=60)
    resp.raise_for_status()
    data = resp.json()
    base_resp = data.get("base_resp", {})
    if base_resp.get("status_code", 0) != 0:
        raise RuntimeError(f"API 错误 [{base_resp.get('status_code')}]: {base_resp.get('status_msg', '未知错误')}")
    content = data.get("content", "")
    if not content:
        raise RuntimeError("API 未返回分析内容")
    return content


def run():
    """交互式图片理解主循环"""
    print_separator("图片理解 (VLM)")
    print("  支持输入本地图片路径或 HTTP URL。")
    print("  支持格式: JPEG, PNG, WebP（最大 20MB）")
    print("  输入 q 退出。")
    print()

    current_image_url = None
    current_source = None

    while True:
        # 选择图片
        if current_image_url is None:
            try:
                source = input("图片路径或URL> ").strip()
            except (EOFError, KeyboardInterrupt):
                break

            if not source:
                continue
            if source.lower() == "q":
                break

            # 去除拖拽时可能带的引号
            source = source.strip('"').strip("'")

            try:
                current_image_url = process_image_source(source)
                current_source = source
                if source.startswith(("http://", "https://")):
                    print(f"  已加载 URL: {source}")
                else:
                    print(f"  已加载文件: {os.path.basename(source)}")
            except (FileNotFoundError, ValueError) as e:
                print(f"  错误: {e}")
                continue

        # 输入分析提示
        print()
        print("  输入你想了解的内容（如「描述这张图片」「图中有什么文字」）")
        print("  输入 /new 换图，输入 q 退出")
        try:
            prompt = input("提问> ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not prompt:
            continue
        if prompt.lower() == "q":
            break
        if prompt.lower() == "/new":
            current_image_url = None
            current_source = None
            print()
            continue

        try:
            print()
            print("  分析中...")
            result = analyze_image(prompt, current_image_url)
            print()
            print("  ── 分析结果 ──")
            print()
            # 缩进输出每一行
            for line in result.split("\n"):
                print(f"  {line}")
            print()
        except httpx.HTTPStatusError as e:
            print(f"  HTTP 错误: {e.response.status_code} - {e.response.text[:200]}")
        except Exception as e:
            print(f"  分析失败: {e}")
        print()

    print("已退出图片理解。")


if __name__ == "__main__":
    run()
