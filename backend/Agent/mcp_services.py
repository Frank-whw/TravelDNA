"""
上海旅游AI - MCP服务模块
实现天气、人流量、交通等MCP服务调用
"""
import requests
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

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
    """天气MCP服务"""
    
    @classmethod
    def get_weather(cls, attraction: str) -> Dict[str, Any]:
        """
        获取指定景点的天气信息
        """
        params = {
            "location": attraction,
            "city": "上海",
            "type": "current"
        }
        
        data = cls.fetch_data("/weather", params)
        
        if data:
            return {
                "service": "weather",
                "location": attraction,
                "temperature": data.get("temperature", "未知"),
                "weather": data.get("weather", "未知"),
                "humidity": data.get("humidity", "未知"),
                "wind": data.get("wind", "未知"),
                "air_quality": data.get("air_quality", "未知"),
                "recommendation": data.get("recommendation", ""),
                "timestamp": datetime.now().isoformat()
            }
        else:
            # 返回默认数据
            return {
                "service": "weather",
                "location": attraction,
                "temperature": "22°C",
                "weather": "多云",
                "humidity": "65%",
                "wind": "微风",
                "air_quality": "良",
                "recommendation": "天气适宜出行，建议携带薄外套",
                "timestamp": datetime.now().isoformat(),
                "fallback": True
            }

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
    """交通MCP服务"""
    
    @classmethod
    def get_traffic_info(cls, attraction: str, origin: str = "市中心") -> Dict[str, Any]:
        """
        获取到指定景点的交通信息
        """
        params = {
            "destination": attraction,
            "origin": origin,
            "city": "上海",
            "type": "realtime"
        }
        
        data = cls.fetch_data("/traffic", params)
        
        if data:
            return {
                "service": "traffic",
                "destination": attraction,
                "origin": origin,
                "routes": data.get("routes", []),
                "estimated_time": data.get("estimated_time", "未知"),
                "traffic_status": data.get("traffic_status", "未知"),
                "best_route": data.get("best_route", ""),
                "alternative_routes": data.get("alternative_routes", []),
                "recommendation": data.get("recommendation", ""),
                "timestamp": datetime.now().isoformat()
            }
        else:
            # 返回默认数据
            return {
                "service": "traffic",
                "destination": attraction,
                "origin": origin,
                "routes": [
                    {"type": "地铁", "time": "30-45分钟", "cost": "6-8元"},
                    {"type": "出租车", "time": "20-40分钟", "cost": "50-80元"},
                    {"type": "公交", "time": "45-60分钟", "cost": "2-4元"}
                ],
                "estimated_time": "30-45分钟",
                "traffic_status": "畅通",
                "best_route": "地铁",
                "alternative_routes": ["出租车", "公交"],
                "recommendation": "推荐使用地铁出行，准时便捷",
                "timestamp": datetime.now().isoformat(),
                "fallback": True
            }

class MCPServiceManager:
    """MCP服务管理器"""
    
    def __init__(self):
        self.weather_service = WeatherMCPService()
        self.crowd_service = CrowdMCPService()
        self.traffic_service = TrafficMCPService()
        
    def get_comprehensive_info(self, attraction: str, origin: str = "市中心") -> Dict[str, Any]:
        """
        获取景点的综合信息（天气+人流+交通）
        """
        logger.info(f"正在获取 {attraction} 的综合信息...")
        
        weather_info = self.weather_service.get_weather(attraction)
        crowd_info = self.crowd_service.get_crowd_info(attraction)
        traffic_info = self.traffic_service.get_traffic_info(attraction, origin)
        
        return {
            "attraction": attraction,
            "weather": weather_info,
            "crowd": crowd_info,
            "traffic": traffic_info,
            "query_time": datetime.now().isoformat(),
            "services_used": ["weather", "crowd", "traffic"]
        }
    
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
        crowd_keywords = ["多人", "排队", "拥挤", "人流", "等待", "繁忙", "游客"]
        if any(keyword in query for keyword in crowd_keywords):
            services.append("crowd")
        
        # 交通相关关键词
        traffic_keywords = ["交通", "怎么去", "路线", "地铁", "公交", "打车", "开车", "导航"]
        if any(keyword in query for keyword in traffic_keywords):
            services.append("traffic")
        
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
        
        return result
    
    # 新增：从查询中提取地点的简易方法（与集成器保持一致的地点词表）
    def _extract_location(self, query: str) -> str:
        locations = [
            '外滩', '东方明珠', '豫园', '城隍庙', '南京路', '新天地', '田子坊',
            '朱家角', '七宝古镇', '上海博物馆', '上海科技馆', '迪士尼', '野生动物园',
            '植物园', '中山公园', '人民广场', '陆家嘴', '静安寺', '徐家汇',
            '虹桥', '浦东机场', '虹桥机场', '黄浦江', '苏州河', '世博园',
            '上海大剧院', '音乐厅', '美术馆', '自然博物馆', '海洋馆'
        ]
        for loc in locations:
            if loc in query:
                return loc
        return "上海市中心"
    
    # 新增：供集成器调用的统一接口
    def get_integrated_info(self, query: str, attraction: Optional[str] = None, origin: str = "市中心") -> Dict[str, Any]:
        """
        统一的综合信息获取接口。
        - 若未提供 attraction，则从 query 中尝试提取地点，默认“上海市中心”。
        - 内部根据 query 自动挑选需要的服务。
        """
        target_attraction = attraction or self._extract_location(query)
        return self.get_targeted_info(target_attraction, query, origin)
    
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
            response_parts.append(f"🚇 交通状况: {traffic.get('traffic_status', '未知')}")
            response_parts.append(f"⏱️ 预计时间: {traffic.get('estimated_time', '未知')}")
            response_parts.append(f"🎯 推荐路线: {traffic.get('best_route', '未知')}")
            if traffic.get('recommendation'):
                response_parts.append(f"💡 建议: {traffic['recommendation']}")
        
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

