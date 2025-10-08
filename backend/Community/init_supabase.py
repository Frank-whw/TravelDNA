#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Supabase 数据库初始化脚本
使用 Supabase 客户端进行数据库操作
"""

import sys
import os
from dotenv import load_dotenv
from supabase import create_client, Client
import json

# 加载环境变量
load_dotenv()

# Supabase 配置
SUPABASE_URL = "https://hhgcwivtjpyofheowlqa.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhoZ2N3aXZ0anB5b2ZoZW93bHFhIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1OTMyMzA3MCwiZXhwIjoyMDc0ODk5MDcwfQ.nuo1WkrLrZ7ay9as3VpgZbDd9XSaD7E5rs1SG0zmJrI"

def get_supabase_client() -> Client:
    """获取 Supabase 客户端"""
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

def create_tables():
    """创建数据库表结构"""
    print("🔧 创建数据库表结构...")
    
    supabase = get_supabase_client()
    
    # 使用 Supabase 客户端直接创建表（通过插入操作来隐式创建）
    # 或者我们可以使用 SQL 执行，但需要确保有正确的权限
    
    print("✅ 使用 Supabase 客户端创建表结构...")
    
    # 先尝试创建一个简单的测试表来验证权限
    try:
        # 测试基本的表操作
        test_result = supabase.table('mbti_types').select('*').limit(1).execute()
        print("ℹ️  表已存在，跳过创建")
    except Exception as e:
        if 'not found' in str(e).lower() or 'pgrst205' in str(e).lower():
            print("⚠️  表不存在，需要通过 Supabase Dashboard 创建表结构")
            print("请在 Supabase Dashboard 中执行以下 SQL:")
            
            sql_statements = [
                # MBTI 类型表
                """
CREATE TABLE IF NOT EXISTS mbti_types (
    id SERIAL PRIMARY KEY,
    type_code VARCHAR(4) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT
);
                """,
                # 兴趣爱好表
                """
CREATE TABLE IF NOT EXISTS hobbies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    category VARCHAR(50)
);
                """,
                # 旅行目的地表
                """
CREATE TABLE IF NOT EXISTS destinations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    country VARCHAR(100),
    description TEXT
);
                """,
                # 作息习惯表
                """
CREATE TABLE IF NOT EXISTS schedules (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT
);
                """,
                # 预算范围表
                """
