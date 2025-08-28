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
    # 豆包API配置
    DOUBAO_API_KEY = os.getenv('DOUBAO_API_KEY', '')
    DOUBAO_API_BASE = "https://ark.cn-beijing.volces.com/api/v3"
    DOUBAO_MODEL = "doubao-1-5-pro-32k-250115"
    
    # AI调用参数
    AI_TEMPERATURE = 0.7
    AI_MAX_TOKENS = 2000
    AI_TIMEOUT = 30
    
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
    
    # 导航策略配置
    NAVIGATION_STRATEGIES = {
        "speed_priority": 0,           # 速度优先（仅1条路线）
        "cost_priority": 1,            # 费用优先（仅1条，不走收费路）
        "regular_fastest": 2,          # 常规最快（仅1条，综合距离/耗时）
        "default": 32,                 # 默认（高德推荐，同APP默认）
        "avoid_congestion": 33,        # 躲避拥堵
        "highway_priority": 34,        # 高速优先
        "no_highway": 35,              # 不走高速
        "less_fee": 36,                # 少收费
        "main_road": 37,               # 大路优先
        "fastest": 38,                 # 速度最快
        "avoid_congestion_highway": 39,      # 躲避拥堵+高速优先
        "avoid_congestion_no_highway": 40,   # 躲避拥堵+不走高速
        "avoid_congestion_less_fee": 41,     # 躲避拥堵+少收费
        "less_fee_no_highway": 42,           # 少收费+不走高速
        "comprehensive_avoid": 43,           # 躲避拥堵+少收费+不走高速
        "avoid_congestion_main": 44,         # 躲避拥堵+大路优先
        "avoid_congestion_fastest": 45       # 躲避拥堵+速度最快
    }
    
    # 交通态势查询配置
    TRAFFIC_QUERY_TIMEOUT = 10  # 查询超时时间(秒)
    TRAFFIC_BATCH_SIZE = 5      # 批量查询道路数量限制
    TRAFFIC_CACHE_DURATION = 120 # 交通数据缓存时间(秒)
    
    # 交通状况阈值配置
    TRAFFIC_CONGESTION_THRESHOLDS = {
        "light": 0.3,      # 轻度拥堵阈值
        "moderate": 0.5,   # 中度拥堵阈值  
        "heavy": 0.7       # 重度拥堵阈值
    }
    
    # 上海景点经纬度配置（用于导航API）
    SHANGHAI_ATTRACTION_COORDINATES = {
        # 黄浦区景点
        "外滩": "121.484429,31.240791",
        "豫园": "121.492800,31.228831", 
        "城隍庙": "121.492800,31.228831",
        "南京路": "121.474311,31.235668",
        "南京路步行街": "121.474311,31.235668",
        "人民广场": "121.475049,31.228917",
        "上海博物馆": "121.475049,31.228917",
        "上海大剧院": "121.475049,31.228917",
        "新天地": "121.477419,31.220089",
        "田子坊": "121.466536,31.211037",
        
        # 浦东新区景点
        "东方明珠": "121.506377,31.245105",
        "陆家嘴": "121.506377,31.245105",
        "环球金融中心": "121.506377,31.245105",
        "金茂大厦": "121.506377,31.245105", 
        "上海中心": "121.506377,31.245105",
        "上海科技馆": "121.535530,31.222982",
        "海洋馆": "121.535530,31.222982",
        "迪士尼": "121.656084,31.150625",
        "浦东机场": "121.799320,31.195888",
        "世博园": "121.506377,31.245105",
        
        # 徐汇区景点
        "徐家汇": "121.427700,31.196742",
        "淮海路": "121.471569,31.220587",
        "上海植物园": "121.441354,31.154988",
        
        # 长宁区景点
        "虹桥": "121.350693,31.193895",
        "虹桥机场": "121.350693,31.193895",
        "中山公园": "121.418228,31.223577",
        
        # 静安区景点
        "静安寺": "121.444906,31.227906",
        "上海火车站": "121.458006,31.249162",
        
        # 普陀区景点
        "长风公园": "121.397728,31.252683",
        
        # 虹口区景点
        "四川北路": "121.494382,31.251928",
        "多伦路": "121.494382,31.251928",
        "鲁迅公园": "121.494382,31.251928",
        
        # 杨浦区景点
        "复兴公园": "121.471831,31.232407",
        "共青森林公园": "121.559793,31.305866",
        
        # 其他区域
        "七宝古镇": "121.356476,31.148641",
        "朱家角": "121.061989,31.114396",
        "佘山": "121.181250,31.081250"
    }
    
    # 上海景点到区级代码的映射
    SHANGHAI_ATTRACTION_DISTRICTS = {
        # 黄浦区景点 - 310101
        "外滩": "310101",
        "豫园": "310101", 
        "城隍庙": "310101",
        "南京路": "310101",
        "人民广场": "310101",
        "上海博物馆": "310101",
        "上海大剧院": "310101",
        "音乐厅": "310101",
        "新天地": "310101",
        "田子坊": "310101",
        
        # 浦东新区景点 - 310115
        "东方明珠": "310115",
        "陆家嘴": "310115",
        "环球金融中心": "310115",
        "金茂大厦": "310115",
        "上海中心": "310115",
        "上海科技馆": "310115",
        "海洋馆": "310115",
        "迪士尼": "310115",
        "浦东机场": "310115",
        "世博园": "310115",
        
        # 徐汇区景点 - 310104
        "徐家汇": "310104",
        "上海植物园": "310104",
        "襄阳公园": "310104",
        
        # 长宁区景点 - 310105
        "虹桥": "310105",
        "虹桥机场": "310105",
        "中山公园": "310105",
        
        # 静安区景点 - 310106
        "静安寺": "310106",
        "静安公园": "310106",
        
        # 普陀区景点 - 310107
        "长风公园": "310107",
        
        # 虹口区景点 - 310109
        "四川北路": "310109",
        "多伦路": "310109",
        "鲁迅公园": "310109",
        
        # 杨浦区景点 - 310110
        "复兴公园": "310110",
        "共青森林公园": "310110",
        
        # 闵行区景点 - 310112
        "七宝古镇": "310112",
        
        # 宝山区景点 - 310113
        "滨江森林公园": "310113",
        
        # 嘉定区景点 - 310114
        "嘉定古镇": "310114",
        
        # 松江区景点 - 310117
        "松江大学城": "310117",
        "佘山": "310117",
        
        # 青浦区景点 - 310118
        "朱家角": "310118",
        
        # 金山区景点 - 310116
        "金山海滩": "310116",
        
        # 奉贤区景点 - 310120
        "奉贤海湾": "310120",
        
        # 崇明区景点 - 310151
        "崇明岛": "310151",
        "东滩湿地": "310151"
    }
    
    # 上海景点周边主要道路映射（用于交通态势查询）
    SHANGHAI_ATTRACTION_ROADS = {
        # 黄浦区景点周边道路
        "外滩": ["中山东一路", "南京东路", "北京东路", "延安东路"],
        "豫园": ["人民路", "中华路", "福佑路", "方浜中路"],
        "城隍庙": ["人民路", "中华路", "福佑路"],
        "南京路": ["南京东路", "南京西路", "西藏中路", "河南中路"],
        "人民广场": ["南京西路", "黄陂北路", "西藏中路", "人民大道"],
        "新天地": ["淮海中路", "太仓路", "马当路", "黄陂南路"],
        "田子坊": ["泰康路", "建国中路", "瑞金二路"],
        
        # 浦东新区景点周边道路
        "东方明珠": ["世纪大道", "陆家嘴环路", "浦东南路", "滨江大道"],
        "陆家嘴": ["世纪大道", "陆家嘴环路", "浦东南路", "张杨路"],
        "环球金融中心": ["世纪大道", "陆家嘴环路", "浦东南路"],
        "金茂大厦": ["世纪大道", "陆家嘴环路", "浦东南路"],
        "上海中心": ["世纪大道", "陆家嘴环路", "浦东南路"],
        "上海科技馆": ["世纪大道", "丁香路", "杨高南路"],
        "迪士尼": ["申迪东路", "申迪南路", "康新公路"],
        
        # 徐汇区景点周边道路
        "徐家汇": ["漕溪北路", "华山路", "天钥桥路", "肇嘉浜路"],
        "上海植物园": ["龙吴路", "百色路", "罗城路"],
        
        # 长宁区景点周边道路
        "虹桥": ["虹桥路", "仙霞路", "威宁路", "延安西路"],
        "虹桥机场": ["虹桥路", "迎宾大道", "虹漕路"],
        "中山公园": ["长宁路", "凯旋路", "万航渡路"],
        
        # 静安区景点周边道路
        "静安寺": ["南京西路", "华山路", "常德路", "万航渡路"],
        
        # 普陀区景点周边道路
        "长风公园": ["大渡河路", "金沙江路", "枣阳路"],
        
        # 虹口区景点周边道路
        "四川北路": ["四川北路", "海伦路", "昆山路"],
        "多伦路": ["多伦路", "四川北路", "虹口足球场路"],
        
        # 杨浦区景点周边道路
        "复兴公园": ["雁荡路", "复兴中路", "重庆南路"],
        "共青森林公园": ["军工路", "嫩江路", "共和新路"],
        
        # 其他区域
        "七宝古镇": ["七莘路", "漕宝路", "新镇路"],
        "朱家角": ["朱枫公路", "沈砖公路", "珠溪路"],
        "佘山": ["佘山大道", "外青松公路", "辰花路"]
    }
    
    # POI类型代码配置
    POI_TYPE_CODES = {
        # 餐饮服务
        "restaurant": "050000",           # 餐饮服务总类
        "chinese_food": "050100",         # 中餐厅
        "foreign_food": "050200",         # 外国餐厅
        "fast_food": "050300",            # 快餐厅
        "cafe": "050500",                 # 咖啡厅
        "tea_house": "050600",            # 茶艺馆
        "bar": "050700",                  # 酒吧
        
        # 生活服务
        "life_service": "070000",         # 生活服务总类
        "shopping": "060000",             # 购物服务
        "supermarket": "060101",          # 超市
        "shopping_mall": "060400",        # 购物中心
        "convenience_store": "060102",    # 便利店
        
        # 商务住宅
        "business": "120000",             # 商务住宅总类
        "company": "120100",              # 公司企业
        "hotel": "100000",                # 住宿服务
        
        # 交通设施服务
        "transport": "150000",            # 交通设施服务总类
        "subway": "150500",               # 地铁站
        "bus_stop": "150700",             # 公交车站
        "parking": "150900",              # 停车场
        "gas_station": "160000",          # 加油站
        
        # 旅游景点
        "scenic_spot": "110000",          # 风景名胜
        "park": "110101",                 # 公园
        "museum": "130000",               # 科教文化服务
        "entertainment": "080000",        # 体育休闲服务
        
        # 医疗保健
        "hospital": "090000",             # 医疗保健服务
        "pharmacy": "090600",             # 药店
        
        # 政府机构
        "government": "170000",           # 政府机构及社会团体
        "bank": "160300",                 # 金融保险服务
    }
    
    # 默认搜索类型（常用POI类型）
    DEFAULT_POI_TYPES = [
        "050000",  # 餐饮服务
        "070000",  # 生活服务
        "120000",  # 商务住宅
        "110000",  # 风景名胜
        "080000",  # 体育休闲服务
    ]
    
    # 服务开关（用于调试和维护）
    ENABLE_WEATHER_SERVICE = True
    ENABLE_CROWD_SERVICE = True
    ENABLE_TRAFFIC_SERVICE = True
    ENABLE_NAVIGATION_SERVICE = True
    ENABLE_POI_SEARCH_SERVICE = True
    
    # ==================== 上海地区配置 ====================
    # 支持的上海景点列表
    SHANGHAI_ATTRACTIONS = [
        "外滩", "东方明珠", "豫园", "城隍庙", "南京路", "新天地", "田子坊",
        "朱家角", "七宝古镇", "上海博物馆", "上海科技馆", "迪士尼", "野生动物园",
        "植物园", "中山公园", "人民广场", "陆家嘴", "静安寺", "徐家汇",
        "虹桥", "浦东机场", "虹桥机场", "黄浦江", "苏州河", "世博园",
        "上海大剧院", "音乐厅", "美术馆", "自然博物馆", "海洋馆", "环球金融中心",
        "金茂大厦", "上海中心", "淮海路", "四川北路", "多伦路", "鲁迅公园",
        "复兴公园", "襄阳公园", "长风公园", "共青森林公园", "滨江森林公园"
    ]
    
    # 上海行政区域
    SHANGHAI_DISTRICTS = [
        "黄浦区", "徐汇区", "长宁区", "静安区", "普陀区", "虹口区", "杨浦区",
        "闵行区", "宝山区", "嘉定区", "浦东新区", "金山区", "松江区", 
        "青浦区", "奉贤区", "崇明区"
    ]
    
    # ==================== 服务质量配置 ====================
    # 响应时间配置（秒）
    RESPONSE_TIME_EXCELLENT = 2.0
    RESPONSE_TIME_GOOD = 5.0
    RESPONSE_TIME_ACCEPTABLE = 10.0
    
    # 缓存配置
    CACHE_ENABLED = True
    CACHE_DURATION = 300  # 5分钟
    WEATHER_CACHE_DURATION = 600  # 10分钟
    TRAFFIC_CACHE_DURATION = 180  # 3分钟
    CROWD_CACHE_DURATION = 300   # 5分钟
    
    # ==================== 数据源配置 ====================
    # 知识库配置
    KNOWLEDGE_BASE_PATH = "./data"
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
    
    # ==================== 安全配置 ====================
    # API调用限制
    MAX_REQUESTS_PER_MINUTE = 60
    MAX_REQUESTS_PER_HOUR = 1000
    
    # 输入验证
    MAX_QUERY_LENGTH = 500
    BLOCKED_KEYWORDS = ["admin", "root", "system", "delete"]
    
    # ==================== 特性开关 ====================
    # 功能开关
    ENABLE_ROUTE_PLANNING = True
    ENABLE_WEATHER_ADVICE = True
    ENABLE_CROWD_PREDICTION = True
    ENABLE_TRAFFIC_OPTIMIZATION = True
    
    # 实验性功能
    ENABLE_SENTIMENT_ANALYSIS = False
    ENABLE_IMAGE_RECOGNITION = False
    ENABLE_VOICE_INTERACTION = False
    
    # ==================== MCP服务具体配置 ====================
    
    class WeatherConfig:
        """天气服务配置"""
        API_ENDPOINTS = {
            "current": "/weather/current",
            "forecast": "/weather/forecast",
            "historical": "/weather/historical"
        }
        DEFAULT_FORECAST_DAYS = 3
        WEATHER_ALERT_THRESHOLD = {
            "temperature_high": 35,
            "temperature_low": 0,
            "wind_speed": 20,
            "rainfall": 50
        }
    
    class CrowdConfig:
        """人流量服务配置"""
        API_ENDPOINTS = {
            "realtime": "/crowd/realtime",
            "prediction": "/crowd/prediction",
            "historical": "/crowd/historical"
        }
        CROWD_LEVELS = {
            "empty": (0, 20),
            "light": (20, 40),
            "moderate": (40, 60),
            "heavy": (60, 80),
            "extreme": (80, 100)
        }
        PEAK_HOURS = {
            "weekday": ["09:00-11:00", "14:00-17:00"],
            "weekend": ["10:00-12:00", "14:00-18:00", "19:00-21:00"]
        }
    
    class TrafficConfig:
        """交通服务配置"""
        API_ENDPOINTS = {
            "realtime": "/traffic/realtime", 
            "routes": "/traffic/routes",
            "incidents": "/traffic/incidents"
        }
        CONGESTION_LEVELS = [
            "畅通", "缓慢", "拥堵", "严重拥堵"
        ]
        TRANSPORT_TYPES = [
            "地铁", "公交", "出租车", "私家车", "共享单车", "步行"
        ]
    
    class NavigationConfig:
        """导航服务配置"""
        API_ENDPOINTS = {
            "driving": "/navigation/driving",
            "walking": "/navigation/walking", 
            "transit": "/navigation/transit"
        }
        DEFAULT_STRATEGY = "default"
        MAX_WAYPOINTS = 16
        MAX_AVOID_POLYGONS = 32
        VEHICLE_TYPES = {
            "fuel": 0,        # 普通燃油汽车
            "electric": 1,    # 纯电动汽车
            "hybrid": 2       # 插电式混动汽车
        }
        OUTPUT_FIELDS = [
            "polyline", "restriction", "cost", "distance", 
            "duration", "strategy", "tolls", "traffic_lights"
        ]
    
    # ==================== 用户体验配置 ====================
    # 响应格式配置
    USE_EMOJI = True
    USE_MARKDOWN = True
    RESPONSE_LANGUAGE = "中文"
    
    # 个性化配置
    REMEMBER_USER_PREFERENCES = False  # 需要数据库支持
    SUGGEST_ALTERNATIVES = True
    PROVIDE_DETAILED_INFO = True
    
    @classmethod
    def validate_config(cls):
        """验证配置有效性"""
        errors = []
        
        # 检查必需的API密钥
        if not cls.DOUBAO_API_KEY:
            errors.append("缺少DOUBAO_API_KEY配置")
        
        # 检查配置值范围
        if cls.AI_TEMPERATURE < 0 or cls.AI_TEMPERATURE > 2:
            errors.append("AI_TEMPERATURE应在0-2之间")
        
        if cls.CACHE_DURATION < 60:
            errors.append("CACHE_DURATION不应小于60秒")
        
        # 检查文件路径
        if not os.path.exists(cls.KNOWLEDGE_BASE_PATH):
            errors.append(f"知识库路径不存在: {cls.KNOWLEDGE_BASE_PATH}")
        
        return errors
    
    @classmethod
    def get_debug_info(cls):
        """获取调试信息"""
        return {
            "AI配置": {
                "模型": cls.DOUBAO_MODEL,
                "温度": cls.AI_TEMPERATURE,
                "最大令牌": cls.AI_MAX_TOKENS
            },
            "MCP服务": {
                "基础URL": cls.MCP_BASE_URL,
                "超时时间": cls.MCP_TIMEOUT,
                "天气服务": "启用" if cls.ENABLE_WEATHER_SERVICE else "禁用",
                "人流服务": "启用" if cls.ENABLE_CROWD_SERVICE else "禁用",
                "交通服务": "启用" if cls.ENABLE_TRAFFIC_SERVICE else "禁用"
            },
            "知识库": {
                "路径": cls.KNOWLEDGE_BASE_PATH,
                "最大文档数": cls.MAX_DOCUMENTS,
                "块大小": cls.CHUNK_SIZE
            },
            "缓存": {
                "启用": cls.CACHE_ENABLED,
                "默认时长": cls.CACHE_DURATION,
                "天气缓存": cls.WEATHER_CACHE_DURATION,
                "交通缓存": cls.TRAFFIC_CACHE_DURATION
            }
        }


# 环境特定配置
class DevelopmentConfig(Config):
    """开发环境配置"""
    LOG_LEVEL = "DEBUG"
    CACHE_ENABLED = False
    MCP_TIMEOUT = 10
    ENABLE_SENTIMENT_ANALYSIS = True


class ProductionConfig(Config):
    """生产环境配置"""
    LOG_LEVEL = "WARNING"
    CACHE_ENABLED = True
    MCP_TIMEOUT = 3
    MAX_REQUESTS_PER_MINUTE = 30


class TestingConfig(Config):
    """测试环境配置"""
    LOG_LEVEL = "DEBUG"
    CACHE_ENABLED = False
    MCP_BASE_URL = "http://localhost:8080"
    ENABLE_WEATHER_SERVICE = False
    ENABLE_CROWD_SERVICE = False
    ENABLE_TRAFFIC_SERVICE = False


# 根据环境变量选择配置
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
    errors = config.validate_config()
    
    if errors:
        print("❌ 配置验证失败：")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✅ 配置验证通过")
        print("\n📊 当前配置信息：")
        debug_info = config.get_debug_info()
        
        for category, info in debug_info.items():
            print(f"\n{category}:")
            for key, value in info.items():
                print(f"  {key}: {value}")

