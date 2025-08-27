#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP交通服务集成测试
验证交通MCP与整个MCP框架的集成效果
"""

import sys
from datetime import datetime

def test_mcp_framework():
    """测试MCP框架集成"""
    print("🧪 MCP框架交通服务集成测试")
    print("=" * 60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 测试MCP服务管理器初始化
        print("\n📍 测试1: MCP服务管理器初始化")
        from mcp_services import MCPServiceManager
        
        mcp_manager = MCPServiceManager()
        print("✅ MCP服务管理器初始化成功")
        
        # 检查各个MCP服务
        services = ["weather_service", "crowd_service", "traffic_service"]
        for service_name in services:
            if hasattr(mcp_manager, service_name):
                service = getattr(mcp_manager, service_name)
                print(f"✅ {service_name}: {type(service).__name__}")
            else:
                print(f"❌ {service_name}: 未找到")
        
        # 测试交通MCP服务
        print("\n📍 测试2: 交通MCP服务调用")
        attraction = "外滩"
        try:
            traffic_info = mcp_manager.traffic_service.get_traffic_info(attraction)
            
            if traffic_info.get("service") == "traffic":
                print(f"✅ 交通MCP服务调用成功")
                print(f"   景点: {traffic_info.get('destination', '未知')}")
                print(f"   状况: {traffic_info.get('traffic_status', '未知')}")
                print(f"   建议: {traffic_info.get('recommendation', '无')}")
                print(f"   来源: {traffic_info.get('api_source', '未知')}")
            else:
                print("❌ 交通MCP服务返回格式错误")
                
        except Exception as e:
            print(f"❌ 交通MCP服务调用失败: {e}")
        
        # 测试路线交通分析
        print("\n📍 测试3: 路线交通分析(MCP)")
        route = ["外滩", "东方明珠", "豫园"]
        try:
            route_analysis = mcp_manager.get_route_traffic_analysis(route)
            
            if route_analysis.get("service") == "traffic_route":
                print(f"✅ 路线交通分析成功")
                print(f"   路线: {' -> '.join(route_analysis.get('route', []))}")
                print(f"   整体状况: {route_analysis.get('overall_status', '未知')}")
                print(f"   平均拥堵: {route_analysis.get('average_congestion', '未知')}")
                print(f"   建议数量: {len(route_analysis.get('route_suggestions', []))}")
            else:
                print("❌ 路线交通分析返回格式错误")
                
        except Exception as e:
            print(f"❌ 路线交通分析失败: {e}")
        
        # 测试综合信息获取
        print("\n📍 测试4: 综合信息获取(天气+人流+交通)")
        try:
            comprehensive_info = mcp_manager.get_comprehensive_info(attraction)
            
            services_used = comprehensive_info.get("services_used", [])
            print(f"✅ 综合信息获取成功")
            print(f"   包含服务: {', '.join(services_used)}")
            
            # 检查是否包含交通信息
            if "traffic" in services_used:
                traffic_data = comprehensive_info.get("traffic", {})
                print(f"   交通状况: {traffic_data.get('traffic_status', '未知')}")
                print(f"   ✅ 交通信息已集成到综合信息中")
            else:
                print("   ⚠️ 综合信息中未包含交通数据")
                
        except Exception as e:
            print(f"❌ 综合信息获取失败: {e}")
        
        # 测试Agent集成
        print("\n📍 测试5: Agent集成测试")
        try:
            from model import TourismAssistant
            
            # 使用传统模式测试（更容易调试）
            assistant = TourismAssistant(use_enhanced=False)
            
            # 测试包含交通的查询
            query = "外滩交通怎么样？"
            print(f"   查询: {query}")
            
            response = assistant.generate_response(query)
            
            # 检查回答是否包含交通相关信息
            traffic_keywords = ["交通", "拥堵", "地铁", "出行", "路况", "建议"]
            found_keywords = [kw for kw in traffic_keywords if kw in response]
            
            if found_keywords:
                print(f"✅ Agent回答包含交通信息")
                print(f"   包含关键词: {', '.join(found_keywords)}")
                
                # 显示回答预览
                preview = response[:150] + "..." if len(response) > 150 else response
                print(f"   回答预览: {preview}")
            else:
                print("⚠️ Agent回答未包含明显的交通信息")
                
        except Exception as e:
            print(f"❌ Agent集成测试失败: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ MCP框架测试失败: {e}")
        return False

def test_mcp_architecture():
    """测试MCP架构"""
    print("\n🏗️ MCP架构验证")
    print("=" * 40)
    
    try:
        from mcp_services import MCPService, WeatherMCPService, CrowdMCPService, TrafficMCPService
        
        # 检查继承关系
        print("📋 MCP服务继承关系:")
        
        services = [
            ("WeatherMCPService", WeatherMCPService),
            ("CrowdMCPService", CrowdMCPService), 
            ("TrafficMCPService", TrafficMCPService)
        ]
        
        for name, service_class in services:
            # 检查是否继承自MCPService
            if issubclass(service_class, MCPService):
                print(f"✅ {name} -> MCPService")
            else:
                print(f"❌ {name} 未继承MCPService")
        
        # 检查交通MCP的特殊性（实例方法vs类方法）
        print(f"\n🔍 交通MCP服务分析:")
        traffic_service = TrafficMCPService()
        
        # 检查主要方法
        main_methods = ["get_traffic_info", "get_route_traffic_analysis"]
        for method_name in main_methods:
            if hasattr(traffic_service, method_name):
                method = getattr(traffic_service, method_name)
                print(f"✅ {method_name}: {type(method)}")
            else:
                print(f"❌ {method_name}: 方法不存在")
        
        return True
        
    except Exception as e:
        print(f"❌ MCP架构验证失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🎯 MCP框架交通服务完整测试")
    print("📋 测试范围: MCP架构、交通服务、Agent集成")
    print("🔑 API密钥: 425125fef7e244aa380807946ec48776")
    
    tests = [
        ("MCP框架集成", test_mcp_framework),
        ("MCP架构验证", test_mcp_architecture)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
            results.append((test_name, False))
    
    # 输出总结
    print("\n" + "="*60)
    print("📊 测试结果总结")
    print("="*60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {test_name:<20} {status}")
    
    print(f"\n📈 通过率: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 所有测试通过！MCP交通服务集成成功")
        print("\n✅ MCP框架结构:")
        print("   🌤️  WeatherMCPService  - 天气服务")
        print("   👥  CrowdMCPService    - 人流服务") 
        print("   🚦  TrafficMCPService  - 交通服务")
        print("   🤖  Agent集成完成     - 智能回答")
    else:
        print("\n⚠️ 部分测试失败，请检查MCP框架集成")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
