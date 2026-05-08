import os
import re
import sys
from config import OUTPUT_DIR, SCRIPT_DIR
from utils import api_post, poll_task, get_file_download_url, download_file, print_separator

MAX_CHARS = 49000  # 留一点余量，API 限制 50000 字符
NOVEL_INPUT_DIR = os.path.join(SCRIPT_DIR, "novel_input")
os.makedirs(NOVEL_INPUT_DIR, exist_ok=True)

# TTS 模型选项
TTS_MODELS = [
    ("speech-2.8-hd",    "2.8 HD - 最新高清音质"),
    ("speech-2.8-turbo", "2.8 Turbo - 极速版"),
    ("speech-2.6-hd",    "2.6 HD - 高清"),
    ("speech-2.6-turbo", "2.6 Turbo - 快速"),
]


def select_voice():
    """直接输入 Voice ID（参考 Voice ID.md 音色列表）"""
    print("\n请输入 Voice ID（参考项目目录下 Voice ID.md 中的音色列表）")
    print("  示例: male-qn-qingse, female-shaonv, female-yujie, male-qn-jingying ...")
    voice_id = input("Voice ID: ").strip()
    if not voice_id:
        voice_id = "male-qn-qingse"
        print(f"  未输入，使用默认: {voice_id}")
    else:
        print(f"  已选择: {voice_id}")
    return voice_id


def select_model():
    print("\n可用 TTS 模型:")
    for i, (mid, desc) in enumerate(TTS_MODELS, 1):
        print(f"  {i}. {desc} ({mid})")
    choice = input(f"请选择模型 [1-{len(TTS_MODELS)}，默认 1]: ").strip()
    idx = int(choice) - 1 if choice.isdigit() and 1 <= int(choice) <= len(TTS_MODELS) else 0
    model = TTS_MODELS[idx][0]
    print(f"已选择: {TTS_MODELS[idx][1]}")
    return model


def read_novel(file_path):
    """读取小说文本文件"""
    encodings = ["utf-8", "utf-8-sig", "gbk", "gb2312", "gb18030"]
    for enc in encodings:
        try:
            with open(file_path, "r", encoding=enc) as f:
                return f.read()
        except (UnicodeDecodeError, UnicodeError):
            continue
    raise RuntimeError(f"无法读取文件 {file_path}，请确保文件编码为 UTF-8 或 GBK")


def split_by_chapters(text):
    """
    按章节标记拆分文本。
    支持: 第X章、第X节、第X回、Chapter X 等
    """
    # 章节正则 — 匹配行首的章节标记
    chapter_pattern = re.compile(
        r'(?=^(第.{1,10}[章节回篇卷]|Chapter\s+\d+|CHAPTER\s+\d+))',
        re.MULTILINE
    )

    positions = [m.start() for m in chapter_pattern.finditer(text)]

    if len(positions) < 2:
        return None  # 没有检测到足够的章节标记

    chunks = []
    for i, pos in enumerate(positions):
        end = positions[i + 1] if i + 1 < len(positions) else len(text)
        chunk_text = text[pos:end].strip()
        if chunk_text:
            # 提取章节名作为标签
            first_line = chunk_text.split("\n")[0].strip()
            label = re.sub(r'[\\/:*?"<>|]', '_', first_line[:30])
            chunks.append((label, chunk_text))

    # 处理第一个章节标记之前的前言/序言
    if positions[0] > 0:
        prologue = text[:positions[0]].strip()
        if prologue:
            chunks.insert(0, ("序言", prologue))

    return chunks


def split_by_length(text, max_chars=MAX_CHARS):
    """按字符上限拆分文本，尽量在段落边界处断开"""
    if len(text) <= max_chars:
        return [("全文", text)]

    chunks = []
    remaining = text
    part_num = 1

    while remaining:
        if len(remaining) <= max_chars:
            chunks.append((f"部分_{part_num:03d}", remaining))
            break

        # 在 max_chars 范围内找最后一个段落分隔
        cut_pos = max_chars
        # 尝试找 \n\n（段落边界）
        last_para = remaining[:max_chars].rfind("\n\n")
        if last_para > max_chars // 2:
            cut_pos = last_para + 2
        else:
            # 退而求其次找 \n
            last_newline = remaining[:max_chars].rfind("\n")
            if last_newline > max_chars // 2:
                cut_pos = last_newline + 1

        chunk = remaining[:cut_pos].strip()
        if chunk:
            chunks.append((f"部分_{part_num:03d}", chunk))
            part_num += 1
        remaining = remaining[cut_pos:]

    return chunks


