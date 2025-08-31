# -*- coding: utf-8 -*-
"""
智能旅行对话Agent配置文件
包含所有API密钥和系统配置参数
"""

import os
from typing import Dict, Any

# API密钥配置
API_KEYS = {
    "DOUBAO_API_KEY": "5325ec5a-dd88-417c-bec6-0963d78e1753",
    "AMAP_WEATHER_API_KEY": "eabe457b791e74946b2aeb6a9106b17a",
    "AMAP_TRAFFIC_API_KEY": "425125fef7e244aa380807946ec48776",
    "AMAP_NAVIGATION_API_KEY": "95dfa5cfda994230af9b6ab64de4b84b",
    "AMAP_POI_API_KEY": "f2b480c54a1805d9f6d5aa7b845fc360",
    "AMAP_TRAFFIC_SECURITY_KEY": "425125fef7e244aa380807946ec48776"
}

# 高德地图API配置
AMAP_CONFIG = {
    "base_url": "https://restapi.amap.com/v3",
    "weather_url": "https://restapi.amap.com/v3/weather/weatherInfo",
    "traffic_url": "https://restapi.amap.com/v3/traffic/status/rectangle",
    "navigation_url": "https://restapi.amap.com/v3/direction",
    "poi_url": "https://restapi.amap.com/v3/place/text",
    "geocode_url": "https://restapi.amap.com/v3/geocode/geo",
    "regeocode_url": "https://restapi.amap.com/v3/geocode/regeo"
}

# RAG知识库配置
RAG_CONFIG = {
    "data_dir": "backend/Agent/data",
    "max_results": 10,
    "relevance_threshold": 0.7,
    "max_cache_age": 3600  # 1小时缓存
}

# 系统默认配置
DEFAULT_CONFIG = {
    "default_travel_days": 3,
    "default_transport": "公共交通",
    "default_poi_count": 5,
    "max_route_options": 2,
    "weather_cache_time": 3600,  # 天气数据缓存1小时
    "traffic_cache_time": 1800,  # 路况数据缓存30分钟
}

# 城市代码映射文件
CITY_CODE_FILE = "AMap_adcode_citycode.xlsx"

# 日志配置
LOG_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "agent.log"
}

# 缓存配置
CACHE_CONFIG = {
    "enabled": True,
    "max_size": 1000,
    "ttl": 3600  # 默认1小时过期
}

def get_api_key(service: str) -> str:
    """获取指定服务的API密钥"""
    key_name = f"{service.upper()}_API_KEY"
    return API_KEYS.get(key_name, "")

def get_config() -> Dict[str, Any]:
    """获取完整配置"""
    return {
        "api_keys": API_KEYS,
        "amap": AMAP_CONFIG,
        "rag": RAG_CONFIG,
        "defaults": DEFAULT_CONFIG,
        "city_code_file": CITY_CODE_FILE,
        "log": LOG_CONFIG,
        "cache": CACHE_CONFIG
    }

def validate_config() -> bool:
    """验证配置完整性"""
    required_keys = [
        "DOUBAO_API_KEY",
        "AMAP_WEATHER_API_KEY", 
        "AMAP_TRAFFIC_API_KEY",
        "AMAP_NAVIGATION_API_KEY",
        "AMAP_POI_API_KEY"
    ]
    
    for key in required_keys:
        if not API_KEYS.get(key):
            print(f"警告: 缺少API密钥 {key}")
            return False
    
    return True

if __name__ == "__main__":
    if validate_config():
        print("配置验证通过")
    else:
        print("配置验证失败，请检查API密钥")
