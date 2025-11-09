#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版智能旅行对话Agent
使用豆包Agent作为核心推理引擎，MCP服务提供实时数据支持
"""

import json
import logging
import re
import requests
import urllib3
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import pandas as pd
from pathlib import Path
from threading import Lock

from config import (
    API_KEYS, AMAP_CONFIG, RAG_CONFIG, DEFAULT_CONFIG,
    get_api_key, get_config
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 枚举定义
class WeatherCondition(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    MODERATE = "moderate"
    POOR = "poor"
    EXTREME = "extreme"

class TrafficCondition(Enum):
    SMOOTH = "smooth"
    SLOW = "slow"
    CONGESTED = "congested"
    BLOCKED = "blocked"

class CrowdLevel(Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"

class MCPServiceType(Enum):
    WEATHER = "weather"
    NAVIGATION = "navigation"
    TRAFFIC = "traffic"
    POI = "poi"
    CROWD = "crowd"

# 数据结构定义
@dataclass
class WeatherInfo:
    """天气信息数据结构"""
    date: str
    weather: str
    temperature: str
    wind: str
    humidity: str
    precipitation: str

@dataclass
class RouteInfo:
    """路线信息数据结构"""
    distance: str
    duration: str
    traffic_status: str
    route_description: str
    congestion_level: str

@dataclass
class POIInfo:
    """POI信息数据结构"""
    name: str
    address: str
    rating: float
    business_hours: str
    price: str
    distance: str
    category: str
    reviews: List[str] = None

@dataclass
class TravelPreference:
    """用户旅游偏好"""
    weather_tolerance: WeatherCondition = WeatherCondition.MODERATE
    traffic_tolerance: TrafficCondition = TrafficCondition.SLOW
    crowd_tolerance: CrowdLevel = CrowdLevel.HIGH
    preferred_time: str = "morning"
    budget_conscious: bool = False
    time_conscious: bool = True
    comfort_priority: bool = False
    start_date: str = None
    
    def __post_init__(self):
        if self.start_date is None:
            self.start_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

@dataclass
class ThoughtProcess:
    """思考过程记录"""
    step: int
    thought: str
    keywords: List[str]
    mcp_services: List[MCPServiceType]
    reasoning: str
    timestamp: str

@dataclass
class UserContext:
    """用户上下文"""
    user_id: str
    conversation_history: List[Dict]
    travel_preferences: TravelPreference
    current_plan: Optional[Dict] = None
    thought_process: List[ThoughtProcess] = None
    
    def __post_init__(self):
        if self.thought_process is None:
            self.thought_process = []

class DouBaoAgent:
    """豆包Agent接口"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        # 使用正确的豆包API端点
        self.api_url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # 测试连接
        self._test_connection()
    
    def _test_connection(self):
        """测试豆包API连接"""
        try:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            # 简单的连接测试
            test_payload = {
                "model": "doubao-1-5-pro-32k-250115",
                "messages": [{"role": "user", "content": "你好"}],
                "max_tokens": 10
            }
            
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=test_payload,
                timeout=30,
                verify=False  # 测试时禁用SSL验证
            )
            
            if response.status_code == 200:
                logger.info("✅ 豆包API连接测试成功")
            else:
                logger.warning(f"⚠️ 豆包API连接测试失败，状态码: {response.status_code}")
                
        except Exception as e:
            logger.warning(f"⚠️ 豆包API连接测试失败: {e}")
            logger.info("💡 建议检查网络连接或API密钥")
    
    def generate_response(self, messages: List[Dict], system_prompt: str = None) -> str:
        """调用豆包API生成回复"""
        try:
            payload = {
                "model": "doubao-1-5-pro-32k-250115",
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 2000
            }
            
            if system_prompt:
                payload["messages"].insert(0, {"role": "system", "content": system_prompt})
            
            # 增加重试机制和更长的超时时间
            for attempt in range(3):
                try:
                    # 尝试不同的SSL配置
                    ssl_configs = [
                        {"verify": True},  # 标准SSL验证
                        {"verify": False},  # 禁用SSL验证（仅用于测试）
                        {"verify": True, "timeout": 120}  # 更长超时时间
                    ]
                    
                    current_config = ssl_configs[min(attempt, len(ssl_configs)-1)]
                    
                    response = requests.post(
                        self.api_url, 
                        headers=self.headers, 
                        json=payload, 
                        timeout=current_config.get("timeout", 60),
                        verify=current_config["verify"]
                    )
                    response.raise_for_status()
                    
                    result = response.json()
                    return result["choices"][0]["message"]["content"]
                    
                except requests.exceptions.SSLError as ssl_e:
                    logger.warning(f"SSL错误，尝试第{attempt+1}次: {ssl_e}")
                    if attempt == 2:  # 最后一次尝试
                        raise
                    continue
                except requests.exceptions.RequestException as req_e:
                    logger.warning(f"请求错误，尝试第{attempt+1}次: {req_e}")
                    if attempt == 2:  # 最后一次尝试
                        raise
                    continue
            
        except Exception as e:
            logger.error(f"豆包API调用失败: {e}")
            # 返回一个基于本地逻辑的回复，而不是完全失败
            return self._generate_fallback_response(messages)
    
    def _generate_fallback_response(self, messages: List[Dict]) -> str:
        """生成备用回复"""
        return """我理解您的需求，正在为您规划个性化旅游攻略。

由于网络连接问题，我暂时无法使用豆包Agent为您生成详细回复。
请稍后再试，或者您可以尝试：
• 检查网络连接
• 重新输入您的需求
• 稍后再次尝试

我会继续收集实时数据来支持您的旅游规划。"""

