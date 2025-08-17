from typing import Any

from ..services.qwen_service import QwenService
from ..services.poi_embedding_service import POIEmbeddingService
from ..services.route_validator_service import RouteValidatorService
from ..services.amap_service import AmapService
from ..services.weather_service import WeatherService
from ..config import get_settings
from ..logging_config import get_logger
from ..schemas import TripPlan, DailyForecast, WeatherForecast
from .state import PlanState


logger = get_logger(__name__)
_settings = get_settings()
qwen = QwenService()
poi = POIEmbeddingService()
amap = AmapService(api_key=_settings.AMAP_API_KEY)
weather = WeatherService(api_key=_settings.QWEATHER_API_KEY)
validator = RouteValidatorService(amap)


def planner_node(state: PlanState) -> dict[str, Any]:
    # 复用现有主流程：先直接产出一个初版 plan
    plan: TripPlan = qwen.generate_trip_plan(state.request)
    return {"plan": plan}


def retriever_node(state: PlanState) -> dict[str, Any]:
    # 最小版：planner 里已注入 RAG。此处预留位后续扩展（补证据/sources）
    return {}


def scheduler_node(state: PlanState) -> dict[str, Any]:
    # 最小版：先不做调序（保持 LLM 顺序）。后续引入贪心/OR-Tools
    return {}


def weather_node(state: PlanState) -> dict[str, Any]:
    """根据目的地/起始日期获取3日天气，写入 state.weather。

    - 优先使用目的地名称（或经纬度，未来 state 可扩展坐标）
    - 上游失败时，返回降级本地样例
    """
    try:
        destination = state.request.destination or "Beijing"
        # 直接使用已有服务封装的 forecast 接口（映射到 WeatherForecast）
        from ..api import get_weather_forecast  # 复用现有端点逻辑（内部已做降级）
        weather: WeatherForecast = get_weather_forecast.__wrapped__(  # type: ignore
            location=destination, days=3, host=""
        )
        return {"weather": weather}
    except Exception as _:
        # 构造本地降级，避免阻断流程
        from datetime import datetime, timedelta, timezone
        today = datetime.now(timezone.utc).date()
        samples = [
            ("Sunny", "100", 31, 23, 0.0),
            ("Cloudy", "101", 30, 22, 0.2),
            ("Showers", "306", 28, 21, 3.5),
        ]
        mapped: list[DailyForecast] = []
        for i, (text, icon, tmax, tmin, p) in enumerate(samples[:3]):
            mapped.append(DailyForecast(
                date=(today + timedelta(days=i)).isoformat(),
                text_day=text,
                icon_day=icon,
                temp_max_c=tmax,
                temp_min_c=tmin,
                precip_mm=p,
                advice="带伞或注意防晒"
            ))
        fallback = WeatherForecast(
            location=destination,
            location_id=None,
            days=len(mapped),
            updated_at=datetime.now(timezone.utc).isoformat(),
            daily=mapped,
        )
        return {"weather": fallback}


def validators_node(state: PlanState) -> dict[str, Any]:
    # 使用现有服务为行程添加距离与开门标注
    if not state.plan:
        return {}
    annotated = validator.annotate_trip(state.plan)
    # violations: 简单规则——若有 open_ok 为 False 则记为违规
    violations: list[dict[str, Any]] = []
    for day in annotated.daily_plans:
        for act in day.activities:
            if act.open_ok is False:
                violations.append({"type": "closed", "name": act.name})
    return {"plan": annotated, "violations": violations}


def repair_node(state: PlanState) -> dict[str, Any]:
    # annotate_trip 已尝试替换；此处只打 repaired 标记
    return {"repaired": True}


def finalize_node(state: PlanState) -> dict[str, Any]:
    # 未来：补齐 sources、trace_id、指标等
    return {}


