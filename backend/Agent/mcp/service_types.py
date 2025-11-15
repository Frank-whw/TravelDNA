"""
MCP服务类型定义
"""
from enum import Enum


class MCPServiceType(Enum):
    """MCP服务类型"""
    WEATHER = "weather"      # 天气服务
    POI = "poi"              # POI服务（景点、餐厅等）
    NAVIGATION = "navigation"  # 导航服务
    TRAFFIC = "traffic"      # 交通路况服务
    CROWD = "crowd"          # 人流服务

