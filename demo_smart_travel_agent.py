#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能旅行攻略规划师演示脚本
展示完整的工作流程和功能特性
"""

import sys
import time
import json
from typing import List, Dict
from datetime import datetime

try:
    from smart_travel_agent import SmartTravelAgent
    from rag_knowledge_base import get_rag_knowledge
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print("请确保所有必要文件都存在：smart_travel_agent.py, rag_knowledge_base.py, mcp_services.py, config.py")
    sys.exit(1)

class TravelAgentDemo:
    """智能旅行攻略规划师演示器"""
    
    def __init__(self):
        """初始化演示器"""
        print("🚀 正在初始化智能旅行攻略规划师...")
        try:
            self.agent = SmartTravelAgent()
            self.rag_kb = get_rag_knowledge()
            print("✅ 初始化完成！")
        except Exception as e:
            print(f"❌ 初始化失败: {e}")
            sys.exit(1)
        
        # 预设测试用例
        self.test_cases = [
            {
                "name": "完整旅行规划",
                "queries": [
                    "我想明天从人民广场去外滩看夜景",
                    "人民广场"  # 澄清起点
                ],
                "description": "完整的旅行攻略规划流程，包括天气、交通、RAG增强等"
            },
            {
                "name": "极端天气处理", 
                "queries": [
                    "今天想去迪士尼，天气怎么样",
                ],
                "description": "测试极端天气时的智能决策和建议调整"
            },
            {
                "name": "用户偏好收集",
                "queries": [
                    "我想去浦东新区玩",
                    "陆家嘴",  # 澄清具体地点
                    "摄影",    # 澄清活动偏好
                    "地铁"     # 澄清交通偏好
                ],
                "description": "测试多轮对话和用户偏好收集"
            },
            {
                "name": "RAG知识展示",
                "queries": [
                    "给我详细介绍一下东方明珠的游览攻略"
                ],
                "description": "展示RAG知识库的深度洞察能力"
            },
            {
                "name": "交通规划",
                "queries": [
                    "从虹桥机场到陆家嘴怎么走，路况如何"
                ],
                "description": "测试交通路径规划和实时路况分析"
            }
        ]
    
    def run_interactive_demo(self):
        """运行交互式演示"""
        print("\n" + "="*60)
        print("🤖 智能旅行攻略规划师 - 交互式演示")
        print("="*60)
        print("功能特色：")
        print("• 🌤️  实时天气感知与风险评估")
        print("• 🚦 智能交通路况分析")
        print("• 👥 人流预测与错峰建议")  
        print("• 🗺️  精准导航路径规划")
        print("• 📚 RAG知识库深度洞察")
        print("• 💬 多轮对话智能决策")
        print("\n输入 'quit' 退出，'demo' 查看预设演示")
        print("-"*60)
        
        user_id = "demo_user"
        
        while True:
            user_input = input("\n👤 您: ").strip()
            
            if user_input.lower() in ['quit', 'exit', '退出']:
                print("👋 感谢体验智能旅行攻略规划师！")
                break
            
            if user_input.lower() == 'demo':
                self.run_preset_demos()
                continue
            
            if not user_input:
                continue
            
            try:
                print("\n🤖 正在为您规划最优攻略...")
                start_time = time.time()
                
                response = self.agent.process_user_request(user_input, user_id)
                
                end_time = time.time()
                print(f"\n🤖 规划师: {response}")
                print(f"\n⏱️  处理时间: {end_time - start_time:.2f}秒")
                print("-"*60)
                
            except Exception as e:
                print(f"❌ 处理请求时出错: {e}")
                print("请稍后重试或联系技术支持")
    
    def run_preset_demos(self):
        """运行预设演示案例"""
        print("\n" + "="*60)
        print("📋 预设演示案例")
        print("="*60)
        
        for i, case in enumerate(self.test_cases, 1):
            print(f"\n{i}. {case['name']}")
            print(f"   {case['description']}")
        
        while True:
            try:
                choice = input(f"\n请选择演示案例 (1-{len(self.test_cases)}) 或 'back' 返回: ").strip()
                
                if choice.lower() == 'back':
                    break
                
                case_index = int(choice) - 1
                if 0 <= case_index < len(self.test_cases):
                    self.run_single_demo(self.test_cases[case_index])
                else:
                    print("❌ 无效选择，请重新输入")
                    
            except ValueError:
                print("❌ 请输入有效数字")
            except KeyboardInterrupt:
                print("\n👋 演示已中断")
                break
    
    def run_single_demo(self, test_case: Dict):
        """运行单个演示案例"""
        print(f"\n{'='*60}")
        print(f"🎯 演示案例: {test_case['name']}")
        print(f"📝 说明: {test_case['description']}")
        print(f"{'='*60}")
        
        user_id = f"demo_{test_case['name']}"
        queries = test_case['queries']
        
        for i, query in enumerate(queries, 1):
            print(f"\n步骤 {i}/{len(queries)}")
            print(f"👤 用户: {query}")
            print("🤖 正在处理...")
            
            try:
                start_time = time.time()
                response = self.agent.process_user_request(query, user_id)
                end_time = time.time()
                
                print(f"\n🤖 规划师: {response}")
                print(f"\n⏱️ 处理时间: {end_time - start_time:.2f}秒")
                
                if i < len(queries):
                    input("\n按 Enter 继续下一步...")
                    
            except Exception as e:
                print(f"❌ 处理失败: {e}")
                break
        
        print(f"\n✅ 演示案例 '{test_case['name']}' 完成")
        input("\n按 Enter 返回演示菜单...")
    
    def run_performance_test(self):
        """运行性能测试"""
        print("\n" + "="*60)
        print("⚡ 性能测试")
        print("="*60)
        
        test_queries = [
            "我想去外滩",
            "从人民广场到东方明珠",
            "迪士尼乐园攻略",
            "豫园一日游"
        ]
        
        results = []
        
        for query in test_queries:
            print(f"\n测试查询: {query}")
            
            start_time = time.time()
            try:
                response = self.agent.process_user_request(query, "perf_test")
                end_time = time.time()
                duration = end_time - start_time
                
                results.append({
                    "query": query,
                    "duration": duration,
                    "success": True,
                    "response_length": len(response)
                })
                
                print(f"✅ 完成 - {duration:.2f}秒")
                
            except Exception as e:
                end_time = time.time()
                duration = end_time - start_time
                
                results.append({
                    "query": query,
                    "duration": duration,
                    "success": False,
                    "error": str(e)
                })
                
                print(f"❌ 失败 - {duration:.2f}秒 - {e}")
        
        # 性能统计
        print(f"\n📊 性能统计")
        print("-"*40)
        
        successful_tests = [r for r in results if r["success"]]
        if successful_tests:
            avg_duration = sum(r["duration"] for r in successful_tests) / len(successful_tests)
            max_duration = max(r["duration"] for r in successful_tests)
            min_duration = min(r["duration"] for r in successful_tests)
            
            print(f"成功率: {len(successful_tests)}/{len(results)} ({len(successful_tests)/len(results)*100:.1f}%)")
            print(f"平均响应时间: {avg_duration:.2f}秒")
            print(f"最快响应: {min_duration:.2f}秒")
            print(f"最慢响应: {max_duration:.2f}秒")
        else:
            print("❌ 所有测试都失败了")
    
    def show_features(self):
        """展示功能特性"""
        print("\n" + "="*60)
        print("🌟 智能旅行攻略规划师功能特性")
        print("="*60)
        
        features = [
            {
                "title": "🧠 智能决策引擎",
                "details": [
                    "根据用户输入智能分析意图",
                    "动态调用相应的MCP服务",
                    "综合多维度信息生成最优方案"
                ]
            },
            {
                "title": "🌤️ 环境感知能力", 
                "details": [
                    "实时天气预报与风险评估",
                    "极端天气智能预警和方案调整",
                    "季节性出行建议"
                ]
            },
            {
                "title": "🚦 交通智能分析",
                "details": [
                    "实时路况监测与避堵路线",
                    "多模式交通方案对比",
                    "精准导航步骤指引"
                ]
            },
            {
                "title": "👥 人流预测优化",
                "details": [
                    "景点人流密度预测",
                    "错峰游览时间建议",
                    "替代景点智能推荐"
                ]
            },
            {
                "title": "📚 RAG知识增强",
                "details": [
                    "深度景点游览攻略",
                    "隐藏玩法和拍照技巧",
                    "当地美食和实用贴士"
                ]
            },
            {
                "title": "💬 多轮对话交互",
                "details": [
                    "自然语言理解和澄清",
                    "个性化偏好收集",
                    "上下文状态维护"
                ]
            }
        ]
        
        for feature in features:
            print(f"\n{feature['title']}")
            for detail in feature['details']:
                print(f"  • {detail}")
        
        print(f"\n{'='*60}")

def main():
    """主函数"""
    print("🎉 欢迎使用智能旅行攻略规划师演示系统")
    
    try:
        demo = TravelAgentDemo()
        
        while True:
            print("\n" + "="*60)
            print("📋 请选择演示模式：")
            print("1. 🔄 交互式对话演示")
            print("2. 📋 预设案例演示") 
            print("3. ⚡ 性能测试")
            print("4. 🌟 功能特性介绍")
            print("5. 🚪 退出")
            print("="*60)
            
            choice = input("请输入选择 (1-5): ").strip()
            
            if choice == "1":
                demo.run_interactive_demo()
            elif choice == "2":
                demo.run_preset_demos()
            elif choice == "3":
                demo.run_performance_test()
            elif choice == "4":
                demo.show_features()
            elif choice == "5":
                print("👋 感谢使用智能旅行攻略规划师！")
                break
            else:
                print("❌ 无效选择，请重新输入")
                
    except KeyboardInterrupt:
        print("\n\n👋 演示已中断，感谢使用！")
    except Exception as e:
        print(f"\n❌ 演示系统出错: {e}")

if __name__ == "__main__":
    main()
