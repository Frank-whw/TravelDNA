import os
import re
import requests
from dotenv import load_dotenv
from datetime import datetime
import json
import time
from mcp_services import MCPServiceManager, WeatherMCPService, CrowdMCPService, TrafficMCPService
from mcp_rag_integration import EnhancedTourismAssistant, MCPRAGIntegrator
from traffic_service import TrafficService, get_attraction_traffic, analyze_route_traffic, format_traffic_for_agent

load_dotenv()

class TourismAssistant:
    """上海旅游AI助手，集成MCP+RAG服务"""
    
    def __init__(self, api_key=None, model="doubao-1-5-pro-32k-250115", use_enhanced=True):
        """
        初始化旅游助手
        Args:
            api_key: API密钥
            model: 使用的模型名称
            use_enhanced: 是否使用增强版MCP+RAG系统
        """
        self.api_url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key or os.getenv('DOUBAO_API_KEY')}",
            "Content-Type": "application/json"
        }
        self.model = model
        self.api_key = api_key or os.getenv('DOUBAO_API_KEY')
        self.documents = []
        
        # 选择使用增强版或传统版
        self.use_enhanced = use_enhanced
        if use_enhanced:
            # 初始化增强版助手
            self.enhanced_assistant = EnhancedTourismAssistant(api_key=self.api_key)
            self.enhanced_available = False
        else:
            # 初始化传统MCP服务管理器
            self.mcp_manager = MCPServiceManager()
            self.enhanced_assistant = None
        
        # 初始化交通服务
        self.traffic_service = TrafficService()
        
        # 上海旅游知识库
        self.shanghai_knowledge = {
            "attractions": {
                "外滩": {
                    "description": "上海最著名的地标，黄浦江畔的万国建筑博览群",
                    "best_time": "晚上观赏夜景最佳",
                    "duration": "2-3小时",
                    "tips": "建议选择合适的观景位置拍照"
                },
                "东方明珠": {
                    "description": "上海标志性电视塔，可俯瞰全城美景",
                    "best_time": "日落时分最美",
                    "duration": "1.5-2小时",
                    "tips": "建议提前预订门票，避免排队"
                },
                "南京路": {
                    "description": "中华商业第一街，购物和美食的天堂",
                    "best_time": "全天开放，晚上更有氛围",
                    "duration": "3-4小时",
                    "tips": "注意保管随身物品，人流量大"
                },
                "豫园": {
                    "description": "明代古典园林，体验传统江南文化",
                    "best_time": "上午人少时参观",
                    "duration": "2-3小时",
                    "tips": "可以顺便游览城隍庙"
                },
                "迪士尼": {
                    "description": "上海迪士尼乐园，梦幻童话世界",
                    "best_time": "工作日人相对较少",
                    "duration": "全天",
                    "tips": "建议下载官方APP，合理规划路线"
                }
            },
            "transportation": {
                "地铁": "上海地铁网络发达，覆盖主要景点",
                "出租车": "起步价14元，可使用打车软件",
                "公交": "2元起步，支持交通卡和手机支付",
                "共享单车": "适合短距离出行，注意停放规范"
            },
            "food": {
                "本帮菜": "红烧肉、白切鸡、油爆虾等经典菜肴",
                "小笼包": "南翔小笼包是上海特色点心",
                "生煎包": "底部酥脆，汁水丰富",
                "糖醋里脊": "酸甜可口的上海家常菜"
            }
        }

    def _call_doubao_api(self, prompt):
        """调用豆包API获取回复"""
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                return f"API请求失败：{response.status_code} - {response.text}"
                
        except Exception as e:
            return f"API调用异常：{str(e)}"

    def _extract_keywords(self, query):
        """从查询中提取关键词"""
        # 中文分词简化版
        keywords = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', query.lower())
        return [kw for kw in keywords if len(kw) > 1]

    def _search_knowledge_base(self, query):
        """搜索本地知识库"""
        keywords = self._extract_keywords(query)
        relevant_info = []
        
        # 搜索景点信息
        for attraction, info in self.shanghai_knowledge["attractions"].items():
            if any(keyword in attraction or keyword in info["description"] for keyword in keywords):
                relevant_info.append(f"**{attraction}**：{info['description']}")
                relevant_info.append(f"最佳游览时间：{info['best_time']}")
                relevant_info.append(f"建议游览时长：{info['duration']}")
                relevant_info.append(f"小贴士：{info['tips']}")
        
        # 搜索文档库
        if self.documents:
            doc_matches = []
            for doc in self.documents:
                score = sum(1 for keyword in keywords if keyword in doc.lower())
                if score > 0:
                    doc_matches.append((doc, score))
            
            # 按相关性排序，取前3个
            doc_matches.sort(key=lambda x: x[1], reverse=True)
            for doc, _ in doc_matches[:3]:
                relevant_info.append(doc[:300] + "...")
        
        return "\n\n".join(relevant_info) if relevant_info else ""

    def _extract_attraction_from_query(self, query):
        """从查询中提取景点名称"""
        # 遍历知识库中的景点名称
        for attraction in self.shanghai_knowledge["attractions"].keys():
            if attraction in query:
                return attraction
        
        # 常见景点关键词匹配
        attraction_keywords = {
            "迪士尼": "上海迪士尼度假区",
            "外滩": "外滩", 
            "东方明珠": "东方明珠",
            "南京路": "南京路步行街",
            "豫园": "豫园",
            "田子坊": "田子坊",
            "淮海路": "淮海路",
            "武康路": "武康路",
            "城隍庙": "城隍庙旅游区"
        }
        
        for keyword, attraction in attraction_keywords.items():
            if keyword in query:
                return attraction
        
        return "上海市中心"  # 默认景点
    
    def _format_mcp_response(self, mcp_results, query):
        """格式化MCP服务响应"""
        if not mcp_results:
            return "暂无实时信息"
        
        response_parts = []
        attraction = mcp_results.get('attraction', '指定地点')
        
        response_parts.append(f"📍 {attraction} 实时信息")
        response_parts.append("=" * 30)
        
        # 天气信息
        if 'weather' in mcp_results:
            weather = mcp_results['weather']
            response_parts.append(f"🌤️ 天气: {weather.get('weather', '未知')} {weather.get('temperature', '未知')}")
            response_parts.append(f"💧 湿度: {weather.get('humidity', '未知')} | 🌬️ 风力: {weather.get('wind', '未知')}")
            response_parts.append(f"🌍 空气质量: {weather.get('air_quality', '未知')}")
            if weather.get('recommendation'):
                response_parts.append(f"💡 建议: {weather['recommendation']}")
        
        # 人流信息
        if 'crowd' in mcp_results:
            crowd = mcp_results['crowd']
            response_parts.append(f"👥 人流状况: {crowd.get('crowd_level', '未知')}")
            response_parts.append(f"⏰ 预计等待: {crowd.get('wait_time', '未知')}")
            if crowd.get('best_visit_time'):
                response_parts.append(f"🎯 最佳时间: {crowd['best_visit_time']}")
            if crowd.get('recommendation'):
                response_parts.append(f"💡 建议: {crowd['recommendation']}")
        
        # 交通信息
        if 'traffic' in mcp_results:
            traffic = mcp_results['traffic']
            response_parts.append(f"🚇 交通状况: {traffic.get('traffic_status', '未知')}")
            response_parts.append(f"⏱️ 预计时间: {traffic.get('estimated_time', '未知')}")
            response_parts.append(f"🎯 推荐路线: {traffic.get('best_route', '未知')}")
            if traffic.get('recommendation'):
                response_parts.append(f"💡 建议: {traffic['recommendation']}")
        
        return "\n".join(response_parts)

    def _needs_mcp_services(self, query):
        """判断是否需要调用MCP服务"""
        mcp_keywords = [
            # 天气相关
            "天气", "温度", "下雨", "晴天", "阴天", "风", "湿度", "空气质量", "紫外线",
            # 人流量相关
            "人多", "人少", "拥挤", "排队", "人流", "游客", "等待", "热门", "现在",
            # 交通相关
            "交通", "堵车", "路况", "开车", "地铁", "公交", "停车", "路线", "怎么去",
            # 实时信息相关
            "实时", "现在", "目前", "最新", "当前", "情况", "状态"
        ]
        
        return any(keyword in query for keyword in mcp_keywords)

    def _create_enhanced_prompt(self, query, knowledge_context="", mcp_results=None, traffic_info=None):
        """创建增强的提示词，整合所有信息源"""
        
        current_time = datetime.now().strftime('%Y年%m月%d日 %H:%M')
        
        prompt_parts = [
            f"当前时间：{current_time}",
            "",
            "你是一个专业的上海旅游AI助手，具备以下能力：",
            "1. 提供上海各景点的详细介绍和游览建议",
            "2. 获取实时天气、人流量、交通状况信息",
            "3. 根据实时数据给出个性化的旅游建议",
            "4. 帮助游客规划最佳的旅游路线",
            "",
            "请基于以下信息回答用户问题，确保信息准确、实用、友好："
        ]
        
        # 添加实时数据（天气、人流、交通）
        if mcp_results or traffic_info:
            prompt_parts.append("\n🔴 实时数据（优先参考并融入攻略建议）：")
            
            # 处理天气数据
            if 'weather' in mcp_results and mcp_results['weather']:
                weather = mcp_results['weather']
                weather_info = []
                if weather.get('district'):
                    weather_info.append(f"地点：{weather.get('district')}")
                weather_info.append(f"温度：{weather.get('temperature', '未知')}")
                weather_info.append(f"天气：{weather.get('weather', '未知')}")
                weather_info.append(f"湿度：{weather.get('humidity', '未知')}")
                weather_info.append(f"风力：{weather.get('wind', '未知')}")
                if weather.get('recommendation'):
                    weather_info.append(f"建议：{weather.get('recommendation')}")
                if weather.get('report_time'):
                    weather_info.append(f"数据时间：{weather.get('report_time')}")
                prompt_parts.append(f"☀️ 天气状况：{' | '.join(weather_info)}")
            
            # 处理人流数据
            if 'crowd' in mcp_results and mcp_results['crowd']:
                crowd = mcp_results['crowd']
                crowd_info = []
                crowd_info.append(f"人流状况：{crowd.get('crowd_level', '未知')}")
                crowd_info.append(f"等待时间：{crowd.get('wait_time', '未知')}")
                if crowd.get('best_visit_time'):
                    crowd_info.append(f"最佳时间：{crowd.get('best_visit_time')}")
                prompt_parts.append(f"👥 人流信息：{' | '.join(crowd_info)}")
            
            # 处理传统交通数据
            if mcp_results and 'traffic' in mcp_results and mcp_results['traffic']:
                traffic = mcp_results['traffic']
                if isinstance(traffic, dict):  # 确保是字典类型
                    traffic_info_parts = []
                    traffic_info_parts.append(f"交通状况：{traffic.get('traffic_status', '未知')}")
                    traffic_info_parts.append(f"预计时间：{traffic.get('estimated_time', '未知')}")
                    traffic_info_parts.append(f"推荐路线：{traffic.get('best_route', '未知')}")
                    prompt_parts.append(f"🚗 交通信息：{' | '.join(traffic_info_parts)}")
            
            # 处理详细交通数据（新版）
            if traffic_info and traffic_info.get("has_traffic_data"):
                traffic_details = []
                traffic_details.append(f"状况：{traffic_info.get('traffic_status', '未知')}")
                traffic_details.append(f"拥堵度：{traffic_info.get('average_congestion', '未知')}")
                traffic_details.append(f"建议：{traffic_info.get('suggestion', '未知')}")
                traffic_details.append(f"推荐交通：{traffic_info.get('best_transport', '地铁')}")
                traffic_details.append(f"预计用时：{traffic_info.get('estimated_time', '未知')}")
                prompt_parts.append(f"🚦 详细交通信息：{' | '.join(traffic_details)}")
            
            # 添加天气预报信息
            if 'weather_forecast' in mcp_results and mcp_results['weather_forecast']:
                forecast = mcp_results['weather_forecast']
                if forecast.get('forecasts'):
                    forecast_info = []
                    for day_forecast in forecast['forecasts'][:3]:
                        date = day_forecast.get('date', '')
                        day_weather = day_forecast.get('dayweather', '未知')
                        night_weather = day_forecast.get('nightweather', '未知')
                        day_temp = day_forecast.get('daytemp', '未知')
                        night_temp = day_forecast.get('nighttemp', '未知')
                        forecast_info.append(f"{date}: {day_weather}/{night_weather} {day_temp}°C/{night_temp}°C")
                    prompt_parts.append(f"📅 未来3天天气预报：{' | '.join(forecast_info)}")
            
            prompt_parts.append("\n⚠️ 重要指令：")
            prompt_parts.append("1. 必须生成完整详细的旅游攻略，不能只列出实时数据")
            prompt_parts.append("2. 将当前天气和未来天气预报信息自然融入到攻略建议中")
            prompt_parts.append("3. 根据天气预报调整多日行程安排（如雨天推荐室内活动）")
            prompt_parts.append("4. 提供具体的游览建议、注意事项、最佳时间安排等")
            prompt_parts.append("5. 结合实时数据给出个性化建议（如避开人流高峰、选择最佳交通路线）")
        
        # 添加知识库信息
        if knowledge_context:
            prompt_parts.append(f"\n📚 旅游知识库：\n{knowledge_context}")
        
        # 添加用户问题
        prompt_parts.extend([
            "",
            f"👤 用户问题：{query}",
            "",
            "请提供详细、实用的攻略回答，包括：",
            "- 直接回答用户问题",
            "- **必须结合实时天气数据给出游览建议**",
            "- 根据天气状况调整活动安排和注意事项",
            "- 提供相关的实用信息和小贴士",
            "- 如果合适，推荐相关景点或活动",
            "",
            "回答要求：",
            "- 友好、专业的旅游攻略语调",
            "- 信息准确、具体、实用",
            "- 适当使用表情符号增加亲和力",
            "- **天气信息必须融入到攻略建议中，不能只是简单罗列**",
            "- 根据实时数据调整建议（如雨天推荐室内活动等）"
        ])
        
        return "\n".join(prompt_parts)

    def initialize_enhanced_system(self):
        """初始化增强版系统"""
        if self.use_enhanced and self.enhanced_assistant:
            try:
                self.enhanced_available = self.enhanced_assistant.initialize()
                if self.enhanced_available:
                    print("✅ MCP+RAG增强系统初始化成功")
                else:
                    print("⚠️ MCP+RAG系统初始化失败，将使用传统模式")
            except Exception as e:
                print(f"❌ 增强系统初始化错误: {e}")
                self.enhanced_available = False

    def generate_response(self, query):
        """
        生成智能回复，优先使用MCP+RAG集成系统
        Args:
            query: 用户查询
        Returns:
            str: 生成的回复
        """
        try:
            # 使用增强版系统
            if self.use_enhanced and self.enhanced_assistant and self.enhanced_available:
                return self.enhanced_assistant.generate_response(query)
            
            # 降级到传统模式
            return self._traditional_generate_response(query)
            
        except Exception as e:
            return f"😅 抱歉，处理您的问题时出现了错误：{str(e)}\n\n请稍后再试，或者换个方式问问我。"
    
    def _traditional_generate_response(self, query):
        """传统模式的回复生成"""
        try:
            # 1. 搜索本地知识库
            knowledge_context = self._search_knowledge_base(query)
            
            # 2. 获取实时信息（天气、人流、交通）
            mcp_results = None
            traffic_info = None
            should_get_realtime = self._needs_mcp_services(query) or any(keyword in query for keyword in ["攻略", "建议", "推荐", "游览", "去", "玩", "路线", "交通", "怎么去"])
            
            if should_get_realtime:
                print("🔄 正在获取实时信息（天气、人流、交通）...")
                try:
                    # 提取景点名称
                    attraction = self._extract_attraction_from_query(query)
                    if attraction:
                        # 获取天气和人流信息
                        if hasattr(self, 'mcp_manager'):
                            mcp_results = self.mcp_manager.get_comprehensive_info(attraction)
                        else:
                            temp_manager = MCPServiceManager()
                            mcp_results = temp_manager.get_comprehensive_info(attraction)
                        
                        # 获取交通信息（通过MCP框架）
                        # 交通信息已经包含在mcp_results中，无需单独获取
                        traffic_info = None
                        
                        if mcp_results:
                            print("✅ 已获取实时天气、人流、交通数据")
                        else:
                            print("⚠️ 无法获取实时数据，将使用基础知识库")
                        
                except Exception as e:
                    print(f"⚠️ 获取实时数据时出错: {e}")
                    mcp_results = None
                    traffic_info = None
                
                # 如果获取到MCP数据，格式化返回
                if mcp_results:
                    formatted_mcp = self._format_mcp_response(mcp_results, query)
                    
                    # 只有在非常明确的纯实时信息查询时才直接返回MCP数据
                    # 比如"外滩现在天气"，"东方明珠人流状况"等
                    pure_realtime_keywords = ["现在天气", "实时天气", "人流状况", "交通状况", "现在情况"]
                    is_pure_realtime = any(keyword in query for keyword in pure_realtime_keywords)
                    
                    # 如果包含"攻略"、"建议"、"推荐"等词，则一定要生成完整回答
                    needs_full_guide = any(keyword in query for keyword in ["攻略", "建议", "推荐", "规划", "游览", "怎么玩", "去玩"])
                    
                    # 只有在明确的纯实时查询且没有攻略需求时才直接返回
                    if is_pure_realtime and not needs_full_guide and not knowledge_context:
                        return formatted_mcp
            
            # 3. 创建增强提示词（包含交通信息）
            enhanced_prompt = self._create_enhanced_prompt(query, knowledge_context, mcp_results, traffic_info)
            
            # 4. 调用AI生成回复
            ai_response = self._call_doubao_api(enhanced_prompt)
            
            # 5. 如果有实时数据，在AI回复后添加实时信息
            if (mcp_results or traffic_info) and "API" not in ai_response:  # 确保AI调用成功
                realtime_info = []
                
                # 添加MCP信息（天气、人流）
                if mcp_results:
                    if hasattr(self, 'mcp_manager'):
                        formatted_mcp = self.mcp_manager.format_response(mcp_results, query)
                    else:
                        formatted_mcp = temp_manager.format_response(mcp_results, query)
                    realtime_info.append(formatted_mcp)
                
                # 添加交通信息
                if traffic_info and traffic_info.get("has_traffic_data"):
                    formatted_traffic = format_traffic_for_agent(traffic_info)
                    realtime_info.append(formatted_traffic)
                
                if realtime_info:
                    return f"{ai_response}\n\n{'-'*30}\n💡 实时信息补充：\n{chr(10).join(realtime_info)}"
            
            return ai_response
            
        except Exception as e:
            return f"😅 抱歉，处理您的问题时出现了错误：{str(e)}\n\n请稍后再试，或者换个方式问问我。"

    def get_attraction_suggestions(self, preferences=None):
        """根据偏好推荐景点"""
        if not preferences:
            return list(self.shanghai_knowledge["attractions"].keys())
        
        # 简单的基于关键词的推荐
        suggestions = []
        for attraction, info in self.shanghai_knowledge["attractions"].items():
            if any(pref in info["description"] for pref in preferences):
                suggestions.append(attraction)
        
        return suggestions if suggestions else list(self.shanghai_knowledge["attractions"].keys())

    def plan_route(self, attractions, start_time="09:00"):
        """智能路线规划，集成实时交通数据和出行建议"""
        if not attractions:
            return "请先选择要游览的景点。"
        
        # 获取整条路线的交通分析（使用MCP框架）
        try:
            if hasattr(self, 'mcp_manager'):
                route_traffic_analysis = self.mcp_manager.get_route_traffic_analysis(attractions)
            else:
                temp_manager = MCPServiceManager()
                route_traffic_analysis = temp_manager.get_route_traffic_analysis(attractions)
            print(f"🚦 路线交通分析完成：{route_traffic_analysis.get('overall_status', '未知')}")
        except Exception as e:
            print(f"⚠️ 路线交通分析失败: {e}")
            route_traffic_analysis = {"overall_status": "未知", "attractions_traffic": []}
        
        # 获取每个景点的完整实时信息
        route_plan = []
        current_time = start_time
        attractions_traffic = route_traffic_analysis.get("attractions_traffic", [])
        
        for i, attraction in enumerate(attractions):
            try:
                # 获取天气和人流信息
                if hasattr(self, 'mcp_manager'):
                    weather_info = self.mcp_manager.weather_service.get_weather(attraction)
                    crowd_info = self.mcp_manager.crowd_service.get_crowd_info(attraction)
                else:
                    temp_manager = MCPServiceManager()
                    weather_info = temp_manager.weather_service.get_weather(attraction)
                    crowd_info = temp_manager.crowd_service.get_crowd_info(attraction)
                
                # 获取对应的交通信息
                traffic_info = attractions_traffic[i] if i < len(attractions_traffic) else {}
                
                route_plan.append({
                    "order": i + 1,
                    "attraction": attraction,
                    "suggested_time": current_time,
                    "weather": {
                        "temperature": weather_info.get("temperature", "未知"),
                        "condition": weather_info.get("weather", "未知"),
                        "recommendation": weather_info.get("recommendation", "")
                    },
                    "crowd_level": crowd_info.get("crowd_level", "未知"),
                    "traffic": {
                        "status": traffic_info.get("traffic_status", "未知"),
                        "suggestion": traffic_info.get("suggestion", "建议使用公共交通"),
                        "best_transport": traffic_info.get("best_transport", "地铁"),
                        "congestion": traffic_info.get("average_congestion", "未知")
                    },
                    "duration": self.shanghai_knowledge["attractions"].get(attraction, {}).get("duration", "2小时")
                })
                
            except Exception as e:
                print(f"⚠️ 获取 {attraction} 实时信息失败: {e}")
                # 使用基础信息
                route_plan.append({
                    "order": i + 1,
                    "attraction": attraction,
                    "suggested_time": current_time,
                    "weather": {"temperature": "未知", "condition": "未知", "recommendation": ""},
                    "crowd_level": "未知",
                    "traffic": {"status": "未知", "suggestion": "建议使用公共交通", "best_transport": "地铁", "congestion": "未知"},
                    "duration": self.shanghai_knowledge["attractions"].get(attraction, {}).get("duration", "2小时")
                })
            
            # 简单的时间推进
            hour, minute = map(int, current_time.split(":"))
            hour += 2  # 假设每个景点需要2小时
            if hour >= 24:
                hour -= 24
            current_time = f"{hour:02d}:{minute:02d}"
        
        return route_plan

    def set_documents(self, documents):
        """设置文档库"""
        self.documents = documents
        print(f"✅ 已加载 {len(documents)} 个旅游文档到知识库")

    def add_document(self, document):
        """添加单个文档"""
        if document and document.strip():
            self.documents.append(document.strip())
            return True
        return False

    def get_service_status(self):
        """获取各服务状态"""
        status = {
            "AI服务": "✅ 正常" if self.api_key else "❌ 未配置API密钥",
            "运行模式": "🚀 增强模式(MCP+RAG)" if self.use_enhanced else "🔧 传统模式",
        }
        
        if self.use_enhanced and self.enhanced_assistant:
            status["增强系统"] = "✅ 可用" if self.enhanced_available else "❌ 不可用"
            if self.enhanced_available:
                # 获取集成系统状态
                try:
                    enhanced_status = self.enhanced_assistant.integrator.get_system_status()
                    status.update({
                        "MCP服务": "✅ 可用" if enhanced_status.get('mcp_available') else "❌ 不可用",
                        "RAG检索": "✅ 可用" if enhanced_status.get('rag_available') else "❌ 不可用",
                        "知识库文档": f"✅ {enhanced_status.get('rag_stats', {}).get('traditional_docs', 0)}个文档" if enhanced_status.get('rag_available') else "❌ 未加载"
                    })
                except:
                    status.update({
                        "MCP服务": "✅ 可用",
                        "RAG检索": "❓ 状态未知",
                        "知识库文档": "❓ 状态未知"
                    })
        else:
            status.update({
                "天气服务": "✅ 可用",
                "人流量服务": "✅ 可用", 
                "交通服务": "✅ 可用",
                "知识库": f"✅ 已加载{len(self.documents)}个文档"
            })
        
        return status


