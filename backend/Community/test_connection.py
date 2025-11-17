#!/usr/bin/env python3
"""测试数据库连接的诊断脚本"""
import os
import socket
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
script_dir = Path(__file__).parent
env_path = script_dir / ".env"
load_dotenv(env_path, override=True)

database_url = os.getenv("DATABASE_URL")
if not database_url:
    print("❌ DATABASE_URL 未找到")
    exit(1)

print(f"✅ DATABASE_URL: {database_url}")
print()

# 解析连接字符串
try:
    # 提取主机和端口
    # 格式: postgresql://user:password@host:port/database
    parts = database_url.replace("postgresql://", "").split("@")
    if len(parts) < 2:
        print("❌ 连接字符串格式不正确")
        exit(1)
    
    host_port_db = parts[1].split("/")
    host_port = host_port_db[0]
    
    if ":" in host_port:
        host, port = host_port.split(":")
        port = int(port)
    else:
        host = host_port
        port = 5432
    
    print(f"📍 数据库主机: {host}")
    print(f"📍 端口: {port}")
    print()
    
    # 测试 DNS 解析（支持 IPv4 和 IPv6）
    print("🔍 测试 DNS 解析...")
    try:
        # 尝试 IPv4
        try:
            ipv4 = socket.gethostbyname(host)
            print(f"✅ DNS 解析成功 (IPv4): {host} -> {ipv4}")
        except socket.gaierror:
            # 如果 IPv4 失败，尝试 IPv6
            try:
                import socket as sock
                ipv6 = sock.getaddrinfo(host, None, socket.AF_INET6)[0][4][0]
                print(f"✅ DNS 解析成功 (IPv6): {host} -> {ipv6}")
                print("   ⚠️  注意：只返回 IPv6 地址，可能需要启用 IPv6 或使用连接池")
            except Exception as e:
                raise socket.gaierror(f"无法解析 {host} (IPv4 和 IPv6 都失败)")
    except socket.gaierror as e:
        print(f"❌ DNS 解析失败: {e}")
        print("   可能原因：")
        print("   1. 网络连接问题")
        print("   2. 主机名不正确")
        print("   3. 防火墙或代理阻止 DNS 查询")
        print("   4. 只返回 IPv6 地址但系统不支持 IPv6")
        print("\n   建议：使用 Supabase 连接池（通常同时支持 IPv4 和 IPv6）")
        exit(1)
    
    print()
    
    # 测试 TCP 连接
    print(f"🔍 测试 TCP 连接到 {host}:{port}...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)  # 5秒超时
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"✅ TCP 连接成功: {host}:{port}")
        else:
            print(f"❌ TCP 连接失败: 错误代码 {result}")
            print("   可能原因：")
            print("   1. 端口被防火墙阻止")
            print("   2. Supabase 数据库需要 IP 白名单（检查 Supabase Dashboard -> Settings -> Database -> Connection Pooling）")
            print("   3. 网络连接问题")
    except Exception as e:
        print(f"❌ TCP 连接异常: {e}")
    
    print()
    
    # 测试 PostgreSQL 连接
    print("🔍 测试 PostgreSQL 连接...")
    try:
        import psycopg
        # 如果主机只有 IPv6，尝试强制使用 IPv6
        # psycopg 应该能自动处理，但如果失败可以尝试指定连接选项
        conn_params = {
            "connect_timeout": 10,
            # 如果只有 IPv6，让 psycopg 自动处理
        }
        with psycopg.connect(database_url, **conn_params) as conn:
            print("✅ PostgreSQL 连接成功！")
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                version = cur.fetchone()
                print(f"   数据库版本: {version[0][:50]}...")
    except psycopg.OperationalError as e:
        error_msg = str(e)
        print(f"❌ PostgreSQL 连接失败: {e}")
        print()
        if "getaddrinfo" in error_msg or "11001" in error_msg:
            print("⚠️  DNS/网络连接问题：")
            print("   1. 主机可能只返回 IPv6 地址，但系统可能无法使用 IPv6")
            print("   2. 建议使用 Supabase 连接池（通常同时支持 IPv4 和 IPv6）")
            print("   3. 从 Supabase Dashboard -> Settings -> Database -> Connection Pooling")
            print("      获取连接池连接字符串（端口 6543）")
            print()
            print("   如果无法访问 Dashboard（不是项目成员）：")
            print("   - 联系项目管理员获取连接池连接字符串")
            print("   - 或请求添加为 Supabase 项目协作者")
        else:
            print("可能的原因：")
            print("1. Supabase 数据库需要 IP 白名单设置")
            print("   请访问: Supabase Dashboard -> Settings -> Database -> Connection Pooling")
            print("2. 检查连接池配置是否正确")
            print("3. 确认数据库密码是否正确")
    except psycopg.Error as e:
        print(f"❌ PostgreSQL 错误: {e}")
    except Exception as e:
        print(f"❌ 连接异常: {e}")

except Exception as e:
    print(f"❌ 解析连接字符串时出错: {e}")

