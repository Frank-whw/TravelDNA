"""
上海旅游AI - MCP服务模块
实现天气、人流量、交通等MCP服务调用
"""
import requests
import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional, List

try:
    from city_code_loader import get_city_code, get_city_info
    from config import Config
except ImportError as e:
    print(f"导入错误: {e}")
    # 为了避免循环导入，先检查是否能正常导入

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPService:
    """MCP服务基类"""
    BASE_URL = "https://sh-mcp-api.example.com"  # 示例URL，实际使用时需要替换
    TIMEOUT = 10
    # 添加开关控制是否使用真实网络请求
    USE_REAL_API = False  # 设为False避免SSL错误
    
    @classmethod
    def fetch_data(cls, endpoint: str, params: Dict[str, Any] = None) -> Optional[Dict]:
        """
        发起MCP服务请求
        """
        # 如果禁用真实API，直接返回None让服务使用默认数据
        if not cls.USE_REAL_API:
            logger.info(f"MCP服务使用离线模式，返回默认数据")
            return None
            
        try:
            url = f"{cls.BASE_URL}{endpoint}"
            response = requests.get(url, params=params, timeout=cls.TIMEOUT)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.warning(f"MCP服务调用异常: {e}")
            return None

class WeatherMCPService(MCPService):
    """天气MCP服务 - 使用高德地图天气API"""
    
    def get_weather_info(self, attraction: str, city: str = "上海") -> Dict[str, Any]:
        """
        获取指定景点的天气信息 (实例方法)
        兼容TravelAgentService调用
        """
        return self.get_weather(attraction, city)
    
    @classmethod
    def get_weather(cls, attraction: str, city: str = "上海") -> Dict[str, Any]:
        """
        获取指定景点的天气信息
        使用高德地图天气API
        """
        try:
            # 优先使用景点到区级代码的映射
            district_code = Config.SHANGHAI_ATTRACTION_DISTRICTS.get(attraction)
            
            if district_code:
                city_code = district_code
                logger.info(f"使用景点 {attraction} 的区级代码: {city_code}")
            else:
                # 如果没有景点映射，使用城市代码
                city_code = get_city_code(city)
                if not city_code:
                    raise ValueError(f"无法获取城市 {city} 的代码，且景点 {attraction} 未在映射表中")
                logger.info(f"使用城市 {city} 的代码: {city_code}")
            
            # 构建API请求参数
            params = {
                "city": city_code,
                "key": Config.AMAP_WEATHER_API_KEY,
                "extensions": "base",  # base:当前天气, all:天气预报
                "output": "json"
            }
            
            # 调用高德天气API
            response = requests.get(Config.AMAP_WEATHER_URL, params=params, timeout=10)
            response.raise_for_status()
            
            api_data = response.json()
            logger.info(f"高德天气API响应: {api_data}")
            
            # 检查API响应状态
            if api_data.get("status") != "1":
                error_info = api_data.get("info", "未知错误")
                error_code = api_data.get("infocode", "")
                logger.error(f"高德天气API错误 [{error_code}]: {error_info}")
                
                # 不再使用回退数据，直接抛出异常
                raise RuntimeError(f"天气API调用失败: {error_info} (错误码: {error_code})")
            
            # 解析天气数据
            lives = api_data.get("lives", [])
            if not lives:
                raise RuntimeError("高德天气API返回空数据")
            
            weather_data = lives[0]  # 取第一个结果
            
            # 解析温度和天气状况
            temperature = weather_data.get("temperature", "未知")
            weather_desc = weather_data.get("weather", "未知")
            humidity = weather_data.get("humidity", "未知")
            winddirection = weather_data.get("winddirection", "")
            windpower = weather_data.get("windpower", "")
            reporttime = weather_data.get("reporttime", "")
            
            # 获取区域信息
            province = weather_data.get("province", "")
            city_name = weather_data.get("city", "")
            
            # 组装风力信息
            wind_info = f"{winddirection}风 {windpower}级" if winddirection and windpower else "微风"
            
            # 生成出行建议
            recommendation = cls._generate_recommendation(temperature, weather_desc, humidity)
            
            return {
                "service": "weather",
                "location": attraction,
                "city": city,
                "city_code": city_code,
                "district": city_name,
                "province": province,
                "temperature": f"{temperature}°C" if temperature != "未知" else "未知",
                "weather": weather_desc,
                "humidity": f"{humidity}%" if humidity != "未知" else "未知",
                "wind": wind_info,
                "recommendation": recommendation,
                "report_time": reporttime,
                "timestamp": datetime.now().isoformat(),
                "api_source": "amap"
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"高德天气API网络请求失败: {e}")
            raise RuntimeError(f"天气API网络请求失败: {str(e)}")
        except Exception as e:
            logger.error(f"获取天气信息异常: {e}")
            raise
    

    
    @classmethod
    def _generate_recommendation(cls, temperature: str, weather: str, humidity: str) -> str:
        """根据天气条件生成出行建议"""
        recommendations = []
        
        try:
            # 处理温度建议
            if temperature != "未知":
                temp_val = float(temperature)
                if temp_val >= 30:
                    recommendations.append("天气炎热，注意防暑降温，建议携带遮阳伞和充足饮水")
                elif temp_val <= 5:
                    recommendations.append("天气寒冷，注意保暖，建议穿着厚重衣物")
                elif temp_val <= 15:
                    recommendations.append("天气较凉，建议携带外套")
                else:
                    recommendations.append("温度适宜，适合户外活动")
        except (ValueError, TypeError):
            pass
        
        # 处理天气状况建议
        if "雨" in weather:
            recommendations.append("有降雨，建议携带雨具")
        elif "雪" in weather:
            recommendations.append("有降雪，注意路面湿滑，出行小心")
        elif "雾" in weather or "霾" in weather:
            recommendations.append("能见度较低，出行注意安全")
        elif "晴" in weather:
            recommendations.append("天气晴朗，适合户外游览")
        
        # 处理湿度建议
        try:
            if humidity != "未知":
                humidity_val = float(humidity.replace("%", ""))
                if humidity_val >= 80:
                    recommendations.append("湿度较高，注意防潮")
                elif humidity_val <= 30:
                    recommendations.append("空气干燥，注意补水")
        except (ValueError, TypeError):
            pass
        
        return "；".join(recommendations) if recommendations else "天气状况良好，适宜出行"
    
    @classmethod
    def get_weather_forecast(cls, city: str = "上海", days: int = 3) -> Dict[str, Any]:
        """
        获取未来几天的天气预报
        """
        try:
            # 对于上海，使用市级代码
            if city == "上海" or city == "上海市":
                city_code = "310000"  # 上海市代码
            else:
                city_code = get_city_code(city)
                if not city_code:
                    raise ValueError(f"无法获取城市 {city} 的代码")
            
            params = {
                "city": city_code,
                "key": Config.AMAP_WEATHER_API_KEY,
                "extensions": "all",  # 获取天气预报
                "output": "json"
            }
            
            response = requests.get(Config.AMAP_WEATHER_URL, params=params, timeout=10)
            response.raise_for_status()
            
            api_data = response.json()
            logger.info(f"高德天气预报API响应: {api_data}")
            
            if api_data.get("status") != "1":
                error_info = api_data.get("info", "未知错误")
                error_code = api_data.get("infocode", "")
                raise RuntimeError(f"天气预报API调用失败: {error_info} (错误码: {error_code})")
            
            forecasts = api_data.get("forecasts", [])
            if not forecasts:
                raise RuntimeError("未获取到预报数据")
            
            forecast_data = forecasts[0]
            casts = forecast_data.get("casts", [])[:days]
            
            forecast_list = []
            for cast in casts:
                forecast_list.append({
                    "date": cast.get("date", ""),
                    "week": cast.get("week", ""),
                    "dayweather": cast.get("dayweather", ""),
                    "nightweather": cast.get("nightweather", ""),
                    "daytemp": cast.get("daytemp", ""),
                    "nighttemp": cast.get("nighttemp", ""),
                    "daywind": cast.get("daywind", ""),
                    "nightwind": cast.get("nightwind", ""),
                    "daypower": cast.get("daypower", ""),
                    "nightpower": cast.get("nightpower", "")
                })
            
            return {
                "service": "weather_forecast",
                "city": city,
                "city_code": city_code,
                "forecasts": forecast_list,
                "timestamp": datetime.now().isoformat(),
                "api_source": "amap"
            }
            
        except Exception as e:
            logger.error(f"获取天气预报失败: {e}")
            raise

