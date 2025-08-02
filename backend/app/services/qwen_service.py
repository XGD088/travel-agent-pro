import json
import os
from typing import Optional
from openai import OpenAI
from ..schemas import TripRequest, TripPlan
from ..logging_config import get_logger

logger = get_logger(__name__)

class QwenService:
    def __init__(self):
        """初始化 Qwen 服务"""
        logger.info("🔧 初始化 Qwen 服务")
        self.client = None

    def _get_client(self):
        """延迟初始化 Qwen 客户端"""
        if self.client is None:
            api_key = os.getenv("DASHSCOPE_API_KEY")
            logger.debug(f"获取 API Key: {'已配置' if api_key else '未配置'}")
            
            if not api_key or api_key.startswith("sk-test-"):
                logger.error("❌ 无效的 DASHSCOPE_API_KEY")
                raise ValueError("请设置有效的 DASHSCOPE_API_KEY 环境变量")
            
            logger.info("🔗 创建 Qwen 客户端连接")
            logger.info("api key: %s", api_key[:4] + "..." + api_key[-4:])  # 只打印前后4位，避免泄露完整API Key
            # 使用阿里云DashScope的OpenAI兼容接口
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
            )
            logger.debug("✅ Qwen 客户端创建成功")
        return self.client

    def generate_trip_plan(self, request: TripRequest) -> TripPlan:
        """生成旅行计划"""
        logger.info(f"🎯 开始生成旅行计划: {request.destination}, {request.duration_days}天")

        # 构建 prompt
        prompt = self._build_prompt(request)
        logger.debug(f"构建的 prompt 长度: {len(prompt)} 字符")

        try:
            logger.info("📡 调用 Qwen API...")
            
            response = self._get_client().chat.completions.create(
                model="qwen-plus",  # 使用通义千问Plus模型
                messages=[
                    {
                        "role": "system",
                        "content": "你是一位专业的旅行规划师，专门为用户创建详细的旅行计划。你必须返回严格符合JSON Schema的响应，不要添加任何额外的文字说明。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=4000,
                # 注意：Qwen模型可能不支持response_format参数，先移除
            )

            # 解析响应
            response_text = response.choices[0].message.content
            logger.info(f"📥 收到 Qwen 响应，长度: {len(response_text)} 字符")
            logger.debug(f"响应内容预览: {response_text[:200]}...")

            # 尝试从响应中提取JSON
            # Qwen模型可能会在JSON前后加一些说明文字，需要提取JSON部分
            try:
                # 查找JSON开始和结束位置
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1

                if start_idx != -1 and end_idx > start_idx:
                    json_text = response_text[start_idx:end_idx]
                    logger.debug(f"提取的 JSON 文本: {json_text[:100]}...")
                    trip_data = json.loads(json_text)
                else:
                    # 如果没找到JSON，尝试直接解析
                    logger.warning("⚠️ 未找到JSON标记，尝试直接解析")
                    trip_data = json.loads(response_text)

            except json.JSONDecodeError:
                # 如果JSON解析失败，尝试直接解析原文本
                logger.warning("⚠️ JSON解析失败，尝试解析原文本")
                trip_data = json.loads(response_text)

            logger.info("✅ JSON 解析成功")
            trip_plan = TripPlan(**trip_data)

            logger.info(f"🎉 成功生成旅行计划: {request.destination}")
            logger.debug(f"计划概要: {trip_plan.destination}, {len(trip_plan.daily_plans)}天, 总费用: {trip_plan.total_estimated_cost}元")
            return trip_plan

        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON 解析失败: {e}")
            logger.error(f"原始响应: {response_text}")
            raise ValueError(f"Qwen 返回的内容不是有效的 JSON 格式: {e}")

        except Exception as e:
            logger.error(f"❌ 生成旅行计划时出错: {e}", exc_info=True)
            raise ValueError(f"生成旅行计划时出错: {e}")

    def _build_prompt(self, request: TripRequest) -> str:
        """构建 Qwen prompt"""
        logger.debug("📝 构建 prompt")

        # 基础信息
        prompt = f"""请为我生成一个详细的{request.destination}旅行计划。

要求：
- 目的地: {request.destination}
- 旅行天数: {request.duration_days}天
- 主题: {request.theme or '休闲旅游'}
"""

        # 可选信息
        if request.budget:
            prompt += f"- 预算: {request.budget}元\n"

        if request.interests:
            prompt += f"- 兴趣爱好: {', '.join(request.interests)}\n"

        if request.start_date:
            prompt += f"- 开始日期: {request.start_date}\n"

        # JSON Schema 要求
        prompt += f"""
请返回严格符合以下JSON Schema的旅行计划：

{{
  "destination": "目的地名称",
  "duration_days": {request.duration_days},
  "theme": "旅行主题",
  "start_date": "开始日期 (YYYY-MM-DD)",
  "end_date": "结束日期 (YYYY-MM-DD)",
  "daily_plans": [
    {{
      "date": "日期 (YYYY-MM-DD)",
      "day_title": "当日主题",
      "activities": [
        {{
          "name": "活动名称",
          "type": "活动类型 (sightseeing/dining/shopping/entertainment/transportation/accommodation/culture/nature)",
          "location": "详细地址",
          "start_time": "开始时间 (HH:MM)",
          "end_time": "结束时间 (HH:MM)",
          "duration_minutes": 活动时长分钟数,
          "description": "详细描述",
          "estimated_cost": 预估费用数字,
          "tips": "实用小贴士"
        }}
      ],
      "daily_summary": "当日总结",
      "estimated_daily_cost": 当日总费用数字
    }}
  ],
  "total_estimated_cost": 总费用数字,
  "general_tips": ["建议1", "建议2", "建议3"]
}}

注意事项：
1. 确保时间安排合理，活动之间留有足够的交通时间
2. 费用估算要实际合理
3. 景点和餐厅要真实存在
4. 每天安排4-6个主要活动
5. 包含早中晚餐安排
6. 给出实用的旅行建议
7. 只返回JSON，不要任何其他文字说明

请严格按照上述JSON格式返回旅行计划："""

        logger.debug(f"构建的 prompt 长度: {len(prompt)} 字符")
        return prompt 
