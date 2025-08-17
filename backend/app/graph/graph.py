from langgraph.graph import StateGraph, END
from .state import PlanState
from .nodes import planner_node, retriever_node, scheduler_node, validators_node, repair_node, finalize_node, weather_node


_compiled_graph = None


def get_graph():
    global _compiled_graph
    if _compiled_graph is not None:
        return _compiled_graph

    g = StateGraph(PlanState)
    g.add_node("planner", planner_node)
    g.add_node("retriever", retriever_node)
    g.add_node("scheduler", scheduler_node)
    g.add_node("validators", validators_node)
    g.add_node("weather", weather_node)
    g.add_node("repair", repair_node)
    g.add_node("finalize", finalize_node)

    g.set_entry_point("planner")
    g.add_edge("planner", "retriever")
    g.add_edge("retriever", "scheduler")
    g.add_edge("scheduler", "validators")
    # 天气不阻断主链路，放在并行支线，validators 之后或之前均可，这里放在 validators 之后
    g.add_edge("validators", "weather")

    def _route(state: PlanState):
        return "repair" if state.violations else "finalize"

    g.add_conditional_edges("validators", _route, {"repair": "repair", "finalize": "finalize"})
    g.add_edge("repair", "finalize")
    # weather 不影响 finalize 的条件，直接收敛到 finalize
    g.add_edge("weather", "finalize")
    g.add_edge("finalize", END)
    _compiled_graph = g.compile()
    return _compiled_graph


