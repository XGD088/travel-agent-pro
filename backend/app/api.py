from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .schemas import TripRequest, TripPlan
from .services import QwenService
from .services.poi_embedding_service import POIEmbeddingService
from .services import WeatherService
from .services import AmapService
from .schemas import WeatherForecast, DailyForecast
from .graph import get_graph, PlanState
from typing import Dict
import os
from dotenv import load_dotenv, find_dotenv
from .logging_config import setup_logging, get_logger
from .services.route_validator_service import RouteValidatorService

# 加载环境变量（优先找到项目根的 .env，允许覆盖 shell）
load_dotenv(find_dotenv(usecwd=True), override=True)

# 设置日志系统
setup_logging()
logger = get_logger(__name__)

# 延迟初始化服务（在环境变量加载后）
def _init_services():
    """初始化所有服务"""
    global qwen_service, poi_service, amap_service, weather_service, route_validator, graph
    
    print("🚀 INIT: 开始初始化服务...")  # 添加 print 调试
    logger.info("🚀 开始初始化服务...")
    
    try:
        from .config import get_settings
        settings = get_settings()
        qwen_service = QwenService()
        poi_service = POIEmbeddingService()
        amap_service = AmapService(api_key=settings.AMAP_API_KEY)
        weather_service = WeatherService(api_key=settings.QWEATHER_API_KEY)
        route_validator = RouteValidatorService(amap_service)
        graph = get_graph()
        print("✅ INIT: 服务初始化完成")  # 添加 print 调试
        logger.info("✅ 服务初始化完成")
        return True
    except Exception as e:
        print(f"❌ INIT: 服务初始化失败: {e}")  # 添加 print 调试
        logger.error(f"❌ 服务初始化失败: {e}")
        return False

# 立即初始化服务
try:
    _init_services()
except Exception as e:
    print(f"❌ 模块级别初始化失败: {e}")
    logger.error(f"❌ 模块级别初始化失败: {e}")

app = FastAPI(
    title="Travel Agent Pro API",
    description="AI-Powered Weekend Trip Planner Backend (Powered by Qwen + RAG)",
    version="1.0.0"
)



# 添加 CORS 中间件以允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # 允许前端域名（3001 为端口回退时使用）
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 惰性初始化守护
def ensure_initialized() -> None:
    """确保服务与图已初始化（热重载/导入顺序安全）。"""
    global qwen_service, poi_service, amap_service, weather_service, route_validator, graph
    if any(x is None for x in [
        globals().get("qwen_service"),
        globals().get("poi_service"),
        globals().get("amap_service"),
        globals().get("weather_service"),
        globals().get("route_validator"),
        globals().get("graph"),
    ]):
        _init_services()



@app.get("/health")
def health():
    """健康检查接口"""
    logger.info("Health check requested")
    return {"status": "ok"}

@app.get("/")
def root():
    """API根路径"""
    return {"message": "Travel Agent Pro Backend API"}




@app.post("/destination-weather")
async def destination_weather(payload: Dict[str, str]):
    """简化的目的地天气接口：文本 → 目的地 → 天气预报

    输入: { text: string }
    输出: { destination_context: {...}, weather: WeatherForecast }
    """
    try:
        ensure_initialized()
        text = (payload.get("text") or "").strip()
        if not text:
            raise HTTPException(status_code=400, detail="text is required")

        # 使用 QwenService 提取目的地
        destinations = qwen_service.extract_destinations(text)
        destination = destinations[0] if destinations else text
        
        # 尝试地理编码获取坐标
        coords = amap_service.geocode(destination)
        if not coords:
            # 兜底：直接用城市名查询天气
            weather = await get_weather_forecast(location=destination, days=3)
            return {"destination_context": {"destination": destination}, "weather": weather}
        
        lng, lat = coords

        # 优先使用坐标查询天气（更精确）
        coord_str = f"{lng},{lat}"
        weather = await get_weather_forecast(location=coord_str, days=3)
        return {"destination_context": {"destination": destination, "lng": lng, "lat": lat}, "weather": weather}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("destination-weather failed: %s", e)
        raise HTTPException(status_code=500, detail="destination-weather failed")

