#!/usr/bin/env python3
"""
交互式脚本：帮助更新 .env 文件中的 DATABASE_URL
"""
from pathlib import Path
from urllib.parse import quote

def update_env_file():
    script_dir = Path(__file__).parent
    env_path = script_dir / ".env"
    
    print("=" * 60)
    print("Supabase 数据库连接字符串更新工具")
    print("=" * 60)
    print()
    print("请从 Supabase Dashboard 获取连接字符串：")
    print("  1. 登录 https://supabase.com/dashboard")
    print("  2. 进入 Settings → Database → Connection Pooling")
    print("  3. 复制 Connection string（推荐使用连接池）")
    print()
    print("或者：")
    print("  1. Settings → Database → Connection String")
    print("  2. 选择 URI 格式并复制")
    print()
    print("-" * 60)
    
    # 读取现有的 .env 文件
    if env_path.exists():
        current_content = env_path.read_text(encoding='utf-8')
        print("\n当前 .env 文件内容：")
        print("-" * 60)
        for line in current_content.strip().split('\n'):
            if 'DATABASE_URL' in line:
                # 隐藏密码显示
                if '@' in line:
                    parts = line.split('@')
                    print(f"{parts[0]}@***")
                else:
                    print(line)
            else:
                print(line)
        print("-" * 60)
    
    print("\n请输入新的 DATABASE_URL：")
    print("（可以直接粘贴完整的连接字符串，或输入 'skip' 跳过）")
    new_url = input("> ").strip()
    
    if new_url.lower() == 'skip':
        print("已跳过更新")
        return
    
    if not new_url:
        print("❌ 连接字符串不能为空")
        return
    
    if not new_url.startswith('postgresql://'):
        print("⚠️  警告：连接字符串应该以 'postgresql://' 开头")
        confirm = input("是否继续？(y/n): ").strip().lower()
        if confirm != 'y':
            return
    
    # 更新 .env 文件
    if env_path.exists():
        lines = current_content.strip().split('\n')
        updated = False
        new_lines = []
        
        for line in lines:
            if line.startswith('DATABASE_URL='):
                new_lines.append(f'DATABASE_URL={new_url}')
                updated = True
            else:
                new_lines.append(line)
        
        if not updated:
            new_lines.insert(0, f'DATABASE_URL={new_url}')
    else:
        new_lines = [
            f'DATABASE_URL={new_url}',
            'SQLALCHEMY_TRACK_MODIFICATIONS=False',
            'SECRET_KEY=dev-secret-key-change-in-production'
        ]
    
    # 写入文件
    env_path.write_text('\n'.join(new_lines) + '\n', encoding='utf-8')
    print("\n✅ .env 文件已更新！")
    print("\n新的连接字符串（隐藏密码）：")
    if '@' in new_url:
        parts = new_url.split('@')
        print(f"  {parts[0]}@***")
    else:
        print(f"  {new_url}")
    print("\n请运行 'python test_connection.py' 测试连接")

if __name__ == "__main__":
    try:
        update_env_file()
    except KeyboardInterrupt:
        print("\n\n已取消")
    except Exception as e:
        print(f"\n❌ 错误: {e}")

