from typing import Any

from ..logging_config import get_logger
from ..schemas import TripPlan, DailyForecast, WeatherForecast
from .state import PlanState
from app.utils.weather_utils import try_get_real_weather, generate_fallback_weather
from app.logging_config import get_logger

logger = get_logger(__name__)

def _get_services():
    """获取全局服务实例"""
    from .. import api
    return {
        'qwen': api.qwen_service,
        'poi': api.poi_service,
        'amap': api.amap_service,
        'weather': api.weather_service,
        'validator': api.route_validator
    }


def planner_node(state: PlanState) -> dict[str, Any]:
    # 复用现有主流程：先直接产出一个初版 plan
    services = _get_services()
    plan: TripPlan = services['qwen'].generate_trip_plan(state.request)
    return {"plan": plan}


def retriever_node(state: PlanState) -> dict[str, Any]:
    # 最小版：planner 里已注入 RAG。此处预留位后续扩展（补证据/sources）
    return {}


def scheduler_node(state: PlanState) -> dict[str, Any]:
    # 最小版：先不做调序（保持 LLM 顺序）。后续引入贪心/OR-Tools
    return {}


def weather_node(state: PlanState) -> dict[str, Any]:
    """智能天气节点：根据旅行天数获取对应的天气预报"""
    destination = state.request.destination or "Beijing"
    trip_days = state.request.duration_days or 3
    

    logger.info("Getting %d-day weather forecast for %s", trip_days, destination)
    
    # 尝试获取真实天气数据
    weather = try_get_real_weather(destination, trip_days)
    if weather:
        return {"weather": weather}
    
    # 降级到样例数据
    fallback_weather = generate_fallback_weather(destination, trip_days)
    return {"weather": fallback_weather}


def validators_node(state: PlanState) -> dict[str, Any]:
    # 使用现有服务为行程添加距离与开门标注
    if not state.plan:
        return {}
    services = _get_services()
    annotated = services['validator'].annotate_trip(state.plan)
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


