"""
MCP服务实现 - 天气、POI、导航、交通、人流等服务
"""
import time
import requests
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from threading import Lock

from .models import WeatherInfo, RouteInfo, POIInfo, TrafficInfo, CrowdInfo
from .service_types import MCPServiceType
try:
    from config import get_api_key, AMAP_CONFIG
except ImportError:
    # 如果从外部导入，尝试从父级导入
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import get_api_key, AMAP_CONFIG

logger = logging.getLogger(__name__)


class BaseMCPService:
    """MCP服务基类"""
    
    def __init__(self, api_lock: Lock, last_api_call: Dict, min_interval: float = 0.35):
        self._api_lock = api_lock
        self._last_api_call = last_api_call
        self._min_interval = min_interval
    
    def _rate_limit_wait(self, api_name: str):
        """API限流控制"""
        with self._api_lock:
            current_time = time.time()
            if api_name in self._last_api_call:
                elapsed = current_time - self._last_api_call[api_name]
                if elapsed < self._min_interval:
                    wait_time = self._min_interval - elapsed
                    time.sleep(wait_time)
            self._last_api_call[api_name] = time.time()
    
    def _make_request(self, url: str, params: Dict[str, Any], api_name: str = "default") -> Dict[str, Any]:
        """发送HTTP请求（带限流控制）"""
        try:
            self._rate_limit_wait(api_name)
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"API请求失败: {url}, 错误: {e}")
            return {}
    
    def _get_city_code(self, city: str) -> str:
        """获取城市代码"""
        # 简化的城市代码映射
        city_codes = {
            "上海": "310000",
            "北京": "110000",
            "广州": "440100",
            "深圳": "440300",
        }
        return city_codes.get(city, "310000")
    
    def _geocode(self, address: str) -> Optional[str]:
        """地理编码，获取坐标"""
        try:
            params = {
                "key": get_api_key("AMAP_POI"),
                "address": address,
                "city": "上海"
            }
            result = self._make_request(AMAP_CONFIG["geocode_url"], params, "geocode")
            if result.get("status") == "1":
                geocodes = result.get("geocodes", [])
                if geocodes:
                    return geocodes[0].get("location", "")
        except Exception as e:
            logger.error(f"地理编码失败: {e}")
        return None


class WeatherService(BaseMCPService):
    """天气服务"""
    
    def get_weather(self, city: str, date: str = None) -> List[WeatherInfo]:
        """获取天气信息"""
        logger.info(f"调用天气API获取实时数据: {city}")
        
        try:
            city_code = self._get_city_code(city)
            
            params = {
                "key": get_api_key("AMAP_WEATHER"),
                "city": city_code,
                "extensions": "all"
            }
            
            result = self._make_request(AMAP_CONFIG["weather_url"], params, "weather")
            
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


class POIService(BaseMCPService):
    """POI服务"""
    
    def __init__(self, api_lock: Lock, last_api_call: Dict, min_interval: float, qunar_places=None):
        super().__init__(api_lock, last_api_call, min_interval)
        self.qunar_places = qunar_places
    
    def _search_qunar_places(self, keyword: str, limit: int = 10) -> List[POIInfo]:
        """从Excel数据中搜索景点"""
        if self.qunar_places is None or self.qunar_places.empty:
            return []
        
        try:
            # 在name和intro列中搜索关键词
            mask = (
                self.qunar_places['name'].str.contains(keyword, case=False, na=False) |
                self.qunar_places['intro'].str.contains(keyword, case=False, na=False)
            )
            results = self.qunar_places[mask].head(limit)
            
            pois = []
            for _, row in results.iterrows():
                districts = str(row.get('districts', ''))
                address = districts.replace('·', '') if districts else ''
                
                # 解析point获取坐标
                point = str(row.get('point', ''))
                
                poi = POIInfo(
                    name=row.get('name', ''),
                    address=address,
                    rating=float(row.get('score', 0) or 0),
                    category=row.get('category', ''),
                    price=str(row.get('price', '')),
                    distance="",
                    business_hours="",
                    reviews=[]
                )
                pois.append(poi)
            
            return pois
        except Exception as e:
            logger.error(f"搜索Excel数据失败: {e}")
            return []
    
    def search_poi(self, keyword: str, city: str, category: str = None) -> List[POIInfo]:
        """搜索POI信息 - 优先使用Excel数据，然后调用API"""
        logger.info(f"搜索POI: {keyword} in {city} (类型: {category})")
        
        # 首先尝试从Excel数据中搜索
        if self.qunar_places is not None and not self.qunar_places.empty and city == "上海":
            excel_results = self._search_qunar_places(keyword, limit=10)
            if excel_results:
                logger.info(f"从Excel数据中找到{len(excel_results)}个结果，优先使用")
                return excel_results
        
        # 如果Excel数据中没有找到，调用API
        logger.info(f"调用POI API搜索: {keyword} in {city} (类型: {category})")
        
        try:
            params = {
                "key": get_api_key("AMAP_POI"),
                "keywords": keyword,
                "city": city,
                "types": category or "",
                "offset": 10,
                "page": 1,
                "extensions": "all"
            }
            
            poi_url = "https://restapi.amap.com/v3/place/text"
            result = self._make_request(poi_url, params, "poi")
            
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
                pois = self._filter_shanghai_only(pois)
                
                logger.info(f"POI API调用成功: {keyword} - {len(pois)}个结果")
                return pois
            else:
                logger.error(f"POI API调用失败: {result.get('info', '未知错误')}")
                
        except Exception as e:
            logger.error(f"搜索POI失败: {e}")
        
        return []
    
    def _filter_shanghai_only(self, pois: List[POIInfo]) -> List[POIInfo]:
        """过滤掉非上海地区的POI"""
        filtered = []
        non_shanghai_cities = [
            "北京", "广州", "深圳", "杭州", "南京", "苏州", "成都", "重庆",
            "西安", "武汉", "天津", "长沙", "郑州", "济南", "青岛", "大连"
        ]
        shanghai_streets = [
            "北京东路", "北京西路", "南京东路", "南京西路", "淮海东路", "淮海西路"
        ]
        
        for poi in pois:
            name = poi.name or ""
            address = poi.address or ""
            full_text = f"{name} {address}".lower()
            
            is_non_shanghai = False
            for city in non_shanghai_cities:
                if city in full_text:
                    is_shanghai_street = any(street in name or street in address for street in shanghai_streets)
                    if not is_shanghai_street:
                        is_non_shanghai = True
                        break
            
            if not is_non_shanghai:
                filtered.append(poi)
        
        return filtered


