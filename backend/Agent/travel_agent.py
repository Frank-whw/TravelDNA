#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能旅游Agent核心服务
提供旅游规划、路线优化、智能推荐等功能
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config

class WeatherCondition(Enum):
    """天气状况枚举"""
    EXCELLENT = "excellent"  # 优秀
    GOOD = "good"           # 良好
    FAIR = "fair"           # 一般
    POOR = "poor"           # 较差

class TrafficCondition(Enum):
    """交通状况枚举"""
    SMOOTH = "smooth"       # 畅通
    SLOW = "slow"           # 缓慢
    CONGESTED = "congested" # 拥堵
    SEVERE = "severe"       # 严重拥堵

class CrowdLevel(Enum):
    """人流密度枚举"""
    LOW = "low"             # 人少
    MEDIUM = "medium"       # 适中
    HIGH = "high"           # 人多
    VERY_HIGH = "very_high" # 非常拥挤

@dataclass
class TravelPreference:
    """用户旅游偏好"""
    weather_tolerance: WeatherCondition = WeatherCondition.GOOD
    traffic_tolerance: TrafficCondition = TrafficCondition.SLOW
    crowd_tolerance: CrowdLevel = CrowdLevel.MEDIUM
    time_conscious: bool = False        # 时间敏感
    budget_conscious: bool = False      # 预算敏感
    comfort_priority: bool = False      # 舒适优先
    cultural_interest: bool = True      # 文化兴趣
    nature_preference: bool = False     # 自然偏好
    food_lover: bool = True            # 美食爱好
    photography_enthusiast: bool = False # 摄影爱好

@dataclass
class POIInfo:
    """景点信息"""
    name: str
    address: str = ""
    rating: float = 0.0
    category: str = ""
    description: str = ""
    coordinates: Dict[str, float] = field(default_factory=dict)
    opening_hours: str = ""
    ticket_price: float = 0.0
    visit_duration: int = 120  # 建议游览时间(分钟)
    crowd_level: CrowdLevel = CrowdLevel.MEDIUM
    weather_dependency: bool = False  # 是否依赖天气

@dataclass
class RouteSegment:
    """路线段信息"""
    from_poi: str
    to_poi: str
    distance: float = 0.0      # 距离(公里)
    duration: int = 0          # 时间(分钟)
    transport_mode: str = "walking"
    traffic_condition: TrafficCondition = TrafficCondition.SMOOTH
    cost: float = 0.0          # 费用

@dataclass
class TravelPlan:
    """旅游计划"""
    id: str
    origin: str
    destinations: List[str]
    pois: List[POIInfo] = field(default_factory=list)
    route_segments: List[RouteSegment] = field(default_factory=list)
    total_distance: float = 0.0
    total_duration: int = 0
    total_cost: float = 0.0
    weather_compatibility: float = 0.0  # 天气适宜度(0-100)
    traffic_score: float = 0.0          # 交通便利度(0-100)
    crowd_score: float = 0.0            # 人流舒适度(0-100)
    overall_score: float = 0.0          # 综合评分(0-100)
    recommendations: List[str] = field(default_factory=list)
    adjustments: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

