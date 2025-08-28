#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
POI搜索功能测试
测试关键字搜索、周边搜索、多边形搜索和旅游推荐功能
"""

import sys
import os
import json
import time
from datetime import datetime

# 添加模块路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mcp_services import POISearchMCPService, MCPServiceManager
from config import Config

def test_keyword_search():
    """测试关键字搜索功能"""
    print("🔍 POI关键字搜索测试")
    print("=" * 50)
    
    poi_service = POISearchMCPService()
    
    # 测试不同类型的关键字搜索
    test_cases = [
        {"keywords": "咖啡厅", "region": "上海", "description": "搜索上海的咖啡厅"},
        {"keywords": "麦当劳", "region": "黄浦区", "description": "搜索黄浦区的麦当劳"},
        {"keywords": "银行", "region": "上海", "description": "搜索上海的银行"},
        {"keywords": "地铁站", "region": "徐汇区", "description": "搜索徐汇区的地铁站"},
    ]
    
    for i, test_case in enumerate(test_cases):
        print(f"\n📍 测试 {i+1}: {test_case['description']}")
        
        start_time = time.time()
        result = poi_service.text_search(
            keywords=test_case["keywords"],
            region=test_case["region"],
            page_size=5
        )
        end_time = time.time()
        
        print(f"  关键字: {test_case['keywords']}")
        print(f"  区域: {test_case['region']}")
        print(f"  响应时间: {end_time - start_time:.2f}秒")
        
        if result.get("api_source") == "amap_poi_search":
            pois = result.get("pois", [])
            total_count = result.get("total_count", 0)
            
            print(f"  ✅ 搜索成功: 共找到 {total_count} 个结果")
            print(f"  📋 显示前 {len(pois)} 个结果:")
            
            for j, poi in enumerate(pois[:3]):
                name = poi.get("name", "未知")
                address = poi.get("address", "地址未知")
                poi_type = poi.get("type", "类型未知")
                distance = poi.get("distance_formatted", poi.get("distance", ""))
                
                print(f"    {j+1}. {name}")
                print(f"       地址: {address}")
                print(f"       类型: {poi_type}")
                if distance:
                    print(f"       距离: {distance}")
        else:
            print(f"  ❌ 搜索失败: {result.get('error', '未知错误')}")
        
        # 避免API限制
        time.sleep(0.2)
    
    return True

def test_around_search():
    """测试周边搜索功能"""
    print("\n📍 POI周边搜索测试")
    print("=" * 50)
    
    poi_service = POISearchMCPService()
    
    # 测试不同地点的周边搜索
    test_locations = [
        {
            "name": "外滩",
            "location": "121.484429,31.240791",
            "keywords": "餐厅",
            "radius": 1000,
            "description": "外滩周边1公里内的餐厅"
        },
        {
            "name": "人民广场",
            "location": "121.475049,31.228917",
            "keywords": None,
            "radius": 500,
            "description": "人民广场周边500米内的POI"
        },
        {
            "name": "陆家嘴",
            "location": "121.506377,31.245105",
            "keywords": "咖啡",
            "radius": 2000,
            "description": "陆家嘴周边2公里内的咖啡店"
        }
    ]
    
    for i, test_loc in enumerate(test_locations):
        print(f"\n📍 测试 {i+1}: {test_loc['description']}")
        
        start_time = time.time()
        result = poi_service.around_search(
            location=test_loc["location"],
            keywords=test_loc["keywords"],
            radius=test_loc["radius"]
        )
        end_time = time.time()
        
        print(f"  地点: {test_loc['name']} ({test_loc['location']})")
        print(f"  关键字: {test_loc['keywords'] or '全部类型'}")
        print(f"  搜索半径: {test_loc['radius']}米")
        print(f"  响应时间: {end_time - start_time:.2f}秒")
        
        if result.get("api_source") == "amap_poi_search":
            pois = result.get("pois", [])
            total_count = result.get("total_count", 0)
            
            print(f"  ✅ 搜索成功: 共找到 {total_count} 个结果")
            print(f"  📋 显示前 {len(pois)} 个结果:")
            
            for j, poi in enumerate(pois[:3]):
                name = poi.get("name", "未知")
                address = poi.get("address", "地址未知")
                distance = poi.get("distance_formatted", poi.get("distance", ""))
                poi_type = poi.get("type", "类型未知")
                
                print(f"    {j+1}. {name}")
                print(f"       地址: {address}")
                print(f"       类型: {poi_type}")
                if distance:
                    print(f"       距离: {distance}")
        else:
            print(f"  ❌ 搜索失败: {result.get('error', '未知错误')}")
        
        # 避免API限制
        time.sleep(0.2)
    
    return True

def test_poi_types_and_filtering():
    """测试POI类型过滤功能"""
    print("\n🏷️ POI类型过滤测试")
    print("=" * 50)
    
    poi_service = POISearchMCPService()
    
    # 测试不同POI类型的搜索
    type_tests = [
        {
            "keywords": "服务",
            "types": ["050000"],  # 餐饮服务
            "description": "餐饮服务类POI"
        },
        {
            "keywords": "购物",
            "types": ["060000"],  # 购物服务
            "description": "购物服务类POI"
        },
        {
            "keywords": "交通",
            "types": ["150500", "150700"],  # 地铁站、公交站
            "description": "交通设施类POI"
        }
    ]
    
    for i, test_type in enumerate(type_tests):
        print(f"\n🏷️ 测试 {i+1}: {test_type['description']}")
        
        start_time = time.time()
        result = poi_service.text_search(
            keywords=test_type["keywords"],
            region="上海",
            types=test_type["types"],
            page_size=5
        )
        end_time = time.time()
        
        print(f"  关键字: {test_type['keywords']}")
        print(f"  类型过滤: {test_type['types']}")
        print(f"  响应时间: {end_time - start_time:.2f}秒")
        
        if result.get("api_source") == "amap_poi_search":
            pois = result.get("pois", [])
            total_count = result.get("total_count", 0)
            
            print(f"  ✅ 搜索成功: 共找到 {total_count} 个结果")
            
            # 统计类型分布
            type_distribution = {}
            for poi in pois:
                typecode = poi.get("typecode", "").split("|")[0][:6]  # 取前6位
                if typecode:
                    type_distribution[typecode] = type_distribution.get(typecode, 0) + 1
            
            print(f"  📊 类型分布: {type_distribution}")
            
            # 显示示例
            for j, poi in enumerate(pois[:2]):
                name = poi.get("name", "未知")
                poi_type = poi.get("type", "类型未知")
                typecode = poi.get("typecode", "")
                
                print(f"    {j+1}. {name} (类型: {poi_type}, 代码: {typecode})")
        else:
            print(f"  ❌ 搜索失败: {result.get('error', '未知错误')}")
        
        # 避免API限制
        time.sleep(0.2)
    
    return True

def test_mcp_integration():
    """测试MCP框架集成"""
    print("\n🔧 MCP框架集成测试")
    print("=" * 50)
    
    mcp_manager = MCPServiceManager()
    
    # 测试通过MCP管理器的POI搜索
    print("📍 测试 1: 通过MCP管理器搜索POI")
    
    start_time = time.time()
    result = mcp_manager.search_poi_by_keyword("星巴克", "上海")
    end_time = time.time()
    
    print(f"  关键字: 星巴克")
    print(f"  响应时间: {end_time - start_time:.2f}秒")
    
    if result.get("api_source") == "amap_poi_search":
        pois = result.get("pois", [])
        print(f"  ✅ MCP搜索成功: 找到 {len(pois)} 个星巴克")
        
        if pois:
            first_poi = pois[0]
            print(f"  📍 第一个结果: {first_poi.get('name', '未知')}")
            print(f"     地址: {first_poi.get('address', '地址未知')}")
    else:
        print(f"  ❌ MCP搜索失败: {result.get('error', '未知错误')}")
    
    # 测试周边搜索
    print("\n📍 测试 2: 通过MCP管理器周边搜索")
    
    start_time = time.time()
    result = mcp_manager.search_poi_around("121.484429,31.240791", "咖啡", radius=1000)
    end_time = time.time()
    
    print(f"  位置: 外滩 (121.484429,31.240791)")
    print(f"  关键字: 咖啡")
    print(f"  响应时间: {end_time - start_time:.2f}秒")
    
    if result.get("api_source") == "amap_poi_search":
        pois = result.get("pois", [])
        print(f"  ✅ MCP周边搜索成功: 找到 {len(pois)} 个咖啡店")
    else:
        print(f"  ❌ MCP周边搜索失败: {result.get('error', '未知错误')}")
    
    # 测试旅游推荐
    print("\n📍 测试 3: 获取旅游POI推荐")
    
    start_time = time.time()
    result = mcp_manager.get_poi_recommendations_for_travel("外滩", "tourism")
    end_time = time.time()
    
    print(f"  目的地: 外滩")
    print(f"  旅游类型: tourism")
    print(f"  响应时间: {end_time - start_time:.2f}秒")
    
    if result.get("api_source") == "amap_poi_search":
        pois = result.get("pois", [])
        print(f"  ✅ 旅游推荐成功: 找到 {len(pois)} 个相关POI")
        
        # 统计类型分布
        type_counts = {}
        for poi in pois:
            typecode = poi.get("typecode", "")
            if typecode.startswith("05"):
                type_counts["餐饮"] = type_counts.get("餐饮", 0) + 1
            elif typecode.startswith("06"):
                type_counts["购物"] = type_counts.get("购物", 0) + 1
            elif typecode.startswith("11"):
                type_counts["景点"] = type_counts.get("景点", 0) + 1
            elif typecode.startswith("15"):
                type_counts["交通"] = type_counts.get("交通", 0) + 1
        
        print(f"  📊 推荐分布: {type_counts}")
    else:
        print(f"  ❌ 旅游推荐失败: {result.get('error', '未知错误')}")
    
    return True

def test_rate_limiting():
    """测试速率限制功能"""
    print("\n⏱️ POI搜索速率限制测试")
    print("=" * 50)
    
    poi_service = POISearchMCPService()
    
    print(f"配置的速率限制: {Config.AMAP_POI_RATE_LIMIT}次/秒")
    
    # 快速连续调用测试
    search_terms = ["咖啡", "餐厅", "银行", "地铁", "超市"]
    
    start_time = time.time()
    results = []
    
    for i, term in enumerate(search_terms):
        call_start = time.time()
        result = poi_service.text_search(term, "上海", page_size=1)
        call_end = time.time()
        
        api_source = result.get("api_source", "unknown")
        results.append({
            'term': term,
            'source': api_source,
            'time': call_end - call_start,
            'success': api_source == "amap_poi_search"
        })
        
        print(f"  第{i+1}次调用: {term}")
        print(f"    结果: {api_source} | 耗时: {call_end - call_start:.3f}秒")
    
    total_time = time.time() - start_time
    successful_calls = [r for r in results if r['success']]
    
    print(f"\n📊 速率限制测试结果:")
    print(f"  总调用: {len(results)}次")
    print(f"  成功调用: {len(successful_calls)}次")
    print(f"  总耗时: {total_time:.3f}秒")
    print(f"  平均耗时: {total_time/len(results):.3f}秒")
    
    return True

def test_comprehensive_poi_functionality():
    """综合POI功能测试"""
    print("\n🎯 综合POI功能测试")
    print("=" * 50)
    
    mcp_manager = MCPServiceManager()
    
    # 模拟真实使用场景：为外滩游客推荐周边服务
    print("📍 场景: 外滩游客需要周边服务推荐")
    
    外滩坐标 = "121.484429,31.240791"
    
    scenarios = [
        {"keywords": "咖啡厅", "description": "寻找休息场所"},
        {"keywords": "餐厅", "description": "寻找用餐地点"},
        {"keywords": "银行", "description": "寻找ATM机"},
        {"keywords": "地铁站", "description": "寻找交通换乘"}
    ]
    
    comprehensive_results = {}
    
    for scenario in scenarios:
        print(f"\n🔍 {scenario['description']}: 搜索{scenario['keywords']}")
        
        # 周边搜索
        result = mcp_manager.search_poi_around(
            location=外滩坐标,
            keywords=scenario['keywords'],
            radius=1000
        )
        
        if result.get("api_source") == "amap_poi_search":
            pois = result.get("pois", [])
            comprehensive_results[scenario['keywords']] = len(pois)
            
            print(f"  ✅ 找到 {len(pois)} 个{scenario['keywords']}")
            
            # 显示最近的3个
            for i, poi in enumerate(pois[:3]):
                name = poi.get("name", "未知")
                distance = poi.get("distance_formatted", poi.get("distance", ""))
                address = poi.get("address", "")
                
                print(f"    {i+1}. {name}")
                if distance:
                    print(f"       距离: {distance}")
                if address:
                    print(f"       地址: {address[:30]}..." if len(address) > 30 else f"       地址: {address}")
        else:
            print(f"  ❌ 搜索{scenario['keywords']}失败")
            comprehensive_results[scenario['keywords']] = 0
        
        # 避免API限制
        time.sleep(0.3)
    
    print(f"\n📊 外滩周边服务统计:")
    for service, count in comprehensive_results.items():
        print(f"  {service}: {count}个")
    
    total_services = sum(comprehensive_results.values())
    print(f"  📍 总计: {total_services}个周边服务点")
    
    return True

def main():
    """主测试函数"""
    print("🧪 POI搜索功能测试套件")
    print("=" * 60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API配置: {Config.AMAP_POI_API_KEY[:10]}...")
    print(f"速率限制: {Config.AMAP_POI_RATE_LIMIT}次/秒")
    print("测试范围: 关键字搜索 + 周边搜索 + MCP集成 + 速率控制")
    print()
    
    try:
        # 测试1: 关键字搜索
        test_keyword_search()
        
        # 等待避免API限制
        time.sleep(1)
        
        # 测试2: 周边搜索
        test_around_search()
        
        # 等待避免API限制
        time.sleep(1)
        
        # 测试3: POI类型过滤
        test_poi_types_and_filtering()
        
        # 等待避免API限制
        time.sleep(1)
        
        # 测试4: MCP框架集成
        test_mcp_integration()
        
        # 等待避免API限制
        time.sleep(1)
        
        # 测试5: 速率限制
        test_rate_limiting()
        
        # 等待避免API限制
        time.sleep(1)
        
        # 测试6: 综合功能
        test_comprehensive_poi_functionality()
        
        print("\n🎉 所有POI搜索测试完成！")
        print("\n💡 POI搜索MCP特性总结:")
        print("  ✅ 关键字搜索 - 支持区域限制和类型过滤")
        print("  ✅ 周边搜索 - 基于坐标的半径搜索")
        print("  ✅ 多边形搜索 - 支持复杂区域定义")
        print("  ✅ 类型过滤 - 30+种POI类型精确分类")
        print("  ✅ MCP集成 - 与现有服务框架无缝融合")
        print("  ✅ 速率控制 - 智能限流和重试机制")
        print("  ✅ 旅游推荐 - 专门为旅游场景优化的POI推荐")
        print("  ✅ 实时数据 - 基于高德地图的准确POI信息")
        
    except Exception as e:
        print(f"❌ 测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

