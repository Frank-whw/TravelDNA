#!/usr/bin/env python3
"""修复 .env 文件的 BOM 问题"""
from pathlib import Path

env_path = Path(__file__).parent / ".env"

print(f"正在修复: {env_path}")

# 读取文件内容（使用 utf-8-sig 自动处理 BOM）
with open(env_path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

# 检查原始文件是否有 BOM
with open(env_path, 'rb') as f:
    raw_content = f.read()
    has_bom = raw_content.startswith(b'\xef\xbb\xbf')
    print(f"检测到 BOM: {has_bom}")

# 以 UTF-8 without BOM 格式重新写入
with open(env_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ .env 文件已修复（移除 BOM）")
print(f"\n文件内容预览:")
print("-" * 50)
print(content[:200])
print("-" * 50)