class EnhancedTravelAgent:
    """增强版智能旅行对话Agent"""
    
    def __init__(self):
        """初始化增强版Agent"""
        self.config = get_config()
        self.user_contexts = {}
        
        # 初始化豆包Agent
        doubao_api_key = get_api_key("DOUBAO")
        if not doubao_api_key:
            raise ValueError("缺少豆包API密钥配置")
        self.doubao_agent = DouBaoAgent(doubao_api_key)
        
        # API请求限流控制
        self._api_lock = Lock()
        self._last_api_call = {}  # 记录每个API的最后调用时间
        self._min_interval = 0.35  # 最小请求间隔（秒），确保不超过3次/秒
        
        # 上海地区关键词映射
        self.location_keywords = {
            # 浦东新区
            "浦东": ["东方明珠", "陆家嘴", "上海中心", "环球金融中心", "金茂大厦", "海洋馆", "科技馆", "迪士尼", "浦东机场"],
            "陆家嘴": ["东方明珠", "上海中心", "环球金融中心", "金茂大厦", "正大广场"],
            "迪士尼": ["上海迪士尼乐园", "迪士尼小镇", "奕欧来奥特莱斯"],
            
            # 黄浦区
            "外滩": ["外滩", "南京路", "和平饭店", "外白渡桥"],
            "人民广场": ["人民广场", "上海博物馆", "上海大剧院", "人民公园"],
            "豫园": ["豫园", "城隍庙", "南翔馒头店"],
            "南京路": ["南京路步行街", "第一百货", "新世界"],
            
            # 徐汇区
            "徐家汇": ["徐家汇", "太平洋百货", "港汇恒隆", "上海体育馆"],
            "淮海路": ["淮海路", "新天地", "田子坊", "思南路"],
            
            # 静安区
            "静安寺": ["静安寺", "久光百货", "嘉里中心"],
            "南京西路": ["静安嘉里中心", "梅龙镇广场", "中信泰富"],
            
            # 长宁区
            "虹桥": ["虹桥机场", "虹桥火车站", "龙之梦"],
            
            # 普陀区
            "长风公园": ["长风公园", "长风海洋世界"],
            
            # 虹口区
            "四川北路": ["多伦路", "鲁迅公园", "虹口足球场"],
            
            # 杨浦区
            "五角场": ["五角场", "合生汇", "大学路"],
            
            # 闵行区
            "七宝": ["七宝古镇", "七宝老街"],
            
            # 青浦区
            "朱家角": ["朱家角古镇", "课植园", "大清邮局"],
            
            # 松江区
            "佘山": ["佘山", "欢乐谷", "玛雅海滩"],
            
            # 嘉定区
            "南翔": ["古漪园", "南翔老街"]
        }
        
        # 活动类型关键词
        self.activity_keywords = {
            "购物": ["shopping", "买", "商场", "百货", "奥特莱斯", "专卖店"],
            "美食": ["吃", "餐厅", "小吃", "美食", "菜", "料理", "火锅", "烧烤"],
            "文化": ["博物馆", "展览", "历史", "文化", "古迹", "艺术"],
            "娱乐": ["游乐", "娱乐", "KTV", "电影", "酒吧", "夜生活"],
            "自然": ["公园", "花园", "湖", "江", "山", "海", "自然"],
            "商务": ["会议", "商务", "办公", "工作"],
            "亲子": ["孩子", "儿童", "亲子", "家庭", "带娃"]
        }
        
        # 天气相关关键词
        self.weather_keywords = ["天气", "下雨", "晴天", "阴天", "温度", "冷", "热", "风", "雪"]
        
        # 交通相关关键词
        self.traffic_keywords = ["开车", "自驾", "地铁", "公交", "打车", "走路", "骑车", "交通", "堵车"]
        
        # 时间相关关键词
        self.time_keywords = ["今天", "明天", "周末", "早上", "上午", "下午", "晚上", "夜里"]
        
        logger.info("🤖 增强版智能旅行对话Agent初始化完成")
    
    def process_user_request(self, user_input: str, user_id: str = "default", show_thoughts: bool = True, return_thoughts: bool = False) -> Any:
        """
        处理用户请求的主入口 - 基于思考链的智能Agent系统
        
        流程：
        1. 深度理解用户需求，生成思考链（Thoughts）
        2. 从思考链中提取关键词和所需API
        3. 根据关键词智能调用相应的API
        4. 收集并整理实时数据
        5. 基于数据生成最终决策
        
        Args:
            user_input: 用户输入
            user_id: 用户ID
            show_thoughts: 是否展示思考过程给用户（控制台输出）
            return_thoughts: 是否在返回结果中包含思考过程（供API使用）
            
        Returns:
            如果return_thoughts=True，返回字典 {"response": str, "thoughts": list}
            否则返回字符串（回复内容）
        """
        logger.info(f"👤 用户 {user_id} 输入: {user_input}")
        
        # 获取或创建用户上下文
        if user_id not in self.user_contexts:
            self.user_contexts[user_id] = UserContext(
                user_id=user_id,
                conversation_history=[],
                travel_preferences=TravelPreference()
            )
        
        context = self.user_contexts[user_id]
        
        # 记录用户输入
        context.conversation_history.append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now().isoformat()
        })
        
        print("\n" + "="*80)
        print("🧠 智能旅游规划Agent - 思考链系统")
        print("="*80)
        
        # ============ Step 1: 深度理解需求并生成思考链 ============
        print("\n📋 Step 1: 深度理解您的需求...")
        thoughts = self._generate_thought_chain(user_input, context)
        
        if show_thoughts:
            self._display_thoughts(thoughts)
        
        # ============ Step 2: 从思考链中提取关键信息 ============
        print("\n🔍 Step 2: 提取关键信息和规划策略...")
        extracted_info = self._extract_info_from_thoughts(thoughts, user_input)
        self._display_extracted_info(extracted_info)
        
        # ============ Step 3: 智能API调用决策 ============
        print("\n🤖 Step 3: 决定需要调用的API服务...")
        api_plan = self._plan_api_calls(extracted_info, thoughts)
        self._display_api_plan(api_plan)
        
        # ============ Step 4: 执行API调用并收集数据 ============
        print("\n📡 Step 4: 调用API收集实时数据...")
        real_time_data = self._execute_api_calls(api_plan, extracted_info, context)
        
        # ============ Step 5: 综合分析并生成最终决策 ============
        print("\n💡 Step 5: 综合分析，生成最优旅游攻略...")
        final_response = self._generate_final_decision(
            user_input, thoughts, extracted_info, real_time_data, context
        )
        
        # 记录Agent回复
        context.conversation_history.append({
            "role": "assistant",
            "content": final_response,
            "thoughts": [{"step": t.step, "thought": t.thought, "keywords": t.keywords} for t in thoughts],
            "timestamp": datetime.now().isoformat()
        })
        
        print("\n" + "="*80)
        print("✅ 规划完成！")
        print("="*80 + "\n")
        
        # 根据参数决定返回格式
        if return_thoughts:
            # 返回完整信息，包含思考过程（供API使用）
            simplified_thoughts = []
            for t in thoughts:
                simplified_thoughts.append({
                    "step": t.step,
                    "thought": t.thought,
                    "keywords": t.keywords[:5],  # 只返回前5个关键词
                    "reasoning": t.reasoning,
                    "icon": self._get_thought_icon(t.step)
                })
            
            return {
                "response": final_response,
                "thoughts": simplified_thoughts,
                "extracted_info": {
                    "travel_days": extracted_info.get('travel_days', 1),
                    "locations": extracted_info.get('locations', []),
                    "companions": self._format_companions(extracted_info.get('companions', {})) if extracted_info.get('companions') else None,
                    "emotional_context": self._format_emotional_context(extracted_info.get('emotional_context', {})) if extracted_info.get('emotional_context') else None
                }
            }
        else:
            # 仅返回回复文本
            return final_response
    
    def _get_thought_icon(self, step: int) -> str:
        """根据步骤获取合适的图标"""
        icons = ["🤔", "💡", "🌤️", "🗺️", "🚦", "📊", "✨"]
        return icons[min(step - 1, len(icons) - 1)]
    
    # ==================== 思考链系统核心方法 ====================
    
    def _generate_thought_chain(self, user_input: str, context: UserContext) -> List[ThoughtProcess]:
        """生成思考链 - 让AI深度分析用户需求"""
        system_prompt = """你是一个专业的上海旅游规划专家。请深入分析用户的需求，并生成一个详细的思考过程。

你需要思考：
1. 用户的核心需求是什么？（景点、美食、交通、住宿等）
2. 用户提到了哪些具体地点或区域？
3. 用户的时间安排如何？（几天、什么时候）
4. 用户有什么特殊偏好？（不喜欢人多、想要浪漫氛围等）
5. 需要哪些实时数据来支持决策？（天气、路况、POI等）

请以JSON格式返回你的思考过程：
{
  "thoughts": [
    {
      "step": 1,
      "thought": "用户想要规划3天的上海旅游",
      "keywords": ["3天", "上海", "旅游"],
      "api_needs": ["天气", "景点"],
      "reasoning": "需要查询未来3天天气，并推荐适合3天游览的景点"
    }
  ]
}"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"请分析这个需求：{user_input}"}
        ]
        
        try:
            response = self.doubao_agent.generate_response(messages)
            
            # 尝试解析JSON响应
            思考数据 = self._parse_thought_response(response)
            
            # 转换为ThoughtProcess对象
            thoughts = []
            for idx, thought_data in enumerate(思考数据.get("thoughts", []), 1):
                thought = ThoughtProcess(
                    step=idx,
                    thought=thought_data.get("thought", ""),
                    keywords=thought_data.get("keywords", []),
                    mcp_services=self._map_api_needs_to_services(thought_data.get("api_needs", [])),
                    reasoning=thought_data.get("reasoning", ""),
                    timestamp=datetime.now().isoformat()
                )
                thoughts.append(thought)
            
            # 如果AI没有返回有效的思考链，使用备用方法
            if not thoughts:
                thoughts = self._fallback_thought_generation(user_input, context)
            
            return thoughts
            
        except Exception as e:
            logger.error(f"思考链生成失败: {e}")
            # 使用备用方法
            return self._fallback_thought_generation(user_input, context)
    
    def _parse_thought_response(self, response: str) -> Dict:
        """解析AI的思考响应"""
        try:
            # 尝试提取JSON部分
            import re
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
            else:
                # 如果没有JSON，返回空字典
                return {"thoughts": []}
        except:
            return {"thoughts": []}
    
    def _map_api_needs_to_services(self, api_needs: List[str]) -> List[MCPServiceType]:
        """将API需求映射到服务类型"""
        service_map = {
            "天气": MCPServiceType.WEATHER,
            "weather": MCPServiceType.WEATHER,
            "景点": MCPServiceType.POI,
            "poi": MCPServiceType.POI,
            "餐厅": MCPServiceType.POI,
            "美食": MCPServiceType.POI,
            "导航": MCPServiceType.NAVIGATION,
            "路线": MCPServiceType.NAVIGATION,
            "navigation": MCPServiceType.NAVIGATION,
            "交通": MCPServiceType.TRAFFIC,
            "路况": MCPServiceType.TRAFFIC,
            "traffic": MCPServiceType.TRAFFIC,
            "人流": MCPServiceType.CROWD,
            "crowd": MCPServiceType.CROWD
        }
        
        services = []
        for need in api_needs:
            service = service_map.get(need.lower())
            if service and service not in services:
                services.append(service)
        
        return services
    
    def _fallback_thought_generation(self, user_input: str, context: UserContext) -> List[ThoughtProcess]:
        """备用思考链生成方法 - 基于规则"""
        thoughts = []
        keywords = self._extract_keywords(user_input)
        detected_locations, activity_types = self._analyze_user_intent(user_input)
        travel_days = self._extract_travel_days(user_input)
        
        # Thought 1: 理解需求
        thoughts.append(ThoughtProcess(
            step=1,
            thought=f"用户需要规划{travel_days}天的上海旅游攻略",
            keywords=keywords + [f"{travel_days}天"] + detected_locations,
            mcp_services=[],
            reasoning="首先理解用户的基本需求和时间安排",
            timestamp=datetime.now().isoformat()
        ))
        
        # Thought 2: 地点分析
        if detected_locations:
            thoughts.append(ThoughtProcess(
                step=2,
                thought=f"用户提到了具体地点：{', '.join(detected_locations)}",
                keywords=detected_locations,
                mcp_services=[MCPServiceType.POI],
                reasoning="需要搜索这些地点的详细信息和周边景点",
                timestamp=datetime.now().isoformat()
            ))
        else:
            thoughts.append(ThoughtProcess(
                step=2,
                thought="用户没有指定具体地点，需要推荐上海经典景点",
                keywords=["上海", "经典景点"],
                mcp_services=[MCPServiceType.POI],
                reasoning="推荐适合游览时长的经典景点组合",
                timestamp=datetime.now().isoformat()
            ))
        
        # Thought 3: 天气考虑
        thoughts.append(ThoughtProcess(
            step=3,
            thought=f"需要查询未来{travel_days}天的天气情况",
            keywords=["天气", "预报"],
            mcp_services=[MCPServiceType.WEATHER],
            reasoning="根据天气情况调整室内外活动安排",
            timestamp=datetime.now().isoformat()
        ))
        
        # Thought 4: 交通规划
        if len(detected_locations) > 1 or "交通" in user_input or "路线" in user_input:
            thoughts.append(ThoughtProcess(
                step=4,
                thought="需要规划景点间的交通路线",
                keywords=["导航", "路线", "交通"],
                mcp_services=[MCPServiceType.NAVIGATION, MCPServiceType.TRAFFIC],
                reasoning="提供最优交通方案，考虑路况避免拥堵",
                timestamp=datetime.now().isoformat()
            ))
        
        return thoughts
    
    def _display_thoughts(self, thoughts: List[ThoughtProcess]):
        """展示思考过程"""
        print("\n💭 AI思考过程：")
        print("-" * 80)
        for thought in thoughts:
            print(f"\n  步骤 {thought.step}: {thought.thought}")
            if thought.keywords:
                print(f"  关键词: {', '.join(thought.keywords)}")
            if thought.mcp_services:
                services = [s.value for s in thought.mcp_services]
                print(f"  需要API: {', '.join(services)}")
            print(f"  原因: {thought.reasoning}")
    
    def _extract_info_from_thoughts(self, thoughts: List[ThoughtProcess], user_input: str) -> Dict[str, Any]:
        """从思考链中提取关键信息 - 包括人文因素"""
        # 收集所有关键词
        all_keywords = []
        for thought in thoughts:
            all_keywords.extend(thought.keywords)
        
        # 提取地点
        locations = self._extract_locations_from_input(user_input)
        
        # 智能选择关键词进行输入提示API调用
        enhanced_locations = []
        
        # 按优先级排序关键词
        priority_keywords = self._prioritize_keywords_for_inputtips(all_keywords, user_input)
        
        # 只对前5个最重要的关键词使用输入提示API（分批调用避免QPS超限）
        for i, keyword in enumerate(priority_keywords[:5]):
            try:
                # 每次调用间隔0.4秒，确保不超过QPS限制
                if i > 0:
                    time.sleep(0.4)
                
                # 使用输入提示API验证和增强地点信息
                tips = self.get_inputtips(keyword, city="上海", citylimit=True)
                if tips:
                    enhanced_locations.append({
                        "keyword": keyword,
                        "suggestions": tips[:5],  # 前5个建议
                        "priority": i + 1
                    })
                    logger.info(f"输入提示API成功: {keyword} -> {len(tips)}个建议")
            except Exception as e:
                logger.warning(f"输入提示API调用失败 for {keyword}: {e}")
                # 继续处理下一个关键词，不中断整个流程
        
        # 提取活动类型
        activity_types = []
        for activity, kws in self.activity_keywords.items():
            if any(kw in user_input for kw in kws):
                activity_types.append(activity)
        
        # 提取时间信息
        travel_days = self._extract_travel_days(user_input)
        
        # ========== 新增：提取人文因素 ==========
        
        # 提取社交关系和同伴信息
        companions = self._extract_companions(user_input)
        
        # 提取情感需求和氛围
        emotional_context = self._extract_emotional_context(user_input)
        
        # 提取预算信息
        budget_info = self._extract_budget(user_input)
        
        # 提取特殊偏好
        preferences = self._extract_preferences(user_input)
        
        # 提取完整的用户原始意图（保留所有细节）
        user_intent_summary = self._summarize_user_intent(user_input, thoughts)
        
        return {
            "keywords": list(set(all_keywords)),
            "locations": locations,
            "enhanced_locations": enhanced_locations,
            "activity_types": activity_types,
            "travel_days": travel_days,
            "route_info": self._extract_route_from_input(user_input),
            # 人文因素
            "companions": companions,
            "emotional_context": emotional_context,
            "budget_info": budget_info,
            "preferences": preferences,
            "user_intent_summary": user_intent_summary,
            "original_input": user_input  # 保留原始输入
        }
    
    def _extract_companions(self, user_input: str) -> Dict[str, Any]:
        """提取同伴信息"""
        companions = {
            "type": None,
            "count": 1,
            "details": []
        }
        
        # 检测同伴类型
        companion_patterns = {
            "女朋友": {"type": "romantic_partner", "gender": "female", "relationship": "girlfriend"},
            "男朋友": {"type": "romantic_partner", "gender": "male", "relationship": "boyfriend"},
            "老婆": {"type": "spouse", "gender": "female", "relationship": "wife"},
            "老公": {"type": "spouse", "gender": "male", "relationship": "husband"},
            "爱人": {"type": "spouse", "relationship": "spouse"},
            "女朋友": {"type": "romantic_partner", "relationship": "girlfriend"},
            "父母": {"type": "family", "relationship": "parents", "count": 2},
            "爸妈": {"type": "family", "relationship": "parents", "count": 2},
            "孩子": {"type": "family", "relationship": "children"},
            "小孩": {"type": "family", "relationship": "children"},
            "宝宝": {"type": "family", "relationship": "baby"},
            "家人": {"type": "family", "relationship": "family"},
            "朋友": {"type": "friends", "relationship": "friends"},
            "闺蜜": {"type": "friends", "relationship": "best_friend", "gender": "female"},
            "兄弟": {"type": "friends", "relationship": "brother"},
            "同事": {"type": "colleagues", "relationship": "colleagues"},
            "团队": {"type": "team", "relationship": "team"}
        }
        
        for pattern, info in companion_patterns.items():
            if pattern in user_input:
                companions["type"] = info["type"]
                companions["details"].append(info)
                if "count" in info:
                    companions["count"] += info["count"]
                else:
                    companions["count"] += 1
                break
        
        return companions
    
    def _extract_emotional_context(self, user_input: str) -> Dict[str, Any]:
        """提取情感需求和氛围"""
        emotional_context = {
            "mood": [],
            "atmosphere": [],
            "avoid": [],
            "desire": []
        }
        
        # 情绪和氛围关键词
        mood_keywords = {
            "浪漫": "romantic",
            "温馨": "cozy",
            "轻松": "relaxed",
            "安静": "quiet",
            "热闹": "lively",
            "文艺": "artistic",
            "小资": "petty_bourgeois",
            "高端": "upscale",
            "奢华": "luxury",
            "朴实": "simple",
            "地道": "authentic",
            "特色": "unique"
        }
        
        for keyword, mood in mood_keywords.items():
            if keyword in user_input:
                emotional_context["mood"].append(mood)
                emotional_context["atmosphere"].append(keyword)
        
        # 避开的内容
        avoid_keywords = ["避开", "不要", "别去", "不想", "讨厌"]
        for avoid_kw in avoid_keywords:
            if avoid_kw in user_input:
                # 提取避开的具体内容
                if "人多" in user_input or "拥挤" in user_input or "热门" in user_input:
                    emotional_context["avoid"].append("crowded_places")
                if "商业" in user_input:
                    emotional_context["avoid"].append("commercial")
                if "网红" in user_input:
                    emotional_context["avoid"].append("internet_famous")
        
        # 期望体验
        desire_keywords = {
            "感受": "experience",
            "体验": "experience",
            "了解": "understand",
            "风土人情": "local_culture",
            "当地生活": "local_life",
            "历史": "history",
            "文化": "culture",
            "美食": "cuisine"
        }
        
        for keyword, desire in desire_keywords.items():
            if keyword in user_input:
                emotional_context["desire"].append(desire)
        
        return emotional_context
    
    def _extract_budget(self, user_input: str) -> Dict[str, Any]:
        """提取预算信息"""
        import re
        
        budget_info = {
            "amount": None,
            "level": "medium",
            "constraint": None
        }
        
        # 提取具体金额
        amount_patterns = [
            r'(\d+)万',  # 如：2万
            r'(\d+)千',  # 如：5千
            r'(\d+)元',  # 如：20000元
            r'预算.*?(\d+)',  # 预算xxx
            r'不低于.*?(\d+)',  # 不低于xxx
            r'不超过.*?(\d+)',  # 不超过xxx
        ]
        
        for pattern in amount_patterns:
            match = re.search(pattern, user_input)
            if match:
                amount = int(match.group(1))
                if '万' in pattern:
                    amount *= 10000
                elif '千' in pattern:
                    amount *= 1000
                budget_info["amount"] = amount
                break
        
        # 判断预算等级
        if budget_info["amount"]:
            if budget_info["amount"] >= 20000:
                budget_info["level"] = "high"
            elif budget_info["amount"] >= 10000:
                budget_info["level"] = "medium_high"
            elif budget_info["amount"] >= 5000:
                budget_info["level"] = "medium"
            else:
                budget_info["level"] = "low"
        
        # 预算约束
        if "不低于" in user_input:
            budget_info["constraint"] = "minimum"
        elif "不超过" in user_input or "最多" in user_input:
            budget_info["constraint"] = "maximum"
        
        # 关键词判断
        if "经济" in user_input or "省钱" in user_input or "便宜" in user_input:
            budget_info["level"] = "low"
        elif "奢华" in user_input or "高端" in user_input or "不差钱" in user_input:
            budget_info["level"] = "high"
        
        return budget_info
    
    def _extract_preferences(self, user_input: str) -> List[str]:
        """提取特殊偏好"""
        preferences = []
        
        preference_keywords = {
            "风土人情": "local_culture",
            "当地特色": "local_specialty",
            "非热门": "off_the_beaten_path",
            "小众": "niche",
            "网红": "internet_famous",
            "打卡": "photo_spots",
            "美食": "food_focused",
            "购物": "shopping_focused",
            "历史": "history_focused",
            "自然": "nature_focused",
            "艺术": "art_focused",
            "夜生活": "nightlife",
            "慢节奏": "slow_paced",
            "深度游": "in_depth"
        }
        
        for keyword, preference in preference_keywords.items():
            if keyword in user_input:
                preferences.append(preference)
        
        return preferences
    
    def _summarize_user_intent(self, user_input: str, thoughts: List[ThoughtProcess]) -> str:
        """总结用户完整意图，保留所有人文细节"""
        # 使用AI来总结，保留人文细节
        try:
            summary_prompt = f"""请用一句话总结用户的旅游需求，要保留所有人文细节和情感因素。

