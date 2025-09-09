import json
import os
from typing import Optional
from openai import OpenAI
from ..schemas import TripRequest, TripPlan
from ..schemas import ActivityType
from ..logging_config import get_logger
from .poi_embedding_service import POIEmbeddingService
from datetime import datetime, timedelta

logger = get_logger(__name__)

class QwenService:
    def __init__(self):
        """初始化 Qwen 服务"""
        logger.info("🔧 初始化 Qwen 服务")
        self.client = None
        # 初始化POI嵌入服务
        self.poi_service = POIEmbeddingService()
        logger.info("🔧 初始化POI嵌入服务")

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

    def _normalize_trip_data(self, data: dict) -> dict:
        """规范化模型输出，避免类型不一致导致校验失败。"""
        if not isinstance(data, dict):
            return data
        # general_tips: 需要是字符串列表
        gt = data.get("general_tips")
        if gt is None:
            data["general_tips"] = []
        elif isinstance(gt, str):
            # 简单按换行/分号拆分；若无法拆分，就包一层列表
            parts = [p.strip() for p in gt.replace("；", ";").replace("\n", ";").split(";") if p.strip()]
            data["general_tips"] = parts if parts else [gt]
        elif isinstance(gt, list):
            data["general_tips"] = [str(x) for x in gt]
        else:
            data["general_tips"] = [str(gt)]

        # daily_plans.activities 内 tips 需为字符串
        for day in data.get("daily_plans", []) or []:
            # 费用字段兜底转 int
            if isinstance(day.get("estimated_daily_cost"), str) and day["estimated_daily_cost"].isdigit():
                day["estimated_daily_cost"] = int(day["estimated_daily_cost"])
            for act in day.get("activities", []) or []:
                # 仅保留原始类型字符串，用于前端展示；不进行标准化
                raw_type = str(act.get("type", "")).strip()
                act["type"] = raw_type
                tips = act.get("tips")
                if isinstance(tips, list):
                    act["tips"] = "；".join([str(x) for x in tips])
                elif tips is not None and not isinstance(tips, str):
                    act["tips"] = str(tips)
                # 费用兜底转 int
                ec = act.get("estimated_cost")
                if isinstance(ec, str) and ec.isdigit():
                    act["estimated_cost"] = int(ec)
        # 总费用兜底转 int
        tec = data.get("total_estimated_cost")
        if isinstance(tec, str) and tec.isdigit():
            data["total_estimated_cost"] = int(tec)
        return data

    def _strip_accommodation(self, trip: TripPlan, allow_accommodation: bool) -> TripPlan:
        """根据策略移除住宿类活动。"""
        if allow_accommodation:
            return trip
        for day in trip.daily_plans:
            day.activities = [
                act for act in day.activities
                if getattr(act, "type", None) != ActivityType.ACCOMMODATION
                and not (isinstance(getattr(act, "name", ""), str) and ("酒店" in act.name or "民宿" in act.name or "宾馆" in act.name))
            ]
        return trip

    def generate_trip_plan(self, request: TripRequest) -> TripPlan:
        """生成旅行计划"""
        logger.info(f"🎯 开始生成旅行计划: {request.destination}, {request.duration_days}天")

        # 使用RAG检索相关POI信息
        poi_context = self._get_poi_context(request)
        
        # 构建 prompt
        prompt = self._build_prompt(request, poi_context)
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
            # Qwen模型可能会在JSON前后加一些说明文字或markdown标记，需要提取JSON部分
            try:
                # 移除可能的markdown代码块标记
                cleaned_text = response_text.strip()
                
                # 处理markdown代码块格式 ```json ... ```
                if cleaned_text.startswith('```'):
                    # 找到第一个换行符，跳过 ```json
                    first_newline = cleaned_text.find('\n')
                    if first_newline != -1:
                        cleaned_text = cleaned_text[first_newline + 1:]
                    
                    # 移除结尾的 ```
                    if cleaned_text.endswith('```'):
                        cleaned_text = cleaned_text[:-3].strip()
                
                # 查找JSON开始和结束位置
                start_idx = cleaned_text.find('{')
                end_idx = cleaned_text.rfind('}') + 1

                if start_idx != -1 and end_idx > start_idx:
                    json_text = cleaned_text[start_idx:end_idx]
                    logger.debug(f"提取的 JSON 文本: {json_text[:100]}...")
                    trip_data = json.loads(json_text)
                else:
                    # 如果没找到JSON结构，尝试直接解析原文本
                    logger.warning("⚠️ 未找到JSON结构，尝试直接解析原文本")
                    trip_data = json.loads(cleaned_text)

            except json.JSONDecodeError as e:
                # 如果JSON解析失败，记录详细错误信息
                logger.warning("⚠️ JSON解析失败，错误: %s", str(e))
                logger.debug("⚠️ 尝试解析的文本: %s", cleaned_text[:500])
                # 最后尝试解析原始响应文本
                trip_data = json.loads(response_text)

            logger.info("✅ JSON 解析成功")
            # 注入“人话”的规划思路：让模型补一句不含技术术语的 rationale
            try:
                rationale_prompt = (
                    "用中文简短说明这份行程的规划思路，避免技术术语，更像旅行顾问给用户的说明。"
                    "要求50-80字，突出这些景点好玩点、风格与节奏、为什么这样排序和取舍。只返回一句话。"
                )
                rationale_resp = self._get_client().chat.completions.create(
                    model="qwen-plus",
                    messages=[
                        {"role": "system", "content": "你是旅行顾问"},
                        {"role": "user", "content": rationale_prompt + "\n\n以下是本次行程JSON：\n" + json.dumps(trip_data, ensure_ascii=False)[:6000]},
                    ],
                    temperature=0.6,
                    max_tokens=120,
                )
                plan_rationale = rationale_resp.choices[0].message.content.strip()
                if plan_rationale:
                    trip_data["plan_rationale"] = plan_rationale
            except Exception as _:
                pass

            trip_plan = TripPlan(**self._normalize_trip_data(trip_data))
            # 若请求未显式包含住宿，则剔除住宿活动
            allow = bool(getattr(request, "include_accommodation", False))
            trip_plan = self._strip_accommodation(trip_plan, allow_accommodation=allow)

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

    # ============ 自由文本支持（方案三：混合检索） ============
    def extract_request_from_free_text(self, text: str) -> TripRequest:
        """使用 LLM 从自由文本中抽取 TripRequest 关键字段。"""
        try:
            prompt = (
                "请从用户的自由文本旅行需求中严格提取以下 JSON 字段，不要增加多余内容：\n"
                "{\n"
                "  \"destination\": \"城市名（必填）\",\n"
                "  \"duration_days\": 2,\n"
                "  \"theme\": \"主题（可选，无则用\\\"休闲旅游\\\"）\",\n"
                "  \"budget\": 1000,\n"
                "  \"interests\": [\"兴趣关键字1\", \"兴趣关键字2\"],\n"
                "  \"start_date\": \"YYYY-MM-DD 或 null\"\n"
                "}\n\n"
                f"用户输入：{text}\n"
                "只输出 JSON。"
            )
            response = self._get_client().chat.completions.create(
                model="qwen-plus",
                messages=[
                    {"role": "system", "content": "你是一个提取器，只输出严格 JSON。"},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=400,
            )
            content = response.choices[0].message.content
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            data = json.loads(content[start_idx:end_idx])
            # 默认值兜底
            if not data.get("theme"):
                data["theme"] = "休闲旅游"
            return TripRequest(**data)
        except Exception as e:
            logger.warning(f"自由文本抽取失败，回退最小请求: {e}")
            # 极端回退：仅猜测目的地为北京、2天
            return TripRequest(destination="北京", duration_days=2, theme="休闲旅游")

    def mixed_retrieve_pois(self, request: TripRequest, free_text: str, n_results: int = 10) -> str:
        """混合检索：城市/类型过滤 + 语义检索 + 关键词加权，返回拼接上下文。"""
        # 语义检索查询语句
        semantic_query = f"{request.destination}{request.theme or ''}{' '.join(request.interests or [])} {free_text}"
        results = self.poi_service.search_pois_by_query(semantic_query, n_results)

        # 关键词加权（简单版）：目的地/必提景点命中加分
        keyword_terms = [request.destination] + (request.interests or [])
        def score(result):
            base = 1 - result.get('distance', 0)
            meta = result.get('poi_info') or result.get('metadata') or {}
            name = (meta.get('name') or '').lower()
            tags = (meta.get('tags') or '').lower()
            bonus = sum(0.05 for t in keyword_terms if t and (t.lower() in name or t.lower() in tags))
            return base + bonus

        results = sorted(results, key=score, reverse=True)[:n_results]

        # 过滤城市：仅保留地址或名称包含目的地的结果
        filtered = []
        dest = request.destination or ""
        for r in results:
            meta = r.get('poi_info') or r.get('metadata') or {}
            addr = str(meta.get('address') or '')
            name = str(meta.get('name') or '')
            if not dest or dest in addr or dest in name:
                filtered.append(r)

        if not filtered:
            logger.info("ℹ️ mixed_retrieve_pois: 目的地=%s 越界过滤后无POI，跳过RAG上下文", dest)
            return ""

        # 拼接上下文
        parts = []
        for r in filtered:
            meta = r.get('poi_info') or r.get('metadata') or {}
            parts.append(
                f"景点名称: {meta.get('name')}\n类型: {meta.get('type')}\n地址: {meta.get('address')}\n门票: {meta.get('ticket_price')}元\n营业时间: {meta.get('business_hours')}\n标签: {meta.get('tags')}\n——"
            )
        return "\n".join(parts)

    def plan_from_free_text(self, text: str) -> TripPlan:
        """自由文本 → 抽取 TripRequest → 混合检索 POI → 调用主流程生成计划。"""
        request = self.extract_request_from_free_text(text)
        poi_context = self.mixed_retrieve_pois(request, text, n_results=10)
        prompt = self._build_prompt(request, poi_context)
        # 复用主流程生成
        try:
            response = self._get_client().chat.completions.create(
                model="qwen-plus",
                messages=[
                    {"role": "system", "content": "你是一位专业的旅行规划师，只返回 JSON。"},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=4000,
            )
            content = response.choices[0].message.content
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            data = json.loads(content[start_idx:end_idx])
            # 同样为自由文本接口补充“人话”的规划思路
            try:
                rationale_prompt = (
                    "用中文简短说明这份行程的规划思路，避免技术术语，更像旅行顾问给用户的说明。"
                    "要求50-80字，突出这些景点好玩点、风格与节奏、为什么这样排序和取舍。只返回一句话。"
                )
                rationale_resp = self._get_client().chat.completions.create(
                    model="qwen-plus",
                    messages=[
                        {"role": "system", "content": "你是旅行顾问"},
                        {"role": "user", "content": rationale_prompt + "\n\n以下是本次行程JSON：\n" + json.dumps(data, ensure_ascii=False)[:6000]},
                    ],
                    temperature=0.6,
                    max_tokens=120,
                )
                plan_rationale = rationale_resp.choices[0].message.content.strip()
                if plan_rationale:
                    data["plan_rationale"] = plan_rationale
            except Exception:
                pass

            trip = TripPlan(**self._normalize_trip_data(data))
            # 自由文本：若文本包含住宿关键词，保留住宿，否则剔除
            keywords = ["住宿", "酒店", "民宿", "宾馆", "hotel"]
            allow_accommodation = any(k in (text or "").lower() for k in keywords)
            trip = self._strip_accommodation(trip, allow_accommodation)
            return trip
        except Exception as e:
            logger.error(f"❌ 自由文本生成失败: {e}")
            raise ValueError(f"自由文本生成失败: {e}")

    def extract_destinations(self, text: str) -> list[str]:
        """使用LLM从自由文本抽取目的地短语（中文或英文地名、行政区、国家）。

        返回按相关性排序的最多5个候选，全部为去重后的短语。
        """
        try:
            prompt = (
                "从下面自由文本中抽取最多5个目的地短语，可以是城市/行政区/国家/景区名，按相关性排序，去重；只返回JSON数组，如：[\"北京\", \"首尔\"]。\n\n"
                f"文本：{text}"
            )
            resp = self._get_client().chat.completions.create(
                model="qwen-plus",
                messages=[
                    {"role": "system", "content": "你是信息抽取助手，只返回严格的JSON数组，不含其他文字。"},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=200,
            )
            content = resp.choices[0].message.content.strip()
            start = content.find('[')
            end = content.rfind(']') + 1
            arr = json.loads(content[start:end])
            phrases = []
            seen = set()
            for item in arr:
                s = str(item).strip()
                if not s or s in seen:
                    continue
                seen.add(s)
                phrases.append(s)
            return phrases[:5]
        except Exception as e:
            logger.warning("extract_destinations 失败，返回空列表: %s", e)
            return []

    def _get_poi_context(self, request: TripRequest) -> str:
        """获取相关POI上下文信息（按目的地过滤）。"""
        try:
            dest = request.destination or "北京"
            query = f"{dest}{request.theme or '旅游'}景点"
            poi_results = self.poi_service.search_pois_by_query(query, n_results=10)
            if not poi_results:
                logger.warning("⚠️ 未找到相关POI信息")
                return ""
            # 目的地越界过滤
            filtered = []
            for r in poi_results:
                meta = r.get('poi_info') or r.get('metadata') or {}
                addr = str(meta.get('address') or '')
                name = str(meta.get('name') or '')
                if dest in addr or dest in name:
                    filtered.append(r)
            if not filtered:
                logger.info("ℹ️ 目的地=%s 越界过滤后无POI，跳过RAG上下文", dest)
                return ""
            context_parts = []
            for result in filtered:
                poi_info = result['poi_info']
                context_parts.append(f"""
景点名称: {poi_info['name']}
类型: {poi_info['type']}
地址: {poi_info['address']}
评分: {poi_info['rating']}
门票: {poi_info['ticket_price']}元
营业时间: {poi_info['business_hours']}
标签: {', '.join(poi_info['tags'])}
详细介绍: {result['description']}
相似度: {result['similarity_score']:.2f}
---""")
            context = "\n".join(context_parts)
            logger.info(f"📚 获取到 {len(filtered)} 个相关POI信息（目的地={dest}）")
            return context
        except Exception as e:
            logger.error(f"❌ 获取POI上下文失败: {e}")
            return ""

    def _build_prompt(self, request: TripRequest, poi_context: str = "") -> str:
        """构建 Qwen prompt"""
        logger.debug("📝 构建 prompt")

        # Add date calculation and constraints
        try:
            start_date = datetime.strptime(request.start_date, "%Y-%m-%d")
            end_date = (start_date + timedelta(days=request.duration_days - 1)).strftime("%Y-%m-%d")
            date_constraint = f"""
【重要：日期强制规则】
✅ 旅行开始日期：{request.start_date}（用户指定）
✅ 旅行结束日期：{end_date}（自动计算）
✅ 每日计划的date字段必须严格按顺序：{request.start_date} → {end_date}
❌ 禁止使用其他日期（如2023-10-15等示例日期）
❌ 违反此规则将导致整个行程计划无效

            """
        except Exception as e:
            logger.error(f"日期解析错误: {e}")
            date_constraint = "# 日期格式错误，请使用 YYYY-MM-DD 格式"

        # 基础信息
        prompt = f"""{date_constraint}

请为我生成一个详细的{request.destination}旅行计划。

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

# 日期信息已在上方日期约束中包含，移除重复

        # 添加POI上下文信息
        if poi_context:
            prompt += f"""
相关景点信息参考：
{poi_context}

请基于以上景点信息来规划行程，确保推荐的景点真实存在且信息准确。
"""

        # JSON Schema 要求（并禁止虚构住宿）
        prompt += f"""
请返回严格符合以下JSON Schema的旅行计划：

{{
  "destination": "目的地名称",
  "duration_days": {request.duration_days},
  "theme": "旅行主题",
  "start_date": "开始日期 (YYYY-MM-DD，必须使用上述指定的开始日期)",
  "end_date": "结束日期 (YYYY-MM-DD，必须使用上述计算的结束日期)",
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
          "tips": "实用小贴士（必须是单个字符串，不能是数组）"
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
7. 优先使用提供的景点信息
8. 只返回JSON，不要任何其他文字说明
9. tips字段必须是字符串，不能是数组
 10. 确保所有字段类型正确
 11. 不要包含任何住宿/酒店安排，也不要输出具体酒店名称或 accommodation 类型的活动，除非用户在输入中明确提出住宿需求或指定酒店。

请严格按照上述JSON格式返回旅行计划："""

        logger.debug(f"构建的 prompt 长度: {len(prompt)} 字符")
        return prompt 