class CrowdMCPService(MCPService):
    """人流量MCP服务"""
    
    @classmethod
    def get_crowd_info(cls, attraction: str) -> Dict[str, Any]:
        """
        获取指定景点的人流量信息
        """
        params = {
            "location": attraction,
            "city": "上海",
            "type": "realtime"
        }
        
        data = cls.fetch_data("/crowd", params)
        
        if data:
            return {
                "service": "crowd",
                "location": attraction,
                "crowd_level": data.get("crowd_level", "未知"),
                "wait_time": data.get("wait_time", "未知"),
                "best_visit_time": data.get("best_visit_time", ""),
                "peak_hours": data.get("peak_hours", []),
                "recommendation": data.get("recommendation", ""),
                "timestamp": datetime.now().isoformat()
            }
        else:
            # 返回默认数据
            return {
                "service": "crowd",
                "location": attraction,
                "crowd_level": "中等",
                "wait_time": "15-30分钟",
                "best_visit_time": "上午9-11点或下午3-5点",
                "peak_hours": ["11:00-14:00", "18:00-20:00"],
                "recommendation": "建议避开周末和节假日，选择工作日游览",
                "timestamp": datetime.now().isoformat(),
                "fallback": True
            }

class TrafficMCPService(MCPService):
    """交通MCP服务 - 使用高德地图交通态势API"""
    
    def __init__(self):
        """初始化交通MCP服务"""
        # 导入交通服务模块
        try:
            from traffic_service import TrafficService
            self.traffic_service = TrafficService(Config.AMAP_TRAFFIC_API_KEY)
            logger.info("✅ 交通MCP服务初始化成功")
        except ImportError as e:
            logger.error(f"❌ 交通服务模块导入失败: {e}")
            self.traffic_service = None
    
    def get_traffic_info(self, attraction: str, origin: str = "市中心") -> Dict[str, Any]:
        """
        获取到指定景点的交通信息
        集成到MCP框架中的交通服务
        """
        try:
            if not self.traffic_service:
                logger.warning("交通服务未初始化，返回默认数据")
                return self._get_default_traffic_info(attraction, origin)
            
            # 使用新的交通服务获取数据
            traffic_result = self.traffic_service.get_attraction_roads_traffic(attraction)
            
            if not traffic_result.get("has_traffic_data"):
                logger.warning(f"景点 {attraction} 无交通数据")
                return self._get_default_traffic_info(attraction, origin)
            
            # 转换为MCP格式
            return {
                "service": "traffic",
                "destination": attraction,
                "origin": origin,
                "city": traffic_result.get("attraction", "上海"),
                "roads_checked": traffic_result.get("roads_checked", 0),
                "traffic_status": traffic_result.get("traffic_status", "未知"),
                "estimated_time": traffic_result.get("estimated_time", "未知"),
                "best_route": traffic_result.get("best_transport", "地铁"),
                "alternative_routes": ["地铁", "公交", "出租车", "共享单车"],
                "recommendation": traffic_result.get("suggestion", "建议使用公共交通"),
                "congestion_level": traffic_result.get("average_congestion", "未知"),
                "road_traffic_details": traffic_result.get("road_details", []),
                "timestamp": datetime.now().isoformat(),
                "api_source": "amap_traffic_mcp"
            }
            
        except Exception as e:
            logger.error(f"获取交通信息异常: {e}")
            return self._get_default_traffic_info(attraction, origin)
    
    def get_route_traffic_analysis(self, attractions: List[str]) -> Dict[str, Any]:
        """
        获取路线交通分析 - MCP服务接口
        """
        try:
            if not self.traffic_service:
                return {"service": "traffic", "route": attractions, "status": "服务不可用"}
            
            # 使用交通服务分析路线
            route_analysis = self.traffic_service.get_route_traffic_analysis(attractions)
            
            # 转换为MCP格式
            return {
                "service": "traffic_route",
                "route": attractions,
                "overall_status": route_analysis.get("overall_status", "未知"),
                "route_suggestions": route_analysis.get("route_suggestions", []),
                "average_congestion": route_analysis.get("average_route_congestion", "未知"),
                "attractions_traffic": route_analysis.get("attractions_traffic", []),
                "timestamp": datetime.now().isoformat(),
                "api_source": "amap_traffic_mcp"
            }
            
        except Exception as e:
            logger.error(f"路线交通分析异常: {e}")
            return {
                "service": "traffic_route",
                "route": attractions,
                "status": "分析失败",
                "error": str(e)
            }
    
    @classmethod
    def _get_road_traffic(cls, road_name: str, city_name: str) -> Optional[Dict]:
        """获取单条道路的交通状况"""
        try:
            # 构建基础参数
            params = {
                "city": city_name,
                "name": road_name,
                "key": Config.AMAP_TRAFFIC_API_KEY,
                "output": "json"
            }
            
            # 添加安全签名（如果有安全密钥）
            if hasattr(Config, 'AMAP_TRAFFIC_SECURITY_KEY') and Config.AMAP_TRAFFIC_SECURITY_KEY:
                params["sig"] = cls._generate_signature(params, Config.AMAP_TRAFFIC_SECURITY_KEY)
            
            response = requests.get(Config.AMAP_TRAFFIC_URL, params=params, timeout=10)
            response.raise_for_status()
            
            api_data = response.json()
            logger.info(f"高德交通API响应 ({road_name}): {api_data}")
            
            if api_data.get("status") != "1":
                error_info = api_data.get("info", "未知错误")
                logger.warning(f"交通API错误: {error_info}, 使用模拟数据")
                # 使用智能模拟数据
                return cls._get_simulated_road_traffic(road_name)
            
            # 解析交通数据
            roads = api_data.get("roads", [])
            if not roads:
                logger.warning(f"道路 {road_name} 无数据，使用模拟数据")
                return cls._get_simulated_road_traffic(road_name)
            
            road_data = roads[0]  # 取第一条结果
            
            # 解析交通状况
            status = road_data.get("status", "0")
            speed = road_data.get("speed", "0")
            direction = road_data.get("direction", "")
            
            # 转换状态码为中文描述
            status_map = {
                "0": "未知",
                "1": "畅通",
                "2": "缓慢", 
                "3": "拥堵",
                "4": "严重拥堵"
            }
            
            status_desc = status_map.get(status, "未知")
            
            return {
                "road_name": road_name,
                "status": status_desc,
                "status_code": status,
                "speed": f"{speed}km/h" if speed != "0" else "未知",
                "direction": direction,
                "update_time": datetime.now().strftime('%H:%M'),
                "api_source": "amap_traffic"
            }
            
        except Exception as e:
            logger.error(f"获取道路 {road_name} 交通信息失败: {e}")
            return cls._get_simulated_road_traffic(road_name)
    
    @classmethod
    def _get_simulated_road_traffic(cls, road_name: str) -> Dict:
        """生成智能模拟的道路交通数据"""
        import hashlib
        from datetime import datetime
        
        # 基于道路名称和当前时间生成相对稳定的模拟数据
        seed = hashlib.md5(f"{road_name}{datetime.now().hour}".encode()).hexdigest()
        hash_val = int(seed[:8], 16) % 100
        
        # 根据时间和道路类型模拟交通状况
        current_hour = datetime.now().hour
        
        # 高峰时段交通更拥堵
        if current_hour in [7, 8, 9, 17, 18, 19]:  # 早晚高峰
            if hash_val < 20:
                status = "畅通"
                speed = "35-50"
            elif hash_val < 50:
                status = "缓慢"
                speed = "20-35"
            elif hash_val < 80:
                status = "拥堵"
                speed = "10-20"
            else:
                status = "严重拥堵"
                speed = "5-10"
        else:  # 非高峰时段
            if hash_val < 60:
                status = "畅通"
                speed = "40-60"
            elif hash_val < 85:
                status = "缓慢"
                speed = "25-40"
            else:
                status = "拥堵"
                speed = "15-25"
        
        # 主要道路通常更拥堵
        main_roads = ["南京东路", "南京西路", "淮海中路", "延安路", "中山路", "人民大道"]
        if any(main_road in road_name for main_road in main_roads):
            if status == "畅通":
                status = "缓慢"
                speed = "25-35"
            elif status == "缓慢":
                status = "拥堵"
                speed = "15-25"
        
        return {
            "road_name": road_name,
            "status": status,
            "speed": f"{speed}km/h",
            "direction": "双向",
            "update_time": datetime.now().strftime('%H:%M'),
            "api_source": "simulated"
        }
    
    @classmethod
    def _generate_signature(cls, params: Dict, secret_key: str) -> str:
        """生成高德API安全签名"""
        import hashlib
        
        # 按照ASCII码排序参数
        sorted_params = sorted(params.items())
        
        # 拼接参数字符串
        param_str = "&".join([f"{k}={v}" for k, v in sorted_params])
        
        # 拼接安全密钥
        sign_str = f"{param_str}&{secret_key}"
        
        # 计算MD5
        md5_hash = hashlib.md5(sign_str.encode('utf-8')).hexdigest()
        
        return md5_hash
    
    @classmethod
    def _get_district_name(cls, city_code: str) -> str:
        """根据城市代码获取区域名称"""
        district_map = {
            "310101": "黄浦区",
            "310104": "徐汇区", 
            "310105": "长宁区",
            "310106": "静安区",
            "310107": "普陀区",
            "310109": "虹口区",
            "310110": "杨浦区",
            "310112": "闵行区",
            "310113": "宝山区",
            "310114": "嘉定区",
            "310115": "浦东新区",
            "310116": "金山区",
            "310117": "松江区",
            "310118": "青浦区",
            "310120": "奉贤区",
            "310151": "崇明区"
        }
        return district_map.get(city_code, "上海市")
    
    @classmethod
    def _generate_traffic_recommendation(cls, overall_status: str, traffic_data: List[Dict]) -> str:
        """生成交通建议"""
        recommendations = []
        
        if overall_status in ["拥堵", "严重拥堵"]:
            recommendations.append("当前道路较为拥堵，建议优先选择地铁出行")
            recommendations.append("避开高峰时段，或考虑其他出行方式")
        elif overall_status == "缓慢":
            recommendations.append("道路略有拥堵，地铁和出租车均可考虑")
            recommendations.append("注意预留充足的出行时间")
        else:
            recommendations.append("当前交通状况良好，各种出行方式都比较便捷")
        
        # 根据具体道路情况添加建议
        if traffic_data:
            congested_roads = [road['road_name'] for road in traffic_data if road.get('status') in ['拥堵', '严重拥堵']]
            if congested_roads:
                recommendations.append(f"避开拥堵路段：{', '.join(congested_roads)}")
        
        return "；".join(recommendations)
    
    @classmethod
    def _estimate_travel_time(cls, traffic_status: str) -> str:
        """根据交通状况估算出行时间"""
        time_map = {
            "畅通": "20-35分钟",
            "缓慢": "35-50分钟", 
            "拥堵": "50-70分钟",
            "严重拥堵": "70-90分钟",
            "未知": "30-45分钟"
        }
        return time_map.get(traffic_status, "30-45分钟")
    
    @classmethod
    def _get_default_traffic_info(cls, attraction: str, origin: str) -> Dict[str, Any]:
        """返回默认交通信息"""
        return {
            "service": "traffic",
            "destination": attraction,
            "origin": origin,
            "traffic_status": "畅通",
            "estimated_time": "30-45分钟",
            "best_route": "地铁",
            "alternative_routes": ["出租车", "公交", "共享单车"],
            "recommendation": "推荐使用地铁出行，准时便捷",
            "timestamp": datetime.now().isoformat(),
            "api_source": "fallback"
        }