用户输入：{user_input}

要求：
1. 保留同伴信息（如：女朋友、父母、孩子等）
2. 保留情感需求（如：浪漫、温馨、避开人群等）
3. 保留预算信息
4. 保留特殊偏好
5. 用温暖、人性化的语言表达

示例：
输入："我想带女朋友去上海玩3天"
输出："您计划和女朋友一起在上海度过浪漫的3天"

请总结："""
            
            messages = [{"role": "user", "content": summary_prompt}]
            summary = self.doubao_agent.generate_response(messages)
            return summary.strip()
        except:
            # 如果AI失败，返回原始输入
            return user_input
    
    def _display_extracted_info(self, info: Dict[str, Any]):
        """展示提取的信息 - 包括人文因素"""
        print("\n📌 提取的关键信息：")
        print("-" * 80)
        
        # 显示用户意图总结（最重要，放在最前面）
        if info.get('user_intent_summary'):
            print(f"  💭 需求理解: {info['user_intent_summary']}")
            print()
        
        # 显示同伴信息
        if info.get('companions') and info['companions']['type']:
            companion_desc = self._format_companions(info['companions'])
            print(f"  👥 同伴信息: {companion_desc}")
        
        # 显示情感需求和氛围
        if info.get('emotional_context'):
            emotional_desc = self._format_emotional_context(info['emotional_context'])
            if emotional_desc:
                print(f"  💝 情感需求: {emotional_desc}")
        
        # 显示预算信息
        if info.get('budget_info') and info['budget_info']['amount']:
            budget_desc = self._format_budget(info['budget_info'])
            print(f"  💰 预算信息: {budget_desc}")
        
        # 显示特殊偏好
        if info.get('preferences'):
            pref_desc = self._format_preferences(info['preferences'])
            print(f"  ⭐ 特殊偏好: {pref_desc}")
        
        # 基础信息
        print(f"\n  📅 旅行天数: {info['travel_days']}天")
        
        if info['locations']:
            print(f"  📍 提到的地点: {', '.join(info['locations'])}")
        
        if info['enhanced_locations']:
            print(f"  🔍 智能识别的地点:")
            for loc in info['enhanced_locations'][:3]:
                print(f"     • {loc['keyword']}: {loc['suggestions'][0]['name'] if loc['suggestions'] else '未找到'}")
        
        if info['activity_types']:
            print(f"  🎯 活动类型: {', '.join(info['activity_types'])}")
        
        if info['route_info']:
            print(f"  🗺️  路线: {info['route_info']['start']} → {info['route_info']['end']}")
    
    def _format_companions(self, companions: Dict[str, Any]) -> str:
        """格式化同伴信息"""
        if not companions['details']:
            return "独自一人"
        
        companion_names = {
            "girlfriend": "女朋友",
            "boyfriend": "男朋友",
            "wife": "妻子",
            "husband": "丈夫",
            "spouse": "爱人",
            "parents": "父母",
            "children": "孩子",
            "baby": "宝宝",
            "family": "家人",
            "friends": "朋友",
            "best_friend": "闺蜜",
            "brother": "兄弟",
            "colleagues": "同事",
            "team": "团队"
        }
        
        parts = []
        for detail in companions['details']:
            relationship = detail.get('relationship', '')
            name = companion_names.get(relationship, relationship)
            parts.append(name)
        
        if companions['count'] > 2:
            return f"{', '.join(parts)} ({companions['count']}人)"
        else:
            return ', '.join(parts)
    
    def _format_emotional_context(self, emotional_context: Dict[str, Any]) -> str:
        """格式化情感需求"""
        parts = []
        
        if emotional_context['atmosphere']:
            parts.append(f"氛围偏好：{', '.join(emotional_context['atmosphere'])}")
        
        if emotional_context['avoid']:
            avoid_names = {
                "crowded_places": "避开人群",
                "commercial": "避开商业区",
                "internet_famous": "避开网红景点"
            }
            avoid_desc = [avoid_names.get(a, a) for a in emotional_context['avoid']]
            parts.append(f"{', '.join(avoid_desc)}")
        
        if emotional_context['desire']:
            desire_names = {
                "experience": "想要体验",
                "local_culture": "感受风土人情",
                "local_life": "了解当地生活",
                "history": "了解历史",
                "culture": "了解文化",
                "cuisine": "品尝美食"
            }
            desire_desc = [desire_names.get(d, d) for d in emotional_context['desire'][:2]]
            parts.append(f"{', '.join(desire_desc)}")
        
        return '；'.join(parts) if parts else ""
    
    def _format_budget(self, budget_info: Dict[str, Any]) -> str:
        """格式化预算信息"""
        if budget_info['amount']:
            amount_str = f"{budget_info['amount']}元"
            if budget_info['constraint'] == 'minimum':
                return f"不低于{amount_str} ({budget_info['level']}档次)"
            elif budget_info['constraint'] == 'maximum':
                return f"不超过{amount_str} ({budget_info['level']}档次)"
            else:
                return f"约{amount_str} ({budget_info['level']}档次)"
        else:
            level_names = {
                "low": "经济型",
                "medium": "中等",
                "medium_high": "中高端",
                "high": "高端"
            }
            return level_names.get(budget_info['level'], budget_info['level'])
    
    def _format_preferences(self, preferences: List[str]) -> str:
        """格式化特殊偏好"""
        preference_names = {
            "local_culture": "风土人情",
            "local_specialty": "当地特色",
            "off_the_beaten_path": "小众景点",
            "niche": "小众体验",
            "internet_famous": "网红打卡",
            "photo_spots": "拍照打卡",
            "food_focused": "美食之旅",
            "shopping_focused": "购物为主",
            "history_focused": "历史文化",
            "nature_focused": "自然风光",
            "art_focused": "艺术体验",
            "nightlife": "夜生活",
            "slow_paced": "慢节奏",
            "in_depth": "深度游"
        }
        
        pref_desc = [preference_names.get(p, p) for p in preferences[:5]]
        return ', '.join(pref_desc)
    
    def _plan_api_calls(self, extracted_info: Dict[str, Any], thoughts: List[ThoughtProcess]) -> Dict[str, Any]:
        """规划API调用策略"""
        api_plan = {
            "weather": True,
            "poi": True,
            "navigation": False,
            "traffic": False,
            "crowd": False,
            "inputtips": False
        }
        
        # 从thoughts中收集需要的API
        for thought in thoughts:
            for service in thought.mcp_services:
                if service == MCPServiceType.WEATHER:
                    api_plan["weather"] = True
                elif service == MCPServiceType.POI:
                    api_plan["poi"] = True
                elif service == MCPServiceType.NAVIGATION:
                    api_plan["navigation"] = True
                elif service == MCPServiceType.TRAFFIC:
                    api_plan["traffic"] = True
                elif service == MCPServiceType.CROWD:
                    api_plan["crowd"] = True
        
        # 如果有多天行程，必须查天气
        if extracted_info['travel_days'] > 1:
            api_plan["weather"] = True
        
        # 如果有地点或路线，需要POI和导航
        if extracted_info['locations'] or extracted_info['route_info']:
            api_plan["poi"] = True
            api_plan["navigation"] = True
            api_plan["traffic"] = True
        
        # 如果有模糊的关键词，使用输入提示API
        if extracted_info['keywords'] and not extracted_info['locations']:
            api_plan["inputtips"] = True
        
        return api_plan
    
    def _display_api_plan(self, api_plan: Dict[str, Any]):
        """展示API调用计划"""
        print("\n📞 API调用计划：")
        print("-" * 80)
        
        api_icons = {
            "weather": "🌤️  天气API",
            "poi": "🏛️  POI搜索API",
            "navigation": "🗺️  导航API",
            "traffic": "🚦 路况API",
            "crowd": "👥 人流API",
            "inputtips": "💡 输入提示API"
        }
        
        for api, enabled in api_plan.items():
            if enabled:
                print(f"  ✓ {api_icons.get(api, api)}")
    
    def _execute_api_calls(self, api_plan: Dict[str, Any], extracted_info: Dict[str, Any], context: UserContext) -> Dict[str, Any]:
        """执行API调用"""
        real_time_data = {}
        
        locations = extracted_info['locations'] if extracted_info['locations'] else ["上海"]
        
        # 调用天气API
        if api_plan["weather"]:
            print("  🌤️  正在获取天气信息...")
            weather_data = {}
            for location in locations:
                try:
                    weather = self.get_weather(location, context.travel_preferences.start_date)
                except Exception as e:
                    logger.warning(f"获取{location}天气失败: {e}")
                    weather = []
                weather_data[location] = weather or []
            
            if not weather_data:
                weather_data["上海"] = []
            real_time_data["weather"] = weather_data
        
        # 调用输入提示API（智能选择关键词）
        if api_plan["inputtips"] and extracted_info['keywords']:
            print("  💡 正在使用输入提示API识别地点...")
            tips_data = {}
            
            # 使用智能优先级排序
            priority_keywords = self._prioritize_keywords_for_inputtips(extracted_info['keywords'], extracted_info.get('original_input', ''))
            
            # 对前3个高优先级关键词调用API
            for i, keyword in enumerate(priority_keywords[:3]):
                try:
                    # 控制调用频率
                    if i > 0:
                        time.sleep(0.4)
                    
                    tips = self.get_inputtips(keyword, city="上海", citylimit=True)
                    if tips:
                        tips_data[keyword] = {
                            "suggestions": tips[:5],
                            "priority": i + 1,
                            "count": len(tips)
                        }
                        logger.info(f"输入提示API成功: {keyword} -> {len(tips)}个建议")
                except Exception as e:
                    logger.warning(f"输入提示API调用失败 for {keyword}: {e}")
            
            real_time_data["inputtips"] = tips_data
        
        # 调用POI API
        if api_plan["poi"]:
            print("  🏛️  正在搜索景点和餐厅...")
            poi_data = {}
            for location in locations:
                attractions = self.search_poi("景点", location, "110000")
                poi_data[f"{location}_景点"] = attractions[:5]
                
                restaurants = self.search_poi("餐厅", location, "050000")
                poi_data[f"{location}_餐饮"] = restaurants[:5]
            real_time_data["poi"] = poi_data
        
        # 调用导航API
        if api_plan["navigation"]:
            print("  🗺️  正在规划路线...")
            navigation_data = {}
            
            if extracted_info['route_info']:
                routes = self.get_navigation_routes(
                    extracted_info['route_info']['start'],
                    extracted_info['route_info']['end']
                )
                navigation_data[f"{extracted_info['route_info']['start']}_to_{extracted_info['route_info']['end']}"] = routes
            elif len(locations) >= 2:
                for i in range(len(locations) - 1):
                    routes = self.get_navigation_routes(locations[i], locations[i+1])
                    navigation_data[f"{locations[i]}_to_{locations[i+1]}"] = routes
            
            real_time_data["navigation"] = navigation_data
        
        # 调用路况API
        if api_plan["traffic"]:
            print("  🚦 正在检查路况...")
            traffic_data = {}
            for location in locations:
                traffic = self.get_traffic_status(location)
                traffic_data[location] = traffic
            real_time_data["traffic"] = traffic_data
        
        print("  ✅ 数据收集完成！")
        return real_time_data
    
    def _build_environmental_recommendations(self, extracted_info: Dict[str, Any],
                                             real_time_data: Dict[str, Any],
                                             context: UserContext) -> Dict[str, Any]:
        """融合天气与POI的综合推荐分析"""
        locations = list(extracted_info.get('locations') or [])
        weather_map = real_time_data.get("weather") or {}
        poi_map = real_time_data.get("poi") or {}
        
        if not locations:
            derived_locations = list(weather_map.keys())
            if not derived_locations:
                derived_locations = [key.split("_")[0] for key in poi_map.keys()]
            locations = derived_locations or ["上海"]
        
        preferences = set()
        for key in ("activity_types", "preferences"):
            pref_list = extracted_info.get(key) or []
            preferences.update(pref_list)
        
        budget_info = extracted_info.get('budget_info') or {}
        budget_level = budget_info.get('level')
        
        recommendations = []
        
        for location in locations:
            weather_records = self._get_weather_records_for_location(weather_map, location)
            weather_analysis = self._analyze_weather_condition(weather_records)
            
            collected_pois = self._collect_pois_for_location(poi_map, location)
            scored_pois = []
            for category_label, poi in collected_pois:
                score, reasons = self._score_poi_candidate(
                    poi,
                    category_label,
                    weather_analysis,
                    preferences,
                    budget_level
                )
                scored_pois.append({
                    "name": poi.name,
                    "category": category_label or poi.category,
                    "address": poi.address,
                    "score": round(score, 1),
                    "reasons": reasons,
                    "price": poi.price,
                    "business_hours": poi.business_hours
                })
            
            scored_pois.sort(key=lambda x: x["score"], reverse=True)
            
            recommendations.append({
                "location": location,
                "weather": weather_analysis,
                "top_pois": scored_pois[:5],
                "indoor_priority": not weather_analysis.get("suitable_for_outdoor", True),
                "data_available": bool(collected_pois)
            })
        
        overall_tips = self._generate_overall_tips(recommendations)
        
        return {
            "generated_at": datetime.now().isoformat(),
            "locations": recommendations,
            "overall_tips": overall_tips
        }
    
    def _get_weather_records_for_location(self, weather_map: Dict[str, Any], location: str) -> List[WeatherInfo]:
        """获取指定地点的天气记录，必要时回退到其他地点"""
        if not weather_map:
            return []
        
        if location in weather_map and weather_map[location]:
            return weather_map[location]
        
        for key, records in weather_map.items():
            if location in key and records:
                return records
        
        for records in weather_map.values():
            if records:
                return records
        
        return []
    
    def _analyze_weather_condition(self, weather_records: List[WeatherInfo]) -> Dict[str, Any]:
        """根据天气数据生成可用性评估"""
        if not weather_records:
            return {
                "summary": "暂无天气数据",
                "condition": "unknown",
                "temperature": "未知",
                "average_temperature": None,
                "suitable_for_outdoor": False,
                "advice": "暂无可靠天气信息，请提醒用户出行前再次确认天气预报。",
                "score": 50
            }
        
        record = weather_records[0] if isinstance(weather_records, list) else weather_records
        weather_text = getattr(record, "weather", "") or ""
        temperature_text = getattr(record, "temperature", "") or ""
        temp_value = self._parse_temperature_value(temperature_text)
        
        condition = "moderate"
        score = 70
        suitable_for_outdoor = True
        advice = "天气整体适宜，可以灵活安排室内外活动。"
        
        if any(keyword in weather_text for keyword in ["雷", "暴雨", "台风", "大风", "冰雹"]):
            condition = "extreme"
            score = 20
            suitable_for_outdoor = False
            advice = "天气较为极端，请优先选择室内活动，并留意官方安全预警。"
        elif "雨" in weather_text:
            condition = "rainy"
            score = 45
            suitable_for_outdoor = False
            advice = "有降雨，建议准备雨具，把重点放在室内或半室内项目上。"
        elif "雪" in weather_text:
            condition = "snow"
            score = 40
            suitable_for_outdoor = False
            advice = "可能有降雪或湿冷，注意防滑保暖，多安排室内体验。"
        elif any(keyword in weather_text for keyword in ["阴", "多云"]):
            condition = "cloudy"
            score = 65
            advice = "多云天气，光线柔和，适合轻松散步或艺术展览等活动。"
        elif any(keyword in weather_text for keyword in ["晴", "阳"]):
            condition = "sunny"
            score = 85
            advice = "晴朗天气，适合户外活动，也别忘了补水和防晒。"
        
        if temp_value is not None:
            if temp_value >= 33:
                score -= 10
                advice += " 气温偏高，户外时段请安排在早晚并注意补水。"
            elif temp_value <= 5:
                score -= 10
                suitable_for_outdoor = False
                advice += " 气温较低，需要防寒保暖，可多考虑室内选项。"
        
        return {
            "summary": weather_text or "暂无天气描述",
            "condition": condition,
            "temperature": temperature_text or "未知",
            "average_temperature": temp_value,
            "suitable_for_outdoor": suitable_for_outdoor,
            "advice": advice,
            "score": max(min(score, 100), 0)
        }
    
    def _parse_temperature_value(self, temperature_text: str) -> Optional[float]:
        """解析温度字符串，返回平均温度"""
        if not temperature_text:
            return None
        matches = re.findall(r'-?\d+', temperature_text)
        if not matches:
            return None
        values = [int(m) for m in matches]
        if not values:
            return None
        return sum(values) / len(values)
    
    def _collect_pois_for_location(self, poi_map: Dict[str, List[POIInfo]], location: str) -> List[Tuple[str, POIInfo]]:
        """收集与地点相关的POI"""
        if not poi_map:
            return []
        
        collected: List[Tuple[str, POIInfo]] = []
        for key, pois in poi_map.items():
            if not pois:
                continue
            key_location, _, category_label = key.partition("_")
            matches_location = (key_location == location) or (location in key_location) or (location in key)
            if matches_location:
                for poi in pois:
                    normalized_poi = poi
                    if isinstance(poi, dict):
                        normalized_poi = POIInfo(
                            name=poi.get("name", ""),
                            address=poi.get("address", ""),
                            rating=float(poi.get("rating", 0) or 0),
                            business_hours=poi.get("business_hours", "") or poi.get("open_time", ""),
                            price=str(poi.get("price", "")),
                            distance=str(poi.get("distance", "")),
                            category=poi.get("category", ""),
                            reviews=poi.get("reviews", [])
                        )
                    collected.append((category_label or normalized_poi.category, normalized_poi))
        
        if not collected:
            for key, pois in poi_map.items():
                if pois:
                    fallback_category = key.partition("_")[2]
                    for poi in pois:
                        normalized_poi = poi
                        if isinstance(poi, dict):
                            normalized_poi = POIInfo(
                                name=poi.get("name", ""),
                                address=poi.get("address", ""),
                                rating=float(poi.get("rating", 0) or 0),
                                business_hours=poi.get("business_hours", "") or poi.get("open_time", ""),
                                price=str(poi.get("price", "")),
                                distance=str(poi.get("distance", "")),
                                category=poi.get("category", ""),
                                reviews=poi.get("reviews", [])
                            )
                        collected.append((fallback_category or normalized_poi.category, normalized_poi))
                    break
        
        return collected
    
    def _is_outdoor_poi(self, poi: POIInfo, category_label: Optional[str]) -> bool:
        """判断POI是否偏户外场景"""
        text = f"{poi.category or ''}{category_label or ''}{poi.name or ''}"
        outdoor_keywords = ["公园", "广场", "景区", "风景", "户外", "古镇", "滨江", "滨水", "步道", "花园", "绿地", "亲水", "动物园", "植物园", "露台", "天台"]
        return any(keyword in text for keyword in outdoor_keywords)
    
    def _is_indoor_poi(self, poi: POIInfo, category_label: Optional[str]) -> bool:
        """判断POI是否偏室内场景"""
        text = f"{poi.category or ''}{category_label or ''}{poi.name or ''}"
        indoor_keywords = ["博物馆", "美术馆", "展览", "购物", "商场", "百货", "餐厅", "咖啡", "KTV", "剧院", "水族馆", "书店", "市集", "体验馆"]
        return any(keyword in text for keyword in indoor_keywords)
    
    def _infer_price_level(self, price_text: str) -> Optional[str]:
        """根据价格信息判断消费档次"""
        if not price_text:
            return None
        matches = re.findall(r'\d+', price_text)
        if not matches:
            return None
        amount = int(matches[0])
        if amount <= 80:
            return "low"
        if amount <= 180:
            return "medium"
        if amount <= 300:
            return "medium_high"
        return "high"
    
    def _score_poi_candidate(self, poi: POIInfo, category_label: Optional[str],
                             weather_analysis: Dict[str, Any],
                             preferences: set,
                             budget_level: Optional[str]) -> Tuple[float, List[str]]:
        """计算POI综合得分及推荐理由"""
        score = 40.0
        reasons: List[str] = []
        
        rating = poi.rating if isinstance(poi.rating, (int, float)) else 0
        if rating and rating > 0:
            score += min(rating * 18, 60)
            reasons.append(f"大众评分 {rating:.1f} 分")
        else:
            reasons.append("口碑信息有限，以现场体验为准")
        
        if self._is_outdoor_poi(poi, category_label):
            reasons.append("户外体验感强")
            if not weather_analysis.get("suitable_for_outdoor", True):
                score -= 25
                reasons.append("当前天气不利于长时间户外，建议作为备选")
            else:
                score += 12
        elif self._is_indoor_poi(poi, category_label):
            reasons.append("室内环境舒适")
            if not weather_analysis.get("suitable_for_outdoor", True):
                score += 18
            else:
                score += 6
        
        preference_labels = {
            "local_culture": "风土人情",
            "local_specialty": "当地特色",
            "off_the_beaten_path": "小众探索",
            "niche": "小众体验",
            "internet_famous": "网红打卡",
            "photo_spots": "拍照",
            "food_focused": "美食",
            "shopping_focused": "购物",
            "history_focused": "历史文化",
            "nature_focused": "自然风光",
            "art_focused": "艺术",
            "nightlife": "夜生活",
            "slow_paced": "慢节奏",
            "in_depth": "深度体验",
            "购物": "购物",
            "美食": "美食",
            "文化": "文化",
            "娱乐": "娱乐",
            "自然": "自然",
            "亲子": "亲子",
            "休闲": "休闲"
        }
        
        poi_text = f"{poi.name or ''}{poi.category or ''}{category_label or ''}"
        for pref in preferences:
            pref_display = preference_labels.get(pref, pref)
            if pref_display and pref_display != pref and pref_display in poi_text:
                score += 10
                reasons.append(f"匹配偏好「{pref_display}」")
            elif pref in poi_text:
                score += 10
                reasons.append(f"匹配偏好「{pref}」")
        
        price_level = self._infer_price_level(poi.price)
        if budget_level and price_level:
            if budget_level == "low" and price_level in ("medium_high", "high"):
                score -= 18
                reasons.append("价格偏高，注意控制预算")
            elif budget_level == "high" and price_level in ("low", "medium"):
                score += 8
                reasons.append("价格亲民，可适当升级体验")
            elif budget_level == price_level:
                score += 6
                reasons.append("价格与预算匹配")
        
        return max(min(score, 100), 0), list(dict.fromkeys(reasons))
    
    def _generate_overall_tips(self, recommendations: List[Dict[str, Any]]) -> List[str]:
        """提炼整体提示"""
        tips: List[str] = []
        
        if not recommendations:
            return ["尚未收集到有效的天气或POI数据，请提醒用户稍后再试。"]
        
        challenging_weather = [
            rec for rec in recommendations
            if rec["weather"].get("condition") in ("extreme", "rainy", "snow") or rec["weather"].get("score", 0) < 55
        ]
        if challenging_weather:
            for rec in challenging_weather:
                tips.append(f"{rec['location']}天气提示：{rec['weather'].get('advice', '请关注天气变化')}。")
        else:
            tips.append("当前整体天气友好，可以安排室内外结合的丰富行程。")
        
        indoor_priority = any(rec.get("indoor_priority") for rec in recommendations)
        if indoor_priority:
            tips.append("为确保体验舒适，建议准备至少一条以室内体验为主的备用路线。")
        
        missing_poi = [rec for rec in recommendations if not rec.get("data_available")]
        if missing_poi:
            tips.append("部分地点暂无权威POI数据，可考虑自行补充当地热门场所。")
        
        return tips
    
    def _format_analysis_for_prompt(self, analysis: Dict[str, Any]) -> str:
        """将综合分析结果转为文本"""
        if not analysis:
            return "暂无综合分析结果，请提醒补充实时数据。"
        
        lines: List[str] = []
        for rec in analysis.get("locations", []):
            weather = rec.get("weather", {})
            location_name = rec.get("location", "上海")
            lines.append(
                f"- {location_name}：天气 {weather.get('summary', '未知')}，温度 {weather.get('temperature', '未知')}，"
                f"户外适宜：{'是' if weather.get('suitable_for_outdoor') else '否'}。建议：{weather.get('advice', '')}"
            )
            top_pois = rec.get("top_pois", [])
            if top_pois:
                for poi in top_pois[:3]:
                    reason_text = "；".join(poi.get("reasons", [])) if poi.get("reasons") else "综合表现较好"
                    lines.append(
                        f"    · {poi.get('name')}（{poi.get('category') or '未分类'}，综合评分 {poi.get('score')}）—{reason_text}"
                    )
            else:
                lines.append("    · 暂无合适的POI，建议补充相关地点数据。")
        
        overall_tips = analysis.get("overall_tips")
        if overall_tips:
            lines.append("整体提示：" + "；".join(overall_tips))
        
        return "\n".join(lines)
    
    def _generate_final_decision(self, user_input: str, thoughts: List[ThoughtProcess], 
                                extracted_info: Dict[str, Any], real_time_data: Dict[str, Any],
                                context: UserContext) -> str:
        """生成最终决策 - 强调人文因素"""
        system_prompt = """你是一个充满人情味、专业又温暖的上海本地旅游规划师。你不仅懂旅游，更懂人心。

