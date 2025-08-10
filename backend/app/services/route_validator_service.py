from typing import Dict, Optional, Tuple

from ..schemas import TripPlan
from .amap_service import AmapService
from ..logging_config import get_logger

logger = get_logger(__name__)


class RouteValidatorService:
    """
    Annotates a TripPlan with driving distance and duration between consecutive activities per day.
    Keeps architecture simple: no persistence, just AmapService + minimal in-memory cache.
    """

    def __init__(self, amap_service: Optional[AmapService] = None):
        self.amap = amap_service or AmapService()
        self._geocode_cache: Dict[str, Tuple[float, float]] = {}

    def _get_coords(self, address: str, city_hint: Optional[str] = None) -> Optional[Tuple[float, float]]:
        if address in self._geocode_cache:
            return self._geocode_cache[address]
        coords = self.amap.geocode(address, city=city_hint or "北京")
        if coords:
            self._geocode_cache[address] = coords
        return coords

    def annotate_trip(self, trip: TripPlan) -> TripPlan:
        city_hint = trip.destination or "北京"
        for day in trip.daily_plans:
            prev_coords: Optional[Tuple[float, float]] = None
            for idx, act in enumerate(day.activities):
                # Reset fields to ensure idempotency
                act.distance_km_from_prev = None
                act.drive_time_min_from_prev = None

                coords = self._get_coords(act.location, city_hint)
                if idx == 0:
                    prev_coords = coords
                    continue

                if not prev_coords or not coords:
                    prev_coords = coords
                    continue

                drive = self.amap.driving_distance(prev_coords, coords)
                if drive:
                    distance_m, duration_s = drive
                    act.distance_km_from_prev = round(distance_m / 1000.0, 2)
                    act.drive_time_min_from_prev = int(round(duration_s / 60.0))
                prev_coords = coords
        return trip 