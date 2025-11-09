"""
实时数据采集服务
封装对高德地图等外部API的访问，供推荐引擎调用。
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any, Dict, List, Optional

import requests

from config import AMAP_CONFIG, get_api_key

logger = logging.getLogger(__name__)


class RealtimeDataService:
    """提供天气、POI等实时数据的统一访问接口"""

    def __init__(self) -> None:
        self.weather_key = get_api_key("AMAP_WEATHER")
        self.poi_key = get_api_key("AMAP_POI")
        self.prompt_key = get_api_key("AMAP_PROMPT")

        if not self.weather_key:
            logger.warning("AMAP_WEATHER_API_KEY 未配置，天气数据将使用占位信息。")
        if not self.poi_key:
            logger.warning("AMAP_POI_API_KEY 未配置，POI数据将使用占位信息。")

    def _request(self, url: str, params: Dict[str, Any], name: str) -> Dict[str, Any]:
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get("status") != "1":
                logger.warning("%s 接口返回异常: %s", name, data.get("info", "未知错误"))
            return data
        except Exception as exc:
            logger.error("调用 %s 接口失败: %s", name, exc)
            return {}

    @lru_cache(maxsize=32)
    def fetch_weather(self, city: str) -> Dict[str, Any]:
        """获取指定城市的天气信息"""
        if not self.weather_key:
            return {}

        params = {
            "key": self.weather_key,
            "city": city,
            "extensions": "all",  # 返回多日预报
            "output": "JSON",
        }
        return self._request(AMAP_CONFIG["weather_url"], params, "weather")

    def fetch_poi(
        self,
        city: str,
        keyword: str,
        category: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """根据关键词搜索POI"""
        if not self.poi_key:
            return []

        params = {
            "key": self.poi_key,
            "keywords": keyword,
            "city": city,
            "citylimit": "true",
            "extensions": "all",
            "offset": min(limit, 20),
            "page": 1,
        }
        if category:
            params["types"] = category

        data = self._request(AMAP_CONFIG["poi_url"], params, "poi_text_search")
        return data.get("pois", []) if data else []

    def fetch_input_tips(self, keyword: str, city: str = "上海") -> List[Dict[str, Any]]:
        """调用输入提示API，辅助地点识别"""
        if not self.prompt_key:
            return []

        params = {
            "key": self.prompt_key,
            "keywords": keyword,
            "city": city,
            "citylimit": "true",
            "output": "JSON",
        }
        data = self._request(AMAP_CONFIG["inputtips_url"], params, "inputtips")
        return data.get("tips", []) if data else []


# 单例实例，避免重复初始化
realtime_service = RealtimeDataService()


