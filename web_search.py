"""
MiniMax Token Plan - 网络搜索
使用 coding-plan-search 额度进行网络搜索
"""

import httpx
from config import BASE_URL, get_headers
from utils import print_separator


def search(query):
    """调用网络搜索 API"""
    url = f"{BASE_URL}/v1/coding_plan/search"
    payload = {"q": query}
    resp = httpx.post(url, json=payload, headers=get_headers(), timeout=30)
    resp.raise_for_status()
    data = resp.json()
    base_resp = data.get("base_resp", {})
    if base_resp.get("status_code", 0) != 0:
        raise RuntimeError(f"API 错误 [{base_resp.get('status_code')}]: {base_resp.get('status_msg', '未知错误')}")
    return data


def display_results(data):
    """格式化显示搜索结果"""
    organic = data.get("organic", [])
    related = data.get("related_searches", [])

    if not organic:
        print("  未找到相关结果。")
        return related

    for i, item in enumerate(organic, 1):
        title = item.get("title", "无标题")
        link = item.get("link", "")
        snippet = item.get("snippet", "")
        date = item.get("date", "")

        print(f"  [{i}] {title}")
        if date:
            print(f"      日期: {date}")
        print(f"      链接: {link}")
        if snippet:
            print(f"      摘要: {snippet}")
        print()

    if related:
        print("  ── 相关搜索 ──")
        for j, r in enumerate(related, 1):
            print(f"    {j}. {r.get('query', '')}")
        print()

    return related


def run():
    """交互式网络搜索主循环"""
    print_separator("网络搜索 (Web Search)")
    print("  输入搜索关键词进行搜索，输入 q 退出。")
    print("  搜索后可输入相关搜索的编号继续搜索。")
    print()

    related_searches = []

    while True:
        try:
            query = input("搜索> ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not query:
            continue
        if query.lower() == "q":
            break

        # 如果输入的是数字且有相关搜索，使用相关搜索
        if query.isdigit() and related_searches:
            idx = int(query) - 1
            if 0 <= idx < len(related_searches):
                query = related_searches[idx].get("query", query)
                print(f"  → 搜索: {query}")
            else:
                print("  编号超出范围，请直接输入关键词。")
                continue

        try:
            print()
            print("  搜索中...")
            data = search(query)
            print()
            related_searches = display_results(data)
        except httpx.HTTPStatusError as e:
            print(f"  HTTP 错误: {e.response.status_code} - {e.response.text[:200]}")
        except Exception as e:
            print(f"  搜索失败: {e}")
        print()

    print("已退出网络搜索。")


if __name__ == "__main__":
    run()
