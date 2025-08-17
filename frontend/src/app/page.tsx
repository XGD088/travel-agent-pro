'use client'

import React, { useState } from 'react'
import { TooltipProvider, Tooltip, TooltipTrigger, TooltipContent } from '@/components/ui/tooltip'
import WeatherCard from '@/components/WeatherCard'

interface TripPlan {
  destination: string
  duration_days: number
  theme: string
  start_date: string
  end_date: string
  daily_plans: Array<{
    date: string
    day_title: string
    activities: Array<{
      name: string
      type: string
      category?: string
      location: string
      start_time: string
      end_time: string
      duration_minutes: number
      description: string
      estimated_cost: number | null
      tips: string | null
      // Day 3 fields (optional)
      distance_km_from_prev?: number | null
      drive_time_min_from_prev?: number | null
      // Day 4 fields (optional)
      open_ok?: boolean | null
      open_hours_raw?: string | null
      closed_reason?: string | null
      replaced_from?: string | null
      open_hours_explain?: string | null
      replaced_from_open_hours_raw?: string | null
      replacement_reason?: string | null
      replacement_commute_delta_min?: number | null
      replacement_candidates?: Array<{
        name: string
        summary?: string | null
        commute_delta_min?: number | null
        open_hours_raw?: string | null
        open_ok?: boolean | null
      }> | null
    }>
    daily_summary: string
    estimated_daily_cost: number
  }>
  total_estimated_cost: number
  general_tips: string[]
  // 追加：规划思路（来自后端简单生成或前端拼装）
  plan_rationale?: string
}
// 将技术性理由转为用户可读文案
function readableReason(activity: any): string {
  if (activity.closed_reason === 'replaced') {
    const commute = activity.replacement_commute_delta_min
    const sim = activity.replacement_candidates?.[0]?.similarity
    const parts: string[] = []
    parts.push('原计划该时段不营业，已为你换成相似体验的备选')
    if (sim != null) parts.push(`相似度约 ${Number(sim).toFixed(2)}`)
    if (commute != null) parts.push(`通勤变化约 ${Math.round(commute)} 分钟`)
    return parts.join('；')
  }
  if (activity.open_ok === false) {
    return '该时段可能不营业或需到店确认，你可以考虑调整时间或更换景点'
  }
  return '基于营业时间与路程做了适配'
}

