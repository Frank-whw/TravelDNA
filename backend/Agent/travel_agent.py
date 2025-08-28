#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能旅游攻略规划Agent
整合MCP服务（天气、导航、路况、人流）与RAG，实现智能旅游攻略规划
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from mcp_services import MCPServiceManager
from config import Config

logger = logging.getLogger(__name__)

class WeatherCondition(Enum):
    """天气状况枚举"""
    EXCELLENT = "excellent"      # 优秀
    GOOD = "good"               # 良好
    MODERATE = "moderate"       # 一般
    POOR = "poor"              # 较差
    EXTREME = "extreme"        # 极端恶劣

class TrafficCondition(Enum):
    """交通状况枚举"""
    SMOOTH = "smooth"          # 畅通
    SLOW = "slow"              # 缓慢
    CONGESTED = "congested"    # 拥堵
    BLOCKED = "blocked"        # 严重拥堵

class CrowdLevel(Enum):
    """人流量等级枚举"""
    LOW = "low"                # 人少
    MODERATE = "moderate"      # 适中
    HIGH = "high"              # 人多
    VERY_HIGH = "very_high"    # 人非常多

@dataclass
class TravelPreference:
    """用户旅游偏好"""
    weather_tolerance: WeatherCondition = WeatherCondition.MODERATE
    traffic_tolerance: TrafficCondition = TrafficCondition.SLOW
    crowd_tolerance: CrowdLevel = CrowdLevel.HIGH
    preferred_time: str = "morning"  # morning, afternoon, evening
    budget_conscious: bool = False
    time_conscious: bool = True
    comfort_priority: bool = False

@dataclass
class LocationCondition:
    """地点实时状况"""
    location: str
    weather: Dict[str, Any]
    weather_condition: WeatherCondition
    crowd_level: CrowdLevel
    accessibility: str
    recommendation: str

@dataclass
class RouteCondition:
    """路线实时状况"""
    origin: str
    destination: str
    route_info: Dict[str, Any]
    traffic_condition: TrafficCondition
    estimated_duration: int
    alternative_routes: List[Dict]
    recommendation: str

@dataclass
class TravelPlan:
    """旅游计划"""
    plan_id: str
    origin: str
    destinations: List[str]
    route_conditions: List[RouteCondition]
    location_conditions: List[LocationCondition]
    total_duration: int
    total_distance: float
    weather_compatibility: float
    traffic_score: float
    crowd_score: float
    overall_score: float
    recommendations: List[str]
    adjustments: List[str]
    timestamp: str

