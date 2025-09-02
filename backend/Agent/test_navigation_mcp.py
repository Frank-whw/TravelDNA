#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导航MCP服务测试
测试高德地图路径规划API的集成和MCP框架功能
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

def test_navigation_basic():
    """测试基础导航功能"""
    print("=" * 60)
    print("🧭 测试1: 基础导航路径规划")
    print("=" * 60)
    
    try:
        # 初始化导航服务
        nav_service = NavigationMCPService()
        
        # 测试基础路径规划
        print("\n📍 测试: 外滩 -> 东方明珠 导航规划")
        result = nav_service.get_route_planning("外滩", "东方明珠")
        
        print("✅ 导航规划结果:")
        print(f"  起点: {result.get('origin')}")
        print(f"  终点: {result.get('destination')}")
        print(f"  距离: {result.get('distance')}")
        print(f"  时长: {result.get('duration')}")
        print(f"  过路费: {result.get('tolls')}")
        print(f"  红绿灯: {result.get('traffic_lights')}")
        print(f"  限行状态: {result.get('restriction_status')}")
        print(f"  路线总结: {result.get('route_summary')}")
        print(f"  API来源: {result.get('api_source')}")
        
        if result.get('navigation_steps'):
            print("\n🗺️ 导航步骤 (前5步):")
            for step in result['navigation_steps'][:5]:
                print(f"  {step['step']}. {step['instruction']} ({step['distance']})")
        
        if result.get('advice'):
            print(f"\n💡 导航建议: {result['advice']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 基础导航测试失败: {e}")
        return False

def test_navigation_strategies():
    """测试不同导航策略"""
    print("\n" + "=" * 60)
    print("🚗 测试2: 不同导航策略")
    print("=" * 60)
    
    try:
        nav_service = NavigationMCPService()
        
        strategies_to_test = [
            ("default", "默认策略"),
            ("avoid_congestion", "躲避拥堵"),
            ("no_highway", "不走高速"),
            ("less_fee", "少收费")
        ]
        
        print("\n📍 测试路线: 人民广场 -> 虹桥机场")
        
        for strategy, description in strategies_to_test:
            print(f"\n🎯 策略: {description} ({strategy})")
            
            result = nav_service.get_route_planning(
                "人民广场", "虹桥机场", strategy=strategy
            )
            
            print(f"  距离: {result.get('distance')} | 时长: {result.get('duration')}")
            print(f"  过路费: {result.get('tolls')} | 建议: {result.get('advice', '无')[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ 策略测试失败: {e}")
        return False

def test_multi_destination():
    """测试多目的地路径规划"""
    print("\n" + "=" * 60)
    print("🗺️ 测试3: 多目的地路径规划")
    print("=" * 60)
    
    try:
        nav_service = NavigationMCPService()
        
        print("\n📍 测试多目的地路线:")
        origin = "外滩"
        destinations = ["豫园", "新天地", "东方明珠"]
        
        print(f"  起点: {origin}")
        print(f"  目的地: {' -> '.join(destinations)}")
        
        result = nav_service.get_multi_destination_planning(origin, destinations)
        
        print("\n✅ 多目的地规划结果:")
        print(f"  总距离: {result.get('total_distance')}")
        print(f"  总时长: {result.get('total_duration')}")
        print(f"  总过路费: {result.get('total_tolls')}")
        
        # 显示各段路线
        if result.get('route_segments'):
            print("\n🛣️ 分段路线:")
            for segment in result['route_segments']:
                segment_info = segment['route_info']
                print(f"  段{segment['segment']}: {segment['from']} -> {segment['to']}")
                print(f"    距离: {segment_info.get('distance')} | 时长: {segment_info.get('duration')}")
        
        # 显示路线优化建议
        if result.get('route_optimization'):
            optimization = result['route_optimization']
            print(f"\n📊 路线评估: {optimization.get('efficiency_score')}")
            
            if optimization.get('suggestions'):
                print("💡 优化建议:")
                for suggestion in optimization['suggestions']:
                    print(f"  - {suggestion}")
            
            if optimization.get('alternative_transport'):
                print(f"🚇 替代交通: {', '.join(optimization['alternative_transport'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ 多目的地测试失败: {e}")
        return False

def test_coordinate_handling():
    """测试坐标处理功能"""
    print("\n" + "=" * 60)
    print("📍 测试4: 坐标处理功能")
    print("=" * 60)
    
    try:
        nav_service = NavigationMCPService()
        
        # 测试景点名称转坐标
        print("\n🔍 测试景点坐标获取:")
        attractions = ["外滩", "东方明珠", "迪士尼", "不存在的景点"]
        
        for attraction in attractions:
            coords = nav_service._get_coordinates(attraction)
            if coords:
                print(f"  ✅ {attraction}: {coords}")
            else:
                print(f"  ❌ {attraction}: 坐标未找到")
        
        # 测试直接使用坐标
        print("\n📐 测试直接坐标导航:")
        result = nav_service.get_route_planning(
            "121.484429,31.240791",  # 外滩坐标
            "121.506377,31.245105"   # 东方明珠坐标
        )
        
        print(f"  坐标导航结果: {result.get('route_summary')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 坐标处理测试失败: {e}")
        return False

