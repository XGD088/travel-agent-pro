import os
import time
from typing import Dict, Optional, Tuple

import requests

from ..logging_config import get_logger
from ..config import get_settings

logger = get_logger(__name__)


class WeatherService:
    """QWeather (和风天气) client.

    提供基础的城市查询与3日天气预报能力，用于连通性与Key有效性验证。
    """

    def __init__(self, api_key: Optional[str] = None, timeout_seconds: int = 5):
        settings = get_settings()
        self.api_key = api_key or settings.QWEATHER_API_KEY or os.getenv("QWEATHER_API_KEY")
        self.jwt_token = settings.QWEATHER_JWT or os.getenv("QWEATHER_JWT")
        self.timeout_seconds = timeout_seconds
        # 支持自定义 API Host（和风控制台分配的专属域名）
        self.api_host = (settings.QWEATHER_API_HOST or os.getenv("QWEATHER_API_HOST") or "").strip()
        if self.api_host:
            if self.api_host.startswith("http://") or self.api_host.startswith("https://"):
                base = self.api_host.rstrip("/")
            else:
                base = f"https://{self.api_host}"
            # 使用同一 Host 下的 Geo 与 Weather 路径（注意 Geo 前缀）
            self.city_lookup_url = f"{base}/geo/v2/city/lookup"
            self.forecast_3d_url = f"{base}/v7/weather/3d"
            self.now_url = f"{base}/v7/weather/now"
            logger.info("Using custom QWeather API host: %s", base)
        else:
            # 默认公共域名（可能受限，若返回 Invalid Host 需配置自定义 Host）
            self.city_lookup_url = "https://geoapi.qweather.com/v2/city/lookup"
            self.forecast_3d_url = "https://devapi.qweather.com/v7/weather/3d"
            self.now_url = "https://devapi.qweather.com/v7/weather/now"

    def _urls(self, host_override: Optional[str] = None):
        """根据 override 或已配置 host 生成各 API URL。"""
        host = (host_override or self.api_host or "").strip()
        if host:
            if host.startswith("http://") or host.startswith("https://"):
                base = host.rstrip("/")
            else:
                base = f"https://{host}"
            return (
                f"{base}/geo/v2/city/lookup",
                f"{base}/v7/weather/3d",
                f"{base}/v7/weather/now",
            )
        return (
            "https://geoapi.qweather.com/v2/city/lookup",
            "https://devapi.qweather.com/v7/weather/3d",
            "https://devapi.qweather.com/v7/weather/now",
        )

    # 简单内存缓存（30分钟）
    _cache: Dict[str, Tuple[float, Dict]] = {}

    def _cache_get(self, key: str, ttl_seconds: int = 1800) -> Optional[Dict]:
        now = time.time()
        item = self._cache.get(key)
        if not item:
            return None
        ts, data = item
        if now - ts <= ttl_seconds:
            logger.info("Weather cache hit: %s", key)
            return data
        self._cache.pop(key, None)
        return None

    def _cache_set(self, key: str, data: Dict) -> None:
        self._cache[key] = (time.time(), data)

    def _ensure_api_key(self) -> None:
        if not self.api_key:
            logger.error("QWEATHER_API_KEY is not configured")
            raise ValueError("QWEATHER_API_KEY is not configured")

    def city_lookup(self, location: str, host_override: Optional[str] = None) -> Optional[str]:
        """根据城市名/地名查找 location id。

        返回第一个匹配的 location id，未找到则返回 None。
        """
        self._ensure_api_key()
        city_lookup_url, _, _ = self._urls(host_override)
        params = {
            "key": self.api_key,
            "location": location,
        }
        headers = {}
        if self.jwt_token:
            headers["Authorization"] = f"Bearer {self.jwt_token}"
        logger.info("Looking up city: %s", location)
        try:
            resp = requests.get(city_lookup_url, params=params, headers=headers, timeout=self.timeout_seconds)
            status = resp.status_code
            text = resp.text
            try:
                data: Dict = resp.json()
            except Exception:
                data = {"raw": text[:512]}
            if status == 200 and data.get("code") == "200" and data.get("location"):
                loc = data["location"][0]
                loc_id = loc.get("id")
                logger.info("City lookup success: %s -> %s", location, loc_id)
                return loc_id
            logger.error("City lookup failed: http=%s, code=%s, body=%s", status, data.get("code"), str(data)[:256])
            return None
        except requests.RequestException as exc:
            logger.error("City lookup request error: %s", exc)
            return None

    def forecast_3d(self, location_id: str, host_override: Optional[str] = None) -> Optional[Dict]:
        """获取3日天气预报原始数据。

        成功时返回响应 JSON；失败返回 None。
        """
        self._ensure_api_key()
        _, forecast_3d_url, _ = self._urls(host_override)
        params = {
            "key": self.api_key,
            "location": location_id,
        }
        headers = {}
        if self.jwt_token:
            headers["Authorization"] = f"Bearer {self.jwt_token}"
        logger.info("Fetching 3-day forecast: %s", location_id)
        cache_key = f"3d:{host_override or self.api_host}:{location_id}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached
        try:
            resp = requests.get(forecast_3d_url, params=params, headers=headers, timeout=self.timeout_seconds)
            status = resp.status_code
            text = resp.text
            try:
                data: Dict = resp.json()
            except Exception:
                data = {"raw": text[:512]}
            if status == 200 and data.get("code") == "200" and data.get("daily"):
                logger.info("Forecast fetch success: %d days", len(data.get("daily", [])))
                self._cache_set(cache_key, data)
                return data
            logger.error("Forecast fetch failed: http=%s, code=%s, body=%s", status, data.get("code"), str(data)[:256])
            return None
        except requests.RequestException as exc:
            logger.error("Forecast request error: %s", exc)
            return None

    def now_weather(self, location: str, host_override: Optional[str] = None) -> Optional[Dict]:
        """获取实时天气，作为连通性降级检测。"""
        self._ensure_api_key()
        _, _, now_url = self._urls(host_override)
        params = {
            "key": self.api_key,
            "location": location,
        }
        headers = {}
        if self.jwt_token:
            headers["Authorization"] = f"Bearer {self.jwt_token}"
        logger.info("Fetching now weather: %s", location)
        try:
            resp = requests.get(now_url, params=params, headers=headers, timeout=self.timeout_seconds)
            status = resp.status_code
            text = resp.text
            try:
                data: Dict = resp.json()
            except Exception:
                data = {"raw": text[:512]}
            if status == 200 and data.get("code") == "200" and data.get("now"):
                logger.info("Now weather fetch success")
                return data
            logger.error("Now weather fetch failed: http=%s, code=%s, body=%s", status, data.get("code"), str(data)[:256])
            return None
        except requests.RequestException as exc:
            logger.error("Now weather request error: %s", exc)
            return None

    def test_connection(self, location: str = "Beijing", host_override: Optional[str] = None) -> Dict[str, object]:
        """连通性自检：城市查询 + 3日预报。

        返回简单状态对象以便在 /weather-status 暴露。
        """
        start_ts = time.time()
        try:
            self._ensure_api_key()
        except ValueError as e:
            return {"status": "error", "message": str(e), "api_key_configured": False}

        loc_id = self.city_lookup(location, host_override=host_override)
        elapsed_ms = int((time.time() - start_ts) * 1000)
        if not loc_id:
            # 兜底：直接用传入的 location 名称尝试 forecast
            logger.warning("City lookup failed, try forecast with raw location string: %s", location)
            forecast = self.forecast_3d(location, host_override=host_override)
            if forecast is None:
                # 再兜底一次：尝试中文名
                alt = "北京" if location.lower() == "beijing" else location
                if alt != location:
                    logger.info("Retry forecast with alt name: %s", alt)
                    forecast = self.forecast_3d(alt)
            if forecast is None:
                return {
                    "status": "unavailable",
                    "message": "City lookup failed and direct forecast failed",
                    "api_key_configured": True,
                    "elapsed_ms": elapsed_ms,
                    "location": location,
                }
            return {
                "status": "available",
                "message": "Direct forecast success without city lookup",
                "api_key_configured": True,
                "elapsed_ms": elapsed_ms,
                "location": location,
                "daily_count": len(forecast.get("daily", [])),
            }

        forecast = self.forecast_3d(loc_id, host_override=host_override)
        elapsed_ms = int((time.time() - start_ts) * 1000)
        if forecast is None:
            # Try now weather as degraded check
            now = self.now_weather(loc_id, host_override=host_override)
            if now is not None:
                return {
                    "status": "now_only",
                    "message": "City lookup ok, now available; 3-day forecast failed",
                    "api_key_configured": True,
                    "elapsed_ms": elapsed_ms,
                    "location": location,
                    "location_id": loc_id,
                }
            else:
                return {
                    "status": "lookup_ok",
                    "message": "City lookup ok, both forecast and now failed",
                    "api_key_configured": True,
                    "elapsed_ms": elapsed_ms,
                    "location": location,
                    "location_id": loc_id,
                }

        return {
            "status": "available",
            "message": "City lookup and 3-day forecast success",
            "api_key_configured": True,
            "elapsed_ms": elapsed_ms,
            "location": location,
            "location_id": loc_id,
            "daily_count": len(forecast.get("daily", [])),
        }


