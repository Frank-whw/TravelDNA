#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能旅行攻略规划师Agent
基于用户需求，通过调用MCP服务获取实时数据，结合RAG技术，生成个性化、动态且最优的旅行攻略
"""

import re
import json
import logging
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

# 导入现有模块
try:
    from mcp_services import MCPServiceManager
    from config import Config
    from rag_knowledge_base import get_rag_knowledge
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保mcp_services.py、config.py和rag_knowledge_base.py文件存在")

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ConversationState(Enum):
    """对话状态枚举"""
    INITIAL = "initial"
    LOCATION_CLARIFYING = "location_clarifying"
    PREFERENCE_COLLECTING = "preference_collecting"
    PLANNING = "planning"
    COMPLETED = "completed"

@dataclass
class UserContext:
    """用户上下文信息"""
    origin: Optional[str] = None
    destination: Optional[str] = None
    travel_date: Optional[str] = None
    travel_duration: Optional[int] = None
    preferences: Dict[str, Any] = None
    conversation_state: ConversationState = ConversationState.INITIAL
    conversation_history: List[Dict] = None
    
    def __post_init__(self):
        if self.preferences is None:
            self.preferences = {}
        if self.conversation_history is None:
            self.conversation_history = []

class SmartTravelAgent:
    """智能旅行攻略规划师 - 专业AI助手"""
    
    def __init__(self):
        """初始化智能旅行攻略规划师"""
        self.mcp_manager = MCPServiceManager()
        self.user_contexts = {}  # 存储用户会话上下文
        self.rag_kb = get_rag_knowledge()  # RAG知识库
        
        # 地点映射和坐标信息
        self.location_mapping = {
            # 核心景点
            "外滩": {"coords": "121.4905,31.2404", "district": "黄浦区", "type": "观光"},
            "东方明珠": {"coords": "121.5052,31.2397", "district": "浦东新区", "type": "观光"},
            "上海迪士尼乐园": {"coords": "121.6707,31.1505", "district": "浦东新区", "type": "娱乐"},
            "人民广场": {"coords": "121.4737,31.2316", "district": "黄浦区", "type": "交通枢纽"},
            "南京路步行街": {"coords": "121.4792,31.2350", "district": "黄浦区", "type": "购物"},
            "豫园": {"coords": "121.4925,31.2267", "district": "黄浦区", "type": "文化"},
            "陆家嘴": {"coords": "121.5078,31.2397", "district": "浦东新区", "type": "商务"},
            "徐家汇": {"coords": "121.4418,31.1989", "district": "徐汇区", "type": "购物"},
            "田子坊": {"coords": "121.4695,31.2143", "district": "黄浦区", "type": "文化"},
            "新天地": {"coords": "121.4759,31.2179", "district": "黄浦区", "type": "娱乐"},
            "虹桥机场": {"coords": "121.3364,31.1979", "district": "长宁区", "type": "交通枢纽"},
            "浦东机场": {"coords": "121.7934,31.1434", "district": "浦东新区", "type": "交通枢纽"},
            # 添加更多景点...
        }
        
        # 天气状况关键词映射
        self.weather_conditions = {
            "extreme": ["暴雨", "台风", "大雪", "冰雹", "雷暴"],
            "bad": ["雨", "雪", "雾", "霾", "大风"],
            "good": ["晴", "多云", "阴"]
        }
        
        # 删除原有的简单RAG知识，改用专业的RAG知识库
        
        logger.info("🤖 智能旅行攻略规划师初始化完成")
    
    def process_user_request(self, user_input: str, user_id: str = "default") -> str:
        """
        处理用户请求的主入口函数
        
        Args:
            user_input: 用户输入
            user_id: 用户ID，用于维护会话状态
            
        Returns:
            智能回复内容
        """
        logger.info(f"🎯 收到用户请求: {user_input}")
        
        # 获取或创建用户上下文
        if user_id not in self.user_contexts:
            self.user_contexts[user_id] = UserContext()
        
        context = self.user_contexts[user_id]
        context.conversation_history.append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now().isoformat()
        })
        
        # 根据当前状态和用户输入决定下一步行动
        response = self._route_conversation(user_input, context)
        
        # 记录AI回复
        context.conversation_history.append({
            "role": "assistant", 
            "content": response,
            "timestamp": datetime.now().isoformat()
        })
        
        return response
    
    def _route_conversation(self, user_input: str, context: UserContext) -> str:
        """根据用户输入和上下文状态路由对话"""
        
        # 分析用户输入
        intent = self._analyze_user_intent(user_input)
        
        if intent["is_travel_request"]:
            # 明确的旅行需求
            return self._handle_travel_request(user_input, context, intent)
        elif intent["is_clarification"]:
            # 用户在回答澄清问题
            return self._handle_clarification(user_input, context)
        else:
            # 其他情况 - 引导用户提供旅行需求
            return self._guide_user_to_travel_request(user_input)
    
    def _analyze_user_intent(self, user_input: str) -> Dict[str, Any]:
        """分析用户意图"""
        intent = {
            "is_travel_request": False,
            "is_clarification": False,
            "mentioned_locations": [],
            "travel_keywords": [],
            "time_keywords": [],
            "activity_keywords": []
        }
        
        # 检查旅行相关关键词
        travel_keywords = ["旅游", "攻略", "规划", "去", "玩", "游览", "景点", "路线", "行程"]
        intent["travel_keywords"] = [kw for kw in travel_keywords if kw in user_input]
        
        # 检查地点 - 改进地点识别逻辑
        # 1. 先检查已知地点的直接匹配
        for location in self.location_mapping.keys():
            if location in user_input:
                intent["mentioned_locations"].append(location)
        
        # 2. 如果没有直接匹配，尝试提取可能的地点词汇
        if not intent["mentioned_locations"]:
            # 提取可能的地点名词
            import re
            extracted_locations = set()  # 使用集合避免重复
            
            # 高优先级模式（更精确）
            high_priority_patterns = [
                r"(\w+新区)",  # "xxx新区"
                r"(\w+乐园)", # "xxx乐园"
                r"(\w+古镇)", # "xxx古镇"
                r"(\w+大厦)", # "xxx大厦"
                r"(\w+中心)", # "xxx中心"
            ]
            
            # 中优先级模式
            medium_priority_patterns = [
                r"去(\w+)",    # "去xxx"
                r"到(\w+)",    # "到xxx" 
                r"想去(\w+)",  # "想去xxx"
                r"(\w+区)",    # "xxx区"
                r"(\w+公园)",  # "xxx公园"
            ]
            
            # 先尝试高优先级模式
            for pattern in high_priority_patterns:
                matches = re.findall(pattern, user_input)
                for match in matches:
                    if len(match) >= 2:
                        extracted_locations.add(match)
            
            # 如果高优先级没找到，再尝试中优先级
            if not extracted_locations:
                for pattern in medium_priority_patterns:
                    matches = re.findall(pattern, user_input)
                    for match in matches:
                        if len(match) >= 2:
                            # 过滤掉明显不是地点的词
                            non_location_words = ["什么", "怎么", "如何", "好玩", "有趣", "推荐", "建议", "天气", "时候"]
                            if match not in non_location_words:
                                extracted_locations.add(match)
            
            # 转换为列表
            intent["mentioned_locations"] = list(extracted_locations)
        
        # 检查时间词
        time_keywords = ["今天", "明天", "后天", "这周", "下周", "周末", "早上", "下午", "晚上"]
        intent["time_keywords"] = [kw for kw in time_keywords if kw in user_input]
        
        # 检查活动词
        activity_keywords = ["吃", "购物", "拍照", "观光", "娱乐", "文化", "商务", "亲子"]
        intent["activity_keywords"] = [kw for kw in activity_keywords if kw in user_input]
        
        # 判断是否为旅行请求
        if (intent["mentioned_locations"] or intent["travel_keywords"] or 
            ("帮我" in user_input and any(kw in user_input for kw in ["规划", "推荐", "安排"]))):
            intent["is_travel_request"] = True
        
        # 判断是否为澄清回答
        if any(word in user_input for word in ["是", "对", "不是", "没有", "有", "我想"]):
            intent["is_clarification"] = True
        
        return intent
    
    def _handle_travel_request(self, user_input: str, context: UserContext, intent: Dict) -> str:
        """处理旅行请求 - 智能渐进式处理"""
        
        # 1. 需求澄清与地点精准定位
        location_info = self._clarify_locations(intent["mentioned_locations"], user_input)
        
        if location_info["needs_clarification"]:
            context.conversation_state = ConversationState.LOCATION_CLARIFYING
            return location_info["clarification_question"]
        
        # 更新上下文
        context.origin = location_info["origin"]
        context.destination = location_info["destination"]
        
        # 2. Agent智能思考阶段 - 分析需要什么信息
        logger.info("🧠 Agent开始智能分析用户需求...")
        thinking_result = self._agent_intelligent_thinking(user_input, intent, context)
        
        # 3. 全面调用所有MCP服务获取科学数据
        logger.info("🔧 开始全面调用MCP服务，获取科学攻略所需数据...")
        mcp_data = self._comprehensive_mcp_calls(context)
        
        # 4. 检查MCP数据中的极端情况，只有这时才询问用户
        extreme_condition_response = self._check_extreme_conditions(mcp_data, context)
        if extreme_condition_response:
            return extreme_condition_response
        
        # 5. RAG增强与方案输出
        logger.info("📖 开始RAG增强与方案生成")
        
        rag_insights = self._get_rag_insights(context.destination)
        
        # 生成最终攻略
        final_plan = self._generate_intelligent_plan(
            context, thinking_result, mcp_data, rag_insights
        )
        
        context.conversation_state = ConversationState.COMPLETED
        
        return final_plan
    
    def _clarify_locations(self, mentioned_locations: List[str], user_input: str) -> Dict[str, Any]:
        """智能推断起点终点，减少不必要的澄清"""
        
        result = {
            "needs_clarification": False,
            "clarification_question": "",
            "origin": None,
            "destination": None
        }
        
        # 智能提取起点和终点
        origin_keywords = ["从", "出发", "起点"]
        destination_keywords = ["到", "去", "想去", "前往"]
        
        # 解析起点
        has_explicit_origin = any(kw in user_input for kw in origin_keywords)
        if has_explicit_origin:
            # 提取明确的起点
            for location in mentioned_locations:
                if any(kw + location in user_input or location + kw in user_input for kw in origin_keywords):
                    result["origin"] = location
                    break
        
        # 解析终点 - 改进逻辑
        if mentioned_locations:
            for location in mentioned_locations:
                # 先尝试直接匹配
                if location in self.location_mapping:
                    result["destination"] = location
                    logger.info(f"📍 精确定位 {location}: {self.location_mapping[location]['coords']}")
                    break
                else:
                    # 尝试模糊匹配
                    fuzzy_match = self._fuzzy_match_location(location)
                    if fuzzy_match:
                        result["destination"] = fuzzy_match
                        logger.info(f"📍 模糊匹配 {location} → {fuzzy_match}: {self.location_mapping[fuzzy_match]['coords']}")
                        break
            
            # 如果没有找到匹配，使用第一个地点作为目的地
            if not result["destination"]:
                result["destination"] = mentioned_locations[0]
        
        # 智能设置默认值
        if not result["origin"]:
            if has_explicit_origin:
                # 用户明确想说起点但没识别到，才问
                result["needs_clarification"] = True
                result["clarification_question"] = "请问您的出发地点是哪里？"
                return result
            else:
                # 用户没提起点，默认人民广场（上海市中心）
                result["origin"] = "人民广场"
                logger.info("🤖 智能推断：起点默认为人民广场")
        
        # 特殊处理："浦东有什么好玩的"这类问题
        if not result["destination"] and not mentioned_locations:
            # 检查是否是区域性询问
            area_keywords = ["浦东", "徐汇", "黄浦", "静安", "长宁", "虹口", "杨浦"]
            found_area = None
            for area in area_keywords:
                if area in user_input:
                    found_area = area
                    break
            
            if found_area:
                # 将区域映射为具体景点
                area_mapping = {
                    "浦东": "陆家嘴",
                    "徐汇": "徐家汇", 
                    "黄浦": "外滩",
                    "静安": "静安寺",
                    "长宁": "虹桥机场",
                    "虹口": "外滩",
                    "杨浦": "外滩"
                }
                result["destination"] = area_mapping.get(found_area, "陆家嘴")
                logger.info(f"🤖 智能推断：{found_area}区域查询 → {result['destination']}")
            else:
                result["needs_clarification"] = True
                result["clarification_question"] = "请告诉我您想去哪里？比如外滩、迪士尼、陆家嘴等。"
                return result
        
        # 模糊地点智能匹配
        if result["destination"] and result["destination"] not in self.location_mapping:
            # 尝试模糊匹配
            fuzzy_match = self._fuzzy_match_location(result["destination"])
            if fuzzy_match:
                result["destination"] = fuzzy_match
                logger.info(f"🤖 智能匹配：{result['destination']} → {fuzzy_match}")
            else:
                # 只有在完全无法匹配时才澄清
                result["needs_clarification"] = True
                result["clarification_question"] = f"您说的\"{result['destination']}\"我不太确定具体位置，您指的是哪个地方呢？"
                return result
        
        return result
    
    def _fuzzy_match_location(self, location: str) -> Optional[str]:
        """模糊匹配地点名称"""
        # 常见别名映射
        aliases = {
            # 迪士尼相关
            "迪士尼": "上海迪士尼乐园",
            "迪斯尼": "上海迪士尼乐园",
            "disney": "上海迪士尼乐园",
            "迪斯尼乐园": "上海迪士尼乐园",
            
            # 东方明珠相关  
            "东方明珠塔": "东方明珠",
            "明珠塔": "东方明珠",
            "电视塔": "东方明珠",
            
            # 南京路相关
            "南京路": "南京路步行街", 
            "步行街": "南京路步行街",
            "南京东路": "南京路步行街",
            
            # 豫园相关
            "城隍庙": "豫园",
            "老城隍庙": "豫园",
            "豫园商城": "豫园",
            
            # 浦东相关
            "浦东": "陆家嘴",
            "浦东新区": "陆家嘴", 
            "金茂": "陆家嘴",
            "环球": "陆家嘴",
            "上海中心": "陆家嘴",
            "金茂大厦": "陆家嘴",
            "环球金融中心": "陆家嘴",
            
            # 机场相关
            "虹桥机场": "虹桥机场",
            "浦东机场": "浦东机场",
            "虹桥": "虹桥机场",
            
            # 徐汇相关
            "徐汇": "徐家汇",
            "徐汇区": "徐家汇",
            
            # 其他别名
            "外滩观光隧道": "外滩",
            "黄浦江": "外滩",
            "万国建筑博览群": "外滩"
        }
        
        # 直接匹配
        if location in aliases:
            return aliases[location]
        
        # 包含匹配
        for alias, real_name in aliases.items():
            if alias in location or location in alias:
                return real_name
        
        # 在已知地点中查找包含关系
        for known_location in self.location_mapping.keys():
            if location in known_location or known_location in location:
                return known_location
        
        return None
    
    def _agent_intelligent_thinking(self, user_input: str, intent: Dict, context: UserContext) -> Dict[str, Any]:
        """
        Agent智能思考阶段 - 分析用户需求，决定需要调用哪些MCP服务
        这是核心的智能决策逻辑
        """
        logger.info(f"🧠 正在分析用户需求: {user_input}")
        
        thinking_result = {
            "user_query": user_input,
            "detected_intent": intent,
            "suggested_attractions": [],
            "mcp_services_needed": [],
            "reasoning": [],
            "priority": "medium"
        }
        
        # 1. 基于地点关键词推理相关景点
        destination = context.destination
        if destination:
            # 根据目的地推理相关景点和活动
            related_attractions = self._infer_related_attractions(destination, user_input)
            thinking_result["suggested_attractions"] = related_attractions
            thinking_result["reasoning"].append(f"用户想去{destination}，推理出相关景点: {', '.join(related_attractions)}")
        
        # 2. 分析是否需要导航信息
        navigation_keywords = ["去", "到", "怎么走", "路线", "开车", "自驾", "距离", "时间", "导航"]
        if any(keyword in user_input for keyword in navigation_keywords) or context.origin:
            thinking_result["mcp_services_needed"].append("navigation")
            thinking_result["reasoning"].append("用户询问路线或提及出行，需要获取导航信息")
            
            # 有导航需求时，自然需要了解路况
            thinking_result["mcp_services_needed"].append("traffic")
            thinking_result["reasoning"].append("有导航需求，需要获取实时路况信息以优化路线")
        
        # 3. 分析是否需要POI信息
        poi_keywords = ["玩", "吃", "购物", "景点", "餐厅", "周边", "附近", "推荐"]
        activity_types = intent.get("activity_keywords", [])
        if any(keyword in user_input for keyword in poi_keywords) or activity_types:
            thinking_result["mcp_services_needed"].append("poi")
            thinking_result["reasoning"].append("用户询问游玩、餐饮或购物，需要获取周边POI信息")
        
        # 4. 分析是否需要天气信息
        weather_keywords = ["天气", "下雨", "晴天", "温度", "冷", "热", "今天", "明天"]
        time_keywords = intent.get("time_keywords", [])
        if any(keyword in user_input for keyword in weather_keywords) or time_keywords:
            thinking_result["mcp_services_needed"].append("weather")
            thinking_result["reasoning"].append("用户询问天气或提及时间，需要获取天气信息评估出行条件")
        
        # 5. 分析是否需要人流信息
        crowd_keywords = ["人多", "拥挤", "排队", "人少", "游客", "繁忙"]
        if any(keyword in user_input for keyword in crowd_keywords):
            thinking_result["mcp_services_needed"].append("crowd")
            thinking_result["reasoning"].append("用户关心人流状况，需要获取景点人流信息")
        
        # 6. 智能推理 - 根据用户意图自动补充必要的MCP服务
        travel_planning_keywords = ["攻略", "规划", "安排", "一日游", "旅游", "游览", "玩"]
        
        # 如果是完整的旅行规划，自动补充全面的MCP服务
        if any(keyword in user_input for keyword in travel_planning_keywords):
            # 完整攻略需要全面的信息
            if "weather" not in thinking_result["mcp_services_needed"]:
                thinking_result["mcp_services_needed"].append("weather")
                thinking_result["reasoning"].append("制定旅行攻略需要考虑天气因素")
            
            if "crowd" not in thinking_result["mcp_services_needed"]:
                thinking_result["mcp_services_needed"].append("crowd")
                thinking_result["reasoning"].append("制定旅行攻略需要考虑景点人流状况")
                
            if "poi" not in thinking_result["mcp_services_needed"]:
                thinking_result["mcp_services_needed"].append("poi")
                thinking_result["reasoning"].append("完整攻略需要推荐周边景点和设施")
        
        # 如果用户只是简单说"去某地"，也智能补充基础信息
        simple_go_keywords = ["去", "想去", "到"]
        if (any(keyword in user_input for keyword in simple_go_keywords) and 
            len(thinking_result["mcp_services_needed"]) == 0):
            # 简单的去某地，至少需要基础信息
            thinking_result["mcp_services_needed"].extend(["weather", "poi"])
            thinking_result["reasoning"].append("用户想去某地，提供天气和周边信息")
        
        # 如果用户提到时间（今天、明天等），自动加上天气
        if intent.get("time_keywords") and "weather" not in thinking_result["mcp_services_needed"]:
            thinking_result["mcp_services_needed"].append("weather")
            thinking_result["reasoning"].append("用户关心时间，需要了解天气状况")
        
        # 7. 确定优先级
        if "紧急" in user_input or "急" in user_input:
            thinking_result["priority"] = "high"
        elif "详细" in user_input or "攻略" in user_input:
            thinking_result["priority"] = "comprehensive"
        
        # 去重MCP服务
        thinking_result["mcp_services_needed"] = list(set(thinking_result["mcp_services_needed"]))
        
        logger.info(f"🧠 思考完成，需要调用的MCP服务: {thinking_result['mcp_services_needed']}")
        for reason in thinking_result["reasoning"]:
            logger.info(f"💭 推理: {reason}")
        
        return thinking_result
    
    def _infer_related_attractions(self, destination: str, user_input: str) -> List[str]:
        """根据目的地推理相关景点"""
        
        # 地区到景点的智能映射
        area_to_attractions = {
            "浦东新区": ["东方明珠", "陆家嘴", "上海中心", "环球金融中心", "金茂大厦"],
            "浦东": ["东方明珠", "陆家嘴", "上海中心", "上海迪士尼乐园"],
            "黄浦区": ["外滩", "南京路步行街", "豫园", "人民广场"],
            "外滩": ["外滩", "南京路步行街", "和平饭店"],
            "陆家嘴": ["东方明珠", "上海中心", "环球金融中心", "金茂大厦"],
            "徐汇区": ["徐家汇", "淮海路", "田子坊", "新天地"],
            "迪士尼": ["上海迪士尼乐园", "迪士尼小镇"],
        }
        
        related = area_to_attractions.get(destination, [destination])
        
        # 根据用户的活动偏好调整
        if "购物" in user_input:
            if destination in ["徐家汇", "徐汇区"]:
                related.extend(["港汇恒隆", "太平洋百货"])
            elif destination in ["南京路", "黄浦区"]:
                related.extend(["南京路步行街", "第一百货"])
        
        if "吃" in user_input or "美食" in user_input:
            if destination in ["豫园", "黄浦区"]:
                related.extend(["城隍庙", "南翔馒头店"])
            elif destination in ["新天地", "徐汇区"]:
                related.extend(["淮海路", "田子坊"])
        
        return list(set(related))[:5]  # 最多返回5个相关景点
    
    def _progressive_mcp_calls(self, thinking_result: Dict, context: UserContext) -> Dict[str, Any]:
        """
        渐进式MCP服务调用 - 根据思考结果按需调用
        """
        mcp_data = {}
        services_needed = thinking_result["mcp_services_needed"]
        
        logger.info(f"🔧 开始渐进式调用MCP服务: {services_needed}")
        
        # 1. 优先调用导航MCP（如果需要）
        if "navigation" in services_needed:
            logger.info("🗺️ 调用导航MCP获取路径信息")
            try:
                if Config.USE_DEMO_MODE:
                    navigation_result = self._get_demo_navigation_data(context.origin, context.destination)
                else:
                    navigation_result = self.mcp_manager.get_navigation_planning(context.origin, context.destination)
                mcp_data["navigation"] = navigation_result
                logger.info("✅ 导航信息获取成功")
            except Exception as e:
                logger.warning(f"⚠️ 导航信息获取失败: {e}")
                mcp_data["navigation"] = self._get_demo_navigation_data(context.origin, context.destination)
        
        # 2. 基于导航结果调用交通MCP（如果需要）
        if "traffic" in services_needed:
            logger.info("🚦 调用交通MCP获取路况信息")
            try:
                # 如果有导航信息，基于具体路线查询交通状况
                if mcp_data.get("navigation"):
                    traffic_result = self.mcp_manager.traffic_service.get_traffic_info(
                        context.destination, context.origin
                    )
                else:
                    # 没有导航信息时，查询目的地周边交通状况
                    traffic_result = self.mcp_manager.traffic_service.get_traffic_info(context.destination)
                
                mcp_data["traffic"] = traffic_result
                logger.info("✅ 交通信息获取成功")
                
                # 如果交通状况不佳且有导航信息，重新规划路线
                if (traffic_result.get("requires_rerouting") and 
                    mcp_data.get("navigation") and 
                    "navigation" in services_needed):
                    logger.info("🔄 交通拥堵，重新规划避堵路线")
                    try:
                        alt_navigation = self.mcp_manager.get_navigation_planning(
                            context.origin, context.destination, strategy="avoid_congestion"
                        )
                        mcp_data["navigation"] = alt_navigation
                        logger.info("✅ 避堵路线规划完成")
                    except Exception as e:
                        logger.warning(f"⚠️ 避堵路线规划失败: {e}")
                        
            except Exception as e:
                logger.warning(f"⚠️ 交通信息获取失败: {e}")
                mcp_data["traffic"] = None
        
        # 3. 调用天气MCP（如果需要）
        if "weather" in services_needed:
            logger.info("🌤️ 调用天气MCP评估出行条件")
            try:
                weather_assessment = self._get_weather_assessment(context.destination)
                mcp_data["weather"] = weather_assessment
                logger.info("✅ 天气信息获取成功")
                
                # 如果天气条件极端，可能影响其他规划
                if weather_assessment.get("requires_adjustment"):
                    logger.warning("⚠️ 检测到极端天气，建议调整出行计划")
                    
            except Exception as e:
                logger.warning(f"⚠️ 天气信息获取失败: {e}")
                mcp_data["weather"] = None
        
        # 4. 调用人流MCP（如果需要）
        if "crowd" in services_needed:
            logger.info("👥 调用人流MCP获取景点状况")
            try:
                crowd_assessment = self._get_crowd_assessment(context.destination)
                mcp_data["crowd"] = crowd_assessment
                logger.info("✅ 人流信息获取成功")
            except Exception as e:
                logger.warning(f"⚠️ 人流信息获取失败: {e}")
                mcp_data["crowd"] = None
        
        # 5. 调用POI MCP（如果需要）
        if "poi" in services_needed:
            logger.info("🔍 调用POI MCP获取周边信息")
            try:
                # 获取目的地周边POI
                poi_result = self.mcp_manager.get_poi_recommendations_for_travel(context.destination)
                mcp_data["poi"] = poi_result
                logger.info("✅ POI信息获取成功")
                
                # 如果有推理出的相关景点，也获取它们的POI信息
                suggested_attractions = thinking_result.get("suggested_attractions", [])
                if suggested_attractions:
                    mcp_data["related_pois"] = {}
                    for attraction in suggested_attractions[:3]:  # 最多查询3个相关景点
                        try:
                            attraction_poi = self.mcp_manager.get_poi_recommendations_for_travel(attraction)
                            mcp_data["related_pois"][attraction] = attraction_poi
                        except Exception as e:
                            logger.warning(f"⚠️ 获取{attraction}周边POI失败: {e}")
                            
            except Exception as e:
                logger.warning(f"⚠️ POI信息获取失败: {e}")
                mcp_data["poi"] = None
        
        logger.info(f"🎯 渐进式MCP调用完成，获取了 {len([k for k, v in mcp_data.items() if v is not None])} 项数据")
        
        return mcp_data
    
    def _comprehensive_mcp_calls(self, context: UserContext) -> Dict[str, Any]:
        """
        全面调用所有MCP服务获取科学攻略所需数据
        天气、路况、导航、POI四个服务都调用
        """
        mcp_data = {}
        
        logger.info("🔧 开始全面MCP调用 - 天气+路况+导航+POI")
        
        # 1. 天气MCP - 必须调用
        logger.info("🌤️ 调用天气MCP获取气象条件")
        try:
            weather_assessment = self._get_weather_assessment(context.destination)
            mcp_data["weather"] = weather_assessment
            logger.info("✅ 天气信息获取成功")
        except Exception as e:
            logger.warning(f"⚠️ 天气信息获取失败: {e}")
            mcp_data["weather"] = None
        
        # 2. 导航MCP - 必须调用
        logger.info("🗺️ 调用导航MCP获取路径信息")
        try:
            if Config.USE_DEMO_MODE:
                navigation_result = self._get_demo_navigation_data(context.origin, context.destination)
            else:
                navigation_result = self.mcp_manager.get_navigation_planning(context.origin, context.destination)
            mcp_data["navigation"] = navigation_result
            logger.info("✅ 导航信息获取成功")
        except Exception as e:
            logger.warning(f"⚠️ 导航信息获取失败: {e}")
            mcp_data["navigation"] = self._get_demo_navigation_data(context.origin, context.destination)
        
        # 3. 路况MCP - 必须调用（基于导航结果）
        logger.info("🚦 调用路况MCP获取交通状况")
        try:
            if mcp_data.get("navigation"):
                traffic_result = self.mcp_manager.traffic_service.get_traffic_info(
                    context.destination, context.origin
                )
            else:
                traffic_result = self.mcp_manager.traffic_service.get_traffic_info(context.destination)
            
            mcp_data["traffic"] = traffic_result
            logger.info("✅ 路况信息获取成功")
            
            # 如果路况严重拥堵，重新规划路线
            if (traffic_result.get("requires_rerouting") and 
                mcp_data.get("navigation")):
                logger.info("🔄 检测到严重拥堵，重新规划避堵路线")
                try:
                    if Config.USE_DEMO_MODE:
                        alt_navigation = self._get_demo_navigation_data(context.origin, context.destination)
                        alt_navigation["route_type"] = "避堵路线"
                    else:
                        alt_navigation = self.mcp_manager.get_navigation_planning(
                            context.origin, context.destination, strategy="avoid_congestion"
                        )
                    mcp_data["navigation"] = alt_navigation
                    logger.info("✅ 避堵路线规划完成")
                except Exception as e:
                    logger.warning(f"⚠️ 避堵路线规划失败: {e}")
                    
        except Exception as e:
            logger.warning(f"⚠️ 路况信息获取失败: {e}")
            mcp_data["traffic"] = None
        
        # 4. POI MCP - 必须调用
        logger.info("🔍 调用POI MCP获取周边信息")
        try:
            # 获取目的地周边POI
            poi_result = self.mcp_manager.get_poi_recommendations_for_travel(context.destination)
            mcp_data["poi"] = poi_result
            logger.info("✅ POI信息获取成功")
        except Exception as e:
            logger.warning(f"⚠️ POI信息获取失败: {e}")
            mcp_data["poi"] = None
        
        # 5. 人流MCP - 补充调用（为科学攻略提供更多数据）
        logger.info("👥 调用人流MCP获取景点状况")
        try:
            crowd_assessment = self._get_crowd_assessment(context.destination)
            mcp_data["crowd"] = crowd_assessment
            logger.info("✅ 人流信息获取成功")
        except Exception as e:
            logger.warning(f"⚠️ 人流信息获取失败: {e}")
            mcp_data["crowd"] = None
        
        successful_calls = len([k for k, v in mcp_data.items() if v is not None])
        logger.info(f"🎯 全面MCP调用完成，成功获取 {successful_calls}/5 项数据")
        
        return mcp_data
    
    def _check_extreme_conditions(self, mcp_data: Dict, context: UserContext) -> Optional[str]:
        """
        检查MCP数据中的极端情况，只有极端情况才询问用户
        """
        # 检查极端天气
        if mcp_data.get("weather"):
            weather_assessment = mcp_data["weather"]
            if weather_assessment.get("requires_adjustment"):
                logger.warning("⚠️ 检测到极端天气条件")
                return weather_assessment.get("recommendation", "天气条件不适宜出行，建议调整计划。")
        
        # 检查极端交通状况
        if mcp_data.get("traffic"):
            traffic_data = mcp_data["traffic"]
            if traffic_data.get("status") == "严重拥堵":
                # 严重拥堵不询问，直接在攻略中给出建议
                logger.info("🚦 检测到严重拥堵，将在攻略中提供解决方案")
        
        # 检查其他极端情况...
        # 目前只有极端天气需要用户确认，其他情况都在攻略中给出解决方案
        
        return None
    
    def _get_weather_assessment(self, destination: str) -> Dict[str, Any]:
        """获取天气评估"""
        try:
            # 检查是否为演示模式
            if Config.USE_DEMO_MODE:
                weather_info = self._get_demo_weather_data(destination)
            else:
                weather_info = self.mcp_manager.weather_service.get_weather_info(destination)
            
            # 智能决策
            weather_condition = weather_info.get("weather", "")
            temperature = weather_info.get("temperature", "")
            
            assessment = {
                "data": weather_info,
                "risk_level": "low",
                "recommendation": "",
                "requires_adjustment": False
            }
            
            # 极端天气检查
            for extreme_weather in self.weather_conditions["extreme"]:
                if extreme_weather in weather_condition:
                    assessment["risk_level"] = "high"
                    assessment["requires_adjustment"] = True
                    assessment["recommendation"] = f"⚠️ 根据天气预报，{destination}地区将有{weather_condition}。为了您的出行安全和体验，建议将行程调整至天气晴朗的日期，或者我为您推荐一些室内活动方案？"
                    break
            
            # 不良天气检查
            for bad_weather in self.weather_conditions["bad"]:
                if bad_weather in weather_condition:
                    assessment["risk_level"] = "medium"
                    assessment["recommendation"] = f"🌧️ {destination}今天有{weather_condition}，建议携带雨具并考虑室内景点。"
                    break
            
            # 温度检查
            if temperature and temperature.replace("°C", "").isdigit():
                temp_val = int(temperature.replace("°C", ""))
                if temp_val > 35:
                    assessment["risk_level"] = "medium"
                    assessment["recommendation"] = f"🌡️ {destination}今天气温较高({temperature})，建议避开中午时段，选择早晚出行。"
                elif temp_val < 0:
                    assessment["risk_level"] = "medium"
                    assessment["recommendation"] = f"🧊 {destination}今天气温较低({temperature})，请注意保暖。"
            
            return assessment
            
        except Exception as e:
            logger.error(f"天气评估失败: {e}")
            return {"data": {}, "risk_level": "unknown", "recommendation": "", "requires_adjustment": False}
    
    def _get_demo_weather_data(self, destination: str) -> Dict[str, Any]:
        """获取演示天气数据"""
        # 根据目的地返回不同的模拟天气
        demo_weather = {
            "外滩": {"weather": "晴", "temperature": "22°C", "humidity": "65%", "wind": "东南风2级"},
            "东方明珠": {"weather": "多云", "temperature": "21°C", "humidity": "70%", "wind": "东风1级"},
            "上海迪士尼乐园": {"weather": "晴", "temperature": "23°C", "humidity": "60%", "wind": "南风2级"},
            "陆家嘴": {"weather": "晴", "temperature": "22°C", "humidity": "65%", "wind": "东南风2级"},
            "豫园": {"weather": "多云", "temperature": "21°C", "humidity": "68%", "wind": "东风1级"},
        }
        
        weather_data = demo_weather.get(destination, {
            "weather": "晴", "temperature": "22°C", "humidity": "65%", "wind": "微风"
        })
        
        weather_data.update({
            "service": "weather",
            "location": destination,
            "recommendation": "天气适宜出行",
            "timestamp": datetime.now().isoformat(),
            "api_source": "demo"
        })
        
        return weather_data
    
    def _get_demo_navigation_data(self, origin: str, destination: str) -> Dict[str, Any]:
        """获取演示导航数据"""
        # 基于起点终点生成合理的导航数据
        navigation_routes = {
            ("人民广场", "外滩"): {
                "distance": "2.3公里",
                "duration": "15分钟", 
                "navigation_steps": [
                    {"step": 1, "instruction": "从人民广场出发，向东步行至南京东路", "distance": "300米"},
                    {"step": 2, "instruction": "沿南京东路向东直行", "distance": "1.8公里"},
                    {"step": 3, "instruction": "至中山东一路右转即达外滩", "distance": "200米"}
                ]
            },
            ("人民广场", "东方明珠"): {
                "distance": "4.2公里",
                "duration": "25分钟",
                "navigation_steps": [
                    {"step": 1, "instruction": "从人民广场出发，向东前往南京东路", "distance": "300米"},
                    {"step": 2, "instruction": "经外滩隧道过江", "distance": "2.5公里"},
                    {"step": 3, "instruction": "到达陆家嘴环路，前往东方明珠", "distance": "1.4公里"}
                ]
            },
            ("人民广场", "上海迪士尼乐园"): {
                "distance": "28.5公里",
                "duration": "50分钟",
                "navigation_steps": [
                    {"step": 1, "instruction": "从人民广场出发，前往内环高架", "distance": "2公里"},
                    {"step": 2, "instruction": "经内环高架转中环路", "distance": "8公里"},
                    {"step": 3, "instruction": "经迎宾大道前往迪士尼", "distance": "18.5公里"}
                ]
            }
        }
        
        route_key = (origin, destination)
        demo_data = navigation_routes.get(route_key, {
            "distance": "约10公里",
            "duration": "约30分钟",
            "navigation_steps": [
                {"step": 1, "instruction": f"从{origin}出发", "distance": "起点"},
                {"step": 2, "instruction": "沿主要道路行驶", "distance": "中途"},
                {"step": 3, "instruction": f"到达{destination}", "distance": "终点"}
            ]
        })
        
        return {
            "service": "navigation",
            "origin": origin,
            "destination": destination,
            "distance": demo_data["distance"],
            "duration": demo_data["duration"],
            "navigation_steps": demo_data["navigation_steps"],
            "route_summary": f"从{origin}到{destination}，总里程{demo_data['distance']}，预计用时{demo_data['duration']}",
            "timestamp": datetime.now().isoformat(),
            "api_source": "demo"
        }
    
    def _get_crowd_assessment(self, destination: str) -> Dict[str, Any]:
        """获取人流评估"""
        try:
            crowd_info = self.mcp_manager.crowd_service.get_crowd_info(destination)
            
            assessment = {
                "data": crowd_info,
                "congestion_level": crowd_info.get("crowd_level", "中等"),
                "recommendation": ""
            }
            
            # 人流智能决策
            crowd_level = crowd_info.get("crowd_level", "")
            if "高" in crowd_level or "拥挤" in crowd_level:
                assessment["recommendation"] = f"👥 根据预测，{destination}今天人流量较大。建议您选择非高峰时段游览，或考虑周边人流较少的替代景点。"
                
                # 推荐最佳游览时间
                best_time = crowd_info.get("best_visit_time", "")
                if best_time:
                    assessment["recommendation"] += f"最佳游览时间：{best_time}。"
            
            return assessment
            
        except Exception as e:
            logger.error(f"人流评估失败: {e}")
            return {"data": {}, "congestion_level": "未知", "recommendation": ""}
    
    def _assess_environmental_risks(self, weather_data: Dict, crowd_data: Dict) -> Dict[str, Any]:
        """综合评估环境风险"""
        
        risk_assessment = {
            "requires_adjustment": False,
            "recommendation": "",
            "risk_factors": []
        }
        
        # 收集风险因素
        if weather_data.get("requires_adjustment"):
            risk_assessment["requires_adjustment"] = True
            risk_assessment["risk_factors"].append("极端天气")
            risk_assessment["recommendation"] = weather_data["recommendation"]
        
        if crowd_data.get("congestion_level") == "极高":
            risk_assessment["risk_factors"].append("人流过度拥挤")
            if not risk_assessment["requires_adjustment"]:
                risk_assessment["recommendation"] = crowd_data["recommendation"]
        
        return risk_assessment
    
    def _get_navigation_planning(self, origin: str, destination: str) -> Dict[str, Any]:
        """获取导航路径规划"""
        try:
            navigation_result = self.mcp_manager.get_navigation_planning(origin, destination)
            
            logger.info(f"🧭 路径规划完成: {origin} → {destination}")
            
            return {
                "data": navigation_result,
                "route_summary": navigation_result.get("route_summary", ""),
                "duration": navigation_result.get("duration", ""),
                "distance": navigation_result.get("distance", ""),
                "navigation_steps": navigation_result.get("navigation_steps", [])
            }
            
        except Exception as e:
            logger.error(f"导航规划失败: {e}")
            return {"data": {}, "route_summary": "", "duration": "约30分钟", "distance": "约15公里"}
    
    def _get_traffic_assessment(self, origin: str, destination: str) -> Dict[str, Any]:
        """获取交通状况评估"""
        try:
            traffic_info = self.mcp_manager.traffic_service.get_traffic_info(destination, origin)
            
            traffic_status = traffic_info.get("traffic_status", "")
            
            assessment = {
                "data": traffic_info,
                "status": traffic_status,
                "requires_rerouting": False,
                "recommendation": ""
            }
            
            # 交通状况智能决策
            if "严重拥堵" in traffic_status:
                assessment["requires_rerouting"] = True
                assessment["recommendation"] = "🚦 当前路线严重拥堵，已为您重新规划避堵路线。建议选择地铁等公共交通。"
            elif "拥堵" in traffic_status:
                assessment["recommendation"] = "🟡 当前路线略有拥堵，建议预留额外时间或选择公共交通。"
            elif "畅通" in traffic_status:
                assessment["recommendation"] = "🟢 当前交通状况良好，驾车出行较为便捷。"
            
            return assessment
            
        except Exception as e:
            logger.error(f"交通评估失败: {e}")
            return {"data": {}, "status": "未知", "requires_rerouting": False, "recommendation": ""}
    
    def _get_alternative_navigation(self, origin: str, destination: str) -> Dict[str, Any]:
        """获取避堵替代路线"""
        try:
            # 使用避拥堵策略重新规划
            navigation_result = self.mcp_manager.get_navigation_planning(
                origin, destination, strategy="avoid_congestion"
            )
            
            logger.info("🔄 已重新规划避堵路线")
            
            return {
                "data": navigation_result,
                "route_summary": navigation_result.get("route_summary", ""),
                "is_alternative": True
            }
            
        except Exception as e:
            logger.error(f"替代路线规划失败: {e}")
            return self._get_navigation_planning(origin, destination)
    
    def _generate_preference_questions(self, intent: Dict, context: UserContext) -> str:
        """智能推断用户偏好，极少询问"""
        
        # 新策略：只有在关键信息缺失且无法推断时才询问
        # 大部分情况下智能推断用户需求
        
        # 如果用户询问很具体（如路线、天气），直接给答案，不询问偏好
        specific_queries = ["怎么走", "路线", "天气", "人多", "开放时间", "门票"]
        if any(query in context.destination or "" for query in specific_queries):
            return ""
        
        # 如果用户提到了活动类型，直接推断，不询问
        if intent.get("activity_keywords"):
            return ""
        
        # 如果用户提到了时间，直接推断，不询问  
        if intent.get("time_keywords"):
            return ""
            
        # 如果是完整的旅行规划请求，智能推断默认偏好
        travel_planning_keywords = ["攻略", "规划", "安排", "一日游", "旅游", "游览", "玩"]
        if any(keyword in context.destination or "" for keyword in travel_planning_keywords):
            # 智能设置默认偏好，不询问用户
            logger.info("🤖 智能推断：用户想要完整旅游攻略，采用综合推荐方案")
            return ""
        
        # 只有在用户询问非常模糊且无法推断时才询问
        # 比如用户只说了一个地名，没有任何其他信息
        if (not intent.get("activity_keywords") and 
            not intent.get("time_keywords") and 
            not intent.get("travel_keywords") and
            len(context.destination or "") < 5):  # 地名很短且没有其他信息
            
            # 即使这种情况，也尽量简化询问
            return f"我来为您规划{context.destination}的游览攻略！正在获取实时信息..."
        
        # 默认不询问，直接生成攻略
        return ""
    
    def _get_rag_insights(self, destination: str) -> Dict[str, Any]:
        """获取RAG知识库洞察"""
        
        # 使用专业RAG知识库获取深度洞察
        insights = self.rag_kb.get_attraction_insights(destination)
        
        if not insights:
            # 如果没有预设知识，尝试通过POI搜索获取
            try:
                poi_result = self.mcp_manager.get_poi_recommendations_for_travel(destination)
                insights = {
                    "best_time": {"optimal": "建议提前查询开放时间"},
                    "nearby_food": [{"name": "周边餐厅", "note": "建议实地查看"}],
                    "insider_tips": ["建议网上提前了解相关信息"]
                }
                
                if poi_result.get("pois"):
                    pois = poi_result["pois"][:3]  # 取前3个
                    insights["nearby_food"] = [
                        {"name": p.get("name", ""), "type": "周边推荐"} 
                        for p in pois if p.get("name")
                    ]
                    
            except Exception as e:
                logger.warning(f"RAG增强失败: {e}")
                insights = {}
        
        return insights
    
    def _generate_comprehensive_plan(self, context: UserContext, weather_data: Dict, 
                                   crowd_data: Dict, navigation_data: Dict, 
                                   traffic_data: Dict, rag_insights: Dict) -> str:
        """生成综合旅行攻略"""
        
        plan_sections = []
        
        # 攻略标题
        plan_sections.append(f"🎯 {context.destination} 智能旅行攻略")
        plan_sections.append("=" * 50)
        
        # 1. 行程概览
        plan_sections.append("📋 行程概览")
        plan_sections.append(f"• 出发地：{context.origin}")
        plan_sections.append(f"• 目的地：{context.destination}")
        if navigation_data.get("duration"):
            plan_sections.append(f"• 预计行程：{navigation_data['duration']}")
        if navigation_data.get("distance"):
            plan_sections.append(f"• 路程距离：{navigation_data['distance']}")
        plan_sections.append("")
        
        # 2. 实时环境信息
        plan_sections.append("🌤️ 实时环境信息")
        
        # 天气信息
        if weather_data.get("data"):
            weather = weather_data["data"]
            plan_sections.append(f"• 天气状况：{weather.get('weather', '未知')} {weather.get('temperature', '')}")
            if weather.get("humidity"):
                plan_sections.append(f"• 湿度：{weather['humidity']}")
            if weather.get("wind"):
                plan_sections.append(f"• 风力：{weather['wind']}")
            if weather_data.get("recommendation"):
                plan_sections.append(f"• 天气建议：{weather_data['recommendation']}")
        
        # 人流信息
        if crowd_data.get("data"):
            crowd = crowd_data["data"]
            plan_sections.append(f"• 人流状况：{crowd.get('crowd_level', '中等')}")
            if crowd.get("wait_time"):
                plan_sections.append(f"• 预计等待：{crowd['wait_time']}")
            if crowd.get("best_visit_time"):
                plan_sections.append(f"• 最佳时间：{crowd['best_visit_time']}")
        
        plan_sections.append("")
        
        # 3. 交通指南
        plan_sections.append("🚗 交通指南")
        
        if traffic_data.get("recommendation"):
            plan_sections.append(f"• 路况状况：{traffic_data['recommendation']}")
        
        if navigation_data.get("navigation_steps"):
            plan_sections.append("• 详细路线：")
            steps = navigation_data["navigation_steps"][:5]  # 显示前5步
            for step in steps:
                instruction = step.get("instruction", "")
                distance = step.get("distance", "")
                plan_sections.append(f"  {step['step']}. {instruction} ({distance})")
            
            if len(navigation_data["navigation_steps"]) > 5:
                plan_sections.append(f"  ... (共{len(navigation_data['navigation_steps'])}步)")
        
        plan_sections.append("")
        
        # 4. 专业游览建议（RAG增强）
        plan_sections.append("💡 专业游览建议")
        
        # 处理最佳时间信息
        if rag_insights.get("best_time"):
            best_time_info = rag_insights["best_time"]
            if isinstance(best_time_info, dict):
                optimal = best_time_info.get("optimal", "")
                reason = best_time_info.get("reason", "")
                if optimal:
                    plan_sections.append(f"• 最佳时机：{optimal}")
                if reason:
                    plan_sections.append(f"  理由：{reason}")
            else:
                plan_sections.append(f"• 最佳时机：{best_time_info}")
        
        # 处理拍照地点
        if rag_insights.get("photo_spots"):
            photo_spots = rag_insights["photo_spots"]
            if isinstance(photo_spots, list) and len(photo_spots) > 0:
                plan_sections.append("• 推荐拍照地点：")
                for spot in photo_spots[:3]:  # 显示前3个
                    if isinstance(spot, dict):
                        name = spot.get("name", "")
                        tip = spot.get("tip", "")
                        plan_sections.append(f"  📸 {name}: {tip}")
                    else:
                        plan_sections.append(f"  📸 {spot}")
        
        # 处理内行贴士
        if rag_insights.get("insider_tips"):
            insider_tips = rag_insights["insider_tips"]
            if isinstance(insider_tips, list):
                plan_sections.append("• 内行贴士：")
                for tip in insider_tips[:3]:
                    plan_sections.append(f"  💡 {tip}")
            else:
                plan_sections.append(f"• 内行贴士：{insider_tips}")
        
        # 处理隐藏玩法
        if rag_insights.get("hidden_gems"):
            hidden_gems = rag_insights["hidden_gems"]
            if isinstance(hidden_gems, list):
                plan_sections.append("• 隐藏玩法：")
                for gem in hidden_gems[:2]:
                    plan_sections.append(f"  🎯 {gem}")
            else:
                plan_sections.append(f"• 隐藏玩法：{hidden_gems}")
        
        plan_sections.append("")
        
        # 5. 餐饮推荐
        plan_sections.append("🍽️ 餐饮推荐")
        
        if rag_insights.get("nearby_food"):
            nearby_food = rag_insights["nearby_food"]
            if isinstance(nearby_food, list):
                for restaurant in nearby_food[:3]:  # 显示前3个
                    if isinstance(restaurant, dict):
                        name = restaurant.get("name", "")
                        specialty = restaurant.get("specialty", "")
                        price = restaurant.get("price", "")
                        note = restaurant.get("note", "")
                        info_parts = [name]
                        if specialty:
                            info_parts.append(f"主营{specialty}")
                        if price:
                            info_parts.append(price)
                        if note:
                            info_parts.append(note)
                        plan_sections.append(f"• {' - '.join(info_parts)}")
                    else:
                        plan_sections.append(f"• {restaurant}")
            else:
                plan_sections.append(f"• {nearby_food}")
        else:
            plan_sections.append(f"• 建议提前查询{context.destination}周边餐厅")
        
        plan_sections.append("")
        
        # 6. 注意事项  
        plan_sections.append("⚠️ 注意事项")
        plan_sections.append("• 出行前请再次确认天气和交通状况")
        plan_sections.append("• 建议携带身份证等必要证件")
        plan_sections.append("• 如有变化可随时咨询获取更新建议")
        
        plan_sections.append("")
        plan_sections.append("🤖 如果行程有任何变动，或者您想了解更多信息，请随时告诉我！")
        
        return "\n".join(plan_sections)
    
    def _handle_clarification(self, user_input: str, context: UserContext) -> str:
        """处理澄清回答"""
        
        if context.conversation_state == ConversationState.LOCATION_CLARIFYING:
            # 用户回答了起点问题
            context.origin = user_input.strip()
            
            # 重新尝试生成攻略
            return self._continue_planning_after_clarification(context)
            
        elif context.conversation_state == ConversationState.PREFERENCE_COLLECTING:
            # 用户回答了偏好问题
            context.preferences.update(self._parse_preference_response(user_input))
            
            # 继续生成攻略
            return self._continue_planning_after_clarification(context)
        
        return "感谢您的回答，让我为您重新规划攻略。"
    
    def _continue_planning_after_clarification(self, context: UserContext) -> str:
        """澄清后继续规划"""
        
        if not context.destination:
            return "请告诉我您想去的具体目的地？"
        
        # 重新执行完整规划流程
        try:
            # 环境评估
            weather_data = self._get_weather_assessment(context.destination)
            crowd_data = self._get_crowd_assessment(context.destination)
            
            # 如果有极端风险，直接返回建议
            risk_assessment = self._assess_environmental_risks(weather_data, crowd_data)
            if risk_assessment["requires_adjustment"]:
                return risk_assessment["recommendation"]
            
            # 交通规划
            navigation_data = self._get_navigation_planning(context.origin, context.destination)
            traffic_data = self._get_traffic_assessment(context.origin, context.destination)
            
            # RAG增强
            rag_insights = self._get_rag_insights(context.destination)
            
            # 生成最终攻略
            context.conversation_state = ConversationState.COMPLETED
            return self._generate_comprehensive_plan(
                context, weather_data, crowd_data, navigation_data, traffic_data, rag_insights
            )
            
        except Exception as e:
            logger.error(f"规划生成失败: {e}")
            return "抱歉，生成攻略时遇到了问题。请稍后重试或提供更多信息。"
    
    def _parse_preference_response(self, user_input: str) -> Dict[str, Any]:
        """解析用户偏好回答"""
        preferences = {}
        
        # 解析活动偏好
        if "观光" in user_input or "游览" in user_input:
            preferences["activity"] = "观光"
        elif "购物" in user_input:
            preferences["activity"] = "购物"
        elif "美食" in user_input or "吃" in user_input:
            preferences["activity"] = "美食"
        elif "文化" in user_input:
            preferences["activity"] = "文化"
        
        # 解析交通偏好
        if "地铁" in user_input:
            preferences["transport"] = "地铁"
        elif "开车" in user_input or "自驾" in user_input:
            preferences["transport"] = "自驾"
        elif "打车" in user_input:
            preferences["transport"] = "打车"
        
        return preferences
    
    def _guide_user_to_travel_request(self, user_input: str) -> str:
        """引导用户提供旅行需求"""
        
        greetings = ["你好", "您好", "hi", "hello"]
        if any(greeting in user_input.lower() for greeting in greetings):
            return ("您好！我是您的专业旅行攻略规划师。我可以根据实时天气、交通、人流等信息，"
                   "为您制定最优的旅行方案。\n\n" 
                   "请告诉我您的旅行需求，比如：\n"
                   "• '我想去外滩看夜景'\n"
                   "• '明天带孩子去迪士尼，路况怎么样'\n"
                   "• '从人民广场到徐家汇购物的路线'\n\n"
                   "我会为您提供最专业、最贴心的攻略建议！")
        
        return ("我是您的智能旅行攻略规划师。请告诉我您想去哪里，我来为您制定最优的出行方案！\n\n"
               "您可以这样问我：\n"
               "• 目的地 + 活动：'我想去外滩拍照'\n" 
               "• 路线规划：'从虹桥机场到陆家嘴怎么走'\n"
               "• 实时信息：'迪士尼今天人多吗，天气如何'\n\n"
               "我会实时获取天气、交通、人流信息，给您最智能的建议！")
    
    def _generate_intelligent_plan(self, context: UserContext, thinking_result: Dict, 
                                 mcp_data: Dict, rag_insights: Dict) -> str:
        """
        基于智能思考和MCP数据生成个性化攻略
        """
        plan_sections = []
        
        # 攻略标题和概览
        plan_sections.append(f"🎯 {context.destination} 智能旅行攻略")
        plan_sections.append("=" * 50)
        
        # 显示Agent的思考过程
        plan_sections.append("🧠 智能分析结果")
        plan_sections.append(f"• 分析需求：{thinking_result['user_query']}")
        if thinking_result.get("suggested_attractions"):
            attractions_str = "、".join(thinking_result["suggested_attractions"])
            plan_sections.append(f"• 推理景点：{attractions_str}")
        
        services_used = [s for s in thinking_result["mcp_services_needed"] if mcp_data.get(s)]
        if services_used:
            plan_sections.append(f"• 调用服务：{' + '.join(services_used)}")
        plan_sections.append("")
        
        # 行程基本信息
        plan_sections.append("📋 行程概览")
        plan_sections.append(f"• 出发地：{context.origin}")
        plan_sections.append(f"• 目的地：{context.destination}")
        
        # 导航信息（如果有）
        if mcp_data.get("navigation"):
            nav_data = mcp_data["navigation"]
            if nav_data.get("duration"):
                plan_sections.append(f"• 预计时长：{nav_data['duration']}")
            if nav_data.get("distance"):
                plan_sections.append(f"• 路程距离：{nav_data['distance']}")
        
        plan_sections.append("")
        
        # 实时环境状况
        plan_sections.append("🌤️ 实时环境状况")
        
        # 天气信息
        if mcp_data.get("weather"):
            weather = mcp_data["weather"]["data"]
            plan_sections.append(f"• 天气：{weather.get('weather', '未知')} {weather.get('temperature', '')}")
            if weather.get("recommendation"):
                plan_sections.append(f"• 天气建议：{mcp_data['weather']['recommendation']}")
        
        # 人流信息
        if mcp_data.get("crowd"):
            crowd = mcp_data["crowd"]["data"]
            plan_sections.append(f"• 人流状况：{crowd.get('crowd_level', '中等')}")
            if crowd.get("best_visit_time"):
                plan_sections.append(f"• 最佳时间：{crowd['best_visit_time']}")
        
        plan_sections.append("")
        
        # 交通指南
        if mcp_data.get("navigation") or mcp_data.get("traffic"):
            plan_sections.append("🚗 交通指南")
            
            if mcp_data.get("traffic"):
                traffic = mcp_data["traffic"]
                if traffic.get("recommendation"):
                    plan_sections.append(f"• 路况：{traffic['recommendation']}")
            
            if mcp_data.get("navigation"):
                nav_data = mcp_data["navigation"]
                steps = nav_data.get("navigation_steps", [])
                if steps:
                    plan_sections.append("• 详细路线：")
                    for step in steps[:5]:  # 显示前5步
                        instruction = step.get("instruction", "")
                        distance = step.get("distance", "")
                        plan_sections.append(f"  {step['step']}. {instruction} ({distance})")
                    
                    if len(steps) > 5:
                        plan_sections.append(f"  ... (共{len(steps)}步)")
            
            plan_sections.append("")
        
        # RAG增强的专业建议
        if rag_insights:
            plan_sections.append("💡 专业游览建议")
            
            # 最佳时间
            if rag_insights.get("best_time"):
                best_time_info = rag_insights["best_time"]
                if isinstance(best_time_info, dict):
                    optimal = best_time_info.get("optimal", "")
                    reason = best_time_info.get("reason", "")
                    if optimal:
                        plan_sections.append(f"• 最佳时机：{optimal}")
                        if reason:
                            plan_sections.append(f"  原因：{reason}")
                else:
                    plan_sections.append(f"• 最佳时机：{best_time_info}")
            
            # 拍照推荐
            if rag_insights.get("photo_spots"):
                photo_spots = rag_insights["photo_spots"]
                if isinstance(photo_spots, list):
                    plan_sections.append("• 拍照推荐：")
                    for spot in photo_spots[:3]:
                        if isinstance(spot, dict):
                            name = spot.get("name", "")
                            tip = spot.get("tip", "")
                            plan_sections.append(f"  📸 {name}: {tip}")
                        else:
                            plan_sections.append(f"  📸 {spot}")
            
            # 内行贴士
            if rag_insights.get("insider_tips"):
                tips = rag_insights["insider_tips"]
                if isinstance(tips, list):
                    plan_sections.append("• 内行贴士：")
                    for tip in tips[:3]:
                        plan_sections.append(f"  💡 {tip}")
                else:
                    plan_sections.append(f"• 内行贴士：{tips}")
            
            plan_sections.append("")
        
        # POI推荐
        if mcp_data.get("poi"):
            plan_sections.append("🔍 周边推荐")
            poi_data = mcp_data["poi"]
            if poi_data.get("pois"):
                pois = poi_data["pois"][:5]  # 显示前5个
                for poi in pois:
                    name = poi.get("name", "")
                    poi_type = poi.get("type", "")
                    address = poi.get("address", "")
                    plan_sections.append(f"• {name} ({poi_type}) - {address}")
            
            plan_sections.append("")
        
        # 餐饮推荐
        if rag_insights.get("nearby_food"):
            plan_sections.append("🍽️ 餐饮推荐")
            nearby_food = rag_insights["nearby_food"]
            if isinstance(nearby_food, list):
                for restaurant in nearby_food[:3]:
                    if isinstance(restaurant, dict):
                        name = restaurant.get("name", "")
                        specialty = restaurant.get("specialty", "")
                        price = restaurant.get("price", "")
                        info_parts = [name]
                        if specialty:
                            info_parts.append(f"主营{specialty}")
                        if price:
                            info_parts.append(price)
                        plan_sections.append(f"• {' - '.join(info_parts)}")
            plan_sections.append("")
        
        # 注意事项和贴士
        plan_sections.append("⚠️ 注意事项")
        plan_sections.append("• 出行前请再次确认天气和交通状况")
        plan_sections.append("• 建议携带身份证等必要证件")
        
        # 基于MCP数据的个性化建议
        if mcp_data.get("weather") and mcp_data["weather"].get("recommendation"):
            plan_sections.append(f"• {mcp_data['weather']['recommendation']}")
        
        plan_sections.append("")
        plan_sections.append("🤖 这份攻略基于实时数据智能生成，如有变动请随时咨询更新！")
        
        return "\n".join(plan_sections)


def main():
    """测试智能旅行攻略规划师"""
    
    agent = SmartTravelAgent()
    
    print("🤖 智能旅行攻略规划师已启动")
    print("输入 'quit' 退出")
    print("-" * 50)
    
    user_id = "test_user"
    
    while True:
        user_input = input("您: ").strip()
        
        if user_input.lower() in ['quit', 'exit', '退出']:
            print("👋 感谢使用智能旅行攻略规划师，祝您旅途愉快！")
            break
        
        if not user_input:
            continue
        
        try:
            response = agent.process_user_request(user_input, user_id)
            print(f"\n🤖 规划师: {response}\n")
            print("-" * 50)
            
        except Exception as e:
            print(f"❌ 处理请求时出错: {e}")
            logger.error(f"处理用户请求失败: {e}")

if __name__ == "__main__":
    main()
