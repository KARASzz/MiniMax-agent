import os
import sys
import time
import base64
from config import OUTPUT_DIR
from utils import api_post, download_file, save_hex_audio, print_separator


def music_generation():
    """文本生成音乐 (music-2.6)"""
    print_separator("音乐生成 (Music Generation)")

    # 纯音乐 or 有歌词
    instrumental = input("\n生成纯音乐（无人声）？(y/n，默认 n): ").strip().lower() == "y"

    prompt = input("请输入音乐描述 (风格、情绪、场景): ").strip()
    if not prompt and instrumental:
        print("纯音乐模式下描述为必填。")
        return

    lyrics = ""
    if not instrumental:
        print("请输入歌词（用 \\n 分隔行，支持 [Verse] [Chorus] 等标签）:")
        print("（输入空行结束，或直接回车跳过）")
        lines = []
        while True:
            line = input()
            if line == "":
                break
            lines.append(line)
        lyrics = "\n".join(lines)

        if not lyrics:
            auto_lyrics = input("是否自动根据描述生成歌词？(y/n，默认 y): ").strip().lower()
            if auto_lyrics != "n":
                if not prompt:
                    prompt = input("请输入描述以生成歌词: ").strip()

    payload = {
        "model": "music-2.6",
        "prompt": prompt,
        "output_format": "url",
        "is_instrumental": instrumental,
        "audio_setting": {
            "sample_rate": 44100,
            "bitrate": 256000,
            "format": "mp3",
        },
    }

    if lyrics:
        payload["lyrics"] = lyrics
    elif not instrumental and not lyrics:
        payload["lyrics_optimizer"] = True

    print("\n正在生成音乐（可能需要较长时间）...")
    try:
        data = api_post("/v1/music_generation", payload)
        music_data = data.get("data", {})
        extra_info = data.get("extra_info", {})

        duration_ms = extra_info.get("music_duration", 0)
        duration_s = duration_ms / 1000 if duration_ms else 0
        print(f"  生成完成！时长: {duration_s:.1f}s")

        # 保存音频
        music_dir = os.path.join(OUTPUT_DIR, "music")
        os.makedirs(music_dir, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        save_path = os.path.join(music_dir, f"music_{timestamp}.mp3")

        audio_url = music_data.get("audio")
        if audio_url and audio_url.startswith("http"):
            download_file(audio_url, save_path)
        elif audio_url:
            # hex 编码的音频数据
            save_hex_audio(audio_url, save_path)
        else:
            print("  未获取到音频数据。")

    except Exception as e:
        print(f"[错误] {e}")


def music_cover():
    """音乐翻唱 (music-cover)"""
    print_separator("音乐翻唱 (Music Cover)")

    prompt = input("\n请输入目标翻唱风格描述 (10-300字符): ").strip()
    if not prompt or len(prompt) < 10:
        print("风格描述至少需要 10 个字符。")
        return

    # 参考音频来源
    print("\n参考音频来源:")
    print("  1. 本地文件路径")
    print("  2. 在线 URL")
    source = input("请选择 [1/2，默认 1]: ").strip()

    audio_url = None
    audio_base64 = None

    if source == "2":
        audio_url = input("请输入音频 URL: ").strip()
        if not audio_url:
            print("URL 不能为空。")
            return
    else:
        audio_path = input("请输入音频文件路径: ").strip().strip('"')
        if not os.path.isfile(audio_path):
            print(f"文件不存在: {audio_path}")
            return
        # 检查文件大小限制 (50MB)
        file_size = os.path.getsize(audio_path)
        if file_size > 50 * 1024 * 1024:
            print(f"文件过大 ({file_size / 1024 / 1024:.1f}MB)，最大支持 50MB")
            return
        print("正在编码音频...")
        with open(audio_path, "rb") as f:
            audio_base64 = base64.b64encode(f.read()).decode("utf-8")

    # 可选歌词
    lyrics = input("\n请输入歌词（直接回车跳过，将自动从音频中提取）: ").strip()

    payload = {
        "model": "music-cover",
        "prompt": prompt,
        "output_format": "url",
        "audio_setting": {
            "sample_rate": 44100,
            "bitrate": 256000,
            "format": "mp3",
        },
    }

    if audio_url:
        payload["audio_url"] = audio_url
    elif audio_base64:
        payload["audio_base64"] = audio_base64

    if lyrics:
        payload["lyrics"] = lyrics

    print("\n正在生成翻唱（可能需要较长时间）...")
    try:
        data = api_post("/v1/music_generation", payload)
        music_data = data.get("data", {})
        extra_info = data.get("extra_info", {})

        duration_ms = extra_info.get("music_duration", 0)
        duration_s = duration_ms / 1000 if duration_ms else 0
        print(f"  生成完成！时长: {duration_s:.1f}s")

        # 保存音频
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
            print("  未获取到音频数据。")

    except Exception as e:
        print(f"[错误] {e}")


def music_generation_with_lyrics(prompt="", lyrics=""):
    """从歌词生成模块直接调用的快捷入口"""
    print_separator("音乐生成 (从歌词生成调用)")

    if not prompt:
        prompt = input("请输入音乐描述 (风格、情绪、场景): ").strip()

    payload = {
        "model": "music-2.6",
        "prompt": prompt,
        "lyrics": lyrics,
        "output_format": "url",
        "audio_setting": {
            "sample_rate": 44100,
            "bitrate": 256000,
            "format": "mp3",
        },
    }

    print("\n正在生成音乐（可能需要较长时间）...")
    try:
        data = api_post("/v1/music_generation", payload)
        music_data = data.get("data", {})
        extra_info = data.get("extra_info", {})

        duration_ms = extra_info.get("music_duration", 0)
        duration_s = duration_ms / 1000 if duration_ms else 0
        print(f"  生成完成！时长: {duration_s:.1f}s")

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
            print("  未获取到音频数据。")

    except Exception as e:
        print(f"[错误] {e}")


def run(mode="gen"):
    if mode == "cover":
        music_cover()
    else:
        music_generation()


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "gen"
    run(mode)
