"""
用户画像构建工具。
根据表单参数和默认权重生成用户偏好向量与画像摘要。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from .data import SHANGHAI_USER_ARCHETYPES


STYLE_WEIGHTS: Dict[str, Dict[str, float]] = {
    "relaxed": {"slow_walk": 0.7, "local_life": 0.6, "indoor": 0.4},
    "adventure": {"outdoor": 0.7, "large_scale": 0.5, "night_view": 0.4},
    "cultural": {"history": 0.8, "art": 0.6, "education": 0.5},
    "food": {"food": 0.9, "nightlife": 0.4, "local_life": 0.6},
    "photography": {"photography": 0.9, "landmark": 0.6, "night_view": 0.5},
}


INTEREST_WEIGHTS: Dict[str, Dict[str, float]] = {
    "历史文化": {"history": 0.9, "architecture": 0.6},
    "自然风光": {"nature": 0.8, "outdoor": 0.6},
    "美食": {"food": 0.9, "nightlife": 0.3},
    "购物": {"shopping": 0.8, "fashion": 0.6},
    "夜生活": {"nightlife": 0.9, "entertainment": 0.5},
    "博物馆": {"history": 0.5, "education": 0.8, "indoor": 0.7},
    "户外运动": {"outdoor": 0.8, "large_scale": 0.5},
    "温泉": {"relax": 0.8, "indoor": 0.5},
    "亲子互动": {"family": 0.9, "education": 0.6},
    "艺术设计": {"art": 0.9, "creative": 0.7},
    "潮流打卡": {"photo_spot": 0.8, "fashion": 0.7},
}


BUDGET_LEVELS = {
    "low": {"label": "经济型", "range": "≤¥1500/天"},
    "medium": {"label": "舒适型", "range": "¥1500-3000/天"},
    "medium_high": {"label": "品质型", "range": "¥3000-5000/天"},
    "high": {"label": "高端型", "range": "≥¥5000/天"},
}


@dataclass
class UserPersona:
    user_id: str
    tags: Dict[str, float]
    travel_style: Optional[str]
    budget_level: str
    interests: List[str]
    weather_adaptive: bool
    avoid_crowd: bool
    traffic_optimization: bool

    def to_dict(self) -> Dict[str, object]:
        ordered_tags = dict(sorted(self.tags.items(), key=lambda x: x[1], reverse=True))
        return {
            "user_id": self.user_id,
            "tags": ordered_tags,
            "top_tags": list(ordered_tags.keys())[:5],
            "travel_style": self.travel_style,
            "budget_level": {
                "key": self.budget_level,
                **BUDGET_LEVELS.get(self.budget_level, {}),
            },
            "interests": self.interests,
            "preferences": {
                "weather_adaptive": self.weather_adaptive,
                "avoid_crowd": self.avoid_crowd,
                "traffic_optimization": self.traffic_optimization,
            },
        }


def merge_weights(base: Dict[str, float], addition: Dict[str, float], weight: float = 1.0) -> Dict[str, float]:
    result = base.copy()
    for key, value in addition.items():
        result[key] = result.get(key, 0.0) + value * weight
    return result


def normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
    if not weights:
        return {}
    max_value = max(abs(v) for v in weights.values()) or 1.0
    return {k: round(v / max_value, 4) for k, v in weights.items()}


def build_user_persona(
    user_id: str,
    travel_style: Optional[str],
    interests: List[str],
    budget_level: str,
    archetype: Optional[str] = None,
    weather_adaptive: bool = True,
    avoid_crowd: bool = True,
    traffic_optimization: bool = True,
) -> UserPersona:
    weights: Dict[str, float] = {}

    if archetype and archetype in SHANGHAI_USER_ARCHETYPES:
        weights = merge_weights(weights, SHANGHAI_USER_ARCHETYPES[archetype], 1.0)

    if travel_style and travel_style in STYLE_WEIGHTS:
        weights = merge_weights(weights, STYLE_WEIGHTS[travel_style], 1.2)

    for interest in interests:
        if interest in INTEREST_WEIGHTS:
            weights = merge_weights(weights, INTEREST_WEIGHTS[interest], 1.0)

    if weather_adaptive:
        weights = merge_weights(weights, {"indoor": 0.3, "weather_safe": 0.3}, 1.0)
    if avoid_crowd:
        weights = merge_weights(weights, {"low_crowd": 0.4, "slow_walk": 0.2}, 1.0)
    if traffic_optimization:
        weights = merge_weights(weights, {"transport": 0.3, "central": 0.2}, 1.0)

    persona = UserPersona(
        user_id=user_id,
        tags=normalize_weights(weights),
        travel_style=travel_style,
        budget_level=budget_level if budget_level in BUDGET_LEVELS else "medium",
        interests=interests,
        weather_adaptive=weather_adaptive,
        avoid_crowd=avoid_crowd,
        traffic_optimization=traffic_optimization,
    )
    return persona

