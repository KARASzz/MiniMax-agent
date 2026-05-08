import os
import sys

# ============================================================
# MiniMax API 配置
# ============================================================

API_KEY = os.environ.get("MINIMAX_API_KEY", "")

if not API_KEY:
    print("=" * 50)
    print("错误：未检测到环境变量 MINIMAX_API_KEY")
    print()
    print("请先设置 API 密钥，方法如下：")
    print()
    print("方法一（推荐）：Windows 系统设置")
    print("  1. 按 Win+R，输入 sysdm.cpl，回车")
    print("  2. 点击「高级」→「环境变量」")
    print("  3. 在「用户变量」中新建：")
    print("     变量名: MINIMAX_API_KEY")
    print("     变量值: 你的API密钥")
    print("  4. 确定保存，重启终端")
    print()
    print("方法二：PowerShell 命令")
    print('  [Environment]::SetEnvironmentVariable("MINIMAX_API_KEY", "你的密钥", "User")')
    print("=" * 50)
    sys.exit(1)

# 基础 URL
BASE_URL = "https://api.minimaxi.com"
ANTHROPIC_BASE_URL = "https://api.minimaxi.com/anthropic"

# 输出目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def get_headers():
    """返回通用 API 请求头"""
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
