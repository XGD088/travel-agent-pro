// Travel Agent Pro - Empty State Component
// 空状态组件（无行程时显示）

import React from 'react'
import { Map, AlertCircle } from 'lucide-react'
import { useUIStore } from '../../stores/uiStore'

export function EmptyState() {
  const backendHealthy = useUIStore(state => state.backendHealthy)

  return (
    <div className="text-center py-24 flex flex-col items-center">
      <Map className="w-16 h-16 text-muted-foreground" />
      <h2 className="text-2xl font-semibold mt-4">无行程</h2>
      <p className="mt-2 text-muted-foreground">
        请点击左侧的"新建行程"按钮开始。
      </p>
      
      {/* 显示后端连接状态 */}
      {backendHealthy === false && (
        <div className="mt-6 p-4 bg-red-100 border border-red-300 rounded-lg text-red-700">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-5 h-5" />
            <p>后端服务连接失败，请确保后端服务正在运行 (http://localhost:8000)</p>
          </div>
        </div>
      )}
    </div>
  )
}

