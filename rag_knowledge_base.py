#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG知识库模块 - 为智能旅行攻略提供深度知识支持
包含景点详细信息、隐藏玩法、实用贴士等
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class RAGKnowledgeBase:
    """RAG知识库 - 上海旅游深度知识"""
    
    def __init__(self):
        """初始化RAG知识库"""
        
        # 核心景点深度知识
        self.attractions_knowledge = {
            "外滩": {
                "overview": "上海最著名的滨江风景线，汇集了上海滩最精华的城市景观",
                "best_time": {
                    "optimal": "傍晚18:00-20:00",
                    "reason": "日落时分可以看到黄浦江两岸从白天到夜晚的完美过渡",
                    "alternative": "早上7:00-9:00人少景美，适合拍照"
                },
                "photo_spots": [
                    {"name": "外白渡桥", "tip": "经典角度拍摄浦东天际线", "best_time": "日落前30分钟"},
                    {"name": "和平饭店老楼", "tip": "复古建筑与现代建筑对比", "best_time": "任何时间"},
                    {"name": "十六铺码头", "tip": "低机位拍摄外滩建筑群", "best_time": "黄昏时分"},
                    {"name": "外滩源33号观景台", "tip": "免费观景台，人少视野好", "best_time": "避开周末"}
                ],
                "insider_tips": [
                    "避开国庆黄金周，人流是平时的5-10倍",
                    "工作日早晨最安静，适合深度游览",
                    "外滩18号顶层餐厅景观绝佳但价格昂贵",
                    "地铁2号线南京东路站2号出口最近"
                ],
                "hidden_gems": [
                    "外滩源33号免费观景台，很多人不知道",
                    "和平饭店爵士酒吧，周五晚上有现场演出",
                    "外滩历史纪念馆，了解外滩百年变迁",
                    "外滩隧道观光廊，独特的江底体验"
                ],
                "nearby_food": [
                    {"name": "外滩18号", "type": "高端餐厅", "specialty": "法餐", "price": "人均500+", "view": "黄浦江景观"},
                    {"name": "老正兴", "type": "本帮菜", "specialty": "上海菜", "price": "人均150", "note": "百年老店"},
                    {"name": "小南国", "type": "粤菜", "specialty": "港式茶点", "price": "人均200", "note": "环境优雅"},
                    {"name": "BFC外滩金融中心", "type": "美食城", "specialty": "各国料理", "price": "人均80-200", "note": "选择丰富"}
                ],
                "practical_info": {
                    "opening_hours": "全天开放",
                    "ticket_price": "免费",
                    "transportation": ["地铁2号线南京东路站", "地铁10号线南京东路站", "公交20路、37路"],
                    "parking": "外滩中心停车场，30元/小时",
                    "facilities": ["公共洗手间", "无障碍通道", "观光长椅"]
                }
            },
            
            "东方明珠": {
                "overview": "上海地标性建筑，468米高的电视塔，浦东新区的象征",
                "best_time": {
                    "optimal": "日落前1小时登塔",
                    "reason": "可以同时欣赏到白天的城市全景和夜晚的璀璨灯光",
                    "alternative": "晴朗天气的上午，能见度最高"
                },
                "photo_spots": [
                    {"name": "259米主观光层", "tip": "360度全景视角", "best_time": "日落时分"},
                    {"name": "263米悬空观光廊", "tip": "脚下就是上海", "best_time": "白天，看得更清楚"},
                    {"name": "太空舱", "tip": "科幻感十足的拍照背景", "best_time": "任何时间"},
                    {"name": "塔底广场", "tip": "仰拍整个明珠塔", "best_time": "夜晚，配合灯光效果"}
                ],
                "insider_tips": [
                    "网上购票比现场便宜约30-50元",
                    "下载'东方明珠'APP可获得导览信息",
                    "B1层有免费的上海城市历史发展陈列馆",
                    "高峰期排队等电梯需要30-60分钟",
                    "259米和263米票价不同，建议选择263米套票"
                ],
                "hidden_gems": [
                    "零米大厅的上海城市历史发展陈列馆免费参观",
                    "旋转餐厅可以边用餐边360度观景",
                    "城市历史发展陈列馆有很多老上海珍贵照片",
                    "塔内邮局可以买到特色明信片"
                ],
                "nearby_food": [
                    {"name": "东方明珠旋转餐厅", "type": "观景餐厅", "specialty": "自助餐", "price": "人均300+", "view": "360度城景"},
                    {"name": "陆家嘴正大广场", "type": "购物中心", "specialty": "各国美食", "price": "人均50-200", "note": "距离500米"},
                    {"name": "IFC国金中心", "type": "高端商场", "specialty": "精品餐厅", "price": "人均200+", "note": "距离800米"},
                    {"name": "滨江大道小食", "type": "街边小食", "specialty": "简餐", "price": "人均30-50", "note": "江边美食"}
                ],
                "practical_info": {
                    "opening_hours": "8:00-21:30（最晚入场21:00）",
                    "ticket_price": "A票160元（263米），B票120元（259米），C票80元（220米）",
                    "transportation": ["地铁2号线陆家嘴站", "观光巴士", "轮渡"],
                    "parking": "东方明珠停车场，首小时免费",
                    "facilities": ["观光电梯", "餐厅", "纪念品店", "洗手间"]
                }
            },
            
            "上海迪士尼乐园": {
                "overview": "中国大陆首座迪士尼主题乐园，融合迪士尼经典与中国文化特色",
                "best_time": {
                    "optimal": "开园前30分钟到达",
                    "reason": "避开人潮，直奔热门项目如创极速光轮、飞跃地平线",
                    "alternative": "工作日比周末人少50%以上"
                },
                "photo_spots": [
                    {"name": "奇幻童话城堡", "tip": "正面拍摄最经典", "best_time": "早上10点前或傍晚"},
                    {"name": "米奇大街", "tip": "入园第一拍照点", "best_time": "刚入园时"},
                    {"name": "创极速光轮", "tip": "科技感外观很酷", "best_time": "夜晚灯光效果最佳"},
                    {"name": "宝藏湾海盗船", "tip": "冒险岛风格", "best_time": "白天拍摄细节"}
                ],
                "insider_tips": [
                    "下载官方APP可预约快速通行证（免费）",
                    "入园安检不能带自拍杆和大型三脚架",
                    "园内餐饮价格较高，可在迪士尼小镇用餐",
                    "烟花表演最佳观赏位置是城堡前广场",
                    "雨天部分室外项目会暂停，但人流会减少"
                ],
                "hidden_gems": [
                    "创极速光轮夜晚体验比白天更震撼",
                    "加勒比海盗船排队区域有很多细节可以拍照",
                    "奇幻童话城堡内部可以参观，很多人不知道",
                    "晚上的灯光秀从不同角度观看效果不同"
                ],
                "nearby_food": [
                    {"name": "迪士尼小镇", "type": "主题餐厅", "specialty": "各国料理", "price": "人均100-300", "note": "园外，价格比园内便宜"},
                    {"name": "皇家宴会厅", "type": "园内餐厅", "specialty": "公主主题", "price": "人均200+", "note": "需要预约"},
                    {"name": "奕欧来奥特莱斯", "type": "购物中心", "specialty": "美食广场", "price": "人均50-150", "note": "距离3公里"}
                ],
                "practical_info": {
                    "opening_hours": "8:00/9:00-21:00/22:00（季节性调整）",
                    "ticket_price": "平日399元，高峰期599元，节假日719元",
                    "transportation": ["地铁11号线迪士尼站", "公交申迪东路站"],
                    "parking": "停车费100元/天",
                    "facilities": ["快速通行证", "童车租赁", "轮椅租赁", "寄存服务"]
                }
            },
            
            "豫园": {
                "overview": "明代私人花园，江南古典园林代表，周边是传统商业区",
                "best_time": {
                    "optimal": "工作日上午9:00-11:00",
                    "reason": "游客相对较少，可以静心欣赏园林之美",
                    "alternative": "傍晚17:00后，有不同的光影效果"
                },
                "photo_spots": [
                    {"name": "湖心亭", "tip": "经典的九曲桥拍摄点", "best_time": "上午光线柔和"},
                    {"name": "三穗堂", "tip": "古典建筑细节", "best_time": "任何时间"},
                    {"name": "玉玲珑", "tip": "太湖石经典", "best_time": "侧逆光拍摄"},
                    {"name": "城隍庙", "tip": "传统建筑群", "best_time": "避开正午强光"}
                ],
                "insider_tips": [
                    "豫园门票30元，城隍庙免费",
                    "南翔馒头店总店就在这里，但要排长队",
                    "老城隍庙小商品质量参差不齐，注意甄别",
                    "春节期间有特色灯会，但人流如潮"
                ],
                "hidden_gems": [
                    "城隍庙后面有个安静的小园林",
                    "豫园商城地下有个古玩市场",
                    "老街上有几家百年老店值得一看",
                    "豫园夜景灯光很美，晚上7点后开启"
                ],
                "nearby_food": [
                    {"name": "南翔馒头店", "type": "传统小笼包", "specialty": "小笼包", "price": "人均50", "note": "总店，需排队"},
                    {"name": "绿波廊", "type": "本帮菜", "specialty": "上海菜", "price": "人均200", "note": "老字号"},
                    {"name": "老城隍庙小吃", "type": "传统小吃", "specialty": "各种小食", "price": "人均30-80", "note": "种类丰富"}
                ],
                "practical_info": {
                    "opening_hours": "豫园8:30-17:00，城隍庙全天",
                    "ticket_price": "豫园30元，城隍庙免费",
                    "transportation": ["地铁10号线豫园站", "多路公交"],
                    "parking": "周边停车位紧张，建议公共交通",
                    "facilities": ["导游服务", "茶室", "古玩店"]
                }
            }
        }
        
        # 实用旅游贴士
        self.practical_tips = {
            "weather": {
                "rainy": ["携带雨具", "选择室内景点", "注意路面湿滑", "备用鞋袜"],
                "hot": ["防晒霜必备", "多补充水分", "避开11-15点户外活动", "轻薄透气衣物"],
                "cold": ["保暖衣物", "热饮保温", "室内外温差注意", "防滑鞋子"],
                "windy": ["固定好帽子围巾", "注意高处拍照安全", "头发护理用品"]
            },
            "crowd": {
                "high": ["错峰出行", "提前在线购票", "选择非热门景点", "耐心排队"],
                "medium": ["适当预留时间", "关注实时人流", "准备排队娱乐"],
                "low": ["抓紧拍照机会", "深度游览", "与景点工作人员互动"]
            },
            "transport": {
                "metro": ["下载地铁APP", "避开早晚高峰", "准备零钱或手机支付", "了解换乘路线"],
                "taxi": ["使用正规打车软件", "准备现金", "记住目的地具体地址", "避开高峰期"],
                "walking": ["舒适的鞋子", "查看天气预报", "了解路线距离", "注意安全"],
                "driving": ["提前查看停车信息", "避开限行时间", "了解路况", "准备停车费"]
            }
        }
        
        # 季节性建议
        self.seasonal_advice = {
            "spring": {
                "months": [3, 4, 5],
                "weather": "温和多雨",
                "clothing": "薄外套、雨具",
                "activities": ["赏花", "户外摄影", "公园游览"],
                "special": "樱花季（3-4月）"
            },
            "summer": {
                "months": [6, 7, 8],
                "weather": "炎热多雨",
                "clothing": "轻薄衣物、防晒用品",
                "activities": ["室内景点", "夜游", "滨江散步"],
                "special": "梅雨季注意（6-7月）"
            },
            "autumn": {
                "months": [9, 10, 11],
                "weather": "凉爽干燥",
                "clothing": "长袖、薄外套",
                "activities": ["户外游览", "登高望远", "城市漫步"],
                "special": "最佳旅游季节"
            },
            "winter": {
                "months": [12, 1, 2],
                "weather": "寒冷湿润",
                "clothing": "厚外套、保暖用品",
                "activities": ["室内景点", "温泉", "特色美食"],
                "special": "春节期间人流大增"
            }
        }
        
        logger.info("📚 RAG知识库初始化完成")
    
    def get_attraction_insights(self, attraction: str) -> Dict[str, Any]:
        """获取景点深度洞察"""
        return self.attractions_knowledge.get(attraction, {})
    
    def get_practical_tips_by_condition(self, condition_type: str, condition_value: str) -> List[str]:
        """根据条件获取实用贴士"""
        return self.practical_tips.get(condition_type, {}).get(condition_value, [])
    
    def get_seasonal_advice(self, month: int = None) -> Dict[str, Any]:
        """获取季节性建议"""
        if month is None:
            month = datetime.now().month
        
        for season, info in self.seasonal_advice.items():
            if month in info["months"]:
                return {**info, "season": season}
        
        return {}
    
    def search_knowledge(self, query: str, attraction: str = None) -> Dict[str, Any]:
        """搜索相关知识"""
        results = {
            "attraction_info": {},
            "tips": [],
            "seasonal": {},
            "relevance_score": 0
        }
        
        query_lower = query.lower()
        
        # 如果指定了景点，获取该景点信息
        if attraction and attraction in self.attractions_knowledge:
            results["attraction_info"] = self.attractions_knowledge[attraction]
            results["relevance_score"] += 50
        
        # 搜索相关贴士
        for tip_category, tips in self.practical_tips.items():
            for tip_type, tip_list in tips.items():
                if tip_type in query_lower or tip_category in query_lower:
                    results["tips"].extend(tip_list)
                    results["relevance_score"] += 10
        
        # 添加季节性建议
        results["seasonal"] = self.get_seasonal_advice()
        
        return results
    
    def generate_personalized_recommendations(self, user_preferences: Dict[str, Any], 
                                           weather_condition: str, crowd_level: str) -> List[str]:
        """生成个性化推荐"""
        recommendations = []
        
        # 基于天气的建议
        weather_tips = self.get_practical_tips_by_condition("weather", weather_condition.lower())
        recommendations.extend([f"🌤️ 天气建议：{tip}" for tip in weather_tips[:2]])
        
        # 基于人流的建议
        crowd_tips = self.get_practical_tips_by_condition("crowd", crowd_level.lower())
        recommendations.extend([f"👥 人流建议：{tip}" for tip in crowd_tips[:2]])
        
        # 基于用户偏好的建议
        if user_preferences.get("activity") == "摄影":
            recommendations.append("📸 摄影贴士：避开正午强光，选择侧逆光或柔和光线")
        
        if user_preferences.get("budget") == "经济":
            recommendations.append("💰 省钱贴士：选择工作日出行，关注团购优惠")
        
        return recommendations

# 全局实例
rag_kb = RAGKnowledgeBase()

def get_rag_knowledge() -> RAGKnowledgeBase:
    """获取RAG知识库实例"""
    return rag_kb

if __name__ == "__main__":
    # 测试RAG知识库
    kb = RAGKnowledgeBase()
    
    print("=== RAG知识库测试 ===")
    
    # 测试景点洞察
    waitan_info = kb.get_attraction_insights("外滩")
    print(f"外滩信息: {json.dumps(waitan_info, ensure_ascii=False, indent=2)}")
    
    # 测试实用贴士
    rainy_tips = kb.get_practical_tips_by_condition("weather", "rainy")
    print(f"雨天贴士: {rainy_tips}")
    
    # 测试季节建议
    seasonal = kb.get_seasonal_advice()
    print(f"当前季节建议: {seasonal}")
