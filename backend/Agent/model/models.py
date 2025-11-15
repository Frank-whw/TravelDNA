"""
Agent模型数据结构
"""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from enum import Enum


class WeatherCondition(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    MODERATE = "moderate"
    POOR = "poor"


class TrafficCondition(Enum):
    SMOOTH = "smooth"
    SLOW = "slow"
    CONGESTED = "congested"
    SEVERE = "severe"


class CrowdLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


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
    mcp_services: List[Any]  # MCPServiceType
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
    user_memory: Dict[str, Any] = None  # 用户记忆（偏好沉淀）
    iteration_count: int = 0  # 迭代次数
    feedback_history: List[Dict] = None  # 反馈历史
    
    def __post_init__(self):
        if self.thought_process is None:
            self.thought_process = []
        if self.user_memory is None:
            self.user_memory = {
                "stable_preferences": {},  # 稳定偏好（3次以上）
                "recent_choices": [],  # 最近选择
                "avoid_items": []  # 明确拒绝的项目
            }
        if self.feedback_history is None:
            self.feedback_history = []

