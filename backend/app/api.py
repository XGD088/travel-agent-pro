from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .schemas import TripRequest, TripPlan
from .services import QwenService
from .services.poi_embedding_service import POIEmbeddingService
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
    description="AI-Powered Weekend Trip Planner Backend (Powered by Qwen + RAG)",
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
poi_service = POIEmbeddingService()

@app.get("/health")
def health():
    """健康检查接口"""
    logger.info("Health check requested")
    return {"status": "ok"}

@app.get("/")
def root():
    """API根路径"""
    return {"message": "Travel Agent Pro Backend API"}

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