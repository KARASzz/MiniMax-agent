"""Local browser for the bundled MiniMax official skills package."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
SKILLS_ROOT = PROJECT_DIR / "skills"
SKILLS_DIR = SKILLS_ROOT / "skills"
README_ZH = SKILLS_ROOT / "README_zh.md"


@dataclass
class SkillInfo:
    name: str
    description: str
    source: str
    path: str


def _plain_markdown(text: str) -> str:
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _read_zh_table() -> dict[str, SkillInfo]:
    if not README_ZH.exists():
        return {}

    skills: dict[str, SkillInfo] = {}
    for line in README_ZH.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| `"):
            continue
        columns = [part.strip() for part in line.strip().strip("|").split("|")]
        if len(columns) < 3:
            continue
        name = columns[0].strip("` ")
        path = SKILLS_DIR / name / "SKILL.md"
        skills[name] = SkillInfo(
            name=name,
            description=_plain_markdown(columns[1]),
            source=_plain_markdown(columns[2]),
            path=str(path),
        )
    return skills


def _frontmatter_value(text: str, key: str) -> str:
    pattern = rf"^{re.escape(key)}:\s*(.*)$"
    match = re.search(pattern, text, flags=re.MULTILINE)
    if not match:
        return ""
    value = match.group(1).strip()
    if value in {">", "|"}:
        start = match.end()
        lines = []
        for line in text[start:].splitlines():
            if line and not line.startswith((" ", "\t")):
                break
            lines.append(line.strip())
        return _plain_markdown(" ".join(lines))
    return _plain_markdown(value.strip('"'))


def discover_skills() -> list[SkillInfo]:
    table = _read_zh_table()
    discovered: dict[str, SkillInfo] = {}

    if SKILLS_DIR.exists():
        for skill_file in sorted(SKILLS_DIR.glob("*/SKILL.md")):
            content = skill_file.read_text(encoding="utf-8", errors="replace")
            folder_name = skill_file.parent.name
            name = folder_name if folder_name in table else (_frontmatter_value(content, "name") or folder_name)
            description = _frontmatter_value(content, "description")
            existing = table.get(name)
            discovered[name] = SkillInfo(
                name=name,
                description=(existing.description if existing else description),
                source=(existing.source if existing else "Unknown"),
                path=str(skill_file),
            )

    for name, item in table.items():
        discovered.setdefault(name, item)

    return [discovered[name] for name in sorted(discovered)]


def find_skill(name: str) -> SkillInfo:
    for skill in discover_skills():
        if skill.name == name:
            return skill
    names = ", ".join(skill.name for skill in discover_skills())
    raise SystemExit(f"未找到技能: {name}\n可用技能: {names}")


def print_list(as_json: bool = False) -> None:
    skills = discover_skills()
    if as_json:
        print(json.dumps([asdict(skill) for skill in skills], ensure_ascii=False, indent=2))
        return

    print("MiniMax 官方 Skills 技能包")
    print(f"目录: {SKILLS_ROOT}")
    print()
    for index, skill in enumerate(skills, 1):
        print(f"{index:02d}. {skill.name} [{skill.source}]")
        if skill.description:
            print(f"    {skill.description}")
    print()
    print("查看单个技能: python cli.py skills <技能名>")


def print_detail(name: str, lines: int = 80) -> None:
    skill = find_skill(name)
    print(f"技能: {skill.name}")
    print(f"来源: {skill.source}")
    print(f"路径: {skill.path}")
    if skill.description:
        print(f"简介: {skill.description}")
    print()

    path = Path(skill.path)
    if not path.exists():
        print("未找到 SKILL.md 文件。")
        return

    content_lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    preview = "\n".join(content_lines[:lines])
    print(preview)
    if len(content_lines) > lines:
        print()
        print(f"... 已截断，完整文件共 {len(content_lines)} 行。")


def print_install_info() -> None:
    print("官方 Skills 已保留在项目目录下:")
    print(f"  {SKILLS_DIR}")
    print()
    print("如果要让 Codex 在全局发现这些技能，可把该目录链接到 ~/.agents/skills。")
    print("macOS/Linux 示例:")
    print(f"  mkdir -p ~/.agents/skills")
    print(f"  ln -s \"{SKILLS_DIR}\" ~/.agents/skills/minimax-skills")
    print()
    print("Cursor 可在设置中把 skills 路径指向:")
    print(f"  {SKILLS_DIR}")


def run_interactive() -> None:
    skills = discover_skills()
    if not skills:
        print(f"未发现技能目录: {SKILLS_DIR}")
        return

    while True:
        print()
        print("=" * 50)
        print("MiniMax 官方 Skills 技能包")
        print("=" * 50)
        for index, skill in enumerate(skills, 1):
            print(f"  {index:2d}. {skill.name}")
        print("   i. 接入说明")
        print("   0. 返回")
        choice = input("请选择技能编号: ").strip().lower()
        if choice == "0":
            return
        if choice == "i":
            print()
            print_install_info()
            input("\n按回车继续...")
            continue
        if not choice.isdigit():
            print("无效选择。")
            continue
        index = int(choice) - 1
        if not 0 <= index < len(skills):
            print("编号超出范围。")
            continue
        print()
        print_detail(skills[index].name)
        input("\n按回车继续...")


def main() -> None:
    parser = argparse.ArgumentParser(description="查看项目内置 MiniMax 官方 Skills 技能包")
    parser.add_argument("skill", nargs="?", help="技能名；留空则列出全部技能")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出技能列表")
    parser.add_argument("--lines", type=int, default=80, help="查看技能时显示的 SKILL.md 行数")
    parser.add_argument("--interactive", action="store_true", help="打开交互式技能菜单")
    parser.add_argument("--install-info", action="store_true", help="显示接入到 Codex/Cursor 的路径说明")
    args = parser.parse_args()

    if args.install_info:
        print_install_info()
    elif args.interactive:
        run_interactive()
    elif args.skill:
        print_detail(args.skill, lines=args.lines)
    else:
        print_list(as_json=args.json)


if __name__ == "__main__":
    main()
