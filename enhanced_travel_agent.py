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
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import pandas as pd
from pathlib import Path

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
    
    def process_user_request(self, user_input: str, user_id: str = "default") -> str:
        """
        处理用户请求的主入口
        
        Args:
            user_input: 用户输入
            user_id: 用户ID
            
        Returns:
            生成的回复
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
        
        # 1. 先让豆包Agent理解用户需求并生成初始回复
        initial_response = self._generate_initial_response(user_input, context)
        
        # 2. 根据Agent的回复决定需要哪些MCP服务
        required_services = self._analyze_agent_response_for_mcp(initial_response, user_input)
        
        # 3. 调用相应的MCP服务获取实时数据
        real_time_data = self._call_targeted_mcp_services(required_services, user_input, context)
        
        # 4. 使用实时数据优化Agent的回复
        final_response = self._optimize_response_with_data(user_input, initial_response, real_time_data, context)
        
        # 记录Agent回复
        context.conversation_history.append({
            "role": "assistant",
            "content": final_response,
            "timestamp": datetime.now().isoformat()
        })
        
        logger.info(f"🤖 Agent回复: {len(final_response)} 字符")
        
        return final_response
    
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
            
            if "poi" in real_time_data:
                poi_info = real_time_data["poi"]
                message += "🎯 景点信息：\n"
                for category, pois in poi_info.items():
                    if pois and len(pois) > 0:
                        message += f"  {category}：\n"
                        for poi in pois[:3]:
                            if poi.name and len(poi.name) > 2:
                                message += f"    - {poi.name}（评分：{poi.rating}星）\n"
            
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
        
        message += "\n请基于以上信息，为用户生成详细的旅游攻略。"
        
        return message
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        keywords = []
        
        # 提取地点关键词
        for location in self.location_keywords.keys():
            if location in text:
                keywords.append(location)
        
        # 提取活动关键词
        for activity, activity_keywords in self.activity_keywords.items():
            if any(keyword in text for keyword in activity_keywords):
                keywords.append(activity)
        
        # 提取其他关键词
        if any(keyword in text for keyword in self.weather_keywords):
            keywords.append("天气")
        if any(keyword in text for keyword in self.traffic_keywords):
            keywords.append("交通")
        if any(keyword in text for keyword in self.time_keywords):
            keywords.append("时间")
        
        return keywords
    
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
    def _make_request(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """发送HTTP请求"""
        try:
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
            
            result = self._make_request(AMAP_CONFIG["weather_url"], params)
            
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
            
            params = {
                "key": get_api_key("AMAP_NAVIGATION"),
                "origin": origin_coords,
                "destination": dest_coords,
                "strategy": "0",
                "extensions": "all"
            }
            
            if transport_mode == "transit":
                params["strategy"] = "0"
                url = f"{AMAP_CONFIG['base_url']}/direction/transit/integrated"
            else:
                url = f"{AMAP_CONFIG['base_url']}/direction/driving"
            
            result = self._make_request(url, params)
            
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
            
            result = self._make_request(AMAP_CONFIG["traffic_url"], params)
            
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
            params = {
                "key": get_api_key("AMAP_POI"),
                "keywords": keyword,
                "city": city,
                "types": category or "",
                "offset": 10,  # 增加结果数量
                "page": 1,
                "extensions": "all"
            }
            
            result = self._make_request(AMAP_CONFIG["poi_url"], params)
            
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
    
    def _geocode(self, address: str) -> Optional[str]:
        """地理编码"""
        try:
            params = {
                "key": get_api_key("AMAP_POI"),
                "address": address
            }
            
            result = self._make_request(AMAP_CONFIG["geocode_url"], params)
            
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