@app.get("/weather/forecast", response_model=WeatherForecast)
async def get_weather_forecast(location: str = "Beijing", days: int = 3):
    """智能天气预报接口：根据天数自动选择最优API参数"""
    try:
        ensure_initialized()
        
        # 限制天数范围：1-30天
        days = min(30, max(1, days))
        
        # 使用智能天数选择的天气服务
        forecast_raw = weather_service.get_forecast(location, days=days)

        if forecast_raw and forecast_raw.get("daily"):
            daily_raw = forecast_raw.get("daily", [])
            mapped: list[DailyForecast] = []
            for d in daily_raw:
                temp_max = int(float(d.get("tempMax", 20)))
                precip = float(d.get("precip") or 0.0)
                mapped.append(DailyForecast(
                    date=d.get("fxDate"),
                    text_day=d.get("textDay"),
                    icon_day=d.get("iconDay"),
                    temp_max_c=temp_max,
                    temp_min_c=int(float(d.get("tempMin", 15))),
                    precip_mm=precip,
                    advice=weather_service.generate_advice(temp_max, precip)
                ))
            from datetime import datetime, timezone
            return WeatherForecast(
                location=location,
                location_id=forecast_raw.get("location", {}).get("id"),
                days=len(mapped),
                updated_at=datetime.now(timezone.utc).isoformat(),
                daily=mapped,
            )

        # 降级：返回固定示例，确保前端不被阻塞
        logger.warning("Weather upstream unavailable; return local fallback")
        # 构造schema一致的降级数据
        from datetime import datetime, timedelta, timezone
        today = datetime.now(timezone.utc).date()
        samples = [
            ("Sunny", "100", 31, 23, 0.0),
            ("Cloudy", "101", 30, 22, 0.2),
            ("Showers", "306", 28, 21, 3.5),
        ]
        mapped: list[DailyForecast] = []
        for i, (text, icon, tmax, tmin, p) in enumerate(samples[: max(1, min(3, days))]):
            mapped.append(DailyForecast(
                date=(today + timedelta(days=i)).isoformat(),
                text_day=text,
                icon_day=icon,
                temp_max_c=tmax,
                temp_min_c=tmin,
                precip_mm=p,
                advice=weather_service.generate_advice(tmax, p)
            ))
        return WeatherForecast(
            location=location,
            location_id=None,  # 降级时没有location_id
            days=len(mapped),
            updated_at=datetime.now(timezone.utc).isoformat(),
            daily=mapped,
        )
    except Exception as e:
        logger.error(f"❌ 获取天气预报失败: {e}")
        logger.warning("Weather upstream unavailable; return local fallback")
        # 继续执行兜底逻辑而不是抛出 HTTPException
        from datetime import datetime, timedelta, timezone
        today = datetime.now(timezone.utc).date()
        samples = [
            ("Sunny", "100", 31, 23, 0.0),
            ("Cloudy", "101", 30, 22, 0.2),
            ("Showers", "306", 28, 21, 3.5),
        ]
        mapped: list[DailyForecast] = []
        for i, (text, icon, tmax, tmin, p) in enumerate(samples[: max(1, min(3, days))]):
            mapped.append(DailyForecast(
                date=(today + timedelta(days=i)).isoformat(),
                text_day=text,
                icon_day=icon,
                temp_max_c=tmax,
                temp_min_c=tmin,
                precip_mm=p,
                advice=weather_service.generate_advice(tmax, p)
            ))
        return WeatherForecast(
            location=location,
            location_id=None,
            days=len(mapped),
            updated_at=datetime.now(timezone.utc).isoformat(),
            daily=mapped,
        )

@app.post("/plan-bundle")
async def plan_bundle(request: TripRequest):
    """返回组合结果：{ plan, weather }，便于前端一次获取。"""
    try:
        ensure_initialized()
        state = PlanState(request=request)
        final_state = graph.invoke(state)
        if not final_state or not final_state.get("plan"):
            raise HTTPException(status_code=500, detail="planning failed")
        return {
            "plan": final_state.get("plan"),
            "weather": final_state.get("weather")
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("/plan-bundle failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="plan-bundle failed")