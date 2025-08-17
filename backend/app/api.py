from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .schemas import TripRequest, TripPlan, FreeTextPlanRequest
from .services import QwenService
from .services.poi_embedding_service import POIEmbeddingService
from .services import WeatherService
from .services import AmapService
from .schemas import WeatherForecast, DailyForecast
from .schemas import DestinationContext, PlanWithContext, FreeTextWithOptions
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


def _gen_advice(temp_max_c: int, precip_mm: float) -> str:
    """根据最高温与降水量生成简短建议（中文）。"""
    advice = []
    if temp_max_c < 5:
        advice.append("穿厚外套/羽绒服")
    elif temp_max_c < 15:
        advice.append("穿夹克/薄外套")
    else:
        advice.append("轻薄上衣即可")
    if precip_mm >= 0.3:
        advice.append("带伞或防水外套")
    return "，".join(advice)

@app.post("/init-poi-data")
async def init_poi_data():
    """初始化POI数据到向量数据库"""
    logger.info("🚀 开始初始化POI数据")
    
    try:
        success = poi_service.embed_and_store_pois()
        if success:
            stats = poi_service.get_collection_stats()
            logger.info(f"✅ POI数据初始化成功: {stats}")
            return {
                "status": "success",
                "message": "POI数据初始化成功",
                "stats": stats
            }
        else:
            logger.error("❌ POI数据初始化失败")
            raise HTTPException(status_code=500, detail="POI数据初始化失败")
            
    except Exception as e:
        logger.error(f"❌ POI数据初始化出错: {e}")
        raise HTTPException(status_code=500, detail=f"POI数据初始化出错: {e}")

@app.get("/poi-stats")
async def get_poi_stats():
    """获取POI向量数据库统计信息"""
    logger.info("📊 获取POI统计信息")
    
    try:
        stats = poi_service.get_collection_stats()
        return stats
    except Exception as e:
        logger.error(f"❌ 获取POI统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取POI统计信息失败: {e}")