def test_mcp_integration():
    """测试MCP框架集成"""
    print("\n" + "=" * 60)
    print("🔧 测试5: MCP框架集成")
    print("=" * 60)
    
    try:
        # 通过MCP管理器调用导航服务
        mcp_manager = MCPServiceManager()
        
        print("\n🎯 测试MCP管理器导航调用:")
        
        # 测试单点导航
        result1 = mcp_manager.get_navigation_planning("徐家汇", "静安寺")
        print(f"  单点导航: {result1.get('route_summary')}")
        
        # 测试多目的地导航
        result2 = mcp_manager.get_multi_destination_planning(
            "人民广场", ["上海博物馆", "新天地", "田子坊"]
        )
        print(f"  多目的地: {result2.get('total_distance')} | {result2.get('total_duration')}")
        
        # 测试服务分析
        query = "从外滩到东方明珠怎么开车去"
        services = mcp_manager.analyze_query(query)
        print(f"  查询分析: '{query}' -> 服务: {services}")
        
        # 测试针对性信息获取
        targeted_info = mcp_manager.get_targeted_info("东方明珠", "怎么开车去", "外滩")
        print(f"  针对性信息: 已获取 {len(targeted_info.get('services_used', []))} 个服务")
        
        return True
        
    except Exception as e:
        print(f"❌ MCP集成测试失败: {e}")
        return False

def test_error_handling():
    """测试错误处理"""
    print("\n" + "=" * 60)
    print("⚠️ 测试6: 错误处理和兜底机制")
    print("=" * 60)
    
    try:
        nav_service = NavigationMCPService()
        
        # 测试无效景点
        print("\n🚫 测试无效景点:")
        result1 = nav_service.get_route_planning("不存在的地点", "另一个不存在的地点")
        print(f"  无效景点结果: {result1.get('api_source')} - {result1.get('advice')}")
        
        # 测试空的目的地列表
        print("\n📝 测试空目的地列表:")
        result2 = nav_service.get_multi_destination_planning("外滩", [])
        print(f"  空列表结果: {result2.get('status', '正常')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 错误处理测试失败: {e}")
        return False

def test_performance():
    """测试性能"""
    print("\n" + "=" * 60)
    print("⚡ 测试7: 性能测试")
    print("=" * 60)
    
    try:
        nav_service = NavigationMCPService()
        
        # 测试单次调用性能
        print("\n⏱️ 单次导航调用性能:")
        start_time = time.time()
        result = nav_service.get_route_planning("外滩", "迪士尼")
        end_time = time.time()
        
        print(f"  调用时间: {end_time - start_time:.2f}秒")
        print(f"  API来源: {result.get('api_source')}")
        
        # 测试批量调用性能
        print("\n📊 批量导航调用性能:")
        test_routes = [
            ("外滩", "东方明珠"),
            ("人民广场", "徐家汇"),
            ("静安寺", "虹桥机场")
        ]
        
        total_start = time.time()
        for origin, destination in test_routes:
            route_start = time.time()
            nav_service.get_route_planning(origin, destination)
            route_end = time.time()
            print(f"  {origin} -> {destination}: {route_end - route_start:.2f}秒")
        
        total_end = time.time()
        print(f"  总计时间: {total_end - total_start:.2f}秒")
        print(f"  平均时间: {(total_end - total_start)/len(test_routes):.2f}秒")
        
        return True
        
    except Exception as e:
        print(f"❌ 性能测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🧭 导航MCP服务测试套件")
    print("=" * 80)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"导航API密钥: {Config.AMAP_NAVIGATION_API_KEY[:10]}...")
    print(f"导航API URL: {Config.AMAP_NAVIGATION_URL}")
    print()
    
    # 执行所有测试
    tests = [
        ("基础导航功能", test_navigation_basic),
        ("导航策略测试", test_navigation_strategies),
        ("多目的地规划", test_multi_destination),
        ("坐标处理功能", test_coordinate_handling),
        ("MCP框架集成", test_mcp_integration),
        ("错误处理机制", test_error_handling),
        ("性能测试", test_performance)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n🔍 执行测试: {test_name}")
        try:
            success = test_func()
            results[test_name] = "✅ 通过" if success else "❌ 失败"
        except Exception as e:
            print(f"❌ 测试 {test_name} 异常: {e}")
            results[test_name] = "❌ 异常"
    
    # 输出测试总结
    print("\n" + "=" * 80)
    print("📊 测试结果总结")
    print("=" * 80)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        print(f"  {result} {test_name}")
        if "✅" in result:
            passed += 1
    
    print(f"\n📈 通过率: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 所有测试通过！导航MCP服务集成成功！")
    else:
        print("⚠️ 部分测试失败，请检查相关功能")
    
    print("\n💡 导航MCP服务功能:")
    print("  - ✅ 单点路径规划")
    print("  - ✅ 多目的地路径规划") 
    print("  - ✅ 多种导航策略")
    print("  - ✅ 景点坐标转换")
    print("  - ✅ MCP框架集成")
    print("  - ✅ 智能查询分析")
    print("  - ✅ 错误处理和兜底")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