🌟 你的性格特质：
1. **温暖体贴**：像朋友一样真诚，用心感受用户的每一个需求和期待
2. **专业可靠**：基于实时数据（天气、路况、人流、POI）制定科学合理的行程
3. **细腻周到**：注意到用户没说出口的需求，提供超出预期的贴心建议
4. **有生活气息**：分享本地人才知道的小tips，让旅行更地道
5. **情感共鸣**：理解旅行背后的意义（浪漫、温馨、放松、探索等）

💝 回复风格要求：
1. **开头先共情**：理解并表达对用户情感需求的认同
   - 例："和女朋友一起的旅行，确实需要更多浪漫和惊喜呢～"
   - 例："带父母出行最重要的是让他们舒适省心，我特别理解"
   
2. **用词温暖自然**：
   - 多用"您"、"咱们"、"我建议"
   - 避免生硬的"应该"、"必须"
   - 用"～"、"呢"、"哦"等语气词增加亲和力
   
3. **加入情感细节**：
   - 推荐景点时说明"为什么适合你们"
   - 分享小故事或本地人的秘密
   - 给出温馨提示时解释背后的原因
   
4. **体现专业温度**：
   - 基于数据，但用人话表达
   - 例：不说"人流密度中等"，而说"这时候人不算多，逛起来会比较舒服"

