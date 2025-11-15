"""
MCP客户端 - 统一管理所有MCP服务
"""
import logging
from typing import List, Dict, Any, Optional
from threading import Lock

from .service_types import MCPServiceType
from .service import WeatherService, POIService, NavigationService, TrafficService, CrowdService
from .models import WeatherInfo, RouteInfo, POIInfo, TrafficInfo, CrowdInfo

logger = logging.getLogger(__name__)


class MCPClient:
    """MCP客户端 - 统一管理所有MCP服务"""
    
    def __init__(self, api_lock: Lock = None, last_api_call: Dict = None, 
                 min_interval: float = 0.35, qunar_places=None):
        """
        初始化MCP客户端
        
        Args:
            api_lock: API锁（用于限流）
            last_api_call: 最后调用时间记录
            min_interval: 最小调用间隔（秒）
            qunar_places: 去哪儿景点数据（DataFrame）
        """
        self._api_lock = api_lock or Lock()
        self._last_api_call = last_api_call or {}
        self._min_interval = min_interval
        
        # 初始化各个服务
        self.weather_service = WeatherService(self._api_lock, self._last_api_call, self._min_interval)
        self.poi_service = POIService(self._api_lock, self._last_api_call, self._min_interval, qunar_places)
        self.navigation_service = NavigationService(self._api_lock, self._last_api_call, self._min_interval)
        self.traffic_service = TrafficService(self._api_lock, self._last_api_call, self._min_interval)
        self.crowd_service = CrowdService(self._api_lock, self._last_api_call, self._min_interval)
    
    def call_service(self, service_type: MCPServiceType, **kwargs) -> Any:
        """
        调用指定的MCP服务
        
        Args:
            service_type: 服务类型
            **kwargs: 服务参数
            
        Returns:
            服务返回结果
        """
        try:
            if service_type == MCPServiceType.WEATHER:
                city = kwargs.get('city', '上海')
                date = kwargs.get('date')
                return self.weather_service.get_weather(city, date)
            
            elif service_type == MCPServiceType.POI:
                keyword = kwargs.get('keyword', '')
                city = kwargs.get('city', '上海')
                category = kwargs.get('category')
                return self.poi_service.search_poi(keyword, city, category)
            
            elif service_type == MCPServiceType.NAVIGATION:
                origin = kwargs.get('origin', '')
                destination = kwargs.get('destination', '')
                transport_mode = kwargs.get('transport_mode', 'driving')
                return self.navigation_service.get_navigation_routes(origin, destination, transport_mode)
            
            elif service_type == MCPServiceType.TRAFFIC:
                area = kwargs.get('area', '上海')
                return self.traffic_service.get_traffic_status(area)
            
            elif service_type == MCPServiceType.CROWD:
                location = kwargs.get('location', '上海')
                return self.crowd_service.get_crowd_info(location)
            
            else:
                logger.warning(f"未知的服务类型: {service_type}")
                return None
                
        except Exception as e:
            logger.error(f"MCP服务调用失败 {service_type.value}: {e}")
            return None
    
    def call_services(self, service_types: List[MCPServiceType], **kwargs) -> Dict[str, Any]:
        """
        批量调用多个MCP服务
        
        Args:
            service_types: 服务类型列表
            **kwargs: 服务参数（会被传递给各个服务）
            
        Returns:
            服务结果字典
        """
        results = {}
        
        for service_type in service_types:
            try:
                result = self.call_service(service_type, **kwargs)
                results[service_type.value] = result
            except Exception as e:
                logger.error(f"调用服务 {service_type.value} 失败: {e}")
                results[service_type.value] = None
        
        return results
    
    def map_api_needs_to_services(self, api_needs: List[str]) -> List[MCPServiceType]:
        """
        将API需求映射到MCP服务类型
        
        Args:
            api_needs: API需求列表（如["天气", "景点"]）
            
        Returns:
            MCP服务类型列表
        """
        mapping = {
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
            need_lower = need.lower()
            if need_lower in mapping:
                service = mapping[need_lower]
                if service not in services:
                    services.append(service)
        
        return services

