'use client'

import React, { useEffect, useState } from 'react'

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

interface Props {
  location: string
}

export default function WeatherCard({ location }: Props) {
  const [data, setData] = useState<WeatherForecast | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState<boolean>(true)

  useEffect(() => {
    const controller = new AbortController()
    const fetchData = async () => {
      setLoading(true)
      setError(null)
      try {
        const params = new URLSearchParams({ location, days: '3' })
        const resp = await fetch(`http://localhost:8000/weather/forecast?${params.toString()}`, {
          signal: controller.signal,
        })
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
        const json = await resp.json()
        setData(json)
      } catch (e: any) {
        console.error('Weather fetch failed', e)
        setError(e?.message || 'fetch failed')
      } finally {
        setLoading(false)
      }
    }
    fetchData()
    return () => controller.abort()
  }, [location])

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto mb-4">
        <div className="animate-pulse h-20 bg-gray-100 rounded-lg" />
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="max-w-4xl mx-auto mb-4">
        <div className="rounded-lg border p-4 bg-yellow-50 text-yellow-800 text-sm">
          天气服务暂不可用，已降级（不影响行程规划）
        </div>
      </div>
    )
  }

  const today = data.daily[0]

  return (
    <div className="max-w-4xl mx-auto mb-6">
      <div className="bg-white border rounded-lg p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="text-4xl">🌤️</div>
            <div>
              <div className="text-lg font-semibold">{today.text_day}</div>
              <div className="text-gray-600 text-sm">{today.temp_min_c}℃ ~ {today.temp_max_c}℃ · 降水 {today.precip_mm}mm</div>
              <div className="text-gray-800 text-sm mt-1">{today.advice}</div>
            </div>
          </div>
          <div className="text-right text-xs text-gray-500">
            更新于 {new Date(data.updated_at).toLocaleString()}
          </div>
        </div>
        {data.daily.length > 1 && (
          <div className="grid grid-cols-3 gap-3 mt-4 text-sm">
            {data.daily.slice(1).map((d, i) => (
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
  )
}


