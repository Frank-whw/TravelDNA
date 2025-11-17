#!/usr/bin/env python3
"""测试 .env 文件加载"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 获取脚本所在目录
script_dir = Path(__file__).parent
env_path = script_dir / ".env"

print(f"脚本目录: {script_dir}")
print(f".env 文件路径: {env_path}")
print(f".env 文件是否存在: {env_path.exists()}")

# 加载 .env 文件（使用 override=True）
load_dotenv(env_path, override=True)

# 调试：打印所有环境变量，查找包含 DATABASE 的
print("\n环境变量中包含 'DATABASE' 的键:")
for key in os.environ.keys():
    if 'DATABASE' in key:
        print(f"  {repr(key)}")

# 读取 DATABASE_URL
database_url = os.getenv("DATABASE_URL")
if database_url:
    print(f"\n✅ DATABASE_URL 加载成功!")
    # 隐藏密码显示
    if "@" in database_url:
        parts = database_url.split("@")
        print(f"   数据库: {parts[-1] if parts else 'N/A'}")
else:
    print("\n❌ DATABASE_URL 未找到!")
    print(f"   当前环境变量: {list(os.environ.keys())}")

