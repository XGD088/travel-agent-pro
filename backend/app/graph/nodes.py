from typing import Any

from ..services.qwen_service import QwenService
from ..services.poi_embedding_service import POIEmbeddingService
from ..services.route_validator_service import RouteValidatorService
from ..services.amap_service import AmapService
from ..services.weather_service import WeatherService
from ..config import get_settings
from ..logging_config import get_logger
from ..schemas import TripPlan
from .state import PlanState


logger = get_logger(__name__)
_settings = get_settings()
qwen = QwenService()
poi = POIEmbeddingService()
amap = AmapService(api_key=_settings.AMAP_API_KEY)
weather = WeatherService(api_key=_settings.QWEATHER_API_KEY)
validator = RouteValidatorService(amap)


def planner_node(state: PlanState) -> PlanState:
    # 复用现有主流程：先直接产出一个初版 plan
    plan: TripPlan = qwen.generate_trip_plan(state.request)
    state.plan = plan
    return state


def retriever_node(state: PlanState) -> PlanState:
    # 最小版：planner 里已注入 RAG。此处预留位后续扩展（补证据/sources）
    return state


def scheduler_node(state: PlanState) -> PlanState:
    # 最小版：先不做调序（保持 LLM 顺序）。后续引入贪心/OR-Tools
    return state


def validators_node(state: PlanState) -> PlanState:
    # 使用现有服务为行程添加距离与开门标注
    if not state.plan:
        return state
    annotated = validator.annotate_trip(state.plan)
    state.plan = annotated
    # violations: 简单规则——若有 open_ok 为 False 则记为违规
    violations: list[dict[str, Any]] = []
    for day in annotated.daily_plans:
        for act in day.activities:
            if act.open_ok is False:
                violations.append({"type": "closed", "name": act.name})
    state.violations = violations
    return state


def repair_node(state: PlanState) -> PlanState:
    # annotate_trip 已尝试替换；此处只打 repaired 标记
    state.repaired = True
    return state


def finalize_node(state: PlanState) -> PlanState:
    # 未来：补齐 sources、trace_id、指标等
    return state


