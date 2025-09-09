import os
import time
from typing import Dict, Optional, List

import requests

from ..logging_config import get_logger
from ..config import get_settings

logger = get_logger(__name__)


class WeatherService:
    """简化的天气服务：城市名 → 天气预报，一步到位"""

    def __init__(self, api_key: Optional[str] = None, timeout_seconds: int = 5):
        settings = get_settings()
        self.api_key = api_key or settings.QWEATHER_API_KEY or os.getenv("QWEATHER_API_KEY")
        self.jwt_token = settings.QWEATHER_JWT or os.getenv("QWEATHER_JWT")
        self.timeout_seconds = timeout_seconds
        
        # 简化：只使用配置的Host，不支持动态覆盖
        api_host = (settings.QWEATHER_API_HOST or os.getenv("QWEATHER_API_HOST") or "").strip()
        if api_host:
            if api_host.startswith("http://") or api_host.startswith("https://"):
                self.base_url = api_host.rstrip("/")
            else:
                self.base_url = f"https://{api_host}"
            self.city_lookup_url = f"{self.base_url}/geo/v2/city/lookup"
            logger.info("Using custom QWeather API host: %s", self.base_url)
        else:
            # 默认公共域名
            self.base_url = "https://devapi.qweather.com"
            self.city_lookup_url = "https://geoapi.qweather.com/v2/city/lookup"

    # 简单内存缓存（30分钟）
    _cache: Dict[str, tuple[float, Dict]] = {}

    def _cache_get(self, key: str, ttl_seconds: int = 1800) -> Optional[Dict]:
        """获取缓存数据"""
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
        """设置缓存数据"""
        self._cache[key] = (time.time(), data)

    def _ensure_api_key(self) -> None:
        """确保API密钥已配置"""
        if not self.api_key:
            logger.error("QWEATHER_API_KEY is not configured")
            raise ValueError("QWEATHER_API_KEY is not configured")

    def _get_optimal_forecast_days(self, required_days: int) -> str:
        """
        根据所需天数选择最优的天气预报API参数
        
        Args:
            required_days: 需要的天气预报天数
            
        Returns:
            API天数参数 (3d, 7d, 10d, 15d, 30d)
        """
        if required_days <= 3:
            return "3d"
        elif required_days <= 7:
            return "7d"
        elif required_days <= 10:
            return "10d"
        elif required_days <= 15:
            return "15d"
        else:
            return "30d"

    def _get_forecast_url(self, days_param: str) -> str:
        """
        根据天数参数构建天气预报URL
        
        Args:
            days_param: 天数参数 (3d, 7d, 10d, 15d, 30d)
            
        Returns:
            完整的天气预报URL
        """
        return f"{self.base_url}/v7/weather/{days_param}"

    def city_lookup(self, location: str) -> Optional[str]:
        """
        查询城市的LocationID
        
        Args:
            location: 城市名称
            
        Returns:
            LocationID，失败返回None
        """
        self._ensure_api_key()
        
        params = {
            "key": self.api_key,
            "location": location,
        }
        headers = {}
        if self.jwt_token:
            headers["Authorization"] = f"Bearer {self.jwt_token}"
            
        logger.info("Looking up city: %s", location)
        
        try:
            resp = requests.get(
                self.city_lookup_url, 
                params=params, 
                headers=headers, 
                timeout=self.timeout_seconds
            )
            
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == "200" and data.get("location"):
                    loc = data["location"][0]
                    loc_id = loc.get("id")
                    logger.info("City lookup success: %s -> %s", location, loc_id)
                    return loc_id
                    
            logger.error("City lookup failed: http=%s, response=%s", 
                        resp.status_code, resp.text[:200])
            return None
            
        except requests.RequestException as exc:
            logger.error("City lookup request error: %s", exc)
            return None

    def get_forecast(self, city_name: str, days: int = 3) -> Optional[Dict]:
        """
        核心方法：根据城市名获取天气预报（智能选择API天数参数）
        
        Args:
            city_name: 城市名称，支持中文/英文
            days: 需要的预报天数，会智能选择合适的API参数
            
        Returns:
            天气预报数据，失败返回None
        """
        self._ensure_api_key()
        
        # 智能选择API天数参数
        api_days_param = self._get_optimal_forecast_days(days)
        forecast_url = self._get_forecast_url(api_days_param)
        
        # 优化缓存键：包含API参数
        cache_key = f"forecast:{city_name}:{api_days_param}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            # 返回缓存数据，但限制到请求的天数
            result = cached.copy()
            if result.get("daily"):
                result["daily"] = result["daily"][:days]
            return result

        # 第一步：查询LocationID
        location_id = self.city_lookup(city_name)
        if not location_id:
            # 兜底：尝试直接用城市名查询（某些情况下可能有效）
            logger.warning("LocationID lookup failed, trying direct city name: %s", city_name)
            location_id = city_name

        # 第二步：用LocationID查询天气
        params = {
            "key": self.api_key,
            "location": location_id,
        }
        
        headers = {}
        if self.jwt_token:
            headers["Authorization"] = f"Bearer {self.jwt_token}"

        logger.info("Fetching %s forecast for location: %s (need %d days)", 
                   api_days_param, location_id, days)
        
        try:
            resp = requests.get(
                forecast_url, 
                params=params, 
                headers=headers, 
                timeout=self.timeout_seconds
            )
            status = resp.status_code
            
            try:
                data: Dict = resp.json()
            except Exception:
                logger.error("Failed to parse weather response as JSON")
                return None
                
            if status == 200 and data.get("code") == "200" and data.get("daily"):
                daily_data = data.get("daily", [])
                result = {
                    "location": data.get("location", {}),
                    "daily": daily_data,  # 缓存完整数据
                    "update_time": data.get("updateTime"),
                    "fxLink": data.get("fxLink")
                }
                logger.info("Weather forecast success: %d days received (API: %s, need: %d) for %s", 
                           len(daily_data), api_days_param, days, city_name)
                self._cache_set(cache_key, result)
                
                # 返回限制到请求天数的数据
                result["daily"] = daily_data[:days]
                return result
                
            logger.error("Weather API failed: http=%s, code=%s, msg=%s", 
                        status, data.get("code"), data.get("text", ""))
            return None
            
        except requests.RequestException as exc:
            logger.error("Weather request failed: %s", exc)
            return None

    def test_connection(self, city_name: str = "Beijing") -> Dict[str, object]:
        """
        简化的连通性测试
        
        Args:
            city_name: 测试用的城市名
            
        Returns:
            测试结果状态
        """
        start_ts = time.time()
        
        try:
            self._ensure_api_key()
        except ValueError as e:
            return {
                "status": "error", 
                "message": str(e), 
                "api_key_configured": False
            }

        forecast = self.get_forecast(city_name, days=3)
        elapsed_ms = int((time.time() - start_ts) * 1000)
        
        if forecast is None:
            return {
                "status": "unavailable",
                "message": f"Failed to get forecast for {city_name}",
                "api_key_configured": True,
                "elapsed_ms": elapsed_ms,
                "city": city_name,
            }

        return {
            "status": "available",
            "message": f"Weather service working for {city_name}",
            "api_key_configured": True,
            "elapsed_ms": elapsed_ms,
            "city": city_name,
            "daily_count": len(forecast.get("daily", [])),
        }

    def generate_advice(self, temp_max: int, precip: float) -> str:
        """
        根据温度和降水生成出行建议
        
        Args:
            temp_max: 最高温度
            precip: 降水量
            
        Returns:
            出行建议文本
        """
        advice = []
        
        # 穿衣建议
        if temp_max < 5:
            advice.append("穿厚外套/羽绒服")
        elif temp_max < 15:
            advice.append("穿夹克/薄外套")
        elif temp_max < 25:
            advice.append("长袖衬衫")
        else:
            advice.append("轻薄上衣即可")
            
        # 降水建议
        if precip >= 0.3:
            advice.append("带伞或防水外套")
        elif precip > 0:
            advice.append("可能有小雨")
            
        return "，".join(advice)