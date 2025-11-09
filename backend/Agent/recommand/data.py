"""
上海旅游数据占位：景点、主题、体验标签等。
后续可替换为真实数据源或数据库检索。
"""

from typing import Dict, List, TypedDict


class POIRecord(TypedDict, total=False):
    id: str
    name: str
    district: str
    category: str
    tags: Dict[str, float]
    description: str
    best_for: List[str]
    price_level: str
    indoor: bool
    weather_dependency: str
    duration_hours: float
    crowd_level: str
    coordinates: Dict[str, float]


SHANGHAI_POIS: List[POIRecord] = [
    {
        "id": "sh_poi_01",
        "name": "外滩滨江步道",
        "district": "黄浦区",
        "category": "城市景观",
        "tags": {"landmark": 0.9, "night_view": 0.8, "photography": 0.7, "history": 0.6},
        "description": "上海地标滨江景观带，可一览万国建筑群与浦东天际线。",
        "best_for": ["情侣", "首次来沪", "夜景"],
        "price_level": "free",
        "indoor": False,
        "weather_dependency": "clear",
        "duration_hours": 2,
        "crowd_level": "high",
        "coordinates": {"lat": 31.240, "lng": 121.490},
    },
    {
        "id": "sh_poi_02",
        "name": "豫园与城隍庙",
        "district": "黄浦区",
        "category": "历史文化",
        "tags": {"history": 0.9, "architecture": 0.7, "food": 0.6, "shopping": 0.5},
        "description": "明清园林与老城厢市集的结合，可品尝小吃、购买伴手礼。",
        "best_for": ["文化体验", "美食"],
        "price_level": "medium",
        "indoor": True,
        "weather_dependency": "all",
        "duration_hours": 2.5,
        "crowd_level": "high",
        "coordinates": {"lat": 31.227, "lng": 121.492},
    },
    {
        "id": "sh_poi_03",
        "name": "上海博物馆",
        "district": "黄浦区",
        "category": "博物馆",
        "tags": {"history": 0.8, "art": 0.7, "indoor": 1.0, "education": 0.6},
        "description": "中国古代青铜器、书画与玉器的精品收藏，需提前预约。",
        "best_for": ["文化体验", "雨天备用"],
        "price_level": "free",
        "indoor": True,
        "weather_dependency": "all",
        "duration_hours": 2,
        "crowd_level": "medium",
        "coordinates": {"lat": 31.230, "lng": 121.470},
    },
    {
        "id": "sh_poi_04",
        "name": "上海中心大厦·观景台",
        "district": "浦东新区",
        "category": "城市地标",
        "tags": {"landmark": 0.8, "skyline": 0.9, "photography": 0.8, "innovation": 0.6},
        "description": "登顶中国第二高楼，俯瞰浦江全景，夜景尤佳。",
        "best_for": ["高空体验", "夜景"],
        "price_level": "high",
        "indoor": True,
        "weather_dependency": "clear",
        "duration_hours": 1.5,
        "crowd_level": "medium",
        "coordinates": {"lat": 31.235, "lng": 121.505},
    },
    {
        "id": "sh_poi_05",
        "name": "田子坊创意街区",
        "district": "黄浦区",
        "category": "文创街区",
        "tags": {"art": 0.8, "local_life": 0.7, "photo_spot": 0.6, "food": 0.5},
        "description": "石库门里弄改造的创意街区，小众设计与咖啡馆云集。",
        "best_for": ["小众探索", "拍照"],
        "price_level": "medium",
        "indoor": False,
        "weather_dependency": "cloudy",
        "duration_hours": 2,
        "crowd_level": "medium",
        "coordinates": {"lat": 31.215, "lng": 121.475},
    },
    {
        "id": "sh_poi_06",
        "name": "上海迪士尼度假区",
        "district": "浦东新区",
        "category": "主题乐园",
        "tags": {"family": 0.9, "entertainment": 0.8, "large_scale": 0.7, "outdoor": 0.6},
        "description": "适合家庭与好友的主题乐园，需预留全天行程与预约快速通行。",
        "best_for": ["亲子", "好友出行"],
        "price_level": "high",
        "indoor": False,
        "weather_dependency": "clear",
        "duration_hours": 8,
        "crowd_level": "high",
        "coordinates": {"lat": 31.145, "lng": 121.658},
    },
    {
        "id": "sh_poi_07",
        "name": "武康路历史风貌街区",
        "district": "徐汇区",
        "category": "城市漫步",
        "tags": {"heritage": 0.8, "photography": 0.7, "cafe": 0.6, "slow_walk": 0.7},
        "description": "法租界梧桐街区，适合慢步与拍照，可安排咖啡时间。",
        "best_for": ["慢节奏", "拍照"],
        "price_level": "medium",
        "indoor": False,
        "weather_dependency": "mild",
        "duration_hours": 2.5,
        "crowd_level": "medium",
        "coordinates": {"lat": 31.203, "lng": 121.439},
    },
    {
        "id": "sh_poi_08",
        "name": "上海天文馆",
        "district": "浦东新区",
        "category": "科技探索",
        "tags": {"science": 0.9, "family": 0.7, "education": 0.8, "indoor": 1.0},
        "description": "沉浸式天文科普场馆，适合亲子与科幻爱好者。",
        "best_for": ["亲子", "科技探索"],
        "price_level": "medium",
        "indoor": True,
        "weather_dependency": "all",
        "duration_hours": 3,
        "crowd_level": "medium",
        "coordinates": {"lat": 31.107, "lng": 121.705},
    },
    {
        "id": "sh_poi_09",
        "name": "上生·新所",
        "district": "长宁区",
        "category": "生活方式",
        "tags": {"art": 0.6, "fashion": 0.7, "local_life": 0.5, "indoor": 0.6},
        "description": "历史泳池改造的生活方式空间，集合美食、展览、市集。",
        "best_for": ["潮流体验", "美食"],
        "price_level": "medium_high",
        "indoor": True,
        "weather_dependency": "all",
        "duration_hours": 2,
        "crowd_level": "medium",
        "coordinates": {"lat": 31.215, "lng": 121.414},
    },
    {
        "id": "sh_poi_10",
        "name": "崇明东滩湿地公园",
        "district": "崇明区",
        "category": "自然生态",
        "tags": {"nature": 0.9, "birdwatching": 0.8, "outdoor": 0.7, "slow_walk": 0.5},
        "description": "长江入海口湿地生态保护区，可观鸟、骑行与自然摄影。",
        "best_for": ["自然探索", "缓慢节奏"],
        "price_level": "medium",
        "indoor": False,
        "weather_dependency": "clear",
        "duration_hours": 4,
        "crowd_level": "low",
        "coordinates": {"lat": 31.503, "lng": 121.957},
    },
]


