import sys
import anthropic
from config import API_KEY, ANTHROPIC_BASE_URL
from utils import print_separator

# 可选模型列表
MODELS = [
    ("MiniMax-M2.7",           "最强模型，自我迭代 (~60 TPS)"),
    ("MiniMax-M2.7-highspeed", "M2.7 极速版 (~100 TPS)"),
    ("MiniMax-M2.5",           "性价比之选 (~60 TPS)"),
    ("MiniMax-M2.5-highspeed", "M2.5 极速版 (~100 TPS)"),
]


def select_model():
    print("\n可用模型:")
    for i, (name, desc) in enumerate(MODELS, 1):
        print(f"  {i}. {name} — {desc}")
    choice = input(f"请选择模型 [1-{len(MODELS)}，默认 1]: ").strip()
    idx = int(choice) - 1 if choice.isdigit() and 1 <= int(choice) <= len(MODELS) else 0
    model = MODELS[idx][0]
    print(f"已选择: {model}\n")
    return model


def run():
    print_separator("文本对话 (AI Chat)")

    model = select_model()

    system_prompt = input("请输入系统提示词（直接回车使用默认）: ").strip()
    if not system_prompt:
        system_prompt = "你是一个有用的AI助手，请用中文回答问题。"
    print(f"系统提示: {system_prompt}\n")

    client = anthropic.Anthropic(
        base_url=ANTHROPIC_BASE_URL,
        api_key=API_KEY,
    )

    messages = []
    print("开始对话（输入 exit 或 quit 退出）：")
    print("-" * 40)

    while True:
        try:
            user_input = input("\n你: ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit", "退出"):
            break

        messages.append({
            "role": "user",
            "content": [{"type": "text", "text": user_input}],
        })

        print("\nAI: ", end="", flush=True)

        try:
            stream = client.messages.create(
                model=model,
                max_tokens=4096,
                system=system_prompt,
                messages=messages,
                stream=True,
            )

            assistant_text = ""
            for chunk in stream:
                if chunk.type == "content_block_delta":
                    if hasattr(chunk, "delta") and chunk.delta:
                        if chunk.delta.type == "thinking_delta":
                            pass  # 不显示思考过程
                        elif chunk.delta.type == "text_delta":
                            text = chunk.delta.text
                            if text:
                                print(text, end="", flush=True)
                                assistant_text += text

            print()  # 换行

            if assistant_text:
                messages.append({
                    "role": "assistant",
                    "content": [{"type": "text", "text": assistant_text}],
                })

        except anthropic.APIError as e:
            print(f"\n[API 错误] {e}")
        except Exception as e:
            print(f"\n[错误] {e}")

    print("\n对话结束。")


if __name__ == "__main__":
    run()
