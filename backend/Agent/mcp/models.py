"""
MCP服务数据模型
"""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional


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
    address: str = ""
    rating: float = 0.0
    business_hours: str = ""
    price: str = ""
    distance: str = ""
    category: str = ""
    reviews: List[str] = None
    
    def __post_init__(self):
        if self.reviews is None:
            self.reviews = []


@dataclass
class TrafficInfo:
    """交通路况信息"""
    status: str
    description: str
    evaluation: Dict[str, Any]
    timestamp: str


@dataclass
class CrowdInfo:
    """人流信息"""
    level: str
    description: str
    recommendation: str

