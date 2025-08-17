'use client'

import React, { useState } from 'react'

type Daily = {
  date: string
  text_day: string
  icon_day: string
  temp_max_c: number
  temp_min_c: number
  precip_mm: number
  advice: string
}

type WeatherForecast = {
  location: string
  location_id?: string | null
  days: number
  updated_at: string
  daily: Daily[]
}

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
  const [startDate, setStartDate] = useState<string>(
    () => new Date().toISOString().slice(0, 10)
  )
  const [freeText, setFreeText] = useState<string>("")
  const [weather, setWeather] = useState<WeatherForecast | null>(null)

  const generateTrip = async () => {
    setIsLoading(true)
    try {
      // 使用新的组合端点，返回 plan + weather
      const response = await fetch('http://localhost:8000/plan-bundle', {
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
        setTripPlan(data.plan)
        setWeather(data.weather || null)
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

  return (
    <main className="container mx-auto px-4 py-8">
      {weather ? (
        <div className="max-w-4xl mx-auto mb-6">
          <div className="bg-white border rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="text-4xl">🌤️</div>
                <div>
                  <div className="text-lg font-semibold">{weather.daily[0].text_day}</div>
                  <div className="text-gray-600 text-sm">{weather.daily[0].temp_min_c}℃ ~ {weather.daily[0].temp_max_c}℃ · 降水 {weather.daily[0].precip_mm}mm</div>
                  <div className="text-gray-800 text-sm mt-1">{weather.daily[0].advice}</div>
                </div>
              </div>
              <div className="text-right text-xs text-gray-500">
                更新于 {new Date(weather.updated_at).toLocaleString()}
              </div>
            </div>
            {weather.daily.length > 1 && (
              <div className="grid grid-cols-3 gap-3 mt-4 text-sm">
                {weather.daily.slice(1).map((d, i) => (
                  <div key={i} className="bg-gray-50 rounded p-3">
                    <div className="font-medium">{d.date}</div>
                    <div className="text-gray-700">{d.text_day}</div>
                    <div className="text-gray-600">{d.temp_min_c}℃ ~ {d.temp_max_c}℃</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="max-w-4xl mx-auto mb-4 rounded border bg-white p-3 text-sm text-gray-600">
          提示：填写下方信息后点击"生成旅行计划"，将使用 LangGraph 编排生成完整的旅行计划。
        </div>
      )}
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          🏃🏻 Travel Agent Pro
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          AI-Powered Weekend Trip Planner (Beijing ver.)
        </p>
        
        {/* LangGraph 功能展示 */}
        <div className="bg-green-50 border border-green-200 rounded-lg p-6 max-w-4xl mx-auto mb-8">
          <h2 className="text-2xl font-semibold text-green-900 mb-4">
            🚀 LangGraph 编排完成 ✅
          </h2>
          <p className="text-green-700 mb-4">
            使用 LangGraph 统一编排，实现 planner → retriever → scheduler → validators 的完整流程！
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
              <h3 className="font-semibold text-gray-800 mb-2">🚀 LangGraph 编排</h3>
              <div className="text-sm text-gray-600 space-y-2">
                <p>• 统一配置中心</p>
                <p>• 图编排流程</p>
                <p>• 状态管理</p>
                <p>• 错误恢复</p>
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
              {isLoading ? '生成中...' : '🎯 生成旅行计划（LangGraph）'}
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
                          <h4 className="font-semibold text-gray-800">{activity.name}</h4>
                          <span className="text-sm text-gray-600">
                            {activity.start_time} - {activity.end_time}
                          </span>
                        </div>
                        
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                          <div>
                            <p><span className="font-medium">类型:</span> {activity.type}</p>
                            <p><span className="font-medium">地点:</span> {activity.location}</p>
                            <p><span className="font-medium">时长:</span> {activity.duration_minutes}分钟</p>
                            <p><span className="font-medium">费用:</span> ¥{activity.estimated_cost || 0}</p>
                          </div>
                          <div>
                            <p><span className="font-medium">描述:</span> {activity.description}</p>
                            {activity.tips && (
                              <p><span className="font-medium">提示:</span> {activity.tips}</p>
                            )}
                          </div>
                        </div>

                        {/* Day 3: 距离信息 */}
                        {activity.distance_km_from_prev != null && (
                          <div className="mt-2 p-2 bg-yellow-50 rounded text-sm">
                            <span className="font-medium">距离上一站:</span> {activity.distance_km_from_prev}km
                            {activity.drive_time_min_from_prev != null && (
                              <span className="ml-4">
                                <span className="font-medium">车程:</span> {activity.drive_time_min_from_prev}分钟
                              </span>
                            )}
                          </div>
                        )}

                        {/* Day 4: 营业时间信息 */}
                        {activity.open_ok === false && (
                          <div className="mt-2 p-2 bg-red-50 rounded text-sm">
                            <span className="font-medium">⚠️ 营业时间:</span> {readableReason(activity)}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                  
                  <div className="mt-4 p-3 bg-gray-50 rounded">
                    <p className="font-medium text-gray-800">当日总结:</p>
                    <p className="text-gray-600">{day.daily_summary}</p>
                    <p className="text-sm text-gray-500 mt-2">
                      当日预估费用: ¥{day.estimated_daily_cost}
                    </p>
                  </div>
                </div>
              ))}
            </div>

            {/* 总体提示 */}
            {tripPlan.general_tips && tripPlan.general_tips.length > 0 && (
              <div className="mt-6 p-4 bg-yellow-50 rounded-lg">
                <h3 className="font-semibold text-gray-800 mb-2">💡 旅行提示</h3>
                <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
                  {tripPlan.general_tips.map((tip, index) => (
                    <li key={index}>{tip}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </main>
  )
}
