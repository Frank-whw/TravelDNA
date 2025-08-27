#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成交通服务测试
验证Agent与交通服务的集成效果
"""

from traffic_service import get_attraction_traffic, analyze_route_traffic, format_traffic_for_agent
from model import TourismAssistant

def test_traffic_integration():
    """测试Agent交通集成"""
    print("🎯 测试Agent交通服务集成")
    print("=" * 50)
    
    # 测试1: 单景点交通查询
    print("\n📍 测试1: 单景点交通查询")
    attraction = "外滩"
    traffic_info = get_attraction_traffic(attraction)
    
    if traffic_info.get("has_traffic_data"):
        print(f"✅ {attraction} 交通数据获取成功")
        print(f"   状况: {traffic_info.get('traffic_status', '未知')}")
        print(f"   建议: {traffic_info.get('suggestion', '无')}")
        
        # 格式化供Agent使用
        formatted = format_traffic_for_agent(traffic_info)
        print(f"   Agent格式: {formatted.replace(chr(10), ' | ')}")
    else:
        print(f"⚠️ {attraction} 无交通数据")
    
    # 测试2: 路线交通分析
    print("\n📍 测试2: 路线交通分析")
    route = ["外滩", "东方明珠", "豫园"]
    route_analysis = analyze_route_traffic(route)
    
    print(f"✅ 路线分析完成: {' -> '.join(route)}")
    print(f"   整体状况: {route_analysis.get('overall_status', '未知')}")
    print(f"   路线建议: {route_analysis.get('route_suggestions', [])}")
    
    # 测试3: Agent集成
    print("\n📍 测试3: Agent对话集成")
    try:
        assistant = TourismAssistant(use_enhanced=False)  # 使用传统模式测试
        
        # 测试交通相关问题
        queries = [
            "外滩现在交通怎么样？",
            "去外滩怎么走比较好？",
            "外滩周边路况如何？"
        ]
        
        for query in queries:
            print(f"\n   问题: {query}")
            try:
                response = assistant.generate_response(query)
                # 只显示前100字符
                preview = response[:100] + "..." if len(response) > 100 else response
                print(f"   回答: {preview}")
                
                # 检查是否包含交通信息
                if "交通" in response or "拥堵" in response or "地铁" in response:
                    print("   ✅ 回答包含交通信息")
                else:
                    print("   ⚠️ 回答未包含交通信息")
                    
            except Exception as e:
                print(f"   ❌ 生成回答失败: {e}")
                
    except Exception as e:
        print(f"❌ Agent初始化失败: {e}")

def test_core_functions():
    """测试核心功能"""
    print("\n🔧 核心功能测试")
    print("=" * 50)
    
    # 测试景点配置
    from config import Config
    attractions_with_roads = list(Config.SHANGHAI_ATTRACTION_ROADS.keys())
    attractions_with_districts = list(Config.SHANGHAI_ATTRACTION_DISTRICTS.keys())
    
    print(f"📍 配置道路的景点: {len(attractions_with_roads)} 个")
    print(f"📍 配置区域的景点: {len(attractions_with_districts)} 个")
    
    # 显示前5个配置示例
    print(f"\n前5个景点配置示例:")
    for i, attraction in enumerate(list(attractions_with_roads)[:5], 1):
        roads = Config.SHANGHAI_ATTRACTION_ROADS.get(attraction, [])
        district = Config.SHANGHAI_ATTRACTION_DISTRICTS.get(attraction, "未知")
        print(f"   {i}. {attraction}: {len(roads)}条道路, 区域码:{district}")

def main():
    """主测试函数"""
    print("🧪 Agent交通服务集成测试")
    print("📅", "2025-08-27")
    
    try:
        test_core_functions()
        test_traffic_integration()
        
        print("\n🎊 测试完成!")
        print("\n✅ 主要功能:")
        print("   - 景点交通状况查询")
        print("   - 路线交通分析") 
        print("   - Agent智能回答集成")
        print("   - 动态出行建议生成")
        
    except Exception as e:
        print(f"\n❌ 测试过程异常: {e}")

if __name__ == "__main__":
    main()