🎯 核心原则：
1. **首先理解情感需求**：
   - 情侣：浪漫、惊喜、拍照、私密空间
   - 家人：便捷、舒适、安全、适合所有年龄
   - 朋友：有趣、新潮、热闹、拍照打卡
   
2. **严格尊重用户偏好**：
   - "避开人群"→推荐小众安静的地方
   - "想要浪漫"→避开过于商业的景点
   - "地道体验"→推荐本地人常去的地方
   
3. **预算敏感度**：
   - 经济型：强调性价比，推荐免费景点和平价美食
   - 高端型：推荐特色体验和品质餐厅
   
4. **真诚实用**：
   - 基于实时数据，不编造信息
   - 给出具体的时间、地址、价格
   - 分享实用的避坑tips

5. **必须反馈的要点**：
   - 无论用户是否提及，都要明确说明天气状况（含温度、对户外活动的影响）
   - 无论用户是否提及，都要提供至少3个核心POI或体验的推荐理由
   - 若实时数据缺失，需诚实告知并给出替代建议

📝 回复结构建议：
1. **温暖的开场**（共情+理解需求）
2. **我的思考**（简要说明规划逻辑）
3. **详细行程**（具体安排+理由）
4. **贴心提示**（实用建议+温馨关怀）
5. **真诚祝福**（期待他们玩得开心）

请用充满人情味的方式，生成让用户感到被理解、被关心的旅游攻略。记住：你不是冰冷的AI，而是一个热爱上海、懂得生活的本地朋友。"""
        
        # 构建思考过程摘要
        thoughts_summary = "\n".join([
            f"步骤{t.step}: {t.thought} - {t.reasoning}"
            for t in thoughts
        ])
        
        # 转换数据为可序列化格式
        recommendation_analysis = self._build_environmental_recommendations(extracted_info, real_time_data, context)
        real_time_data["analysis"] = recommendation_analysis
        
        serializable_data = self._convert_to_serializable(real_time_data)
        
        # 构建人文信息摘要
        human_factors = []
        
        if extracted_info.get('user_intent_summary'):
            human_factors.append(f"需求理解：{extracted_info['user_intent_summary']}")
        
        if extracted_info.get('companions') and extracted_info['companions']['type']:
            companion_desc = self._format_companions(extracted_info['companions'])
            human_factors.append(f"同伴：{companion_desc}")
            
            # 根据同伴类型添加特殊提示
            companion_type = extracted_info['companions']['type']
            if companion_type == 'romantic_partner':
                human_factors.append("💝 特别注意：这是一次浪漫之旅，请推荐适合情侣的浪漫景点和餐厅")
            elif companion_type == 'family':
                human_factors.append("👨‍👩‍👧‍👦 特别注意：这是家庭出游，请考虑便捷性和全家人都适合的活动")
            elif companion_type == 'friends':
                human_factors.append("👫 特别注意：这是朋友聚会，可以推荐有趣、热闹的地方")
        
        if extracted_info.get('emotional_context'):
            emotional_desc = self._format_emotional_context(extracted_info['emotional_context'])
            if emotional_desc:
                human_factors.append(f"情感需求：{emotional_desc}")
        
        if extracted_info.get('budget_info') and extracted_info['budget_info']['amount']:
            budget_desc = self._format_budget(extracted_info['budget_info'])
            human_factors.append(f"预算：{budget_desc}")
        
        if extracted_info.get('preferences'):
            pref_desc = self._format_preferences(extracted_info['preferences'])
            human_factors.append(f"特殊偏好：{pref_desc}")
        
        human_factors_text = "\n- ".join(human_factors) if human_factors else "无特殊要求"
        
        user_message = f"""用户需求：{user_input}

我的思考过程：
{thoughts_summary}

【重要】人文因素分析（请特别关注）：
- {human_factors_text}

基础信息：
- 旅行天数：{extracted_info['travel_days']}天
- 地点：{', '.join(extracted_info['locations']) if extracted_info['locations'] else '未指定'}
- 活动类型：{', '.join(extracted_info['activity_types']) if extracted_info['activity_types'] else '未指定'}

实时数据：
{json.dumps(serializable_data, ensure_ascii=False, indent=2)}

请基于以上信息，生成优化的旅游攻略。

特别提醒：
1. 必须在攻略中体现对同伴关系的关注（如：女朋友、父母等）
2. 必须根据情感需求调整推荐（如：浪漫氛围、避开人群等）
3. 必须考虑预算档次来推荐合适的消费场所
4. 在攻略开头简要说明你的思考逻辑和对用户需求的理解"""
        
        if recommendation_analysis:
            analysis_text = self._format_analysis_for_prompt(recommendation_analysis)
            user_message += f"\n附加分析：\n{analysis_text}\n"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        return self.doubao_agent.generate_response(messages)
    
    # ==================== 原有方法（保留向后兼容） ====================
    
    def _generate_initial_response(self, user_input: str, context: UserContext) -> str:
        """让豆包Agent生成初始回复，理解用户需求"""
        print("🤖 Agent正在理解您的需求...")
        
        system_prompt = """你是一个专业的上海旅游规划师。请理解用户的需求并生成初步的旅游建议。

要求：
1. 只推荐上海地区的景点和地点
2. 不要推荐北京、广州等其他城市的景点
3. 根据用户的具体需求给出建议
4. 如果用户提到特定区域（如普陀区），请推荐该区域及周边的景点

