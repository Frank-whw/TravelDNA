"""
MCP (Model Context Protocol) 服务模块
提供天气、POI、导航、交通、人流等实时数据服务
"""
from .service_types import MCPServiceType
from .mcp_client import MCPClient
from .service import WeatherService, POIService, NavigationService, TrafficService, CrowdService
from .models import WeatherInfo, RouteInfo, POIInfo, TrafficInfo, CrowdInfo

__all__ = [
    'MCPServiceType',
    'MCPClient',
    'WeatherService',
    'POIService',
    'NavigationService',
    'TrafficService',
    'CrowdService',
    'WeatherInfo',
    'RouteInfo',
    'POIInfo',
    'TrafficInfo',
    'CrowdInfo'
]