class TravelAgentService:
    """智能旅游攻略规划服务"""
    
    def __init__(self):
        self.mcp_manager = MCPServiceManager()
        self.plan_history = []
        self.user_feedback_history = []
        
    def create_travel_plan(self, origin: str, destinations: List[str], 
                          user_preferences: Optional[TravelPreference] = None,
                          date: Optional[str] = None) -> TravelPlan:
        """
        创建智能旅游攻略计划
        
        Args:
            origin: 起点
            destinations: 目的地列表
            user_preferences: 用户偏好
            date: 计划日期
            
        Returns:
            TravelPlan: 完整的旅游计划
        """
        logger.info(f"🎯 开始为用户规划从 {origin} 到 {destinations} 的旅游攻略")
        
        if user_preferences is None:
            user_preferences = TravelPreference()
            
        plan_id = f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 第一步：天气检查和动态调整
        logger.info("🌤️ 第一步：检查天气状况并进行动态调整")
        weather_analysis = self._analyze_weather_conditions(destinations, date)
        
        # 如果遇到极端天气，动态调整计划
        if any(loc['weather_condition'] == WeatherCondition.EXTREME for loc in weather_analysis):
            logger.warning("⚠️ 检测到极端天气，启动动态调整...")
            weather_analysis, destinations = self._handle_extreme_weather(
                weather_analysis, destinations, user_preferences
            )
        
        # 第二步：路线规划
        logger.info("🗺️ 第二步：进行智能路线规划")
        route_conditions = self._plan_optimal_routes(origin, destinations, user_preferences)
        
        # 第三步：路况检查和优化
        logger.info("🚦 第三步：检查路况并优化路线")
        route_conditions = self._optimize_routes_by_traffic(route_conditions, user_preferences)
        
        # 第四步：人流量分析
        logger.info("👥 第四步：分析各景点人流量状况")
        location_conditions = self._analyze_crowd_conditions(destinations, weather_analysis)
        
        # 第五步：综合评估
        logger.info("📊 第五步：综合评估并计算方案得分")
        plan_scores = self._calculate_plan_scores(
            route_conditions, location_conditions, user_preferences
        )
        
        # 第六步：POI推荐增强
        logger.info("🔍 第六步：获取周边POI推荐")
        poi_recommendations = self._get_poi_recommendations(destinations)
        
        # 第七步：生成建议和调整方案
        logger.info("💡 第七步：生成智能建议和调整方案")
        recommendations, adjustments = self._generate_recommendations(
            route_conditions, location_conditions, plan_scores, user_preferences, poi_recommendations
        )
        
        # 创建完整旅游计划
        travel_plan = TravelPlan(
            plan_id=plan_id,
            origin=origin,
            destinations=destinations,
            route_conditions=route_conditions,
            location_conditions=location_conditions,
            total_duration=sum(route.estimated_duration for route in route_conditions),
            total_distance=sum(route.route_info.get('distance_value', 0) for route in route_conditions) / 1000,
            weather_compatibility=plan_scores['weather_score'],
            traffic_score=plan_scores['traffic_score'],
            crowd_score=plan_scores['crowd_score'],
            overall_score=plan_scores['overall_score'],
            recommendations=recommendations,
            adjustments=adjustments,
            timestamp=datetime.now().isoformat()
        )
        
        self.plan_history.append(travel_plan)
        logger.info(f"✅ 旅游攻略规划完成，总体得分: {plan_scores['overall_score']:.1f}/100")
        
        return travel_plan
    
    def _analyze_weather_conditions(self, destinations: List[str], date: Optional[str] = None) -> List[Dict]:
        """分析天气状况"""
        weather_analysis = []
        
        for destination in destinations:
            try:
                # 获取天气信息
                weather_info = self.mcp_manager.weather_service.get_weather_info(destination)
                
                if weather_info.get('api_source') == 'amap_weather':
                    current_weather = weather_info.get('current_weather', {})
                    weather_desc = current_weather.get('weather', '').lower()
                    temperature = current_weather.get('temperature', 0)
                    wind_power = current_weather.get('wind_power', '').replace('级', '')
                    
                    # 评估天气状况
                    weather_condition = self._evaluate_weather_condition(
                        weather_desc, int(temperature), wind_power
                    )
                    
                    weather_analysis.append({
                        'location': destination,
                        'weather_info': weather_info,
                        'weather_condition': weather_condition,
                        'temperature': temperature,
                        'description': weather_desc,
                        'suitability': self._get_weather_suitability_advice(weather_condition)
                    })
                else:
                    # 天气API失败时的默认处理
                    weather_analysis.append({
                        'location': destination,
                        'weather_info': {},
                        'weather_condition': WeatherCondition.MODERATE,
                        'temperature': 20,
                        'description': '天气信息暂时无法获取',
                        'suitability': '建议关注实时天气变化'
                    })
                    
            except Exception as e:
                logger.error(f"获取 {destination} 天气信息失败: {e}")
                weather_analysis.append({
                    'location': destination,
                    'weather_info': {},
                    'weather_condition': WeatherCondition.MODERATE,
                    'temperature': 20,
                    'description': '天气信息获取失败',
                    'suitability': '建议出行前确认天气'
                })
        
        return weather_analysis
    
    def _evaluate_weather_condition(self, weather_desc: str, temperature: int, wind_power: str) -> WeatherCondition:
        """评估天气状况等级"""
        # 极端天气判断
        extreme_weather = ['暴雨', '大暴雨', '特大暴雨', '暴雪', '大暴雪', '台风', '龙卷风', '冰雹']
        if any(extreme in weather_desc for extreme in extreme_weather):
            return WeatherCondition.EXTREME
        
        # 温度判断
        if temperature < -5 or temperature > 38:
            return WeatherCondition.POOR
        
        # 风力判断
        try:
            wind_level = int(wind_power) if wind_power.isdigit() else 3
            if wind_level >= 7:
                return WeatherCondition.POOR
        except:
            wind_level = 3
        
        # 天气描述判断
        excellent_weather = ['晴', '多云']
        good_weather = ['阴', '小雨', '小雪']
        poor_weather = ['中雨', '大雨', '中雪', '大雪', '雾', '霾']
        
        if any(weather in weather_desc for weather in excellent_weather):
            return WeatherCondition.EXCELLENT if 15 <= temperature <= 25 else WeatherCondition.GOOD
        elif any(weather in weather_desc for weather in good_weather):
            return WeatherCondition.GOOD if 10 <= temperature <= 30 else WeatherCondition.MODERATE
        elif any(weather in weather_desc for weather in poor_weather):
            return WeatherCondition.POOR
        else:
            return WeatherCondition.MODERATE
    
    def _get_weather_suitability_advice(self, condition: WeatherCondition) -> str:
        """获取天气适宜性建议"""
        advice_map = {
            WeatherCondition.EXCELLENT: "天气极佳，非常适合出游",
            WeatherCondition.GOOD: "天气良好，适合出游",
            WeatherCondition.MODERATE: "天气一般，可以出游但需注意防护",
            WeatherCondition.POOR: "天气较差，建议调整行程或做好防护措施",
            WeatherCondition.EXTREME: "极端天气，强烈建议推迟行程"
        }
        return advice_map.get(condition, "天气状况未知，建议谨慎出行")
    
    def _handle_extreme_weather(self, weather_analysis: List[Dict], destinations: List[str], 
                               preferences: TravelPreference) -> Tuple[List[Dict], List[str]]:
        """处理极端天气，动态调整目的地"""
        logger.warning("🌪️ 检测到极端天气，正在动态调整旅游计划...")
        
        # 找出天气极端的目的地
        extreme_locations = [
            analysis for analysis in weather_analysis 
            if analysis['weather_condition'] == WeatherCondition.EXTREME
        ]
        
        adjusted_destinations = []
        adjusted_weather_analysis = []
        
        for analysis in weather_analysis:
            if analysis['weather_condition'] != WeatherCondition.EXTREME:
                adjusted_destinations.append(analysis['location'])
                adjusted_weather_analysis.append(analysis)
            else:
                logger.warning(f"⚠️ 由于极端天气，已移除目的地: {analysis['location']}")
        
        # 如果所有目的地都有极端天气，建议推迟
        if not adjusted_destinations:
            logger.error("❌ 所有目的地都有极端天气，建议推迟出行")
            # 返回原始计划但添加警告
            for analysis in weather_analysis:
                analysis['suitability'] = "极端天气，强烈建议推迟出行"
            return weather_analysis, destinations
        
        return adjusted_weather_analysis, adjusted_destinations
    
    def _plan_optimal_routes(self, origin: str, destinations: List[str], 
                           preferences: TravelPreference) -> List[RouteCondition]:
        """规划最优路线"""
        route_conditions = []
        current_location = origin
        
        # 选择导航策略
        strategy = self._select_navigation_strategy(preferences)
        
        for i, destination in enumerate(destinations):
            try:
                # 获取路线规划
                route_info = self.mcp_manager.navigation_service.get_route_planning(
                    current_location, destination, strategy=strategy
                )
                
                if route_info.get('api_source') == 'amap_navigation':
                    # 评估交通状况
                    traffic_condition = self._evaluate_traffic_condition(route_info)
                    
                    route_condition = RouteCondition(
                        origin=current_location,
                        destination=destination,
                        route_info=route_info,
                        traffic_condition=traffic_condition,
                        estimated_duration=route_info.get('duration_value', 0) // 60,
                        alternative_routes=[],
                        recommendation=self._get_route_recommendation(route_info, traffic_condition)
                    )
                else:
                    # 导航API失败时的默认处理
                    route_condition = RouteCondition(
                        origin=current_location,
                        destination=destination,
                        route_info={'error': '路线规划失败'},
                        traffic_condition=TrafficCondition.SLOW,
                        estimated_duration=30,  # 默认30分钟
                        alternative_routes=[],
                        recommendation="路线信息暂时无法获取，建议现场确认"
                    )
                
                route_conditions.append(route_condition)
                current_location = destination
                
            except Exception as e:
                logger.error(f"规划从 {current_location} 到 {destination} 的路线失败: {e}")
                # 添加错误处理的路线条件
                route_condition = RouteCondition(
                    origin=current_location,
                    destination=destination,
                    route_info={'error': str(e)},
                    traffic_condition=TrafficCondition.SLOW,
                    estimated_duration=30,
                    alternative_routes=[],
                    recommendation="路线规划出现问题，建议手动确认路线"
                )
                route_conditions.append(route_condition)
                current_location = destination
        
        return route_conditions
    
    def _select_navigation_strategy(self, preferences: TravelPreference) -> str:
        """根据用户偏好选择导航策略"""
        if preferences.time_conscious:
            return "fastest"
        elif preferences.budget_conscious:
            return "less_fee"
        elif preferences.comfort_priority:
            return "avoid_congestion"
        else:
            return "default"
    
    def _evaluate_traffic_condition(self, route_info: Dict) -> TrafficCondition:
        """评估交通状况"""
        # 根据实际时间与预估时间的比较来判断
        distance_km = route_info.get('distance_value', 0) / 1000
        duration_minutes = route_info.get('duration_value', 0) / 60
        
        if distance_km > 0 and duration_minutes > 0:
            avg_speed = distance_km / (duration_minutes / 60)  # km/h
            
            if avg_speed >= 40:
                return TrafficCondition.SMOOTH
            elif avg_speed >= 25:
                return TrafficCondition.SLOW
            elif avg_speed >= 15:
                return TrafficCondition.CONGESTED
            else:
                return TrafficCondition.BLOCKED
        
        return TrafficCondition.SLOW
    
    def _get_route_recommendation(self, route_info: Dict, traffic_condition: TrafficCondition) -> str:
        """获取路线建议"""
        recommendations = []
        
        # 基于距离的建议
        distance_km = route_info.get('distance_value', 0) / 1000
        if distance_km > 20:
            recommendations.append("距离较远，建议预留充足时间")
        
        # 基于交通状况的建议
        traffic_advice = {
            TrafficCondition.SMOOTH: "交通畅通，可按计划出行",
            TrafficCondition.SLOW: "交通略缓慢，建议避开高峰期",
            TrafficCondition.CONGESTED: "交通拥堵，建议选择其他时间或路线",
            TrafficCondition.BLOCKED: "交通严重拥堵，强烈建议调整出行时间"
        }
        recommendations.append(traffic_advice.get(traffic_condition, "交通状况一般"))
        
        # 基于费用的建议
        tolls = route_info.get('tolls_value', 0)
        if tolls > 20:
            recommendations.append("过路费较高，可考虑地面道路")
        
        return "；".join(recommendations)
    
    def _optimize_routes_by_traffic(self, route_conditions: List[RouteCondition], 
                                   preferences: TravelPreference) -> List[RouteCondition]:
        """根据路况优化路线"""
        optimized_routes = []
        
        for route_condition in route_conditions:
            # 如果交通状况不佳且用户不能容忍，尝试获取替代方案
            if (route_condition.traffic_condition.value in ['congested', 'blocked'] and 
                preferences.traffic_tolerance.value not in ['congested', 'blocked']):
                
                logger.info(f"🔄 路况不佳，为 {route_condition.origin} → {route_condition.destination} 寻找替代路线")
                
                # 尝试不同的导航策略
                alternative_strategies = ['avoid_congestion', 'no_highway', 'less_fee']
                
                for strategy in alternative_strategies:
                    try:
                        alt_route = self.mcp_manager.navigation_service.get_route_planning(
                            route_condition.origin, route_condition.destination, strategy=strategy
                        )
                        
                        if alt_route.get('api_source') == 'amap_navigation':
                            alt_traffic = self._evaluate_traffic_condition(alt_route)
                            
                            # 如果替代路线交通状况更好，使用替代路线
                            if self._is_better_route(alt_traffic, route_condition.traffic_condition):
                                logger.info(f"✅ 找到更好的替代路线，策略: {strategy}")
                                route_condition.route_info = alt_route
                                route_condition.traffic_condition = alt_traffic
                                route_condition.recommendation = f"已优化为{strategy}策略：" + self._get_route_recommendation(alt_route, alt_traffic)
                                break
                    except Exception as e:
                        logger.warning(f"尝试替代路线失败 ({strategy}): {e}")
                        continue
            
            optimized_routes.append(route_condition)
        
        return optimized_routes
    
    def _is_better_route(self, new_traffic: TrafficCondition, old_traffic: TrafficCondition) -> bool:
        """判断新路线是否比旧路线更好"""
        traffic_scores = {
            TrafficCondition.SMOOTH: 4,
            TrafficCondition.SLOW: 3,
            TrafficCondition.CONGESTED: 2,
            TrafficCondition.BLOCKED: 1
        }
        return traffic_scores.get(new_traffic, 0) > traffic_scores.get(old_traffic, 0)
    
    def _analyze_crowd_conditions(self, destinations: List[str], weather_analysis: List[Dict]) -> List[LocationCondition]:
        """分析景点人流量状况"""
        location_conditions = []
        
        for i, destination in enumerate(destinations):
            try:
                # 获取人流量信息
                crowd_info = self.mcp_manager.crowd_service.get_crowd_info(destination)
                
                if crowd_info.get('api_source') == 'amap_crowd':
                    crowd_level = self._evaluate_crowd_level(crowd_info)
                else:
                    crowd_level = CrowdLevel.MODERATE  # 默认中等人流
                
                # 获取对应的天气信息
                weather_info = next(
                    (w for w in weather_analysis if w['location'] == destination), 
                    {'weather_condition': WeatherCondition.MODERATE}
                )
                
                location_condition = LocationCondition(
                    location=destination,
                    weather=weather_info.get('weather_info', {}),
                    weather_condition=weather_info['weather_condition'],
                    crowd_level=crowd_level,
                    accessibility=self._evaluate_accessibility(crowd_level, weather_info['weather_condition']),
                    recommendation=self._get_location_recommendation(crowd_level, weather_info['weather_condition'])
                )
                
                location_conditions.append(location_condition)
                
            except Exception as e:
                logger.error(f"分析 {destination} 人流状况失败: {e}")
                # 默认条件
                location_condition = LocationCondition(
                    location=destination,
                    weather={},
                    weather_condition=WeatherCondition.MODERATE,
                    crowd_level=CrowdLevel.MODERATE,
                    accessibility="一般",
                    recommendation="人流和天气信息暂时无法获取，建议现场确认"
                )
                location_conditions.append(location_condition)
        
        return location_conditions
    
    def _evaluate_crowd_level(self, crowd_info: Dict) -> CrowdLevel:
        """评估人流量等级"""
        # 基于API返回的人流描述进行判断
        crowd_desc = crowd_info.get('crowd_status', '').lower()
        
        if '人少' in crowd_desc or '空闲' in crowd_desc:
            return CrowdLevel.LOW
        elif '适中' in crowd_desc or '正常' in crowd_desc:
            return CrowdLevel.MODERATE
        elif '人多' in crowd_desc or '拥挤' in crowd_desc:
            return CrowdLevel.HIGH
        elif '非常多' in crowd_desc or '爆满' in crowd_desc:
            return CrowdLevel.VERY_HIGH
        else:
            return CrowdLevel.MODERATE
    
    def _evaluate_accessibility(self, crowd_level: CrowdLevel, weather_condition: WeatherCondition) -> str:
        """评估地点可达性"""
        accessibility_matrix = {
            (CrowdLevel.LOW, WeatherCondition.EXCELLENT): "优秀",
            (CrowdLevel.LOW, WeatherCondition.GOOD): "很好",
            (CrowdLevel.MODERATE, WeatherCondition.EXCELLENT): "很好",
            (CrowdLevel.MODERATE, WeatherCondition.GOOD): "良好",
            (CrowdLevel.HIGH, WeatherCondition.EXCELLENT): "良好",
            (CrowdLevel.HIGH, WeatherCondition.GOOD): "一般",
            (CrowdLevel.VERY_HIGH, WeatherCondition.POOR): "困难",
            (CrowdLevel.VERY_HIGH, WeatherCondition.EXTREME): "非常困难"
        }
        
        return accessibility_matrix.get((crowd_level, weather_condition), "一般")
    
    def _get_location_recommendation(self, crowd_level: CrowdLevel, weather_condition: WeatherCondition) -> str:
        """获取地点游览建议"""
        recommendations = []
        
        # 人流建议
        crowd_advice = {
            CrowdLevel.LOW: "人流较少，游览体验佳",
            CrowdLevel.MODERATE: "人流适中，适合游览",
            CrowdLevel.HIGH: "人流较多，建议错峰游览",
            CrowdLevel.VERY_HIGH: "人流密集，建议避开或调整时间"
        }
        recommendations.append(crowd_advice.get(crowd_level, "人流状况一般"))
        
        # 天气建议
        if weather_condition in [WeatherCondition.POOR, WeatherCondition.EXTREME]:
            recommendations.append("天气不佳，建议室内活动或调整行程")
        elif weather_condition == WeatherCondition.EXCELLENT:
            recommendations.append("天气绝佳，非常适合户外游览")
        
        return "；".join(recommendations)
    
    def _calculate_plan_scores(self, route_conditions: List[RouteCondition], 
                              location_conditions: List[LocationCondition],
                              preferences: TravelPreference) -> Dict[str, float]:
        """计算旅游计划综合得分"""
        
        # 天气得分 (0-100)
        weather_scores = []
        for location in location_conditions:
            weather_score = {
                WeatherCondition.EXCELLENT: 100,
                WeatherCondition.GOOD: 80,
                WeatherCondition.MODERATE: 60,
                WeatherCondition.POOR: 30,
                WeatherCondition.EXTREME: 0
            }.get(location.weather_condition, 60)
            weather_scores.append(weather_score)
        
        weather_score = sum(weather_scores) / len(weather_scores) if weather_scores else 60
        
        # 交通得分 (0-100)
        traffic_scores = []
        for route in route_conditions:
            traffic_score = {
                TrafficCondition.SMOOTH: 100,
                TrafficCondition.SLOW: 75,
                TrafficCondition.CONGESTED: 50,
                TrafficCondition.BLOCKED: 25
            }.get(route.traffic_condition, 60)
            traffic_scores.append(traffic_score)
        
        traffic_score = sum(traffic_scores) / len(traffic_scores) if traffic_scores else 60
        
        # 人流得分 (0-100)
        crowd_scores = []
        for location in location_conditions:
            crowd_score = {
                CrowdLevel.LOW: 100,
                CrowdLevel.MODERATE: 80,
                CrowdLevel.HIGH: 60,
                CrowdLevel.VERY_HIGH: 30
            }.get(location.crowd_level, 60)
            crowd_scores.append(crowd_score)
        
        crowd_score = sum(crowd_scores) / len(crowd_scores) if crowd_scores else 60
        
        # 综合得分 (权重可调整)
        overall_score = (weather_score * 0.3 + traffic_score * 0.4 + crowd_score * 0.3)
        
        return {
            'weather_score': weather_score,
            'traffic_score': traffic_score,
            'crowd_score': crowd_score,
            'overall_score': overall_score
        }
    
    def _generate_recommendations(self, route_conditions: List[RouteCondition],
                                 location_conditions: List[LocationCondition],
                                 plan_scores: Dict[str, float],
                                 preferences: TravelPreference,
                                 poi_recommendations: Dict[str, List[Dict]] = None) -> Tuple[List[str], List[str]]:
        """生成智能建议和调整方案"""
        recommendations = []
        adjustments = []
        
        # 整体方案评估
        overall_score = plan_scores['overall_score']
        
        if overall_score >= 85:
            recommendations.append("🌟 方案评级：优秀！所有条件都很理想，强烈推荐按计划出行")
        elif overall_score >= 70:
            recommendations.append("👍 方案评级：良好，条件较为理想，推荐出行")
        elif overall_score >= 55:
            recommendations.append("👌 方案评级：一般，可以出行但建议关注调整建议")
        else:
            recommendations.append("⚠️ 方案评级：需要调整，建议考虑调整方案")
            adjustments.append("建议重新规划或推迟出行")
        
        # 基于天气的建议
        if plan_scores['weather_score'] < 50:
            recommendations.append("🌦️ 天气状况较差，建议携带雨具或防护用品")
            adjustments.append("考虑选择室内景点或调整出行日期")
        
        # 基于交通的建议
        if plan_scores['traffic_score'] < 60:
            recommendations.append("🚦 部分路段可能拥堵，建议预留额外时间")
            adjustments.append("考虑错峰出行或选择公共交通")
        
        # 基于人流的建议
        if plan_scores['crowd_score'] < 50:
            recommendations.append("👥 部分景点人流密集，建议错峰游览")
            adjustments.append("考虑调整游览顺序或选择人少的替代景点")
        
        # 具体地点建议
        for location in location_conditions:
            if location.crowd_level == CrowdLevel.VERY_HIGH:
                adjustments.append(f"建议避开 {location.location} 的高峰时段或选择替代景点")
            
            if location.weather_condition == WeatherCondition.EXTREME:
                adjustments.append(f"{location.location} 天气极端恶劣，强烈建议取消或推迟")
        
        # 基于用户偏好的个性化建议
        if preferences.budget_conscious:
            total_tolls = sum(
                route.route_info.get('tolls_value', 0) 
                for route in route_conditions 
                if isinstance(route.route_info, dict)
            )
            if total_tolls > 50:
                recommendations.append(f"💰 总过路费约{total_tolls}元，已为您优化最经济路线")
        
        if preferences.time_conscious:
            total_duration = sum(route.estimated_duration for route in route_conditions)
            recommendations.append(f"⏱️ 总预计行程时间：{total_duration}分钟")
        
        # POI推荐
        if poi_recommendations:
            poi_summary = []
            for destination, pois in poi_recommendations.items():
                restaurant_count = len(pois.get("restaurants", []))
                shopping_count = len(pois.get("shopping", []))
                attraction_count = len(pois.get("attractions", []))
                
                if restaurant_count > 0:
                    poi_summary.append(f"{destination}周边有{restaurant_count}家餐厅")
                if shopping_count > 0:
                    poi_summary.append(f"{destination}周边有{shopping_count}个购物点")
                if attraction_count > 0:
                    poi_summary.append(f"{destination}周边有{attraction_count}个景点")
            
            if poi_summary:
                recommendations.append("🍽️ " + "；".join(poi_summary[:3]))  # 只显示前3个
        
        return recommendations, adjustments
    
    def ask_user_preferences(self, plan: TravelPlan) -> Dict[str, Any]:
        """询问用户具体偏好信息（用于多次调整）"""
        questions = []
        
        # 基于方案得分生成针对性问题
        if plan.weather_compatibility < 70:
            questions.append({
                'type': 'weather_tolerance',
                'question': '检测到天气状况不佳，您是否愿意在恶劣天气下出行？',
                'options': ['完全接受', '可以接受', '尽量避免', '完全不接受']
            })
        
        if plan.traffic_score < 60:
            questions.append({
                'type': 'traffic_tolerance', 
                'question': '部分路段可能拥堵，您更偏好哪种出行方式？',
                'options': ['时间优先(快速路线)', '费用优先(省钱路线)', '舒适优先(避开拥堵)', '平衡选择']
            })
        
        if plan.crowd_score < 50:
            questions.append({
                'type': 'crowd_tolerance',
                'question': '一些景点人流较多，您的游览偏好是？',
                'options': ['不介意人多', '适中人流即可', '偏好人少景点', '必须避开人群']
            })
        
        # 时间偏好
        questions.append({
            'type': 'time_preference',
            'question': '您更倾向于什么时间段出行？',
            'options': ['早上(避开人流)', '上午(黄金时段)', '下午(错峰出行)', '傍晚(欣赏夜景)']
        })
        
        return {
            'plan_id': plan.plan_id,
            'questions': questions,
            'current_score': plan.overall_score,
            'adjustment_needed': plan.overall_score < 70
        }
    
    def adjust_plan_by_preferences(self, plan: TravelPlan, user_answers: Dict[str, str]) -> TravelPlan:
        """根据用户偏好调整方案"""
        logger.info(f"🔄 根据用户反馈调整旅游方案: {plan.plan_id}")
        
        # 解析用户偏好
        new_preferences = TravelPreference()
        
        if 'weather_tolerance' in user_answers:
            tolerance_map = {
                '完全接受': WeatherCondition.EXTREME,
                '可以接受': WeatherCondition.POOR,
                '尽量避免': WeatherCondition.MODERATE,
                '完全不接受': WeatherCondition.GOOD
            }
            new_preferences.weather_tolerance = tolerance_map.get(user_answers['weather_tolerance'], WeatherCondition.MODERATE)
        
        if 'traffic_tolerance' in user_answers:
            if user_answers['traffic_tolerance'] == '时间优先(快速路线)':
                new_preferences.time_conscious = True
            elif user_answers['traffic_tolerance'] == '费用优先(省钱路线)':
                new_preferences.budget_conscious = True
            elif user_answers['traffic_tolerance'] == '舒适优先(避开拥堵)':
                new_preferences.comfort_priority = True
        
        # 重新规划路线
        adjusted_routes = self._plan_optimal_routes(plan.origin, plan.destinations, new_preferences)
        adjusted_routes = self._optimize_routes_by_traffic(adjusted_routes, new_preferences)
        
        # 重新计算得分
        new_scores = self._calculate_plan_scores(adjusted_routes, plan.location_conditions, new_preferences)
        
        # 生成新的建议
        new_recommendations, new_adjustments = self._generate_recommendations(
            adjusted_routes, plan.location_conditions, new_scores, new_preferences
        )
        
        # 创建调整后的计划
        adjusted_plan = TravelPlan(
            plan_id=f"{plan.plan_id}_adjusted_{len(self.user_feedback_history) + 1}",
            origin=plan.origin,
            destinations=plan.destinations,
            route_conditions=adjusted_routes,
            location_conditions=plan.location_conditions,
            total_duration=sum(route.estimated_duration for route in adjusted_routes),
            total_distance=sum(route.route_info.get('distance_value', 0) for route in adjusted_routes) / 1000,
            weather_compatibility=new_scores['weather_score'],
            traffic_score=new_scores['traffic_score'],
            crowd_score=new_scores['crowd_score'],
            overall_score=new_scores['overall_score'],
            recommendations=new_recommendations,
            adjustments=new_adjustments,
            timestamp=datetime.now().isoformat()
        )
        
        # 记录用户反馈
        self.user_feedback_history.append({
            'original_plan_id': plan.plan_id,
            'adjusted_plan_id': adjusted_plan.plan_id,
            'user_answers': user_answers,
            'score_improvement': adjusted_plan.overall_score - plan.overall_score,
            'timestamp': datetime.now().isoformat()
        })
        
        logger.info(f"✅ 方案调整完成，得分变化: {plan.overall_score:.1f} → {adjusted_plan.overall_score:.1f}")
        
        return adjusted_plan
    
    def integrate_with_rag(self, plan: TravelPlan, rag_knowledge: Dict[str, Any]) -> TravelPlan:
        """结合RAG进一步优化方案 (此处为接口，具体RAG集成需要额外实现)"""
        logger.info(f"🧠 正在结合RAG知识库优化旅游方案: {plan.plan_id}")
        
        # RAG优化建议 (示例结构)
        rag_suggestions = rag_knowledge.get('suggestions', [])
        rag_alternative_destinations = rag_knowledge.get('alternative_destinations', [])
        rag_local_insights = rag_knowledge.get('local_insights', [])
        
        enhanced_recommendations = list(plan.recommendations)
        enhanced_adjustments = list(plan.adjustments)
        
        # 整合RAG建议
        if rag_suggestions:
            enhanced_recommendations.extend([f"🧠 RAG建议: {suggestion}" for suggestion in rag_suggestions])
        
        if rag_alternative_destinations:
            enhanced_adjustments.extend([f"🗺️ 替代景点推荐: {dest}" for dest in rag_alternative_destinations])
        
        if rag_local_insights:
            enhanced_recommendations.extend([f"💡 当地人推荐: {insight}" for insight in rag_local_insights])
        
        # 创建RAG增强的计划
        rag_enhanced_plan = TravelPlan(
            plan_id=f"{plan.plan_id}_rag_enhanced",
            origin=plan.origin,
            destinations=plan.destinations,
            route_conditions=plan.route_conditions,
            location_conditions=plan.location_conditions,
            total_duration=plan.total_duration,
            total_distance=plan.total_distance,
            weather_compatibility=plan.weather_compatibility,
            traffic_score=plan.traffic_score,
            crowd_score=plan.crowd_score,
            overall_score=min(plan.overall_score + 5, 100),  # RAG可以略微提升得分
            recommendations=enhanced_recommendations,
            adjustments=enhanced_adjustments,
            timestamp=datetime.now().isoformat()
        )
        
        logger.info("✅ RAG知识库整合完成，方案进一步优化")
        
        return rag_enhanced_plan
    
    def _get_poi_recommendations(self, destinations: List[str]) -> Dict[str, List[Dict]]:
        """获取目的地周边POI推荐"""
        poi_recommendations = {}
        
        for destination in destinations:
            try:
                # 获取旅游相关的POI推荐
                poi_result = self.mcp_manager.get_poi_recommendations_for_travel(destination, "tourism")
                
                if poi_result.get("api_source") == "amap_poi_search":
                    pois = poi_result.get("pois", [])
                    
                    # 按类型分类POI
                    categorized_pois = {
                        "restaurants": [],
                        "shopping": [],
                        "attractions": [],
                        "transport": []
                    }
                    
                    for poi in pois[:15]:  # 取前15个
                        typecode = poi.get("typecode", "")
                        if typecode.startswith("05"):  # 餐饮
                            categorized_pois["restaurants"].append(poi)
                        elif typecode.startswith("06"):  # 购物
                            categorized_pois["shopping"].append(poi)
                        elif typecode.startswith("11"):  # 景点
                            categorized_pois["attractions"].append(poi)
                        elif typecode.startswith("15"):  # 交通
                            categorized_pois["transport"].append(poi)
                    
                    poi_recommendations[destination] = categorized_pois
                    logger.info(f"为 {destination} 获取到 {len(pois)} 个POI推荐")
                else:
                    poi_recommendations[destination] = {
                        "restaurants": [],
                        "shopping": [],
                        "attractions": [],
                        "transport": []
                    }
                    
            except Exception as e:
                logger.warning(f"获取 {destination} POI推荐失败: {e}")
                poi_recommendations[destination] = {
                    "restaurants": [],
                    "shopping": [],
                    "attractions": [],
                    "transport": []
                }
        
        return poi_recommendations
    
    def format_travel_plan(self, plan: TravelPlan) -> str:
        """格式化显示旅游攻略"""
        output = []
        
        # 标题和基本信息
        output.append(f"🎯 智能旅游攻略 - {plan.plan_id}")
        output.append("=" * 50)
        output.append(f"📍 行程: {plan.origin} → {' → '.join(plan.destinations)}")
        output.append(f"🕐 总用时: {plan.total_duration}分钟")
        output.append(f"📏 总距离: {plan.total_distance:.1f}公里")
        output.append(f"⭐ 方案得分: {plan.overall_score:.1f}/100")
        output.append("")
        
        # 各项得分
        output.append("📊 详细评分:")
        output.append(f"  🌤️ 天气适宜度: {plan.weather_compatibility:.1f}/100")
        output.append(f"  🚦 交通便利度: {plan.traffic_score:.1f}/100")
        output.append(f"  👥 人流舒适度: {plan.crowd_score:.1f}/100")
        output.append("")
        
        # 路线详情
        output.append("🗺️ 路线详情:")
        for i, route in enumerate(plan.route_conditions):
            output.append(f"  {i+1}. {route.origin} → {route.destination}")
            if 'distance' in route.route_info:
                output.append(f"     距离: {route.route_info.get('distance', '未知')}")
                output.append(f"     用时: {route.estimated_duration}分钟")
                output.append(f"     路况: {route.traffic_condition.value}")
                output.append(f"     建议: {route.recommendation}")
            else:
                output.append(f"     状态: 路线信息获取失败")
            output.append("")
        
        # 景点状况
        output.append("🏞️ 景点状况:")
        for location in plan.location_conditions:
            output.append(f"  📍 {location.location}")
            output.append(f"     天气: {location.weather_condition.value}")
            output.append(f"     人流: {location.crowd_level.value}")
            output.append(f"     可达性: {location.accessibility}")
            output.append(f"     建议: {location.recommendation}")
            output.append("")
        
        # 智能建议
        if plan.recommendations:
            output.append("💡 智能建议:")
            for rec in plan.recommendations:
                output.append(f"  • {rec}")
            output.append("")
        
        # 调整方案
        if plan.adjustments:
            output.append("🔄 优化建议:")
            for adj in plan.adjustments:
                output.append(f"  • {adj}")
            output.append("")
        
        output.append(f"📅 方案生成时间: {plan.timestamp}")
        
        return "\n".join(output)
