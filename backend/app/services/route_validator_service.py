from typing import Dict, Optional, Tuple, List

from ..schemas import TripPlan
from .amap_service import AmapService
from ..logging_config import get_logger
from .poi_embedding_service import POIEmbeddingService

logger = get_logger(__name__)


class RouteValidatorService:
    """
    Annotates a TripPlan with driving distance and duration between consecutive activities per day.
    Keeps architecture simple: no persistence, just AmapService + minimal in-memory cache.
    """

    def __init__(self, amap_service: Optional[AmapService] = None):
        self.amap = amap_service or AmapService()
        self._geocode_cache: Dict[str, Tuple[float, float]] = {}
        self.poi_service = POIEmbeddingService()
        # 添加POI营业时间缓存，避免重复查询
        self._poi_hours_cache: Dict[str, Optional[str]] = {}

    def _get_coords(self, address: str, city_hint: Optional[str] = None) -> Optional[Tuple[float, float]]:
        if address in self._geocode_cache:
            return self._geocode_cache[address]
        coords = self.amap.geocode(address, city=city_hint or "北京")
        if coords:
            self._geocode_cache[address] = coords
        return coords

    def annotate_trip(self, trip: TripPlan) -> TripPlan:
        city_hint = trip.destination or "北京"
        for day in trip.daily_plans:
            prev_coords: Optional[Tuple[float, float]] = None
            for idx, act in enumerate(day.activities):
                # Reset fields to ensure idempotency
                act.distance_km_from_prev = None
                act.drive_time_min_from_prev = None
                # reset open fields
                act.open_ok = None
                act.open_hours_raw = None
                act.closed_reason = None
                act.replaced_from = None

                coords = self._get_coords(act.location, city_hint)
                if idx == 0:
                    prev_coords = coords
                    continue

                if not prev_coords or not coords:
                    prev_coords = coords
                    continue

                drive = self.amap.driving_distance(prev_coords, coords)
                if drive:
                    distance_m, duration_s = drive
                    act.distance_km_from_prev = round(distance_m / 1000.0, 2)
                    act.drive_time_min_from_prev = int(round(duration_s / 60.0))
                prev_coords = coords
        # After distance annotations, run open-hours validation and replacement
        self._annotate_open_hours_and_replace(trip)
        return trip

    def _parse_time(self, hhmm: str) -> Optional[Tuple[int, int]]:
        try:
            h, m = hhmm.split(":")
            return int(h), int(m)
        except Exception:
            return None

    def _activity_time_window(self, date_str: str, start: str, end: str) -> Optional[Tuple[int, int]]:
        """Return minutes since midnight window for activity."""
        s = self._parse_time(start)
        e = self._parse_time(end)
        if not s or not e:
            return None
        return s[0] * 60 + s[1], e[0] * 60 + e[1]

    def _parse_open_hours(self, raw: str) -> List[Tuple[int, int]]:
        """Very lightweight parser: supports 'HH:MM-HH:MM' joined by ';' or '、' or '/'. Cross-day treated as open until 24:00.
        返回分钟窗口列表。
        """
        windows: List[Tuple[int, int]] = []
        if not raw:
            return windows
        parts = [p.strip() for p in raw.replace("、", ";").replace("/", ";").split(";") if p.strip()]
        for p in parts:
            if "-" not in p:
                continue
            a, b = [q.strip() for q in p.split("-", 1)]
            ts = self._parse_time(a)
            te = self._parse_time(b)
            if not ts or not te:
                continue
            start_min = ts[0] * 60 + ts[1]
            end_min = te[0] * 60 + te[1]
            if end_min < start_min:
                # Cross-day: cap to midnight for simplicity
                end_min = 24 * 60
            windows.append((start_min, end_min))
        return windows

    def _is_open(self, act_window: Tuple[int, int], open_windows: List[Tuple[int, int]]) -> Optional[bool]:
        if not open_windows:
            return None
        a_start, a_end = act_window
        for w_start, w_end in open_windows:
            # require full coverage
            if a_start >= w_start and a_end <= w_end:
                return True
        return False

    def _annotate_open_hours_and_replace(self, trip: TripPlan) -> None:
        city = trip.destination or "北京"
        for day in trip.daily_plans:
            for idx, act in enumerate(day.activities):
                # 获取营业时间
                hours = self.amap.get_poi_open_hours(act.name or act.location, city)
                if not hours:
                    hours = self._fallback_business_hours_from_catalog(act.name)
                act.open_hours_raw = hours

                # 判定开门
                act_window = self._activity_time_window(day.date, act.start_time, act.end_time)
                if not act_window:
                    act.open_ok = None
                    act.closed_reason = "unknown_hours"
                    logger.info("open-hours: time parse failed for activity %s", act.name)
                    continue

                open_windows = self._parse_open_hours(hours) if hours else []
                open_ok = self._is_open(act_window, open_windows)
                act.open_ok = open_ok
                if open_ok is not True:
                    # 记录解释信息
                    plan_range = f"{act.start_time}-{act.end_time}"
                    hours_str = hours or "(unknown)"
                    act.open_hours_explain = f"planned {plan_range}, open {hours_str}"
                if open_ok is True:
                    logger.debug("open-hours: activity open %s", act.name)
                    continue
                if open_ok is None:
                    act.closed_reason = "missing_hours"
                    logger.info("open-hours: missing for %s", act.name)
                    continue

                # 需要替换
                logger.info("open-hours: closed detected, try replace %s", act.name)
                replaced = self._try_replace_activity(trip, day, idx)
                if replaced:
                    logger.info("replaced %s -> %s", act.replaced_from, act.name)
                else:
                    act.closed_reason = "closed"
                    logger.info("replacement failed for %s", act.name)

    def _fallback_business_hours_from_catalog(self, name: str) -> Optional[str]:
        # 使用缓存避免重复查询
        if name in self._poi_hours_cache:
            return self._poi_hours_cache[name]
            
        try:
            pois = self.poi_service.load_poi_data()  # 现在已经有缓存了
            result = None
            for poi in pois:
                if poi.get("name") == name and poi.get("business_hours"):
                    result = str(poi.get("business_hours"))
                    break
            
            # 缓存结果（包括None）
            self._poi_hours_cache[name] = result
            return result
        except Exception:
            self._poi_hours_cache[name] = None
            return None

    def _try_replace_activity(self, trip: TripPlan, day, idx: int) -> bool:
        act = day.activities[idx]
        query = f"{act.name} {act.type} {trip.destination}"
        candidates = self.poi_service.search_pois_by_query(query, n_results=6)
        if not candidates:
            return False

        # 基于通勤与相似度筛选
        def score_candidate(c) -> float:
            sim = float(c.get("similarity_score") or 0.0)
            poi = c.get("poi_info", {})
            addr = poi.get("address") or poi.get("name")
            # 通勤惩罚（相对原活动）
            commute_penalty = 0.0
            try:
                # 计算与上一点和下一点的变化（粗略）：如果有前后点
                before = day.activities[idx - 1] if idx > 0 else None
                after = day.activities[idx + 1] if idx + 1 < len(day.activities) else None
                penalty = 0.0
                if before:
                    bc = self._get_coords(before.location, trip.destination)
                    rc = self._get_coords(addr, trip.destination)
                    if bc and rc:
                        d = self.amap.driving_distance(bc, rc)
                        if d:
                            penalty += (d[1] / 60.0)
                if after:
                    ac = self._get_coords(after.location, trip.destination)
                    rc = self._get_coords(addr, trip.destination)
                    if ac and rc:
                        d = self.amap.driving_distance(rc, ac)
                        if d:
                            penalty += (d[1] / 60.0)
                commute_penalty = penalty
            except Exception:
                commute_penalty = 30.0
            return sim - 0.01 * commute_penalty

        # 预先计算候选评分与通勤差
        scored: List[dict] = []
        for c in candidates:
            sim = float(c.get("similarity_score") or 0.0)
            poi = c.get("poi_info", {})
            addr = poi.get("address") or poi.get("name")
            commute_penalty = 0.0
            try:
                before = day.activities[idx - 1] if idx > 0 else None
                after = day.activities[idx + 1] if idx + 1 < len(day.activities) else None
                penalty = 0.0
                if before:
                    bc = self._get_coords(before.location, trip.destination)
                    rc = self._get_coords(addr, trip.destination)
                    if bc and rc:
                        d = self.amap.driving_distance(bc, rc)
                        if d:
                            penalty += (d[1] / 60.0)
                if after:
                    ac = self._get_coords(after.location, trip.destination)
                    rc = self._get_coords(addr, trip.destination)
                    if ac and rc:
                        d = self.amap.driving_distance(rc, ac)
                        if d:
                            penalty += (d[1] / 60.0)
                commute_penalty = penalty
            except Exception:
                commute_penalty = 30.0
            score = sim - 0.01 * commute_penalty
            scored.append({
                "raw": c,
                "sim": sim,
                "score": score,
                "commute_delta": commute_penalty,
            })

        sorted_cands = sorted(scored, key=lambda x: x["score"], reverse=True)
        # 组装前端可视提示的候选列表（最多 5 个），包含简短简介 summary
        shortlist: List[dict] = []

        for item in sorted_cands:
            cand = item["raw"]
            sim_val = item["sim"]
            poi = cand.get("poi_info", {})
            new_name = poi.get("name")
            new_addr = poi.get("address") or new_name
            hours = self.amap.get_poi_open_hours(new_name or new_addr, trip.destination)
            if not hours:
                hours = str(poi.get("business_hours") or "")
            open_windows = self._parse_open_hours(hours) if hours else []
            act_window = self._activity_time_window(day.date, act.start_time, act.end_time)
            if not act_window:
                continue
            open_ok = self._is_open(act_window, open_windows)
            # 收集候选概览
            if len(shortlist) < 5:
                summary = self._extract_short_description(cand)
                shortlist.append({
                    "name": new_name,
                    "summary": summary,
                    "commute_delta_min": item.get("commute_delta"),
                    "open_ok": bool(open_ok) if open_ok is not None else None,
                    "open_hours_raw": hours or None,
                })
            if open_ok is True:
                # 采用此候选
                original_name = act.name
                original_hours = act.open_hours_raw
                act.name = new_name or act.name
                act.location = new_addr or act.location
                # 使用候选的简介更新描述（截取“详细介绍”部分的前160字）
                new_desc = self._extract_short_description(cand)
                if new_desc:
                    act.description = new_desc
                act.open_ok = True
                act.open_hours_raw = hours
                act.closed_reason = "replaced"
                act.replaced_from = original_name
                act.replaced_from_open_hours_raw = original_hours
                # 生成替换理由说明
                act.replacement_reason = (
                    f"closed -> replaced by similar POI (sim={sim_val:.2f}); commute +{item['commute_delta']:.0f} min"
                )
                act.replacement_commute_delta_min = float(item["commute_delta"]) if item.get("commute_delta") is not None else None
                act.replacement_candidates = [
                    {
                        "name": it["name"],
                        "similarity": float(it["similarity"]),
                        "score": float(it["score"]),
                        "commute_delta_min": float(it["commute_delta_min"]) if it.get("commute_delta_min") is not None else None,
                        "open_hours_raw": it.get("open_hours_raw"),
                        "open_ok": it.get("open_ok"),
                    }
                    for it in shortlist
                ]
                # 在 tips 末尾追加替换说明（中文提示，日志英文）
                suffix = f"已替换为 {act.name}（因闭园）"
                try:
                    act.tips = (act.tips + "；" + suffix) if act.tips else suffix
                except Exception:
                    act.tips = suffix
                return True
        return False

    def _extract_short_description(self, cand: dict) -> Optional[str]:
        try:
            raw: str = cand.get("description") or ""
            if not raw:
                return None
            # 定位“详细介绍:”之后的文本
            marker = "详细介绍:"
            idx = raw.find(marker)
            text = raw[idx + len(marker):] if idx >= 0 else raw
            # 去除多余空白
            text = " ".join(text.split())
            # 截断到160字
            if len(text) > 160:
                text = text[:160].rstrip() + "…"
            return text
        except Exception:
            return None