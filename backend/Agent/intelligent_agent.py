#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能旅游攻略Agent
根据用户提示词智能分析并调用相关MCP服务，生成科学的旅游攻略
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from mcp_services import MCPServiceManager
from travel_agent import TravelAgentService, TravelPreference, WeatherCondition, TrafficCondition, CrowdLevel
from config import Config

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntelligentTravelAgent:
    """智能旅游攻略Agent - 核心决策引擎"""
    
    def __init__(self):
        """初始化智能Agent"""
        self.mcp_manager = MCPServiceManager()
        self.travel_agent = TravelAgentService()
        
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
        
        logger.info("🤖 智能旅游攻略Agent初始化完成")
    
    def analyze_user_query(self, user_input: str) -> Dict[str, Any]:
        """
        分析用户输入，提取关键信息
        
        Args:
            user_input: 用户输入的提示词
            
        Returns:
            分析结果字典
        """
        logger.info(f"🔍 分析用户查询: {user_input}")
        
        analysis = {
            "original_query": user_input,
            "detected_locations": [],
            "suggested_attractions": [],
            "activity_types": [],
            "requires_weather": False,
            "requires_traffic": False,
            "requires_navigation": False,
            "requires_poi": False,
            "time_preferences": [],
            "travel_preferences": None
        }
        
        # 1. 分析地点关键词
        for location, attractions in self.location_keywords.items():
            if location in user_input:
                analysis["detected_locations"].append(location)
                analysis["suggested_attractions"].extend(attractions)
                analysis["requires_navigation"] = True
                analysis["requires_poi"] = True
        
        # 2. 分析活动类型
        for activity, keywords in self.activity_keywords.items():
            if any(keyword in user_input for keyword in keywords):
                analysis["activity_types"].append(activity)
                analysis["requires_poi"] = True
        
        # 3. 检查是否需要天气信息
        if any(keyword in user_input for keyword in self.weather_keywords):
            analysis["requires_weather"] = True
        
        # 4. 检查是否需要交通信息
        if any(keyword in user_input for keyword in self.traffic_keywords):
            analysis["requires_traffic"] = True
            analysis["requires_navigation"] = True
        
        # 5. 分析时间偏好
        for time_keyword in self.time_keywords:
            if time_keyword in user_input:
                analysis["time_preferences"].append(time_keyword)
        
        # 6. 根据分析结果推断旅游偏好
        analysis["travel_preferences"] = self._infer_travel_preferences(analysis, user_input)
        
        # 7. 智能补充建议
        if analysis["detected_locations"] and not analysis["suggested_attractions"]:
            # 如果检测到地点但没有具体景点，智能推荐
            analysis["suggested_attractions"] = self._get_smart_recommendations(analysis["detected_locations"])
        
        logger.info(f"📊 分析结果: 地点{len(analysis['detected_locations'])}个, 景点{len(analysis['suggested_attractions'])}个, 活动{len(analysis['activity_types'])}种")
        
        return analysis
    
    def _infer_travel_preferences(self, analysis: Dict, user_input: str) -> TravelPreference:
        """根据分析结果推断用户旅游偏好"""
        
        # 默认偏好
        weather_tolerance = WeatherCondition.MODERATE
        traffic_tolerance = TrafficCondition.SLOW  
        crowd_tolerance = CrowdLevel.MODERATE
        preferred_time = "morning"
        budget_conscious = False
        time_conscious = False
        comfort_priority = False
        
        # 根据活动类型调整偏好
        if "商务" in analysis["activity_types"]:
            time_conscious = True
            comfort_priority = True
            preferred_time = "morning"
        elif "娱乐" in analysis["activity_types"]:
            crowd_tolerance = CrowdLevel.HIGH
            preferred_time = "evening"
        elif "亲子" in analysis["activity_types"]:
            weather_tolerance = WeatherCondition.GOOD
            comfort_priority = True
            
        # 根据时间偏好调整
        if "早上" in analysis["time_preferences"] or "上午" in analysis["time_preferences"]:
            preferred_time = "morning"
        elif "下午" in analysis["time_preferences"]:
            preferred_time = "afternoon"
        elif "晚上" in analysis["time_preferences"] or "夜里" in analysis["time_preferences"]:
            preferred_time = "evening"
        
        # 根据关键词调整
        if "省钱" in user_input or "便宜" in user_input or "经济" in user_input:
            budget_conscious = True
        if "快" in user_input or "赶时间" in user_input or "急" in user_input:
            time_conscious = True
        if "舒服" in user_input or "舒适" in user_input or "休闲" in user_input:
            comfort_priority = True
        
        return TravelPreference(
            weather_tolerance=weather_tolerance,
            traffic_tolerance=traffic_tolerance,
            crowd_tolerance=crowd_tolerance,
            preferred_time=preferred_time,
            budget_conscious=budget_conscious,
            time_conscious=time_conscious,
            comfort_priority=comfort_priority
        )
    
    def _get_smart_recommendations(self, locations: List[str]) -> List[str]:
        """基于地点智能推荐景点"""
        recommendations = []
        
        for location in locations:
            if location in self.location_keywords:
                recommendations.extend(self.location_keywords[location][:3])  # 每个地点推荐3个
        
        return list(set(recommendations))  # 去重
    
    def generate_intelligent_travel_plan(self, user_input: str) -> Dict[str, Any]:
        """
        根据用户输入生成智能旅游攻略
        
        Args:
            user_input: 用户输入的提示词
            
        Returns:
            完整的旅游攻略字典
        """
        logger.info(f"🎯 开始生成智能旅游攻略")
        
        # 1. 分析用户查询
        analysis = self.analyze_user_query(user_input)
        
        # 2. 确定起点和目的地
        origin, destinations = self._determine_origin_destinations(analysis)
        
        if not destinations:
            return {
                "success": False,
                "message": "未能识别出明确的目的地，请提供更具体的地点信息",
                "suggestions": "例如：'我想去浦东新区玩' 或 '带孩子去迪士尼'"
            }
        
        # 3. 智能MCP服务调用决策
        mcp_calls_needed = self._determine_mcp_calls(analysis, destinations)
        
        # 4. 执行MCP服务调用
        mcp_results = self._execute_mcp_calls(mcp_calls_needed, origin, destinations, analysis)
        
        # 5. 生成核心旅游攻略
        travel_plan = self.travel_agent.create_travel_plan(
            origin=origin,
            destinations=destinations,
            user_preferences=analysis["travel_preferences"]
        )
        
        # 6. 整合MCP结果和旅游攻略
        final_recommendation = self._integrate_results(
            travel_plan, mcp_results, analysis, user_input
        )
        
        logger.info(f"✅ 智能旅游攻略生成完成，总体得分: {travel_plan.overall_score}/100")
        
        return final_recommendation
    
    def _determine_origin_destinations(self, analysis: Dict) -> Tuple[str, List[str]]:
        """确定起点和目的地"""
        
        # 默认起点
        origin = "人民广场"  # 上海市中心
        
        # 从分析结果中提取目的地
        destinations = []
        
        if analysis["suggested_attractions"]:
            # 优先使用具体景点
            destinations = analysis["suggested_attractions"][:5]  # 最多5个目的地
        elif analysis["detected_locations"]:
            # 使用检测到的地点
            destinations = analysis["detected_locations"][:3]  # 最多3个地点
        
        # 去重并过滤
        destinations = list(set(destinations))
        destinations = [dest for dest in destinations if dest != origin]
        
        logger.info(f"📍 确定行程: {origin} → {destinations}")
        
        return origin, destinations
    
    def _determine_mcp_calls(self, analysis: Dict, destinations: List[str]) -> Dict[str, bool]:
        """决定需要调用哪些MCP服务"""
        
        mcp_calls = {
            "weather": False,
            "traffic": False,
            "navigation": False,
            "poi": False,
            "crowd": False
        }
        
        # 基于分析结果决定MCP调用
        if analysis["requires_weather"] or len(destinations) > 0:
            mcp_calls["weather"] = True  # 有目的地就检查天气
        
        if analysis["requires_traffic"] or len(destinations) > 1:
            mcp_calls["traffic"] = True  # 多个目的地需要检查交通
            
        if analysis["requires_navigation"] or len(destinations) > 0:
            mcp_calls["navigation"] = True  # 有目的地就需要导航
            
        if analysis["requires_poi"] or "美食" in analysis["activity_types"] or "购物" in analysis["activity_types"]:
            mcp_calls["poi"] = True  # 需要POI推荐
            
        if len(destinations) > 0:
            mcp_calls["crowd"] = True  # 检查人流情况
        
        logger.info(f"🔧 MCP调用决策: {[k for k, v in mcp_calls.items() if v]}")
        
        return mcp_calls
    
    def _execute_mcp_calls(self, mcp_calls: Dict[str, bool], origin: str, 
                          destinations: List[str], analysis: Dict) -> Dict[str, Any]:
        """执行MCP服务调用"""
        
        results = {}
        
        # 天气MCP
        if mcp_calls["weather"]:
            logger.info("🌤️ 调用天气MCP服务")
            weather_results = {}
            for dest in destinations:
                try:
                    weather_info = self.mcp_manager.weather_service.get_weather_info(dest)
                    weather_results[dest] = weather_info
                except Exception as e:
                    logger.warning(f"获取{dest}天气信息失败: {e}")
            results["weather"] = weather_results
        
        # 导航MCP  
        if mcp_calls["navigation"]:
            logger.info("🗺️ 调用导航MCP服务")
            try:
                if len(destinations) > 1:
                    navigation_result = self.mcp_manager.get_multi_destination_planning(
                        origin, destinations
                    )
                else:
                    navigation_result = self.mcp_manager.get_navigation_planning(
                        origin, destinations[0]
                    )
                results["navigation"] = navigation_result
            except Exception as e:
                logger.warning(f"获取导航信息失败: {e}")
        
        # POI MCP
        if mcp_calls["poi"]:
            logger.info("🔍 调用POI搜索MCP服务")
            poi_results = {}
            for dest in destinations:
                try:
                    # 根据活动类型确定搜索类型
                    travel_type = "tourism"
                    if "商务" in analysis["activity_types"]:
                        travel_type = "business"
                    elif "娱乐" in analysis["activity_types"]:
                        travel_type = "leisure"
                        
                    poi_info = self.mcp_manager.get_poi_recommendations_for_travel(
                        dest, travel_type
                    )
                    poi_results[dest] = poi_info
                except Exception as e:
                    logger.warning(f"获取{dest} POI信息失败: {e}")
            results["poi"] = poi_results
        
        # 交通MCP (路况)
        if mcp_calls["traffic"]:
            logger.info("🚦 调用交通MCP服务") 
            try:
                # 获取主要路线的交通状况
                if results.get("navigation"):
                    # 基于导航结果获取交通信息
                    traffic_info = self.mcp_manager.traffic_service.get_traffic_info(
                        f"{origin}到{destinations[0]}"
                    )
                    results["traffic"] = traffic_info
            except Exception as e:
                logger.warning(f"获取交通信息失败: {e}")
        
        # 人流MCP
        if mcp_calls["crowd"]:
            logger.info("👥 调用人流MCP服务")
            crowd_results = {}
            for dest in destinations:
                try:
                    crowd_info = self.mcp_manager.crowd_service.get_crowd_info(dest)
                    crowd_results[dest] = crowd_info
                except Exception as e:
                    logger.warning(f"获取{dest}人流信息失败: {e}")
            results["crowd"] = crowd_results
        
        return results
    
    def _integrate_results(self, travel_plan, mcp_results: Dict, analysis: Dict, 
                          user_input: str) -> Dict[str, Any]:
        """整合所有结果生成最终攻略"""
        
        # 基础攻略信息
        final_plan = {
            "success": True,
            "user_query": user_input,
            "analysis_summary": {
                "detected_locations": analysis["detected_locations"],
                "suggested_attractions": analysis["suggested_attractions"], 
                "activity_types": analysis["activity_types"]
            },
            "travel_plan": {
                "plan_id": travel_plan.plan_id,
                "origin": travel_plan.origin,
                "destinations": travel_plan.destinations,
                "overall_score": travel_plan.overall_score,
                "recommendations": travel_plan.recommendations
            },
            "mcp_insights": self._generate_mcp_insights(mcp_results),
            "final_recommendations": [],
            "practical_tips": [],
            "timestamp": datetime.now().isoformat()
        }
        
        # 生成最终建议
        final_recommendations = []
        
        # 基于旅游攻略的建议
        final_recommendations.extend(travel_plan.recommendations)
        
        # 基于MCP结果的智能建议
        if "weather" in mcp_results:
            weather_advice = self._generate_weather_advice(mcp_results["weather"])
            final_recommendations.extend(weather_advice)
        
        if "poi" in mcp_results:
            poi_advice = self._generate_poi_advice(mcp_results["poi"], analysis["activity_types"])
            final_recommendations.extend(poi_advice)
        
        if "traffic" in mcp_results:
            traffic_advice = self._generate_traffic_advice(mcp_results["traffic"])
            final_recommendations.extend(traffic_advice)
        
        # 实用建议
        practical_tips = self._generate_practical_tips(analysis, mcp_results)
        
        final_plan["final_recommendations"] = final_recommendations
        final_plan["practical_tips"] = practical_tips
        
        return final_plan
    
    def _generate_mcp_insights(self, mcp_results: Dict) -> Dict[str, str]:
        """生成MCP服务洞察摘要"""
        insights = {}
        
        if "weather" in mcp_results:
            weather_summary = []
            for location, weather in mcp_results["weather"].items():
                if weather and "weather" in weather:
                    weather_summary.append(f"{location}: {weather['weather']} {weather.get('temperature', '')}°C")
            insights["weather"] = "；".join(weather_summary) if weather_summary else "天气信息获取失败"
        
        if "poi" in mcp_results:
            poi_summary = []
            for location, poi_data in mcp_results["poi"].items():
                if poi_data and "total_count" in poi_data:
                    poi_summary.append(f"{location}周边有{poi_data['total_count']}个相关POI")
            insights["poi"] = "；".join(poi_summary) if poi_summary else "POI信息获取失败"
        
        return insights
    
    def _generate_weather_advice(self, weather_data: Dict) -> List[str]:
        """生成天气相关建议"""
        advice = []
        
        for location, weather in weather_data.items():
            if weather and "weather" in weather:
                weather_condition = weather["weather"]
                temperature = weather.get("temperature", "")
                
                if "雨" in weather_condition:
                    advice.append(f"☔ {location}有雨，建议携带雨具")
                elif "雪" in weather_condition:
                    advice.append(f"❄️ {location}有雪，注意保暖和路面安全")
                elif weather_condition == "晴":
                    advice.append(f"☀️ {location}天气晴朗，适合出行")
                
                if temperature:
                    temp_val = int(temperature) if temperature.isdigit() else 0
                    if temp_val > 30:
                        advice.append(f"🌡️ {location}温度较高({temperature}°C)，注意防暑")
                    elif temp_val < 5:
                        advice.append(f"🧊 {location}温度较低({temperature}°C)，注意保暖")
        
        return advice
    
    def _generate_poi_advice(self, poi_data: Dict, activity_types: List[str]) -> List[str]:
        """生成POI相关建议"""
        advice = []
        
        for location, poi_info in poi_data.items():
            if poi_info and "pois" in poi_info:
                pois = poi_info["pois"]
                
                # 统计不同类型POI
                restaurants = [p for p in pois if p.get("typecode", "").startswith("05")]
                shopping = [p for p in pois if p.get("typecode", "").startswith("06")]
                attractions = [p for p in pois if p.get("typecode", "").startswith("11")]
                
                if "美食" in activity_types and restaurants:
                    advice.append(f"🍽️ {location}周边推荐餐厅: {restaurants[0].get('name', '')}")
                
                if "购物" in activity_types and shopping:
                    advice.append(f"🛍️ {location}周边购物推荐: {shopping[0].get('name', '')}")
                
                if attractions:
                    advice.append(f"🎯 {location}周边景点: {attractions[0].get('name', '')}")
        
        return advice
    
    def _generate_traffic_advice(self, traffic_data: Dict) -> List[str]:
        """生成交通相关建议"""
        advice = []
        
        if traffic_data and "status" in traffic_data:
            status = traffic_data["status"]
            if "拥堵" in status or "slow" in status.lower():
                advice.append("🚦 当前路况拥堵，建议选择公共交通或调整出行时间")
            elif "畅通" in status or "smooth" in status.lower():
                advice.append("🟢 当前路况良好，适合自驾出行")
        
        return advice
    
    def _generate_practical_tips(self, analysis: Dict, mcp_results: Dict) -> List[str]:
        """生成实用攻略建议"""
        tips = []
        
        # 基于活动类型的建议
        if "亲子" in analysis["activity_types"]:
            tips.extend([
                "👶 建议携带儿童用品和小食",
                "🎪 选择适合儿童的景点和活动",
                "⏰ 安排适当的休息时间"
            ])
        
        if "美食" in analysis["activity_types"]:
            tips.extend([
                "🍴 建议避开用餐高峰期(12-13点，18-19点)",
                "💰 可以关注团购优惠信息"
            ])
        
        if "购物" in analysis["activity_types"]:
            tips.extend([
                "🛍️ 商场一般10:00开门，建议合理安排时间",
                "💳 大部分商场支持移动支付"
            ])
        
        # 基于地点的建议
        if "外滩" in analysis["detected_locations"]:
            tips.append("🌃 外滩夜景最佳观赏时间是傍晚18-20点")
        
        if "迪士尼" in analysis["detected_locations"]:
            tips.extend([
                "🎫 建议提前购买门票并下载官方APP",
                "⏰ 工作日游客相对较少"
            ])
        
        return tips

def main():
    """测试智能Agent"""
    agent = IntelligentTravelAgent()
    
    # 测试用例
    test_queries = [
        "我想去浦东新区玩，带着孩子",
        "明天要去外滩，担心天气不好", 
        "想在徐家汇附近找个地方吃饭购物",
        "周末开车去迪士尼，路况怎么样",
        "商务出差，需要在陆家嘴附近找酒店和餐厅"
    ]
    
    for query in test_queries:
        print(f"\n" + "="*60)
        print(f"测试查询: {query}")
        print("="*60)
        
        result = agent.generate_intelligent_travel_plan(query)
        
        if result["success"]:
            print(f"📊 攻略得分: {result['travel_plan']['overall_score']}/100")
            print(f"🎯 建议数量: {len(result['final_recommendations'])}")
            print("\n💡 主要建议:")
            for i, rec in enumerate(result['final_recommendations'][:3], 1):
                print(f"  {i}. {rec}")
        else:
            print(f"❌ {result['message']}")

if __name__ == "__main__":
    main()

