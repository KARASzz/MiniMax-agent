import os
import sys
from config import OUTPUT_DIR
from utils import api_post, print_separator


def run():
    print_separator("歌词生成 (Lyrics Generation)")

    print("\n生成模式:")
    print("  1. 创作完整歌曲 (write_full_song)")
    print("  2. 编辑/续写歌词 (edit)")
    mode_choice = input("请选择 [1/2，默认 1]: ").strip()
    mode = "edit" if mode_choice == "2" else "write_full_song"

    prompt = input("\n请输入提示词（歌曲主题/风格/编辑指令，直接回车随机生成）: ").strip()

    title = input("请输入歌曲标题（直接回车自动生成）: ").strip()

    payload = {
        "mode": mode,
    }

    if prompt:
        payload["prompt"] = prompt
    if title:
        payload["title"] = title

    # 编辑模式需要已有歌词
    if mode == "edit":
        print("\n请输入已有歌词（输入空行结束）:")
        lines = []
        while True:
            line = input()
            if line == "":
                break
            lines.append(line)
        existing_lyrics = "\n".join(lines)
        if existing_lyrics:
            payload["lyrics"] = existing_lyrics

    print("\n正在生成歌词...")
    try:
        data = api_post("/v1/lyrics_generation", payload)

        song_title = data.get("song_title", "未命名")
        style_tags = data.get("style_tags", "")
        lyrics = data.get("lyrics", "")

        print(f"\n{'─'*40}")
        print(f"  歌名: {song_title}")
        print(f"  风格: {style_tags}")
        print(f"{'─'*40}")
        print(lyrics)
        print(f"{'─'*40}")

        # 保存到文件
        save = input("\n是否保存到文件？(y/n，默认 y): ").strip().lower()
        if save != "n":
            lyrics_dir = os.path.join(OUTPUT_DIR, "lyrics")
            os.makedirs(lyrics_dir, exist_ok=True)
            safe_title = "".join(c if c.isalnum() or c in " _-" else "_" for c in song_title)
            save_path = os.path.join(lyrics_dir, f"{safe_title}.txt")
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(f"歌名: {song_title}\n")
                f.write(f"风格: {style_tags}\n")
                f.write(f"{'─'*40}\n")
                f.write(lyrics)
            print(f"  已保存: {save_path}")

        # 询问是否直接用于音乐生成
        use_for_music = input("\n是否使用此歌词生成音乐？(y/n，默认 n): ").strip().lower()
        if use_for_music == "y":
            from music_gen import music_generation_with_lyrics
            music_generation_with_lyrics(prompt=style_tags, lyrics=lyrics)

    except Exception as e:
        print(f"[错误] {e}")


if __name__ == "__main__":
    run()