@app.post("/generate-trip", response_model=TripPlan)
async def generate_trip(request: TripRequest):
    """生成旅行计划"""
    logger.info(f"🚀 开始生成旅行计划: {request.destination}, {request.duration_days}天")
    logger.debug(f"请求详情: {request.dict()}")
    
    try:
        # 检查 Qwen API Key
        api_key = os.getenv("DASHSCOPE_API_KEY")
        logger.debug(f"API Key 状态: {'已配置' if api_key else '未配置'}")
        
        if not api_key:
            logger.error("❌ DASHSCOPE_API_KEY 未配置")
            raise HTTPException(
                status_code=500,
                detail="DASHSCOPE API Key not configured"
            )

        logger.info(f"✅ API Key 已配置，开始调用 Qwen 服务")

        # 调用 Qwen 服务生成计划
        trip_plan = qwen_service.generate_trip_plan(request)

        logger.info(f"✅ 成功生成旅行计划: {request.destination}")
        logger.debug(f"生成的计划概要: {trip_plan.destination}, {len(trip_plan.daily_plans)}天")
        return trip_plan

    except ValueError as e:
        logger.error(f"❌ 验证错误: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"❌ 意外错误: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/resolve-destination")
async def resolve_destination(payload: Dict[str, str]):
    """自由文本 → 目的地候选提取 → geocode → regeo → 统一返回目的地上下文。

    输入: { text: string }
    输出: {
      raw_input, candidates: string[], selected: string | null,
      lng: number | null, lat: number | null,
      city: string | null, province: string | null, country: string | null, adcode: string | null,
      formatted_address: string | null
    }
    """
    try:
        # 确保服务初始化，避免热重载后出现 NoneType
        ensure_initialized()
        text = (payload.get("text") or "").strip()
        if not text:
            raise HTTPException(status_code=400, detail="text is required")

        # 1) LLM 提取目的地候选（失败回退为直接使用全文）
        try:
            candidates = qwen_service.extract_destinations(text)
        except Exception as e:
            logger.warning("extract_destinations failed, fallback to raw text: %s", e)
            candidates = [text]
        # 2) geocode：依次尝试候选，命中即停
        lng = lat = None
        chosen = None
        for cand in candidates or []:
            coords = amap_service.geocode(cand)
            if coords:
                lng, lat = coords
                chosen = cand
                break
        # 若 LLM 无候选，或均失败，尝试直接 geocode 全文
        if lng is None or lat is None:
            coords = amap_service.geocode(text)
            if coords:
                lng, lat = coords
                chosen = text

        # 3) 逆地理：补齐城市信息
        city = province = country = adcode = formatted = None
        if lng is not None and lat is not None:
            info = amap_service.regeo(lng, lat)
            if info:
                formatted = info.get("formatted_address")
                city = info.get("city")
                province = info.get("province")
                adcode = info.get("adcode")
        result: Dict[str, object] = {
            "raw_input": text,
            "candidates": candidates,
            "selected": chosen,
            "lng": lng,
            "lat": lat,
            "city": city,
            "province": province,
            "country": country,
            "adcode": adcode,
            "formatted_address": formatted,
        }
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("resolve-destination failed: %s", e)
        raise HTTPException(status_code=500, detail="resolve failed")

@app.post("/destination-weather")
async def destination_weather(payload: Dict[str, str]):
    """自由文本 → 解析坐标 → 天气预报（优先使用坐标避免城市名依赖）。

    输入: { text: string, host?: string }
    输出: { destination_context: {...}, weather: WeatherForecast }
    """
    try:
        ensure_initialized()
        text = (payload.get("text") or "").strip()
        host = (payload.get("host") or "").strip()
        if not text:
            raise HTTPException(status_code=400, detail="text is required")

        # 解析目的地上下文（复用逻辑）
        ctx = await resolve_destination({"text": text})  # type: ignore
        lng = ctx.get("lng")
        lat = ctx.get("lat")
        if lng is None or lat is None:
            # 兜底：直接返回上下文，weather 为 None
            return {"destination_context": ctx, "weather": None}

        # 使用坐标直接查询天气（QWeather 支持经纬度）
        coord_str = f"{lng},{lat}"
        forecast_raw = weather_service.forecast_3d(coord_str, host_override=(host or None))
        if not forecast_raw or not forecast_raw.get("daily"):
            # 降级为本地样例，复用现有映射逻辑
            weather = await get_weather_forecast(location=coord_str, days=3, host=host)  # type: ignore
            return {"destination_context": ctx, "weather": weather}

        # 正常映射为 WeatherForecast
        daily_raw = forecast_raw.get("daily", [])[:3]
        mapped: list[DailyForecast] = []
        for d in daily_raw:
            mapped.append(DailyForecast(
                date=d.get("fxDate"),
                text_day=d.get("textDay"),
                icon_day=d.get("iconDay"),
                temp_max_c=int(float(d.get("tempMax"))),
                temp_min_c=int(float(d.get("tempMin"))),
                precip_mm=float(d.get("precip") or 0.0),
                advice=_gen_advice(int(float(d.get("tempMax"))), float(d.get("precip") or 0.0))
            ))
        from datetime import datetime, timezone
        weather = WeatherForecast(
            location=coord_str,
            location_id=None,
            days=len(mapped),
            updated_at=datetime.now(timezone.utc).isoformat(),
            daily=mapped,
        )
        return {"destination_context": ctx, "weather": weather}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("destination-weather failed: %s", e)
        raise HTTPException(status_code=500, detail="destination-weather failed")

@app.post("/plan-from-text", response_model=TripPlan)
async def plan_from_text(payload: FreeTextPlanRequest):
    """自由文本 → 混合检索 → 生成行程"""
    try:
        trip = qwen_service.plan_from_free_text(payload.text)
        return trip
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ 自由文本生成出错: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/plan-combined", response_model=PlanWithContext)
async def plan_combined(payload: FreeTextWithOptions):
    """自由文本 → 目的地解析 → 天气预报 → 生成行程（单一入口）。

    - 优先解析坐标以确保天气查询稳定
    - 行程生产失败不影响目的地/天气返回
    - 天气失败不影响行程
    """
    try:
        ensure_initialized()
        text = (payload.text or "").strip()
        host = (payload.host or "").strip()
        if not text:
            raise HTTPException(status_code=400, detail="text is required")

        # 目的地解析
        ctx_raw = await resolve_destination({"text": text})  # type: ignore
        ctx = DestinationContext(**ctx_raw)  # type: ignore

        # 天气（若有坐标）
        weather: WeatherForecast | None = None
        if ctx.lng is not None and ctx.lat is not None:
            coord = f"{ctx.lng},{ctx.lat}"
            # 先尝试直接 forecast_3d → 若失败降级到 /weather/forecast 映射
            forecast_raw = weather_service.forecast_3d(coord, host_override=(host or None))
            if forecast_raw and forecast_raw.get("daily"):
                daily_raw = forecast_raw.get("daily", [])[:3]
                daily = []
                for d in daily_raw:
                    daily.append(DailyForecast(
                        date=d.get("fxDate"),
                        text_day=d.get("textDay"),
                        icon_day=d.get("iconDay"),
                        temp_max_c=int(float(d.get("tempMax"))),
                        temp_min_c=int(float(d.get("tempMin"))),
                        precip_mm=float(d.get("precip") or 0.0),
                        advice=_gen_advice(int(float(d.get("tempMax"))), float(d.get("precip") or 0.0))
                    ))
                from datetime import datetime, timezone
                weather = WeatherForecast(
                    location=coord,
                    location_id=None,
                    days=len(daily),
                    updated_at=datetime.now(timezone.utc).isoformat(),
                    daily=daily,
                )
            else:
                weather = await get_weather_forecast(location=coord, days=3, host=host)  # type: ignore

        # 生成行程
        try:
            trip = qwen_service.plan_from_free_text(text)
        except Exception as e:
            logger.error("plan_from_free_text failed: %s", e)
            raise HTTPException(status_code=500, detail="planning failed")

        return PlanWithContext(destination_context=ctx, weather=weather, plan=trip)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("/plan-combined failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="plan-combined failed")

@app.get("/trip-schema")
def get_trip_schema():
    """获取旅行计划的 JSON Schema"""
    logger.info("Schema 请求")
    return TripPlan.schema()

@app.post("/generate-trip-demo", response_model=TripPlan)
async def generate_trip_demo(request: TripRequest):
    """生成旅行计划演示版本（Day 1验证用）"""
    from datetime import datetime, timedelta

    logger.info(f"🎭 生成演示旅行计划: {request.destination}")

    # 演示数据 - 符合 JSON Schema 的2天北京行程
    start_date = request.start_date or "2024-03-15"
    end_date = request.start_date or "2024-03-16"

    demo_plan = {
        "destination": request.destination,
        "duration_days": request.duration_days,
        "theme": request.theme or "文化古都之旅",
        "start_date": start_date,
        "end_date": end_date,
        "daily_plans": [
            {
                "date": start_date,
                "day_title": "古都风貌探索",
                "activities": [
                    {
                        "name": "故宫博物院",
                        "type": "sightseeing",
                        "location": "北京市东城区景山前街4号",
                        "start_time": "09:00",
                        "end_time": "12:00",
                        "duration_minutes": 180,
                        "description": "故宫博物院，旧称紫禁城，是中国明清两代的皇家宫殿，世界上现存规模最大、保存最完整的木质结构古建筑群。故宫占地面积72万平方米，建筑面积约15万平方米，有大小宫殿七十多座，房屋九千余间。故宫博物院收藏了大量珍贵文物，是中国最大的古代文化艺术博物馆。",
                        "estimated_cost": 60,
                        "tips": "建议提前网上预约，避开节假日高峰"
                    },
                    {
                        "name": "天安门广场",
                        "type": "sightseeing",
                        "location": "北京市东城区天安门广场",
                        "start_time": "14:00",
                        "end_time": "16:00",
                        "duration_minutes": 120,
                        "description": "天安门广场是世界上最大的城市广场之一，面积约44万平方米。广场中央矗立着人民英雄纪念碑，南侧是毛主席纪念堂，北侧是天安门城楼，东侧是中国国家博物馆，西侧是人民大会堂。这里是北京的地标性建筑，也是重要的政治和文化中心。",
                        "estimated_cost": 0,
                        "tips": "广场安检严格，请携带身份证"
                    }
                ],
                "daily_summary": "上午游览故宫博物院，感受明清皇家建筑的宏伟壮观；下午参观天安门广场，体验北京的地标性建筑。",
                "estimated_daily_cost": 60
            },
            {
                "date": end_date,
                "day_title": "园林文化体验",
                "activities": [
                    {
                        "name": "颐和园",
                        "type": "sightseeing",
                        "location": "北京市海淀区新建宫门路19号",
                        "start_time": "09:00",
                        "end_time": "12:00",
                        "duration_minutes": 180,
                        "description": "颐和园是清代皇家园林，被誉为'皇家园林博物馆'。园内以昆明湖和万寿山为基址，以杭州西湖为蓝本，汲取江南园林的设计手法而建成的一座大型山水园林。园内建筑精美，景色优美，是中国古典园林的代表作。",
                        "estimated_cost": 30,
                        "tips": "建议从东宫门进入，可以租船游湖"
                    },
                    {
                        "name": "什刹海",
                        "type": "sightseeing",
                        "location": "北京市西城区什刹海地区",
                        "start_time": "14:00",
                        "end_time": "17:00",
                        "duration_minutes": 180,
                        "description": "什刹海是北京城内最大的历史文化保护区，由前海、后海和西海三个湖泊组成。这里保存着大量传统胡同和四合院，是体验老北京风情的最佳去处。夏季可以划船，冬季可以滑冰，四季都有不同的美景。",
                        "estimated_cost": 0,
                        "tips": "可以体验胡同游，感受老北京生活"
                    }
                ],
                "daily_summary": "上午游览颐和园，欣赏皇家园林的精致美景；下午漫步什刹海，体验老北京的传统风情。",
                "estimated_daily_cost": 30
            }
        ],
        "total_estimated_cost": 90,
        "general_tips": [
            "北京春季天气多变，建议携带外套",
            "景点门票建议提前网上预订",
            "地铁是北京最便捷的交通工具",
            "注意保管好随身物品，特别是在人流密集的景点"
        ]
    }

    return TripPlan(**demo_plan) 

@app.get("/embedding-status")
async def get_embedding_status():
    """获取嵌入服务状态"""
    logger.info("🔍 检查嵌入服务状态")
    
    try:
        from .services.embedding_service import EmbeddingService
        embedding_service = EmbeddingService()
        
        # 检查API Key
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            return {
                "status": "error",
                "message": "DASHSCOPE_API_KEY 未设置",
                "embedding_service": "Qwen Embedding API",
                "api_key_configured": False
            }
        
        # 测试连接
        if embedding_service.test_connection():
            dimension = embedding_service.get_embedding_dimension()
            return {
                "status": "available",
                "message": "Qwen Embedding API 连接正常",
                "embedding_service": "Qwen Embedding API",
                "api_key_configured": True,
                "embedding_dimension": dimension
            }
        else:
            return {
                "status": "unavailable",
                "message": "Qwen Embedding API 连接失败",
                "embedding_service": "Qwen Embedding API",
                "api_key_configured": True
            }
            
    except Exception as e:
        logger.error(f"❌ 检查嵌入服务状态失败: {e}")
        return {
            "status": "error",
            "message": f"检查嵌入服务状态失败: {e}",
            "embedding_service": "Qwen Embedding API"
        } 

@app.get("/amap-status")
async def get_amap_status():
    """检查高德 API 连接与 Key 状态"""
    logger.info("🛰️ 检查高德 API 状态")
    try:
        result = amap_service.test_connection()
        return result
    except Exception as e:
        logger.error(f"❌ 高德 API 检查失败: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/weather-status")
async def weather_status(location: str = "Beijing", host: str = ""):
    """检查和风天气 API 连接与 Key 状态"""
    logger.info("🌤️ 检查和风天气 API 状态")
    try:
        result = weather_service.test_connection(location=location, host_override=(host or None))
        return result
    except Exception as e:
        logger.error(f"❌ 和风天气 API 检查失败: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/amap-geocode")
async def amap_geocode(address: str, city: str = "北京"):
    """地理编码测试接口"""
    logger.info(f"📍 地理编码: address={address}, city={city}")
    coords = amap_service.geocode(address, city=city)
    if not coords:
        raise HTTPException(status_code=404, detail="未找到坐标")
    lng, lat = coords
    return {"address": address, "city": city, "lng": lng, "lat": lat}

@app.get("/amap-geocode-debug")
async def amap_geocode_debug(address: str, city: str = "北京"):
    """返回高德原始响应以便调试"""
    logger.info(f"🧪 地理编码调试: address={address}, city={city}")
    return amap_service.geocode_debug(address, city=city)

@app.get("/weather-status")
async def weather_status(location: str = "Beijing"):
    """检查和风天气 API 连接与 Key 状态"""
    logger.info("🌤️ 检查和风天气 API 状态")
    try:
        result = weather_service.test_connection(location=location)
        return result
    except Exception as e:
        logger.error(f"❌ 和风天气 API 检查失败: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/weather/forecast", response_model=WeatherForecast)
async def get_weather_forecast(location: str = "Beijing", days: int = 3, host: str = ""):
    """最小可用的天气预报接口：成功则返回上游 daily，失败降级为本地假数据。

    注意：仅用于 Day5 联调验证，后续会引入 Pydantic schema 与缓存。
    """
    try:
        ensure_initialized()
        loc_id = weather_service.city_lookup(location, host_override=(host or None))
        forecast_raw = None
        if loc_id:
            forecast_raw = weather_service.forecast_3d(loc_id, host_override=(host or None))
        else:
            # 直接尝试传入位置字符串
            forecast_raw = weather_service.forecast_3d(location, host_override=(host or None))

        if forecast_raw and isinstance(forecast_raw, dict) and forecast_raw.get("daily"):
            daily_raw = forecast_raw.get("daily", [])[: max(1, min(3, days))]
            mapped: list[DailyForecast] = []
            for d in daily_raw:
                mapped.append(DailyForecast(
                    date=d.get("fxDate"),
                    text_day=d.get("textDay"),
                    icon_day=d.get("iconDay"),
                    temp_max_c=int(float(d.get("tempMax"))),
                    temp_min_c=int(float(d.get("tempMin"))),
                    precip_mm=float(d.get("precip") or 0.0),
                    advice=_gen_advice(int(float(d.get("tempMax"))), float(d.get("precip") or 0.0))
                ))
            from datetime import datetime, timezone
            return WeatherForecast(
                location=location,
                location_id=loc_id,
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
                advice=_gen_advice(tmax, p)
            ))
        return WeatherForecast(
            location=location,
            location_id=loc_id,
            days=len(mapped),
            updated_at=datetime.now(timezone.utc).isoformat(),
            daily=mapped,
        )
    except Exception as e:
        logger.error(f"❌ 获取天气预报失败: {e}")
        raise HTTPException(status_code=503, detail="weather service unavailable")

@app.get("/weather/debug")
async def weather_debug(location: str = "Beijing", host: str = ""):
    """返回上游诊断信息（不包含密钥），仅用于排查 403/404 等问题。"""
    try:
        loc_id = weather_service.city_lookup(location, host_override=(host or None))
        data = {
            "location": location,
            "location_id": loc_id,
        }
        # 尝试 forecast 与 now
        fc = weather_service.forecast_3d(loc_id or location, host_override=(host or None))
        nw = weather_service.now_weather(loc_id or location, host_override=(host or None))
        data["forecast"] = bool(fc)
        data["now"] = bool(nw)
        return data
    except Exception as e:
        logger.error(f"❌ 天气调试失败: {e}")
        return {"error": str(e)}

@app.post("/validate-trip", response_model=TripPlan)
async def validate_trip(plan: TripPlan):
    """对给定行程进行路线距离与时长标注"""
    try:
        ensure_initialized()
        logger.info("🛣️ 开始路线距离校验与标注")
        annotated = route_validator.annotate_trip(plan)
        return annotated
    except Exception as e:
        logger.error(f"❌ 路线标注失败: {e}")
        raise HTTPException(status_code=500, detail="路线标注失败")

@app.post("/plan", response_model=TripPlan)
async def plan_with_graph(request: TripRequest):
    """使用 LangGraph 编排生成可执行行程（最小骨架）。"""
    try:
        ensure_initialized()
        state = PlanState(request=request)
        final_state = graph.invoke(state)
        if not final_state or not final_state.get("plan"):
            raise HTTPException(status_code=500, detail="planning failed")
        return final_state["plan"]
    except HTTPException:
        raise
    except Exception as e:
        logger.error("/plan failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="planning failed")