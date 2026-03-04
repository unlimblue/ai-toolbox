#!/usr/bin/env python3
"""简化测试 - 验证代码结构和语法."""

import ast
import sys
from pathlib import Path


def check_syntax(filepath: Path) -> bool:
    """检查 Python 文件语法."""
    try:
        with open(filepath, "r") as f:
            ast.parse(f.read())
        return True
    except SyntaxError as e:
        print(f"❌ 语法错误: {filepath} - {e}")
        return False


def main() -> int:
    """主函数."""
    print("="*60)
    print("AI-Toolbox 代码结构验证")
    print("="*60)

    src_dir = Path(__file__).parent.parent / "src"
    all_files = list(src_dir.rglob("*.py"))

    print(f"\n发现 {len(all_files)} 个 Python 文件")
    print()

    passed = 0
    failed = 0

    for filepath in sorted(all_files):
        if check_syntax(filepath):
            rel_path = filepath.relative_to(src_dir.parent)
            print(f"✓ {rel_path}")
            passed += 1
        else:
            failed += 1

    print()
    print("="*60)
    print(f"结果: {passed} 通过, {failed} 失败")
    print("="*60)

    # 检查关键文件
    print("\n关键文件检查:")
    key_files = [
        "src/ai_toolbox/providers/__init__.py",
        "src/ai_toolbox/cli/main.py",
        "src/ai_toolbox/api/server.py",
        "src/ai_toolbox/discord_bot/bot.py",
        "src/ai_toolbox/discord_bot/README.md",
    ]

    for f in key_files:
        path = Path(__file__).parent.parent / f
        exists = "✓" if path.exists() else "✗"
        print(f"{exists} {f}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())