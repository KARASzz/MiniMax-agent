import os
import sys
import time
from config import OUTPUT_DIR
from utils import api_post, download_file, print_separator, multi_line_input

ASPECT_RATIOS = [
    ("1:1",  "1024x1024 正方形"),
    ("16:9", "1280x720 横屏宽幅"),
    ("9:16", "720x1280 竖屏长幅"),
    ("4:3",  "1152x864 传统比例"),
    ("3:2",  "1248x832"),
    ("2:3",  "832x1248 竖版"),
    ("3:4",  "864x1152 竖版"),
    ("21:9", "1344x576 超宽幅"),
]


def select_aspect_ratio():
    print("\n可选宽高比:")
    for i, (ratio, desc) in enumerate(ASPECT_RATIOS, 1):
        print(f"  {i}. {ratio} — {desc}")
    choice = input(f"请选择 [1-{len(ASPECT_RATIOS)}，默认 1]: ").strip()
    idx = int(choice) - 1 if choice.isdigit() and 1 <= int(choice) <= len(ASPECT_RATIOS) else 0
    ratio = ASPECT_RATIOS[idx][0]
    print(f"已选择: {ratio}")
    return ratio


def text_to_image():
    """文生图"""
    print_separator("文生图 (Text → Image)")

    prompt = multi_line_input("\n请输入图片描述 (prompt，支持多行):")
    if not prompt:
        print("描述不能为空。")
        return

    aspect_ratio = select_aspect_ratio()

    n_input = input("生成数量 [1-9，默认 1]: ").strip()
    try:
        n = int(n_input)
        n = max(1, min(9, n))
    except (ValueError, TypeError):
        n = 1

    optimize = input("是否开启 prompt 优化？(y/n，默认 n): ").strip().lower() == "y"

    payload = {
        "model": "image-01",
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "response_format": "url",
        "n": n,
        "prompt_optimizer": optimize,
    }

    print("\n正在生成图片...")
    try:
        data = api_post("/v1/image_generation", payload)
        image_urls = data.get("data", {}).get("image_urls", [])
        metadata = data.get("metadata", {})
        success_count = metadata.get("success_count", len(image_urls))
        failed_count = metadata.get("failed_count", 0)

        print(f"  成功: {success_count}, 失败: {failed_count}")

        if image_urls:
            img_dir = os.path.join(OUTPUT_DIR, "images")
            os.makedirs(img_dir, exist_ok=True)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            for i, url in enumerate(image_urls, 1):
                if url:
                    save_path = os.path.join(img_dir, f"img_{timestamp}_{i}.png")
                    download_file(url, save_path)
        else:
            print("  未生成任何图片。")

    except Exception as e:
        print(f"[错误] {e}")


def image_to_image():
    """图生图"""
    print_separator("图生图 (Image → Image)")

    prompt = multi_line_input("\n请输入图片描述 (prompt，支持多行):")
    if not prompt:
        print("描述不能为空。")
        return

    ref_url = input("请输入参考图片 URL: ").strip()
    if not ref_url:
        print("参考图片不能为空。")
        return

    aspect_ratio = select_aspect_ratio()

    n_input = input("生成数量 [1-9，默认 1]: ").strip()
    try:
        n = int(n_input)
        n = max(1, min(9, n))
    except (ValueError, TypeError):
        n = 1

    payload = {
        "model": "image-01",
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "response_format": "url",
        "n": n,
        "subject_reference": [
            {
                "type": "character",
                "image_file": ref_url,
            }
        ],
    }

    print("\n正在生成图片...")
    try:
        data = api_post("/v1/image_generation", payload)
        image_urls = data.get("data", {}).get("image_urls", [])
        metadata = data.get("metadata", {})
        success_count = metadata.get("success_count", len(image_urls))
        failed_count = metadata.get("failed_count", 0)

        print(f"  成功: {success_count}, 失败: {failed_count}")

        if image_urls:
            img_dir = os.path.join(OUTPUT_DIR, "images")
            os.makedirs(img_dir, exist_ok=True)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            for i, url in enumerate(image_urls, 1):
                if url:
                    save_path = os.path.join(img_dir, f"i2i_{timestamp}_{i}.png")
                    download_file(url, save_path)
        else:
            print("  未生成任何图片。")

    except Exception as e:
        print(f"[错误] {e}")


def run(mode="t2i"):
    if mode == "i2i":
        image_to_image()
    else:
        text_to_image()


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "t2i"
    run(mode)
