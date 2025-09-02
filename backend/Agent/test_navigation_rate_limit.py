#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导航MCP速率限制测试
验证3次/秒的API调用限制是否正常工作
"""

import sys
import os
import time
from datetime import datetime

# 添加模块路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mcp_services import NavigationMCPService
from config import Config

def test_rate_limit():
    """测试速率限制功能"""
    print("🧭 导航MCP速率限制测试")
    print("=" * 50)
    print(f"配置的速率限制: {Config.AMAP_NAVIGATION_RATE_LIMIT}次/秒")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 初始化导航服务
    nav_service = NavigationMCPService()
    
    # 测试连续调用
    print("🔥 连续快速调用测试（应触发速率限制）：")
    
    test_routes = [
        ("外滩", "东方明珠"),
        ("人民广场", "静安寺"),
        ("新天地", "田子坊"),
        ("豫园", "城隍庙"),
        ("徐家汇", "虹桥机场")
    ]
    
    results = []
    start_time = time.time()
    
    for i, (origin, destination) in enumerate(test_routes):
        call_start = time.time()
        
        print(f"  第{i+1}次调用: {origin} -> {destination}")
        
        result = nav_service.get_route_planning(origin, destination)
        
        call_end = time.time()
        call_duration = call_end - call_start
        
        api_source = result.get('api_source', 'unknown')
        calculation_method = result.get('calculation_method', '')
        
        results.append({
            'call_num': i + 1,
            'route': f"{origin} -> {destination}",
            'api_source': api_source,
            'calculation_method': calculation_method,
            'duration': call_duration,
            'timestamp': call_end - start_time
        })
        
        print(f"    结果: {api_source}")
        if calculation_method:
            print(f"    方法: {calculation_method}")
        print(f"    耗时: {call_duration:.3f}秒")
        print()
    
    total_time = time.time() - start_time
    
    # 分析结果
    print("📊 测试结果分析：")
    print("=" * 50)
    
    api_calls = [r for r in results if r['api_source'] == 'amap_navigation']
    offline_calls = [r for r in results if r['api_source'] == 'offline_calculation']
    fallback_calls = [r for r in results if r['api_source'] == 'fallback']
    
    print(f"总调用次数: {len(results)}")
    print(f"API调用次数: {len(api_calls)}")
    print(f"离线计算次数: {len(offline_calls)}")
    print(f"默认兜底次数: {len(fallback_calls)}")
    print(f"总耗时: {total_time:.3f}秒")
    print(f"平均每次: {total_time/len(results):.3f}秒")
    
    # 验证速率限制
    if len(api_calls) <= Config.AMAP_NAVIGATION_RATE_LIMIT:
        print("✅ 速率限制工作正常")
    else:
        print("❌ 速率限制可能失效")
    
    if len(offline_calls) > 0:
        print("✅ 离线计算兜底机制工作正常")
    else:
        print("⚠️ 未触发离线计算，可能是因为调用频率不够高")
    
    print("\n📋 详细调用记录：")
    for result in results:
        print(f"  {result['call_num']}. {result['route']}")
        print(f"     来源: {result['api_source']}")
        print(f"     时间: {result['timestamp']:.3f}s")

def test_controlled_rate():
    """测试控制速率的调用"""
    print("\n🕐 控制速率调用测试（间隔0.5秒）：")
    print("=" * 50)
    
    nav_service = NavigationMCPService()
    
    test_routes = [
        ("静安寺", "人民广场"),
        ("田子坊", "新天地"),
        ("城隍庙", "豫园")
    ]
    
    for i, (origin, destination) in enumerate(test_routes):
        print(f"第{i+1}次调用: {origin} -> {destination}")
        
        result = nav_service.get_route_planning(origin, destination)
        api_source = result.get('api_source', 'unknown')
        
        print(f"  结果: {api_source}")
        
        if i < len(test_routes) - 1:  # 最后一次不等待
            print("  等待0.5秒...")
            time.sleep(0.5)
        
        print()

def test_rate_limiter_reset():
    """测试速率限制器重置功能"""
    print("\n🔄 速率限制器重置测试：")
    print("=" * 50)
    
    nav_service = NavigationMCPService()
    
    # 快速调用超过限制
    print("快速调用4次（应该前3次成功，第4次触发限制）：")
    for i in range(4):
        result = nav_service.get_route_planning("外滩", "东方明珠")
        api_source = result.get('api_source', 'unknown')
        print(f"  第{i+1}次: {api_source}")
    
    print("\n等待1.5秒后重试：")
    time.sleep(1.5)
    
    result = nav_service.get_route_planning("东方明珠", "外滩")
    api_source = result.get('api_source', 'unknown')
    print(f"  重置后调用: {api_source}")
    
    if api_source in ['amap_navigation', 'offline_calculation']:
        print("✅ 速率限制器重置正常")
    else:
        print("❌ 速率限制器重置可能有问题")

def main():
    """主测试函数"""
    print("🎯 导航MCP速率限制完整测试套件")
    print("=" * 60)
    print("目的：验证基础LBS服务3次/秒限制的正确实现")
    print()
    
    try:
        # 测试1：连续快速调用
        test_rate_limit()
        
        # 测试2：控制速率调用
        test_controlled_rate()
        
        # 测试3：速率限制器重置
        test_rate_limiter_reset()
        
        print("\n🎉 所有速率限制测试完成！")
        print("\n💡 速率限制机制说明：")
        print("  - 基础LBS服务限制：3次/秒")
        print("  - 超限自动切换：离线计算模式")
        print("  - 智能兜底：确保服务连续性")
        print("  - 时间窗口：1秒滚动窗口")
        
    except Exception as e:
        print(f"❌ 测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