SHANGHAI_USER_ARCHETYPES: Dict[str, Dict[str, float]] = {
    "city_explorer": {"landmark": 0.8, "history": 0.6, "photography": 0.7, "night_view": 0.6},
    "culture_lover": {"history": 0.9, "art": 0.8, "architecture": 0.6, "education": 0.5},
    "foodie": {"food": 0.9, "local_life": 0.6, "nightlife": 0.5, "shopping": 0.4},
    "family_fun": {"family": 0.9, "entertainment": 0.7, "science": 0.6, "indoor": 0.6},
    "nature_escape": {"nature": 0.8, "slow_walk": 0.6, "birdwatching": 0.5, "outdoor": 0.6},
}


DEFAULT_CITY_SUMMARY = {
    "city": "上海",
    "districts": [
        {"name": "黄浦区", "themes": ["历史人文", "夜景地标"]},
        {"name": "浦东新区", "themes": ["现代地标", "家庭娱乐"]},
        {"name": "徐汇区", "themes": ["海派风情", "慢生活"]},
        {"name": "长宁区", "themes": ["生活方式", "文创空间"]},
        {"name": "崇明区", "themes": ["自然生态", "户外探索"]},
    ],
    "themes": [
        {"id": "night_view", "label": "浦江夜景"},
        {"id": "culture", "label": "海派文化"},
        {"id": "family", "label": "亲子乐园"},
        {"id": "food", "label": "风味美食"},
        {"id": "nature", "label": "自然生态"},
    ],
    "seasonal_notes": {
        "spring": "樱花与城市漫步适宜，气温舒适。",
        "summer": "注意高温与雷阵雨，多安排室内或夜间活动。",
        "autumn": "最佳旅行季节，适合户外与文化活动结合。",
        "winter": "偏冷但人流减少，可安排博物馆与美食路线。",
    },
}