CREATE TABLE IF NOT EXISTS budgets (
    id SERIAL PRIMARY KEY,
    range_name VARCHAR(100) UNIQUE NOT NULL,
    min_amount INTEGER,
    max_amount INTEGER,
    description TEXT
);
                """,
                # 用户表
                """
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    mbti_type_id INTEGER REFERENCES mbti_types(id),
    preferred_destination_id INTEGER REFERENCES destinations(id),
    schedule_id INTEGER REFERENCES schedules(id),
    budget_id INTEGER REFERENCES budgets(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
                """,
                # 用户兴趣爱好关联表
                """
CREATE TABLE IF NOT EXISTS user_hobbies (
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    hobby_id INTEGER REFERENCES hobbies(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, hobby_id)
);
                """,
                # 团队表
                """
CREATE TABLE IF NOT EXISTS teams (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    destination_id INTEGER REFERENCES destinations(id),
    max_members INTEGER DEFAULT 6,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
                """,
                # 团队成员关联表
                """
CREATE TABLE IF NOT EXISTS team_members (
    team_id INTEGER REFERENCES teams(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (team_id, user_id)
);
                """,
                # 匹配记录表
                """
CREATE TABLE IF NOT EXISTS match_records (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    matched_user_id INTEGER REFERENCES users(id),
    compatibility_score FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
                """,
                # 消息表
                """
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    sender_id INTEGER REFERENCES users(id),
    receiver_id INTEGER REFERENCES users(id),
    team_id INTEGER REFERENCES teams(id),
    content TEXT NOT NULL,
    message_type VARCHAR(50) DEFAULT 'text',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
                """
            ]
            
            print("\n=== 请在 Supabase Dashboard 的 SQL Editor 中执行以下 SQL ===")
            for i, sql in enumerate(sql_statements, 1):
                print(f"\n-- 步骤 {i}:")
                print(sql.strip())
            print("\n=== SQL 执行完毕后，重新运行此脚本 ===")
            return False
        else:
            raise e

def init_default_data():
    """初始化默认数据"""
    print("📊 初始化默认数据...")
    
    supabase = get_supabase_client()
    
    try:
        # MBTI 类型数据
        mbti_data = [
            {'type_code': 'INTJ', 'name': '建筑师', 'description': '富有想象力和战略性的思想家'},
            {'type_code': 'INTP', 'name': '思想家', 'description': '具有创造性的思想家，对知识有着不可抑制的渴望'},
            {'type_code': 'ENTJ', 'name': '指挥官', 'description': '大胆、富有想象力、意志强烈的领导者'},
            {'type_code': 'ENTP', 'name': '辩论家', 'description': '聪明好奇的思想家，不会拒绝智力上的挑战'}
        ]
        
        # 检查是否已有数据
        existing_mbti = supabase.table('mbti_types').select('*').limit(1).execute()
        if not existing_mbti.data:
            supabase.table('mbti_types').insert(mbti_data).execute()
            print("✅ MBTI 类型数据初始化完成")
        else:
            print("ℹ️  MBTI 类型数据已存在")
        
        # 兴趣爱好数据
        hobby_data = [
            {'name': '摄影', 'category': '艺术'},
            {'name': '徒步', 'category': '运动'},
            {'name': '美食', 'category': '生活'},
            {'name': '音乐', 'category': '艺术'}
        ]
        
        existing_hobbies = supabase.table('hobbies').select('*').limit(1).execute()
        if not existing_hobbies.data:
            supabase.table('hobbies').insert(hobby_data).execute()
            print("✅ 兴趣爱好数据初始化完成")
        else:
            print("ℹ️  兴趣爱好数据已存在")
        
        # 旅行目的地数据
        destination_data = [
            {'name': '巴黎', 'country': '法国', 'description': '浪漫之都'},
            {'name': '东京', 'country': '日本', 'description': '现代与传统的完美结合'},
            {'name': '纽约', 'country': '美国', 'description': '不夜城'},
            {'name': '伦敦', 'country': '英国', 'description': '历史悠久的国际大都市'}
        ]
        
        existing_destinations = supabase.table('destinations').select('*').limit(1).execute()
        if not existing_destinations.data:
            supabase.table('destinations').insert(destination_data).execute()
            print("✅ 旅行目的地数据初始化完成")
        else:
            print("ℹ️  旅行目的地数据已存在")
        
        # 作息习惯数据
        schedule_data = [
            {'name': '早起型', 'description': '喜欢早起，精力充沛的上午'},
            {'name': '夜猫子型', 'description': '夜晚更有活力和创造力'},
            {'name': '规律型', 'description': '作息时间规律，生活有序'},
            {'name': '灵活型', 'description': '作息时间灵活，适应性强'}
        ]
        
        existing_schedules = supabase.table('schedules').select('*').limit(1).execute()
        if not existing_schedules.data:
            supabase.table('schedules').insert(schedule_data).execute()
            print("✅ 作息习惯数据初始化完成")
        else:
            print("ℹ️  作息习惯数据已存在")
        
        # 预算范围数据
        budget_data = [
            {'range_name': '经济型', 'min_amount': 0, 'max_amount': 5000, 'description': '适合预算有限的旅行者'},
            {'range_name': '舒适型', 'min_amount': 5000, 'max_amount': 15000, 'description': '平衡价格与舒适度'},
            {'range_name': '豪华型', 'min_amount': 15000, 'max_amount': 50000, 'description': '追求高品质旅行体验'},
            {'range_name': '奢华型', 'min_amount': 50000, 'max_amount': None, 'description': '顶级奢华旅行体验'}
        ]
        
        existing_budgets = supabase.table('budgets').select('*').limit(1).execute()
        if not existing_budgets.data:
            supabase.table('budgets').insert(budget_data).execute()
            print("✅ 预算范围数据初始化完成")
        else:
            print("ℹ️  预算范围数据已存在")
            
    except Exception as e:
        print(f"❌ 初始化默认数据时出错: {str(e)}")

def check_connection():
    """检查数据库连接"""
    print("🔍 检查 Supabase 连接...")
    
    try:
        supabase = get_supabase_client()
        
        # 尝试简单的 RPC 调用来测试连接
        result = supabase.rpc('version').execute()
        
        print("✅ Supabase 连接成功！")
        print(f"📊 数据库可正常访问")
        return True
        
    except Exception as e:
        # 如果 version RPC 不存在，尝试其他方式
        try:
            # 尝试查询系统表
            result = supabase.from_('information_schema.tables').select('table_name').limit(1).execute()
            print("✅ Supabase 连接成功！")
            print(f"📊 数据库可正常访问")
            return True
        except Exception as e2:
            print(f"❌ 连接失败: {str(e)}")
            return False

def show_tables():
    """显示数据库表结构"""
    print("📋 数据库表信息:")
    
    supabase = get_supabase_client()
    
    tables = [
        'mbti_types', 'hobbies', 'destinations', 'schedules', 'budgets',
        'users', 'user_hobbies', 'teams', 'team_members', 'match_records', 'messages'
    ]
    
    for table_name in tables:
        try:
            result = supabase.table(table_name).select('*').limit(1).execute()
            count_result = supabase.table(table_name).select('*', count='exact').execute()
            count = count_result.count if hasattr(count_result, 'count') else 'Unknown'
            print(f"  ✅ {table_name}: {count} 条记录")
        except Exception as e:
            print(f"  ❌ {table_name}: 无法访问 ({str(e)})")

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python init_supabase.py init    # 初始化数据库")
        print("  python init_supabase.py check   # 检查连接")
        print("  python init_supabase.py tables  # 显示表信息")
        return
    
    command = sys.argv[1]
    
    if command == 'init':
        print("🚀 开始初始化 Supabase 数据库...")
        # 直接开始创建表，不需要预先检查连接
        try:
            create_tables()
            init_default_data()
            show_tables()
            print("\n🎉 Supabase 数据库初始化完成！")
        except Exception as e:
            print(f"\n❌ 初始化失败: {str(e)}")
            print("请检查 Supabase 配置和网络连接")
    
    elif command == 'check':
        check_connection()
    
    elif command == 'tables':
        if check_connection():
            show_tables()
    
    else:
        print(f"❌ 未知命令: {command}")

if __name__ == '__main__':
    main()