"""
上海旅游AI系统配置文件
包含MCP服务配置、AI模型配置、系统参数等
"""

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """系统配置类"""
    
    # ==================== AI模型配置 ====================
    # 豆包API配置（保留，作为备选）
    DOUBAO_API_KEY = os.getenv('DOUBAO_API_KEY', '')
    DOUBAO_API_BASE = "https://ark.cn-beijing.volces.com/api/v3"
    DOUBAO_MODEL = "doubao-1-5-pro-32k-250115"
    
    # DeepSeek API配置（主要使用）
    DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')
    DEEPSEEK_API_BASE = "https://api.deepseek.com"
    DEEPSEEK_MODEL = "deepseek-chat"  # 使用非思考模式，如需思考模式可使用 "deepseek-reasoner"
    
    # AI调用参数
    AI_TEMPERATURE = 0.7
    AI_MAX_TOKENS = 2000
    AI_TIMEOUT = 30
    
    # AI Provider选择：'deepseek' 或 'doubao'，默认使用deepseek
    AI_PROVIDER = os.getenv('AI_PROVIDER', 'deepseek').lower()
    
    # ==================== MCP服务配置 ====================
    # MCP服务基础配置
    MCP_BASE_URL = "https://sh-mcp-api.example.com"
    MCP_TIMEOUT = 5
    MCP_RETRY_TIMES = 3
    
    # ==================== 高德地图API配置 ====================
    # 高德地图天气API配置
    AMAP_WEATHER_API_KEY = os.getenv("AMAP_WEATHER_API_KEY", "")
    AMAP_WEATHER_URL = "https://restapi.amap.com/v3/weather/weatherInfo"
    AMAP_CITY_CODE_FILE = "AMap_adcode_citycode.xlsx"
    
    # 高德地图交通态势API配置
    AMAP_TRAFFIC_API_KEY = os.getenv("AMAP_TRAFFIC_API_KEY", "")
    AMAP_TRAFFIC_SECURITY_KEY = os.getenv("AMAP_TRAFFIC_SECURITY_KEY", "")
    AMAP_TRAFFIC_URL = "https://restapi.amap.com/v3/traffic/status/road"
    
    # 高德地图导航API配置
    AMAP_NAVIGATION_API_KEY = os.getenv("AMAP_NAVIGATION_API_KEY", "")
    AMAP_NAVIGATION_URL = "https://restapi.amap.com/v5/direction/driving"
    AMAP_NAVIGATION_TIMEOUT = 10  # 导航API超时时间(秒)
    AMAP_NAVIGATION_RATE_LIMIT = 5  # API调用频率(次/秒)，在3次/s基础上适当放宽
    
    # 高德地图POI搜索API配置
    AMAP_POI_API_KEY = os.getenv("AMAP_POI_API_KEY", "")
    AMAP_POI_TEXT_SEARCH_URL = "https://restapi.amap.com/v5/place/text"  # 关键字搜索
    AMAP_POI_AROUND_SEARCH_URL = "https://restapi.amap.com/v5/place/around"  # 周边搜索
    AMAP_POI_POLYGON_SEARCH_URL = "https://restapi.amap.com/v5/place/polygon"  # 多边形区域搜索
    AMAP_POI_TIMEOUT = 10  # POI搜索API超时时间(秒)
    AMAP_POI_RATE_LIMIT = 10  # POI搜索API调用频率(次/秒)
    
    # 高德地图基础URL
    AMAP_BASE_URL = "https://restapi.amap.com"
    AMAP_GEOCODE_URL = "https://restapi.amap.com/v3/geocode/geo"
    
    # ==================== RAG知识库配置 ====================
    KNOWLEDGE_BASE_PATH = os.path.join(os.path.dirname(__file__), "data")
    MAX_DOCUMENTS = 1000
    CHUNK_SIZE = 500
    MAX_CONTEXT_LENGTH = 1000
    
    # 搜索配置
    MIN_KEYWORD_LENGTH = 2
    MAX_SEARCH_RESULTS = 3
    RELEVANCE_THRESHOLD = 0.1
    
    # ==================== 日志配置 ====================
    LOG_LEVEL = "INFO"
    LOG_FILE = "shanghai_tourism.log"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    
    # ==================== 缓存配置 ====================
    CACHE_ENABLED = True
    CACHE_DURATION = 300  # 5分钟
    WEATHER_CACHE_DURATION = 600  # 10分钟
    TRAFFIC_CACHE_DURATION = 180  # 3分钟
    CROWD_CACHE_DURATION = 300   # 5分钟


