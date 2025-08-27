#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交通态势服务 - 专注于Agent路线规划和出行建议
为Agent提供景点间的交通状况信息，用于动态调整出行建议
"""

import requests
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from config import Config

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TrafficService:
    """交通态势服务 - Agent专用"""
    
    def __init__(self, api_key: str = None):
        """初始化交通服务"""
        self.api_key = api_key or Config.AMAP_TRAFFIC_API_KEY
        self.base_url = Config.AMAP_TRAFFIC_URL
        self.timeout = Config.TRAFFIC_QUERY_TIMEOUT
        
        # 交通状况映射
        self.status_map = {
            "0": {"name": "未知", "level": 0, "emoji": "⚪"},
            "1": {"name": "畅通", "level": 1, "emoji": "🟢"}, 
            "2": {"name": "缓慢", "level": 2, "emoji": "🟡"},
            "3": {"name": "拥堵", "level": 3, "emoji": "🟠"},
            "4": {"name": "严重拥堵", "level": 4, "emoji": "🔴"}
        }
    
    def get_attraction_roads_traffic(self, attraction: str) -> Dict[str, Any]:
        """
        获取景点周边道路交通状况
        用于Agent生成出行建议
        
        Args:
            attraction: 景点名称
            
        Returns:
            景点周边交通状况汇总
        """
        logger.info(f"获取景点 {attraction} 周边交通状况")
        
        # 获取景点配置的道路
        roads = Config.SHANGHAI_ATTRACTION_ROADS.get(attraction, [])
        if not roads:
            return {
                "attraction": attraction,
                "has_traffic_data": False,
                "message": f"景点 {attraction} 未配置道路信息",
                "suggestion": "建议使用地铁等公共交通"
            }
        
        # 获取景点所在区域代码
        adcode = Config.SHANGHAI_ATTRACTION_DISTRICTS.get(attraction, "310000")
        
        # 查询主要道路交通状况
        road_results = []
        total_congestion = 0
        valid_roads = 0
        
        for road in roads[:3]:  # 只查询前3条主要道路
            try:
                result = self._query_single_road(road, adcode)
                if result["success"]:
                    road_results.append(result["data"])
                    # 累计拥堵程度
                    congestion_pct = result["data"].get("congestion_percentage", 0)
                    total_congestion += congestion_pct
                    valid_roads += 1
                    
            except Exception as e:
                logger.warning(f"查询道路 {road} 失败: {e}")
                continue
        
        # 生成交通建议
        if valid_roads == 0:
            return {
                "attraction": attraction,
                "has_traffic_data": False,
                "message": "暂无交通数据",
                "suggestion": "建议使用地铁等公共交通出行"
            }
        
        # 计算平均拥堵程度
        avg_congestion = total_congestion / valid_roads
        traffic_summary = self._generate_traffic_advice(avg_congestion, road_results)
        
        return {
            "attraction": attraction,
            "has_traffic_data": True,
            "roads_checked": len(road_results),
            "average_congestion": f"{avg_congestion:.1f}%",
            "traffic_status": traffic_summary["status"],
            "suggestion": traffic_summary["suggestion"],
            "best_transport": traffic_summary["best_transport"],
            "estimated_time": traffic_summary["estimated_time"],
            "road_details": road_results,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_route_traffic_analysis(self, attractions: List[str]) -> Dict[str, Any]:
        """
        分析整条路线的交通状况
        为Agent提供路线优化建议
        
        Args:
            attractions: 景点列表（按访问顺序）
            
        Returns:
            路线交通分析结果
        """
        logger.info(f"分析路线交通状况: {' -> '.join(attractions)}")
        
        route_analysis = {
            "route": attractions,
            "attractions_traffic": [],
            "overall_status": "畅通",
            "route_suggestions": [],
            "optimal_order": None,
            "timestamp": datetime.now().isoformat()
        }
        
        congestion_levels = []
        
        # 分析每个景点的交通状况
        for attraction in attractions:
            traffic_info = self.get_attraction_roads_traffic(attraction)
            route_analysis["attractions_traffic"].append(traffic_info)
            
            if traffic_info.get("has_traffic_data"):
                # 提取拥堵程度数值
                congestion_str = traffic_info.get("average_congestion", "0%")
                congestion_val = float(congestion_str.replace("%", ""))
                congestion_levels.append({
                    "attraction": attraction,
                    "congestion": congestion_val,
                    "status": traffic_info.get("traffic_status", "未知")
                })
        
        # 生成整体路线建议
        if congestion_levels:
            avg_route_congestion = sum(item["congestion"] for item in congestion_levels) / len(congestion_levels)
            route_analysis["average_route_congestion"] = f"{avg_route_congestion:.1f}%"
            
            # 确定整体状况
            if avg_route_congestion > 40:
                route_analysis["overall_status"] = "拥堵"
                route_analysis["route_suggestions"].append("整体路线拥堵较严重，强烈建议使用地铁")
                route_analysis["route_suggestions"].append("考虑调整游览时间，避开高峰时段")
            elif avg_route_congestion > 25:
                route_analysis["overall_status"] = "缓慢"
                route_analysis["route_suggestions"].append("部分路段有拥堵，建议预留充足时间")
                route_analysis["route_suggestions"].append("可考虑地铁+步行的组合方式")
            else:
                route_analysis["overall_status"] = "畅通"
                route_analysis["route_suggestions"].append("交通状况良好，可按计划出行")
            
            # 识别拥堵最严重的景点
            most_congested = max(congestion_levels, key=lambda x: x["congestion"])
            if most_congested["congestion"] > 30:
                route_analysis["route_suggestions"].append(
                    f"特别注意：{most_congested['attraction']} 周边交通拥堵较严重"
                )
        
        return route_analysis
    
    def _query_single_road(self, road_name: str, adcode: str) -> Dict[str, Any]:
        """查询单条道路交通状况"""
        params = {
            "name": road_name,
            "adcode": adcode,
            "level": 6,  # 查询所有道路等级
            "key": self.api_key,
            "output": "JSON",
            "extensions": "base"
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            api_data = response.json()
            
            if api_data.get("status") != "1":
                error_info = api_data.get("info", "未知错误")
                return {
                    "success": False,
                    "error": error_info,
                    "road_name": road_name
                }
            
            # 解析交通信息
            traffic_info = api_data.get("trafficinfo", {})
            if not traffic_info:
                return {
                    "success": False,
                    "error": "无交通数据",
                    "road_name": road_name
                }
            
            # 提取关键信息
            evaluation = traffic_info.get("evaluation", {})
            status_code = evaluation.get("status", "0")
            description = traffic_info.get("description", "")
            
            # 计算拥堵百分比
            try:
                congested_pct = float(evaluation.get("congested", "0").replace("%", ""))
                blocked_pct = float(evaluation.get("blocked", "0").replace("%", ""))
                total_congestion = congested_pct + blocked_pct
            except (ValueError, AttributeError):
                total_congestion = 0
            
            # 状态信息
            status_info = self.status_map.get(status_code, self.status_map["0"])
            
            return {
                "success": True,
                "road_name": road_name,
                "status": status_info["name"],
                "status_emoji": status_info["emoji"],
                "status_level": status_info["level"],
                "congestion_percentage": total_congestion,
                "description": description,
                "timestamp": datetime.now().strftime("%H:%M")
            }
            
        except Exception as e:
            logger.error(f"查询道路 {road_name} 异常: {e}")
            return {
                "success": False,
                "error": str(e),
                "road_name": road_name
            }
    
    def _generate_traffic_advice(self, avg_congestion: float, road_results: List[Dict]) -> Dict[str, str]:
        """根据交通状况生成出行建议"""
        
        if avg_congestion > 40:
            return {
                "status": "拥堵",
                "suggestion": "周边道路拥堵严重，强烈建议选择地铁出行",
                "best_transport": "地铁",
                "estimated_time": "比平时多30-50分钟"
            }
        elif avg_congestion > 25:
            return {
                "status": "缓慢", 
                "suggestion": "道路略有拥堵，建议地铁出行或预留充足时间",
                "best_transport": "地铁/出租车",
                "estimated_time": "比平时多15-30分钟"
            }
        elif avg_congestion > 10:
            return {
                "status": "基本畅通",
                "suggestion": "交通状况尚可，各种出行方式均可选择",
                "best_transport": "出租车/地铁",
                "estimated_time": "比平时多5-15分钟"
            }
        else:
            return {
                "status": "畅通",
                "suggestion": "交通状况良好，出行便利",
                "best_transport": "出租车/自驾",
                "estimated_time": "正常出行时间"
            }
    
    def format_traffic_advice(self, traffic_info: Dict[str, Any]) -> str:
        """
        格式化交通建议供Agent使用
        
        Args:
            traffic_info: 交通信息字典
            
        Returns:
            格式化的交通建议文本
        """
        if not traffic_info.get("has_traffic_data"):
            return f"📍 {traffic_info['attraction']}: {traffic_info.get('suggestion', '建议使用公共交通')}"
        
        attraction = traffic_info["attraction"]
        status_emoji = "🟢" if traffic_info["traffic_status"] == "畅通" else \
                      "🟡" if traffic_info["traffic_status"] == "缓慢" else \
                      "🟠" if traffic_info["traffic_status"] == "基本畅通" else "🔴"
        
        advice = f"""📍 {attraction} 周边交通：
{status_emoji} 状况：{traffic_info['traffic_status']} (拥堵度：{traffic_info['average_congestion']})
🚇 建议：{traffic_info['suggestion']}
⏱️ 预计：{traffic_info['estimated_time']}"""
        
        return advice

# 便捷函数供Agent调用
def get_attraction_traffic(attraction: str) -> Dict[str, Any]:
    """获取景点交通状况 - Agent专用接口"""
    service = TrafficService()
    return service.get_attraction_roads_traffic(attraction)

def analyze_route_traffic(attractions: List[str]) -> Dict[str, Any]:
    """分析路线交通状况 - Agent专用接口"""
    service = TrafficService()
    return service.get_route_traffic_analysis(attractions)

def format_traffic_for_agent(traffic_info: Dict[str, Any]) -> str:
    """格式化交通信息供Agent回答使用"""
    service = TrafficService()
    return service.format_traffic_advice(traffic_info)
