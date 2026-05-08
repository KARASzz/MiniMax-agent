"""
MiniMax 小工具 — 非交互式 CLI 入口
供 OpenClaw agent 通过 exec 工具调用。

用法:
  python cli.py chat "你的问题" [--model MiniMax-M2.7] [--system "系统提示"]
  python cli.py search "搜索关键词"
  python cli.py vlm "分析提示" <图片路径或URL>
  python cli.py image "提示词" [--ratio 1:1] [--n 1] [--ref 参考图URL]
  python cli.py music "描述" [--lyrics "歌词"] [--instrumental]
  python cli.py cover <音频路径或URL> "风格描述" [--lyrics "歌词"]
  python cli.py lyrics "提示词" [--title "标题"] [--mode edit] [--existing "已有歌词"]
  python cli.py tts <md文件路径> <voice_id> [--model speech-2.8-hd] [--speed 1.0]
"""

import argparse
import json
import os
import sys
import time

# 确保项目目录在 sys.path 中
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)


# ── chat ──────────────────────────────────────────────
def cmd_chat(args):
    import anthropic
    from config import API_KEY, ANTHROPIC_BASE_URL

    client = anthropic.Anthropic(base_url=ANTHROPIC_BASE_URL, api_key=API_KEY)
    system_prompt = args.system or "你是一个有用的AI助手，请用中文回答问题。"

    message = client.messages.create(
        model=args.model,
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": [{"type": "text", "text": args.prompt}]}],
    )

    for block in message.content:
        if hasattr(block, "text"):
            print(block.text)


# ── search ────────────────────────────────────────────
def cmd_search(args):
    from web_search import search, display_results

    data = search(args.query)
    organic = data.get("organic", [])
    related = data.get("related_searches", [])

    # 结构化输出 JSON 方便 agent 解析
    results = []
    for item in organic:
        results.append({
            "title": item.get("title", ""),
            "link": item.get("link", ""),
            "snippet": item.get("snippet", ""),
            "date": item.get("date", ""),
        })

    output = {"results": results}
    if related:
        output["related_searches"] = [r.get("query", "") for r in related]

    print(json.dumps(output, ensure_ascii=False, indent=2))


# ── vlm ───────────────────────────────────────────────
def cmd_vlm(args):
    from vlm_image import process_image_source, analyze_image

    image_url = process_image_source(args.image)
    result = analyze_image(args.prompt, image_url)
    print(result)


