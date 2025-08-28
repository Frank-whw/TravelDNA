#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置验证工具 - 检查API密钥和环境配置
"""

import os
import requests
from config import Config

def validate_api_keys():
    """验证所有API密钥"""
    print("🔐 API密钥配置验证")
    print("=" * 50)
    
    results = {}
    
    # 1. 检查环境变量是否配置
    keys_to_check = {
        "天气API": Config.AMAP_WEATHER_API_KEY,
        "交通API": Config.AMAP_TRAFFIC_API_KEY,
        "导航API": Config.AMAP_NAVIGATION_API_KEY,
        "POI搜索API": Config.AMAP_POI_API_KEY,
    }
    
    print("📋 环境变量检查:")
    for name, key in keys_to_check.items():
        if key:
            print(f"  ✅ {name}: 已配置 ({key[:10]}...)")
            results[name] = True
        else:
            print(f"  ❌ {name}: 未配置")
            results[name] = False
    
    print()
    
    # 2. 测试API密钥有效性
    print("🔑 API密钥有效性测试:")
    
    # 测试天气API
    if results["天气API"]:
        try:
            url = "https://restapi.amap.com/v3/weather/weatherInfo"
            params = {
                "key": Config.AMAP_WEATHER_API_KEY,
                "city": "310000",  # 上海
                "extensions": "base"
            }
            response = requests.get(url, params=params, timeout=5)
            data = response.json()
            
            if data.get("status") == "1":
                print(f"  ✅ 天气API: 有效")
            else:
                print(f"  ❌ 天气API: 无效 - {data.get('info', '未知错误')}")
        except Exception as e:
            print(f"  ❌ 天气API: 测试失败 - {e}")
    
    # 测试POI搜索API
    if results["POI搜索API"]:
        try:
            url = "https://restapi.amap.com/v5/place/text"
            params = {
                "key": Config.AMAP_POI_API_KEY,
                "keywords": "咖啡",
                "region": "上海",
                "page_size": 1
            }
            response = requests.get(url, params=params, timeout=5)
            data = response.json()
            
            if data.get("status") == "1":
                print(f"  ✅ POI搜索API: 有效")
            else:
                print(f"  ❌ POI搜索API: 无效 - {data.get('info', '未知错误')}")
        except Exception as e:
            print(f"  ❌ POI搜索API: 测试失败 - {e}")
    
    # 测试导航API
    if results["导航API"]:
        try:
            url = "https://restapi.amap.com/v5/direction/driving"
            params = {
                "key": Config.AMAP_NAVIGATION_API_KEY,
                "origin": "121.475224,31.232275",  # 人民广场
                "destination": "121.484429,31.240791",  # 外滩
                "output": "json"
            }
            response = requests.get(url, params=params, timeout=5)
            data = response.json()
            
            if data.get("status") == "1":
                print(f"  ✅ 导航API: 有效")
            else:
                print(f"  ❌ 导航API: 无效 - {data.get('info', '未知错误')}")
        except Exception as e:
            print(f"  ❌ 导航API: 测试失败 - {e}")
    
    print()
    print("📊 验证总结:")
    valid_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    print(f"  配置完成: {valid_count}/{total_count}")
    
    if valid_count == total_count:
        print("  🎉 所有API密钥配置正确！")
        return True
    else:
        print("  ⚠️ 请完善API密钥配置")
        print("\n📝 配置步骤:")
        print("  1. 复制 env.example 为 .env")
        print("  2. 在 .env 文件中填入真实API密钥")
        print("  3. 重新运行此验证脚本")
        return False

def setup_demo_keys():
    """设置演示用的API密钥（仅用于测试）"""
    print("\n🧪 设置演示API密钥...")
    
    # 注意：这些是示例密钥，实际使用时请替换为您的真实密钥
    demo_keys = {
        'AMAP_WEATHER_API_KEY': 'eabe457b791e74946b2aeb6a9106b17a',
        'AMAP_TRAFFIC_API_KEY': '425125fef7e244aa380807946ec48776',
        'AMAP_NAVIGATION_API_KEY': '95dfa5cfda994230af9b6ab64de4b84b',
        'AMAP_POI_API_KEY': 'f2b480c54a1805d9f6d5aa7b845fc360',
        'AMAP_TRAFFIC_SECURITY_KEY': '5247e3cdc28d7acfaa1f4504e09a4da1'
    }
    
    for key, value in demo_keys.items():
        os.environ[key] = value
        print(f"  ✅ 设置 {key}")
    
    print("  🎯 演示密钥设置完成")

if __name__ == "__main__":
    # 首先尝试正常验证
    is_valid = validate_api_keys()
    
    if not is_valid:
        print("\n" + "="*50)
        print("🔧 尝试使用演示密钥进行测试...")
        setup_demo_keys()
        print()
        validate_api_keys()