class TravelAgentService:
    """智能旅游Agent服务"""
    
    def __init__(self):
        self.config = Config()
        self._load_poi_data()
    
    def _load_poi_data(self):
        """加载POI数据"""
        self.poi_database = {
            "外滩": POIInfo(
                name="外滩",
                address="上海市黄浦区中山东一路",
                rating=4.6,
                category="观光景点",
                description="上海标志性景点，黄浦江畔的万国建筑博览群",
                coordinates={"lat": 31.2396, "lng": 121.4994},
                opening_hours="全天开放",
                visit_duration=90,
                crowd_level=CrowdLevel.HIGH,
                weather_dependency=True
            ),
            "东方明珠": POIInfo(
                name="东方明珠",
                address="上海市浦东新区世纪大道1号",
                rating=4.4,
                category="观光塔",
                description="上海地标性建筑，可俯瞰整个上海市区",
                coordinates={"lat": 31.2397, "lng": 121.4994},
                opening_hours="08:00-21:30",
                ticket_price=180.0,
                visit_duration=120,
                crowd_level=CrowdLevel.HIGH
            ),
            "豫园": POIInfo(
                name="豫园",
                address="上海市黄浦区福佑路168号",
                rating=4.3,
                category="古典园林",
                description="明代古典园林，体验传统江南园林文化",
                coordinates={"lat": 31.2270, "lng": 121.4920},
                opening_hours="08:30-17:30",
                ticket_price=40.0,
                visit_duration=90,
                crowd_level=CrowdLevel.MEDIUM
            ),
            "南京路步行街": POIInfo(
                name="南京路步行街",
                address="上海市黄浦区南京东路",
                rating=4.2,
                category="购物街区",
                description="中华商业第一街，购物和美食的天堂",
                coordinates={"lat": 31.2342, "lng": 121.4753},
                opening_hours="全天开放",
                visit_duration=150,
                crowd_level=CrowdLevel.VERY_HIGH
            ),
            "人民广场": POIInfo(
                name="人民广场",
                address="上海市黄浦区人民大道",
                rating=4.1,
                category="城市广场",
                description="上海市中心，周边有博物馆、大剧院等文化设施",
                coordinates={"lat": 31.2304, "lng": 121.4737},
                opening_hours="全天开放",
                visit_duration=60,
                crowd_level=CrowdLevel.HIGH
            )
        }
    
    def create_travel_plan(
        self, 
        origin: str, 
        destinations: List[str],
        user_preferences: Optional[TravelPreference] = None
    ) -> TravelPlan:
        """创建旅游计划"""
        if user_preferences is None:
            user_preferences = TravelPreference()
        
        # 生成计划ID
        plan_id = f"plan_{int(time.time())}"
        
        # 创建基础计划
        plan = TravelPlan(
            id=plan_id,
            origin=origin,
            destinations=destinations
        )
        
        # 获取POI信息
        plan.pois = self._get_poi_info(destinations)
        
        # 规划路线
        plan.route_segments = self._plan_route(origin, destinations)
        
        # 计算基础指标
        self._calculate_basic_metrics(plan)
        
        # 评估天气适宜度
        plan.weather_compatibility = self._evaluate_weather_compatibility(plan, user_preferences)
        
        # 评估交通便利度
        plan.traffic_score = self._evaluate_traffic_score(plan, user_preferences)
        
        # 评估人流舒适度
        plan.crowd_score = self._evaluate_crowd_score(plan, user_preferences)
        
        # 计算综合评分
        plan.overall_score = self._calculate_overall_score(plan)
        
        # 生成建议
        plan.recommendations = self._generate_recommendations(plan, user_preferences)
        
        # 生成调整建议
        plan.adjustments = self._generate_adjustments(plan, user_preferences)
        
        return plan
    
    def _get_poi_info(self, destinations: List[str]) -> List[POIInfo]:
        """获取POI信息"""
        pois = []
        for dest in destinations:
            if dest in self.poi_database:
                pois.append(self.poi_database[dest])
            else:
                # 创建默认POI信息
                pois.append(POIInfo(
                    name=dest,
                    rating=4.0,
                    category="景点",
                    visit_duration=90
                ))
        return pois
    
    def _plan_route(self, origin: str, destinations: List[str]) -> List[RouteSegment]:
        """规划路线"""
        segments = []
        current_location = origin
        
        for dest in destinations:
            segment = RouteSegment(
                from_poi=current_location,
                to_poi=dest,
                distance=self._calculate_distance(current_location, dest),
                duration=self._estimate_travel_time(current_location, dest),
                transport_mode="地铁",
                cost=self._estimate_cost(current_location, dest)
            )
            segments.append(segment)
            current_location = dest
        
        return segments
    
    def _calculate_distance(self, from_poi: str, to_poi: str) -> float:
        """计算距离(模拟)"""
        # 简单的距离估算，实际应该调用地图API
        import random
        return round(random.uniform(1.0, 8.0), 1)
    
    def _estimate_travel_time(self, from_poi: str, to_poi: str) -> int:
        """估算旅行时间(模拟)"""
        # 简单的时间估算，实际应该调用导航API
        import random
        return random.randint(15, 45)
    
    def _estimate_cost(self, from_poi: str, to_poi: str) -> float:
        """估算费用(模拟)"""
        # 简单的费用估算
        import random
        return round(random.uniform(3.0, 15.0), 1)
    
    def _calculate_basic_metrics(self, plan: TravelPlan):
        """计算基础指标"""
        plan.total_distance = sum(segment.distance for segment in plan.route_segments)
        plan.total_duration = sum(segment.duration for segment in plan.route_segments) + \
                             sum(poi.visit_duration for poi in plan.pois)
        plan.total_cost = sum(segment.cost for segment in plan.route_segments) + \
                         sum(poi.ticket_price for poi in plan.pois)
    
    def _evaluate_weather_compatibility(self, plan: TravelPlan, preferences: TravelPreference) -> float:
        """评估天气适宜度"""
        # 模拟天气评估
        base_score = 75.0
        
        # 根据天气依赖性调整
        weather_dependent_pois = sum(1 for poi in plan.pois if poi.weather_dependency)
        if weather_dependent_pois > 0:
            base_score -= weather_dependent_pois * 5
        
        # 根据用户天气容忍度调整
        if preferences.weather_tolerance == WeatherCondition.EXCELLENT:
            base_score += 10
        elif preferences.weather_tolerance == WeatherCondition.POOR:
            base_score -= 10
        
        return max(0, min(100, base_score))
    
    def _evaluate_traffic_score(self, plan: TravelPlan, preferences: TravelPreference) -> float:
        """评估交通便利度"""
        base_score = 80.0
        
        # 根据总距离调整
        if plan.total_distance > 20:
            base_score -= 15
        elif plan.total_distance < 10:
            base_score += 10
        
        # 根据用户偏好调整
        if preferences.time_conscious:
            base_score += 5
        if preferences.comfort_priority:
            base_score += 5
        
        return max(0, min(100, base_score))
    
    def _evaluate_crowd_score(self, plan: TravelPlan, preferences: TravelPreference) -> float:
        """评估人流舒适度"""
        base_score = 70.0
        
        # 根据景点人流密度调整
        high_crowd_pois = sum(1 for poi in plan.pois if poi.crowd_level in [CrowdLevel.HIGH, CrowdLevel.VERY_HIGH])
        base_score -= high_crowd_pois * 8
        
        # 根据用户人流容忍度调整
        if preferences.crowd_tolerance == CrowdLevel.LOW:
            base_score -= 10
        elif preferences.crowd_tolerance == CrowdLevel.VERY_HIGH:
            base_score += 10
        
        return max(0, min(100, base_score))
    
    def _calculate_overall_score(self, plan: TravelPlan) -> float:
        """计算综合评分"""
        weights = {
            'weather': 0.25,
            'traffic': 0.35,
            'crowd': 0.25,
            'poi_quality': 0.15
        }
        
        poi_quality_score = sum(poi.rating * 20 for poi in plan.pois) / len(plan.pois) if plan.pois else 80
        
        overall = (
            plan.weather_compatibility * weights['weather'] +
            plan.traffic_score * weights['traffic'] +
            plan.crowd_score * weights['crowd'] +
            poi_quality_score * weights['poi_quality']
        )
        
        return round(overall, 1)
    
    def _generate_recommendations(self, plan: TravelPlan, preferences: TravelPreference) -> List[str]:
        """生成智能建议"""
        recommendations = []
        
        # 基于时间的建议
        if plan.total_duration > 480:  # 超过8小时
            recommendations.append("行程较长，建议分两天完成或减少景点")
        
        # 基于人流的建议
        high_crowd_pois = [poi.name for poi in plan.pois if poi.crowd_level == CrowdLevel.VERY_HIGH]
        if high_crowd_pois:
            recommendations.append(f"建议避开周末和节假日游览{', '.join(high_crowd_pois)}")
        
        # 基于天气的建议
        outdoor_pois = [poi.name for poi in plan.pois if poi.weather_dependency]
        if outdoor_pois:
            recommendations.append("建议关注天气预报，携带雨具和防晒用品")
        
        # 基于费用的建议
        if plan.total_cost > 200:
            recommendations.append("可考虑购买景点联票或使用优惠券节省费用")
        
        return recommendations
    
    def _generate_adjustments(self, plan: TravelPlan, preferences: TravelPreference) -> List[str]:
        """生成优化建议"""
        adjustments = []
        
        if plan.overall_score < 70:
            adjustments.append("建议调整行程安排以提高整体体验")
        
        if plan.crowd_score < 60:
            adjustments.append("可考虑选择人流较少的时间段或替代景点")
        
        if plan.traffic_score < 60:
            adjustments.append("建议优化交通路线或选择其他交通方式")
        
        return adjustments
    
    def ask_user_preferences(self, plan: TravelPlan) -> Dict:
        """生成用户偏好问题"""
        questions = {
            'questions': [
                {
                    'key': 'weather_tolerance',
                    'question': '您对天气条件的要求如何？',
                    'options': ['必须晴天', '可以接受', '无所谓']
                },
                {
                    'key': 'traffic_tolerance',
                    'question': '您对交通方式的偏好？',
                    'options': ['时间优先(快速到达)', '舒适优先(避开拥堵)', '费用优先(经济实惠)']
                },
                {
                    'key': 'crowd_tolerance',
                    'question': '您对景点人流的容忍度？',
                    'options': ['偏好人少景点', '适中即可', '不介意人多']
                },
                {
                    'key': 'time_preference',
                    'question': '您偏好的出行时间？',
                    'options': ['早上(避开人流)', '下午(光线较好)', '傍晚(欣赏夜景)']
                }
            ]
        }
        return questions
    
    def adjust_plan_by_preferences(self, plan: TravelPlan, user_answers: Dict) -> TravelPlan:
        """根据用户偏好调整计划"""
        # 创建新的偏好对象
        preferences = TravelPreference()
        
        # 解析用户回答
        if user_answers.get('weather_tolerance') == '必须晴天':
            preferences.weather_tolerance = WeatherCondition.EXCELLENT
        elif user_answers.get('weather_tolerance') == '无所谓':
            preferences.weather_tolerance = WeatherCondition.POOR
        
        if user_answers.get('traffic_tolerance') == '时间优先(快速到达)':
            preferences.time_conscious = True
        elif user_answers.get('traffic_tolerance') == '舒适优先(避开拥堵)':
            preferences.comfort_priority = True
        elif user_answers.get('traffic_tolerance') == '费用优先(经济实惠)':
            preferences.budget_conscious = True
        
        if user_answers.get('crowd_tolerance') == '偏好人少景点':
            preferences.crowd_tolerance = CrowdLevel.LOW
        elif user_answers.get('crowd_tolerance') == '不介意人多':
            preferences.crowd_tolerance = CrowdLevel.VERY_HIGH
        
        # 重新计算评分
        plan.weather_compatibility = self._evaluate_weather_compatibility(plan, preferences)
        plan.traffic_score = self._evaluate_traffic_score(plan, preferences)
        plan.crowd_score = self._evaluate_crowd_score(plan, preferences)
        plan.overall_score = self._calculate_overall_score(plan)
        
        # 重新生成建议
        plan.recommendations = self._generate_recommendations(plan, preferences)
        plan.adjustments = self._generate_adjustments(plan, preferences)
        
        return plan