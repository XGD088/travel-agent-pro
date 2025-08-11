import os
import time
from typing import Dict, Optional, Tuple

import requests

from ..logging_config import get_logger

logger = get_logger(__name__)


class AmapService:
    """Amap (Gaode) Web Service client for geocoding and distance matrix."""

    def __init__(self, api_key: Optional[str] = None, timeout_seconds: int = 10):
        self.api_key = api_key or os.getenv("AMAP_API_KEY")
        self.timeout_seconds = timeout_seconds
        self.base_geocode_url = "https://restapi.amap.com/v3/geocode/geo"
        self.base_distance_url = "https://restapi.amap.com/v3/distance"
        self.base_place_url = "https://restapi.amap.com/v3/place/text"
        self._place_cache: Dict[str, dict] = {}

    def _ensure_api_key(self) -> None:
        if not self.api_key:
            logger.error("AMAP_API_KEY 未配置")
            raise ValueError("AMAP_API_KEY 未配置")

    def geocode(self, address: str, city: Optional[str] = None) -> Optional[Tuple[float, float]]:
        """Geocode a textual address to (lng, lat). Returns None if not found.
        Fallback: place search API when geocode has no result.
        """
        self._ensure_api_key()
        params: Dict[str, str] = {
            "key": self.api_key,
            "address": address,
            "output": "json",
        }
        if city:
            params["city"] = city

        logger.debug(f"调用高德地理编码: address={address}, city={city}")
        try:
            resp = requests.get(self.base_geocode_url, params=params, timeout=self.timeout_seconds)
            resp.raise_for_status()
            data = resp.json()
            if data.get("status") == "1" and data.get("geocodes"):
                location = data["geocodes"][0].get("location")
                if location:
                    lng_str, lat_str = location.split(",")
                    return float(lng_str), float(lat_str)
            logger.warning(f"地理编码无结果，尝试地点搜索兜底: {data}")
        except requests.RequestException as exc:
            logger.error(f"地理编码请求出错: {exc}")

        # Fallback to place search
        try:
            place_params: Dict[str, str] = {
                "key": self.api_key,
                "keywords": address,
                "offset": "1",
                "page": "1",
                "output": "json",
            }
            if city:
                place_params["city"] = city
            logger.debug(f"调用高德地点搜索兜底: keywords={address}, city={city}")
            resp2 = requests.get(self.base_place_url, params=place_params, timeout=self.timeout_seconds)
            resp2.raise_for_status()
            data2 = resp2.json()
            if data2.get("status") == "1" and data2.get("pois"):
                location2 = data2["pois"][0].get("location")
                if location2:
                    lng_str, lat_str = location2.split(",")
                    return float(lng_str), float(lat_str)
            logger.warning(f"地点搜索兜底无结果: {data2}")
        except requests.RequestException as exc:
            logger.error(f"地点搜索请求出错: {exc}")
        return None

    def get_poi_open_hours(self, keyword: str, city: Optional[str] = None) -> Optional[str]:
        """Try to fetch POI open hours from AMap place search by a keyword (name/address).
        Returns raw business hours string or None when missing.
        """
        self._ensure_api_key()
        cache_key = f"{keyword}|{city or ''}"
        if cache_key in self._place_cache:
            place = self._place_cache[cache_key]
        else:
            params: Dict[str, str] = {
                "key": self.api_key,
                "keywords": keyword,
                "offset": "1",
                "page": "1",
                "output": "json",
            }
            if city:
                params["city"] = city
            try:
                resp = requests.get(self.base_place_url, params=params, timeout=self.timeout_seconds)
                resp.raise_for_status()
                data = resp.json()
                if data.get("status") == "1" and data.get("pois"):
                    place = data["pois"][0]
                    self._place_cache[cache_key] = place
                else:
                    logger.info("No POI found for business hours query")
                    return None
            except requests.RequestException as exc:
                logger.error(f"Failed to fetch place for hours: {exc}")
                return None

        # Common fields in AMap POI: business_hours / opentime / opentime_week (varies)
        for field in ["business_hours", "opentime", "opentime_week", "biz_ext"]:
            value = place.get(field)
            if isinstance(value, str) and value.strip():
                logger.debug("Open hours fetched (field=%s): %s", field, value)
                return value.strip()
            if field == "biz_ext" and isinstance(value, dict):
                # Some POIs nest open time under biz_ext.open_time
                inner = value.get("open_time") or value.get("open_hours")
                if isinstance(inner, str) and inner.strip():
                    logger.debug("Open hours fetched (biz_ext.open_time): %s", inner)
                    return inner.strip()
        logger.info("Open hours missing in POI response")
        return None

    def driving_distance(self, origin: Tuple[float, float], destination: Tuple[float, float]) -> Optional[Tuple[int, int]]:
        """
        Driving distance and duration between two points.
        Returns (distance_m, duration_s) or None on failure.
        """
        self._ensure_api_key()
        params: Dict[str, str] = {
            "key": self.api_key,
            "origins": f"{origin[0]},{origin[1]}",
            "destination": f"{destination[0]},{destination[1]}",
            "type": "1",  # 1: driving
            "output": "json",
        }
        logger.debug(f"调用高德距离: origin={origin}, destination={destination}")
        try:
            resp = requests.get(self.base_distance_url, params=params, timeout=self.timeout_seconds)
            resp.raise_for_status()
            data = resp.json()
            if data.get("status") != "1" or not data.get("results"):
                logger.warning(f"距离查询失败: {data}")
                return None
            result = data["results"][0]
            # API returns strings
            distance_m = int(float(result.get("distance", 0)))
            duration_s = int(float(result.get("duration", 0)))
            return distance_m, duration_s
        except requests.RequestException as exc:
            logger.error(f"距离查询请求出错: {exc}")
            return None

    def test_connection(self) -> Dict[str, object]:
        """Run a basic geocode test to verify connectivity and key validity."""
        start_ts = time.time()
        try:
            self._ensure_api_key()
        except ValueError as e:
            return {"status": "error", "message": str(e), "api_key_configured": False}

        # Use two well-known Beijing landmarks
        tiananmen = self.geocode("天安门广场", city="北京")
        forbidden_city = self.geocode("故宫博物院", city="北京")
        elapsed_ms = int((time.time() - start_ts) * 1000)

        if not tiananmen or not forbidden_city:
            return {
                "status": "partial",
                "message": "地理编码失败（请检查配额与Key）",
                "api_key_configured": True,
                "elapsed_ms": elapsed_ms,
                "tiananmen": tiananmen,
                "forbidden_city": forbidden_city,
            }

        drive = self.driving_distance(tiananmen, forbidden_city)
        result: Dict[str, object] = {
            "status": "available" if drive else "geocoded_only",
            "message": "地理编码与距离查询成功" if drive else "地理编码成功，距离查询失败",
            "api_key_configured": True,
            "elapsed_ms": elapsed_ms,
            "tiananmen": {"lng": tiananmen[0], "lat": tiananmen[1]},
            "forbidden_city": {"lng": forbidden_city[0], "lat": forbidden_city[1]},
        }
        if drive:
            distance_m, duration_s = drive
            result.update({
                "distance_m": distance_m,
                "duration_s": duration_s,
                "distance_km": round(distance_m / 1000.0, 2),
                "drive_time_min": int(round(duration_s / 60.0)),
            })
        return result

    def geocode_debug(self, address: str, city: Optional[str] = None) -> Dict[str, object]:
        """Return raw responses from geocode and place fallback for debugging."""
        self._ensure_api_key()
        out: Dict[str, object] = {"address": address, "city": city}
        # primary
        params: Dict[str, str] = {
            "key": self.api_key,
            "address": address,
            "output": "json",
        }
        if city:
            params["city"] = city
        try:
            resp = requests.get(self.base_geocode_url, params=params, timeout=self.timeout_seconds)
            out["geocode_status_code"] = resp.status_code
            out["geocode_url"] = resp.url
            out["geocode_json"] = resp.json()
        except Exception as e:
            out["geocode_error"] = str(e)

        # fallback
        place_params: Dict[str, str] = {
            "key": self.api_key,
            "keywords": address,
            "offset": "1",
            "page": "1",
            "output": "json",
        }
        if city:
            place_params["city"] = city
        try:
            resp2 = requests.get(self.base_place_url, params=place_params, timeout=self.timeout_seconds)
            out["place_status_code"] = resp2.status_code
            out["place_url"] = resp2.url
            out["place_json"] = resp2.json()
        except Exception as e:
            out["place_error"] = str(e)
        return out 