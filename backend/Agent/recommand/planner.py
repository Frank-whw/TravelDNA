"""
推荐规划器：组装用户画像、协同过滤打分与行程生成。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import re
from typing import Any, Dict, List, Optional, Tuple

from .collaborative import cosine_similarity, normalize_scores, score_candidate
from .data import DEFAULT_CITY_SUMMARY, SHANGHAI_POIS
from .profiles import BUDGET_LEVELS, UserPersona, build_user_persona
from .services import realtime_service


WEATHER_SAFE_CONDITIONS = {"all", "cloudy"}
OUTDOOR_PREFERRED = {"clear", "mild"}

TAG_KEYWORD_MAP: Dict[str, List[Dict[str, Optional[str]]]] = {
    "history": [{"keyword": "博物馆", "category": "140100"}, {"keyword": "历史建筑"}],
    "art": [{"keyword": "艺术馆", "category": "140200"}, {"keyword": "美术馆"}],
    "food": [{"keyword": "特色美食", "category": "050000"}, {"keyword": "小吃"}],
    "shopping": [{"keyword": "购物中心", "category": "060000"}],
    "nightlife": [{"keyword": "酒吧", "category": "080300"}, {"keyword": "夜生活"}],
    "family": [{"keyword": "亲子乐园", "category": "110100"}, {"keyword": "儿童乐园"}],
    "nature": [{"keyword": "公园", "category": "110101"}, {"keyword": "湿地公园"}],
    "photo_spot": [{"keyword": "网红打卡"}],
    "slow_walk": [{"keyword": "特色街区", "category": "060400"}],
    "entertainment": [{"keyword": "主题乐园", "category": "080501"}],
    "science": [{"keyword": "科技馆", "category": "140600"}],
}

TRAVEL_STYLE_KEYWORDS: Dict[str, List[Dict[str, Optional[str]]]] = {
    "relaxed": [{"keyword": "城市漫步"}, {"keyword": "咖啡馆"}],
    "adventure": [{"keyword": "探险乐园"}, {"keyword": "户外拓展"}],
    "cultural": [{"keyword": "文化体验"}, {"keyword": "非遗"}],
    "food": [{"keyword": "美食街"}, {"keyword": "本帮菜"}],
    "photography": [{"keyword": "摄影景点"}, {"keyword": "天际线"}],
}

TYPE_TAG_HINTS: Dict[str, str] = {
    "博物馆": "history",
    "美术馆": "art",
    "画廊": "art",
    "餐饮": "food",
    "小吃": "food",
    "餐厅": "food",
    "购物": "shopping",
    "商场": "shopping",
    "夜生活": "nightlife",
    "酒吧": "nightlife",
    "亲子": "family",
    "乐园": "family",
    "公园": "nature",
    "湿地": "nature",
    "景区": "nature",
    "步行街": "slow_walk",
    "历史建筑": "history",
    "教堂": "history",
    "美食": "food",
    "咖啡": "photo_spot",
    "摄影": "photo_spot",
    "艺术": "art",
}


@dataclass
class RecommendationRequest:
    user_id: str = "web_user"
    city: str = "上海"
    travel_days: int = 3
    budget: Optional[int] = None
    budget_level: str = "medium"
    travel_style: Optional[str] = None
    interests: Optional[List[str]] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    weather_adaptive: bool = True
    avoid_crowd: bool = True
    traffic_optimization: bool = True

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "RecommendationRequest":
        travel_days = max(1, min(int(payload.get("travel_days") or 3), 7))
        budget_level = payload.get("budget_level") or _infer_budget_level(payload.get("budget"))
        return cls(
            user_id=payload.get("user_id") or "web_user",
            city=payload.get("city") or "上海",
            travel_days=travel_days,
            budget=payload.get("budget"),
            budget_level=budget_level,
            travel_style=payload.get("travel_style"),
            interests=payload.get("interests") or [],
            start_date=payload.get("start_date"),
            end_date=payload.get("end_date"),
            weather_adaptive=bool(payload.get("weather_adaptive", True)),
            avoid_crowd=bool(payload.get("avoid_crowd", True)),
            traffic_optimization=bool(payload.get("traffic_optimization", True)),
        )


def _infer_budget_level(budget: Optional[int]) -> str:
    if budget is None:
        return "medium"
    if budget <= 1500:
        return "low"
    if budget <= 3000:
        return "medium"
    if budget <= 5000:
        return "medium_high"
    return "high"


class RecommendationPlanner:
    def __init__(self) -> None:
        self.dataset = SHANGHAI_POIS

    def _collect_realtime_context(
        self,
        request: RecommendationRequest,
        persona: UserPersona,
    ) -> Dict[str, Any]:
        context: Dict[str, Any] = {
            "weather_raw": None,
            "weather_records": [],
            "weather_analysis": None,
            "poi_records": [],
            "queries": [],
        }

        weather_response = realtime_service.fetch_weather(request.city)
        context["weather_raw"] = weather_response
        weather_records = self._convert_weather_response(weather_response)
        context["weather_records"] = weather_records
        context["weather_analysis"] = self._analyze_weather_condition(weather_records)

        queries = self._derive_poi_queries(persona, request)
        context["queries"] = queries

        poi_records: Dict[str, Dict[str, Any]] = {}
        for query in queries:
            poi_list = realtime_service.fetch_poi(
                request.city,
                keyword=query["keyword"],
                category=query.get("category"),
                limit=query.get("limit", 10),
            )
            for poi in poi_list:
                record = self._build_poi_record(poi, query["source_tag"])
                if record and record["id"] not in poi_records:
                    poi_records[record["id"]] = record

        context["poi_records"] = list(poi_records.values())
        return context

    def _derive_poi_queries(
        self,
        persona: UserPersona,
        request: RecommendationRequest,
    ) -> List[Dict[str, Any]]:
        queries: List[Dict[str, Any]] = []

        sorted_tags = sorted(
            persona.tags.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        for tag, weight in sorted_tags[:6]:
            for query in TAG_KEYWORD_MAP.get(tag, []):
                queries.append(
                    {
                        "keyword": query["keyword"],
                        "category": query.get("category"),
                        "limit": 8,
                        "source_tag": tag,
                    }
                )

        if request.travel_style in TRAVEL_STYLE_KEYWORDS:
            for query in TRAVEL_STYLE_KEYWORDS[request.travel_style]:
                queries.append(
                    {
                        "keyword": query["keyword"],
                        "category": query.get("category"),
                        "limit": 6,
                        "source_tag": request.travel_style or "",
                    }
                )

        if not queries:
            queries = [
                {"keyword": "上海必玩景点", "limit": 10, "source_tag": "landmark"},
                {"keyword": "上海热门美食", "category": "050000", "limit": 6, "source_tag": "food"},
                {"keyword": "上海特色街区", "limit": 6, "source_tag": "local_life"},
            ]

        # 去重
        unique = {}
        for item in queries:
            key = (item["keyword"], item.get("category"))
            if key not in unique:
                unique[key] = item
        return list(unique.values())

    def _build_poi_record(self, poi: Dict[str, Any], source_tag: str) -> Optional[Dict[str, Any]]:
        name = poi.get("name")
        poi_id = poi.get("id") or name
        if not name:
            return None

        district = poi.get("adname") or poi.get("cityname") or "上海"
        typecode = poi.get("typecode") or ""
        poi_type = poi.get("type") or ""
        biz_ext = poi.get("biz_ext", {})

        tags: Dict[str, float] = {source_tag: 0.9} if source_tag else {}

        for keyword, tag in TYPE_TAG_HINTS.items():
            if keyword in poi_type or keyword in name:
                tags[tag] = max(tags.get(tag, 0.0), 0.7)

        if not tags:
            tags["general"] = 0.5

        price = (
            str(biz_ext.get("cost"))
            if isinstance(biz_ext.get("cost"), (int, float))
            else (biz_ext.get("cost") or "")
        )
        rating_text = biz_ext.get("rating") or ""
        rating = 0.0
        try:
            rating = float(rating_text) if rating_text else 0.0
        except ValueError:
            rating = 0.0

        record = {
            "id": poi_id,
            "name": name,
            "district": district,
            "category": poi_type.split(";")[0] if poi_type else "景点",
            "tags": tags,
            "description": poi.get("address") or poi.get("children") or "",
            "best_for": [],
            "price_level": self._infer_price_level_from_text(price),
            "indoor": self._is_indoor_from_type(poi_type),
            "weather_dependency": self._infer_weather_dependency(poi_type),
            "duration_hours": 2.0,
            "crowd_level": "medium",
            "coordinates": self._parse_location(poi.get("location")),
            "rating": rating,
            "raw": poi,
        }
        return record

    def _convert_weather_response(self, weather_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not weather_response:
            return []

        records: List[Dict[str, Any]] = []
        forecasts = weather_response.get("forecasts", [])
        if forecasts:
            for cast in forecasts[0].get("casts", []):
                records.append(
                    {
                        "date": cast.get("date"),
                        "weather": cast.get("dayweather"),
                        "temperature": f"{cast.get('nighttemp')}~{cast.get('daytemp')}℃",
                        "wind": cast.get("daywind"),
                        "humidity": cast.get("dayweather"),
                        "precipitation": cast.get("daypower"),
                    }
                )
        elif weather_response.get("lives"):
            live = weather_response["lives"][0]
            records.append(
                {
                    "date": live.get("reporttime"),
                    "weather": live.get("weather"),
                    "temperature": f"{live.get('temperature')}℃",
                    "wind": live.get("winddirection"),
                    "humidity": live.get("humidity"),
                    "precipitation": "",
                }
            )
        return records

    def _infer_price_level_from_text(self, price_text: str) -> Optional[str]:
        if not price_text:
            return None
        digits = re.findall(r"\d+", price_text)
        if not digits:
            return None
        try:
            amount = int(digits[0])
        except ValueError:
            return None
        if amount <= 80:
            return "low"
        if amount <= 180:
            return "medium"
        if amount <= 300:
            return "medium_high"
        return "high"

    def _is_indoor_from_type(self, poi_type: str) -> bool:
        if not poi_type:
            return False
        indoor_keywords = [
            "博物馆",
            "美术馆",
            "展览",
            "剧院",
            "餐饮",
            "餐厅",
            "咖啡",
            "购物",
            "商场",
            "水族馆",
            "科技馆",
            "天文馆",
        ]
        return any(keyword in poi_type for keyword in indoor_keywords)

    def _infer_weather_dependency(self, poi_type: str) -> str:
        if self._is_indoor_from_type(poi_type):
            return "all"
        if not poi_type:
            return "mild"
        outdoor_keywords = ["公园", "湿地", "古镇", "广场", "户外", "滨江", "步道", "观景", "乐园", "花园"]
        if any(keyword in poi_type for keyword in outdoor_keywords):
            return "clear"
        return "mild"

    def _parse_location(self, location: Optional[str]) -> Optional[Dict[str, float]]:
        if not location or "," not in location:
            return None
        try:
            lng_str, lat_str = location.split(",", 1)
            return {"lng": float(lng_str), "lat": float(lat_str)}
        except ValueError:
            return None

    def _analyze_weather_condition(self, weather_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not weather_records:
            return {
                "summary": "暂无天气数据",
                "condition": "unknown",
                "temperature": "未知",
                "average_temperature": None,
                "suitable_for_outdoor": False,
                "advice": "暂无可靠天气信息，请提醒用户出行前再次确认天气预报。",
                "score": 50,
            }

        record = weather_records[0] if isinstance(weather_records, list) else weather_records
        if isinstance(record, dict):
            weather_text = record.get("weather") or ""
            temperature_text = record.get("temperature") or ""
        else:
            weather_text = getattr(record, "weather", "") or ""
            temperature_text = getattr(record, "temperature", "") or ""

        condition = "moderate"
        score = 70
        suitable_for_outdoor = True
        advice = "天气整体适宜，可以灵活安排室内外活动。"

        if any(keyword in weather_text for keyword in ["雷", "暴雨", "台风", "大风", "冰雹"]):
            condition = "extreme"
            score = 20
            suitable_for_outdoor = False
            advice = "天气较为极端，请优先选择室内活动，并留意官方安全预警。"
        elif "雨" in weather_text:
            condition = "rainy"
            score = 45
            suitable_for_outdoor = False
            advice = "有降雨，建议准备雨具，把重点放在室内或半室内项目上。"
        elif "雪" in weather_text:
            condition = "snow"
            score = 40
            suitable_for_outdoor = False
            advice = "可能有降雪或湿冷，注意防滑保暖，多安排室内体验。"
        elif any(keyword in weather_text for keyword in ["阴", "多云"]):
            condition = "cloudy"
            score = 65
            advice = "多云天气，光线柔和，适合轻松散步或艺术展览等活动。"
        elif any(keyword in weather_text for keyword in ["晴", "阳"]):
            condition = "sunny"
            score = 85
            advice = "晴朗天气，适合户外活动，也别忘了补水和防晒。"

        temp_value = self._parse_temperature_value(temperature_text)
        if temp_value is not None:
            if temp_value >= 33:
                score -= 10
                advice += " 气温偏高，户外时段请安排在早晚并注意补水。"
            elif temp_value <= 5:
                score -= 10
                suitable_for_outdoor = False
                advice += " 气温较低，需要防寒保暖，可多考虑室内选项。"

        return {
            "summary": weather_text or "暂无天气描述",
            "condition": condition,
            "temperature": temperature_text or "未知",
            "average_temperature": temp_value,
            "suitable_for_outdoor": suitable_for_outdoor,
            "advice": advice,
            "score": max(min(score, 100), 0),
        }

    def _parse_temperature_value(self, temperature_text: str) -> Optional[float]:
        if not temperature_text:
            return None
        matches = re.findall(r"-?\d+", temperature_text)
        if not matches:
            return None
        values = [int(match) for match in matches]
        if not values:
            return None
        return sum(values) / len(values)

    def get_dataset_summary(self) -> Dict[str, Any]:
        return {
            "city": DEFAULT_CITY_SUMMARY["city"],
            "dataset_size": len(self.dataset),
            "sample_pois": [
                {
                    "id": poi["id"],
                    "name": poi["name"],
                    "district": poi["district"],
                    "category": poi["category"],
                    "best_for": poi.get("best_for", []),
                    "price_level": poi.get("price_level"),
                }
                for poi in self.dataset[:6]
            ],
            "themes": DEFAULT_CITY_SUMMARY["themes"],
            "seasonal_notes": DEFAULT_CITY_SUMMARY["seasonal_notes"],
        }

    def generate_plan(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        request = RecommendationRequest.from_payload(payload)
        persona = build_user_persona(
            user_id=request.user_id,
            travel_style=request.travel_style,
            interests=request.interests,
            budget_level=request.budget_level,
            archetype=_guess_archetype(request),
            weather_adaptive=request.weather_adaptive,
            avoid_crowd=request.avoid_crowd,
            traffic_optimization=request.traffic_optimization,
        )

        realtime_context = self._collect_realtime_context(request, persona)

        poi_source = (
            realtime_context.get("poi_records") or SHANGHAI_POIS
        )

        scored_candidates = self._score_candidates(
            persona,
            request,
            poi_source,
            realtime_context.get("weather_analysis") or {},
        )
        itinerary = self._build_itinerary(request, scored_candidates)
        backups = self._pick_backup_options(scored_candidates, itinerary)

        return {
            "user_profile": persona.to_dict(),
            "plan_summary": self._build_plan_summary(request, itinerary),
            "itinerary": itinerary,
            "backup_options": backups,
            "analytics": self._build_analysis(
                request,
                itinerary,
                realtime_context.get("weather_analysis"),
            ),
            "raw_scores": scored_candidates,
            "dataset_version": "mock-shanghai-v1",
            "realtime_context": {
                "weather": realtime_context.get("weather_analysis"),
                "queries": realtime_context.get("queries"),
                "poi_count": len(realtime_context.get("poi_records") or []),
            },
        }

    def _score_candidates(
        self,
        persona: UserPersona,
        request: RecommendationRequest,
        poi_records: List[Dict[str, Any]],
        weather_analysis: Dict[str, Any],
    ) -> Dict[str, Dict[str, Any]]:
        scores: List[Tuple[str, float]] = []
        details: Dict[str, Dict[str, Any]] = {}

        condition = weather_analysis.get("condition") if weather_analysis else None
        suitable_for_outdoor = weather_analysis.get("suitable_for_outdoor", True) if weather_analysis else True

        for poi in poi_records:
            crowd_penalty = 0.0
            if request.avoid_crowd and poi.get("crowd_level") == "high":
                crowd_penalty = 18.0

            weather_penalty = 0.0
            dependency = poi.get("weather_dependency", "all")

            if request.weather_adaptive:
                if not suitable_for_outdoor and not poi.get("indoor", False):
                    weather_penalty += 20.0
                if dependency not in WEATHER_SAFE_CONDITIONS:
                    if dependency == "clear":
                        weather_penalty += 10.0
                    elif dependency == "mild":
                        weather_penalty += 6.0

                if condition and not poi.get("indoor", False):
                    if condition in {"rainy", "snow", "extreme"}:
                        weather_penalty += 12.0
                    elif condition == "cloudy":
                        weather_penalty += 4.0

            budget_penalty = 0.0
            poi_price = poi.get("price_level", "medium")
            budget_penalty = _budget_penalty(request.budget_level, poi_price)

            base_similarity = cosine_similarity(persona.tags, poi.get("tags", {}))
            base_score = round(base_similarity * 100, 2)
            final_score = round(
                score_candidate(
                    persona.tags,
                    poi.get("tags", {}),
                    crowd_penalty=crowd_penalty,
                    weather_penalty=weather_penalty,
                    budget_penalty=budget_penalty,
                ),
                2,
            )

            score = final_score
            scores.append((poi["id"], score))
            total_penalty = round(
                max(base_score - final_score, 0.0), 2
            )

            details[poi["id"]] = {
                "poi": poi,
                "crowd_penalty": round(crowd_penalty, 2),
                "weather_penalty": round(weather_penalty, 2),
                "budget_penalty": round(budget_penalty, 2),
                "base_score": base_score,
                "raw_score": final_score,
                "penalty_breakdown": {
                    "total": total_penalty,
                    "crowd": round(crowd_penalty, 2),
                    "weather": round(weather_penalty, 2),
                    "budget": round(budget_penalty, 2),
                },
            }

        normalized = normalize_scores(scores)
        for poi_id, score in normalized.items():
            details[poi_id]["score"] = score

        return details

    def _build_itinerary(
        self, request: RecommendationRequest, scored_candidates: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        sorted_pois = sorted(
            scored_candidates.values(),
            key=lambda item: item["score"],
            reverse=True,
        )

        days = request.travel_days
        plan: List[Dict[str, Any]] = []
        used_ids: set[str] = set()
        start_date = _parse_date(request.start_date)

        for day_index in range(days):
            day_plan = {
                "day": day_index + 1,
                "date": _format_date(start_date, day_index),
                "focus": None,
                "weather_note": None,
                "spots": [],
            }

            for candidate in sorted_pois:
                poi = candidate["poi"]
                if poi["id"] in used_ids:
                    continue
                if not day_plan["focus"]:
                    day_plan["focus"] = _infer_day_focus(poi)
                day_plan["spots"].append(
                    {
                        "id": poi["id"],
                        "name": poi["name"],
                        "district": poi["district"],
                        "category": poi.get("category", ""),
                        "score": candidate["score"],
                        "schedule": _recommend_schedule(len(day_plan["spots"])),
                        "reasons": _build_reasoning(poi, candidate),
                        "price_level": poi.get("price_level"),
                        "crowd_level": poi.get("crowd_level"),
                        "duration_hours": poi.get("duration_hours", 2.0),
                        "indoor": poi.get("indoor", False),
                    }
                )
                used_ids.add(poi["id"])

                if len(day_plan["spots"]) >= 3:
                    break

            if day_plan["spots"]:
                day_plan["weather_note"] = _generate_weather_note(day_plan)
                plan.append(day_plan)

        return plan

    def _pick_backup_options(
        self, scored_candidates: Dict[str, Dict[str, Any]], itinerary: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        used_ids = {spot["id"] for day in itinerary for spot in day.get("spots", [])}
        remaining = [
            detail for poi_id, detail in scored_candidates.items() if poi_id not in used_ids
        ]
        remaining.sort(key=lambda item: item["score"], reverse=True)
        backups = []
        for item in remaining[:4]:
            poi = item["poi"]
            backups.append(
                {
                    "id": poi["id"],
                    "name": poi["name"],
                    "district": poi["district"],
                    "category": poi.get("category", ""),
                    "score": item["score"],
                    "reason": _build_reasoning(poi, item)[:2],
                }
            )
        return backups

    def _build_plan_summary(
        self, request: RecommendationRequest, itinerary: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        return {
            "city": request.city,
            "travel_days": len(itinerary),
            "budget_level": {
                "key": request.budget_level,
                **BUDGET_LEVELS.get(request.budget_level, {}),
            },
            "highlights": [
                day["focus"] for day in itinerary if day.get("focus")
            ][:3],
        }

    def _build_analysis(
        self,
        request: RecommendationRequest,
        itinerary: List[Dict[str, Any]],
        weather_analysis: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        weather_focus = []
        indoor_ratio = 0
        total_spots = 0

        for day in itinerary:
            if day.get("weather_note"):
                weather_focus.append(day["weather_note"])
            for spot in day.get("spots", []):
                total_spots += 1
                if spot.get("indoor"):
                    indoor_ratio += 1

        indoor_ratio = round(indoor_ratio / total_spots, 2) if total_spots else 0

        weather_summary = []
        if weather_analysis:
            summary = weather_analysis.get("summary")
            advice = weather_analysis.get("advice")
            if summary:
                weather_summary.append(summary)
            if advice:
                weather_summary.append(advice)

        return {
            "weather_advice": weather_focus[:3] or weather_summary,
            "indoor_ratio": indoor_ratio,
            "crowd_strategy": "已自动优先选择人流适中或低的景点" if request.avoid_crowd else "未特别规避人流峰值",
            "traffic_tip": "建议优先选择地铁与步行衔接，避开核心商圈晚高峰" if request.traffic_optimization else "可根据偏好自定义交通方式",
        }


def _describe_penalties(breakdown: Dict[str, float]) -> Optional[str]:
    segments = []
    if breakdown.get("weather", 0) > 0:
        segments.append(f"天气扣 {breakdown['weather']} 分")
    if breakdown.get("crowd", 0) > 0:
        segments.append(f"人流扣 {breakdown['crowd']} 分")
    if breakdown.get("budget", 0) > 0:
        segments.append(f"预算扣 {breakdown['budget']} 分")
    if not segments and breakdown.get("total", 0) == 0:
        return None
    if not segments and breakdown.get("total", 0) > 0:
        segments.append(f"其他因素扣 {breakdown['total']} 分")
    return "，".join(segments)


def _build_reasoning(poi: Dict[str, Any], candidate: Dict[str, Any]) -> List[str]:
    reasons: List[str] = []
    breakdown = candidate.get("penalty_breakdown")
    base_score = candidate.get("base_score")
    raw_score = candidate.get("raw_score")
    normalized_score = candidate.get("score")

    if base_score is not None:
        reasons.append(f"基础偏好匹配 {base_score} 分")
    penalty_text = _describe_penalties(breakdown or {})
    if penalty_text:
        total_penalty = breakdown.get("total", 0) if breakdown else 0
        reasons.append(f"{penalty_text}，合计扣 {total_penalty} 分")
    if raw_score is not None:
        if normalized_score is not None:
            reasons.append(f"综合得分 {raw_score} 分（归一化 {normalized_score}）")
        else:
            reasons.append(f"综合得分 {raw_score} 分")

    if poi.get("description"):
        reasons.append(poi["description"])

    if candidate.get("crowd_penalty", 0) > 0:
        reasons.append("建议提前预约或错峰前往，当前人流较高")

    return reasons


def _recommend_schedule(position: int) -> str:
    slots = ["09:00-11:30", "13:00-15:30", "16:00-19:00", "19:30-21:30"]
    return slots[position % len(slots)]


def _infer_day_focus(poi: Dict[str, Any]) -> str:
    category = poi.get("category")
    if category:
        return f"主题：{category}"
    tags = poi.get("tags", {})
    if tags:
        top_tag = max(tags, key=tags.get)
        return f"主题：{top_tag}"
    return "主题：城市探索"


def _generate_weather_note(day_plan: Dict[str, Any]) -> str:
    indoor_count = sum(1 for spot in day_plan.get("spots", []) if spot.get("indoor"))
    if indoor_count >= 2:
        return "安排了较多室内体验，可应对天气变化。"
    outdoor_count = len(day_plan.get("spots", [])) - indoor_count
    if outdoor_count >= 2:
        return "当日以户外活动为主，建议关注天气并准备防晒/雨具。"
    return "行程室内外均衡，可灵活调整。"


def _parse_date(date_str: Optional[str]) -> Optional[datetime]:
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str)
    except ValueError:
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return None


def _format_date(base: Optional[datetime], offset_days: int) -> Optional[str]:
    if base is None:
        return None
    return (base + timedelta(days=offset_days)).strftime("%Y-%m-%d")


def _budget_penalty(user_level: str, poi_level: Optional[str]) -> float:
    if not poi_level:
        return 0.0
    order = ["low", "medium", "medium_high", "high"]
    user_index = order.index(user_level) if user_level in order else 1
    poi_index = order.index(poi_level) if poi_level in order else 1
    difference = poi_index - user_index
    if difference <= 0:
        return 0.0
    return min(difference * 12.0, 24.0)


def _guess_archetype(request: RecommendationRequest) -> Optional[str]:
    interests = set(request.interests or [])
    if "自然风光" in interests:
        return "nature_escape"
    if "亲子互动" in interests:
        return "family_fun"
    if "美食" in interests:
        return "foodie"
    if "历史文化" in interests or request.travel_style == "cultural":
        return "culture_lover"
    return "city_explorer"