export default function Home() {
  const [isLoading, setIsLoading] = useState(false)
  const [tripPlan, setTripPlan] = useState<TripPlan | null>(null)
  const [poiStats, setPoiStats] = useState<any>(null)
  const [embeddingStatus, setEmbeddingStatus] = useState<any>(null)
  const [startDate, setStartDate] = useState<string>(
    () => new Date().toISOString().slice(0, 10)
  )
  const [freeText, setFreeText] = useState<string>("")
  const [destCtx, setDestCtx] = useState<any>(null)
  const [weatherKey, setWeatherKey] = useState<{ location: string, host?: string } | null>(null)

  const generateTrip = async () => {
    setIsLoading(true)
    try {
      // 使用自由文本接口：将选择的开始日期一并追加，提升解析准确度
      const composed = freeText
        ? `${freeText}\n开始日期: ${startDate}`
        : `在北京${startDate}开始的2天旅行计划`

      // 使用新的 LangGraph 编排端点
      const response = await fetch('http://localhost:8000/plan', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          destination: "北京", 
          duration_days: 2, 
          theme: "亲子",
          start_date: startDate,
          interests: ["公园", "文化"]
        })
      })
      
      if (response.ok) {
        const data = await response.json()
        // LangGraph 端点直接返回 TripPlan，无需额外校验
        setTripPlan(data)
      } else {
        const errorData = await response.json().catch(() => ({}))
        alert(`生成旅行计划失败: ${errorData.detail || '未知错误'}`)
      }
    } catch (error) {
      console.error('Error generating trip plan:', error)
      alert('生成旅行计划时发生错误，请检查网络连接')
    } finally {
      setIsLoading(false)
    }
  }

  const getPoiStats = async () => {
    try {
      const response = await fetch('http://localhost:8000/poi-stats')
      if (response.ok) {
        const data = await response.json()
        setPoiStats(data)
      }
    } catch (error) {
      console.error('Error getting POI stats:', error)
    }
  }

  const getEmbeddingStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/embedding-status')
      if (response.ok) {
        const data = await response.json()
        setEmbeddingStatus(data)
      }
    } catch (error) {
      console.error('Error getting embedding status:', error)
    }
  }

  const resolveDestinationAndWeather = async () => {
    try {
      const resp = await fetch('http://localhost:8000/resolve-destination', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: freeText || '北京' })
      })
      if (!resp.ok) throw new Error('resolve failed')
      const ctx = await resp.json()
      setDestCtx(ctx)
      if (ctx?.lng != null && ctx?.lat != null) {
        setWeatherKey({ location: `${ctx.lng},${ctx.lat}`, host: 'ka4d92udc6.re.qweatherapi.com' })
      } else {
        alert('未能解析出坐标，请尝试更明确的目的地描述')
      }
    } catch (e) {
      console.error(e)
      alert('目的地解析失败')
    }
  }

  return (
    <main className="container mx-auto px-4 py-8">
      {weatherKey ? (
        <WeatherCard location={weatherKey.location} host={weatherKey.host} />
      ) : (
        <div className="max-w-4xl mx-auto mb-4 rounded border bg-white p-3 text-sm text-gray-600">
          提示：填写下方自由文本后点“解析目的地并取天气”，会使用坐标查询天气，更稳健。
        </div>
      )}
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          🏃🏻 Travel Agent Pro
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          AI-Powered Weekend Trip Planner (Beijing ver.)
        </p>
        
        {/* Day 2 RAG功能展示 */}
        <div className="bg-green-50 border border-green-200 rounded-lg p-6 max-w-4xl mx-auto mb-8">
          <h2 className="text-2xl font-semibold text-green-900 mb-4">
            Day 2 - RAG功能完成 ✅
          </h2>
          <p className="text-green-700 mb-4">
            向量检索RAG系统已实现，现在可以生成包含详细POI介绍的旅行计划！
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <div className="bg-white p-4 rounded-lg border">
              <h3 className="font-semibold text-gray-800 mb-2">🔍 RAG功能特性</h3>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• 20条北京POI数据向量化存储</li>
                <li>• Qwen Embedding API远程调用</li>
                <li>• 智能相似度检索</li>
                <li>• 详细POI介绍注入</li>
              </ul>
            </div>
            
            <div className="bg-white p-4 rounded-lg border">
              <h3 className="font-semibold text-gray-800 mb-2">📊 系统状态</h3>
              <div className="text-sm text-gray-600 space-y-2">
                {poiStats ? (
                  <div>
                    <p>• POI数量: {poiStats.total_pois}</p>
                    <p>• 向量维度: {poiStats.embedding_dimension}</p>
                    <p>• 状态: {poiStats.status}</p>
                    <p>• 嵌入服务: {poiStats.embedding_service}</p>
                  </div>
                ) : (
                  <button 
                    onClick={getPoiStats}
                    className="bg-blue-500 text-white px-3 py-1 rounded text-xs hover:bg-blue-600"
                  >
                    获取统计信息
                  </button>
                )}
                
                <div className="mt-2">
                  {embeddingStatus ? (
                    <div className={`text-xs px-2 py-1 rounded ${
                      embeddingStatus.status === 'available' 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-red-100 text-red-800'
                    }`}>
                      🔗 {embeddingStatus.message}
                    </div>
                  ) : (
                    <button 
                      onClick={getEmbeddingStatus}
                      className="bg-green-500 text-white px-3 py-1 rounded text-xs hover:bg-green-600"
                    >
                      检查嵌入服务
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
          
          <div className="flex flex-col md:flex-row items-start md:items-end gap-3">
            <div className="text-left w-full md:w-auto md:min-w-[260px]">
              <label className="block text-sm text-gray-700 mb-1">开始日期</label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="border rounded px-3 py-2 text-sm w-full"
              />
            </div>
            <div className="flex-1 w-full">
              <label className="block text-sm text-gray-700 mb-1">自由文本需求</label>
              <textarea
                value={freeText}
                onChange={(e) => setFreeText(e.target.value)}
                placeholder="例如：想周末在北京两天亲子游，预算1000，想去故宫和颐和园。"
                rows={3}
                className="w-full border rounded px-3 py-2 text-sm"
              />
            </div>
            <button 
              onClick={generateTrip}
              disabled={isLoading}
              className="bg-green-500 text-white px-6 py-3 rounded-lg font-semibold hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? '生成中...' : '🎯 生成旅行计划（自由文本）'}
            </button>
            <button
              onClick={resolveDestinationAndWeather}
              className="bg-blue-500 text-white px-4 py-2 rounded-lg font-semibold hover:bg-blue-600"
            >
              解析目的地并取天气
            </button>
          </div>
        </div>
      </div>

      {/* 旅行计划展示 */}
      {tripPlan && (
        <div className="max-w-4xl mx-auto">
          <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              📋 {tripPlan.destination} {tripPlan.theme}
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6 text-sm">
              <div className="bg-gray-50 p-3 rounded">
                <span className="font-semibold">行程天数:</span> {tripPlan.duration_days}天
              </div>
              <div className="bg-gray-50 p-3 rounded">
                <span className="font-semibold">开始日期:</span> {tripPlan.start_date}
              </div>
              <div className="bg-gray-50 p-3 rounded">
                <span className="font-semibold">总费用:</span> ¥{tripPlan.total_estimated_cost}
              </div>
            </div>

            {/* 每日行程 */}
            <div className="space-y-6">
              {tripPlan.daily_plans.map((day, dayIndex) => (
                <div key={dayIndex} className="border border-gray-200 rounded-lg p-4">
                  <h3 className="text-lg font-semibold text-gray-800 mb-3">
                    📅 {day.date} - {day.day_title}
                  </h3>
                  
                  <div className="space-y-4">
                    {day.activities.map((activity, activityIndex) => (
                      <div key={activityIndex} className="bg-blue-50 p-4 rounded-lg">
                        <div className="flex justify-between items-start mb-2">
                          <div className="flex items-center gap-2">
                            <h4 className="font-semibold text-blue-900">{activity.name}</h4>
                            {activity.closed_reason === 'replaced' && (
                              <TooltipProvider>
                                <Tooltip>
                                  <TooltipTrigger asChild>
                                    <span className="text-xs px-2 py-0.5 rounded bg-yellow-100 text-yellow-800 cursor-default">已替换</span>
                                  </TooltipTrigger>
                                  <TooltipContent>
                                    <div className="space-y-1">
                                      <div>原活动：{activity.replaced_from || '—'}</div>
                                      <div>原营业：{activity.replaced_from_open_hours_raw || '未知'}</div>
                                      <div>说明：{readableReason(activity)}</div>
                                      {activity.replacement_candidates && activity.replacement_candidates.length > 0 && (
                                        <div className="mt-1">
                                          <div className="font-medium">候选概览：</div>
                                          <ul className="list-disc ml-4">
                                            {activity.replacement_candidates.slice(0,3).map((c, i) => (
                                              <li key={i}>
                                                <span className="font-medium">{c.name}</span>
                                                {c.summary ? `：${c.summary}` : ''}
                                              </li>
                                            ))}
                                          </ul>
                                        </div>
                                      )}
                                    </div>
                                  </TooltipContent>
                                </Tooltip>
                              </TooltipProvider>
                            )}
                            {activity.open_ok === true && (
                              <span className="text-xs text-green-700">✅ 开门{activity.open_hours_raw ? ` · ${activity.open_hours_raw}` : ''}</span>
                            )}
                            {activity.open_ok === false && (
                              <TooltipProvider>
                                <Tooltip>
                                  <TooltipTrigger asChild>
                                    <span className="text-xs text-amber-700 cursor-default">
                                      ⚠️ {activity.closed_reason === 'replaced' ? `原 ${activity.replaced_from || '该点'} 闭园，已替换` : '闭园/需线下确认'}
                                      {activity.open_hours_raw ? ` · ${activity.open_hours_raw}` : ''}
                                    </span>
                                  </TooltipTrigger>
                                  <TooltipContent>
                                    {activity.open_hours_explain || '该时段不在营业范围内，建议调整时间或更换同类室内/近距离景点'}
                                  </TooltipContent>
                                </Tooltip>
                              </TooltipProvider>
                            )}
                            {activity.open_ok == null && (
                              <span className="text-xs text-gray-600">ℹ️ 营业时间未知</span>
                            )}
                          </div>
                          <span className="text-sm bg-blue-200 text-blue-800 px-2 py-1 rounded">
                            {activity.type}
                          </span>
                        </div>
                        
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                          <div>
                            <p className="text-gray-600 mb-1">
                              <span className="font-medium">📍 地址:</span> {activity.location}
                            </p>
                            <p className="text-gray-600 mb-1">
                              <span className="font-medium">⏰ 时间:</span> {activity.start_time} - {activity.end_time}
                            </p>
                            <p className="text-gray-600 mb-1">
                              <span className="font-medium">💰 费用:</span> ¥{activity.estimated_cost ?? '—'}
                            </p>
                          </div>
                          
                          <div>
                            <p className="text-gray-600 mb-1">
                              <span className="font-medium">💡 贴士:</span> {activity.tips ?? '—'}
                            </p>
                          </div>
                        </div>
                        
                        {/* Day 3: 相邻活动驾车距离/时长 */}
                        {activityIndex > 0 &&
                          activity.distance_km_from_prev != null &&
                          activity.drive_time_min_from_prev != null && (
                          <div className="mt-2 text-xs text-gray-700">
                            🚗 距上个点 {activity.distance_km_from_prev} km · 约 {activity.drive_time_min_from_prev} 分
                          </div>
                        )}

                        <div className="mt-3 p-3 bg-white rounded border">
                          <p className="text-sm text-gray-700 leading-relaxed">
                            {activity.description}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                  
                  <div className="mt-4 p-3 bg-gray-50 rounded">
                    <p className="text-sm text-gray-700">
                      <span className="font-medium">📝 当日总结:</span> {day.daily_summary}
                    </p>
                    <p className="text-sm text-gray-600 mt-1">
                      <span className="font-medium">当日费用:</span> ¥{day.estimated_daily_cost}
                    </p>
                  </div>
                </div>
              ))}
            </div>

            {/* 总体建议 */}
            <div className="mt-6 p-4 bg-yellow-50 rounded-lg">
              <h4 className="font-semibold text-yellow-900 mb-2">💡 总体建议</h4>
              <ul className="text-sm text-yellow-800 space-y-1">
                {tripPlan.general_tips.map((tip, index) => (
                  <li key={index} className="flex items-start">
                    <span className="mr-2">•</span>
                    <span>{tip}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* 规划思路 */}
            <div className="mt-3 p-4 bg-blue-50 rounded-lg">
              <h4 className="font-semibold text-blue-900 mb-1">🧭 规划思路</h4>
              <p className="text-sm text-blue-900/80">
                {tripPlan.plan_rationale || '根据你的偏好，优先安排口碑好、氛围佳且彼此位置相对顺路的景点；早间挑开门早、人少的点，午后搭配轻松体验，尽量缩短通勤；如遇营业时间不合适，会自动用同风格备选替换。'}
              </p>
            </div>
          </div>
        </div>
      )}
    </main>
  )
} 