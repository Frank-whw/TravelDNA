"""
智能旅游规划Agent系统
基于思考链的先进AI旅游规划系统，具备人文关怀和数据驱动决策能力
"""

from .enhanced_travel_agent import EnhancedTravelAgent
from .config import get_api_key, get_config, API_KEYS, AMAP_CONFIG

__version__ = "1.0.0"
__author__ = "Enhanced Travel Agent Team"

__all__ = [
    "EnhancedTravelAgent",
    "get_api_key",
    "get_config",
    "API_KEYS",
    "AMAP_CONFIG"
]

