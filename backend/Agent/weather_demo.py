#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
天气API演示脚本
展示集成的天气功能
"""

import sys
import os
import json
from datetime import datetime

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mcp_services import WeatherMCPService, MCPServiceManager
from city_code_loader import get_city_code

def demo_weather_api():
    """演示天气API功能"""
    print("🌤️ 上海旅游天气API演示")
    print("=" * 60)
    print(f"⏰ 演示时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 演示城市代码查询
    print("🏙️ 城市代码查询演示")
    print("-" * 30)
    cities = ["上海", "上海市", "北京", "杭州", "南京"]
    for city in cities:
        code = get_city_code(city)
        print(f"📍 {city:6} -> {code}")
    print()
    
    # 演示天气查询
    print("🌦️ 天气信息查询演示")
    print("-" * 30)
    attractions = ["外滩", "东方明珠", "迪士尼", "豫园", "南京路"]
    
    for attraction in attractions:
        print(f"🎯 查询景点: {attraction}")
        weather_data = WeatherMCPService.get_weather(attraction, "上海")
        
        # 显示关键信息
        print(f"   🌡️ 温度: {weather_data.get('temperature', '未知')}")
        print(f"   ☁️ 天气: {weather_data.get('weather', '未知')}")
        print(f"   💧 湿度: {weather_data.get('humidity', '未知')}")
        print(f"   🌬️ 风力: {weather_data.get('wind', '未知')}")
        print(f"   💡 建议: {weather_data.get('recommendation', '无')}")
        print(f"   📡 数据源: {weather_data.get('api_source', '未知')}")
        print()
    
    # 演示综合信息
    print("📊 综合实时信息演示")
    print("-" * 30)
    
    manager = MCPServiceManager()
    attraction = "外滩"
    
    print(f"🎯 获取 {attraction} 的综合信息...")
    comprehensive_info = manager.get_comprehensive_info(attraction)
    
    # 格式化显示
    formatted_info = manager.format_response(comprehensive_info, f"{attraction}实时信息")
    print(formatted_info)
    
    print("\n" + "=" * 60)
    print("✅ 演示完成！")
    print()
    print("📝 API使用说明:")
    print("1. 直接调用: WeatherMCPService.get_weather('外滩', '上海')")
    print("2. 综合信息: MCPServiceManager().get_comprehensive_info('外滩')")
    print("3. HTTP API: GET /api/weather/外滩?city=上海")
    print("4. 预报信息: GET /api/weather/上海?forecast=true")

def demo_api_usage():
    """演示API使用方法"""
    print("\n🔧 API使用代码示例")
    print("=" * 60)
    
    print("Python代码示例:")
    print("-" * 30)
    
    code_example = '''
# 导入模块
from mcp_services import WeatherMCPService, MCPServiceManager

# 获取单个景点天气
weather = WeatherMCPService.get_weather("外滩", "上海")
print(f"外滩天气: {weather['weather']} {weather['temperature']}")

# 获取综合实时信息
manager = MCPServiceManager()
info = manager.get_comprehensive_info("东方明珠")
print(manager.format_response(info, "东方明珠信息"))

# 获取天气预报
forecast = WeatherMCPService.get_weather_forecast("上海", 3)
print(f"天气预报: {forecast}")
'''
    
    print(code_example)
    
    print("\nHTTP API调用示例:")
    print("-" * 30)
    
    api_examples = '''
# 获取景点天气
curl "http://localhost:5000/api/weather/外滩?city=上海"

# 获取天气预报
curl "http://localhost:5000/api/weather/上海?forecast=true"

# 获取综合实时信息
curl "http://localhost:5000/api/realtime/外滩"

# 获取服务状态
curl "http://localhost:5000/api/status"
'''
    
    print(api_examples)

if __name__ == "__main__":
    try:
        demo_weather_api()
        demo_api_usage()
        
        print("\n🎉 天气API功能演示成功！")
        print("💡 系统已经成功集成高德地图天气API")
        print("🔄 即使API调用失败，系统也会提供可靠的默认数据")
        
    except Exception as e:
        print(f"❌ 演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

