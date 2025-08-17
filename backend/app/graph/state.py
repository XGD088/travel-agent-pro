from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from ..schemas import TripRequest, TripPlan, WeatherForecast


class PlanState(BaseModel):
    """Minimal graph state for planning pipeline."""

    request: TripRequest
    plan: Optional[TripPlan] = None
    weather: Optional[WeatherForecast] = None
    violations: List[Dict[str, Any]] = []
    sources: List[Dict[str, Any]] = []
    repaired: bool = False


