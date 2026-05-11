"""CLI and interactive wrappers for the bundled official MiniMax MCP tools."""

from __future__ import annotations

import os

from minimax_mcp_bridge import load_official_server, result_text, run_mcp_server


DEFAULT_PREVIEW_TEXT = "你好，这是一段由 MiniMax 生成的试听音频。"
DEFAULT_TOKEN_PLAN_SPEECH_MODEL = "speech-2.8-hd"


def output_dir(name: str) -> str:
    from config import OUTPUT_DIR

    path = os.path.join(OUTPUT_DIR, name)
    os.makedirs(path, exist_ok=True)
    return path


def print_result(result) -> None:
    print(result_text(result))


def list_voices(voice_type: str = "all"):
    server = load_official_server(resource_mode="local")
    return server.list_voices(voice_type=voice_type)


def text_to_audio(
    text: str,
    voice_id: str | None = None,
    model: str | None = DEFAULT_TOKEN_PLAN_SPEECH_MODEL,
    speed: float = 1.0,
    vol: float = 5.0,
    output_directory: str | None = None,
):
    server = load_official_server(resource_mode="local")
    kwargs = {
        "text": text,
        "speed": speed,
        "vol": vol,
        "output_directory": output_directory or output_dir("speech"),
    }
    if voice_id:
        kwargs["voice_id"] = voice_id
    kwargs["model"] = model or DEFAULT_TOKEN_PLAN_SPEECH_MODEL
    return server.text_to_audio(**kwargs)


def voice_clone(
    voice_id: str,
    file: str,
    text: str = DEFAULT_PREVIEW_TEXT,
    is_url: bool = False,
    output_directory: str | None = None,
):
    server = load_official_server(resource_mode="local")
    return server.voice_clone(
        voice_id=voice_id,
        file=file,
        text=text,
        is_url=is_url,
        output_directory=output_directory or output_dir("voices"),
    )


def voice_design(
    prompt: str,
    preview_text: str = DEFAULT_PREVIEW_TEXT,
    voice_id: str | None = None,
    output_directory: str | None = None,
):
    server = load_official_server(resource_mode="local")
    return server.voice_design(
        prompt=prompt,
        preview_text=preview_text,
        voice_id=voice_id or None,
        output_directory=output_directory or output_dir("voices"),
    )


def generate_video(
    prompt: str,
    model: str | None = None,
    first_frame_image: str | None = None,
    duration: int | None = None,
    resolution: str | None = None,
    output_directory: str | None = None,
    async_mode: bool = False,
):
    server = load_official_server(resource_mode="local")
    return server.generate_video(
        model=model or server.DEFAULT_T2V_MODEL,
        prompt=prompt,
        first_frame_image=first_frame_image or None,
        duration=duration,
        resolution=resolution,
        output_directory=output_directory or output_dir("videos"),
        async_mode=async_mode,
    )


def query_video_generation(task_id: str, output_directory: str | None = None):
    server = load_official_server(resource_mode="local")
    return server.query_video_generation(
        task_id=task_id,
        output_directory=output_directory or output_dir("videos"),
    )


def play_audio(input_file_path: str, is_url: bool = False):
    server = load_official_server(resource_mode="local")
    return server.play_audio(input_file_path=input_file_path, is_url=is_url)


def _ask(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{prompt}{suffix}: ").strip()
    return value or default


def _ask_float(prompt: str, default: float) -> float:
    value = _ask(prompt, str(default))
    try:
        return float(value)
    except ValueError:
        return default


def _ask_int(prompt: str) -> int | None:
    value = _ask(prompt)
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def run() -> None:
    while True:
        print()
        print("=" * 50)
        print("MiniMax 官方 MCP 扩展")
        print("=" * 50)
        print("  1. 启动 MCP Server")
        print("  2. 查询音色列表")
        print("  3. 文本转语音")
        print("  4. 音色设计")
        print("  5. 音色克隆")
        print("  6. 视频生成")
        print("  7. 查询视频任务")
        print("  8. 播放音频")
        print("  0. 返回")
        choice = _ask("请选择功能")

        try:
            if choice == "1":
                print("正在启动 MCP Server，关闭窗口或 Ctrl+C 可停止。")
                run_mcp_server()
                return
            if choice == "2":
                print_result(list_voices(_ask("音色类型 all/system/voice_cloning", "all")))
            elif choice == "3":
                text = _ask("要转成语音的文本")
                if text:
                    print_result(text_to_audio(
                        text=text,
                        voice_id=_ask("Voice ID，留空使用官方默认"),
                        model=_ask("模型", DEFAULT_TOKEN_PLAN_SPEECH_MODEL),
                        speed=_ask_float("语速", 1.0),
                        vol=_ask_float("音量", 5.0),
                    ))
            elif choice == "4":
                prompt = _ask("音色描述")
                if prompt:
                    print_result(voice_design(
                        prompt=prompt,
                        preview_text=_ask("试听文本", DEFAULT_PREVIEW_TEXT),
                        voice_id=_ask("指定 Voice ID，留空自动生成"),
                    ))
            elif choice == "5":
                voice_id = _ask("新 Voice ID")
                file = _ask("音频文件路径或 URL")
                if voice_id and file:
                    print_result(voice_clone(
                        voice_id=voice_id,
                        file=file,
                        text=_ask("试听文本", DEFAULT_PREVIEW_TEXT),
                        is_url=file.startswith(("http://", "https://")),
                    ))
            elif choice == "6":
                prompt = _ask("视频 prompt")
                if prompt:
                    async_mode = _ask("异步提交 y/n", "n").lower() == "y"
                    print_result(generate_video(
                        prompt=prompt,
                        model=_ask("模型，留空使用官方默认"),
                        first_frame_image=_ask("首帧图片路径/URL，留空为文生视频"),
                        duration=_ask_int("时长，留空使用模型默认"),
                        resolution=_ask("分辨率，留空使用模型默认"),
                        async_mode=async_mode,
                    ))
            elif choice == "7":
                task_id = _ask("视频 task_id")
                if task_id:
                    print_result(query_video_generation(task_id))
            elif choice == "8":
                path = _ask("音频文件路径或 URL")
                if path:
                    print_result(play_audio(path, is_url=path.startswith(("http://", "https://"))))
            elif choice == "0":
                return
            else:
                print("无效选择。")
        except Exception as exc:
            print(f"ERROR: {exc}")


if __name__ == "__main__":
    run()
