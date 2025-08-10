from typing import List, Optional
from datetime import datetime, time
from pydantic import BaseModel, Field
from enum import Enum

class ActivityType(str, Enum):
    """活动类型枚举"""
    SIGHTSEEING = "sightseeing"  # 观光
    DINING = "dining"            # 用餐
    SHOPPING = "shopping"        # 购物
    ENTERTAINMENT = "entertainment"  # 娱乐
    TRANSPORTATION = "transportation"  # 交通
    ACCOMMODATION = "accommodation"    # 住宿
    CULTURE = "culture"          # 文化
    NATURE = "nature"           # 自然景观

class Activity(BaseModel):
    """单个活动模型"""
    name: str = Field(..., description="活动名称")
    type: ActivityType = Field(..., description="活动类型")
    location: str = Field(..., description="活动地点")
    start_time: str = Field(..., description="开始时间 (HH:MM)")
    end_time: str = Field(..., description="结束时间 (HH:MM)")
    duration_minutes: int = Field(..., description="活动时长（分钟）")
    description: str = Field(..., description="活动描述")
    estimated_cost: Optional[int] = Field(None, description="预估费用（元）")
    tips: Optional[str] = Field(None, description="小贴士")
    # 新增（可选）：与上一个活动之间的距离与驾车时长
    distance_km_from_prev: Optional[float] = Field(None, description="与上一个活动之间的驾车距离（公里）")
    drive_time_min_from_prev: Optional[int] = Field(None, description="与上一个活动之间的驾车时长（分钟）")

class DayPlan(BaseModel):
    """单日行程模型"""
    date: str = Field(..., description="日期 (YYYY-MM-DD)")
    day_title: str = Field(..., description="当日主题")
    activities: List[Activity] = Field(..., description="活动列表")
    daily_summary: str = Field(..., description="当日总结")
    estimated_daily_cost: int = Field(..., description="当日预估总费用（元）")

class TripPlan(BaseModel):
    """完整旅行计划模型"""
    destination: str = Field(..., description="目的地")
    duration_days: int = Field(..., description="旅行天数")
    theme: str = Field(..., description="旅行主题")
    start_date: str = Field(..., description="开始日期 (YYYY-MM-DD)")
    end_date: str = Field(..., description="结束日期 (YYYY-MM-DD)")
    daily_plans: List[DayPlan] = Field(..., description="每日行程")
    total_estimated_cost: int = Field(..., description="总预估费用（元）")
    general_tips: List[str] = Field(..., description="总体建议")
    
    class Config:
        json_schema_extra = {
            "example": {
                "destination": "北京",
                "duration_days": 2,
                "theme": "文化古都之旅",
                "start_date": "2024-03-15",
                "end_date": "2024-03-16",
                "daily_plans": [
                    {
                        "date": "2024-03-15",
                        "day_title": "古都风貌",
                        "activities": [
                            {
                                "name": "故宫博物院",
                                "type": "sightseeing",
                                "location": "北京市东城区景山前街4号",
                                "start_time": "09:00",
                                "end_time": "12:00",
                                "duration_minutes": 180,
                                "description": "参观明清两代皇宫，体验中华文明",
                                "estimated_cost": 60,
                                "tips": "建议提前网上购票，避开人流高峰"
                            }
                        ],
                        "daily_summary": "探索北京古都历史文化",
                        "estimated_daily_cost": 300
                    }
                ],
                "total_estimated_cost": 600,
                "general_tips": ["准备舒适的步行鞋", "关注天气预报"]
            }
        }

class TripRequest(BaseModel):
    """旅行计划请求模型"""
    destination: str = Field(..., description="目的地")
    duration_days: int = Field(..., ge=1, le=30, description="旅行天数（1-30天）")
    theme: Optional[str] = Field("休闲旅游", description="旅行主题")
    budget: Optional[int] = Field(None, description="预算（元）")
    interests: Optional[List[str]] = Field([], description="兴趣爱好")
    start_date: Optional[str] = Field(None, description="开始日期 (YYYY-MM-DD)") 
    include_accommodation: Optional[bool] = Field(False, description="是否包含住宿/酒店安排（默认不包含）")


class FreeTextPlanRequest(BaseModel):
    """自由文本行程请求模型"""
    text: str = Field(..., description="用户自由文本需求，例如：‘想周末在北京两天亲子游，预算1000，想去故宫和颐和园。’")