# 环境特定配置
class DevelopmentConfig(Config):
    """开发环境配置"""
    LOG_LEVEL = "DEBUG"
    CACHE_ENABLED = False
    MCP_TIMEOUT = 10


class ProductionConfig(Config):
    """生产环境配置"""
    LOG_LEVEL = "WARNING"
    CACHE_ENABLED = True
    MCP_TIMEOUT = 3


class TestingConfig(Config):
    """测试环境配置"""
    LOG_LEVEL = "DEBUG"
    CACHE_ENABLED = False
    MCP_BASE_URL = "http://localhost:8080"


# ==================== 兼容接口 ====================
# 为 enhanced_travel_agent.py 提供兼容的接口

# API Keys字典
API_KEYS = {
    "DOUBAO": os.getenv('DOUBAO_API_KEY', ''),
    "DEEPSEEK": os.getenv('DEEPSEEK_API_KEY', ''),
    "AMAP_WEATHER": os.getenv("AMAP_WEATHER_API_KEY", ""),
    "AMAP_TRAFFIC": os.getenv("AMAP_TRAFFIC_API_KEY", ""),
    "AMAP_NAVIGATION": os.getenv("AMAP_NAVIGATION_API_KEY", ""),
    "AMAP_POI": os.getenv("AMAP_POI_API_KEY", ""),
    "AMAP_PROMPT": os.getenv("AMAP_PROMPT_API_KEY", ""),  # 输入提示API
}

# 高德地图配置字典
AMAP_CONFIG = {
    "base_url": "https://restapi.amap.com",
    "weather_url": "https://restapi.amap.com/v3/weather/weatherInfo",
    "traffic_url": "https://restapi.amap.com/v3/traffic/status/road",
    "navigation_url": "https://restapi.amap.com/v3/direction/driving",  # v3版本
    "transit_url": "https://restapi.amap.com/v3/direction/transit/integrated",  # 公交路径规划
    "walking_url": "https://restapi.amap.com/v3/direction/walking",  # 步行路径规划
    "poi_url": "https://restapi.amap.com/v3/place/text",  # v3版本
    "geocode_url": "https://restapi.amap.com/v3/geocode/geo",
    "inputtips_url": "https://restapi.amap.com/v3/assistant/inputtips",  # 输入提示
}

# RAG配置字典
RAG_CONFIG = {
    "knowledge_base_path": os.path.join(os.path.dirname(__file__), "data"),
    "max_documents": 1000,
    "chunk_size": 500,
    "max_context_length": 1000,
    "min_keyword_length": 2,
    "max_search_results": 3,
    "relevance_threshold": 0.1,
}

# 默认配置字典
DEFAULT_CONFIG = {
    "log_level": "INFO",
    "cache_enabled": True,
    "cache_duration": 300,
    "mcp_timeout": 5,
}


def get_api_key(key_name: str) -> str:
    """获取API密钥
    
    Args:
        key_name: 密钥名称 (DOUBAO, AMAP_WEATHER, AMAP_TRAFFIC, AMAP_NAVIGATION, AMAP_POI)
        
    Returns:
        API密钥字符串
    """
    return API_KEYS.get(key_name, "")


def get_config():
    """根据环境变量获取配置"""
    env = os.getenv('FLASK_ENV', 'development').lower()
    
    config_map = {
        'development': DevelopmentConfig,
        'production': ProductionConfig,
        'testing': TestingConfig
    }
    
    return config_map.get(env, DevelopmentConfig)


# 配置验证
if __name__ == "__main__":
    config = get_config()
    
    print("✅ 配置模块加载成功")
    print("\n📊 当前配置信息：")
    print(f"  环境: {os.getenv('FLASK_ENV', 'development')}")
    print(f"  AI Provider: {Config.AI_PROVIDER}")
    print(f"  DeepSeek API密钥: {'已配置' if API_KEYS['DEEPSEEK'] else '未配置'}")
    print(f"  豆包API密钥: {'已配置' if API_KEYS['DOUBAO'] else '未配置'}")
    print(f"  高德天气API: {'已配置' if API_KEYS['AMAP_WEATHER'] else '未配置'}")
    print(f"  高德交通API: {'已配置' if API_KEYS['AMAP_TRAFFIC'] else '未配置'}")
    print(f"  高德导航API: {'已配置' if API_KEYS['AMAP_NAVIGATION'] else '未配置'}")
    print(f"  高德POI API: {'已配置' if API_KEYS['AMAP_POI'] else '未配置'}")
    print(f"  高德输入提示API: {'已配置' if API_KEYS['AMAP_PROMPT'] else '未配置'}")