# ── image ─────────────────────────────────────────────
def cmd_image(args):
    from config import OUTPUT_DIR
    from utils import api_post, download_file

    payload = {
        "model": "image-01",
        "prompt": args.prompt,
        "aspect_ratio": args.ratio,
        "response_format": "url",
        "n": args.n,
        "prompt_optimizer": args.optimize,
    }

    if args.ref:
        payload["subject_reference"] = [{"type": "character", "image_file": args.ref}]

    data = api_post("/v1/image_generation", payload)
    image_urls = data.get("data", {}).get("image_urls", [])

    if not image_urls:
        print("未生成任何图片。", file=sys.stderr)
        sys.exit(1)

    img_dir = os.path.join(OUTPUT_DIR, "images")
    os.makedirs(img_dir, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    prefix = "i2i" if args.ref else "img"

    saved = []
    for i, url in enumerate(image_urls, 1):
        if url:
            save_path = os.path.join(img_dir, f"{prefix}_{timestamp}_{i}.png")
            download_file(url, save_path)
            saved.append(save_path)

    print(json.dumps({"saved_files": saved}, ensure_ascii=False))


# ── music ─────────────────────────────────────────────
def cmd_music(args):
    from config import OUTPUT_DIR
    from utils import api_post, download_file, save_hex_audio

    payload = {
        "model": "music-2.6",
        "prompt": args.prompt,
        "output_format": "url",
        "is_instrumental": args.instrumental,
        "audio_setting": {
            "sample_rate": 44100,
            "bitrate": 256000,
            "format": "mp3",
        },
    }

    if args.lyrics:
        payload["lyrics"] = args.lyrics
    elif not args.instrumental:
        payload["lyrics_optimizer"] = True

    data = api_post("/v1/music_generation", payload)
    music_data = data.get("data", {})
    extra_info = data.get("extra_info", {})
    duration_ms = extra_info.get("music_duration", 0)

    music_dir = os.path.join(OUTPUT_DIR, "music")
    os.makedirs(music_dir, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    save_path = os.path.join(music_dir, f"music_{timestamp}.mp3")

    audio = music_data.get("audio")
    if audio and audio.startswith("http"):
        download_file(audio, save_path)
    elif audio:
        save_hex_audio(audio, save_path)
    else:
        print("未获取到音频数据。", file=sys.stderr)
        sys.exit(1)

    print(json.dumps({
        "saved_file": save_path,
        "duration_ms": duration_ms,
    }, ensure_ascii=False))


# ── cover ─────────────────────────────────────────────
def cmd_cover(args):
    import base64
    from config import OUTPUT_DIR
    from utils import api_post, download_file, save_hex_audio

    payload = {
        "model": "music-cover",
        "prompt": args.style,
        "output_format": "url",
        "audio_setting": {
            "sample_rate": 44100,
            "bitrate": 256000,
            "format": "mp3",
        },
    }

    source = args.audio
    if source.startswith(("http://", "https://")):
        payload["audio_url"] = source
    else:
        if not os.path.isfile(source):
            print(f"文件不存在: {source}", file=sys.stderr)
            sys.exit(1)
        with open(source, "rb") as f:
            payload["audio_base64"] = base64.b64encode(f.read()).decode("utf-8")

    if args.lyrics:
        payload["lyrics"] = args.lyrics

    data = api_post("/v1/music_generation", payload)
    music_data = data.get("data", {})
    extra_info = data.get("extra_info", {})
    duration_ms = extra_info.get("music_duration", 0)

    music_dir = os.path.join(OUTPUT_DIR, "music")
    os.makedirs(music_dir, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    save_path = os.path.join(music_dir, f"cover_{timestamp}.mp3")

    audio = music_data.get("audio")
    if audio and audio.startswith("http"):
        download_file(audio, save_path)
    elif audio:
        save_hex_audio(audio, save_path)
    else:
        print("未获取到音频数据。", file=sys.stderr)
        sys.exit(1)

    print(json.dumps({
        "saved_file": save_path,
        "duration_ms": duration_ms,
    }, ensure_ascii=False))


# ── lyrics ────────────────────────────────────────────
def cmd_lyrics(args):
    from config import OUTPUT_DIR
    from utils import api_post

    payload = {"mode": args.mode}
    if args.prompt:
        payload["prompt"] = args.prompt
    if args.title:
        payload["title"] = args.title
    if args.existing:
        payload["lyrics"] = args.existing

    data = api_post("/v1/lyrics_generation", payload)

    song_title = data.get("song_title", "未命名")
    style_tags = data.get("style_tags", "")
    lyrics = data.get("lyrics", "")

    # 保存到文件
    lyrics_dir = os.path.join(OUTPUT_DIR, "lyrics")
    os.makedirs(lyrics_dir, exist_ok=True)
    safe_title = "".join(c if c.isalnum() or c in " _-" else "_" for c in song_title)
    save_path = os.path.join(lyrics_dir, f"{safe_title}.txt")
    with open(save_path, "w", encoding="utf-8") as f:
        f.write(f"歌名: {song_title}\n风格: {style_tags}\n{'─'*40}\n{lyrics}")

    print(json.dumps({
        "song_title": song_title,
        "style_tags": style_tags,
        "lyrics": lyrics,
        "saved_file": save_path,
    }, ensure_ascii=False, indent=2))


# ── tts ───────────────────────────────────────────────
def cmd_tts(args):
    from config import OUTPUT_DIR
    from tts_novel import read_novel, split_novel, create_tts_task
    from utils import poll_task, get_file_download_url, download_file

    text = read_novel(args.file)
    chunks = split_novel(text)

    novel_name = os.path.splitext(os.path.basename(args.file))[0]
    novel_dir = os.path.join(OUTPUT_DIR, novel_name)
    os.makedirs(novel_dir, exist_ok=True)

    saved_files = []
    for i, (label, chunk_text) in enumerate(chunks, 1):
        print(f"处理片段 [{i}/{len(chunks)}]: {label}", file=sys.stderr)
        task_id, file_id = create_tts_task(chunk_text, args.voice_id, args.model)
        status, result_file_id = poll_task(task_id)
        download_url = get_file_download_url(result_file_id)
        safe_label = "".join(c if c.isalnum() or c in " _-" else "_" for c in label)
        save_path = os.path.join(novel_dir, f"{i:03d}_{safe_label}.mp3")
        download_file(download_url, save_path)
        saved_files.append(save_path)

    print(json.dumps({
        "total_chunks": len(chunks),
        "saved_files": saved_files,
    }, ensure_ascii=False, indent=2))


# ── argparse ──────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        prog="minimax-cli",
        description="MiniMax 小工具非交互式 CLI (供 OpenClaw agent 调用)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # chat
    p = sub.add_parser("chat", help="文本对话（单轮）")
    p.add_argument("prompt", help="用户问题")
    p.add_argument("--model", default="MiniMax-M2.7", help="模型名称")
    p.add_argument("--system", default="", help="系统提示词")

    # search
    p = sub.add_parser("search", help="网络搜索")
    p.add_argument("query", help="搜索关键词")

    # vlm
    p = sub.add_parser("vlm", help="图片理解 (VLM)")
    p.add_argument("prompt", help="分析提示")
    p.add_argument("image", help="图片路径或 HTTP URL")

    # image
    p = sub.add_parser("image", help="图片生成（文生图/图生图）")
    p.add_argument("prompt", help="图片描述 prompt")
    p.add_argument("--ratio", default="1:1", help="宽高比，如 1:1, 16:9, 9:16")
    p.add_argument("--n", type=int, default=1, help="生成数量 1-9")
    p.add_argument("--ref", default="", help="参考图 URL（提供则为图生图）")
    p.add_argument("--optimize", action="store_true", help="开启 prompt 优化")

    # music
    p = sub.add_parser("music", help="音乐生成")
    p.add_argument("prompt", help="音乐描述（风格、情绪、场景）")
    p.add_argument("--lyrics", default="", help="歌词文本")
    p.add_argument("--instrumental", action="store_true", help="纯音乐模式")

    # cover
    p = sub.add_parser("cover", help="音乐翻唱")
    p.add_argument("audio", help="源音频路径或 URL")
    p.add_argument("style", help="目标翻唱风格描述（≥10字符）")
    p.add_argument("--lyrics", default="", help="歌词文本")

    # lyrics
    p = sub.add_parser("lyrics", help="歌词生成")
    p.add_argument("prompt", nargs="?", default="", help="提示词（主题/风格）")
    p.add_argument("--title", default="", help="歌曲标题")
    p.add_argument("--mode", choices=["write_full_song", "edit"], default="write_full_song")
    p.add_argument("--existing", default="", help="已有歌词（edit 模式）")

    # tts
    p = sub.add_parser("tts", help="小说转语音")
    p.add_argument("file", help=".md 小说文件路径")
    p.add_argument("voice_id", help="Voice ID（如 male-qn-qingse）")
    p.add_argument("--model", default="speech-2.8-hd", help="TTS 模型")
    p.add_argument("--speed", type=float, default=1.0, help="语速 0.5-2.0")

    args = parser.parse_args()

    try:
        handler = {
            "chat": cmd_chat,
            "search": cmd_search,
            "vlm": cmd_vlm,
            "image": cmd_image,
            "music": cmd_music,
            "cover": cmd_cover,
            "lyrics": cmd_lyrics,
            "tts": cmd_tts,
        }[args.command]
        handler(args)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