请生成简洁的初步建议，后续会根据实时数据优化。"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
        
        return self.doubao_agent.generate_response(messages)
    
    def _analyze_agent_response_for_mcp(self, agent_response: str, user_input: str) -> List[MCPServiceType]:
        """根据Agent的回复分析需要哪些MCP服务"""
        required_services = []
        
        # 对于旅游攻略，默认需要所有核心MCP服务
        required_services = [
            MCPServiceType.WEATHER,    # 天气信息
            MCPServiceType.POI,        # 景点和餐厅信息
            MCPServiceType.TRAFFIC,    # 路况信息
            MCPServiceType.NAVIGATION, # 导航路线
            MCPServiceType.CROWD       # 人流信息
        ]
        
        # 根据用户具体需求调整
        if "天气" not in user_input and "下雨" not in user_input and "晴天" not in user_input:
            # 如果用户没有明确询问天气，但需要做攻略，仍然需要天气信息
            pass  # 保留天气服务
        
        if "交通" not in user_input and "路线" not in user_input:
            # 如果用户没有明确询问交通，但需要做攻略，仍然需要导航信息
            pass  # 保留导航服务
        
        return required_services
    
    def _call_targeted_mcp_services(self, required_services: List[MCPServiceType], user_input: str, context: UserContext) -> Dict[str, Any]:
        """调用目标MCP服务"""
        print("📡 Agent正在收集实时数据来优化您的攻略...")
        real_time_data = {}
        
        # 从用户输入中提取具体地点和路线信息
        extracted_locations = self._extract_locations_from_input(user_input)
        route_info = self._extract_route_from_input(user_input)
        
        # 按正确顺序调用MCP服务
        for service in required_services:
            try:
                if service == MCPServiceType.WEATHER:
                    # logger.info("🌤️ 调用天气服务")
                    weather_data = {}
                    if extracted_locations:
                        for location in extracted_locations:
                            weather = self.get_weather(location, context.travel_preferences.start_date)
                            weather_data[location] = weather
                    else:
                        weather = self.get_weather("上海", context.travel_preferences.start_date)
                        weather_data["上海"] = weather
                    real_time_data["weather"] = weather_data
                
                elif service == MCPServiceType.POI:
                    # logger.info("🔍 调用POI服务")
                    poi_data = {}
                    try:
                        if extracted_locations:
                            for location in extracted_locations:
                                # 确保搜索的是上海地区的POI
                                attractions = self.search_poi("景点", location, "110000")
                                poi_data[f"{location}_景点"] = attractions
                                
                                restaurants = self.search_poi("餐厅", location, "050000")
                                poi_data[f"{location}_餐饮"] = restaurants
                        else:
                            # 搜索上海的主要景点
                            attractions = self.search_poi("景点", "上海", "110000")
                            poi_data["上海景点"] = attractions
                            
                            restaurants = self.search_poi("餐厅", "上海", "050000")
                            poi_data["上海餐饮"] = restaurants
                    except Exception as e:
                        logger.error(f"POI服务调用失败: {e}")
                        # 返回模拟POI数据
                        poi_data = {
                            "上海景点": [
                                {"name": "外滩", "address": "黄浦区中山东一路", "rating": 4.5},
                                {"name": "豫园", "address": "黄浦区安仁街132号", "rating": 4.3},
                                {"name": "南京路步行街", "address": "黄浦区南京东路", "rating": 4.2}
                            ],
                            "上海餐饮": [
                                {"name": "老正兴菜馆", "address": "黄浦区南京东路", "rating": 4.4},
                                {"name": "绿波廊", "address": "黄浦区豫园路", "rating": 4.3}
                            ]
                        }
                    real_time_data["poi"] = poi_data
                
                elif service == MCPServiceType.NAVIGATION:
                    # logger.info("🗺️ 调用导航服务")
                    navigation_data = {}
                    
                    # 优先使用从用户输入中提取的路线信息
                    if route_info:
                        start = route_info["start"]
                        end = route_info["end"]
                        routes = self.get_navigation_routes(start, end)
                        navigation_data[f"{start}_to_{end}"] = routes
                        # 保存路线信息供路况服务使用
                        real_time_data["_route_info"] = route_info
                    elif len(extracted_locations) >= 2:
                        for i in range(len(extracted_locations) - 1):
                            start = extracted_locations[i]
                            end = extracted_locations[i + 1]
                            routes = self.get_navigation_routes(start, end)
                            navigation_data[f"{start}_to_{end}"] = routes
                    else:
                        # 如果没有明确的路线，尝试从用户输入中推断
                        inferred_route = self._infer_route_from_input(user_input)
                        if inferred_route:
                            routes = self.get_navigation_routes(inferred_route["start"], inferred_route["end"])
                            navigation_data[f"{inferred_route['start']}_to_{inferred_route['end']}"] = routes
                            real_time_data["_route_info"] = inferred_route
                        else:
                            # 默认路线
                            routes = self.get_navigation_routes("人民广场", "外滩")
                            navigation_data["人民广场_to_外滩"] = routes
                    
                    real_time_data["navigation"] = navigation_data
                
                elif service == MCPServiceType.TRAFFIC:
                    # logger.info("🚦 调用路况服务")
                    traffic_data = {}
                    
                    # 路况服务应该在导航之后调用，针对具体路线
                    if "_route_info" in real_time_data:
                        route_info = real_time_data["_route_info"]
                        # 获取路线上的主要路段路况
                        start = route_info["start"]
                        end = route_info["end"]
                        traffic_start = self.get_traffic_status(start)
                        traffic_end = self.get_traffic_status(end)
                        traffic_data[f"{start}_to_{end}"] = {
                            "start_location": traffic_start,
                            "end_location": traffic_end
                        }
                    elif extracted_locations:
                        for location in extracted_locations:
                            traffic = self.get_traffic_status(location)
                            traffic_data[location] = traffic
                    else:
                        traffic = self.get_traffic_status("上海")
                        traffic_data["上海"] = traffic
                    
                    real_time_data["traffic"] = traffic_data
                
                elif service == MCPServiceType.CROWD:
                    # logger.info("👥 调用人流服务")
                    crowd_data = {}
                    if extracted_locations:
                        for location in extracted_locations:
                            crowd_data[location] = {
                                "level": "moderate",
                                "description": "人流适中",
                                "recommendation": "适合游览"
                            }
                    else:
                        crowd_data["上海"] = {
                            "level": "moderate",
                            "description": "人流适中",
                            "recommendation": "适合游览"
                        }
                    real_time_data["crowd"] = crowd_data
                
            except Exception as e:
                logger.error(f"MCP服务 {service.value} 调用失败: {e}")
                real_time_data[service.value] = {"error": str(e)}
        
        return real_time_data
    
    def _optimize_response_with_data(self, user_input: str, initial_response: str, real_time_data: Dict[str, Any], context: UserContext) -> str:
        """使用实时数据优化Agent的回复"""
        print("🤖 Agent正在思考并优化您的旅游攻略...")
        
        system_prompt = """你是一个专业、温暖、贴心的上海旅游规划师。请基于用户的初始需求和实时数据，生成科学、详细、富有人情味的旅游攻略。

你的特点：
1. 专业：基于实时数据（天气、路况、人流、POI）制定科学合理的行程
2. 贴心：考虑用户的具体需求（如不喜欢人多、想要浪漫氛围等）
3. 详细：提供具体的地址、交通方式、时间安排、费用预算
4. 人性化：用温暖的语言，给出实用的建议和温馨提示

重要要求：
1. 严格基于提供的实时数据生成回复，不要编造信息
2. 只推荐上海地区的景点和地点
3. 根据实时天气调整室内外活动安排
4. 根据路况信息优化交通路线
5. 根据人流信息推荐最佳游览时间
6. 提供具体的地址、交通方式、费用预算
7. 给出贴心的温馨提示和注意事项
8. 请务必在回复中明确说明天气状况（含温度及其对行程的影响）以及核心POI推荐理由；若数据缺失，需要如实告知并提供备选建议

请生成详细、实用、富有人情味的旅游攻略。"""
        
        # 将POIInfo对象转换为可序列化的字典
        serializable_data = self._convert_to_serializable(real_time_data)
        
        user_message = f"""用户需求：{user_input}

初始建议：{initial_response}

实时数据：
{json.dumps(serializable_data, ensure_ascii=False, indent=2)}

请基于以上信息，生成优化的旅游攻略。"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        return self.doubao_agent.generate_response(messages)
    
    def _convert_to_serializable(self, data: Any) -> Any:
        """将数据转换为可JSON序列化的格式"""
        if isinstance(data, dict):
            return {key: self._convert_to_serializable(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._convert_to_serializable(item) for item in data]
        elif hasattr(data, '__dict__'):
            # 处理POIInfo等自定义对象
            if hasattr(data, 'name'):
                # POIInfo对象
                return {
                    "name": data.name,
                    "address": data.address,
                    "rating": data.rating,
                    "business_hours": data.business_hours,
                    "price": data.price,
                    "distance": data.distance,
                    "category": data.category,
                    "reviews": data.reviews
                }
            elif hasattr(data, 'weather'):
                # WeatherInfo对象
                return {
                    "date": data.date,
                    "weather": data.weather,
                    "temperature": data.temperature,
                    "wind": data.wind,
                    "humidity": data.humidity,
                    "precipitation": data.precipitation
                }
            else:
                return str(data)
        else:
            return data
    
    def _start_thinking_process(self, user_input: str, context: UserContext) -> List[ThoughtProcess]:
        """开始思考联想过程"""
        thoughts = []
        step = 1
        
        logger.info("🧠 开始深度思考联想过程...")
        
        # 第一步：深度理解用户需求
        detected_locations, activity_types = self._analyze_user_intent(user_input)
        travel_days = self._extract_travel_days(user_input)
        
        thought1 = ThoughtProcess(
            step=step,
            thought="深度理解用户的核心需求",
            keywords=self._extract_keywords(user_input) + [f"{travel_days}天"],
            mcp_services=[],
            reasoning=f"用户需要{travel_days}天的上海旅游攻略，需要全面考虑时间安排、景点分布、交通规划等",
            timestamp=datetime.now().isoformat()
        )
        thoughts.append(thought1)
        step += 1
        
        # 第二步：智能景点推荐策略
        if not detected_locations:
            thought2 = ThoughtProcess(
                step=step,
                thought="智能推荐上海经典景点",
                keywords=["上海经典景点", "三日游"],
                mcp_services=[MCPServiceType.POI],
                reasoning=f"用户需要{travel_days}天攻略但未指定地点，需要推荐上海经典景点组合",
                timestamp=datetime.now().isoformat()
            )
            thoughts.append(thought2)
            step += 1
        else:
            thought2 = ThoughtProcess(
                step=step,
                thought="分析指定景点的周边推荐",
                keywords=detected_locations + activity_types,
                mcp_services=[MCPServiceType.POI],
                reasoning=f"用户指定了{detected_locations}，需要推荐周边相关景点",
                timestamp=datetime.now().isoformat()
            )
            thoughts.append(thought2)
            step += 1
        
        # 第三步：多日天气规划
        if travel_days > 1:
            thought3 = ThoughtProcess(
                step=step,
                thought="多日天气规划策略",
                keywords=["多日天气", "行程调整"],
                mcp_services=[MCPServiceType.WEATHER],
                reasoning=f"需要规划{travel_days}天的行程，必须考虑每天的天气情况来合理安排室内外活动",
                timestamp=datetime.now().isoformat()
            )
            thoughts.append(thought3)
            step += 1
        else:
            thought3 = ThoughtProcess(
                step=step,
                thought="单日天气检查",
                keywords=["天气", "温度", "降水"],
                mcp_services=[MCPServiceType.WEATHER],
                reasoning="单日行程需要检查天气状况以确保行程合理性",
                timestamp=datetime.now().isoformat()
            )
            thoughts.append(thought3)
            step += 1
        
        # 第四步：多日交通路线规划
        if travel_days > 1:
            thought4 = ThoughtProcess(
                step=step,
                thought="多日交通路线规划",
                keywords=["多日路线", "交通规划"],
                mcp_services=[MCPServiceType.NAVIGATION],
                reasoning=f"需要规划{travel_days}天的交通路线，考虑景点间的距离和交通方式",
                timestamp=datetime.now().isoformat()
            )
            thoughts.append(thought4)
            step += 1
        else:
            thought4 = ThoughtProcess(
                step=step,
                thought="单日交通路线规划",
                keywords=["路线", "交通", "导航"],
                mcp_services=[MCPServiceType.NAVIGATION],
                reasoning="需要规划单日最优交通路线",
                timestamp=datetime.now().isoformat()
            )
            thoughts.append(thought4)
            step += 1
        
        # 第五步：路况和交通优化
        thought5 = ThoughtProcess(
            step=step,
            thought="路况分析和交通优化",
            keywords=["路况", "拥堵", "交通"],
            mcp_services=[MCPServiceType.TRAFFIC],
            reasoning="需要检查实时路况，为交通规划提供优化建议",
            timestamp=datetime.now().isoformat()
        )
        thoughts.append(thought5)
        step += 1
        
        # 第六步：人流分析和时间优化
        thought6 = ThoughtProcess(
            step=step,
            thought="人流分析和时间优化",
            keywords=["人流", "拥挤", "排队", "时间优化"],
            mcp_services=[MCPServiceType.CROWD],
            reasoning="需要分析各景点的人流情况，合理安排游览时间，避开高峰期",
            timestamp=datetime.now().isoformat()
        )
        thoughts.append(thought6)
        step += 1
        
        # 第七步：综合评估和多日规划
        thought7 = ThoughtProcess(
            step=step,
            thought="综合评估和多日旅游规划",
            keywords=["综合评估", "多日规划", "个性化推荐"],
            mcp_services=[MCPServiceType.WEATHER, MCPServiceType.NAVIGATION, MCPServiceType.TRAFFIC, MCPServiceType.POI, MCPServiceType.CROWD],
            reasoning=f"整合所有信息，生成{travel_days}天的科学合理旅游攻略，包含每日安排、交通建议、天气应对等",
            timestamp=datetime.now().isoformat()
        )
        thoughts.append(thought7)
        
        logger.info(f"🧠 深度思考过程完成，共 {len(thoughts)} 个步骤")
        
        return thoughts
    
    def _collect_real_time_data(self, thoughts: List[ThoughtProcess], user_input: str, context: UserContext) -> Dict[str, Any]:
        """收集实时数据"""
        logger.info("📡 收集实时数据...")
        
        # 收集需要调用的MCP服务
        required_services = set()
        for thought in thoughts:
            required_services.update(thought.mcp_services)
        
        # 执行MCP服务调用
        real_time_data = {}
        
        # 提取目的地和起点
        detected_locations, _ = self._analyze_user_intent(user_input)
        travel_days = self._extract_travel_days(user_input)
        
        # 从用户输入中提取具体地点
        extracted_locations = self._extract_locations_from_input(user_input)
        if extracted_locations:
            destinations = extracted_locations
        else:
            destinations = detected_locations if detected_locations else ["外滩"]  # 默认目的地
        
        origin = "人民广场"  # 默认起点
        
        for service in required_services:
            try:
                if service == MCPServiceType.WEATHER:
                    logger.info("🌤️ 调用天气服务")
                    weather_data = {}
                    for dest in destinations:
                        weather_info = self.get_weather(dest, context.travel_preferences.start_date)
                        weather_data[dest] = weather_info
                    real_time_data["weather"] = weather_data
                
                elif service == MCPServiceType.NAVIGATION:
                    logger.info("🗺️ 调用导航服务")
                    if len(destinations) > 1:
                        nav_results = []
                        for i in range(len(destinations) - 1):
                            route = self.get_navigation_routes(destinations[i], destinations[i+1])
                            nav_results.append(route)
                        real_time_data["navigation"] = nav_results
                    else:
                        route = self.get_navigation_routes(origin, destinations[0])
                        real_time_data["navigation"] = [route]
                
                elif service == MCPServiceType.TRAFFIC:
                    logger.info("🚦 调用路况服务")
                    traffic_data = {}
                    
                    # 根据用户输入判断是否需要调用路况服务
                    if "交通" in user_input or "路况" in user_input or "堵车" in user_input:
                        for dest in destinations:
                            logger.info(f"调用路况API获取实时数据: {dest}")
                            traffic_info = self.get_traffic_status(dest)
                            traffic_data[dest] = traffic_info
                    else:
                        # 如果用户没有明确询问交通，只获取主要目的地的路况
                        if destinations:
                            main_dest = destinations[0]
                            logger.info(f"调用路况API获取实时数据: {main_dest}")
                            traffic_info = self.get_traffic_status(main_dest)
                            traffic_data[main_dest] = traffic_info
                    
                    real_time_data["traffic"] = traffic_data
                
                elif service == MCPServiceType.POI:
                    logger.info("🔍 调用POI服务")
                    poi_data = {}
                    
                    # 简化POI搜索逻辑，让豆包Agent来决定如何使用这些数据
                    if not destinations:
                        # 搜索上海的主要景点和商圈
                        attractions = self.search_poi("景点", "上海", "110000")
                        poi_data["上海景点"] = attractions
                        
                        restaurants = self.search_poi("餐厅", "上海", "050000")
                        poi_data["上海餐饮"] = restaurants
                        
                        shopping_areas = self.search_poi("商圈", "上海", "060000")
                        poi_data["上海商圈"] = shopping_areas
                    else:
                        for dest in destinations:
                            attractions = self.search_poi("景点", dest, "110000")
                            poi_data[f"{dest}_景点"] = attractions
                            
                            restaurants = self.search_poi("餐厅", dest, "050000")
                            poi_data[f"{dest}_餐饮"] = restaurants
                    
                    real_time_data["poi"] = poi_data
                
                elif service == MCPServiceType.CROWD:
                    logger.info("👥 调用人流服务")
                    crowd_data = {}
                    for dest in destinations:
                        crowd_data[dest] = {
                            "level": "moderate",
                            "description": "人流适中",
                            "recommendation": "适合游览"
                        }
                    real_time_data["crowd"] = crowd_data
                
            except Exception as e:
                logger.error(f"MCP服务 {service.value} 调用失败: {e}")
                real_time_data[service.value] = {"error": str(e)}
        
        return real_time_data
    
    def _generate_response_with_doubao(self, user_input: str, real_time_data: Dict[str, Any], context: UserContext) -> str:
        """使用豆包Agent生成回复"""
        logger.info("🤖 使用豆包Agent生成回复...")
        
        # 构建系统提示词
        system_prompt = self._build_system_prompt(real_time_data, context)
        
        # 构建用户消息
        user_message = self._build_user_message(user_input, real_time_data)
        
        # 调用豆包Agent
        messages = [
            {"role": "user", "content": user_message}
        ]
        
        response = self.doubao_agent.generate_response(messages, system_prompt)
        
        return response
    
    def _build_system_prompt(self, real_time_data: Dict[str, Any], context: UserContext) -> str:
        """构建系统提示词"""
        prompt = """你是一个专业的上海旅游攻略规划师，具备以下能力：
1. 深度理解用户需求，提供个性化的旅游建议
2. 基于实时数据（天气、交通、人流、POI）制定科学合理的行程
3. 考虑多日游的时间安排和景点分布
4. 提供实用的交通建议和注意事项

重要要求：
- 严格基于提供的实时数据生成回复
- 只推荐上海地区的景点和地点，不要推荐北京、广州等其他城市的景点
- 如果用户询问特定地点的交通情况，请重点回答该地点的路况信息
- 所有推荐的地点必须是上海地区的
- 必须使用提供的实时数据，不要编造信息
- 无论用户是否提及，都要明确说明天气状况（含温度及对行程的影响）和核心POI推荐理由
- 若缺少相关数据，需要坦诚告知并提供替代建议