# 兼容性保持 - 保留原有的MCP服务类（已整合到mcp_services.py中）
class MCPService:
    """保留原有接口以确保兼容性"""
    BASE_URL = "https://sh-mcp-api.example.com"
    
    @classmethod
    def fetch_data(cls, endpoint, params):
        try:
            response = requests.get(f"{cls.BASE_URL}/{endpoint}", params=params, timeout=5)
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            print(f"MCP服务调用异常: {str(e)}")
            return None


class WeatherMCPService(MCPService):
    @classmethod
    def get_weather(cls, attraction):
        return cls.fetch_data("weather", {"location": f"上海{attraction}"}) or {
            "temperature": 25,
            "condition": "晴",
            "update_time": datetime.now().strftime('%Y-%m-%d %H:%M')
        }


class TrafficMCPService(MCPService):
    @classmethod
    def get_traffic(cls, attraction):
        return cls.fetch_data("traffic", {"location": f"上海{attraction}"}) or {
            "congestion_level": "畅通",
            "suggested_route": "延安高架路",
            "update_time": datetime.now().strftime('%H:%M')
        }


# 使用示例和测试代码
if __name__ == "__main__":
    # 初始化增强版助手
    print("🚀 初始化上海旅游AI助手（MCP+RAG增强版）")
    assistant = TourismAssistant(use_enhanced=True)
    
    # 初始化增强系统
    assistant.initialize_enhanced_system()
    
    # 测试服务状态
    print("\n=== 服务状态检查 ===")
    status = assistant.get_service_status()
    for service, state in status.items():
        print(f"{service}: {state}")
    
    print("\n=== 测试MCP+RAG集成系统 ===")
    
    # 测试问题（包含不同类型的查询）
    test_queries = [
        "外滩现在天气怎么样？",  # 实时查询
        "东方明珠的详细介绍",    # 详细信息查询
        "豫园有什么特色？开放时间？", # 实用信息查询
        "上海博物馆游览攻略",    # 攻略查询
        "南京路现在人多吗？",    # 人流查询
        "帮我规划上海一日游",    # 规划查询
        "迪士尼乐园今天适合去吗？", # 综合查询
        "上海有什么特色美食？"   # 一般查询
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 测试 {i}: {query}")
        print("-" * 50)
        try:
            response = assistant.generate_response(query)
            print("💬 AI回答：")
            print(response)
        except Exception as e:
            print(f"❌ 错误：{e}")
        print("=" * 60)
    
    # 传统模式对比测试
    print(f"\n=== 传统模式对比测试 ===")
    traditional_assistant = TourismAssistant(use_enhanced=False)
    
    compare_query = "外滩现在情况如何？"
    print(f"📝 对比查询：{compare_query}")
    print("-" * 50)
    
    print("🔧 传统模式回答：")
    traditional_response = traditional_assistant.generate_response(compare_query)
    print(traditional_response)
    
    print("\n" + "=" * 60)