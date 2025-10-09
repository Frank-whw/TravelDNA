#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速开始脚本 - 智能旅游规划Agent
"""

from enhanced_travel_agent import EnhancedTravelAgent

def main():
    """快速开始示例"""
    print("=" * 80)
    print("🎉 欢迎使用智能旅游规划Agent系统！")
    print("=" * 80)
    print()
    print("这是一个基于思考链的AI旅游规划系统，具备：")
    print("  ✓ 透明的思考过程")
    print("  ✓ 人文关怀（识别同伴、情感需求等）")
    print("  ✓ 数据驱动决策（天气、路况、POI等）")
    print("  ✓ 智能API调用（只调用必要的服务）")
    print()
    print("=" * 80)
    
    # 初始化Agent
    try:
        print("\n🚀 正在初始化Agent...")
        agent = EnhancedTravelAgent()
        print("✅ Agent初始化成功！\n")
    except Exception as e:
        print(f"❌ Agent初始化失败: {e}")
        print("\n请检查：")
        print("  1. 是否已安装依赖：pip install -r requirements.txt")
        print("  2. 是否已配置.env文件并填入API密钥")
        print()
        return
    
    # 示例查询列表
    examples = [
        "我想带女朋友去上海玩3天，预算2万，想要浪漫氛围",
        "带父母去上海玩5天，要轻松舒适",
        "想了解上海的风土人情，避开热门景点，深度游7天",
        "从外滩到陆家嘴怎么走？",
        "上海未来3天天气怎么样？"
    ]
    
    print("📝 示例查询：")
    for i, example in enumerate(examples, 1):
        print(f"  {i}. {example}")
    print(f"  {len(examples) + 1}. 自定义输入")
    print(f"  0. 退出")
    print()
    
    while True:
        try:
            choice = input("请选择示例（输入数字）或直接输入您的需求: ").strip()
            
            if choice == "0" or choice.lower() in ['quit', 'exit', '退出']:
                print("\n👋 感谢使用，再见！")
                break
            
            # 判断是否是数字选择
            if choice.isdigit():
                choice_num = int(choice)
                if 1 <= choice_num <= len(examples):
                    user_input = examples[choice_num - 1]
                elif choice_num == len(examples) + 1:
                    user_input = input("请输入您的需求: ").strip()
                    if not user_input:
                        continue
                else:
                    print("❌ 无效的选择，请重新输入")
                    continue
            else:
                # 直接作为用户输入
                user_input = choice
                if not user_input:
                    continue
            
            print(f"\n📝 您的需求：{user_input}")
            print()
            
            # 处理用户请求
            response = agent.process_user_request(user_input, show_thoughts=True)
            
            print("\n" + "=" * 80)
            print("🤖 最终攻略：")
            print("=" * 80)
            print(response)
            print("\n" + "=" * 80)
            
            # 询问是否继续
            continue_choice = input("\n是否继续查询？(y/n): ").strip().lower()
            if continue_choice not in ['y', 'yes', '是', '']:
                print("\n👋 感谢使用，再见！")
                break
            
            print("\n" + "=" * 80)
            print()
            
        except KeyboardInterrupt:
            print("\n\n👋 感谢使用，再见！")
            break
        except Exception as e:
            print(f"\n❌ 处理请求时出错: {e}")
            import traceback
            traceback.print_exc()
            
            continue_choice = input("\n是否继续？(y/n): ").strip().lower()
            if continue_choice not in ['y', 'yes', '是', '']:
                break

if __name__ == "__main__":
    main()