请根据提供的实时数据，为用户生成详细、实用的旅游攻略。"""
        
        return prompt
    
    def _build_user_message(self, user_input: str, real_time_data: Dict[str, Any]) -> str:
        """构建用户消息"""
        message = f"用户需求：{user_input}\n\n"
        
        # 添加实时数据
        if real_time_data:
            message += "实时数据：\n"
            
            if "weather" in real_time_data:
                weather_info = real_time_data["weather"]
                message += "🌤️ 天气信息：\n"
                for location, weather in weather_info.items():
                    if weather and len(weather) > 0:
                        weather_data = weather[0] if isinstance(weather, list) else weather
                        message += f"  {location}：{weather_data.weather}，{weather_data.temperature}\n"
                    else:
                        message += f"  {location}：暂无实时天气数据\n"
            else:
                message += "🌤️ 天气信息：暂无实时数据，请提醒用户关注临近天气预报。\n"
            
            if "poi" in real_time_data:
                poi_info = real_time_data["poi"]
                message += "🎯 景点信息：\n"
                for category, pois in poi_info.items():
                    if pois and len(pois) > 0:
                        message += f"  {category}：\n"
                        for poi in pois[:3]:
                            poi_name = getattr(poi, "name", None)
                            poi_rating = getattr(poi, "rating", None)
                            if poi_name is None and isinstance(poi, dict):
                                poi_name = poi.get("name")
                            if poi_rating is None and isinstance(poi, dict):
                                poi_rating = poi.get("rating")
                            if poi_name and len(poi_name) > 2:
                                rating_text = f"{poi_rating}星" if poi_rating not in (None, "") else "暂无评分"
                                message += f"    - {poi_name}（评分：{rating_text}）\n"
                    else:
                        message += f"  {category}：暂无符合条件的POI数据\n"
            else:
                message += "🎯 景点信息：暂无实时数据，可结合历史热门景点作为备选。\n"
            
            if "traffic" in real_time_data:
                traffic_info = real_time_data["traffic"]
                message += "🚦 交通信息：\n"
                for location, traffic in traffic_info.items():
                    if traffic and "status" in traffic:
                        message += f"  {location}：{traffic['status']}\n"
            
            if "crowd" in real_time_data:
                crowd_info = real_time_data["crowd"]
                message += "👥 人流信息：\n"
                for location, crowd in crowd_info.items():
                    if crowd and "description" in crowd:
                        message += f"  {location}：{crowd['description']}\n"
            
            if "analysis" in real_time_data:
                analysis_text = self._format_analysis_for_prompt(real_time_data["analysis"])
                message += "📊 综合推荐分析：\n"
                message += f"{analysis_text}\n"
        
        message += "\n请基于以上信息，为用户生成详细的旅游攻略。"
        
        return message
    
    def _extract_keywords(self, text: str) -> List[str]:
        """增强版关键词提取 - 更全面和精准"""
        keywords = []
        
        # 1. 提取地点关键词（包括变体）
        location_variants = {
            "华师大": ["华东师范大学", "华师大", "华东师大"],
            "迪士尼": ["迪士尼", "迪斯尼", "上海迪士尼", "迪士尼乐园"],
            "外滩": ["外滩", "黄浦江", "万国建筑"],
            "南京路": ["南京路", "南京东路", "南京西路", "步行街"],
            "豫园": ["豫园", "城隍庙", "老城厢"],
            "陆家嘴": ["陆家嘴", "东方明珠", "金融区", "上海中心"],
            "新天地": ["新天地", "石库门", "太平桥"],
            "田子坊": ["田子坊", "泰康路", "艺术街"],
            "徐家汇": ["徐家汇", "港汇", "太平洋百货"],
            "静安寺": ["静安寺", "久光", "嘉里中心"],
            "人民广场": ["人民广场", "人民公园", "上海博物馆"],
            "中山公园": ["中山公园", "龙之梦"],
            "五角场": ["五角场", "大学路", "合生汇"]
        }
        
        for main_location, variants in location_variants.items():
            if any(variant in text for variant in variants):
                keywords.append(main_location)
        
        # 2. 提取具体景点和建筑
        specific_places = [
            "东方明珠", "上海中心", "金茂大厦", "环球金融中心", "上海博物馆", 
            "上海科技馆", "上海海洋水族馆", "上海野生动物园", "朱家角", "七宝古镇",
            "思南公馆", "武康路", "多伦路", "1933老场坊", "M50创意园"
        ]
        for place in specific_places:
            if place in text:
                keywords.append(place)
        
        # 3. 提取活动类型关键词（更细致）
        activity_mapping = {
            "购物": ["逛街", "买", "商场", "百货", "奥特莱斯", "专卖店", "购物", "血拼"],
            "美食": ["吃", "餐厅", "小吃", "美食", "菜", "料理", "火锅", "烧烤", "本帮菜", "小笼包"],
            "文化": ["博物馆", "展览", "历史", "文化", "古迹", "艺术", "风情", "传统", "石库门"],
            "娱乐": ["游乐", "娱乐", "KTV", "电影", "酒吧", "夜生活", "迪士尼", "游戏"],
            "自然": ["公园", "花园", "湖", "江", "山", "海", "自然", "绿地", "植物园"],
            "商务": ["会议", "商务", "办公", "工作", "送", "接"],
            "亲子": ["孩子", "儿童", "亲子", "家庭", "带娃", "女儿", "儿子"],
            "休闲": ["散步", "休息", "放松", "慢", "悠闲", "清净", "安静"],
            "观光": ["观光", "游览", "参观", "看", "拍照", "打卡", "风景"]
        }
        
        for activity, activity_keywords in activity_mapping.items():
            if any(keyword in text for keyword in activity_keywords):
                keywords.append(activity)
        
        # 4. 提取人员关系关键词
        people_keywords = ["女朋友", "男朋友", "老婆", "老公", "妻子", "丈夫", "父母", "爸妈", 
                          "孩子", "女儿", "儿子", "家人", "朋友", "同事", "一家", "全家"]
        for people in people_keywords:
            if people in text:
                keywords.append(people)
        
        # 5. 提取时间关键词（更详细）
        time_patterns = ["明天", "后天", "今天", "周末", "工作日", "早上", "上午", "下午", "晚上", "夜里",
                        "第一天", "第二天", "第三天", "第四天", "第五天", "几天", "多天"]
        for time_word in time_patterns:
            if time_word in text:
                keywords.append(time_word)
        
        # 6. 提取偏好和限制关键词
        preference_keywords = {
            "避开人群": ["人少", "不想人多", "避开人群", "清净", "安静"],
            "不想远": ["不想远", "近一点", "附近", "不要太远"],
            "排队": ["排队", "等待", "人多", "拥挤"],
            "交通": ["开车", "自驾", "地铁", "公交", "打车", "走路", "骑车", "不开车"],
            "预算": ["便宜", "经济", "省钱", "贵", "高端", "奢华", "预算"],
            "天气": ["天气", "下雨", "晴天", "阴天", "温度", "冷", "热", "风", "雪"]
        }
        
        for pref_type, pref_words in preference_keywords.items():
            if any(word in text for word in pref_words):
                keywords.append(pref_type)
        
        # 7. 使用正则表达式提取数字+天
        import re
        day_matches = re.findall(r'(\d+)天', text)
        for day_match in day_matches:
            keywords.append(f"{day_match}天")
        
        # 8. 提取特殊需求关键词
        special_needs = ["浪漫", "温馨", "刺激", "新鲜", "特色", "地道", "网红", "小众", "经典"]
        for need in special_needs:
            if need in text:
                keywords.append(need)
        
        # 去重并返回
        return list(set(keywords))
    
    def _prioritize_keywords_for_inputtips(self, keywords: List[str], user_input: str) -> List[str]:
        """为输入提示API智能排序关键词优先级"""
        
        # 定义优先级权重
        priority_scores = {}
        
        for keyword in keywords:
            score = 0
            
            # 1. 地点类关键词优先级最高
            location_keywords = ["华师大", "迪士尼", "外滩", "南京路", "豫园", "陆家嘴", 
                               "新天地", "田子坊", "徐家汇", "静安寺", "人民广场"]
            if keyword in location_keywords:
                score += 100
            
            # 2. 具体景点建筑优先级很高
            specific_places = ["东方明珠", "上海中心", "金茂大厦", "环球金融中心", "上海博物馆", 
                              "上海科技馆", "朱家角", "七宝古镇", "思南公馆", "武康路"]
            if keyword in specific_places:
                score += 90
            
            # 3. 在用户输入中出现位置越靠前，优先级越高
            if keyword in user_input:
                position = user_input.find(keyword)
                score += max(50 - position // 10, 10)  # 位置越靠前分数越高
            
            # 4. 关键词长度适中的优先级较高（2-6个字符）
            if 2 <= len(keyword) <= 6:
                score += 20
            elif len(keyword) > 6:
                score -= 10  # 太长的关键词可能不是地点
            
            # 5. 排除一些通用词汇
            exclude_words = ["天气", "交通", "景点", "餐厅", "上海", "旅游", "攻略", "购物", 
                           "美食", "文化", "娱乐", "自然", "商务", "亲子", "休闲", "观光"]
            if keyword in exclude_words:
                score -= 50
            
            # 6. 数字+天 的关键词不适合输入提示
            if keyword.endswith("天") and any(c.isdigit() for c in keyword):
                score -= 30
            
            # 7. 人员关系词不适合输入提示
            people_words = ["女朋友", "老婆", "妻子", "父母", "女儿", "儿子", "家人", "朋友"]
            if keyword in people_words:
                score -= 40
            
            # 8. 偏好词汇不适合输入提示
            preference_words = ["避开人群", "不想远", "排队", "预算", "浪漫", "温馨"]
            if keyword in preference_words:
                score -= 35
            
            priority_scores[keyword] = score
        
        # 按分数排序，只返回分数大于0的关键词
        sorted_keywords = sorted(
            [(k, v) for k, v in priority_scores.items() if v > 0], 
            key=lambda x: x[1], 
            reverse=True
        )
        
        result = [k for k, v in sorted_keywords]
        logger.info(f"关键词优先级排序结果: {[(k, priority_scores[k]) for k in result[:10]]}")
        
        return result
    
    def _extract_travel_days(self, text: str) -> int:
        """提取旅行天数"""
        import re
        
        # 匹配数字+天/日
        day_patterns = [
            r'(\d+)\s*天',
            r'(\d+)\s*日',
            r'(\d+)\s*天游',
            r'(\d+)\s*日游'
        ]
        
        for pattern in day_patterns:
            match = re.search(pattern, text)
            if match:
                days = int(match.group(1))
                return max(1, min(days, 7))  # 限制在1-7天
        
        # 如果没有明确指定，根据关键词推断
        if "三天" in text or "3天" in text:
            return 3
        elif "两天" in text or "2天" in text:
            return 2
        elif "一天" in text or "1天" in text:
            return 1
        elif "四天" in text or "4天" in text:
            return 4
        elif "五天" in text or "5天" in text:
            return 5
        elif "未来" in text and "天" in text:
            return 3  # 默认3天
        
        return 1  # 默认1天
    
    def _analyze_user_intent(self, user_input: str) -> Tuple[List[str], List[str]]:
        """分析用户意图"""
        detected_locations = []
        activity_types = []
        
        # 检测地点
        for location, attractions in self.location_keywords.items():
            if location in user_input:
                detected_locations.append(location)
        
        # 检测活动类型
        for activity, keywords in self.activity_keywords.items():
            if any(keyword in user_input for keyword in keywords):
                activity_types.append(activity)
        
        return detected_locations, activity_types
    
    def _extract_locations_from_input(self, user_input: str) -> List[str]:
        """从用户输入中提取地点信息"""
        locations = []
        
        # 上海地区关键词
        shanghai_areas = [
            "外滩", "人民广场", "南京路", "豫园", "陆家嘴", "东方明珠", 
            "上海迪士尼", "上海博物馆", "上海科技馆", "田子坊", "新天地",
            "金沙江路", "中山公园", "静安寺", "徐家汇", "五角场", "虹桥",
            "浦东", "浦西", "黄浦区", "静安区", "徐汇区", "长宁区", "普陀区",
            "华东师范大学", "华东师大", "华师大", "徐汇", "普陀"
        ]
        
        for area in shanghai_areas:
            if area in user_input:
                locations.append(area)
        
        return locations
    
    def _extract_route_from_input(self, user_input: str) -> Optional[Dict[str, str]]:
        """从用户输入中提取路线信息"""
        # 简单的路线提取逻辑
        if "从" in user_input and "到" in user_input:
            parts = user_input.split("从")[1].split("到")
            if len(parts) >= 2:
                start = parts[0].strip()
                end = parts[1].split()[0].strip()  # 取第一个词作为终点
                return {"start": start, "end": end}
        
        return None
    
    def _infer_route_from_input(self, user_input: str) -> Optional[Dict[str, str]]:
        """从用户输入中推断路线信息"""
        # 特殊处理：华东师范大学到徐汇区
        if "华东师范大学" in user_input and "徐汇区" in user_input:
            return {"start": "华东师范大学", "end": "徐汇区"}
        
        # 提取地点信息
        locations = self._extract_locations_from_input(user_input)
        
        # 如果找到多个地点，尝试推断起点和终点
        if len(locations) >= 2:
            # 根据用户输入中的关键词推断
            if "出发" in user_input:
                # 找到"出发"前面的地点作为起点
                for i, location in enumerate(locations):
                    if location in user_input[:user_input.find("出发")]:
                        start = location
                        # 其他地点作为终点
                        end = locations[(i + 1) % len(locations)]
                        return {"start": start, "end": end}
            
            # 如果没有"出发"关键词，使用第一个地点作为起点，最后一个作为终点
            return {"start": locations[0], "end": locations[-1]}
        
        return None
    

    
    # MCP服务方法（从smart_travel_agent.py移植）
    def _rate_limit_wait(self, api_name: str):
        """API限流控制 - 确保不超过QPS限制"""
        with self._api_lock:
            current_time = time.time()
            if api_name in self._last_api_call:
                elapsed = current_time - self._last_api_call[api_name]
                if elapsed < self._min_interval:
                    wait_time = self._min_interval - elapsed
                    logger.debug(f"限流等待 {wait_time:.2f}秒 for {api_name}")
                    time.sleep(wait_time)
            self._last_api_call[api_name] = time.time()
    
    def _make_request(self, url: str, params: Dict[str, Any], api_name: str = "default") -> Dict[str, Any]:
        """发送HTTP请求（带限流控制）"""
        try:
            # 限流控制
            self._rate_limit_wait(api_name)
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"API请求失败: {url}, 错误: {e}")
            return {}
    
    def get_weather(self, city: str, date: str) -> List[WeatherInfo]:
        """获取天气信息 - 直接调用API，无缓存"""
        logger.info(f"调用天气API获取实时数据: {city}")
        
        try:
            city_code = self._get_city_code(city)
            
            params = {
                "key": get_api_key("AMAP_WEATHER"),
                "city": city_code,
                "extensions": "all"
            }
            
            result = self._make_request(AMAP_CONFIG["weather_url"], params, "weather")
            
            if result.get("status") == "1":
                forecasts = result.get("forecasts", [])
                if forecasts:
                    weather_data = []
                    for forecast in forecasts[0].get("casts", []):
                        weather_info = WeatherInfo(
                            date=forecast.get("date", ""),
                            weather=forecast.get("dayweather", ""),
                            temperature=f"{forecast.get('nighttemp', '')}°C-{forecast.get('daytemp', '')}°C",
                            wind=forecast.get("daywind", ""),
                            humidity=forecast.get("daypower", ""),
                            precipitation=forecast.get("dayprecipitation", "")
                        )
                        weather_data.append(weather_info)
                    
                    logger.info(f"天气API调用成功: {city} - {len(weather_data)}条数据")
                    return weather_data
                else:
                    logger.warning(f"天气API返回空数据: {city}")
            else:
                logger.error(f"天气API调用失败: {result.get('info', '未知错误')}")
            
        except Exception as e:
            logger.error(f"获取天气信息失败: {e}")
        
        return []
    
    def get_navigation_routes(self, origin: str, destination: str, 
                            transport_mode: str = "driving") -> List[RouteInfo]:
        """获取导航路线 - 直接调用API，无缓存"""
        logger.info(f"调用导航API获取实时路线: {origin} -> {destination}")
        
        try:
            origin_coords = self._geocode(origin)
            dest_coords = self._geocode(destination)
            
            if not origin_coords or not dest_coords:
                logger.warning(f"无法获取坐标: {origin} 或 {destination}")
                return []
            
            # 根据交通方式选择不同的API端点和参数
            if transport_mode == "transit":
                # 公交路径规划 - v3版本
                params = {
                    "key": get_api_key("AMAP_NAVIGATION"),
                    "origin": origin_coords,
                    "destination": dest_coords,
                    "city": "上海",
                    "cityd": "上海",
                    "strategy": "0",  # 0:最快捷 1:最经济 2:最少换乘 3:最少步行
                    "extensions": "base"
                }
                url = "https://restapi.amap.com/v3/direction/transit/integrated"
            else:
                # 驾车路径规划 - v3版本
                params = {
                    "key": get_api_key("AMAP_NAVIGATION"),
                    "origin": origin_coords,
                    "destination": dest_coords,
                    "strategy": "10",  # 10:躲避拥堵，路程较短，时间最短（推荐）
                    "extensions": "base"
                }
                url = "https://restapi.amap.com/v3/direction/driving"
            
            result = self._make_request(url, params, "navigation")
            
            if result.get("status") == "1":
                routes = []
                route_data = result.get("route", {})
                
                if transport_mode == "transit":
                    transit_routes = route_data.get("transits", [])
                    for i, route in enumerate(transit_routes[:2]):
                        route_info = RouteInfo(
                            distance=route.get("distance", ""),
                            duration=route.get("duration", ""),
                            traffic_status="实时路况",
                            route_description=self._format_transit_route(route),
                            congestion_level="正常"
                        )
                        routes.append(route_info)
                else:
                    driving_routes = route_data.get("paths", [])
                    for i, route in enumerate(driving_routes[:2]):
                        route_info = RouteInfo(
                            distance=route.get("distance", ""),
                            duration=route.get("duration", ""),
                            traffic_status="实时路况",
                            route_description=self._format_driving_route(route),
                            congestion_level="正常"
                        )
                        routes.append(route_info)
                
                logger.info(f"导航API调用成功: {origin} -> {destination} - {len(routes)}条路线")
                return routes
            else:
                logger.error(f"导航API调用失败: {result.get('info', '未知错误')}")
                
        except Exception as e:
            logger.error(f"获取导航路线失败: {e}")
        
        return []
    
    def get_traffic_status(self, area: str) -> Dict[str, Any]:
        """获取路况信息 - 直接调用API，无缓存"""
        logger.info(f"调用路况API获取实时数据: {area}")
        
        try:
            # 对于区域名称，先转换为具体地点
            area_mapping = {
                "徐汇区": "徐家汇",
                "普陀区": "普陀区",
                "华东师范大学": "华东师范大学",
                "徐汇": "徐家汇",
                "普陀": "普陀区"
            }
            
            search_area = area_mapping.get(area, area)
            
            # 使用地理编码获取区域中心点坐标
            center_coords = self._geocode(search_area)
            if not center_coords:
                logger.warning(f"无法获取区域坐标: {area}")
                # 返回模拟数据
                return {
                    "status": "正常",
                    "description": "路况良好",
                    "evaluation": {"level": "1", "status": "畅通"},
                    "timestamp": datetime.now().isoformat()
                }
            
            # 构建矩形区域（以中心点为中心，范围约2km）
            center_lng, center_lat = center_coords.split(',')
            center_lng, center_lat = float(center_lng), float(center_lat)
            
            # 计算矩形范围（约2km）
            delta = 0.02  # 约2km
            rectangle = f"{center_lng-delta},{center_lat-delta},{center_lng+delta},{center_lat+delta}"
            
            params = {
                "key": get_api_key("AMAP_TRAFFIC"),
                "rectangle": rectangle,
                "level": "4"
            }
            
            result = self._make_request(AMAP_CONFIG["traffic_url"], params, "traffic")
            
            if result.get("status") == "1":
                traffic_data = {
                    "status": result.get("status", ""),
                    "description": result.get("description", ""),
                    "evaluation": result.get("evaluation", {}),
                    "timestamp": datetime.now().isoformat()
                }
                
                logger.info(f"路况API调用成功: {area}")
                return traffic_data
            else:
                logger.error(f"路况API调用失败: {result.get('info', '未知错误')}")
                # 返回模拟数据
                return {
                    "status": "正常",
                    "description": "路况良好",
                    "evaluation": {"level": "1", "status": "畅通"},
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"获取路况信息失败: {e}")
            # 返回模拟数据
            return {
                "status": "正常",
                "description": "路况良好",
                "evaluation": {"level": "1", "status": "畅通"},
                "timestamp": datetime.now().isoformat()
            }
    
    def search_poi(self, keyword: str, city: str, category: str = None) -> List[POIInfo]:
        """搜索POI信息 - 直接调用API，无缓存"""
        logger.info(f"调用POI API搜索: {keyword} in {city} (类型: {category})")
        
        try:
            # POI搜索API - v3版本（关键字搜索）
            params = {
                "key": get_api_key("AMAP_POI"),
                "keywords": keyword,
                "city": city,
                "types": category or "",
                "offset": 10,  # 每页返回10条
                "page": 1,
                "extensions": "all"
            }
            
            # 使用v3版本的POI搜索API
            poi_url = "https://restapi.amap.com/v3/place/text"
            result = self._make_request(poi_url, params, "poi")
            
            if result.get("status") == "1":
                pois = []
                for poi_data in result.get("pois", []):
                    poi_info = POIInfo(
                        name=poi_data.get("name", ""),
                        address=poi_data.get("address", ""),
                        rating=float(poi_data.get("biz_ext", {}).get("rating", "0") or "0"),
                        business_hours=poi_data.get("biz_ext", {}).get("open_time", ""),
                        price=poi_data.get("biz_ext", {}).get("cost", ""),
                        distance=poi_data.get("distance", ""),
                        category=poi_data.get("type", ""),
                        reviews=poi_data.get("biz_ext", {}).get("comment", "").split(";") if poi_data.get("biz_ext", {}).get("comment") else []
                    )
                    pois.append(poi_info)
                
                pois.sort(key=lambda x: x.rating, reverse=True)
                
                logger.info(f"POI API调用成功: {keyword} - {len(pois)}个结果")
                return pois
            else:
                logger.error(f"POI API调用失败: {result.get('info', '未知错误')}")
                
        except Exception as e:
            logger.error(f"搜索POI失败: {e}")
        
        return []
    
    def get_inputtips(self, keywords: str, city: str = "上海", 
                      poi_type: str = None, location: str = None, 
                      citylimit: bool = False, datatype: str = "all") -> List[Dict[str, Any]]:
        """获取输入提示 - 根据关键词返回建议列表
        
        Args:
            keywords: 查询关键词
            city: 搜索城市（默认：上海）
            poi_type: POI分类代码，多个用"|"分隔
            location: 坐标，格式"经度,纬度"，可优先返回此位置附近的结果
            citylimit: 是否仅返回指定城市数据（True/False）
            datatype: 返回数据类型（all/poi/bus/busline）
            
        Returns:
            建议列表
        """
        logger.info(f"调用输入提示API: {keywords} in {city}")
        
        try:
            params = {
                "key": get_api_key("AMAP_PROMPT"),
                "keywords": keywords,
                "city": city,
                "citylimit": "true" if citylimit else "false",
                "datatype": datatype
            }
            
            # 可选参数
            if poi_type:
                params["type"] = poi_type
            if location:
                params["location"] = location
            
            result = self._make_request(AMAP_CONFIG["inputtips_url"], params, "inputtips")
            
            if result.get("status") == "1":
                tips = []
                for tip_data in result.get("tips", []):
                    tip_info = {
                        "id": tip_data.get("id", ""),
                        "name": tip_data.get("name", ""),
                        "district": tip_data.get("district", ""),
                        "adcode": tip_data.get("adcode", ""),
                        "location": tip_data.get("location", ""),
                        "address": tip_data.get("address", ""),
                        "typecode": tip_data.get("typecode", "")
                    }
                    tips.append(tip_info)
                
                logger.info(f"输入提示API调用成功: {keywords} - {len(tips)}个建议")
                return tips
            else:
                logger.error(f"输入提示API调用失败: {result.get('info', '未知错误')}")
                
        except Exception as e:
            logger.error(f"获取输入提示失败: {e}")
        
        return []
    
    def _geocode(self, address: str) -> Optional[str]:
        """地理编码"""
        try:
            params = {
                "key": get_api_key("AMAP_POI"),
                "address": address
            }
            
            result = self._make_request(AMAP_CONFIG["geocode_url"], params, "geocode")
            
            if result.get("status") == "1":
                geocodes = result.get("geocodes", [])
                if geocodes:
                    return geocodes[0].get("location", "")
        except Exception as e:
            logger.error(f"地理编码失败: {e}")
        
        return None
    
    def _get_city_code(self, city_name: str) -> str:
        """获取城市代码"""
        city_codes = {
            "上海": "310000", "北京": "110000", "广州": "440100",
            "深圳": "440300", "杭州": "330100", "南京": "320100",
            "苏州": "320500", "成都": "510100", "重庆": "500000"
        }
        return city_codes.get(city_name, "310000")
    
    def _get_area_coordinates(self, area: str) -> Optional[str]:
        """获取区域坐标范围"""
        area_coords = {
            "外滩": "121.4805,31.2304,121.5005,31.2504",
            "陆家嘴": "121.4978,31.2297,121.5178,31.2497",
            "人民广场": "121.4637,31.2216,121.4837,31.2416"
        }
        return area_coords.get(area, None)
    
    def _format_transit_route(self, route: Dict[str, Any]) -> str:
        """格式化公交路线描述"""
        segments = route.get("segments", [])
        description = []
        
        for segment in segments:
            bus_info = segment.get("bus", {})
            if bus_info:
                bus_name = bus_info.get("busname", "")
                bus_stops = bus_info.get("buslines", [{}])[0].get("departure_stop", "")
                arrival_stops = bus_info.get("buslines", [{}])[0].get("arrival_stop", "")
                description.append(f"{bus_name}: {bus_stops} → {arrival_stops}")
        
        return " → ".join(description)
    
    def _format_driving_route(self, route: Dict[str, Any]) -> str:
        """格式化驾车路线描述"""
        steps = route.get("steps", [])
        description = []
        
        for step in steps[:3]:
            instruction = step.get("instruction", "")
            if instruction:
                description.append(instruction.split("，")[0])
        
        return " → ".join(description)

def main():
    """测试增强版Agent"""
    agent = EnhancedTravelAgent()
    
    print("🤖 增强版智能旅行对话Agent (豆包版)")
    print("=" * 60)
    print("输入 'quit' 退出对话")
    print("=" * 60)
    
    while True:
        try:
            user_input = input("\n👤 您: ").strip()
            
            if user_input.lower() in ['quit', 'exit', '退出']:
                print("👋 再见！")
                break
            
            if not user_input:
                continue
            
            # 处理用户请求
            response = agent.process_user_request(user_input, "test_user")
            
            print(f"\n🤖 Agent: {response}")
            
        except KeyboardInterrupt:
            print("\n👋 再见！")
            break
        except Exception as e:
            print(f"\n❌ 错误: {e}")

if __name__ == "__main__":
    main()
