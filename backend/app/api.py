from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .schemas import TripRequest, TripPlan
from .services import QwenService
import os
from dotenv import load_dotenv
from .logging_config import setup_logging, get_logger

# 加载环境变量
load_dotenv()

# 设置日志系统
setup_logging()
logger = get_logger(__name__)

app = FastAPI(
    title="Travel Agent Pro API",
    description="AI-Powered Weekend Trip Planner Backend (Powered by Qwen)",
    version="1.0.0"
)

# 添加 CORS 中间件以允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 允许前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化服务
qwen_service = QwenService()

@app.get("/health")
def health():
    """健康检查接口"""
    logger.info("Health check requested")
    return {"status": "ok"}

@app.get("/")
def root():
    """API根路径"""
    logger.info("Root endpoint accessed")
    return {"message": "Travel Agent Pro Backend API"}

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
                        "description": "参观明清两代皇宫，感受中华文明的博大精深",
                        "estimated_cost": 60,
                        "tips": "建议提前网上购票，避开人流高峰时段"
                    },
                    {
                        "name": "北京烤鸭午餐",
                        "type": "dining",
                        "location": "全聚德前门店",
                        "start_time": "12:30",
                        "end_time": "13:30",
                        "duration_minutes": 60,
                        "description": "品尝正宗北京烤鸭，体验京城美食文化",
                        "estimated_cost": 200,
                        "tips": "推荐点半只烤鸭配烙饼和蘸料"
                    },
                    {
                        "name": "天安门广场",
                        "type": "sightseeing",
                        "location": "北京市东城区东长安街",
                        "start_time": "14:00",
                        "end_time": "15:30",
                        "duration_minutes": 90,
                        "description": "参观世界最大的城市广场，感受国家的庄严与壮观",
                        "estimated_cost": 0,
                        "tips": "需要安检，不要携带危险物品"
                    },
                    {
                        "name": "景山公园",
                        "type": "sightseeing",
                        "location": "北京市西城区景山西街44号",
                        "start_time": "16:00",
                        "end_time": "17:30",
                        "duration_minutes": 90,
                        "description": "登顶俯瞰紫禁城全景，欣赏北京城市风貌",
                        "estimated_cost": 10,
                        "tips": "黄昏时分景色最美，适合拍照"
                    }
                ],
                "daily_summary": "第一天探索北京古都核心区域，感受历史文化底蕴",
                "estimated_daily_cost": 270
            },
            {
                "date": end_date,
                "day_title": "现代北京体验",
                "activities": [
                    {
                        "name": "天坛公园",
                        "type": "sightseeing",
                        "location": "北京市东城区天坛路甲1号",
                        "start_time": "09:00",
                        "end_time": "11:00",
                        "duration_minutes": 120,
                        "description": "参观明清皇帝祭天的神圣场所，欣赏古代建筑艺术",
                        "estimated_cost": 35,
                        "tips": "早晨游览可以看到市民晨练，体验老北京生活"
                    },
                    {
                        "name": "王府井大街",
                        "type": "shopping",
                        "location": "北京市东城区王府井大街",
                        "start_time": "11:30",
                        "end_time": "14:00",
                        "duration_minutes": 150,
                        "description": "逛北京最著名的商业街，购买特色纪念品",
                        "estimated_cost": 300,
                        "tips": "可以品尝王府井小吃街的各种传统小食"
                    },
                    {
                        "name": "什刹海",
                        "type": "culture",
                        "location": "北京市西城区什刹海",
                        "start_time": "15:00",
                        "end_time": "17:00",
                        "duration_minutes": 120,
                        "description": "漫步历史街区，感受老北京胡同文化",
                        "estimated_cost": 50,
                        "tips": "可以租自行车环湖骑行，体验不同视角"
                    }
                ],
                "daily_summary": "第二天体验现代北京与传统文化的完美融合",
                "estimated_daily_cost": 385
            }
        ],
        "total_estimated_cost": 655,
        "general_tips": [
            "准备舒适的步行鞋，景点间需要较多步行",
            "关注天气预报，携带雨具或防晒用品",
            "提前了解景点开放时间，合理规划行程",
            "保持手机电量充足，使用地图导航",
            "尊重当地文化和习俗，文明旅游"
        ]
    }

    # 使用 Pydantic 验证数据结构
    trip_plan = TripPlan(**demo_plan)

    logger.info(f"✅ 成功生成演示旅行计划: {request.destination}")
    return trip_plan 