class NavigationMCPService(MCPService):
    """导航MCP服务 - 使用高德地图路径规划API"""
    
    def __init__(self):
        """初始化导航MCP服务"""
        self.api_key = Config.AMAP_NAVIGATION_API_KEY
        self.base_url = Config.AMAP_NAVIGATION_URL
        self.timeout = Config.AMAP_NAVIGATION_TIMEOUT
        self.strategies = Config.NAVIGATION_STRATEGIES
        
        # 速率限制：基础LBS服务并发量上限
        self._rate_limiter = {
            "max_requests": Config.AMAP_NAVIGATION_RATE_LIMIT,  # 每秒最大请求数
            "window_size": 1.0,  # 时间窗口大小（秒）
            "requests": [],  # 请求时间戳列表
            "last_cleanup": time.time()
        }
        
        logger.info(f"✅ 导航MCP服务初始化成功（速率限制：{Config.AMAP_NAVIGATION_RATE_LIMIT}次/秒）")
    
    def _check_rate_limit(self) -> bool:
        """
        检查是否超过速率限制
        
        Returns:
            True: 可以发送请求, False: 超过速率限制
        """
        current_time = time.time()
        rate_limiter = self._rate_limiter
        
        # 清理过期的请求记录（超过时间窗口的请求）
        cutoff_time = current_time - rate_limiter["window_size"]
        rate_limiter["requests"] = [
            req_time for req_time in rate_limiter["requests"] 
            if req_time > cutoff_time
        ]
        
        # 检查当前请求数是否超过限制
        if len(rate_limiter["requests"]) >= rate_limiter["max_requests"]:
            logger.warning(f"达到速率限制：{rate_limiter['max_requests']}次/秒，等待重试")
            return False
        
        # 记录当前请求时间
        rate_limiter["requests"].append(current_time)
        return True
    
    def _wait_for_rate_limit(self):
        """等待速率限制窗口重置"""
        if not self._rate_limiter["requests"]:
            return
        
        # 计算需要等待的时间
        oldest_request = min(self._rate_limiter["requests"])
        wait_time = self._rate_limiter["window_size"] - (time.time() - oldest_request)
        
        if wait_time > 0:
            logger.info(f"等待速率限制重置，暂停 {wait_time:.2f} 秒")
            time.sleep(wait_time)
            # 清理过期请求
            self._check_rate_limit()
    
    def get_route_planning(self, origin: str, destination: str, strategy: str = "default", 
                          waypoints: List[str] = None, avoid_polygons: List[str] = None,
                          plate: str = None, cartype: int = 0) -> Dict[str, Any]:
        """
        获取驾车路径规划
        
        Args:
            origin: 起点（景点名称或经纬度）
            destination: 终点（景点名称或经纬度）
            strategy: 驾车策略
            waypoints: 途经点列表
            avoid_polygons: 避让区域
            plate: 车牌号码
            cartype: 车辆类型 (0:燃油车, 1:电动车, 2:混动车)
        
        Returns:
            路径规划结果
        """
        try:
            # 转换地点名称为经纬度
            origin_coords = self._get_coordinates(origin)
            destination_coords = self._get_coordinates(destination)
            
            if not origin_coords or not destination_coords:
                return self._get_default_navigation_info(origin, destination)
            
            # 检查速率限制，如果超限则等待
            if not self._check_rate_limit():
                logger.info("达到速率限制，等待重试...")
                self._wait_for_rate_limit()
                # 重新检查速率限制
                if not self._check_rate_limit():
                    logger.error("重试后仍超过速率限制，返回错误")
                    return self._get_default_navigation_info(origin, destination)
            
            # 构建API请求参数
            params = {
                "key": self.api_key,
                "origin": origin_coords,
                "destination": destination_coords,
                "strategy": self.strategies.get(strategy, self.strategies["default"]),
                "output": "json"
            }
            
            # 添加可选参数
            if waypoints:
                waypoint_coords = []
                for waypoint in waypoints:
                    coords = self._get_coordinates(waypoint)
                    if coords:
                        waypoint_coords.append(coords)
                if waypoint_coords:
                    params["waypoints"] = ";".join(waypoint_coords)
            
            if avoid_polygons:
                params["avoidpolygons"] = "|".join(avoid_polygons)
            
            if plate:
                params["plate"] = plate
            
            params["cartype"] = cartype
            
            # 控制返回结果字段
            params["show_fields"] = ",".join(Config.NavigationConfig.OUTPUT_FIELDS)
            
            # 发起API请求
            logger.info(f"正在获取从 {origin} 到 {destination} 的路径规划")
            
            # 根据参数长度选择请求方法
            if len(str(params)) > 2000:  # 参数过长时使用POST
                response = requests.post(self.base_url, data=params, timeout=self.timeout)
            else:
                response = requests.get(self.base_url, params=params, timeout=self.timeout)
            
            response.raise_for_status()
            api_data = response.json()
            
            # 检查API响应状态
            if api_data.get("status") != "1":
                error_info = api_data.get("info", "未知错误")
                error_code = api_data.get("infocode", "")
                logger.error(f"高德导航API错误 [{error_code}]: {error_info}")
                
                # 针对不同错误码进行日志记录
                if error_code == "10021":  # CUQPS超限
                    logger.error("导航API配额已超限")
                elif error_code in ["10001", "10002", "10003"]:  # 认证错误
                    logger.error("导航API认证失败，请检查API密钥")
                elif error_code == "20001":  # 请求参数错误
                    logger.error("导航API参数错误")
                elif error_code == "30001":  # 内部错误
                    logger.error("导航API服务内部错误")
                
                return self._get_default_navigation_info(origin, destination)
            
            # 解析路径数据
            route_data = api_data.get("route", {})
            paths = route_data.get("paths", [])
            
            if not paths:
                logger.warning("未获取到路径数据")
                return self._get_default_navigation_info(origin, destination)
            
            # 解析第一条路径（主要推荐路线）
            main_path = paths[0]
            
            # 提取路径信息
            distance = main_path.get("distance", "0")  # 距离（米）
            duration = main_path.get("duration", "0")   # 时长（秒）
            tolls = main_path.get("tolls", "0")         # 过路费（元）
            traffic_lights = main_path.get("traffic_lights", "0")  # 红绿灯数量
            restriction = main_path.get("restriction", "0")  # 限行状态
            
            # 格式化距离和时间
            formatted_distance = self._format_distance(int(distance))
            formatted_duration = self._format_duration(int(duration))
            
            # 解析详细步骤（显示所有步骤）
            steps = main_path.get("steps", [])
            navigation_steps = self._parse_navigation_steps(steps, show_all=True)
            
            # 生成导航建议
            navigation_advice = self._generate_navigation_advice(
                int(distance), int(duration), int(tolls), int(traffic_lights)
            )
            
            # 解析路径的完整信息
            polyline = main_path.get("polyline", "")  # 路径轨迹
            taxi_cost = route_data.get("taxi_cost", "0")  # 出租车费用
            
            return {
                "service": "navigation",
                "origin": origin,
                "destination": destination,
                "origin_coords": origin_coords,
                "destination_coords": destination_coords,
                "strategy": strategy,
                "distance": formatted_distance,
                "distance_value": int(distance),  # 原始距离值（米）
                "duration": formatted_duration,
                "duration_value": int(duration),  # 原始时长值（秒）
                "tolls": f"{tolls}元" if tolls != "0" else "无过路费",
                "tolls_value": int(tolls),  # 原始过路费值
                "traffic_lights": f"{traffic_lights}个" if traffic_lights != "0" else "无红绿灯",
                "traffic_lights_count": int(traffic_lights),  # 红绿灯数量
                "restriction_status": "有限行" if restriction != "0" else "无限行",
                "taxi_cost": f"{taxi_cost}元" if taxi_cost != "0" else "未知",
                "polyline": polyline,  # 路径轨迹编码
                "navigation_steps": navigation_steps,
                "total_steps": len(navigation_steps),  # 总导航步骤数
                "route_summary": f"总里程{formatted_distance}，预计用时{formatted_duration}",
                "advice": navigation_advice,
                "alternative_routes": len(paths),
                "complete_route_data": {
                    "main_path": main_path,  # 完整的主路径数据
                    "all_paths": paths  # 所有可选路径
                },
                "timestamp": datetime.now().isoformat(),
                "api_source": "amap_navigation"
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"高德导航API网络请求失败: {e}")
            return self._get_default_navigation_info(origin, destination)
        except Exception as e:
            logger.error(f"获取导航信息异常: {e}")
            return self._get_default_navigation_info(origin, destination)
    
    def get_multi_destination_planning(self, origin: str, destinations: List[str], 
                                     strategy: str = "default") -> Dict[str, Any]:
        """
        多目的地路径规划（景点路线优化）
        
        Args:
            origin: 起点
            destinations: 目的地列表
            strategy: 路径策略
        
        Returns:
            多目的地路径规划结果
        """
        try:
            logger.info(f"正在规划从 {origin} 到 {destinations} 的多目的地路线")
            
            routes_info = []
            total_distance = 0
            total_duration = 0
            total_tolls = 0
            
            current_location = origin
            
            # 逐个计算到每个目的地的路径
            for i, destination in enumerate(destinations):
                route_result = self.get_route_planning(
                    current_location, destination, strategy
                )
                
                if route_result.get("api_source") == "amap_navigation":
                    # 使用API返回的原始数值
                    distance_km = route_result.get("distance_value", 0) / 1000
                    duration_minutes = route_result.get("duration_value", 0) / 60
                    tolls_amount = route_result.get("tolls_value", 0)
                    
                    total_distance += distance_km
                    total_duration += duration_minutes
                    total_tolls += tolls_amount
                
                routes_info.append({
                    "segment": i + 1,
                    "from": current_location,
                    "to": destination,
                    "route_info": route_result
                })
                
                current_location = destination  # 更新当前位置
            
            # 生成整体路线建议
            route_optimization = self._generate_route_optimization(
                origin, destinations, total_distance, total_duration, total_tolls
            )
            
            return {
                "service": "multi_navigation",
                "origin": origin,
                "destinations": destinations,
                "total_destinations": len(destinations),
                "route_segments": routes_info,
                "total_distance": f"{total_distance:.1f}公里",
                "total_duration": self._format_duration(int(total_duration * 60)),
                "total_tolls": f"{total_tolls:.1f}元" if total_tolls > 0 else "无过路费",
                "route_optimization": route_optimization,
                "timestamp": datetime.now().isoformat(),
                "api_source": "amap_navigation_multi"
            }
            
        except Exception as e:
            logger.error(f"多目的地路径规划异常: {e}")
            return {
                "service": "multi_navigation",
                "origin": origin,
                "destinations": destinations,
                "status": "规划失败",
                "error": str(e)
            }
    
    def _get_coordinates(self, location: str) -> Optional[str]:
        """获取地点的经纬度坐标"""
        # 如果已经是经纬度格式，直接返回
        if "," in location and len(location.split(",")) == 2:
            try:
                parts = location.split(",")
                float(parts[0])  # 验证是否为有效数字
                float(parts[1])
                return location
            except ValueError:
                pass
        
        # 从配置中查找景点坐标
        coords = Config.SHANGHAI_ATTRACTION_COORDINATES.get(location)
        if coords:
            return coords
        
        # 如果找不到，记录警告并返回None
        logger.warning(f"未找到地点 {location} 的坐标信息")
        return None
    
    def _format_distance(self, distance_meters: int) -> str:
        """格式化距离显示"""
        if distance_meters < 1000:
            return f"{distance_meters}米"
        else:
            km = distance_meters / 1000
            return f"{km:.1f}公里"
    
    def _format_duration(self, duration_seconds: int) -> str:
        """格式化时长显示"""
        hours = duration_seconds // 3600
        minutes = (duration_seconds % 3600) // 60
        
        if hours > 0:
            return f"{hours}小时{minutes}分钟"
        else:
            return f"{minutes}分钟"
    
    def _parse_navigation_steps(self, steps: List[Dict], show_all: bool = False) -> List[Dict]:
        """解析导航步骤"""
        navigation_steps = []
        
        # 如果show_all为True，显示所有步骤，否则只显示前10步
        steps_to_show = steps if show_all else steps[:10]
        
        for i, step in enumerate(steps_to_show):
            instruction = step.get("instruction", "")
            distance = step.get("distance", "0")
            duration = step.get("duration", "0")
            road_name = step.get("road", "")
            action = step.get("action", "")
            orientation = step.get("orientation", "")
            
            navigation_steps.append({
                "step": i + 1,
                "instruction": instruction,
                "distance": self._format_distance(int(distance)),
                "duration": self._format_duration(int(duration)),
                "road": road_name,
                "action": action,
                "orientation": orientation
            })
        
        return navigation_steps
    
    def _generate_navigation_advice(self, distance: int, duration: int, 
                                  tolls: int, traffic_lights: int) -> str:
        """生成导航建议"""
        advice_parts = []
        
        # 距离建议
        if distance > 50000:  # 超过50公里
            advice_parts.append("距离较远，建议提前安排时间")
        elif distance < 2000:  # 少于2公里
            advice_parts.append("距离较近，也可考虑步行或骑行")
        
        # 时间建议
        if duration > 3600:  # 超过1小时
            advice_parts.append("行程时间较长，注意驾驶安全和休息")
        
        # 费用建议
        if tolls > 20:
            advice_parts.append("过路费较高，可考虑不走高速的路线")
        elif tolls == 0:
            advice_parts.append("无过路费，经济实惠")
        
        # 红绿灯建议
        if traffic_lights > 10:
            advice_parts.append("红绿灯较多，注意保持耐心")
        
        return "；".join(advice_parts) if advice_parts else "路线规划合理，建议按导航行驶"
    
    def _generate_route_optimization(self, origin: str, destinations: List[str],
                                   total_distance: float, total_duration: int, 
                                   total_tolls: float) -> Dict[str, Any]:
        """生成路线优化建议"""
        optimization = {
            "efficiency_score": "良好",
            "suggestions": [],
            "alternative_transport": [],
            "time_recommendations": []
        }
        
        # 效率评估
        if total_distance > 100:
            optimization["efficiency_score"] = "距离较远"
            optimization["suggestions"].append("考虑分两天游览，避免疲劳驾驶")
        elif total_duration > 180:  # 超过3小时
            optimization["efficiency_score"] = "耗时较长"
            optimization["suggestions"].append("建议合理安排休息时间")
        
        # 交通方式建议
        if len(destinations) > 3:
            optimization["alternative_transport"].append("地铁")
            optimization["alternative_transport"].append("公交+步行")
            optimization["suggestions"].append("景点较多，建议考虑公共交通")
        
        # 时间安排建议
        if total_duration > 120:  # 超过2小时
            optimization["time_recommendations"].append("建议上午9点前出发")
            optimization["time_recommendations"].append("避开下午5-7点高峰期")
        
        return optimization
    
    def _get_default_navigation_info(self, origin: str, destination: str) -> Dict[str, Any]:
        """返回默认导航信息"""
        return {
            "service": "navigation",
            "origin": origin,
            "destination": destination,
            "distance": "约15公里",
            "duration": "约30分钟",
            "route_info": {
                "distance_value": 15000,  # 默认15公里
                "duration_value": 30,     # 默认30分钟
                "tolls_value": 0
            },
            "navigation_steps": [],
            "total_steps": 0,
            "strategy": "default",
            "error": "导航服务暂时不可用",
            "timestamp": datetime.now().isoformat(),
            "api_source": "default"
        }


