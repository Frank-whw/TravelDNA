#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能旅游攻略规划Agent测试
测试MCP服务深度整合和智能决策流程
"""

import sys
import os
import json
import time
from datetime import datetime

# 添加模块路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from travel_agent import TravelAgentService, TravelPreference, WeatherCondition, TrafficCondition, CrowdLevel
from config import Config

def test_basic_travel_planning():
    """测试基础旅游攻略规划"""
    print("🎯 基础旅游攻略规划测试")
    print("=" * 50)
    
    travel_agent = TravelAgentService()
    
    # 测试基本旅游计划
    print("📍 测试路线: 人民广场 → 外滩 → 东方明珠 → 豫园")
    
    start_time = time.time()
    travel_plan = travel_agent.create_travel_plan(
        origin="人民广场",
        destinations=["外滩", "东方明珠", "豫园"]
    )
    end_time = time.time()
    
    print(f"\n⏱️ 规划用时: {end_time - start_time:.2f}秒")
    print(f"📊 方案得分: {travel_plan.overall_score:.1f}/100")
    print(f"🌤️ 天气适宜度: {travel_plan.weather_compatibility:.1f}/100")
    print(f"🚦 交通便利度: {travel_plan.traffic_score:.1f}/100")
    print(f"👥 人流舒适度: {travel_plan.crowd_score:.1f}/100")
    
    # 显示智能建议
    print("\n💡 智能建议:")
    for rec in travel_plan.recommendations:
        print(f"  • {rec}")
    
    if travel_plan.adjustments:
        print("\n🔄 优化建议:")
        for adj in travel_plan.adjustments:
            print(f"  • {adj}")
    
    return travel_plan

def test_weather_condition_handling():
    """测试天气状况处理"""
    print("\n🌦️ 天气状况处理测试")
    print("=" * 50)
    
    travel_agent = TravelAgentService()
    
    # 创建不同天气容忍度的偏好
    weather_sensitive = TravelPreference()
    weather_sensitive.weather_tolerance = WeatherCondition.GOOD
    
    weather_tolerant = TravelPreference()
    weather_tolerant.weather_tolerance = WeatherCondition.POOR
    
    destinations = ["南京路步行街", "城隍庙", "新天地"]
    
    print("👤 天气敏感用户:")
    plan_sensitive = travel_agent.create_travel_plan(
        origin="静安寺",
        destinations=destinations,
        user_preferences=weather_sensitive
    )
    print(f"  得分: {plan_sensitive.overall_score:.1f}, 天气: {plan_sensitive.weather_compatibility:.1f}")
    
    print("👤 天气容忍用户:")
    plan_tolerant = travel_agent.create_travel_plan(
        origin="静安寺", 
        destinations=destinations,
        user_preferences=weather_tolerant
    )
    print(f"  得分: {plan_tolerant.overall_score:.1f}, 天气: {plan_tolerant.weather_compatibility:.1f}")

def test_traffic_optimization():
    """测试交通优化"""
    print("\n🚦 交通优化测试")
    print("=" * 50)
    
    travel_agent = TravelAgentService()
    
    # 测试不同交通偏好
    time_priority = TravelPreference()
    time_priority.time_conscious = True
    
    cost_priority = TravelPreference()
    cost_priority.budget_conscious = True
    
    comfort_priority = TravelPreference()
    comfort_priority.comfort_priority = True
    
    destinations = ["虹桥机场", "徐家汇", "淮海路"]
    
    print("⏱️ 时间优先策略:")
    plan_time = travel_agent.create_travel_plan(
        origin="人民广场",
        destinations=destinations,
        user_preferences=time_priority
    )
    print(f"  交通得分: {plan_time.traffic_score:.1f}, 总用时: {plan_time.total_duration}分钟")
    
    print("💰 费用优先策略:")
    plan_cost = travel_agent.create_travel_plan(
        origin="人民广场",
        destinations=destinations,
        user_preferences=cost_priority
    )
    print(f"  交通得分: {plan_cost.traffic_score:.1f}, 总距离: {plan_cost.total_distance:.1f}公里")
    
    print("😌 舒适优先策略:")
    plan_comfort = travel_agent.create_travel_plan(
        origin="人民广场",
        destinations=destinations,
        user_preferences=comfort_priority
    )
    print(f"  交通得分: {plan_comfort.traffic_score:.1f}, 综合得分: {plan_comfort.overall_score:.1f}")

def test_user_preference_adjustment():
    """测试用户偏好调整"""
    print("\n🔄 用户偏好调整测试")
    print("=" * 50)
    
    travel_agent = TravelAgentService()
    
    # 创建初始计划
    initial_plan = travel_agent.create_travel_plan(
        origin="陆家嘴",
        destinations=["田子坊", "新天地", "淮海路"]
    )
    
    print(f"📊 初始方案得分: {initial_plan.overall_score:.1f}/100")
    
    # 获取用户偏好问题
    preference_questions = travel_agent.ask_user_preferences(initial_plan)
    
    print(f"\n❓ 生成了 {len(preference_questions['questions'])} 个偏好问题:")
    for i, question in enumerate(preference_questions['questions']):
        print(f"  {i+1}. {question['question']}")
        print(f"     选项: {', '.join(question['options'])}")
    
    # 模拟用户回答
    user_answers = {
        'weather_tolerance': '可以接受',
        'traffic_tolerance': '舒适优先(避开拥堵)',
        'crowd_tolerance': '偏好人少景点',
        'time_preference': '早上(避开人流)'
    }
    
    print(f"\n👤 用户偏好回答: {user_answers}")
    
    # 调整方案
    adjusted_plan = travel_agent.adjust_plan_by_preferences(initial_plan, user_answers)
    
    print(f"📈 调整后得分: {adjusted_plan.overall_score:.1f}/100")
    print(f"📊 得分提升: {adjusted_plan.overall_score - initial_plan.overall_score:.1f}分")
    
    return initial_plan, adjusted_plan

def test_rag_integration():
    """测试RAG知识库整合"""
    print("\n🧠 RAG知识库整合测试")
    print("=" * 50)
    
    travel_agent = TravelAgentService()
    
    # 创建基础计划
    base_plan = travel_agent.create_travel_plan(
        origin="外滩",
        destinations=["南京路", "人民广场", "豫园"]
    )
    
    print(f"📊 基础方案得分: {base_plan.overall_score:.1f}/100")
    
    # 模拟RAG知识库数据
    rag_knowledge = {
        'suggestions': [
            "南京路最佳拍照时间是下午4-6点，逆光效果最佳",
            "豫园周边小笼包推荐南翔馒头店，避开12-14点高峰期",
            "人民广场地铁站人流密集，建议使用2号出口"
        ],
        'alternative_destinations': [
            "如果豫园人太多，可以考虑附近的城隍庙",
            "南京路购物可以延伸到淮海路，品牌更加国际化"
        ],
        'local_insights': [
            "外滩观景最佳位置在浦东陆家嘴滨江大道",
            "避开周末，工作日的人流量会少30-40%"
        ]
    }
    
    print("\n🔍 RAG知识库内容:")
    print(f"  建议数量: {len(rag_knowledge['suggestions'])}")
    print(f"  替代景点: {len(rag_knowledge['alternative_destinations'])}")
    print(f"  当地洞察: {len(rag_knowledge['local_insights'])}")
    
    # RAG增强
    enhanced_plan = travel_agent.integrate_with_rag(base_plan, rag_knowledge)
    
    print(f"\n📈 RAG增强后得分: {enhanced_plan.overall_score:.1f}/100")
    print(f"📊 得分提升: {enhanced_plan.overall_score - base_plan.overall_score:.1f}分")
    
    print("\n🧠 新增RAG建议:")
    rag_recommendations = [rec for rec in enhanced_plan.recommendations if "RAG建议" in rec]
    for rec in rag_recommendations:
        print(f"  • {rec}")
    
    return enhanced_plan

def test_comprehensive_workflow():
    """测试完整的工作流程"""
    print("\n🎯 完整工作流程测试")
    print("=" * 50)
    
    travel_agent = TravelAgentService()
    
    print("阶段1: 创建初始攻略")
    initial_plan = travel_agent.create_travel_plan(
        origin="上海火车站",
        destinations=["外滩", "陆家嘴", "新天地", "田子坊", "豫园"]
    )
    
    print(f"  初始得分: {initial_plan.overall_score:.1f}/100")
    print(f"  总用时: {initial_plan.total_duration}分钟")
    print(f"  总距离: {initial_plan.total_distance:.1f}公里")
    
    print("\n阶段2: 用户偏好优化")
    user_feedback = {
        'weather_tolerance': '尽量避免',
        'traffic_tolerance': '时间优先(快速路线)',
        'crowd_tolerance': '必须避开人群'
    }
    
    optimized_plan = travel_agent.adjust_plan_by_preferences(initial_plan, user_feedback)
    print(f"  优化得分: {optimized_plan.overall_score:.1f}/100")
    print(f"  得分提升: {optimized_plan.overall_score - initial_plan.overall_score:.1f}分")
    
    print("\n阶段3: RAG知识增强")
    rag_data = {
        'suggestions': ["避开周末和节假日", "选择早晨8-10点出行"],
        'alternative_destinations': ["如人流过多可选择静安寺商圈"],
        'local_insights': ["使用上海地铁日票可节省交通费"]
    }
    
    final_plan = travel_agent.integrate_with_rag(optimized_plan, rag_data)
    print(f"  最终得分: {final_plan.overall_score:.1f}/100")
    print(f"  总体提升: {final_plan.overall_score - initial_plan.overall_score:.1f}分")
    
    print(f"\n🎉 完整攻略规划完成!")
    print(f"  计划ID: {final_plan.plan_id}")
    print(f"  历史记录数: {len(travel_agent.plan_history)}")
    print(f"  用户反馈数: {len(travel_agent.user_feedback_history)}")
    
    return final_plan

def test_formatted_output():
    """测试格式化输出"""
    print("\n📄 格式化输出测试")
    print("=" * 50)
    
    travel_agent = TravelAgentService()
    
    plan = travel_agent.create_travel_plan(
        origin="虹桥机场",
        destinations=["南京路", "外滩", "东方明珠"]
    )
    
    formatted_output = travel_agent.format_travel_plan(plan)
    
    print("🎯 格式化的旅游攻略:")
    print(formatted_output)

def main():
    """主测试函数"""
    print("🧪 智能旅游攻略规划Agent测试套件")
    print("=" * 60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"MCP服务: 天气 + 人流 + 交通 + 导航")
    print(f"智能特性: 天气感知 + 交通优化 + 用户偏好 + RAG增强")
    print()
    
    try:
        # 测试1: 基础规划
        plan1 = test_basic_travel_planning()
        
        # 等待避免API限制
        time.sleep(2)
        
        # 测试2: 天气处理
        test_weather_condition_handling()
        
        # 等待避免API限制
        time.sleep(2)
        
        # 测试3: 交通优化
        test_traffic_optimization()
        
        # 等待避免API限制 
        time.sleep(2)
        
        # 测试4: 偏好调整
        initial_plan, adjusted_plan = test_user_preference_adjustment()
        
        # 等待避免API限制
        time.sleep(2)
        
        # 测试5: RAG整合
        enhanced_plan = test_rag_integration()
        
        # 等待避免API限制
        time.sleep(2)
        
        # 测试6: 完整工作流程
        final_plan = test_comprehensive_workflow()
        
        # 测试7: 格式化输出
        test_formatted_output()
        
        print("\n🎉 所有测试完成！")
        print("\n💡 智能旅游攻略Agent特性总结:")
        print("  ✅ 多源数据整合 - 天气、人流、交通、导航MCP服务深度融合")
        print("  ✅ 智能决策流程 - 天气检查 → 路线规划 → 路况分析 → 人流评估")
        print("  ✅ 动态调整机制 - 极端天气自动调整，交通拥堵智能绕行")
        print("  ✅ 用户偏好学习 - 多轮交互优化，个性化推荐")
        print("  ✅ RAG知识增强 - 结合本地知识库，提供深度建议")
        print("  ✅ 综合评分系统 - 天气、交通、人流多维度量化评估")
        print("  ✅ 实时优化建议 - 基于实时数据提供动态调整方案")
        
    except Exception as e:
        print(f"❌ 测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

