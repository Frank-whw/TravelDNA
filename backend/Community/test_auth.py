#!/usr/bin/env python3
"""
测试注册和登录功能的脚本
使用方法：
    python test_auth.py register  # 测试注册
    python test_auth.py login     # 测试登录
    python test_auth.py both      # 测试注册和登录
"""
import sys
import requests
import json
from pathlib import Path

# 服务器地址（根据实际情况修改）
BASE_URL = "http://localhost:5000/api/v1"

def test_register():
    """测试用户注册"""
    print("=" * 60)
    print("测试用户注册")
    print("=" * 60)
    
    # 测试数据
    test_data = {
        "email": "test@example.com",
        "password": "test123456",
        "name": "测试用户",
        "gender": "男",
        "age": 25,
        "bio": "这是一个测试用户"
    }
    
    print(f"\n请求 URL: {BASE_URL}/auth/register")
    print(f"请求数据: {json.dumps(test_data, ensure_ascii=False, indent=2)}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/register",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        print(f"\n响应状态码: {response.status_code}")
        print(f"响应内容:")
        print(json.dumps(response.json(), ensure_ascii=False, indent=2))
        
        if response.status_code == 201:
            print("\n✅ 注册成功！")
            return response.json().get("data", {}).get("id")
        else:
            print(f"\n❌ 注册失败: {response.json().get('message', '未知错误')}")
            return None
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ 连接失败：无法连接到服务器 {BASE_URL}")
        print("   请确保服务器已启动：python run.py")
        return None
    except Exception as e:
        print(f"\n❌ 请求异常: {e}")
        return None

def test_login(email_or_phone=None, password="test123456"):
    """测试用户登录"""
    print("\n" + "=" * 60)
    print("测试用户登录")
    print("=" * 60)
    
    if not email_or_phone:
        email_or_phone = "test@example.com"
    
    # 测试数据
    test_data = {
        "account": email_or_phone,  # 可以是邮箱或手机号
        "password": password
    }
    
    print(f"\n请求 URL: {BASE_URL}/auth/login")
    print(f"请求数据: {json.dumps(test_data, ensure_ascii=False, indent=2)}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        print(f"\n响应状态码: {response.status_code}")
        print(f"响应内容:")
        print(json.dumps(response.json(), ensure_ascii=False, indent=2))
        
        if response.status_code == 200:
            print("\n✅ 登录成功！")
            user_data = response.json().get("data", {})
            print(f"   用户ID: {user_data.get('id')}")
            print(f"   用户名: {user_data.get('name')}")
            return True
        else:
            print(f"\n❌ 登录失败: {response.json().get('message', '未知错误')}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ 连接失败：无法连接到服务器 {BASE_URL}")
        print("   请确保服务器已启动：python run.py")
        return False
    except Exception as e:
        print(f"\n❌ 请求异常: {e}")
        return False

def test_invalid_login():
    """测试错误密码登录"""
    print("\n" + "=" * 60)
    print("测试错误密码登录（应失败）")
    print("=" * 60)
    
    test_data = {
        "account": "test@example.com",
        "password": "wrongpassword"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        print(f"\n响应状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        
        if response.status_code == 401:
            print("\n✅ 测试通过：错误密码被正确拒绝")
            return True
        else:
            print("\n❌ 测试失败：应该返回 401 错误")
            return False
    except Exception as e:
        print(f"\n❌ 请求异常: {e}")
        return False

def main():
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
    else:
        command = "both"
    
    print("\n" + "=" * 60)
    print("用户注册和登录功能测试")
    print("=" * 60)
    print(f"\n服务器地址: {BASE_URL}")
    print("提示: 如果服务器地址不同，请修改脚本中的 BASE_URL 变量")
    print()
    
    if command == "register":
        test_register()
    elif command == "login":
        test_login()
    elif command == "both":
        # 先测试注册
        user_id = test_register()
        
        if user_id:
            # 等待一下，确保数据已保存
            import time
            time.sleep(1)
            
            # 测试登录
            test_login()
            
            # 测试错误密码
            test_invalid_login()
    else:
        print(f"未知命令: {command}")
        print("用法: python test_auth.py [register|login|both]")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n测试已取消")