def split_novel(text):
    """
    智能拆分小说文本：
    1. 先尝试按章节拆分
    2. 对超长章节进行二次拆分
    3. 无章节标记则按字符上限拆分
    """
    # 尝试按章节拆分
    chapters = split_by_chapters(text)

    if chapters:
        print(f"  检测到 {len(chapters)} 个章节")
        # 对超长章节二次拆分
        final_chunks = []
        for label, chunk_text in chapters:
            if len(chunk_text) <= MAX_CHARS:
                final_chunks.append((label, chunk_text))
            else:
                print(f"  章节「{label}」过长 ({len(chunk_text)} 字符)，进行二次拆分")
                sub_chunks = split_by_length(chunk_text)
                for i, (_, sub_text) in enumerate(sub_chunks, 1):
                    final_chunks.append((f"{label}_P{i}", sub_text))
        return final_chunks
    else:
        print("  未检测到章节标记，按长度拆分")
        return split_by_length(text)


def create_tts_task(text, voice_id, model):
    """创建异步 TTS 任务"""
    payload = {
        "model": model,
        "text": text,
        "voice_setting": {
            "voice_id": voice_id,
            "speed": 1.0,
            "vol": 5.0,
            "pitch": 0,
        },
        "audio_setting": {
            "audio_sample_rate": 44100,
            "bitrate": 256000,
            "format": "mp3",
            "channel": 1,
        },
        "language_boost": "Chinese",
    }
    data = api_post("/v1/t2a_async_v2", payload)
    task_id = data.get("task_id")
    file_id = data.get("file_id")
    usage = data.get("usage_characters", 0)
    print(f"  任务已创建: task_id={task_id}, 计费字符数={usage}")
    return task_id, file_id


def run():
    print_separator("小说转语音 (Novel → Audio)")

    # 扫描 novel_input 文件夹中的 .md 文件
    md_files = [f for f in os.listdir(NOVEL_INPUT_DIR) if f.lower().endswith(".md")]
    if not md_files:
        print(f"\n  novel_input 文件夹为空，请将 .md 小说文件放入以下目录：")
        print(f"  {NOVEL_INPUT_DIR}")
        return

    md_files.sort()
    print(f"\n  在 novel_input 中找到 {len(md_files)} 个文件：")
    for i, name in enumerate(md_files, 1):
        print(f"    {i}. {name}")

    choice = input(f"\n请选择文件 [1-{len(md_files)}]: ").strip()
    idx = int(choice) - 1 if choice.isdigit() and 1 <= int(choice) <= len(md_files) else 0
    file_path = os.path.join(NOVEL_INPUT_DIR, md_files[idx])
    print(f"  已选择: {md_files[idx]}")

    # 读取文本
    print("\n正在读取文件...")
    text = read_novel(file_path)
    print(f"  文件总长度: {len(text)} 字符")

    # 选择音色和模型
    voice_id = select_voice()
    model = select_model()

    # 语速设置
    speed_input = input("\n请输入语速 [0.5-2.0，默认 1.0]: ").strip()
    try:
        speed = float(speed_input)
        speed = max(0.5, min(2.0, speed))
    except (ValueError, TypeError):
        speed = 1.0
    print(f"语速: {speed}")

    # 拆分文本
    print("\n正在分析文本结构...")
    chunks = split_novel(text)
    print(f"  共 {len(chunks)} 个片段待处理")

    # 确认
    total_chars = sum(len(c[1]) for c in chunks)
    print(f"\n  总计字符数: {total_chars}")
    print(f"  预估片段: {len(chunks)} 个")
    confirm = input("\n确认开始合成？(y/n，默认 y): ").strip().lower()
    if confirm == "n":
        print("已取消。")
        return

    # 创建输出目录
    novel_name = os.path.splitext(os.path.basename(file_path))[0]
    novel_dir = os.path.join(OUTPUT_DIR, novel_name)
    os.makedirs(novel_dir, exist_ok=True)

    # 逐片处理
    success_count = 0
    fail_count = 0

    for i, (label, chunk_text) in enumerate(chunks, 1):
        print(f"\n{'─'*40}")
        print(f"处理片段 [{i}/{len(chunks)}]: {label} ({len(chunk_text)} 字符)")

        try:
            # 创建任务
            task_id, file_id = create_tts_task(chunk_text, voice_id, model)

            # 轮询等待完成
            print("  等待合成完成...")
            status, result_file_id = poll_task(task_id, interval=5, timeout=900)
            print(f"  合成完成！")

            # 获取下载链接
            download_url = get_file_download_url(result_file_id)

            # 下载音频
            save_path = os.path.join(novel_dir, f"{i:03d}_{label}.mp3")
            download_file(download_url, save_path)
            success_count += 1

        except Exception as e:
            print(f"  [失败] {e}")
            fail_count += 1

    # 总结
    print(f"\n{'='*40}")
    print(f"处理完成！")
    print(f"  成功: {success_count}/{len(chunks)}")
    if fail_count:
        print(f"  失败: {fail_count}/{len(chunks)}")
    print(f"  输出目录: {novel_dir}")


if __name__ == "__main__":
    run()