class POISearchMCPService(MCPService):
    """POI搜索MCP服务 - 使用高德地图POI搜索API"""
    
    def __init__(self):
        """初始化POI搜索服务"""
        self.api_key = Config.AMAP_POI_API_KEY
        self.text_search_url = Config.AMAP_POI_TEXT_SEARCH_URL
        self.around_search_url = Config.AMAP_POI_AROUND_SEARCH_URL
        self.polygon_search_url = Config.AMAP_POI_POLYGON_SEARCH_URL
        self.timeout = Config.AMAP_POI_TIMEOUT
        self.poi_types = Config.POI_TYPE_CODES
        self.default_types = Config.DEFAULT_POI_TYPES
        
        # 速率限制器
        self._rate_limiter = {
            "max_requests": Config.AMAP_POI_RATE_LIMIT,
            "window_size": 1,  # 1秒窗口
            "requests": [],
            "last_cleanup": time.time()
        }
        
        logger.info(f"✅ POI搜索MCP服务初始化成功（速率限制：{Config.AMAP_POI_RATE_LIMIT}次/秒）")
    
    def _check_rate_limit(self) -> bool:
        """检查速率限制"""
        current_time = time.time()
        rate_limiter = self._rate_limiter
        
        # 清理过期的请求记录
        cutoff_time = current_time - rate_limiter["window_size"]
        rate_limiter["requests"] = [
            req_time for req_time in rate_limiter["requests"]
            if req_time > cutoff_time
        ]
        
        # 检查当前请求数是否超过限制
        if len(rate_limiter["requests"]) >= rate_limiter["max_requests"]:
            logger.warning(f"达到速率限制：{rate_limiter['max_requests']}次/秒，等待重试")
            return False
        
        # 记录当前请求时间
        rate_limiter["requests"].append(current_time)
        return True
    
    def _wait_for_rate_limit(self):
        """等待速率限制窗口重置"""
        if not self._rate_limiter["requests"]:
            return
        
        # 计算需要等待的时间
        oldest_request = min(self._rate_limiter["requests"])
        wait_time = self._rate_limiter["window_size"] - (time.time() - oldest_request)
        
        if wait_time > 0:
            logger.info(f"等待速率限制重置，暂停 {wait_time:.2f} 秒")
            time.sleep(wait_time)
            # 清理过期请求
            self._check_rate_limit()
    
    def text_search(self, keywords: str, region: str = "上海", city_limit: bool = True, 
                   types: List[str] = None, page_size: int = 10, page_num: int = 1) -> Dict[str, Any]:
        """关键字搜索POI"""
        try:
            logger.info(f"正在搜索POI关键字: {keywords} (区域: {region})")
            
            # 检查速率限制
            if not self._check_rate_limit():
                logger.info("达到速率限制，等待重试...")
                self._wait_for_rate_limit()
                if not self._check_rate_limit():
                    logger.error("重试后仍超过速率限制，返回错误")
                    return self._get_default_search_result(keywords, "text_search")
            
            # 构建请求参数
            params = {
                "key": self.api_key,
                "keywords": keywords,
                "region": region,
                "city_limit": "true" if city_limit else "false",
                "page_size": min(page_size, 25),
                "page_num": page_num,
                "output": "json"
            }
            
            if types:
                params["types"] = "|".join(types)
            
            response = requests.get(self.text_search_url, params=params, timeout=self.timeout)
            response.raise_for_status()
            api_data = response.json()
            
            if api_data.get("status") != "1":
                error_info = api_data.get("info", "未知错误")
                error_code = api_data.get("infocode", "")
                logger.error(f"高德POI搜索API错误 [{error_code}]: {error_info}")
                return self._get_default_search_result(keywords, "text_search")
            
            pois = api_data.get("pois", [])
            count = api_data.get("count", "0")
            logger.info(f"搜索到 {count} 个POI结果")
            
            return {
                "service": "poi_search",
                "search_type": "text_search",
                "keywords": keywords,
                "region": region,
                "total_count": int(count),
                "pois": self._parse_poi_results(pois),
                "timestamp": datetime.now().isoformat(),
                "api_source": "amap_poi_search"
            }
            
        except Exception as e:
            logger.error(f"POI关键字搜索异常: {e}")
            return self._get_default_search_result(keywords, "text_search")
    
    def around_search(self, location: str, keywords: str = None, types: List[str] = None, 
                     radius: int = 5000) -> Dict[str, Any]:
        """周边搜索POI"""
        try:
            logger.info(f"正在搜索周边POI: {location} (半径: {radius}米)")
            
            if not self._check_rate_limit():
                logger.info("达到速率限制，等待重试...")
                self._wait_for_rate_limit()
                if not self._check_rate_limit():
                    return self._get_default_search_result(location, "around_search")
            
            params = {
                "key": self.api_key,
                "location": location,
                "radius": min(radius, 50000),
                "output": "json"
            }
            
            if keywords:
                params["keywords"] = keywords
            if types:
                params["types"] = "|".join(types)
            else:
                params["types"] = "|".join(self.default_types)
            
            response = requests.get(self.around_search_url, params=params, timeout=self.timeout)
            response.raise_for_status()
            api_data = response.json()
            
            if api_data.get("status") != "1":
                return self._get_default_search_result(location, "around_search")
            
            pois = api_data.get("pois", [])
            count = api_data.get("count", "0")
            
            return {
                "service": "poi_search",
                "search_type": "around_search",
                "center_location": location,
                "total_count": int(count),
                "pois": self._parse_poi_results(pois),
                "timestamp": datetime.now().isoformat(),
                "api_source": "amap_poi_search"
            }
            
        except Exception as e:
            logger.error(f"POI周边搜索异常: {e}")
            return self._get_default_search_result(location, "around_search")
    
    def _parse_poi_results(self, pois: List[Dict]) -> List[Dict]:
        """解析POI搜索结果"""
        parsed_pois = []
        for poi in pois:
            parsed_poi = {
                "id": poi.get("id", ""),
                "name": poi.get("name", ""),
                "type": poi.get("type", ""),
                "typecode": poi.get("typecode", ""),
                "address": poi.get("address", ""),
                "location": poi.get("location", ""),
                "tel": poi.get("tel", ""),
                "distance": poi.get("distance", ""),
                "business_area": poi.get("business_area", ""),
                "timestamp": datetime.now().isoformat()
            }
            parsed_pois.append(parsed_poi)
        return parsed_pois
    
    def _get_default_search_result(self, query: str, search_type: str) -> Dict[str, Any]:
        """返回默认搜索结果"""
        return {
            "service": "poi_search",
            "search_type": search_type,
            "query": query,
            "total_count": 0,
            "pois": [],
            "error": "POI搜索暂时不可用",
            "timestamp": datetime.now().isoformat(),
            "api_source": "default"
        }

