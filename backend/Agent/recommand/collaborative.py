"""
简化的协同过滤实现。
基于用户画像标签与POI标签的余弦相似度进行打分。
"""

from __future__ import annotations

import math
from typing import Dict, Iterable, Tuple


def cosine_similarity(vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
    if not vec_a or not vec_b:
        return 0.0

    numerator = 0.0
    sum_a = 0.0
    sum_b = 0.0

    for key, value in vec_a.items():
        if key in vec_b:
            numerator += value * vec_b[key]
        sum_a += value * value

    for value in vec_b.values():
        sum_b += value * value

    denominator = math.sqrt(sum_a) * math.sqrt(sum_b)
    if denominator == 0.0:
        return 0.0
    return numerator / denominator


def score_candidate(
    persona_tags: Dict[str, float],
    poi_tags: Dict[str, float],
    crowd_penalty: float = 0.0,
    weather_penalty: float = 0.0,
    budget_penalty: float = 0.0,
) -> float:
    base_score = cosine_similarity(persona_tags, poi_tags) * 100
    penalties = crowd_penalty + weather_penalty + budget_penalty
    return max(base_score - penalties, 0.0)


def normalize_scores(scores: Iterable[Tuple[str, float]]) -> Dict[str, float]:
    score_dict = dict(scores)
    if not score_dict:
        return {}
    max_score = max(score_dict.values()) or 1.0
    min_score = min(score_dict.values())
    # 使用线性归一化，保留原始排序
    normalized = {}
    for key, value in score_dict.items():
        if max_score == min_score:
            normalized[key] = 60.0
        else:
            normalized[key] = round(60 + 40 * (value - min_score) / (max_score - min_score), 2)
    return normalized

