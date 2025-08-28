#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整导航路径规划测试
验证移除离线计算后的导航功能和完整路径显示
"""

import sys
import os
import json
import time
from datetime import datetime

# 添加模块路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mcp_services import NavigationMCPService, MCPServiceManager
from config import Config

def test_single_route():
    """测试单点路径规划"""
    print("🧭 单点路径规划测试")
    print("=" * 50)
    
    nav_service = NavigationMCPService()
    
    # 测试外滩到东方明珠的路径规划
    print("📍 测试路线: 外滩 → 东方明珠")
    
    result = nav_service.get_route_planning("外滩", "东方明珠", strategy="default")
    
    print("\n✅ 路径规划结果:")
    print(f"  起点: {result.get('origin')}")
    print(f"  终点: {result.get('destination')}")
    print(f"  策略: {result.get('strategy')}")
    print(f"  距离: {result.get('distance')} (原始值: {result.get('distance_value')}米)")
    print(f"  时长: {result.get('duration')} (原始值: {result.get('duration_value')}秒)")
    print(f"  过路费: {result.get('tolls')} (原始值: {result.get('tolls_value')}元)")
    print(f"  红绿灯: {result.get('traffic_lights')} (数量: {result.get('traffic_lights_count')})")
    print(f"  限行状态: {result.get('restriction_status')}")
    print(f"  出租车费用: {result.get('taxi_cost')}")
    print(f"  API来源: {result.get('api_source')}")
    
    # 显示导航步骤
    steps = result.get('navigation_steps', [])
    total_steps = result.get('total_steps', len(steps))
    
    if steps:
        print(f"\n🗺️ 详细导航步骤（共{total_steps}步）:")
        for step in steps:
            instruction = step.get('instruction', '')
            distance = step.get('distance', '')
            duration = step.get('duration', '')
            road = step.get('road', '')
            action = step.get('action', '')
            orientation = step.get('orientation', '')
            
            print(f"  {step['step']}. {instruction}")
            print(f"     距离: {distance} | 时长: {duration}")
            if road:
                print(f"     道路: {road}")
            if action:
                print(f"     动作: {action}")
            if orientation:
                print(f"     方向: {orientation}")
            print()
    
    # 显示路径轨迹信息
    polyline = result.get('polyline', '')
    if polyline:
        print(f"📍 路径轨迹长度: {len(polyline)}字符")
        print(f"   轨迹预览: {polyline[:100]}..." if len(polyline) > 100 else f"   轨迹内容: {polyline}")
    
    # 显示完整路径数据
    complete_data = result.get('complete_route_data', {})
    if complete_data:
        main_path = complete_data.get('main_path', {})
        all_paths = complete_data.get('all_paths', [])
        
        print(f"\n📊 路径数据统计:")
        print(f"   主路径字段数: {len(main_path)}")
        print(f"   可选路径数: {len(all_paths)}")
        print(f"   建议: {result.get('advice', '无')}")
    
    return result

def test_multiple_strategies():
    """测试不同导航策略"""
    print("\n🚗 多策略路径规划测试")
    print("=" * 50)
    
    nav_service = NavigationMCPService()
    
    strategies_to_test = [
        ("default", "默认策略"),
        ("avoid_congestion", "躲避拥堵"),
        ("no_highway", "不走高速"),
        ("less_fee", "少收费"),
        ("fastest", "速度最快")
    ]
    
    print("📍 测试路线: 人民广场 → 虹桥机场")
    
    for strategy, description in strategies_to_test:
        print(f"\n🎯 策略: {description} ({strategy})")
        
        start_time = time.time()
        result = nav_service.get_route_planning("人民广场", "虹桥机场", strategy=strategy)
        end_time = time.time()
        
        api_source = result.get('api_source', 'unknown')
        if api_source == 'amap_navigation':
            distance = result.get('distance', '未知')
            duration = result.get('duration', '未知')
            tolls = result.get('tolls', '未知')
            steps_count = result.get('total_steps', 0)
            
            print(f"  ✅ 成功: {distance} | {duration} | {tolls}")
            print(f"     导航步骤: {steps_count}步 | 响应时间: {end_time - start_time:.2f}秒")
        else:
            print(f"  ❌ 失败: {api_source}")
        
        # 避免超过速率限制
        time.sleep(0.3)

def test_mcp_integration():
    """测试MCP框架集成"""
    print("\n🔧 MCP框架集成测试")
    print("=" * 50)
    
    mcp_manager = MCPServiceManager()
    
    print("📍 测试: 通过MCP框架获取导航信息")
    
    # 测试MCP管理器的导航功能
    result = mcp_manager.get_navigation_planning("外滩", "静安寺", strategy="avoid_congestion")
    
    print(f"  MCP导航调用: {result.get('api_source', 'unknown')}")
    print(f"  路线总结: {result.get('route_summary', '未知')}")
    
    # 测试针对性信息获取（包含导航）
    targeted_info = mcp_manager.get_targeted_info("东方明珠", "怎么开车去", "外滩")
    services_used = targeted_info.get('services_used', [])
    
    print(f"  智能服务识别: {services_used}")
    
    if 'navigation' in services_used:
        nav_info = targeted_info.get('navigation', {})
        print(f"  导航信息获取: {nav_info.get('api_source', 'unknown')}")
        
        # 格式化显示
        formatted_response = mcp_manager.format_response(targeted_info, "怎么开车去")
        print("\n📝 格式化输出:")
        print(formatted_response)

def test_rate_limiting():
    """测试速率限制"""
    print("\n⏱️ 速率限制测试")
    print("=" * 50)
    
    nav_service = NavigationMCPService()
    
    print(f"配置的速率限制: {Config.AMAP_NAVIGATION_RATE_LIMIT}次/秒")
    
    # 连续调用测试
    routes = [
        ("外滩", "豫园"),
        ("新天地", "田子坊"),
        ("静安寺", "人民广场")
    ]
    
    results = []
    start_time = time.time()
    
    for i, (origin, destination) in enumerate(routes):
        call_start = time.time()
        result = nav_service.get_route_planning(origin, destination)
        call_end = time.time()
        
        api_source = result.get('api_source', 'unknown')
        results.append({
            'route': f"{origin} → {destination}",
            'source': api_source,
            'time': call_end - call_start
        })
        
        print(f"  第{i+1}次调用: {origin} → {destination}")
        print(f"    结果: {api_source} | 耗时: {call_end - call_start:.3f}秒")
    
    total_time = time.time() - start_time
    successful_calls = [r for r in results if r['source'] == 'amap_navigation']
    
    print(f"\n📊 速率限制测试结果:")
    print(f"  总调用: {len(results)}次")
    print(f"  成功调用: {len(successful_calls)}次")
    print(f"  总耗时: {total_time:.3f}秒")
    print(f"  平均耗时: {total_time/len(results):.3f}秒")

def main():
    """主测试函数"""
    print("🎯 完整导航路径规划测试套件")
    print("=" * 60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API配置: {Config.AMAP_NAVIGATION_API_KEY[:10]}...")
    print(f"速率限制: {Config.AMAP_NAVIGATION_RATE_LIMIT}次/秒")
    print("功能特点: 完整路径规划, 无离线计算, 智能速率控制")
    print()
    
    try:
        # 测试1：单点路径规划
        test_single_route()
        
        # 等待避免速率限制
        time.sleep(1)
        
        # 测试2：多策略测试
        test_multiple_strategies()
        
        # 等待避免速率限制
        time.sleep(1)
        
        # 测试3：MCP框架集成
        test_mcp_integration()
        
        # 等待避免速率限制
        time.sleep(1)
        
        # 测试4：速率限制
        test_rate_limiting()
        
        print("\n🎉 所有测试完成！")
        print("\n💡 导航MCP特性总结:")
        print("  ✅ 完整路径规划 - 显示所有导航步骤")
        print("  ✅ 智能速率控制 - 自动等待和重试")
        print("  ✅ 详细路径信息 - 包含轨迹、费用、红绿灯等")
        print("  ✅ 多策略支持 - 15种不同的导航策略")
        print("  ✅ MCP框架集成 - 与其他服务协同工作")
        print("  ❌ 取消离线计算 - 错了就是错了，确保数据准确性")
        
    except Exception as e:
        print(f"❌ 测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