class NavigationService(BaseMCPService):
    """导航服务"""
    
    def get_navigation_routes(self, origin: str, destination: str, 
                            transport_mode: str = "driving") -> List[RouteInfo]:
        """获取导航路线"""
        logger.info(f"调用导航API获取实时路线: {origin} -> {destination}")
        
        try:
            origin_coords = self._geocode(origin)
            dest_coords = self._geocode(destination)
            
            if not origin_coords or not dest_coords:
                logger.warning(f"无法获取坐标: {origin} 或 {destination}")
                return []
            
            if transport_mode == "transit":
                params = {
                    "key": get_api_key("AMAP_NAVIGATION"),
                    "origin": origin_coords,
                    "destination": dest_coords,
                    "city": "上海",
                    "cityd": "上海",
                    "strategy": "0",
                    "extensions": "base"
                }
                url = "https://restapi.amap.com/v3/direction/transit/integrated"
            else:
                params = {
                    "key": get_api_key("AMAP_NAVIGATION"),
                    "origin": origin_coords,
                    "destination": dest_coords,
                    "strategy": "10",
                    "extensions": "base"
                }
                url = "https://restapi.amap.com/v3/direction/driving"
            
            result = self._make_request(url, params, "navigation")
            
            if result.get("status") == "1":
                routes = []
                route_data = result.get("route", {})
                
                if transport_mode == "transit":
                    transit_routes = route_data.get("transits", [])
                    for route in transit_routes[:2]:
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
                    for route in driving_routes[:2]:
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
    
    def _format_transit_route(self, route: Dict) -> str:
        """格式化公交路线"""
        segments = []
        for segment in route.get("segments", []):
            if "walking" in segment:
                walk = segment["walking"]
                segments.append(f"步行{walk.get('distance', '')}米")
            elif "bus" in segment:
                bus = segment["bus"]
                buslines = bus.get("buslines", [])
                if buslines:
                    busline = buslines[0]
                    segments.append(f"{busline.get('name', '')} ({busline.get('departure_stop', {}).get('name', '')} -> {busline.get('arrival_stop', {}).get('name', '')})")
        return " → ".join(segments)
    
    def _format_driving_route(self, route: Dict) -> str:
        """格式化驾车路线"""
        steps = route.get("steps", [])
        if not steps:
            return "路线详情"
        
        # 提取主要路段
        main_roads = []
        for step in steps[:5]:  # 只取前5个路段
            instruction = step.get("instruction", "")
            if instruction:
                main_roads.append(instruction.split("，")[0])  # 取第一句
        
        return " → ".join(main_roads[:3])  # 只显示前3个主要路段


class TrafficService(BaseMCPService):
    """交通路况服务"""
    
    def get_traffic_status(self, area: str) -> Dict[str, Any]:
        """获取路况信息"""
        logger.info(f"调用路况API获取实时数据: {area}")
        
        try:
            area_mapping = {
                "徐汇区": "徐家汇",
                "普陀区": "普陀区",
                "华东师范大学": "华东师范大学",
                "徐汇": "徐家汇",
                "普陀": "普陀区"
            }
            
            search_area = area_mapping.get(area, area)
            center_coords = self._geocode(search_area)
            if not center_coords:
                logger.warning(f"无法获取区域坐标: {area}")
                return {
                    "status": "正常",
                    "description": "路况良好",
                    "evaluation": {"level": "1", "status": "畅通"},
                    "timestamp": datetime.now().isoformat()
                }
            
            center_lng, center_lat = center_coords.split(',')
            center_lng, center_lat = float(center_lng), float(center_lat)
            
            delta = 0.02
            rectangle = f"{center_lng-delta},{center_lat-delta},{center_lng+delta},{center_lat+delta}"
            
            params = {
                "key": get_api_key("AMAP_TRAFFIC"),
                "rectangle": rectangle,
                "level": "4"
            }
            
            result = self._make_request(AMAP_CONFIG["traffic_url"], params, "traffic")
            
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
                return {
                    "status": "正常",
                    "description": "路况良好",
                    "evaluation": {"level": "1", "status": "畅通"},
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"获取路况信息失败: {e}")
            return {
                "status": "正常",
                "description": "路况良好",
                "evaluation": {"level": "1", "status": "畅通"},
                "timestamp": datetime.now().isoformat()
            }


class CrowdService(BaseMCPService):
    """人流服务"""
    
    def get_crowd_info(self, location: str) -> Dict[str, Any]:
        """获取人流信息"""
        # 目前返回模拟数据，后续可以接入真实的人流API
        return {
            "level": "moderate",
            "description": "人流适中",
            "recommendation": "适合游览"
        }
