#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
天气API功能测试脚本
测试高德地图天气API集成
"""

import sys
import os
import json
import requests
from datetime import datetime

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mcp_services import WeatherMCPService, MCPServiceManager
from city_code_loader import CityCodeLoader, get_city_code, get_city_info
from config import Config

def test_city_code_loader():
    """测试城市代码加载器"""
    print("=" * 50)
    print("🏙️ 测试城市代码加载器")
    print("=" * 50)
    
    loader = CityCodeLoader()
    
    # 测试加载
    success = loader.load_city_codes()
    print(f"📁 加载结果: {'成功' if success else '失败'}")
    
    if success:
        # 测试统计信息
        stats = loader.get_statistics()
        print(f"📊 统计信息:")
        print(f"  - 已加载: {stats['loaded']}")
        print(f"  - 城市数量: {stats['total_cities']}")
        print(f"  - 文件路径: {stats['file_path']}")
        print(f"  - 示例城市: {stats['sample_cities'][:5]}")
        
        # 测试城市查询
        test_cities = ['上海', '上海市', '北京', '杭州']
        print(f"\n🔍 测试城市查询:")
        for city in test_cities:
            code = loader.get_city_code(city)
            info = loader.get_city_info(city)
            print(f"  {city} -> 代码: {code}")
            if info:
                print(f"    详细信息: {info}")
    
    return success

def test_amap_weather_api():
    """测试高德天气API直接调用"""
    print("\n" + "=" * 50)
    print("🌤️ 测试高德天气API直接调用")
    print("=" * 50)
    
    # 测试上海天气
    city_code = get_city_code("上海")
    print(f"🏙️ 上海城市代码: {city_code}")
    
    if not city_code:
        print("❌ 无法获取上海城市代码")
        return False
    
    # 当前天气
    print(f"\n📡 调用高德天气API...")
    try:
        params = {
            "city": city_code,
            "key": Config.AMAP_API_KEY,
            "extensions": "base",
            "output": "json"
        }
        
        response = requests.get(Config.AMAP_WEATHER_URL, params=params, timeout=10)
        print(f"🔗 请求URL: {response.url}")
        print(f"📊 响应状态: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📄 API响应:")
            print(json.dumps(data, ensure_ascii=False, indent=2))
            
            if data.get("status") == "1":
                print("✅ API调用成功")
                return True
            else:
                print(f"❌ API返回错误: {data.get('info', '未知错误')}")
                return False
        else:
            print(f"❌ HTTP请求失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

def test_weather_service():
    """测试WeatherMCPService"""
    print("\n" + "=" * 50)
    print("🌦️ 测试WeatherMCPService")
    print("=" * 50)
    
    # 测试当前天气
    print("🔍 测试获取当前天气...")
    weather_data = WeatherMCPService.get_weather("外滩", "上海")
    print(f"📄 天气数据:")
    print(json.dumps(weather_data, ensure_ascii=False, indent=2))
    
    # 测试天气预报
    print(f"\n🔍 测试获取天气预报...")
    forecast_data = WeatherMCPService.get_weather_forecast("上海", 3)
    print(f"📄 预报数据:")
    print(json.dumps(forecast_data, ensure_ascii=False, indent=2))
    
    return weather_data.get('api_source') == 'amap'

def test_mcp_service_manager():
    """测试MCP服务管理器"""
    print("\n" + "=" * 50)
    print("🎯 测试MCP服务管理器")
    print("=" * 50)
    
    manager = MCPServiceManager()
    
    # 测试综合信息获取
    print("🔍 测试获取综合信息...")
    comprehensive_info = manager.get_comprehensive_info("东方明珠")
    print(f"📄 综合信息:")
    print(json.dumps(comprehensive_info, ensure_ascii=False, indent=2))
    
    # 测试格式化响应
    print(f"\n🔍 测试格式化响应...")
    formatted_response = manager.format_response(comprehensive_info, "东方明珠天气怎么样？")
    print(f"📝 格式化响应:")
    print(formatted_response)
    
    return True

def test_api_endpoints():
    """测试API端点（需要服务器运行）"""
    print("\n" + "=" * 50)
    print("🌐 测试API端点")
    print("=" * 50)
    
    base_url = "http://localhost:5000"
    
    # 测试健康检查
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print("✅ 健康检查端点正常")
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接到API服务器: {e}")
        print("💡 请先运行 'python api_server.py' 启动服务器")
        return False
    
    # 测试天气端点
    try:
        response = requests.get(f"{base_url}/api/weather/外滩?city=上海", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ 天气API端点正常")
            print(f"📄 响应数据:")
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            print(f"❌ 天气API失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 天气API请求异常: {e}")
        return False
    
    # 测试天气预报端点
    try:
        response = requests.get(f"{base_url}/api/weather/上海?forecast=true", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ 天气预报API端点正常")
            print(f"📄 预报数据:")
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            print(f"❌ 天气预报API失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 天气预报API请求异常: {e}")
        return False
    
    return True

def main():
    """主测试函数"""
    print("🚀 开始天气API功能测试")
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    test_results = {}
    
    # 1. 测试城市代码加载器
    test_results['city_loader'] = test_city_code_loader()
    
    # 2. 测试高德天气API直接调用
    test_results['amap_api'] = test_amap_weather_api()
    
    # 3. 测试天气服务
    test_results['weather_service'] = test_weather_service()
    
    # 4. 测试MCP服务管理器
    test_results['mcp_manager'] = test_mcp_service_manager()
    
    # 5. 测试API端点
    test_results['api_endpoints'] = test_api_endpoints()
    
    # 总结测试结果
    print("\n" + "=" * 50)
    print("📊 测试结果总结")
    print("=" * 50)
    
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result)
    
    for test_name, result in test_results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    print(f"\n🎯 总体结果: {passed_tests}/{total_tests} 项测试通过")
    
    if passed_tests == total_tests:
        print("🎉 所有测试通过！天气API功能集成成功！")
    else:
        print("⚠️ 部分测试失败，请检查相关配置和依赖")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

