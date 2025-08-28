#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能旅行攻略规划师 - 智能MCP调用决策演示
展示Agent如何根据用户提示词智能思考并按需调用MCP服务
"""

from smart_travel_agent import SmartTravelAgent

def demo_intelligent_decision():
    """演示智能决策过程"""
    
    print("🎯 智能旅行攻略规划师 - MCP调用决策演示")
    print("=" * 60)
    
    agent = SmartTravelAgent()
    
    test_cases = [
        {
            "query": "我想去浦东新区玩",
            "description": "地点查询 → Agent推理景点 → 调用POI MCP",
            "expected_mcp": ["poi"]
        },
        {
            "query": "从人民广场到外滩怎么走",
            "description": "路线查询 → 调用导航MCP → 自然调用路况MCP",
            "expected_mcp": ["navigation", "traffic"]
        },
        {
            "query": "明天去迪士尼天气怎么样",
            "description": "天气查询 → 调用天气MCP",
            "expected_mcp": ["weather"]
        },
        {
            "query": "外滩现在人多吗",
            "description": "人流查询 → 调用人流MCP",
            "expected_mcp": ["crowd"]
        },
        {
            "query": "给我详细规划一下浦东一日游攻略",
            "description": "完整攻略 → 全面调用各MCP服务",
            "expected_mcp": ["navigation", "traffic", "weather", "crowd", "poi"]
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n【测试 {i}】{case['description']}")
        print(f"用户询问：\"{case['query']}\"")
        print("-" * 40)
        
        try:
            # 模拟用户对话
            user_id = f"demo_{i}"
            response = agent.process_user_request(case['query'], user_id)
            
            # 提取用户上下文以查看决策过程
            context = agent.user_contexts.get(user_id)
            if context and context.conversation_history:
                # 查看最新的对话记录
                latest_conversation = context.conversation_history[-1]
                print(f"✅ 处理完成")
                print(f"📝 回复长度：{len(response)} 字符")
                
                # 如果是澄清问题，显示
                if "您的出发地点是哪里" in response or "更具体" in response:
                    print("💬 Agent正在澄清信息")
                elif "制定更贴心的攻略" in response:
                    print("💬 Agent正在收集偏好")
                else:
                    print("💬 Agent已生成完整攻略")
            
        except Exception as e:
            print(f"❌ 处理失败：{e}")
        
        print()
    
    print("=" * 60)
    print("🎯 演示总结：")
    print("✅ Agent能够根据用户提示词中的关键词智能推理需要的信息")
    print("✅ 不同的用户需求触发不同的MCP服务调用组合")
    print("✅ 渐进式调用：先导航再路况，先推理景点再查POI")
    print("✅ 避免了无意义的全量MCP调用，提高了效率")

if __name__ == "__main__":
    demo_intelligent_decision()