class MCPServiceManager:
    """MCP服务管理器"""
    
    def __init__(self):
        self.weather_service = WeatherMCPService()
        self.crowd_service = CrowdMCPService()
        self.traffic_service = TrafficMCPService()  # 现在是实例方法
        self.navigation_service = NavigationMCPService()  # 新增导航服务
        self.poi_search_service = POISearchMCPService()  # 新增POI搜索服务
        logger.info("🚀 MCP服务管理器初始化完成")
        
    def get_comprehensive_info(self, attraction: str, origin: str = "市中心", include_forecast: bool = True) -> Dict[str, Any]:
        """
        获取景点的综合信息（天气+人流+交通+天气预报）
        """
        logger.info(f"正在获取 {attraction} 的综合信息...")
        
        weather_info = self.weather_service.get_weather(attraction)
        crowd_info = self.crowd_service.get_crowd_info(attraction)
        traffic_info = self.traffic_service.get_traffic_info(attraction, origin)
        
        result = {
            "attraction": attraction,
            "weather": weather_info,
            "crowd": crowd_info,
            "traffic": traffic_info,
            "query_time": datetime.now().isoformat(),
            "services_used": ["weather", "crowd", "traffic"]
        }
        
        # 添加天气预报
        if include_forecast:
            try:
                forecast_info = self.weather_service.get_weather_forecast("上海", 3)
                result["weather_forecast"] = forecast_info
                result["services_used"].append("weather_forecast")
                logger.info("✅ 已获取3天天气预报")
            except Exception as e:
                logger.warning(f"⚠️ 获取天气预报失败: {e}")
                result["weather_forecast"] = None
        
        return result
    
    def get_route_traffic_analysis(self, attractions: List[str]) -> Dict[str, Any]:
        """
        获取路线交通分析 - MCP框架接口
        """
        logger.info(f"正在分析路线交通: {' -> '.join(attractions)}")
        return self.traffic_service.get_route_traffic_analysis(attractions)
    
    def get_navigation_planning(self, origin: str, destination: str, strategy: str = "default", 
                              waypoints: List[str] = None, **kwargs) -> Dict[str, Any]:
        """
        获取导航路径规划 - MCP框架接口
        """
        logger.info(f"正在规划从 {origin} 到 {destination} 的导航路线")
        return self.navigation_service.get_route_planning(origin, destination, strategy, waypoints, **kwargs)
    
    def get_multi_destination_planning(self, origin: str, destinations: List[str], 
                                     strategy: str = "default") -> Dict[str, Any]:
        """
        多目的地路径规划 - MCP框架接口
        """
        logger.info(f"正在规划多目的地路线: {origin} -> {' -> '.join(destinations)}")
        return self.navigation_service.get_multi_destination_planning(origin, destinations, strategy)
    
    def search_poi_by_keyword(self, keywords: str, region: str = "上海", types: List[str] = None, 
                             page_size: int = 10) -> Dict[str, Any]:
        """根据关键字搜索POI"""
        logger.info(f"正在搜索POI关键字: {keywords}")
        return self.poi_search_service.text_search(keywords, region, True, types, page_size)
    
    def search_poi_around(self, location: str, keywords: str = None, types: List[str] = None, 
                         radius: int = 5000) -> Dict[str, Any]:
        """搜索周边POI"""
        logger.info(f"正在搜索周边POI: {location}")
        return self.poi_search_service.around_search(location, keywords, types, radius)
    
    def get_poi_recommendations_for_travel(self, destination: str, travel_type: str = "tourism") -> Dict[str, Any]:
        """为旅游目的地获取POI推荐"""
        # 获取目的地坐标
        destination_coords = Config.SHANGHAI_ATTRACTION_COORDINATES.get(destination)
        if not destination_coords:
            logger.warning(f"未找到 {destination} 的坐标信息")
            return {"error": f"未找到 {destination} 的坐标信息"}
        
        # 根据旅游类型选择POI类型
        poi_types_map = {
            "tourism": ["110000", "050000", "060000"],  # 景点、餐饮、购物
            "business": ["120000", "070000", "100000"],  # 商务、生活服务、住宿
            "leisure": ["080000", "050000", "110101"]    # 娱乐、餐饮、公园
        }
        
        poi_types = poi_types_map.get(travel_type, ["110000", "050000", "060000"])
        
        # 搜索周边POI
        return self.search_poi_around(destination_coords, types=poi_types, radius=3000)
    
    def analyze_query(self, query: str) -> List[str]:
        """
        分析用户查询，确定需要调用的服务
        """
        services = []
        
        # 天气相关关键词
        weather_keywords = ["天气", "温度", "下雨", "晴天", "阴天", "气温", "湿度", "风", "空气"]
        if any(keyword in query for keyword in weather_keywords):
            services.append("weather")
        
        # 人流相关关键词
        crowd_keywords = ["人多", "排队", "拥挤", "人流", "等待", "繁忙", "游客"]
        if any(keyword in query for keyword in crowd_keywords):
            services.append("crowd")
        
        # 交通相关关键词
        traffic_keywords = ["交通", "路况", "拥堵", "堵车"]
        if any(keyword in query for keyword in traffic_keywords):
            services.append("traffic")
        
        # 导航相关关键词
        navigation_keywords = ["怎么去", "路线", "导航", "开车", "自驾", "驾车", "路径", "规划", "路程", "距离", "时间"]
        if any(keyword in query for keyword in navigation_keywords):
            services.append("navigation")
        
        # 如果没有匹配到特定服务，返回所有服务
        if not services:
            services = ["weather", "crowd", "traffic"]
        
        return services
    
    def get_targeted_info(self, attraction: str, query: str, origin: str = "市中心") -> Dict[str, Any]:
        """
        根据查询内容获取针对性信息
        """
        services_needed = self.analyze_query(query)
        result = {
            "attraction": attraction,
            "query": query,
            "services_used": services_needed,
            "query_time": datetime.now().isoformat()
        }
        
        if "weather" in services_needed:
            result["weather"] = self.weather_service.get_weather(attraction)
        
        if "crowd" in services_needed:
            result["crowd"] = self.crowd_service.get_crowd_info(attraction)
        
        if "traffic" in services_needed:
            result["traffic"] = self.traffic_service.get_traffic_info(attraction, origin)
        
        if "navigation" in services_needed:
            result["navigation"] = self.navigation_service.get_route_planning(origin, attraction)
        
        return result
    
    def format_response(self, mcp_results: Dict[str, Any], query: str) -> str:
        """
        格式化MCP服务响应为用户友好的文本
        """
        if not mcp_results:
            return "暂无实时信息"
        
        response_parts = []
        attraction = mcp_results.get('attraction', '指定地点')
        
        response_parts.append(f"📍 {attraction} 实时信息")
        response_parts.append("=" * 30)
        
        # 天气信息
        if 'weather' in mcp_results:
            weather = mcp_results['weather']
            response_parts.append(f"🌤️ 天气: {weather.get('weather', '未知')} {weather.get('temperature', '未知')}")
            response_parts.append(f"💧 湿度: {weather.get('humidity', '未知')} | 🌬️ 风力: {weather.get('wind', '未知')}")
            response_parts.append(f"🌍 空气质量: {weather.get('air_quality', '未知')}")
            if weather.get('recommendation'):
                response_parts.append(f"💡 建议: {weather['recommendation']}")
        
        # 人流信息
        if 'crowd' in mcp_results:
            crowd = mcp_results['crowd']
            response_parts.append(f"👥 人流状况: {crowd.get('crowd_level', '未知')}")
            response_parts.append(f"⏰ 预计等待: {crowd.get('wait_time', '未知')}")
            if crowd.get('best_visit_time'):
                response_parts.append(f"🎯 最佳时间: {crowd['best_visit_time']}")
            if crowd.get('recommendation'):
                response_parts.append(f"💡 建议: {crowd['recommendation']}")
        
        # 交通信息
        if 'traffic' in mcp_results:
            traffic = mcp_results['traffic']
            response_parts.append(f"🚇 总体交通: {traffic.get('traffic_status', '未知')}")
            response_parts.append(f"⏱️ 预计时间: {traffic.get('estimated_time', '未知')}")
            response_parts.append(f"🎯 推荐出行: {traffic.get('best_route', '未知')}")
            
            # 显示具体道路状况
            if traffic.get('road_traffic_details'):
                response_parts.append("📍 周边道路状况:")
                for road_info in traffic['road_traffic_details']:
                    road_name = road_info.get('road_name', '未知道路')
                    road_status = road_info.get('status', '未知')
                    road_speed = road_info.get('speed', '未知')
                    status_emoji = {"畅通": "🟢", "缓慢": "🟡", "拥堵": "🟠", "严重拥堵": "🔴"}.get(road_status, "⚪")
                    response_parts.append(f"  {status_emoji} {road_name}: {road_status} ({road_speed})")
            
            if traffic.get('recommendation'):
                response_parts.append(f"💡 建议: {traffic['recommendation']}")
        
        # 导航信息
        if 'navigation' in mcp_results:
            navigation = mcp_results['navigation']
            response_parts.append(f"🧭 驾车导航: {navigation.get('route_summary', '未知')}")
            response_parts.append(f"📍 路线: {navigation.get('origin', '起点')} → {navigation.get('destination', '终点')}")
            response_parts.append(f"📏 距离: {navigation.get('distance', '未知')} | ⏱️ 时长: {navigation.get('duration', '未知')}")
            response_parts.append(f"💰 过路费: {navigation.get('tolls', '未知')} | 🚦 红绿灯: {navigation.get('traffic_lights', '未知')}")
            
            if navigation.get('restriction_status'):
                response_parts.append(f"🚫 限行: {navigation['restriction_status']}")
            
            if navigation.get('advice'):
                response_parts.append(f"💡 导航建议: {navigation['advice']}")
            
            # 显示完整的导航步骤
            if navigation.get('navigation_steps'):
                steps = navigation['navigation_steps']
                total_steps = navigation.get('total_steps', len(steps))
                
                response_parts.append(f"🗺️ 详细导航路线（共{total_steps}步）:")
                for step in steps:
                    instruction = step.get('instruction', '')
                    distance = step.get('distance', '')
                    road = step.get('road', '')
                    road_info = f" - {road}" if road else ""
                    response_parts.append(f"  {step['step']}. {instruction} ({distance}){road_info}")
                
                # 如果有路径轨迹信息
                if navigation.get('polyline'):
                    response_parts.append(f"📍 路径轨迹已获取，可用于地图显示")
                
                # 显示完整路径数据信息
                if navigation.get('complete_route_data'):
                    alt_routes = navigation.get('alternative_routes', 0)
                    if alt_routes > 1:
                        response_parts.append(f"🛣️ 共有{alt_routes}条可选路线")
        
        # 天气预报信息
        if 'weather_forecast' in mcp_results and mcp_results['weather_forecast']:
            forecast = mcp_results['weather_forecast']
            if forecast.get('forecasts'):
                response_parts.append("")
                response_parts.append("📅 未来3天天气预报:")
                for i, day_forecast in enumerate(forecast['forecasts'][:3]):
                    date = day_forecast.get('date', '')
                    week_day = day_forecast.get('week', '')
                    day_weather = day_forecast.get('dayweather', '未知')
                    night_weather = day_forecast.get('nightweather', '未知')
                    day_temp = day_forecast.get('daytemp', '未知')
                    night_temp = day_forecast.get('nighttemp', '未知')
                    
                    # 转换星期
                    week_map = {'1': '一', '2': '二', '3': '三', '4': '四', '5': '五', '6': '六', '7': '日'}
                    week_name = f"周{week_map.get(week_day, week_day)}"
                    
                    response_parts.append(f"  {date} ({week_name}): {day_weather}/{night_weather} {day_temp}°C/{night_temp}°C")
        
        return "\n".join(response_parts)

# 用于快速测试的函数
def test_mcp_services():
    """测试MCP服务"""
    manager = MCPServiceManager()
    
    print("=== MCP服务测试 ===")
    
    # 测试综合信息获取
    result = manager.get_comprehensive_info("外滩")
    print(f"外滩综合信息: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    # 测试针对性查询
    targeted_result = manager.get_targeted_info("上海迪士尼", "今天天气怎么样？")
    print(f"针对性查询结果: {json.dumps(targeted_result, ensure_ascii=False, indent=2)}")

if __name__ == "__main__":
    test_mcp_services()

